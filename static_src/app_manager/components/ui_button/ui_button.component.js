(function () {
  'use strict';

  /**
   * uiButton
   * Default button for use on forms and tasks.
   */

  window.ngModule.component('uiButton', {
    transclude: true,
    bindings: {
      fullWidth: '<',
      disabled: '<',
      loading: '<',
      active: '<',
      danger: '<',
      passive: '<',
      onClick: '&',
    },
    template: `
      <button
        class="Button"
        ng-class="{
          active: $ctrl.active,
          danger: $ctrl.danger,
          passive: $ctrl.passive,
          disabled: $ctrl.disabled,
          loading: $ctrl.loading,
          block: $ctrl.fullWidth,
        }"
        ng-disabled="$ctrl.disabled || $ctrl.loading"
        ng-transclude
      ></button>
    `,
  });
})();
