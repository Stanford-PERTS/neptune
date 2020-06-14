(function () {
  'use strict';

  window.ngModule.component('uiInputText', {
    bindings: {
      disabled: '<',
      label: '@',
      linkForm: '&',
      model: '=',
      required: '<',
      type: '@',
    },
    controller() {
      const vm = this;

      vm.$onInit = function () {
        vm.type = vm.type || 'text';
      };

      vm.linkFormData = function (form) {
        vm.linkForm({ form });
      };
    },
    template: `
      <form name="form" novalidate>
        <div class="InputLabel">{{ $ctrl.label }}</div>
        <div class="InputField">
          <input
            type="{{::$ctrl.type}}"
            name="field"
            ng-model="$ctrl.model"
            ng-disabled="$ctrl.disabled"
            ng-required="$ctrl.required"
          >
        </div>

        <!-- field errors -->
        <div ng-init="$ctrl.linkFormData(form)">
          <ui-input-error ng-show="form.field.$error.required">
            This field is required.
          </ui-input-error>
        </div>
      </form>
    `,
  });
})();
