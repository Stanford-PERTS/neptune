(function () {
  'use strict';

  angular.module('appParticipate').config([
    '$locationProvider',
    configureModule
  ]);

  function configureModule($locationProvider) {

    // Angular url location w/o preceeding '#'
    $locationProvider.html5Mode(true);

  }

}());
