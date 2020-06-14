(function () {
  'use strict';

  window.ngModule.component('uiFilterOptionsOption', {
    transclude: true,
    bindings: {
      filters: '<',
      filter: '<',
      value: '<',
    },
    controller() {
      const vm = this;

      vm.updateFilter = function (value) {
        vm.filters[vm.filter] = value;
      };
    },
    template: `
      <button
        class="Button FilterOptionsOption"
        ng-class="{ active: $ctrl.filters[$ctrl.filter] === $ctrl.value }"
        ng-click="$ctrl.updateFilter($ctrl.value)"
        ng-transclude
      ></button>
    `,
  });
})();
