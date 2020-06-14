// Angular controller survey session instructions.
//
// Must be able to display the program name, the survey name, and the
// participation code.
//
// The template is dynamic basic on the program label.

angular.module('neptuneApp').controller('SessionInstructionCtrl', [
  '$scope', '$stateParams', 'Program', 'ProjectCohort', 'Survey',
  function ($scope, $stateParams, Program, ProjectCohort, Survey) {

    'use strict';

    $scope.survey = Survey.get({id: $stateParams.surveyId}, function (s) {
      $scope.program = Program.get({label: s.program_label});
      $scope.projectCohort = ProjectCohort.get({id: s.project_cohort_id});
    });
  }
]);
