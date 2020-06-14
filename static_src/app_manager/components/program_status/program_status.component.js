(function () {
  'use strict';

  window.ngModule.component('nepProgramStatus', {
    bindings: {

      /**
       * Project cohort status, either 'open' or 'closed'
       * @type {String}
       */
      projectCohortStatus: '<',
    },
    require: {
      parent: '^^nepProjectCohort',
    },
    controller: ProgramStatusController,
    template: require('./program_status.view.html'),
  });

  function ProgramStatusController($q, $scope, ProjectCohort, Survey) {
    const vm = this;

    vm.$onInit = function () {
      updateStatus();
      $scope.$on('/Task/updated', updateStatus);
    };

    function updateStatus() {
      vm.parent
        .getSurveys()
        .then(placeSurveysOnScope)
        .then(getProgramStatus)
        .then(placeProgramStatusOnScope);
    }

    function getProgramStatus() {
      let status;
      // Figure out the first non-complete survey.
      const activeSurvey = vm.surveys.filter((s) => s.status !== Survey.COMPLETE_STATUS)[0]; // perhaps undefined

      if (isProgramClosed()) {
        // The close date for this cohort has passed, everything is locked.
        status = {
          particiationOpen: false,
          label: 'Closed',
          tooltip: 'Your program has closed. You may still view results below.',
        };
      } else if (isAllComplete()) {
        // All tasks (including report tasks) are done. Participation is still
        // open.
        status = {
          particiationOpen: true,
          label: 'All Finished',
          tooltip: 'You have completed all tasks. Congratulations!',
        };
      } else if (!activeSurvey) {
        // The first incomplete survey can't be found b/c they're all complete.
        // The only task(s) left involve waiting for and viewing reports.
        status = {
          particiationOpen: true,
          label: 'View Report',
          tooltip: 'View and download report(s) below.',
        };
      } else if (activeSurvey.status === Survey.NOT_READY_STATUS) {
        status = {
          particiationOpen: false,
          label: `${activeSurvey.name  } Not Ready`,
          tooltip: 'Complete tasks below to get ready.',
        };
      } else if (activeSurvey.status === Survey.READY_STATUS) {
        status = {
          particiationOpen: true,
          label: `${activeSurvey.name  } Ready`,
          tooltip: 'Participants may begin.',
        };
      }

      return status;
    }

    function placeSurveysOnScope(surveys) {
      vm.surveys = surveys;
    }

    function placeProgramStatusOnScope(status) {
      vm.status = status;
      return status;
    }

    // Using the `tasks` provided, checks against the app's task status and
    // returns the last completed task found. We care about the last one
    // since we want to know how far along the user has progressed.
    function findCompletedTask(tasks) {
      let completedTask;

      tasks.forEach((task) => {
        if (isTaskWithLabelComplete(task.label)) {
          completedTask = task;
        }
      });

      return completedTask;
    }

    // Finds the task based on provided `label`.
    function taskWithLabel(label) {
      return vm.parent.tasks.find((task) => task.label === label);
    }

    // Returns true if task with `label` is marked isComplete.
    function isTaskWithLabelComplete(label) {
      return taskWithLabel(label).isComplete;
    }

    // Checks to make sure all tasks for either isComplete or isForbidden.
    // How do we want to handle `Program Status` and `Final Report` tasks?
    function isAllComplete() {
      return vm.parent.tasks.every((task) => task.isComplete || task.isForbidden);
    }

    function isProgramClosed() {
      return vm.projectCohortStatus === ProjectCohort.CLOSED_STATUS;
    }
  }
})();
