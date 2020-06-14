// Controller for index.

angular.module('neptuneApp').controller('LandingCtrl', [
  '$scope', '$state', 'User',
  function ($scope, $state, User) {

    'use strict';

    var user = User.getCurrent();
    if (User.loggedIn()) {
      $state.go('dashboard', {}, {location: 'replace'});
    }

  }
]);
