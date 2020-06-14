(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name neptuneApp.component:nepSidenavOverlay
   * @description
   *   Overlay to prevent interacting with main content while side panels
   *   are active.
   */

  /**
   * @TODO Overlay should also appear when mobile nav appears.
   */

  window.ngModule.component('nepSidenavOverlay', {
    bindings: {

      /**
       * Boolean indicating if this Notifications panel is displayed.
       * @type {Boolean}
       */
      display: '<',

      /**
       * Function to invoke to dismiss the overlay.
       * @type {Function}
       */
      dismiss: '&',
    },
    controller: SidenavOverlayController,
    template: require('./sidenav_overlay.view.html'),
  });

  function SidenavOverlayController() {}
})();
