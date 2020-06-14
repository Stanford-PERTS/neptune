(function () {
  'use strict';

  window.ngModule.component('uiProjectCohortName', {
    transclude: true,
    template: `
      <div class="ProjectCohortName">
        <h2 ng-transclude></h2>
      </div>
    `,
  });
})();
