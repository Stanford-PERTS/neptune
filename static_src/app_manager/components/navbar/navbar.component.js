(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name neptuneApp.component:nepNavbar
   * @description
   *   The main navigation bar for the app.
   */

  /**
   * @TODO Move notifications into it's own service instead of passing in.
   * @TODO Make the hamburger menu (mobile) functional.
   */

  window.ngModule.component('nepNavbar', {
    bindings: {

      /**
       * An Array of notifications Objects. Each notification Object is
       * expected to contain a `msg` String and `uiSref` String.
       * @type {Array}
       */
      notifications: '<',

      /**
       * Boolean indicating if this Notifications panel is displayed.
       * @type {Boolean}
       */
      isMobileNavActive: '<',

      /**
       * Boolean indicating if this Notifications panel is displayed.
       * @type {Boolean}
       */
      showNotifications: '&',

      /**
       * Boolean indicating if the mobile nav is displayed.
       * @type {Boolean}
       */
      showMobileNav: '&',

      /**
       * Function to invoke to dismiss the overlay.
       * @type {Function}
       */
      dismiss: '&',
    },
    controller: NavbarController,
    template: require('./navbar.view.html'),
  });

  function NavbarController(User) {
    const vm = this;

    vm.$onInit = function () {
      vm.isLoggedIn = User.loggedIn();
      vm.isSuperAdmin = User.isSuperAdmin();

      const name = User.getCurrent().email;
      vm.name = name ? name.split('@')[0] : undefined;

      vm.login = User.login;
      vm.logout = User.logout;
    };

    vm.nonzeroActiveNotifications = function () {
      return vm.notifications.filter(n => !n.dismissed).length > 0;
    };
  }
})();
