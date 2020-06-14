(function () {
  'use strict';

  window.ngModule.controller(
    'ApproveParticipationController',
    function ApproveParticipationController(
      $scope,
      $q,
      Checkpoint,
      Dashboard,
      Task,
      close,
      program,
      projectDataRows,
    ) {
      $scope.program = program;
      $scope.projectDataRows = projectDataRows;
      $scope.organization_names = projectDataRows
        .map(row => row.project.organization_name)
        .join(', ');

      $scope.loadingTasks = true;
      retrieveProjectApprovalTasks().then(() => ($scope.loadingTasks = false));

      /**
       * Retrieve project approval tasks for each projectDataRow.
       */
      function retrieveProjectApprovalTasks() {
        return $q.all(
          projectDataRows.map(row => Dashboard.getParticipationApprovalTask(row, false).then(
              task => {
                row.participationApprovalTask = task;
                return task;
              },
            )),
        );
      }

      /**
       * Approve project approval for each projectDataRow.
       */
      $scope.approveParticipation = function () {
        const approved = $q.all(
          projectDataRows.map(row => {
            row.participationApprovalTask.status = Task.COMPLETE_STATUS;
            return Task.put(row.participationApprovalTask)
              .then(task => Checkpoint.updateStatus({ id: task.checkpoint_id }))
              .then(() => Dashboard.updateProjectDataRow(row));
          }),
        );

        approved.then(() => {
          $scope.close();
        });
      };

      /**
       * Closes the modal window.
       */
      $scope.close = function () {
        close();

        // We also need to clean up $scope
        $scope.$destroy();
      };
    },
  );
})();
