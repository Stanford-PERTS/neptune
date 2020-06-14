(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name neptuneApp.component:nepNotificationsPanel
   * @description
   *   The side panel that user's can slide out to view recent notifications.
   */

  /**
   * @TODO Move notifications into it's own service instead of passing in.
   * @TODO Using link for now, but I think we want to use ui-sref instead.
   * @TODO Archive notifications on click.
   * @TODO UX: Let user know there are no notifications if none.
   * @TODO UX: Add slide-in slide-out animations.
   */

  window.ngModule.component('nepNotificationsPanel', {
    bindings: {

      /**
       * An Array of notifications Objects. Each notification Object is
       * expected to contain a `msg` String and `uiSref` String.
       * @type {Array}
       */
      activeNotifications: '<notifications',

      /**
       * Boolean indicating if this Notifications panel is displayed.
       * @type {Boolean}
       */
      isNotificationsActive: '<',

      /**
       * Function to invoke to dismiss the overlay.
       * @type {Function}
       */
      closePanel: '&',
    },
    controller: NotificationsPanelController,
    template: require('./notifications_panel.view.html'),
  });

  function NotificationsPanelController() {
    const vm = this;

    // Dismiss a notification
    vm.dismiss = function (notification) {
      notification.dismissed = true;
      vm.activeNotifications.remove(notification);
      notification.$update();
    };
  }
})();
