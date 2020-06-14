import getKind from 'utils/getKind';

const checkpointService = ngModule => {
  ngModule.service('Checkpoint', function Checkpoint(
    $q,
    $resource,
    Task,
    User,
    queryByCache,
    hostingDomain,
  ) {
    // @todo: abstract this into a layer above $resource that lets you set
    // queryByX for arbitrary X, and uses queryByCache on all of them.

    const CheckpointResource = $resource(
      `//${hostingDomain}/api/checkpoints/:id`,
      { id: '@uid' },
      {
        // These get checkpoints by their parent, e.g. checkpoints whose
        // immediate parent is an org and that are part of that org's
        // tasklist.
        _queryByOrganization: {
          url: `//${hostingDomain}/api/organizations/:id/checkpoints`,
          method: 'GET',
          isArray: true,
        },
        _queryByProject: {
          url: `//${hostingDomain}/api/projects/:id/checkpoints`,
          method: 'GET',
          isArray: true,
        },
        _queryBySurvey: {
          url: `//${hostingDomain}/api/surveys/:id/checkpoints`,
          method: 'GET',
          isArray: true,
        },
        queryProjectCheckpointsByProgram: {
          url: `//${hostingDomain}/api/checkpoints`,
          method: 'GET',
          isArray: true,
          params: {
            parent_kind: 'Project',
          },
        },
        querySurveyCheckpointsByProgram: {
          url: `//${hostingDomain}/api/checkpoints`,
          method: 'GET',
          isArray: true,
          params: {
            parent_kind: 'Survey',
            n: 5000,
          },
        },
        queryOrganizationCheckpointsByProgram: {
          url: `//${hostingDomain}/api/checkpoints`,
          method: 'GET',
          isArray: true,
          params: {
            parent_kind: 'Organization',
          },
        },
        update: {
          method: 'PUT',
        },
      },
    );

    CheckpointResource.COMPLETE_STATUS = Task.COMPLETE_STATUS;
    CheckpointResource.INCOMPLETE_STATUS = Task.INCOMPLETE_STATUS;
    CheckpointResource.WAITING_STATUS = 'waiting';

    CheckpointResource.queryBy = function(parent, callback) {
      const kind = getKind(parent.uid);
      return this[`queryBy${kind}`]({ id: parent.uid }, callback);
    };

    CheckpointResource.queryByOrganization = function(params, callback) {
      // @todo: the callback is being provided the non-referenced result set.
      // For now, always use the returned result set rather than the argument
      // to the callback. Eventually should fix.
      const resultSet = this._queryByOrganization(params, callback);
      return queryByCache(resultSet, `${params.id}/checkpoints`);
    };

    CheckpointResource.queryByProject = function(params, callback) {
      const resultSet = this._queryByProject(params, callback);
      return queryByCache(resultSet, `${params.id}/checkpoints`);
    };

    CheckpointResource.queryBySurvey = function(params, callback) {
      const resultSet = this._queryBySurvey(params, callback);
      return queryByCache(resultSet, `${params.id}/checkpoints`);
    };

    /**
     * Retrieve Task with desired label from Checkpoint.
     * id: Checkpoint UID
     * label: Task label
     */
    CheckpointResource.getTaskWithLabel = function({ id, label }) {
      return CheckpointResource.get({ id })
        .$promise.then(getTasksfromCheckpoint)
        .then(tasks => tasks.find(t => t.label.includes(label)));
    };

    /**
     * Update Checkpoint Status based on Checkpoint Tasks.
     * id: checkpoint_id
     */
    CheckpointResource.updateStatus = function({ id }) {
      return CheckpointResource.get({ id }).$promise.then(
        updateCheckpointStatusFromTasks,
      );
    };

    function updateCheckpointStatusFromTasks(checkpoint) {
      return $q
        .when(getTasksfromCheckpoint(checkpoint))
        .then(getCheckpointStatusFromTasks)
        .then(checkpointStatus => {
          checkpoint.status = checkpointStatus;
          return checkpoint.$update();
        });
    }

    function getTasksfromCheckpoint(checkpoint) {
      if (User.isSuperAdmin()) {
        // supers have access to batch queries
        return $q
          .when(getTaskIdsFromCheckpoint(checkpoint))
          .then(taskIds =>
            Task.query({ uid: taskIds }).$promise.then(tasks => tasks),
          );
      }
      // non-admins don't have batch queries, so we single query tasks
      return $q
        .when(getTaskIdsFromCheckpoint(checkpoint))
        .then(taskIds => $q.all(taskIds.map(id => Task.get({ id }).$promise)));
    }

    function getTaskIdsFromCheckpoint(checkpoint) {
      return angular.fromJson(checkpoint.task_ids);
    }

    function getCheckpointStatusFromTasks(tasks) {
      let allComplete = true;
      let allAssignedComplete = true;

      tasks.forEach(task => {
        if (task.status !== Task.COMPLETE_STATUS) {
          allComplete = false;
          if (task.non_admin_may_edit) {
            allAssignedComplete = false;
          }
        }
      });

      if (allComplete) {
        return CheckpointResource.COMPLETE_STATUS;
      } else if (allAssignedComplete) {
        return CheckpointResource.WAITING_STATUS;
      }
      return CheckpointResource.INCOMPLETE_STATUS;
    }

    return CheckpointResource;
  });
};

export default checkpointService;
