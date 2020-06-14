(function () {
  'use strict';

  window.ngModule.component('uiLoadingCard', {
    template: `
        <ui-info-card>
          <div><i class="fa fa-3x fa-spinner fa-spin"></i></div>
          <div>Loading...</div>
        </ui-info-card>
      `,
  });
})();
