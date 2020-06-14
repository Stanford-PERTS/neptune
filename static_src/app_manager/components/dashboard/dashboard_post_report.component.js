(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name neptuneApp.component:nepDashboardPostReport
   * @description
   *   Allows super admins to upload many reports and attach them to report
   *   tasks.
   *
   *   Select inputs allow user to choose a cohort, checkpoint label, and task
   *   label, in addition to the known program. This limits the scope of the
   *   reports to a group of project cohorts. The file upload control accepts
   *   pdfs with the project cohort id at the end of the file name.
   *
   *   The component queries for checkpoints that might match the specified
   *   project cohorts, then extracts the correct task id from each. Then the
   *   file is attached to the task and the task is marked complete.
   */

  window.ngModule.component('nepDashboardPostReport', {
    bindings: {
      programLabel: '<',
    },
    controller: DashboardPostReportController,
    template: require('./dashboard_post_report.view.html'),
  });

  function DashboardPostReportController(
    $timeout,
    $q,
    Program,
    PostReportService,
  ) {
    const vm = this;
    const service = PostReportService;

    vm.checkpointsLoaded = false;

    vm.$onInit = function () {
      vm.program = Program.get({ label: vm.programLabel });
      vm.program.$promise.then(() => {
        service.setProgram(vm.program);
        vm.checkpointTemplates = service.listCheckpointTemplates(vm.program);
      });
    };

    /**
     * Non-pure; tried to put most of the view-related side effects here.
     * @param {string} checkpointLabel - checkpoint label
     */
    vm.checkpointLabelChange = function (checkpointLabel) {
      vm.busy = true;
      vm.taskTemplates = service.listTaskTemplates(checkpointLabel);
      vm.checkpoints = service.getCheckpointsByLabel(
        vm.program.label,
        vm.cohortLabel,
        checkpointLabel,
      );
      vm.checkpoints.$promise.then(() => {
        vm.checkpointsLoaded = true;
        vm.busy = false;
      });
    };

    /**
     * Upload a list of files to specified tasks.
     * vm.checkpoints must have resolved; enforced in ngDisabled of upload
     * button.
     * @param {Array} files - of ngUploadFiles
     * @param {Array} errFiles - not sure, see ngUploadFiles docs
     * @param {string} cLabel - checkpoint label
     * @param {string} tLabel - task label
     */
    vm.upload = function (files, errFiles, cLabel, tLabel) {
      // Where is the task within the checkpoint? This is the same for all
      // checkpoints in the program.
      const taskIndex = service.getTaskIndex(cLabel, tLabel);

      vm.reportFiles = [];
      vm.errFiles = [];
      vm.busy = true;

      const fileError = function (msg, file) {
        console.error(msg || 'Error with file:', file.name);
        files.remove(file);
        errFiles.push(file);
      };

      files.forEach(file => {
        const pcid = service.projectCohortFromFile(file);

        const ckpt = vm.checkpoints.find(c => c.project_cohort_id === pcid);
        if (!ckpt) {
          fileError('Could not find checkpoint for file:', file);
          return;
        }

        const taskId = angular.fromJson(ckpt.task_ids)[taskIndex];

        service.uploadFile(taskId, file).catch(httpResponse => {
          fileError(httpResponse.data, file);
        });
      });

      $q.all(files.map(f => f.upload)).finally(() => {
        vm.reportFiles = files;
        vm.errFiles = errFiles;
        vm.busy = false;
      });
    };
  }
})();
