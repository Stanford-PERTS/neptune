import getShortUid from 'utils/getShortUid';

(function () {
  'use strict';

  window.ngModule.component('uiProjectCohortClosed', {
    controller($state, $transitions, Dashboard, User) {
      const vm = this;

      function getProgram() {
        if (!vm.projectCohortId) {
          return;
        }

        Dashboard.getProjectDataRow(vm.projectCohortId).then(projectDataRow => {
          vm.projectDataRow = projectDataRow;
          Dashboard.getProgram(projectDataRow);
        });
      }

      vm.$onInit = function () {
        vm.user = User.getCurrent();
        vm.isSuperAdmin = User.isSuperAdmin();
        vm.projectCohortId = getShortUid($state.params.projectCohortId);

        getProgram();
      };
    },
    template: `
      <ui-card ng-show="!$ctrl.isSuperAdmin && $ctrl.projectCohortId && $ctrl.projectDataRow.projectCohort.status === 'closed'">
        <strong>
          Your Registration and Setup for {{::$ctrl.projectDataRow.program.name}} is
          now closed for {{::$ctrl.projectDataRow.program.cohorts[$ctrl.projectDataRow.projectCohort.cohort_label].name}}
        </strong>
        <p>
          If you are seeing this message your registration for {{::$ctrl.projectDataRow.program.name}}
          has been closed. There are several reasons why your registration could
          be closed, including ineligibility for the program, incomplete tasks,
          or no remaining spots in the program. You should have received
          communications from our team regarding the details on why your
          registration has been closed. If you believe you have reached this
          message in error, please contact support@perts.net
        </p>
        <p>
        Thank you for your interest in PERTS programs!
        </p>
        <p>
          We plan to make more programs available in the future (including
          {{::$ctrl.projectDataRow.program.name}} ), but the terms of that
          continuation depend on  both PERTS staffing and capacity, as well as
          the level of interest. If  your organization is interested in
          participating in future programs,  please fill out the &ldquo;Get
          Updates&rdquo; form for one of our  programs at  <a
          href="//www.perts.net/programs">perts.net/programs</a> and we&rsquo;ll
          be in touch about the process for joining!
        </p>
        <p>
          Your work is still saved for your reference, but details regarding the
          {{::$ctrl.projectDataRow.program.cohorts[$ctrl.projectDataRow.projectCohort.cohort_label].name}}
          program cannot be changed.
        </p>
      </ui-card>
    `,
  });
})();
