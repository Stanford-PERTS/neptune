(function () {
  'use strict';

  window.ngModule.component('nepProjectCohortNotes', {
    bindings: {
      projectCohortId: '<',
    },
    controller($state, Dashboard, User) {
      const vm = this;

      vm.$onInit = function () {
        // Place user on $scope for permissions
        vm.user = User.getCurrent();
        vm.isSuperAdmin = User.isSuperAdmin();

        // Retrieve projectDataRow so that we can access loa_notes on project
        Dashboard.getProjectDataRow(vm.projectCohortId)
          .then(projectDataRow => {
            vm.projectDataRow = projectDataRow;
            vm.project = projectDataRow.project;
            return projectDataRow;
          })
          // Retrieve emails that have been sent to liaison
          .then(projectDataRow => Dashboard.getOrganization(projectDataRow))
          .then(projectDataRow => Dashboard.getLiaison(projectDataRow))
          .then(projectDataRow => Dashboard.getLiaisonEmails(projectDataRow));
      };

      vm.update = function () {
        vm.updating = true;
        vm.error = false;

        Dashboard.updateProjectAndProjectCohort(vm.projectDataRow)
          .then(() => {
            vm.updating = false;
            vm.success = 'Project status and notes saved';
          })
          .catch(() => {
            vm.updating = false;
            vm.error = 'Error updating project status and notes';
          });
      };
    },
    // Don't display notes at all unless its a PERTS admin
    template: `
      <ui-card-panel ng-if="$ctrl.isSuperAdmin">
        <h3>Project Cohort Status &amp; Notes</h3>

        <ui-input-select
          label="Status"
          model="$ctrl.projectDataRow.projectCohort.status"
        >
          <option value="open">Open</option>
          <option value="closed">Closed</option>
        </ui-input-select>

        <ui-input-textarea
          label="Notes"
          model="$ctrl.project.loa_notes"
        ></ui-input-textarea>

        <ui-button
          full-width="true"
          ng-click="$ctrl.update()"
          loading="$ctrl.updating"
        >
          Save Project Cohort Status &amp; Notes
        </ui-button>

        <ui-input-error type="form" ng-show="$ctrl.error">
          {{ $ctrl.error }}
        </ui-input-error>
        <ui-input-success type="form" message="$ctrl.success"></ui-input-success>

        <div class="NotesEmailList">
          <h3>Emails Sent</h3>
          <div ng-repeat="email in $ctrl.projectDataRow.emails" class="NotesEmail">
            <div class="NotesEmailTo">
              <strong>To</strong>: {{ $ctrl.projectDataRow.liaison.name }}
              &lt;{{ $ctrl.projectDataRow.liaison.email }}&gt;
            </div>
            <div class="NotesEmailSubject">
              <strong>Subject</strong>: {{ email.subject }}
            </div>
            <div class="NotesEmailDate">
              <strong>Sent</strong>: {{ email.created | date:'yyyy-MM-dd HH:mm:ss' }}
            </div>
            <div class="NotesEmailBody">
              <strong>Message</strong>: To view, log into <a
              href="https://login.mailchimp.com">login.mailchimp.com</a>
            </div>
          </div>
        </div>

        <div class="NotesEmailList" ng-hide="$ctrl.projectDataRow.emails.length">
          <strong>No emails sent to this liaison.</strong>
        </div>
      </ui-card-panel>
    `,
  });
})();
