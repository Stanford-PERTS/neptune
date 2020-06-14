// ui-card
//
// A card is container used to present data. This is used for presenting
// organization info, project cohort info, option panels, search panels, etc.
//
// Example usage:
//
// <ui-card>
//   Card content goes here.
// </ui-card>
//
// <ui-card loading="$ctrl.isLoading">
//   Card content goes here.
//   Loading indicator will be displayed.
// </ui-card>
//
// <ui-card closed="$ctrl.isCohortClosed">
//   Used with project cohort cards.
//   Styled to indicate the cohort is closed.
// </ui-card>

(function () {
  'use strict';
  window.ngModule.component('uiCard', {
    transclude: true,
    bindings: {
      closed: '<',
      disabled: '<',
      loading: '<',
    },
    template: `
      <div
        class="Card"
        ng-class="{closed: $ctrl.closed, disabled: $ctrl.disabled}"
      >
        <div ng-transclude></div>

        <div ng-show="$ctrl.loading" class="loading">
          <div><i class="fa fa-lg fa-spinner fa-spin"></i></div>
        </div>
      </div>
    `,
  });
})();
