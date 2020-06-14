(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name appManager.component:nepProgramRegistration
   * @description
   *    Multi-use cohort registration selection page.
   *    1. You are an existing user and you click join/add program. Gives you
   *       a menu of all possibilities; programLabel is null.
   *    2. You arrive from authentication with a program flag in the query
   *       string; programLabel is set.
   *       a. If there's more than one cohort in that program open for
   *          registration it displays those options.
   *       b. If there's only one, you're forwarded to choosing an org.
   */

  window.ngModule.component('nepProgramRegistration', {
    controller: ProgramRegistrationController,
    template: require('./program_registration.view.html'),
  });

  function ProgramRegistrationController(
    $state,
    User,
    Program,
    yellowstoneDomain,
  ) {
    const vm = this;

    vm.$onInit = function () {
      vm.yellowstoneDomain = yellowstoneDomain;

      Program.query()
        .$promise.then(filterUnlistedPrograms)
        .then(selectRequestedProgram)
        .then(forwardIfCohortDetermined)
        .then(placeProgramsOnScope);
    };

    function filterUnlistedPrograms(programs) {
      return programs.filter(function filter(program) {
        return program.listed === true;
      });
    }

    /**
     * This component accepts a program label as a route parameter. If present,
     * this function will display only cohorts for that program.
     * @param {Array} programs from api
     * @returns {Array} matching input if no param, else containing matching
     *   program only.
     */
    function selectRequestedProgram(programs) {
      if ($state.params.programLabel) {
        return programs.filter(p => p.label === $state.params.programLabel);
      }
      return programs;
    }

    /**
     * In the special cases where a specific program has been requested and
     * there is only one cohort open for registration, save the user a click
     * and forward them on to choosing their organization.
     */
    function forwardIfCohortDetermined(programs) {
      if ($state.params.programLabel && programs.length === 1) {
        const cohorts = programs[0].registrableCohorts();
        if (cohorts.length === 1) {
          $state.go('.chooseOrg', { cohortLabel: cohorts[0].label });
        }
      }
      return programs;
    }

    function placeProgramsOnScope(programs) {
      vm.programs = programs;
    }
  }
})();
