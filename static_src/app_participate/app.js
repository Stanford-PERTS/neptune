// Module for admitting participants to programs.

(function () {
  'use strict';

  var appParticipate = angular.module(
    'appParticipate',
    [
      'ui.router',
      'nepUtil',
      'nepApi',
      'nepCookies',
      'templates-app_participate',
      'validation.match',
    ]
  );

  appParticipate.run([
    '$rootScope', '$state',
    function ($rootScope, $state) {
      $rootScope.$state = $state;
    }
  ]);

  /**
   * @ngdoc factory
   * @name appParticipate.factory:portalCookies
   * @description
   *    Getter/setter for cookies namespaced for appParticipate.
   */

  appParticipate.factory('portalCookies', [
    'ModuleCookies',
    function (ModuleCookies) {
      return new ModuleCookies('appParticipate');
    }
  ]);

}());
