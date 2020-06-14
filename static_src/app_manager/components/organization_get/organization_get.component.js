(function () {
  'use strict';

  function OrganizationGetController($state, Organization) {
    const vm = this;

    vm.$onInit = function () {
      vm.loading = true;

      Organization.get({ id: $state.params.organizationId }).$promise.then(
        organization => {
          vm.organization = organization;
          vm.loading = false;
        },
      );
    };
  }

  window.ngModule.component('nepOrganizationGet', {
    controller: OrganizationGetController,
    template: require('./organization_get.view.html'),
  });
})();
