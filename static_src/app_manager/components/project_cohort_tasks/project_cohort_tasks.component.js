import getShortUid from 'utils/getShortUid';

(function () {
  'use strict';

  window.ngModule.component('nepProjectCohortTasks', {
    controller($state) {
      const vm = this;

      vm.$onInit = function () {
        vm.projectCohortId = getShortUid($state.params.projectCohortId);
      };
    },
    template: `
      <div>ProjectCohortTasks: {{ $ctrl.projectCohortId }}</div>
    `,
  });
})();
