(function () {
  'use strict';

  window.ngModule.component('uiProjectCohortCard', {
    bindings: {
      projectCohort: '<',
      updateSelectedCount: '&',
    },
    controller($state, $element, User) {
      const vm = this;

      vm.isSuperAdmin = User.getCurrent().user_type === 'super_admin';

      vm.$onInit = function () {
        // Put an ID on the pc card so we can bookmark it.
        $element.attr('id', vm.projectCohort.projectCohort.short_uid);
      };

      vm.toggleSelect = function (projectCohort) {
        projectCohort.selected = !projectCohort.selected;
        vm.updateSelectedCount();
      };

      vm.toggleAdminPanel = function (projectCohort, panelName) {
        // Only one admin panel open per project cohort card.
        projectCohort.adminPanel = projectCohort.adminPanel || false;
        projectCohort.adminPanel =
          projectCohort.adminPanel === panelName ? false : panelName;

        if (!$state.is('dashboard.query')) {
          $state.go('dashboard.query', {
            // Making the assumption we want to open the admin panel within
            // the context of the associated program. This is how we've done it.
            // It's possible the user might want it to open within the context
            // of the organization_id filter, but we don't have a way to know.
            program_label: projectCohort.projectCohort.program_label,
            cohort_label: projectCohort.projectCohort.cohort_label,
            '#': projectCohort.projectCohort.short_uid,
          });
        }
      };

      vm.closeAdminPanel = function () {
        vm.projectCohort.adminPanel = false;
      };
    },
    template: `
      <ui-card
        ng-if="!$ctrl.isSuperAdmin"
        closed="$ctrl.projectCohort.projectCohort.status_vm === 'closed'"
      >
        <ui-organization-name>{{ $ctrl.projectCohort.project.organization_name }}</ui-organization-name>
        <ui-project-cohort-name>
          {{ $ctrl.projectCohort.project.program_name }}
          <span class="program-cohort-name">
            <i class="fa fa-calendar"></i>
            {{ $ctrl.projectCohort.program_cohort.name }}
          </span>
        </ui-project-cohort-name>
        <ui-project-cohort-status
          project-cohort="$ctrl.projectCohort"
          checkpoints="$ctrl.projectCohort.checkpoints"
          organization-checkpoint="$ctrl.projectCohort.organizationCheckpoint"
          project-checkpoint="$ctrl.projectCohort.projectCheckpoint"
          survey-checkpoints="$ctrl.projectCohort.surveyCheckpoints"
          is-super-admin="$ctrl.isSuperAdmin"
        ></ui-project-cohort-status>
        <ui-project-cohort-actions project-cohort="$ctrl.projectCohort" is-super-admin="$ctrl.isSuperAdmin"></ui-project-cohort-actions>
      </ui-card>

      <ui-selectable-card
        ng-if="$ctrl.isSuperAdmin"
        selected="$ctrl.projectCohort.selected"
        on-click="$ctrl.toggleSelect($ctrl.projectCohort)"
        closed="$ctrl.projectCohort.projectCohort.status_vm === 'closed'"
      >
        <div class="div-flex">
          <ui-organization-name>
            <a ui-sref="dashboard.query({
              organization_id: $ctrl.projectCohort.projectCohort.organization_id,
              program_label: null,
              cohort_label: null,
            })">
              {{ $ctrl.projectCohort.project.organization_name }}
            </a>
          </ui-organization-name>
          <ui-project-star project="$ctrl.projectCohort.project"></ui-project-star>
        </div>
        <ui-project-cohort-name>
          {{ $ctrl.projectCohort.project.program_name }}
          <span class="program-cohort-name">
            <i class="fa fa-calendar"></i>
            {{ $ctrl.projectCohort.program_cohort.name }}
          </span>
        </ui-project-cohort-name>
        <ui-project-cohort-status
          project-cohort="$ctrl.projectCohort"
          checkpoints="$ctrl.projectCohort.checkpoints"
          organization-checkpoint="$ctrl.projectCohort.organizationCheckpoint"
          project-checkpoint="$ctrl.projectCohort.projectCheckpoint"
          survey-checkpoints="$ctrl.projectCohort.surveyCheckpoints"
          is-super-admin="$ctrl.isSuperAdmin"
        ></ui-project-cohort-status>
        <ui-project-cohort-actions
          project-cohort="$ctrl.projectCohort"
          is-super-admin="$ctrl.isSuperAdmin"
          toggle-admin-panel="$ctrl.toggleAdminPanel(projectCohort, panelName)"
          close-admin-panel="$ctrl.closeAdminPanel()"
        ></ui-project-cohort-actions>
      </ui-selectable-card>

      <nep-organization
        ng-if="$ctrl.projectCohort.adminPanel === 'organization'"
        organization-id="$ctrl.projectCohort.organization.uid"
        project-cohort-id="$ctrl.projectCohort.projectCohort.short_uid"
      ></nep-organization>

      <nep-organization-users
        ng-if="$ctrl.projectCohort.adminPanel === 'organizationUsers'"
        organization="$ctrl.projectCohort.organization"
        project-cohort-id="$ctrl.projectCohort.projectCohort.short_uid"
        close-admin-panel="$ctrl.closeAdminPanel()"
      ></nep-organization-users>

      <nep-project-cohort-notes
        ng-if="$ctrl.projectCohort.adminPanel === 'notes'"
        project-cohort-id="$ctrl.projectCohort.projectCohort.short_uid"
      ></nep-project-cohort-notes>
    `,
  });
})();
