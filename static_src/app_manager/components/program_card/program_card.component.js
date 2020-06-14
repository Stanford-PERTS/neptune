(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name neptuneApp.component:nepProgramCard
   * @description
   *   Program Title Card to display a program's summary
   */

  window.ngModule.component('nepProgramCard', {
    bindings: {

      /**
       * Organization
       * @type {Object}
       */
      organization: '<',

      /**
       * Program title
       * @type {String}
       */
      programTitle: '<',

      /**
       * Project cohort status, either 'open' or 'closed'
       * @type {String}
       */
      projectCohortStatus: '<',

      /**
       * Optional ui-sref value
       * -- used on Dashboard for linking into project cohorts
       * @type {String}
       */
      projectCohortSref: '<',
    },
    controller: ProgramCardController,
    template: require('./program_card.view.html'),
  });

  function ProgramCardController($state) {
    const vm = this;

    vm.$onInit = function () {
      vm.displayProgramStatus = $state.includes('projectCohorts');
    };
  }
})();
