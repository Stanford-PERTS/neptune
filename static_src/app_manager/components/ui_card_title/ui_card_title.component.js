(function () {
  'use strict';

  window.ngModule.component('uiCardTitle', {
    transclude: true,
    template: `
      <div class="CardTitle"><h1 ng-transclude></h1></div>
    `,
  });
})();
