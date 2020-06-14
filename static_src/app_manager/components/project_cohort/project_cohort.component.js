import getShortUid from 'utils/getShortUid';

(function() {
  'use strict';

  window.ngModule.component('nepProjectCohort', {
    bindings: {},
    controller: ProjectCohortController,
    template: require('./project_cohort.view.html'),
  });

  function ProjectCohortController(
    $state,
    $transitions,
    $rootScope,
    $q,
    $log,
    User,
    ProjectCohort,
    Program,
    Project,
    Organization,
    Checkpoint,
    Survey,
    Task,
    Title,
    Dashboard,
  ) {
    const vm = this;

    let deregisterTransitions;

    vm.$onInit = function() {
      const projectCohortId = getShortUid($state.params.projectCohortId);

      const includeTasks = true;
      // vm.loaded is a promise to help children know when they have all parent
      // dependencies.
      vm.loaded = Dashboard.getProjectDataRow(projectCohortId, includeTasks)
        .then(placeEntitiesOnScope)
        .then(convertDashboardToTasklist)
        .then(loaded => {
          const program = $q
            .when(loaded.projectCohort)
            .then(getProgramByProjectCohort)
            .then(placeProgramOnScope)
            .then(addProgramNameToTitle);
          const tasklist = $q
            .when(loaded)
            .then(placeCheckpointsOnScope)
            .then(placeTasksOnScope)
            .then(placeSurveysOnScope)
            .then(updateTaskStatus)
            .then(updateCheckpointStatus)
            .then(updateSurveyStatus)
            .then(redirectToCheckpoint);
          return $q.all([program, tasklist]).then(() => loaded);
        });
    };

    vm.$onDestroy = function() {
      deregisterTransitions();
    };

    deregisterTransitions = $transitions.onSuccess(
      { to: 'dashboard.tasks.**' },
      () => {
        redirectToCheckpoint();
      },
    );

    function placeEntitiesOnScope(dashboardData) {
      vm.projectCohort = dashboardData.projectCohort;
      vm.organization = dashboardData.organization;
      vm.project = dashboardData.project;
      vm.surveys = dashboardData.surveys;
      return dashboardData;
    }

    function convertDashboardToTasklist(dashboardData) {
      const d = dashboardData;
      const flatTasks = [].concat.apply(
        [],
        d.surveyCheckpoints.map(c => c.tasks),
      );

      return {
        organization: {
          organization: d.organization,
          checkpoints: [d.organizationCheckpoint],
          tasks: d.organizationCheckpoint.tasks,
        },
        project: {
          project: d.project,
          checkpoints: [d.projectCheckpoint],
          tasks: d.projectCheckpoint.tasks,
        },
        projectCohort: d.projectCohort,
        surveys: {
          surveys: d.surveys,
          checkpoints: groupByParentId(d.surveyCheckpoints),
          tasks: groupByParentId(flatTasks),
        },
      };
    }

    // Program Data
    function getProgramByProjectCohort(projectCohort) {
      return Program.get({ label: projectCohort.program_label }).$promise;
    }

    function placeProgramOnScope(program) {
      vm.program = program;
      return program;
    }

    function addProgramNameToTitle(program) {
      Title.setDynamic(program.name);
    }

    // Organization Data
    function getOrganizationDataByProjectCohort(projectCohort) {
      const organization = Organization.get({
        id: projectCohort.organization_id,
      });

      const organizationCheckpoints = organization.$promise.then(
        org => Checkpoint.queryBy(org).$promise,
      );

      const organizationTasks = organization.$promise.then(
        org => Task.queryBy(org).$promise,
      );

      return $q.all({
        organization,
        checkpoints: organizationCheckpoints,
        tasks: organizationTasks,
      });
    }

    function placeOrganizationOnScope(organizationData) {
      vm.organization = organizationData.organization;
      return organizationData;
    }

    // Project Data
    function getProjectDataByProjectCohort(projectCohort) {
      const project = Project.get({
        id: projectCohort.project_id,
      });

      const projectCheckpoints = projectCohort.$promise.then(
        pc => Checkpoint.queryByProject({ id: pc.project_id }).$promise,
      );

      const projectTasks = projectCohort.$promise.then(
        pc => Task.queryByProject({ id: pc.project_id }).$promise,
      );

      return $q.all({
        project,
        checkpoints: projectCheckpoints,
        tasks: projectTasks,
      });
    }

    function placeProjectOnScope(projectData) {
      vm.project = projectData.project;
      return projectData;
    }

    // Survey Data
    function getSurveyDataByProjectCohort(projectCohort) {
      const surveys = Survey.queryByProjectCohort({ id: projectCohort.uid });

      const surveysCheckpoints = surveys.$promise.then(ss =>
        // Some Programs may have multiple Surveys,
        // so we need to map Checkpoints
        $q.all(ss.map(s => Checkpoint.queryBySurvey({ id: s.uid }).$promise)),
      );

      const surveysTasks = surveys.$promise.then(ss =>
        // Some Programs may have multiple Surveys,
        // so we need to map Tasks
        $q.all(ss.map(s => Task.queryBySurvey({ id: s.uid }).$promise)),
      );

      return $q.all({
        surveys,
        checkpoints: surveysCheckpoints,
        tasks: surveysTasks,
      });
    }

    // Update Task Status
    // Marks each task with an isForbidden flag.
    // Marks task with isCurrent true, if it's the next task.
    function updateTaskStatus() {
      let foundNextTask = false;

      vm.tasks.forEach(task => {
        // Set isForbidden
        task.isForbidden = !task.non_admin_may_edit && User.isNonAdmin();

        // Hide controls if hidden from non-admins
        task.isDataHidden = task.data_admin_only_visible && User.isNonAdmin();

        // Set isCurrentTask
        task.isCurrent = false;

        const isCurrent =
          !foundNextTask && task.status === 'incomplete' && !task.isForbidden;

        if (isCurrent) {
          task.isCurrent = true;
          vm.nextTaskUid = task.uid;

          foundNextTask = true;
        }
      });
    }

    // Update Checkpoint Status
    // This function updates both the "source" checkpoint status (status) and
    // "view model" checkpoint status (status_vm). Both versions are being
    // tracked: the source so that Checkpoint.update calls occur properly and
    // the view model for friendly display.
    function updateCheckpointStatus() {
      let foundNextCheckpoint = false;

      vm.checkpoints.forEach(checkpoint => {
        // Calculate for server.
        const tasks = vm.tasks.filter(
          task => task.checkpoint_id === checkpoint.uid,
        );
        checkpoint.status = getCheckpointStatusFromTasks(tasks);

        // Calculate for view.
        const viewTasks = vm.tasks.filter(
          task => task.checkpoint_id_vm === checkpoint.uid,
        );
        checkpoint.status_vm = getCheckpointStatusFromTasks(viewTasks);

        // The view's version of the checkpoint status hides "waiting" if
        // we are an org admin. Other admins see the checkpoint as needing
        // attention.
        if (
          checkpoint.status_vm === Checkpoint.WAITING_STATUS &&
          User.isNonAdmin()
        ) {
          checkpoint.status_vm = Checkpoint.COMPLETE_STATUS;
        }

        // Mark checkpoint with isCurrent flag.
        const isCurrent =
          !foundNextCheckpoint &&
          checkpoint.status === Checkpoint.INCOMPLETE_STATUS &&
          checkpoint.isVisible;

        if (isCurrent) {
          checkpoint.isCurrent = true;
          vm.nextCheckpointShortUid = checkpoint.short_uid;

          foundNextCheckpoint = true;
        }
      });

      // If we didn't mark a checkpoint with isCurrent, then just set the last
      // checkpoint as isCurrent. The assumption is that users will probably want
      // to see their participation and reports.
      if (!foundNextCheckpoint) {
        vm.nextCheckpointShortUid = vm.checkpoints
          .filter(checkpoint => checkpoint.isVisible)
          .last().short_uid;
      }
    }

    /**
     * Checks if survey status/readiness needs to change in response to a task
     * update. This happens if the update completes a task such that all tasks
     * prior to the survey's monitor task are complete.
     * Note that this used to be done in the controller of the monitor task, but
     * then code didn't run if that task wasn't visible, which is often the case
     * when the monitor task is at the beginning of a step, see #925.
     */
    function updateSurveyStatus() {
      const task = vm.tasks.find(t => t.isCurrent);

      if (!task || task.data_type !== 'monitor' || task.attachment) {
        // Non-monitor tasks don't update surveys.
        // Monitor tasks with attachments have already done their work.
        return;
      }

      // Are all previous checkpoints complete?
      const ckpt = vm.checkpoints.find(c => c.uid === task.checkpoint_id);
      const prevCkpts = vm.checkpoints.slice(0, vm.checkpoints.indexOf(ckpt));
      const allPreviousComplete = prevCkpts.every(
        c => c.status === Checkpoint.COMPLETE_STATUS,
      );

      // The monitor task stores the survey status.
      task.attachment = allPreviousComplete
        ? Survey.READY_STATUS
        : Survey.NOT_READY_STATUS;

      // Update the related survey.
      handleSpecialTaskUpdates(task);
    }

    function placeSurveysOnScope(data) {
      vm.surveys = data.surveys.surveys;
      return data;
    }

    // Place Tasks on Scope
    // While placing tasks onto scope, this function also corrects the
    // checkpoint_id for Project Cohort tasks. For all vm display, use the
    // checkpoint_id_vm property. The original checkpoint_id is retained for
    // Task.update calls.
    function placeTasksOnScope(data) {
      vm.tasks = [];

      // Place Organization Tasks on Scope
      data.organization.tasks.forEach(task => {
        task.checkpoint_id_vm = task.checkpoint_id;
        vm.tasks.push(task);
      });

      // Place Project Tasks on Scope
      // -- We display Project tasks in the first Survey Checkpoint.
      // -- Assumption: there is a Survey Checkpoint
      data.project.tasks.forEach(task => {
        task.checkpoint_id_vm = data.surveys.checkpoints[0][0].uid;
        vm.tasks.push(task);
      });

      // Place Survey Tasks on Scope
      data.surveys.tasks.forEach(survey => {
        survey.forEach(task => {
          task.checkpoint_id_vm = task.checkpoint_id;
          vm.tasks.push(task);
        });
      });

      return data;
    }

    // Place Checkpoints in Scope
    // While placing checkpoints onto scope, this function also adds an
    // isVisible flag that can be used in the vm to hide the Project checkpoint
    // that we don't want to display. Project tasks are being displayed under
    // the first Survey Checkpoint.
    function placeCheckpointsOnScope(data) {
      vm.checkpoints = [];

      // For UI display of steps ("Step 1, Step 2, etc."). Only counting
      // Checkpoints that are visible.
      let step = 1;

      // Place Organization Tasks on Scope
      data.organization.checkpoints.forEach(checkpoint => {
        checkpoint.isVisible = true;
        checkpoint.step = step++;
        vm.checkpoints.push(checkpoint);
      });

      // Handle Project Checkpoints
      // -- Mark Project Checkpoints as not isVisible so that they won't show
      // -- up in the view. We are displaying the tasks that belong to this
      // -- Checkpoint under the first Survey Checkpoint.
      data.project.checkpoints.forEach(checkpoint => {
        checkpoint.isVisible = false;
        vm.checkpoints.push(checkpoint);
      });

      // Place Survey Tasks on Scope
      data.surveys.checkpoints.forEach(survey => {
        survey.forEach(checkpoint => {
          checkpoint.isVisible = true;
          checkpoint.step = step++;
          vm.checkpoints.push(checkpoint);
        });
      });

      return data;
    }

    // Redirects to the next Checkpoint if we haven't yet specified one in
    // state.
    function redirectToCheckpoint() {
      if ($state.current.name === 'dashboard.tasks') {
        $state.go(
          'dashboard.tasks.checkpoints',
          { checkpointId: vm.nextCheckpointShortUid },
          { location: 'replace' },
        );
      } else if ($state.includes('dashboard.tasks.checkpoints')) {
        redirectPastInvisibleCheckpoint();
      }
    }

    function redirectPastInvisibleCheckpoint() {
      vm.getCheckpoints().then(checkpoints => {
        // Find the current checkpoint and note the index.
        const current = checkpoints.find(c =>
          c.uid.includes($state.params.checkpointId),
        );
        const index = checkpoints.indexOf(current);

        // If it's invisible, redirect to the next one, keeping other
        // parameters the same.
        if (!current.isVisible) {
          const nextCheckpoint = checkpoints[index + 1];
          $state.go(
            $state.current.name,
            { checkpointId: nextCheckpoint.short_uid },
            { location: 'replace' },
          );
        }
      });
    }

    // Update Task
    vm.updateTask = function(task) {
      // Get index of task in tasks array for isComplete vm update below.
      const i = vm.tasks.indexOf(task);

      Task.update(task)
        .$promise.then(task => {
          // Some tasks require additional service updates
          handleSpecialTaskUpdates(task);

          // Update the vm
          vm.tasks[i].isComplete = task.isComplete;
          vm.tasks[i].isExpanded = !task.isComplete;
          updateTaskStatus();
          updateCheckpointStatus();
          updateSurveyStatus();
          updateExpandedTaskState();

          // Broadcast task update
          $rootScope.$broadcast('/Task/updated', task);

          return task;
        })
        .then(getCheckpointByTask)
        // We no longer save the modified checkpoint (the status may have
        // changed as tasks are updated) because the server takes care of that
        // as a side effect of saving the task. Rather we update the
        // client data to mirror what the server is doing. See #771.
        .then(checkpoint => {
          // Broadcast that checkpoint has updated so other views can sync up.
          $rootScope.$broadcast('/Checkpoint/updated', checkpoint);
        });
    };

    // Update Expanded Task
    // If the task marked isCurrent is on the current checkpoint, then update
    // state to redirect to that task.
    function updateExpandedTaskState() {
      const nextTaskOnCurrentCheckpoint = vm.tasks.find(task => {
        const taskShortCheckpointUid = getShortUid(task.checkpoint_id_vm);

        return (
          taskShortCheckpointUid === $state.params.checkpointId &&
          !task.isComplete &&
          !task.isForbidden
        );
      });

      if (nextTaskOnCurrentCheckpoint) {
        $state.go('.', { taskId: nextTaskOnCurrentCheckpoint.uid });
      } else {
        $state.go('projectCohorts.checkpoints');
      }
    }

    // Get the Checkpoint associated with the `task`.
    function getCheckpointByTask(task) {
      return vm.checkpoints.find(cp => cp.uid === task.checkpoint_id);
    }

    /**
     * Rules for how checkpoint status is derived from child tasks. Must be
     * the same as the logic in Checkpoint.get_status_from_tasks() in
     * checkpoint.py.
     *
     * @param Array of task resource objects
     * @returns string a checkpoint status value
     */

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
        return Checkpoint.COMPLETE_STATUS;
      } else if (allAssignedComplete) {
        return Checkpoint.WAITING_STATUS;
      }
      return Checkpoint.INCOMPLETE_STATUS;
    }

    /**
     * Some tasks require additional work to update Organizations, Projects,
     * or Surveys. This function handles those special tasks.
     */

    function handleSpecialTaskUpdates(task) {
      // Update Organization: Liaison
      if (task.label === 'organization__liaison') {
        Organization.get({ id: task.parent_id }, organization => {
          organization.liaison_id = task.attachment || null;
          Organization.update(organization);
        });
      }

      // Update Organization: Approved Status
      if (task.label === 'organization__approval') {
        Organization.get({ id: task.parent_id }, organization => {
          organization.status =
            task.status === 'complete' ? 'approved' : 'unapproved';
          organization.poid = task.attachment;
          Organization.update(organization);
        });
      }

      // @todo(chris): prob can find a way to abstract this pattern of
      // setting an entity property of the same name as the label.

      // Other label-based updates have to match on substrings because
      // labels are often program-specific, but the desired behavior exists
      // across programs.
      // @todo(chris): it's probably fine to exclude the program abbreviation
      // in most task labels, the compiled bodies would still vary by program.

      // Update Project Cohort: Expected Participants
      if (task.label.includes('__expected_participants')) {
        vm.projectCohort.expected_participants = task.attachment;
        ProjectCohort.update(vm.projectCohort);
      }

      // Update Project Cohort: Expected Participants
      if (task.label.includes('__portal_quiz')) {
        // Don't put values that are "task internal" to the project cohort.
        // Things like incorrect responses are never meant to leave the task.
        if (!task.attachment.includes('incorrect')) {
          // Assuming this is a valid response, save it to the portal type.
          vm.projectCohort.portal_type = task.attachment;
          ProjectCohort.update(vm.projectCohort);
        }
      }

      // Update Project Cohort: Custom Portal URL
      if (task.label.includes('__custom_portal_url')) {
        vm.projectCohort.custom_portal_url = task.attachment;
        ProjectCohort.update(vm.projectCohort);
      }

      switch (task.data_type) {
        case 'monitor':
          vm.getSurveys(task.parent_id).then(survey => {
            survey.status = task.attachment || Survey.NOT_READY_STATUS;
            Survey.update(survey);
          });
          break;
        case 'survey_params':
          var surveyParams;
          try {
            // The task attachment should be a flat JSON dictionary.
            surveyParams = angular.fromJson(task.attachment);
          } catch (e) {
            // Catch to make sure a parse error doesn't break the page.
            $log.error(
              `Survey param task attachment must be valid JSON: ${
                task.attachment
              }`,
            );
          }
          angular.extend(vm.projectCohort.survey_params, surveyParams);
          ProjectCohort.update(vm.projectCohort);
          break;
      }
    }

    // Data API methods for child scopes. With no args, returns all available
    // surveys, in order. With optional surveyId arg, returns the requested
    // survey, if available, otherwise undefined.
    //
    // Used by requiring this controller eg
    // require: {parent: '^nepProjectCohort'}
    // ...
    // vm.parent.getSurveys().then(...)
    //
    // @todo(chris): remove the get-by-id aspect of this function, which is
    // redundant with the Survey service, as soon as we implement a "store"
    // object cache in such services. It's important that we
    // maintain a single shared object reference per id so that updates
    // propagate through the app, so getting a disconnected copy from the
    // (currently) reference-naive service won't work.
    vm.getSurveys = function(surveyId) {
      return vm.loaded.then(data => {
        if (surveyId) {
          return data.surveys.surveys.find(s => s.uid === surveyId);
        }
        return data.surveys.surveys;
      });
    };

    vm.getCheckpoints = function() {
      return vm.loaded.then(() => vm.checkpoints);
    };

    // groupByParentId will take a flattened array of entities and return them
    // grouped with entities that have the same parent_id.
    //
    // Example:
    //
    // const flattenedArray = [
    //   { parent_id: 'Survey_001', uid: 'Task_001' },
    //   { parent_id: 'Survey_001', uid: 'Task_002' },
    //   { parent_id: 'Survey_001', uid: 'Task_003' },
    //   { parent_id: 'Survey_002', uid: 'Task_004' },
    // ];
    //
    // const groupedArray = groupByParentId(flattenedArray);
    //
    // [
    //   [
    //     { parent_id: 'Survey_001', uid: 'Task_001' },
    //     { parent_id: 'Survey_001', uid: 'Task_002' },
    //     { parent_id: 'Survey_001', uid: 'Task_003' },
    //   ],
    //   [
    //     { parent_id: 'Survey_002', uid: 'Task_004' },
    //   ],
    // ]

    function groupByParentId(flattenEntityArray) {
      const grouped = [];
      let groupedIndex = undefined;
      let previousParentId = undefined;

      flattenEntityArray.forEach(entity => {
        const currentParentId = entity.parent_id;

        // Increment the groupedIndex if we have moved on to a new parent_id.
        if (currentParentId !== previousParentId) {
          // If this is the first entity, then groupIndex will be undefined, so
          // initialize it to 0, else increment it.
          groupedIndex = groupedIndex === undefined ? 0 : groupedIndex =+ 1;
        }

        // Add entity to grouped array.
        grouped[groupedIndex] = grouped[groupedIndex] || [];
        grouped[groupedIndex].push(entity);

        // Update previous parent_id for tracking/comparisons.
        previousParentId = currentParentId;
      });

      return grouped;
    }
  }
})();
