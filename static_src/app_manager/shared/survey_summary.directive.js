// Handles rendering of a whole task list, using checkpoints and nested tasks.
angular.module('neptuneApp').directive('surveySummary', [
  'Checkpoint', 'Participation', 'displayPercent',
  function (Checkpoint, Participation, displayPercent) {
    'use strict';

    return {
      restrict: 'A',
      scope: {
        'survey': '=',
        'expectedParticipants': '='
      },
      templateUrl: 'shared/survey_summary.html',

      link: function(scope, element, attrs) {
        scope.checkpoints = Checkpoint.queryBySurvey({id: scope.survey.uid});
        scope.participation = Participation.queryBySurvey(
          {id: scope.survey.uid});

        scope.displayPercent = displayPercent;
      }
    };
  }
]);
