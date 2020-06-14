(function () {
  'use strict';

  function DashboardOptionsController($state, User) {
    const vm = this;

    vm.$onInit = function () {
      vm.$state = $state;
      initUser();
    };

    function initUser() {
      vm.user = User.getCurrent();
      vm.isSuperAdmin = User.isSuperAdmin();
    }
  }

  window.ngModule.component('nepDashboardOptions', {
    bindings: {
      cardRows: '<',
      options: '<',

      resetDashboard: '&',
      selectAllVisible: '&',
      deselectAllVisible: '&',
    },
    controller: DashboardOptionsController,
    template: require('./dashboard_options.view.html'),
  });
})();
