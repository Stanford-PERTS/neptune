(function () {
  'use strict';

  /**
   * uiActionButton
   * Smaller button sized for Project Cohort cards functionality.
   */

  window.ngModule.component('uiActionButton', {
    transclude: {
      status: '?uiActionButtonStatus',
    },
    bindings: {
      disabled: '<',
      loading: '<',
      active: '<',
      admin: '<',
      onClick: '&',
    },
    template: `
      <button
        class="Button ActionButton"
        ng-class="{
          active: $ctrl.active,
          admin: $ctrl.admin,
          disabled: $ctrl.disabled,
          loading: $ctrl.loading,
        }"
        ng-disabled="$ctrl.disabled || $ctrl.loading"
        ng-transclude
      ></button>
      <span ng-transclude="status"></span>
    `,
  });
})();
