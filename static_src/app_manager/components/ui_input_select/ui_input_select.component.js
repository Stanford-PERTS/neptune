(function () {
  'use strict';

  window.ngModule.component('uiInputSelect', {
    transclude: true,
    bindings: {
      label: '@',
      model: '=',
      disabled: '<',
    },
    template: `
      <div class="InputLabel">{{ $ctrl.label }}</div>
      <div class="InputField">
        <select
          ng-model="$ctrl.model"
          ng-disabled="$ctrl.disabled"
          ng-transclude
        >
      </div>
    `,
  });
})();
