angular.module('neptuneApp').controller('ProjectCtrl', [
  '$scope', '$stateParams', 'User', 'Organization', 'Project', 'ProjectCohort',
  'Survey',
  function ($scope, $stateParams, User, Organization, Project, ProjectCohort,
            Survey) {

    'use strict';

    $scope.user = User.getCurrent();
    $scope.projectId = $stateParams.projectId;  // easier for child directives
    $scope.project = Project.get({id: $scope.projectId}, function () {
      $scope.organization = Organization.getName(
        {id: $scope.project.organization_id});
      $scope.accountManager = User.getAccountManager(
        {projectId: $scope.project.uid});

      if (!User.isNonAdmin()) {
        // Allows for either super admins or program admins.
        $scope.programOwners = User.queryByProgram(
          {label: $scope.project.program_label});
      }
    });
    $scope.projectCohorts = ProjectCohort.queryByProject(
      {id: $scope.projectId});
    $scope.surveys = Survey.queryByProject({id: $scope.projectId});
  }
]);
