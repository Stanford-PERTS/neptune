/* global util */

(function () {

  'use strict';

  /**
   * @ngdoc module
   * @name nepCookies
   * @description
   *    Utility module for namespacing the functionality of $cookies. Rather
   *    than providing access to all cookies in the browser, only acts on those
   *    prefixed with the module name, e.g. myModule.fooCookie
   *
   *    Must be instantiated as a separate factory within the module where
   *    you'd like to use it.
   *
   *    Example:
   *
   *    angular
   *      // require in your module
   *      .module('myApp', ['nepCookies'])
   *      // instantiate as a factory within the module
   *      .factory('myCookies', ['ModuleCookies', function (ModuleCookies) {
   *        return new ModuleCookies('myApp');
   *      }])
   *      // use it to set/get namespaced cookies
   *      .controller('myCtrl', ['myCookies', function (myCookies) {
   *        myCookies.put('foo');  // actually puts a cookie named myApp.foo
   *        var all = myCookies.getAll();  // ignores cookies w/o prefix
   *      }]);
   */

  var nepCookies = angular.module(
    'nepCookies',
    ['ngCookies']
  );

  /**
   * @ngdoc factory
   * @name nepCookies.factory:ModuleCookies
   * @description
   *    ModuleCookies is a constructor. Use it to make your own factory with
   *    your module name as the namespace. See example use above.
   */

  nepCookies.factory('ModuleCookies', [
    '$cookies',
    function ($cookies) {

      function ModuleCookies(moduleName) {
        this.moduleName = moduleName;
      }

      ModuleCookies.prototype.fullCookieName = function (partialName) {
        return this.moduleName + '.' + partialName;
      };

      ModuleCookies.prototype.partialCookieName = function (fullName) {
        return fullName.slice(this.moduleName.length + 1);  // +1 for the dot
      };

      ModuleCookies.prototype.get = function (key) {
        return $cookies.get(this.fullCookieName(key));
      };

      ModuleCookies.prototype.put = function (key, value) {
        return $cookies.put(this.fullCookieName(key), value);
      };

      ModuleCookies.prototype.remove = function (key) {
        return $cookies.remove(this.fullCookieName(key));
      };


      ModuleCookies.prototype.getAll = function () {
        // Ignores cookies outside the namespace.

        var r = new RegExp('^' + this.moduleName);
        var cookieHash = {};
        util.forEachObj($cookies.getAll(), function (key, value) {
          if (r.test(key)) {
            cookieHash[this.partialCookieName(key)] = value;
          }
        }, this);

        return cookieHash
      };

      ModuleCookies.prototype.removeAll = function () {
        util.forEachObj(this.getAll(), function (key, value) {
          this.remove(key);
        }, this);
      };



      return ModuleCookies;
    }
  ]);

}());
