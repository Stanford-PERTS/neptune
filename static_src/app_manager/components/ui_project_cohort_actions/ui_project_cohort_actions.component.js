import getShortUid from 'utils/getShortUid';

(function () {
  'use strict';

  window.ngModule.component('uiProjectCohortActions', {
    bindings: {
      projectCohort: '<',
      isSuperAdmin: '<',
      toggleAdminPanel: '&',
      closeAdminPanel: '&',
    },
    controller($state, Dashboard) {
      const vm = this;

      vm.openParticipationApprovalTask = function () {
        Dashboard.getParticipationApprovalTask(vm.projectCohort).then(task => {
          $state.go('dashboard.tasks.checkpoints.tasks', {
            projectCohortId: vm.projectCohort.projectCohort.short_uid,
            checkpointId: getShortUid(task.checkpoint_id),
            taskId: task.uid,
          });
        });
      };

      vm.openAddUserPanel = function () {
        Dashboard.getInviteUsersTask(vm.projectCohort).then(task =>
          $state.go('dashboard.tasks.checkpoints.tasks', {
            projectCohortId: vm.projectCohort.projectCohort.short_uid,
            checkpointId: getShortUid(task.checkpoint_id),
            taskId: task.uid,
          }),
        );
      };
    },
    template: `
      <!-- Tasks -->
      <ui-action-button
        ui-sref="dashboard.tasks({ projectCohortId: $ctrl.projectCohort.projectCohort.short_uid })"
        ui-sref-active="active"
        ng-click="$ctrl.closeAdminPanel()"
      >
        <i class="fa fa-tasks"></i>
        Tasks
      </ui-action-button>

      <!-- Participation -->
      <ui-action-button
        ui-sref="dashboard.participation({ projectCohortId: $ctrl.projectCohort.projectCohort.short_uid })"
        ui-sref-active="active"
        ng-click="$ctrl.closeAdminPanel()"
      >
        <i class="fa fa-child"></i>
        Participation
      </ui-action-button>

      <!-- Reports -->
      <ui-action-button
        ui-sref="dashboard.reports({ projectCohortId: $ctrl.projectCohort.projectCohort.short_uid })"
        ui-sref-active="active"
        ng-click="$ctrl.closeAdminPanel()"
      >
        <i class="fa fa-bar-chart-o"></i>
        Reports
      </ui-action-button>

      <!-- Right Side, Super Admin Menu Items -->
      <div ng-if="$ctrl.isSuperAdmin" class="push-right">
        <!-- Organization -->
        <ui-action-button
          ng-click="$ctrl.toggleAdminPanel({ projectCohort: $ctrl.projectCohort, panelName: 'organization' })"
          active="$ctrl.projectCohort.adminPanel === 'organization'"
          admin="true"
        >
          <i class="fa fa-building-o"></i>
          <span>Organization</span>

          <ui-action-button-status
            ng-if="$ctrl.isSuperAdmin"
            class="ActionButtonStatus {{ $ctrl.projectCohort.organization.status }}"
          ><span class="sr-only">{{ $ctrl.projectCohort.organization.status }}</span></ui-action-button-status>
        </ui-action-button>

        <!-- Participation Approval -->
        <ui-action-button
          ng-click="$ctrl.openParticipationApprovalTask(); $ctrl.closeAdminPanel()"
        >
          <i class="fa fa-file-o"></i>
          <span>Program</span>

          <ui-action-button-status
            ng-if="$ctrl.isSuperAdmin"
            class="ActionButtonStatus {{ $ctrl.projectCohort.projectCheckpoint.status }}"
          ><span class="sr-only">{{ $ctrl.projectCohort.projectCheckpoint.status }}</span></ui-action-button-status>
        </ui-action-button>

        <!-- Organization Users -->
        <ui-action-button
          ng-click="$ctrl.toggleAdminPanel({ projectCohort: $ctrl.projectCohort, panelName: 'organizationUsers' })"
          active="$ctrl.projectCohort.adminPanel === 'organizationUsers'"
          admin="true"
        >
          <span ng-if="$ctrl.isSuperAdmin">{{ $ctrl.projectCohort.project.last_active | date:"MM/dd/yyyy" }}</span>
          <i class="fa fa-users"></i>
          <span>Users</span>
        </ui-action-button>

        <!-- Notes -->
        <ui-action-button
          ng-click="$ctrl.toggleAdminPanel({ projectCohort: $ctrl.projectCohort, panelName: 'notes' })"
          active="$ctrl.projectCohort.adminPanel === 'notes'"
          admin="true"
        >
          <i class="fa fa-commenting"></i>
          <span>Notes</span>
        </ui-action-button>
      </div>

      <!-- Right Side, Org Admin Menu Items -->
      <div ng-if="!$ctrl.isSuperAdmin" class="push-right">
        <!-- Organization -->
        <ui-action-button
          ui-sref="dashboard.organizationPanel({ projectCohortId: $ctrl.projectCohort.projectCohort.short_uid })"
          ui-sref-active="active"
          ng-click="$ctrl.closeAdminPanel()"
        >
          <i class="fa fa-building-o"></i>
          <span>Organization</span>

          <ui-action-button-status
            ng-if="$ctrl.isSuperAdmin"
            class="ActionButtonStatus {{ $ctrl.projectCohort.organization.status }}"
          ><span class="sr-only">{{ $ctrl.projectCohort.organization.status }}</span></ui-action-button-status>
        </ui-action-button>

        <!-- Organization Users -->
        <ui-action-button
          ui-sref="dashboard.organizationUsers({ projectCohortId: $ctrl.projectCohort.projectCohort.short_uid })"
          ui-sref-active="active"
          ng-click="$ctrl.closeAdminPanel()"
        >
          <span ng-if="$ctrl.isSuperAdmin">{{ $ctrl.projectCohort.project.last_active | date:"MM/dd/yyyy" }}</span>
          <i class="fa fa-users"></i>
          <span>Users</span>
        </ui-action-button>
      </div>
    `,
  });
})();
