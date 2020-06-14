(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name appParticipate.component:nepFirstMiLast
   * @description
   *    Form to identify a participant based on their name. Takes first and
   *    last name as text fields, and middle initial as either a single letter
   *    or blank if they mark the "I don't have a middle name" checkbox.
   *    Returns first two initials and stripped last name as the token,
   *    e.g. "Jane Doe" returns 'jdoe' and "John Q. Public" returns 'jqpublic'.
   */

  window.ngModule
    .component('nepFirstMiLast', {
      bindings: {

        /**
         * Parent can bind to this event. Called when token value changes.
         * @type {Function}
         */
        setToken: '&',
      },
      controller: FirstMiLastController,
      template: require('./first_mi_last.view.html'),
    })
    .directive('nepStripName', stripNameDirective);

  function FirstMiLastController() {
    const vm = this;

    vm.updateToken = function () {
      const firstInitial = vm.firstName ? vm.firstName.charAt(0) : '';
      const t = firstInitial + (vm.middleInitial || '') + (vm.lastName || '');
      vm.setToken({ token: t });
      vm.token = t;
    };
  }

  function stripName(rawName) {
    // Clean up user input of names.
    // Allow a full range of non-ascii letters, but still lowercase and strip
    // whitespace and puncutation.

    // http://stackoverflow.com/questions/4328500/how-can-i-strip-all-punctuation-from-a-string-in-javascript-using-regex#answer-25575009
    const punctuation = /[\u2000-\u206F\u2E00-\u2E7F\\'!"#$%&()*+,\-.\/:;<=>?@\[\]^_`{|}~]/g;

    return typeof rawName !== 'string'
      ? undefined
      : rawName
          .toLowerCase()
          // Remove all whitespace, digits, and punctuation
          .replace(/\s+/g, '')
          .replace(/0-9/g, '')
          .replace(punctuation, '');
  }

  function stripNameDirective() {
    return {
      restrict: 'A',
      require: 'ngModel',
      link(scope, element, attrs, ngModel) {
        if (!ngModel) {
          console.error('nepStripName directive requires ngModel');
          return;
        }
        ngModel.$parsers.push(stripName);
      },
    };
  }
})();
