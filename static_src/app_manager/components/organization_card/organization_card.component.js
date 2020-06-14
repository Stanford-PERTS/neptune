(function () {
  'use strict';

  window.ngModule.component('nepOrganizationCard', {
    bindings: {
      loading: '<',
      organization: '<',
    },
    template: require('./organization_card.view.html'),
  });
})();
