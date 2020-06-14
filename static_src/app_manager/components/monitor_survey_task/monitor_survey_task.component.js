import moment from 'moment';

(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name neptuneApp.component:nepMonitorSurveyTask
   * @description
   *   Shows various messages and lets users mark survey complete, conditional
   *   on having some participation.
   */

  window.ngModule.component('nepMonitorSurveyTask', {
    bindings: {

      /**
       * Parent can bind to this event. Called when survey has enough
       * participation to be completable by the org admin.
       * @type {Function}
       */
      setCompletable: '&',

      /**
       * Parent can bind to this event. Called to trigger an update/PUT of
       * the task.
       * @type {Function}
       */
      taskComplete: '&',

      /**
       * The task resource.
       * @type {Object}
       */
      task: '<',

      /**
       * Cohort (not a resource)
       * @type {Object}
       */
      cohort: '<',
    },
    transclude: true,
    controller: MonitorSurveyTaskController,
    template: require('./monitor_survey_task.view.html'),
  });

  function MonitorSurveyTaskController(
    $scope,
    Survey,
    Checkpoint,
    Task,
    Participation,
  ) {
    const vm = this;

    vm.$onInit = function () {
      // Until the data comes in, assume the task cannot be completed i.e.
      // is invalid.
      vm.setCompletable({ surveyCompletable: false, error: null });
    };

    vm.$onChanges = function (changes) {
      const previouslyUnset =
        changes.cohort &&
        changes.cohort.currentValue &&
        (!changes.cohort.previousValue ||
          Object.keys(changes.cohort.previousValue).length === 0);
      if (previouslyUnset) {
        initCohort();
      }
    };

    $scope.$watch(
      function valueToWatch() {
        return vm.task.status;
      },
      function onChange() {
        watchForParticipation();
      },
    );

    function initCohort() {
      // Is participation open according to the current date and the date
      // the cohort opens? N.B. ISO strings are well ordered
      const today = new Date();
      vm.openByDate =
        vm.cohort.participationOpenDate && today > vm.cohort.participationOpenDate;

      // Is participation open according to the status of the survey (which
      // is also stored in the task attachment)?
      vm.openByReadiness =
        vm.task.attachment && vm.task.attachment !== Survey.NOT_READY_STATUS;

      watchForParticipation();
    }

    function watchForParticipation() {
      if (vm.openByDate && vm.openByReadiness) {
        // Get participation stats for the view and also check if participation
        // is sufficient to make the task completable.
        const params = {
          id: vm.task.parent_id,
          start: moment.utc(vm.cohort.participationOpenDate).format(),
          end: moment.utc(vm.cohort.participationCloseDate).format(),
        };
        Participation.queryBySurvey(params)
          .$promise.then(placeParticipationOnScope)
          .then(checkCompletable);
      } // else participation isn't open; participation rates aren't relevant.
    }

    function placeParticipationOnScope(participation) {
      vm.participation = participation;
      const finishedRow = participation.find(row => row.value === '100');
      vm.numFinished = finishedRow ? parseInt(finishedRow.n, 10) : 0;
      return participation;
    }

    function checkCompletable(participation) {
      let someFinished = false;
      // Given stats on how many participants have reached each progress marker
      // in a survey, determine if user can move on past this task.
      // Current rule is: greater than zero finished is completable.
      if (vm.task.status !== Task.COMPLETE_STATUS) {
        const finalMarker = participation.last();
        someFinished =
          finalMarker && finalMarker.value === '100' && finalMarker.n > 0;
        vm.setCompletable({
          surveyCompletable: someFinished,
          error: 'insufficient participation',
        });
      }
      return someFinished;
    }
  }
})();
