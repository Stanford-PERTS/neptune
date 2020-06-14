import getShortUid from 'utils/getShortUid';

(function () {
  'use strict';

  window.ngModule.component('nepProjectCohortReports', {
    controller($state, $q, ProjectCohort, Survey, Task) {
      const vm = this;

      vm.$onInit = function () {
        vm.projectCohortId = getShortUid($state.params.projectCohortId);

        getProjectCohort()
          .then(getSurveys)
          .then(getSurveyTasks)
          .then(wrangleReports);
      };

      function getProjectCohort() {
        return ProjectCohort.get({ id: vm.projectCohortId }).$promise;
      }

      function getSurveys() {
        return Survey.queryByProjectCohort({ id: vm.projectCohortId }).$promise;
      }

      function getSurveyTasks(surveys) {
        const groupedPromises = surveys.map(
          s => Task.queryBySurvey({ id: s.uid }).$promise,
        );
        return $q
          .all(groupedPromises)
          .then(groupedTasks => [].concat(...groupedTasks));
      }

      function wrangleReports(tasks) {
        vm.reportTasks = tasks.filter(
          t => t.data_type === 'file' && t.label.includes('report'),
        );
        vm.reportTasks.forEach(task => {
          task.attachmentParsed = task.attachment
            ? JSON.parse(task.attachment)
            : {};
        });
      }
    },
    template: `
      <ui-card-panel>
        <ul>
          <li ng-repeat="t in $ctrl.reportTasks">
            {{::t.name}}:
            <a
              ng-if="t.attachmentParsed.gcs_path"
              href="/api/tasks/{{::t.uid}}/attachment"
              target="_blank"
              ng-show="t.attachmentParsed.filename"
            >
              {{ ::t.attachmentParsed.filename }}
            </a>
            <a
              ng-if="t.attachmentParsed.link"
              ng-href="{{ t.attachmentParsed.link }}"
              target="_blank"
              ng-show="t.attachmentParsed.filename"
            >
              {{ ::t.attachmentParsed.filename }}
            </a>
            <em ng-hide="t.attachmentParsed.filename">
              (no report available)
            </em>
          </li>
        </ul>
      </ui-card-panel>
    `,
  });
})();
