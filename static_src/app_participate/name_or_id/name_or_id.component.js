(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name appParticipate.component:nepNameOrId
   * @description
   *    Form to identify a participant based on a single text field.
   */

  window.ngModule
    .component('nepNameOrId', {
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
      template: require('./name_or_id.view.html'),
    })
    .directive('nepStripToken', stripTokenDirective);

  function stripToken(rawToken) {
    // Clean up user input of tokens.
    // Token should be lowercase alpha numeric characters without whitespace.
    return typeof rawToken !== 'string'
      ? undefined
      : rawToken.toLowerCase().replace(/[^a-z0-9]/g, '');
  }

  function stripTokenDirective() {
    return {
      restrict: 'A',
      require: 'ngModel',
      link(scope, element, attrs, ngModel) {
        if (!ngModel) {
          console.error('nepStripToken directive requires ngModel');
          return;
        }
        ngModel.$parsers.push(stripToken);
      },
    };
  }
})();
