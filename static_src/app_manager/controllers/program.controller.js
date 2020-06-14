// Angular controller for organization pages

angular.module('neptuneApp').controller('ProgramCtrl', [
  '$scope', '$stateParams', 'Program', 'Project',
  function ($scope, $stateParams, Program, Project) {

    'use strict';

    $scope.program = Program.get({label: $stateParams.programLabel});
    $scope.projects = Project.queryByProgram(
      {label: $stateParams.programLabel});

  }
]);
