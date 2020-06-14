import sha1 from 'crypto-js/sha1';
import URI from 'urijs';
import parseLocalDateStr from 'utils/parseLocalDateStr';
import getShortUid from 'utils/getShortUid';
import ValidationError from 'utils/ValidationError';

(function() {
  'use strict';

  /**
   * @ngdoc component
   * @name appParticipate.component:nepPresurvey
   * @description
   *    Make program-agnostic decisions about an already identified participant
   *    based on their data, execute sub-components based on program
   *    configuration, and redirect them to Qualtrics.
   *
   *    Requires values set in cookies:
   *    * code - a project cohort participation code
   *    * session - a survey ordinal
   *    * token - stripped version of participant's id or name, to be stored
   *              in the `name` field of the participant table.
   *
   *    Concerns include:
   *    * loading data about the participant
   *    * generating unique qualtrics links
   *    * if cohort is open
   *    * if survey is ready
   *    * if survey is already done, e.g. if comes before one already started
   *
   *    Possible sub-components that might be configured in the program:
   *    * consent to participate
   *    * randomizing them to a condition
   *    * if "skippers" have already done the first session
   */

  window.ngModule.component('nepPresurvey', {
    controller: PresurveyController,
    template: require('./presurvey.view.html'),
  });

  function PresurveyController(
    $state,
    $window,
    $q,
    portalCookies,
    redirect,
    serverTime,
    Organization,
    Program,
    Survey,
    SurveyLink,
    Participant,
    ParticipantData,
    ParticipationCode,
  ) {
    const vm = this;

    this.$onInit = function() {
      // Call toggleMask(false) in subcomponents to turn off the busy image and
      // display a view.
      vm.mask = true;

      // Bool whether participant is recognized or newly created, passed to Q.`
      vm.firstLogin;

      vm.loaded = loadByCookies()
        .then(loadByProjectCohort)
        .then(loadByProgram)
        .then(loadByParticipant)
        .then(loaded => {
          if (isTritonProgram(loaded.program)) {
            return setTritonParams(loaded);
          }
          return vm
            .getSurveyLink(loaded)
            .then(checkCohortOpen)
            .then(checkSurveyReady)
            .then(checkSurveyNotDone);
        })
        .then(startPresurvey)
        .catch(reason => {
          // This will display an appropriate message for why the participant
          // can't access the survey.
          if (reason instanceof Array && reason.length === 0) {
            vm.accessDeniedReason = 'not found';
          } else if (reason instanceof ValidationError) {
            vm.accessDeniedReason = reason.message;
          } else {
            // This error doesn't come from expected sources, re-reject it, which
            // will send it to Sentry with a "Possibly uncaught rejection"
            // message.
            vm.accessDeniedReason = 'unexpected error';
            toggleMask(false);
            return $q.reject(reason);
          }

          console.error(reason);
          toggleMask(false);
        });

      // Make these functions available to subcomponents.
      vm.createPd = createPd;
      vm.nextPresurveyState = nextPresurveyState;
      vm.presurveyError = presurveyError;
      vm.getLoadedData = getLoadedData;
      vm.setLoadedData = setLoadedData;
      vm.setSurveyParams = setSurveyParams;
      vm.toggleMask = toggleMask;
    };

    function toggleMask(shouldMask) {
      if (shouldMask === undefined) {
        vm.mask = !vm.mask;
      } else {
        vm.mask = shouldMask;
      }
    }

    function loadByCookies() {
      if (!portalCookies.get('code')) {
        return $q.reject(new ValidationError('code cookie missing'));
      }

      return $q.all({
        code: portalCookies.get('code'),
        session: Number(portalCookies.get('session')), // coerce to int
        token: portalCookies.get('token'),
        projectCohort: ParticipationCode.get({
          code: portalCookies.get('code'),
        }).$promise,
      });
    }

    /**
     * Load data that require knowing the project cohort:
     * - program
     * - participant
     *
     * @return {Object} Promise resolving with dictionary of loaded data.
     */
    function loadByProjectCohort(loaded) {
      const pc = loaded.projectCohort;

      loaded.program = Program.get({ label: pc.program_label }).$promise;

      loaded.participant = Participant.query({
        name: loaded.token,
        organization_id: pc.organization_id,
      }).$promise.then(results => {
        if (results.length === 0) {
          vm.firstLogin = true;
          return null;
        }

        vm.firstLogin = false;
        return results[0];
      });

      return $q.all(loaded);
    }

    /**
     * Load data that are conditional based on program.
     * - survey
     * - organization
     * - tritonParticipant
     *
     * Also enforces that triton participants can be found on Copilot.
     *
     * @return {Object} Promise resolving with dictionary of loaded data.
     */
    function loadByProgram(loaded) {
      loaded.survey = Survey.queryOne({
        project_cohort_id: loaded.projectCohort.uid,
        ordinal: loaded.session,
      }).$promise.catch(reason => {
        // Ignore a 404 on surveys if this is a Copilot participant.
        if (!isTritonProgram(loaded.program)) {
          return $q.reject(reason);
        }
      });

      if (isTritonProgram(loaded.program)) {
        // check roster
        loaded.tritonParticipant = Participant.getTritonParticipant({
          code: loaded.code.replace(/ /g, '-'),
          token: loaded.token,
        }).$promise.catch(response => {
          if (response.status === 404) {
            // This participant not found on the corresponding Triton roster.
            // Send them back where they can try a new token.
            $state.go('portal.code.session', {
              code: loaded.code,
              session: loaded.session,
              tokenError:
                'We could not find the student ID ' +
                `\u201C${loaded.token}\u201D on your classroom roster.`,
            });

            // Must reject to break the chain of async logic currently
            // executing, so we can let the router take over.
            return $q.reject(new ValidationError());
          } else {
            return $q.reject('unexpected error');
          }
        });

        loaded.surveyDescriptor = loaded.tritonParticipant.then(ppt => {
          // Found on roster. Add cycle details and save.
          return ppt && ppt.cycle ? `cycle-${ppt.cycle.ordinal}` : undefined;
        });
      }

      // Org names are useful in surveys for customization, but they don't
      // apply to triton.
      if (!isTritonProgram(loaded.program)) {
        loaded.organization = Organization.getName({
          id: loaded.projectCohort.organization_id,
        });
      }

      return $q.all(loaded);
    }

    /**
     * Load data that require knowing the participant (or lack of):
     * - array of participant data (`pdArr`)
     * - newly created participant
     *
     * Also responsible for sycning Neptune and Triton participant ids so they
     * always match.
     *
     * @return {Object} Promise resolving with dictionary of loaded data.
     */
    function loadByParticipant(loaded) {
      // Check for mismatch between Neptune and Triton participant ids.
      if (
        loaded.tritonParticipant &&
        loaded.participant &&
        loaded.tritonParticipant.uid !== loaded.participant.uid
      ) {
        return $q.reject(
          `Participant id mismatch. Neptune: ${loaded.participant.uid}, ` +
            `Triton: ${loaded.tritonParticipant.uid}`,
        );
      }

      if (!loaded.participant) {
        // New participant. Create one.

        const params = {
          name: loaded.token,
          organization_id: loaded.projectCohort.organization_id,
        };

        // If this "new" participant already exists on Triton, make sure to
        // created it with a matching id. This is critical for data integrity.
        if (loaded.tritonParticipant) {
          params.id = getShortUid(loaded.tritonParticipant.uid);
        }

        loaded.participant = new Participant(params).$save();
        // The call above may respond with 303 See Other if we're mistaken
        // about this participant being new. So we don't know at this point if
        // they have pd (and a unique link) or not.
      }

      loaded.allPdArr = $q
        .when(loaded.participant)
        .then(
          participant =>
            ParticipantData.query({ participantId: participant.uid }).$promise,
        );

      loaded.pdArr = loaded.allPdArr.then(allPdArr =>
        allPdArr.filter(
          pd => pd.project_cohort_id === loaded.projectCohort.uid,
        ),
      );

      return $q.all(loaded);
    }

    function mockSurvey(pc, session) {
      if (session === 1) {
        status = Survey.COMPLETE_STATUS;
      } else if (session === 2) {
        status = Survey.READY_STATUS;
      } else if (session === 3) {
        status = Survey.NOT_READY_STATUS;
      }

      return $q.when(
        new Survey({
          uid: 'Survey_mocked',
          short_uid: 'mocked',
          project_id: pc.project_id,
          organization_id: pc.organization_id,
          program_label: pc.program_label,
          cohort_label: pc.cohort_label,
          project_cohort_id: pc.uid,
          liaison_id: pc.liaison_id,
          ordinal: session,
          status,
        }),
      );
    }

    function mockPd(pc, participant) {
      // Empty set of pd for a new user.
      return $q.when([]);
    }

    /**
     * Get a survey link from one of three places:
     * 1. The array of participant data already loaded, else
     * 2. A new url from /api/survey_links/X/Y/get_unique, else
     * 3. The anonymous link from the program config.
     *
     * @return {Object} Promise resolving with dictionary of loaded data
     *         including `linkPd`.
     */
    vm.getSurveyLink = function(loaded) {
      // Is the necessary survey link in the pd array?
      loaded.linkPd = loaded.pdArr.find(
        pd => pd.key === 'link' && pd.survey_ordinal === loaded.session,
      );

      if (!loaded.linkPd) {
        // If it's missing, request one and save it to pd.
        const surveyLink = new SurveyLink({
          program_label: loaded.program.label,
          survey_ordinal: loaded.session,
        });

        let saveUniqueLink = true;

        loaded.linkPd = surveyLink
          .$getUnique()
          .catch(function mockAnonymousLink(reason) {
            if (reason.status === 404) {
              // Uh-oh, no unique links left! Fill in the anonymous one and
              // continue loading by mocking the surveyLink entity with the
              // anonymous link in the config.
              const surveyConfig = loaded.program.surveys[loaded.session - 1];
              const anonLink = { url: surveyConfig.anonymous_link };
              // N.B. Don't save that to pd, however, because it may reference
              // the _wrong qualtrics survey_ if participation hasn't opened
              // yet, and we don't want the value to persist. See
              // https://github.com/PERTS/triton/issues/588
              saveUniqueLink = false;
              return anonLink;
            }
            return $q.reject(reason); // Unexpected error, don't catch.
          })
          .then(function linkToPd(linkResponse) {
            const newLinkPd = createPd(loaded, 'link', linkResponse.url);
            // See comments in the .catch() for whether or not to save.
            return saveUniqueLink ? newLinkPd.$save() : $q.when(newLinkPd);
          })
          .then(function putLinkInPdArr(linkPd) {
            loaded.pdArr.push(linkPd); // update client after POST
            // Put the new linkPd promise in loaded so the computer waits for
            // the save to finish.
            return linkPd;
          });
      }

      return $q.all(loaded);
    };

    // Cohorts are only open within a date range. Check against current date in
    // whatever the local time zone is.
    // @param {Object} The loaded data being passed along the chain.
    // @return {Object} Either a promise rejection if the date is out of range,
    // or the loaded data if the cohort is open.
    function checkCohortOpen(loaded) {
      const cohort = loaded.program.cohorts[loaded.projectCohort.cohort_label];
      // Interpret dates locally. If we declare that a program closes on a
      // certain day on our website, people in various timezones can assume
      // it closes on that day in _their timezone_. Parsing this in
      // UTC might cause the program to open or close earlier or later than
      // expected.
      vm.openDate = parseLocalDateStr(cohort.open_date);
      vm.closeDate = parseLocalDateStr(cohort.close_date);

      // Server logic closes programs _on_ the close date, but most people
      // would misinterpret that, so display a close date one day earlier.
      const dayInterval = 24 * 60 * 60 * 1000;
      vm.communicatedCloseDate = new Date(vm.closeDate - dayInterval);

      const serverTimeParsed = parseLocalDateStr(serverTime);
      const cohortClosed =
        serverTimeParsed < vm.openDate || serverTimeParsed > vm.closeDate;

      if (cohortClosed && !$state.params.date_override) {
        return $q.reject(new ValidationError('cohort closed'));
      }

      return loaded;
    }

    /**
     * Check the status of the requested survey. The server has previously
     * derived this from contained checkpoints and tasks.
     */
    function checkSurveyReady(loaded) {
      const surveyReady = loaded.survey.status !== Survey.NOT_READY_STATUS;
      if (!surveyReady && !$state.params.ready_override) {
        return $q.reject(new ValidationError('survey not ready'));
      }
      return loaded;
    }

    /**
     * If they have progress 100 for this survey, don't let them in.
     */
    function checkSurveyNotDone(loaded) {
      const theyAlreadyDidIt = loaded.pdArr.find(
        pd =>
          pd.key === 'progress' &&
          pd.survey_ordinal === loaded.session &&
          parseInt(pd.value, 10) === 100,
      );
      if (theyAlreadyDidIt) {
        return $q.reject(new ValidationError('survey done'));
      }
      return loaded;
    }

    let presurveyStates;

    function startPresurvey(loaded) {
      presurveyStates = loaded.program.presurvey_states || [];
      presurveyStates = presurveyStates.map(
        partialStateName => `presurvey.${partialStateName}`,
      );
      if (presurveyStates.length > 0) {
        $state.go(
          presurveyStates[0],
          null, // no params
          // Replace the current browser history entry with nextState.
          // There's no reason to be able to hit the back button and arrive
          // at the abstract presurvey state.
          { location: 'replace' },
        );
      } else {
        goToSurvey();
      }

      return loaded;
    }

    function nextPresurveyState() {
      toggleMask(true);

      const currentIndex = presurveyStates.indexOf($state.current.name);
      const nextState = presurveyStates[currentIndex + 1];

      // If we're on the last one, or if we're off the reservation, we're done.
      if (!nextState || currentIndex === -1) {
        goToSurvey();
      } else {
        $state.go(nextState, null, { location: 'replace' });
      }
    }

    function presurveyError(reason) {
      console.error('presurvey rejected', $state.current.name, reason);
      vm.accessDeniedReason = reason;
      toggleMask(false);
      getLoadedData().then(loaded => {
        throw new Error(`${reason} ${loaded.code} ${loaded.session}`);
      });
    }

    function goToSurvey() {
      getLoadedData().then(loaded => {
        // Some params are always added to the link.
        const params = { participant_id: loaded.participant.uid };
        if (loaded.survey) {
          params.survey_id = compoundSurveyId(loaded);
        }
        if (loaded.organization) {
          params.organization_id = loaded.organization.uid;
          params.organization_name = loaded.organization.name;
        }
        if ($state.params.date_override || $state.params.ready_override) {
          params.testing = 'true';
        }
        params.first_login = vm.firstLogin ? 'true' : 'false';

        // Add params which may have been set by admins in the tasklist.
        angular.extend(params, loaded.projectCohort.survey_params);

        // Add params generated by presurvey states.
        angular.extend(params, loaded.surveyParams || {});

        // Survey params with whatever query string data is already on the
        // link.
        const url = URI(loaded.linkPd.value).setSearch(params);

        // Go!
        redirect(url);
      });
    }

    function getLoadedData() {
      return vm.loaded; // a promise
    }

    function setLoadedData(loaded) {
      vm.loaded = $q.all(loaded);
      return vm.loaded;
    }

    function setSurveyParams(params) {
      return getLoadedData()
        .then(loaded => {
          if (!loaded.surveyParams) {
            loaded.surveyParams = {};
          }
          angular.extend(loaded.surveyParams, params);
          return loaded;
        })
        .then(setLoadedData);
    }

    function setTritonParams(loaded) {
      // Always use the anonymous link, don't use unique links.
      const surveyConfig = loaded.program.surveys[loaded.session - 1];
      loaded.linkPd = { value: surveyConfig.anonymous_link };

      // Last login, used by our Q survey to determine whether to ask students
      // various validation/demographics questions.
      const lastLoginPd = loaded.pdArr.find(pd => pd.key === 'last_login');

      // Queue all these up for inclusion in the Qualtrics URL. They'll be
      // mixed with the survey params on the project cohort.
      loaded.surveyParams = {
        // Created from Qualtrics, if at all.
        last_login: lastLoginPd ? lastLoginPd.value : undefined,
        // Temporary hack: salt with project cohort id.
        token: sha1(loaded.token + loaded.projectCohort.uid).toString(),
        code: loaded.code,
      };

      return $q.all(loaded);
    }

    /**
     * Should match the behavior of ParticipantData.combine_survey_descriptor
     * on the server.
     * @param  {Object} loaded client data store
     * @return {string}        like 'Survey_ABC', or 'Survey_ABC:descriptor'
     */
    function compoundSurveyId(loaded) {
      return loaded.surveyDescriptor
        ? `${loaded.survey.uid}:${loaded.surveyDescriptor}`
        : loaded.survey.uid;
    }

    function createPd(loaded, key, value) {
      return new ParticipantData({
        key,
        value,
        participant_id: loaded.participant.uid,
        program_label: loaded.program.label,
        project_id: loaded.projectCohort.project_id,
        cohort_label: loaded.projectCohort.cohort_label,
        project_cohort_id: loaded.projectCohort.uid,
        code: loaded.projectCohort.code,
        survey_id: compoundSurveyId(loaded),
        survey_ordinal: loaded.session,
      });
    }

    function isTritonProgram(program) {
      return program.platform === 'triton';
    }
  }
})();
