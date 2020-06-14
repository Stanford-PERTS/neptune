(function () {
  'use strict';

  window.ngModule.component('uiInputError', {
    bindings: {
      type: '@',
    },
    transclude: true,
    template: `
      <div
        class="{{ $ctrl.type === 'form' ? 'FormError' : 'InputError' }}"
        ng-transclude
      >
      </div>
    `,
  });
})();
