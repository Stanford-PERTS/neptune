(function () {
  'use strict';

  window.ngModule.component('uiInputTextarea', {
    bindings: {
      label: '@',
      model: '=',
      disabled: '<',
    },
    template: `
      <div class="InputLabel">{{ $ctrl.label }}</div>
      <div class="InputField">
        <textarea
          ng-model="$ctrl.model"
          ng-disabled="$ctrl.disabled"
          rows="{{ $ctrl.model.split('\n').length }}"
        ></textarea>
      </div>
    `,
  });
})();
