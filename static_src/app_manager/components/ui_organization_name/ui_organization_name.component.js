(function () {
  'use strict';

  window.ngModule.component('uiOrganizationName', {
    transclude: true,
    template: `
      <div class="OrganizationName"><h1 ng-transclude></h1></div>
    `,
  });
})();
