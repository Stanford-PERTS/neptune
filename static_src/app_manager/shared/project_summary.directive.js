angular.module('neptuneApp')
  .directive('projectSummary', [
    'Organization', 'Checkpoint',
    function (Organization, Checkpoint) {

    'use strict';

    return {
      restrict: 'A',
      scope: {
        'project': '='
      },
      templateUrl: 'shared/project_summary.html',

      link: function(scope, element, attrs) {

        scope.organization = Organization.getName(
          {id: scope.project.organization_id});
        scope.checkpoints = Checkpoint.queryByProject(
          {id: scope.project.uid});

      }
    };

  }]);
