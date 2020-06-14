import URI from 'urijs';
import randomString from 'utils/randomString';
import isStringNumeric from 'utils/isStringNumeric';
import ValidationError from 'utils/ValidationError';

(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name appParticipate.component:nepPortal
   * @description
   *    Identify a participant based on their participation code and token.
   */

  window.ngModule
    .component('nepPortal', {
      controller: PortalController,
      template: require('./portal.view.html'),
    })
    .directive('nepStripCode', stripCodeDirective);

  function PortalController(
    $state,
    $transitions,
    $q,
    $location,
    $window,
    portalCookies,
    redirect,
    Program,
    ProjectCohort,
    ParticipationCode,
  ) {
    const vm = this;
    let numSessionPromise;

    const MISSING_SESSION = '__missing_session__';
    const MISSING_CODE = '__missing_code__';
    const MAX_TOKEN_LENGTH = 128; // varchar(128), see participant.py
    const RANDOM_TOKEN_LENGTH = 12; // used in "skipped" portal type

    this.$onInit = function () {
      // Clear the cookies; fresh start.
      portalCookies.removeAll();

      stateParamsToView();
      vm.stateParams = $state.params;

      vm.mask = true;

      // This function could grab any query string parameters and pass them
      // eventually on to qualtrics. For now, according to Dave, we don't want
      // to support that. To re-enable, just uncomment this function call.
      // storeQueryString();

      // Validate and act on any data parsed from the URL. This is a different
      // chain of promises than when someone types into the form; those start
      // with the functions named submit*().
      $q.when()
        .then(() => {
          if (vm.code) {
            return $q
              .when(vm.checkShortcut(vm.code))
              .then(vm.validateCode)
              .then(vm.deriveSession);
          }
        })
        .then(() => {
          if (vm.session) {
            return vm.validateSession(vm.session);
          }
        })
        .then(() => {
          if (vm.token) {
            return vm.submitToken(vm.token);
          } else if (
            vm.session &&
            vm.participationInfo.portal_type === 'custom'
          ) {
            redirectToCustomPortal();
          } else if (
            vm.session &&
            vm.participationInfo.portal_type === 'skipped'
          ) {
            return vm.submitToken(randomString(RANDOM_TOKEN_LENGTH));
          }
        })
        .then(() => {
          // The session may have been derived from the code in the URL. If we
          // can automatically advance from the session-collecting state
          // (portal.code) to the token-collecting state (porta.code.session),
          // and if we don't yet have the token, then do so.
          if ($state.is('portal.code') && vm.session && !vm.token) {
            $state.go(
              'portal.code.session',
              angular.merge($state.params, {
                code: vm.code,
                session: vm.session,
              }),
            );
          }
        })
        .catch((error) => {
          if (error instanceof ValidationError) {
            console.error(error);
          } else {
            // This error doesn't come from expected sources, re-reject it, which
            // will send it to Sentry with a "Possibly uncaught rejection"
            // message.
            return $q.reject(error);
          }
        })
        .finally(() => {
          vm.mask = false;
        });
    };

    $transitions.onSuccess({ to: 'portal.**' }, stateParamsToView);
    $transitions.onSuccess({ to: 'portal' }, startOver);

    /**
     * Keep the state and the view up to date with each state transition.
     * @param {Object} a ui-router transition
     */
    function stateParamsToView(transition) {
      // Copy `code`, `session`, and `token` to the view. Used when first
      // loading and whenever someone clicks "Start Over".
      ['code', 'session', 'token', 'tokenError'].forEach((k) => {
        vm[k] = $state.params[k];
      });

      // Switch visible form based on state. I've done this instead of having
      // a separate component for each because each state is so simple.
      vm.state = $state.current.name;
    }

    /**
     * Clear any vm-scoped variables when the user starts over.
     */
    function startOver(transition) {
      portalCookies.removeAll();
      numSessionPromise = null;
    }

    /**
     * Parse the query string and store each value in cookies.
     */
    function storeQueryString() {
      util.forEachObj($location.search(), (key, value) => {
        portalCookies.put(key, value);
      });
    }

    /**
     * API for child components, e.g. nepFirstMiLast.
     */
    vm.setToken = function (token) {
      vm.token = token;
    };

    /**
     * Triggered when user clicks the button in the code form.
     * @parm {string} code phrase, possibly with single digit session number,
     *   e.g. "trout viper" or "trout viper 1".
     * @returns {Object} promise
     */
    vm.submitCode = function (code, options = {}) {
      vm.codeError = false;
      vm.mask = true;
      vm.agreeTerms = options.agreeTerms || vm.agreeTerms;

      const submitCodePromise = $q
        .when(code)
        .then(vm.checkShortcut)
        .then(vm.splitCode)
        .then(vm.validateCode)
        .then(vm.deriveSession)
        .then(vm.validateSession)
        .then(() => {
          if (vm.session && vm.participationInfo.portal_type === 'custom') {
            return redirectToCustomPortal();
          }
          if (vm.session && vm.participationInfo.portal_type === 'skipped') {
            // Skip entering both the session ordinal and token.
            return vm.submitToken(randomString(RANDOM_TOKEN_LENGTH));
          }
          // May branch states depending on what information the user gives.
          // These are the defaults.
          let targetState = 'portal.code';
          $state.params.code = vm.code;
          if (vm.session) {
            // Skip the state that involves entering the session ordinal.
            targetState = 'portal.code.session';
            $state.params.session = vm.session;
          }
          $state.go(targetState, $state.params);
        })
        .catch((error) => {
          if (error instanceof ValidationError) {
            console.error(error);
          } else {
            // This error doesn't come from expected sources, re-reject it, which
            // will send it to Sentry with a "Possibly uncaught rejection"
            // message.
            return $q.reject(error);
          }
        })
        .finally(() => {
          vm.mask = false;
        });

      return submitCodePromise;
    };

    /**
     * There's a special leading string that allows you in no matter what.
     */
    vm.checkShortcut = function (code) {
      const [match, remainder] = /^testing only (.*)$/.exec(code) || [];
      if (match) {
        vm.code = remainder;
        $state.params.date_override = true;
        $state.params.ready_override = true;
      }
      return vm.code;
    };

    function codeErrorCallback() {
      vm.codeError = "We don't recognize that code. Please try again.";
      vm.code = undefined;

      $state.go('participate', { code: vm.code });
      return $q.reject(new ValidationError(vm.codeError));
    }

    /**
     * If the code has a session number, split it into a code phrase and a
     * number, setting both on the view. Otherwise noop.
     * @param {string} user-entered code
     * @returns {string} code w/o a session number
     */
    vm.splitCode = function (codeInput) {
      // People don't always put the spaces in the right place. Use a fairly
      // forgiving regex to separate the code and the session.
      // N.B. this runs after stripCode() so we don't have to worry about
      // whitespace or case.
      let codeWord1, codeWord2, session;
      // Should handle things like "trout viper1" or "trout viper 1foo"
      const withSession = /^([a-z]+) ([a-z]+) ?(\d+).*$/;
      const withoutSession = /^([a-z]+) ([a-z]+)$/;
      if (withSession.test(codeInput)) {
        [, codeWord1, codeWord2, session] = withSession.exec(codeInput);
        vm.session = parseInt(session, 10);
      } else if (withoutSession.test(codeInput)) {
        [, codeWord1, codeWord2] = withoutSession.exec(codeInput);
      } else {
        return codeErrorCallback();
      }
      vm.code = `${codeWord1} ${codeWord2}`;
      return vm.code;
    };

    // Make accessible for testing.
    vm.stripCode = stripCode;

    /**
     * Triggered when user submits the session form.
     * @param {Number} session number
     * @returns {Object} promise
     */
    vm.submitSession = function (session, options = {}) {
      vm.mask = true;
      vm.agreeTerms = options.agreeTerms || vm.agreeTerms;

      return vm
        .validateSession(session)
        .then(() => {
          if (vm.participationInfo.portal_type === 'custom') {
            redirectToCustomPortal();
          } else if (vm.participationInfo.portal_type === 'skipped') {
            return vm.submitToken(randomString(RANDOM_TOKEN_LENGTH));
          } else {
            $state.go('portal.code.session', { session });
          }
        })
        .finally(() => {
          vm.mask = false;
        });
    };

    /**
     * Triggered when user submits the token form.
     * @param {string} token, either student ID or name or similar
     * @returns {Object} promise
     */
    vm.submitToken = function (token, options = {}) {
      vm.mask = true;
      vm.agreeTerms = options.agreeTerms || vm.agreeTerms;

      return vm
        .validateToken(token)
        .then(() => {
          vm.setToken(token);
          portalCookies.put('code', vm.code);
          portalCookies.put('session', vm.session);
          portalCookies.put('token', vm.token);

          if (vm.agreeTerms) {
            $state.go('presurvey', $state.params);
          } else {
            // Make sure to get agreement from the user re: terms of use
            // and privacy policy.
            $state.go('portal.code.session.token', {
              code: vm.code,
              session: vm.session,
              token: vm.token,
            });
          }
        })
        .finally(() => {
          vm.mask = false;
        });
    };

    vm.submitAgreeTerms = function () {
      vm.mask = true;
      vm.agreeTerms = true;
      $state.go('presurvey', $state.params);
    };

    /**
     * Check code against database of project cohorts.
     * @param {string} code phrase w/o session number. If this is the
     *   MISSING_CODE constant, an error is logged.
     * @returns {Object} promise(participationInfo) or rejection
     */
    vm.validateCode = function (code) {
      // Get and store the PC based on the code.
      // Returns a promise with pc or rejects if none found.
      // Sets the project cohort on the scope.

      vm.codeError = undefined;

      if (code === MISSING_CODE) {
        // @todo(chris): get a js logger up and running so we can formally
        // log this error, like $log.error, or TrackJS.
        console.error('Missing code reported from custom portal.');
        return codeErrorCallback();
      }

      // @todo(chris): support default session number, see #263
      return ParticipationCode.get({ code: vm.code }).$promise.then(
        function success(info) {
          // The server's response includes properties of the corresponding
          // project cohort or reporting unit necessary for starting the
          // participant's survey.
          vm.participationInfo = info;

          // Apply defaults if the portal type is undefined or generic.
          vm.participationInfo.portal_type = validatePortalType(
            vm.participationInfo.portal_type,
          );

          return info;
        },
        codeErrorCallback,
      );
    };

    /**
     * If the session derivable from the code/program then sets it on the view.
     * @param {Object} participationInfo from /api/codes
     * @returns {Object} promise(session)
     */
    vm.deriveSession = function (partInfo) {
      return vm.getNumSessions(partInfo.program_label).then((num) => {
        if (num === 1) {
          vm.session = 1;
        }
        return vm.session;
      });
    };

    /**
     * Checks if the session is valid, given the code/program.
     * @param {*} session as number (via form) or string (via URL) or undefined
     * @returns {*} session number or undefined or promise rejection.
     */
    vm.validateSession = function (session) {
      // Check session ordinal against program config, if necessary.
      // Returns a promise with program or rejects if session is invalid.
      // If there's a session ordinal, we need to fetch the program also.
      vm.sessionError = undefined;

      const programLabel = vm.participationInfo.program_label;

      // Is the requested session valid given that number of sessions?
      return vm.getNumSessions(programLabel).then((numSessions) => {
        const s = parseSession(session);
        if (s === undefined) {
          // It's not set yet. This happens when someone types in a sessionless
          // participation code. No big deal, treat as valid.
          return;
        }
        if (isNaN(s) || s < 1 || s > numSessions) {
          // Use pre-parsed session value for debugging.
          vm.sessionError = `There is no session ${session} for this program.`;
          // This may require a transition if the session was entered with
          // the code.
          $state.go('portal.code', { code: vm.code, session: s });
          return $q.reject(new ValidationError(vm.sessionError));
        }
        // Else the session is parseable. Store and allow promise chain to
        // continue.
        vm.session = s;
        return s;
      });
    };

    /**
     * Parse a session string, either from user input or the URL.
     * @param {*} some value to parse
     * @returns {*} see below:
     *   undefined -> undefined
     *   numeric string -> corresponding base ten number
     *   number -> number
     *   MISSING_SESSION constant -> 1
     */
    function parseSession(s) {
      if (s === undefined) {
        return undefined;
      }
      if (s === MISSING_SESSION) {
        // @todo(chris): get a js logger up and running so we can formally
        // log this error, like $log.error, or TrackJS.
        console.error('Missing session reported from custom portal.');
        // Default to 1 because we're a) sure it exists for any program
        // and b) it's usually the most important session.
        return 1;
      }
      return isStringNumeric(s) ? parseFloat(s) : NaN;
    }

    /**
     * Get the number of sessions available in the program. Tries to be smart
     * about not fetching multiple times.
     * @param {string} program label e.g. 'cg17' or 'ep19'
     * @returns {Object} promise(numSessions)
     */
    vm.getNumSessions = function (programLabel) {
      if (numSessionPromise) {
        return numSessionPromise;
      }

      numSessionPromise = Program.get({ label: programLabel }).$promise.then(
        (program) => program.surveys.length,
      );
      return numSessionPromise;
    };

    /**
     * Show warnings if the token is (somehow) not a string, or if the token is
     * too long to fit in the db.
     * @returns {Object} promise
     */
    vm.validateToken = function (token) {
      vm.tokenError = null;
      let validityPromise = $q.when(token);

      if (typeof token !== 'string') {
        vm.tokenError = 'Invalid entry.';
      } else if (token.length > MAX_TOKEN_LENGTH) {
        vm.tokenError = 'Your entry is too long.';
      } else if (token === '') {
        vm.tokenError = 'Please enter a value.';
      }

      if (vm.tokenError) {
        validityPromise = $q.reject(new ValidationError(vm.tokenError));
      }

      return validityPromise;
    };

    /**
     * Takes a potential portal type, and returns one guaranteed to be from
     * a whitelisted set. Ensures the view can determine what to display.
     * @param {string} portal type
     * @returns {string} portal type, see nepApi.ProjectCohort
     */
    function validatePortalType(portalType) {
      if (ProjectCohort.PORTAL_TYPES.includes(portalType)) {
        return portalType;
      }
      return 'first_mi_last';
    }

    function redirectToCustomPortal() {
      // Adds code and session to the query string of the custom portal,
      // preserving whatever query string it may already have.
      if (!vm.participationInfo.custom_portal_url) {
        vm.codeError =
          'The custom portal URL has not been set. Please ' +
          'contact your program administrator.';
        return;
      }

      // Retain the `testing only` code prefix if it's being used
      const code =
        $state.params.date_override && $state.params.ready_override
          ? `testing only ${vm.code}`
          : vm.code;

      const url = URI(vm.participationInfo.custom_portal_url).setSearch({
        code: code.replace(/ /g, '-'),
        session: vm.session,
      });

      redirect(url);
    }
  }

  function stripCode(rawCode) {
    // Clean up user input of participation codes.
    // Codes should be space-separated words and/or numbers.
    return typeof rawCode !== 'string'
      ? undefined
      : rawCode
          .trim()
          .replace(/\s+/g, ' ') // clean multiple/strange spaces between words
          .toLowerCase()
          .replace(/[^a-z0-9 ]/g, ''); // allow only alphanumeric characters
  }

  function stripCodeDirective() {
    return {
      restrict: 'A',
      require: 'ngModel',
      link(scope, element, attrs, ngModel) {
        if (!ngModel) {
          console.error('nepStripCode directive requires ngModel');
          return;
        }
        ngModel.$parsers.push(stripCode);
      },
    };
  }
})();
