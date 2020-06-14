(function () {
  'use strict';

  window.ngModule.component('nepCheckpointsIcon', {
    bindings: {
      checkpoint: '<',
    },
    controller() {
      const vm = this;

      vm.$onInit = () => {
        vm.icon = vm.iconToDisplay();
      };

      vm.iconToDisplay = () => {
        if (vm.showOrganizationIcon()) {
          return 'fa-building-o';
        }

        if (vm.showQuizIcon()) {
          return 'fa-list-alt';
        }

        if (vm.showLaunchIcon()) {
          return 'fa-rocket';
        }

        return 'fa-tasks';
      };

      vm.showOrganizationIcon = () =>
        vm.checkpoint.parent_id.includes('Organization');

      vm.showQuizIcon = () =>
        vm.checkpoint.parent_id.includes('Survey') &&
        vm.checkpoint.name.includes('Quiz');

      vm.showLaunchIcon = () =>
        vm.checkpoint.parent_id.includes('Survey') &&
        vm.checkpoint.name.includes('Launch');
    },
    template: `
        <i class="fa fa-3x {{ ::$ctrl.icon }}" aria-hidden="true"></i>
      `,
  });
})();
