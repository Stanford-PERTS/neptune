import moment from 'moment';

(function () {
  'use strict';
  window.ngModule.component('uiProjectCohortStatus', {
    bindings: {
      projectCohort: '<',
      checkpoints: '<',
      organizationCheckpoint: '<',
      projectCheckpoint: '<',
      surveyCheckpoints: '<',
      isSuperAdmin: '<',
    },
    controller($scope, Organization, ProjectCohort, Survey, Checkpoint) {
      const vm = this;

      // Calculate the project cohort's visible status whenever we get new data
      // from higher components. **Also** update it whenever a checkpoint is
      // updated, because changed properties of an object do not trigger
      // $onChanges (sincet he object reference doesn't change).

      vm.$onChanges = function () {
        calculateStatus();
      };

      $scope.$on('/Checkpoint/updated', calculateStatus);

      function calculateStatus() {
        const activeSurvey = getActiveSurvey(vm.projectCohort.surveys);

        if (
          vm.projectCohort.organization.status === Organization.REJECTED_STATUS
        ) {
          // This whole organization is invalid, everthing (all project
          // cohorts) can't participate.
          vm.status = {
            particiationOpen: false,
            label: 'Closed',
            tooltip: 'Your organization was rejected.',
            icon: 'fa-power-off',
          };
        } else if (projectCohortClosed() || cohortClosed()) {
          // The close date for this cohort has passed, everything is locked.
          vm.status = {
            particiationOpen: false,
            label: 'Closed',
            tooltip:
              'Your program has closed. You may still view results below.',
            icon: 'fa-power-off',
          };
        } else if (allCheckpointsComplete(vm.checkpoints)) {
          // All checkpoints are complete, which means reports have been
          // uploaded.
          vm.status = {
            particiationOpen: true,
            label: 'View Report',
            tooltip: 'View and download report(s) below.',
            icon: 'fa-file-text',
          };
        } else if (noIncompleteCheckpoints(vm.checkpoints)) {
          // There are no incomplete checkpoints, but some are 'waiting',
          // possibly waiting on reports to be uploaded.
          vm.status = {
            particiationOpen: true,
            label: 'All Finished',
            tooltip: 'You have completed all tasks. Congratulations!',
            icon: 'fa-check',
          };
        } else if (!activeSurvey) {
          // All surveys are complete, but there are still incomplete
          // checkpoints _after_ those surveys.
          vm.status = {
            particiationOpen: true,
            label: 'Participation Complete',
            tooltip: 'Some tasks remain to complete your program.',
            icon: 'fa-user',
          };
        } else if (activeSurvey.status === Survey.NOT_READY_STATUS) {
          if (
            vm.organizationCheckpoint.status === Checkpoint.COMPLETE_STATUS &&
            vm.projectCheckpoint.status === Checkpoint.COMPLETE_STATUS
          ) {
            vm.status = {
              particiationOpen: false,
              label: `Spot Secured, But ${activeSurvey.name} Not Ready`,
              tooltip: 'Complete tasks below to get ready.',
              icon: 'fa-power-off',
            };
          } else {
            vm.status = {
              particiationOpen: false,
              label: 'Spot Not Secured',
              tooltip: 'Accept the Terms of Service and wait for approval.',
              icon: 'fa-warning',
            };
          }
        } else if (activeSurvey.status === Survey.READY_STATUS) {
          vm.status = {
            particiationOpen: true,
            label: `${activeSurvey.name} Ready`,
            tooltip: 'Participants may begin.',
            icon: 'fa-rocket',
          };
        }
      }

      function getActiveSurvey(surveys) {
        return surveys
          .sort((sA, sB) => sA.ordinal - sB.ordinal)
          .filter((s) => s.status !== Survey.COMPLETE_STATUS)[0]; // perhaps undefined
      }

      function projectCohortClosed() {
        const pcStatus = vm.projectCohort.projectCohort.status;
        return pcStatus === ProjectCohort.CLOSED_STATUS;
      }

      function cohortClosed() {
        const closeDate = moment(
          vm.projectCohort.program_cohort.close_date,
        ).toDate();
        const today = new Date();
        return closeDate < today;
      }

      function allCheckpointsComplete(cps) {
        return cps.every((c) => c.status === Checkpoint.COMPLETE_STATUS);
      }

      function noIncompleteCheckpoints(cps) {
        return (
          cps.length &&
          cps.every((c) => c.status !== Checkpoint.INCOMPLETE_STATUS)
        );
      }
    },
    template: `
      <div class="ProjectCohortStatus">
        <ui-project-cohort-status-bar
          is-super-admin="$ctrl.isSuperAdmin"
          project-cohort="$ctrl.projectCohort"
          checkpoints="$ctrl.checkpoints"
        ></ui-project-cohort-status-bar>

        <ui-project-cohort-status-button
          participation-open="$ctrl.status.particiationOpen"
          label="$ctrl.status.label"
          tooltip="$ctrl.status.tooltip"
          icon="$ctrl.status.icon"
        >
        </ui-project-cohort-status-button>
      </div>
    `,
  });
})();
