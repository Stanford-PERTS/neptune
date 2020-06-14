(function () {
  'use strict';

  window.ngModule.component('uiProjectCohortStatusBar', {
    bindings: {
      checkpoints: '<',
      projectCohort: '<',
      isSuperAdmin: '<',
    },

    // Need to use ng-if below because using ng-show causes a rendering / style
    // issue that I'm unable to resolve. This is probably appropriate since it's
    // using PERTS Admin status to determine, so it's unlikely to change from
    // view to view.
    template: `
      <ui-project-cohort-status-bar-org
        ng-if="!$ctrl.isSuperAdmin"
        checkpoints="$ctrl.checkpoints"
        project-cohort="$ctrl.projectCohort"
      ></ui-project-cohort-status-bar-org>

      <ui-project-cohort-status-bar-admin
        ng-if="$ctrl.isSuperAdmin"
        checkpoints="$ctrl.checkpoints"
        project-cohort="$ctrl.projectCohort"
      ></ui-project-cohort-status-bar-admin>
    `,
  });

  // Regular user version of the StatusBar. This status bar fills up based on the
  // percentage of checkpoints that are "complete" from the user perspective.
  // Technically, this means checkpoints that are `!== incomplete`.
  window.ngModule.component('uiProjectCohortStatusBarOrg', {
    bindings: {
      checkpoints: '<',
      projectCohort: '<',
    },
    controller() {
      const vm = this;

      vm.$onChanges = function ({ checkpoints: { currentValue: checkpoints } }) {
        const totalStatusParts = checkpoints.length;
        const incompleteStatusParts = checkpoints.filter(
          c => c.status_vm === 'incomplete',
        ).length;
        const completeStatusParts = totalStatusParts - incompleteStatusParts;

        const percentComplete = (completeStatusParts / totalStatusParts) * 100;
        vm.percentComplete = isNaN(percentComplete) ? 0 : percentComplete;
      };
    },
    template: `
      <ui-project-cohort-status-bar-complete
        percent-complete="$ctrl.percentComplete"
      ></ui-project-cohort-status-bar-complete>
    `,
  });

  window.ngModule.component('uiProjectCohortStatusBarComplete', {
    bindings: {
      percentComplete: '<',
    },
    template: `
      <div style="width: {{ $ctrl.percentComplete }}%">
        <span>{{ $ctrl.percentComplete }}% Complete</span>
      </div>
    `,
  });

  // Admin version of StatusBar. Admins get additional details on checkpoint
  // status that might be confusing to regular users. The StatusBar is broken up
  // into N parts, where N equals the number of checkpoints.
  window.ngModule.component('uiProjectCohortStatusBarAdmin', {
    bindings: {
      checkpoints: '<',
      projectCohort: '<',
    },
    controller($state) {
      const vm = this;

      vm.$onChanges = function ({ checkpoints: { currentValue: checkpoints } }) {
        const totalStatusParts = checkpoints.length;
        let checkpointPercent = 100 / totalStatusParts;
        checkpointPercent =
          isNaN(checkpointPercent) || checkpointPercent === Infinity
            ? 0
            : checkpointPercent;
        vm.checkpointPercent = checkpointPercent;
      };

      vm.openCheckpoint = function (checkpoint) {
        $state.go('dashboard.tasks.checkpoints', {
          projectCohortId: vm.projectCohort.projectCohort.short_uid,
          checkpointId: checkpoint.short_uid,
        });
      };
    },
    template: `
      <div ng-repeat="cp in $ctrl.checkpoints track by cp.uid"
        ng-click="$ctrl.openCheckpoint(cp)"
        class="ProjectCohortStatusBarCheckpoint {{ cp.status_vm }}"
        style="width: {{ $ctrl.checkpointPercent }}%"
      ></div>
    `,
  });
})();
