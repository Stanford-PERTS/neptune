import formatDate from 'utils/formatDate';

const programService = ngModule => {
  ngModule.service('Program', function Program($q, $resource, hostingDomain) {
    const ProgramResource = $resource(`//${hostingDomain}/api/programs/:label`);

    // Cache, indexed by Program label
    const data = {};

    /**
     * Querying all programs allows us to retrieve all of the program
     * details (including cohort info) that is needed for UI. The server
     * only returns a subset of program data when performing a `query()`.
     */
    ProgramResource.queryAllPrograms = function () {
      return this.query().$promise.then(getPrograms);
    };

    // Get all programs requested via `programs` array.
    function getPrograms(programs) {
      return $q.all(programs.filter(p => p.listed === true).map(getProgram));
    }

    // Get a single program requested via `program`.
    function getProgram({ label }) {
      // if program is already cached, return it
      if (data[label]) {
        return $q.when(data[label]);
      }

      return ProgramResource.get({ label }).$promise.then(p => {
        // Save program into Program data cache.
        data[p.label] = p;

        // Return requested program.
        return p;
      });
    }

    /**
     */
    ProgramResource.cohorts = function (program) {
      return (
        getProgram(program)
          // pull cohorts out of requested program object
          .then(p => p.cohorts)
          // convert cohorts object to array
          .then(cohorts => {
            // Instead of Object.values since we have some users with browsers
            // without support. https://github.com/PERTS/neptune/issues/894
            const cohortsArray = [];
            for (const label in cohorts) {
              if (cohorts.hasOwnProperty(label)) {
                cohortsArray.push(cohorts[label]);
              }
            }
            return cohortsArray;
          })
          // add readable text for drop down menu display
          .then(cohorts =>
            cohorts.map(cohort => {
              cohort.options_text = `Cohort ${cohort.name}`;
              return cohort;
            }),
          )
          // sort cohorts descending by open_date
          .then(cohorts => cohorts.sort((a, b) => a.open_date - b.open_date))
      );
    };

    ProgramResource.findParticipationCohort = function (program) {
      // The "Participation" Cohort is the first cohort found where today's
      // date falls between the open and close dates.
      return ProgramResource.cohorts(program).then(cohorts =>
        cohorts.find(betweenOpenAndCloseDates),
      );
    };

    ProgramResource.findRegistrationCohort = function (program) {
      // The "Registration Cohort" is the first cohort found where today's
      // date falls between the open and close registration dates, that also
      // is not the Participation Cohort.
      const participationCohort = ProgramResource.findParticipationCohort(
        program,
      );

      const registrationCohort = ProgramResource.cohorts(program).then(
        cohorts => cohorts.find(betweenOpenAndCloseRegistrationDates),
      );

      return $q
        .all({ participationCohort, registrationCohort })
        .then(({ participationCohort, registrationCohort }) => {
          // If a cohort is open for both participation and registration,
          // participation takes precedence. This cohort is returned by
          // findParticipationCohort() but not this one.
          if (
            participationCohort &&
            registrationCohort &&
            participationCohort.label === registrationCohort.label
          ) {
            return undefined;
          }

          // possibly undefined, if the dates don't match
          return registrationCohort;
        });
    };

    function betweenOpenAndCloseDates(cohort) {
      const today = formatDate(new Date());

      return (
        today >= formatDate(cohort.open_date) &&
        today < formatDate(cohort.close_date)
      );
    }

    function betweenOpenAndCloseRegistrationDates(cohort) {
      const today = formatDate(new Date());

      return (
        today >= formatDate(cohort.registration_open_date) &&
        today < formatDate(cohort.registration_close_date)
      );
    }

    /**
     * The structure of checkpoint and task configs will vary from program
     * to program. We need a way to determine where a given task, based on
     * its label, lies within the config, so that we can use that info to
     * search inside tasklists which are provided by the function
     * Checkpoint.queryProjectCheckpointsByProgram which is hitting and API
     * endpoint that only provide task IDs.
     *
     * This function will provide the ordinal (index into checkpoints) and
     * index (index into tasks) where the task with requested label reside.
     */
    ProgramResource.getTaskOrdinalAndIndexByLabel = function (program, label) {
      // Retrieve full program config for this program
      return this.get(program).$promise.then(p => {
        let ordinal;
        let index;

        p.project_tasklist_template.map((checkpoint, cpIndex) => {
          checkpoint.tasks.map((task, taskIndex) => {
            if (task.label.includes(label)) {
              ordinal = cpIndex + 1; // human entered, starting at 1
              index = taskIndex;
            }
          });
        });

        return { ordinal, index };
      });
    };

    /**
     * Compare cohort registration open/close dates to current date.
     * @returns {Array} of cohorts whose registration is open, extracted
     *   from program, possible an empty array.
     */
    ProgramResource.prototype.registrableCohorts = function () {
      // Instead of Object.values since we have some users with browsers
      // without support. https://github.com/PERTS/neptune/issues/894
      const cohortsArray = [];
      for (const label in this.cohorts) {
        if (this.cohorts.hasOwnProperty(label)) {
          cohortsArray.push(this.cohorts[label]);
        }
      }

      return cohortsArray.filter(cohort => {
        // Use the fact ISO 8601 strings are well-ordered and this
        // method outputs in UTC.
        const today = new Date().toISOString();
        return (
          cohort.registration_open_date < today &&
          today < cohort.registration_close_date
        );
      });
    };

    return ProgramResource;
  });
};

export default programService;
