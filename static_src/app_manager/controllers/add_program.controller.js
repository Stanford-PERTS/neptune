// Angular controller for add organization modals

/* global util */

angular.module('neptuneApp').controller('AddProgramCtrl', [
  '$scope', '$stateParams', 'User', 'Organization', 'Program', 'Project',
  function ($scope, $stateParams, User, Organization, Program, Project) {

    'use strict';

    $scope.organization = Organization.get({id: $stateParams.orgId});
    $scope.programs = Program.query();
    $scope.projects = Project.queryByOrganization({id: $stateParams.orgId});
    $scope.selectedProgram = undefined;

    $scope.selectProgram = function (program) {
      $scope.errorCode = null;
      $scope.programs.forEach(function (p) {
        p.selected = false;
      });
      program.selected = true;
      $scope.selectedProgram = program;
    };

    $scope.joinProgram = function() {

      $scope.busy = true;

      $scope.projects.forEach(function (project) {
        if (project.program_label === $scope.selectedProgram.label) {
          $scope.errorCode = 'already_associated';
        }
      });
      if ($scope.errorCode) {
        $scope.busy = false;
        return;
      }

      var newProject = new Project({
        organization_id: $stateParams.orgId,
        program_label: $scope.selectedProgram.label,
        liaison_id: User.getCurrent().uid
      });
      newProject.$save(function (response) {
        $scope.errorCode = null;
        $scope.busy = false;
        $('#addProgramModal').modal('hide');
        $scope.projects.push(newProject);
      });

    };
  }
]);
