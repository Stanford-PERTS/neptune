(function () {
  'use strict';

  function OrganizationsController(Organization, User) {
    const vm = this;

    vm.$onInit = function () {
      initUser();

      vm.loading = true;

      Organization.queryByUser({ id: vm.user.uid }).$promise.then(
        organizations => {
          vm.assc_organizations = organizations.filter(org =>
            vm.user.assc_organizations.includes(org.uid),
          );

          vm.owned_organizations = organizations.filter(org =>
            vm.user.owned_organizations.includes(org.uid),
          );

          vm.loading = false;
        },
      );
    };

    function initUser() {
      vm.user = User.getCurrent();
      vm.isSuperAdmin = User.isSuperAdmin();
    }
  }

  window.ngModule.component('nepOrganizations', {
    controller: OrganizationsController,
    template: require('./organizations.view.html'),
  });
})();
