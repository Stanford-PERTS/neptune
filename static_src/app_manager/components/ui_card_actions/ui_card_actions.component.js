(function () {
  'use strict';

  window.ngModule.component('uiCardActions', {
    transclude: true,
    template: `
      <div class="CardActions">
        <ng-transclude></ng-transclude>
      </div>
    `,
  });
})();
