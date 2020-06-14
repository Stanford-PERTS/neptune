// Angular controller for super admin organization index.

angular.module('neptuneApp').controller('ProgramIndexCtrl', [
  '$scope', 'Program',
  function ($scope, Program) {

    'use strict';

    // Get related resources
    $scope.programs = Program.query();

  }
]);
