export default ngModule => {
  function controller(Notification, User) {
    const vm = this;

    // // Notifications management

    // // All users want to see their notifications all the time, so keep them
    // // in the root scope.
    vm.notifications = [];

    if (User.getCurrent() && User.getCurrent().uid) {
      vm.notifications = Notification.queryByUser({
        id: User.getCurrent().uid,
        dismissed: false,
      });
    }

    vm.dismissedNotifications = [];

    vm.showDismissedNotifications = function () {
      vm.dismissedNotifications = Notification.queryByUser({
        id: User.getCurrent().uid,
        dismissed: true,
      });
    };

    vm.hideDismissedNotifications = function () {
      vm.dismissedNotifications = [];
    };

    vm.toggleNotifications = function () {
      vm.showNotifications = !vm.showNotifications;
    };

    // App State: Notifications and Mobile Nav Side Panels
    vm.hideSidePanels = function () {
      vm.isMobileNavActive = false;
      vm.isNotificationsActive = false;
    };

    vm.hideSidePanels(); // initially hide side panels

    vm.showMobileNav = function () {
      vm.hideSidePanels();
      vm.isMobileNavActive = true;
    };

    vm.showNotifications = function () {
      vm.hideSidePanels();
      vm.isNotificationsActive = true;
    };
  }

  const template = `
    <nep-navbar
      notifications="$ctrl.notifications"
      is-mobile-nav-active="$ctrl.isMobileNavActive"
      show-notifications="$ctrl.showNotifications()"
      show-mobile-nav="$ctrl.showMobileNav()"
      dismiss="$ctrl.hideSidePanels()">
    </nep-navbar>
    <main>
      <ui-view></ui-view>
    </main>
    <nep-notifications-panel
      notifications="$ctrl.notifications"
      is-notifications-active="$ctrl.isNotificationsActive"
      close-panel="$ctrl.hideSidePanels()">
    </nep-notifications-panel>
    <nep-footer></nep-footer>
    <nep-sidenav-overlay
      display="$ctrl.isNotificationsActive || $ctrl.isMobileNavActive"
      dismiss="$ctrl.hideSidePanels()">
    </nep-sidenav-overlay>
  `;

  ngModule.component('app', {
    controller,
    template,
  });
};
