(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name appParticipate.component:nepEmailConfirm
   * @description
   *    Form to identify a participant based on their email address; requested
   *    twice.
   */

  window.ngModule.component('nepEmailConfirm', {
    bindings: {

      /**
       * Parent can bind to this event. Called when token value changes.
       * @type {Function}
       */
      setToken: '&',

      /**
       * Optional text to display in form.
       * @type {string}
       */
      portalMessage: '<',
    },
    // controller: EmailConfirmController,
    template: require('./email_confirm.view.html'),
  });
})();
