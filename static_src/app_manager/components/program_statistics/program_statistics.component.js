(function () {
  'use strict';

  window.ngModule.component('nepProgramStatistics', {
    require: {
      dashboardCtrl: '^nepDashboardMain',
    },
    bindings: {
      program: '<',
      projectDataRows: '<',
    },
    controller() {
      const vm = this;

      vm.$onInit = function () {};
    },
    template: `
      <ui-card>
        <h1>{{ $ctrl.program.name }}</h1>
        <h2>Program Statistics</h2>
      </ui-card>
      <ui-card-panel>
        <table>
          <thead>
            <tr>
              <th>Description</th>
              <th>Number</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Number of Colleges Started Process</td>
              <td>{{ $ctrl.projectDataRows.length }}</td>
            </tr>

            <tr>
              <td>Number of Colleges Org Approved</td>
              <td>
                {{
                  (
                    $ctrl.projectDataRows |
                    filter:$ctrl.dashboardCtrl.getFilter({orgApproved:'yes'})
                  ).length
                }}
              </td>
            </tr>

            <tr>
              <td>Number of Colleges Terms of Use Accepted</td>
              <td>
                {{
                  (
                    $ctrl.projectDataRows |
                    filter:$ctrl.dashboardCtrl.getFilter({termsAccepted:'yes'})
                  ).length
                }}
              </td>
            </tr>
            <tr>
              <td>Number of Colleges with Program Approved</td>
              <td>
                {{
                  (
                    $ctrl.projectDataRows |
                    filter:$ctrl.dashboardCtrl.getFilter({programApproved:'yes'})
                  ).length
                }}
              </td>
            </tr>
            <tr>
              <td>Number of Colleges with Program Unapproved</td>
              <td>
                {{
                  (
                    $ctrl.projectDataRows |
                    filter:$ctrl.dashboardCtrl.getFilter({programApproved:'no'})
                  ).length
                }}
              </td>
            </tr>

          </tbody>
        </table>
      </ui-card-panel>
    `,
  });
})();
