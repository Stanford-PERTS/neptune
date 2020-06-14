// ui-card-panel
// A card pane is container used to present data. This should when you'd like to
// visually indicate that the content belong to a organization/project cohort.
// Example usage:
// <ui-card>
// Organization name
// </ui-card>
// <ui-card-panel>
// Organization details update form
// </ui-card-panel>

(function () {
  'use strict';
  window.ngModule.component('uiCardPanel', {
    transclude: true,
    bindings: {
      error: '<',
      loading: '<',
    },
    template: `
      <div class="CardPanel">
        <div ng-transclude></div>

        <div ng-show="$ctrl.loading" class="loading">
          <div><i class="fa fa-3x fa-spinner fa-spin"></i></div>
          <div>Loading...</div>
        </div>

        <div ng-show="$ctrl.error" class="error">
          <div><i class="fa fa-3x fa-exclamation-triangle"></i></div>
          <div>{{ $ctrl.error }}</div>
        </div>
      </div>
    `,
  });
})();
