(function () {
  'use strict';
  window.ngModule.component('uiProjectCohortStatusButton', {
    bindings: {
      participationOpen: '<',
      label: '<',
      tooltip: '<',
      icon: '<',
    },
    // controller: function () {
    //   this.$onInit = function () {
    //     console.log("uipcsb", this);
    //   };
    // },
    template: `
      <div class="ProjectCohortStatusButton">
        <ui-action-button
          loading="!$ctrl.label"
          active="$ctrl.participationOpen"
          disabled="{true}"
        >
          <i class="fa fa-lg {{ $ctrl.icon || 'fa-rocket' }}"></i>
          {{ $ctrl.label }}
        </ui-action-button>
      </div>
    `,
  });
})();
