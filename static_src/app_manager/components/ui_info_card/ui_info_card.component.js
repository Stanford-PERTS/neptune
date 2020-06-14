(function () {
  'use strict';

  window.ngModule.component('uiInfoCard', {
    transclude: true,
    template: `
      <ui-card>
        <div class="InfoCard">
          <ng-transclude></ng-transclude>
        </div>
      </ui-card>
    `,
  });
})();
