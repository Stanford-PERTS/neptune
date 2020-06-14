/* global util, moment, expect */

(function() {
  'use strict';

  var nepUtil = angular.module('nepUtil', []);

  nepUtil.factory('showAllWarnings', function() {
    return function showAllWarnings(form) {
      // The form.$error object stores invalid ng-model fields in lists keyed
      // by the type of error. For instance, if you have two blank required
      // fields, and one field whose entry doesn't match the ng-pattern, then
      // $error is {required: [field, field], pattern: [field]}
      util.forEachObj(form.$error, function(errorType, fields) {
        fields.forEach(function(errorField) {
          errorField.$setTouched();
          errorField.$setDirty();
        });
      });
    };
  });

  nepUtil.factory('formatDate', [
    function() {
      return function formatDate(str) {
        return new Date(str).toISOString().split('T')[0];
      };
    },
  ]);

  nepUtil.factory('getKind', [
    function() {
      return function getKind(uid) {
        return uid.split('_')[0];
      };
    },
  ]);

  nepUtil.factory('getShortUid', function() {
    /**
     * Given a UID or Short UID, returns the Short UID.
     * @param  {String} uid UID or Short UID
     * @return {String}     Short UID
     */
    return function getShortUid(uid) {
      if (!uid) {
        return undefined;
      }
      const splitIdentifier = uid.split('_');
      return splitIdentifier.length === 2 ? splitIdentifier[1] : uid;
    };
  });

  nepUtil.factory('getUrlKind', [
    'getKind',
    function(getKind) {
      return function getUrlKind(uid) {
        var kind = getKind(uid);
        var standing = true;
        // plural snake case
        return util.camelToSeparated(kind, '_', standing) + 's';
      };
    },
  ]);

  nepUtil.factory('displayPercent', function() {
    var round = function(value, decimals) {
      return Number(Math.round(value + 'e' + decimals) + 'e-' + decimals);
    };
    return function displayPercent(numer, denom, dbz) {
      // This makes the fuction play nice with one-time binding, because
      // angular considers a value "stable" as soon as it's not undefined.
      if (numer === undefined || denom === undefined) {
        return;
      }
      dbz = dbz === undefined ? '--' : dbz; // divide by zero symbol
      return denom === 0 ? dbz : round((numer / denom) * 100, 0);
    };
  });

  nepUtil.factory('deepRetrieveObjectProperty', function() {
    /**
     * Traverses into the `obj` using the `propertyString` to find the desired
     * property within `obj`. For example, given:
     *
     * obj = {
     *   liaison: { name: 'Java Script', email: 'java@script.com' },
     *   program: { name: 'Social-Belonging', label: 'cb17' },
     * };
     *
     * propertyString = 'liaison.email';
     *
     * We would be returned 'java@script.com'.
     *
     * @param  {Object} obj            The Object we want to traverse
     * @param  {String} propertyString The location within the Object we want
     * @return {Object}                If found, the value at property location
     * @return {undefined}             If not found
     */
    function deepRetrieveObjectProperty(obj, propertyString) {
      var currentObjectLocation = obj;
      var props = propertyString.split('.');

      props.every(currentProp => {
        if (currentObjectLocation[currentProp] !== undefined) {
          currentObjectLocation = currentObjectLocation[currentProp];
          return true;
        } else {
          currentObjectLocation = undefined;
          // Taking advantage of the fact that `.every` will stop interating
          // as soon as the callback returns `false`.
          return false;
        }
      });

      return currentObjectLocation;
    }

    return deepRetrieveObjectProperty;
  });

  nepUtil.factory('materializeModal', function() {
    // The jquery plugin from materializecss for opening modals doesn't work.
    // This imitates the effect of such.
    // Example:
    // function MyController(materializeModal) {
    //   this.myModal = materializeModal($('#my-div'));
    //   this.myModal('open');
    //   this.myModal('close');
    // }
    return function(element) {
      return function materializeModal(openOrClose) {
        $(element).css({
          'z-index': openOrClose === 'open' ? 1003 : '',
          display: openOrClose === 'open' ? 'block' : '',
          opacity: openOrClose === 'open' ? 1 : '',
          transform: openOrClose === 'open' ? 'scaleX(1)' : '',
          top: openOrClose === 'open' ? '10%' : '',
        });
      };
    };
  });

  nepUtil.factory('parseLocalDateStr', function() {
    /**
     * Parse date string in the client's local time zone.
     *
     * @param {string} dateStr in YYYY-MM-DD format.
     * @returns {Date}
     */
    return function parseLocalDateStr(dateStr) {
      return moment(dateStr, 'YYYY-MM-DD').toDate();
    };
  });

  nepUtil.factory('parseUTCDateStr', function() {
    /**
     * Parse date string in UTC.
     *
     * @param {string} dateStr in YYYY-MM-DD format.
     * @returns {Date}
     */
    return function parseUTCDateStr(dateStr) {
      return moment.utc(dateStr, 'YYYY-MM-DD').toDate();
    };
  });

  nepUtil.factory('addQTools', function() {
    return function addQTools($q) {
      if (window.__karma__ === undefined) {
        console.error('Only use addQTools in testing!');
      }
      $q.prototype.assertFulfilled = function() {
        // Add a catch with an always-failing expect() so the assert fails
        // if the promise is ever rejected.
        return this.catch(error =>
          expect(`rejected reason: ${error}`).toBe('should not reject'),
        );
      };

      $q.prototype.assertRejected = function() {
        // Add a then with an always-failing expect() so the assert fails
        // if the proimse is NOT rejected.
        return this.then(value =>
          expect(`resolved value: ${value}`).toBe('should not resolve'),
        );
      };
    };
  });

  /**
   * Use when you have angular markup as a string and want to render it. We
   * use this in tasks whose templates are retrieved over AJAX.
   *
   * Angular expressions in the string are evaluated against the parent scope
   * because this directive doesn't declare an isolate scope.
   *
   * For example, if you have '{{ $ctrl.foo }} bar' (note: that's a string)
   * stored in scope.fooMarkup, and 'foo' stored in scope.foo, you can write
   * this in your view:
   *     <div nep-bind-markup="$ctrl.fooMarkup"></div>
   * and get this:
   *     <div>foo bar</div>
   */
  nepUtil.directive('nepBindMarkup', function($compile) {
    return {
      restrict: 'A',
      link: function(scope, element, attrs) {
        let ngMarkup = scope.$eval(attrs.nepBindMarkup);
        element.append($compile('<div>' + ngMarkup + '</div>')(scope));
      },
    };
  });

  // http://odetocode.com/blogs/scott/archive/2014/10/13/confirm-password-validation-in-angularjs.aspx
  nepUtil.directive('compareTo', function() {
    return {
      require: 'ngModel',
      scope: {
        otherModelValue: '=compareTo',
      },
      link: function(scope, element, attributes, ngModel) {
        ngModel.$validators.compareTo = function(modelValue) {
          return modelValue === scope.otherModelValue;
        };

        scope.$watch('otherModelValue', function() {
          ngModel.$validate();
        });
      },
    };
  });

  // Cribbed from:
  // https://docs.angularjs.org/error/ngModel/numfmt
  nepUtil.directive('stringToNumber', function() {
    return {
      require: 'ngModel',
      link: function(scope, element, attrs, ngModel) {
        ngModel.$parsers.push(function(value) {
          return '' + value;
        });
        ngModel.$formatters.push(function(value) {
          return parseFloat(value);
        });
      },
    };
  });

  nepUtil.filter('trustAsHtml', [
    '$sce',
    function($sce) {
      return $sce.trustAsHtml;
    },
  ]);

  nepUtil.filter('keyLength', function() {
    return function(obj) {
      return angular.isObject(obj) ? Object.keys(obj).length : 0;
    };
  });
})();
