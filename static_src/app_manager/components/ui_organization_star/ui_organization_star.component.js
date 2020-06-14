(function () {
  'use strict';

  window.ngModule.component('uiProjectStar', {
    bindings: {
      project: '<',
    },
    controller(Project) {
      const vm = this;

      vm.togglePriority = function () {
        vm.project.priority = !vm.project.priority;
        return Project.put(vm.project);
      };
    },
    template: `
      <div class="ProjectStar">
        <i
          ng-class="{
            fa: true,
            'fa-star': $ctrl.project.priority,
            'fa-star-o': !$ctrl.project.priority
          }"
          ng-click="$ctrl.togglePriority()"
        >
        </i>
      </div>
    `,
  });
})();
