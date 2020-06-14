(function () {
  'use strict';
  window.ngModule.component('uiSelectableCard', {
    bindings: {
      selected: '<',
      onClick: '&',
      closed: '<',
      disabled: '<',
    },
    transclude: true,
    template: `
      <ui-card closed="$ctrl.closed" disabled="$ctrl.disabled">
        <div class="CardSelect" ng-click="$ctrl.onClick()">
          <i class="fa fa-check" ng-show="$ctrl.selected"></i>
        </div>
        <div ng-transclude></div>
      </ui-card>
    `,
  });
})();
