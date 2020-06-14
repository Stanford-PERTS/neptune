{
  // From the end of the filename: the file extension, the short uid (which
  // should be of a project cohrot), and then any separator character that
  // isn't a valid short uid character.
  // Examples:
  // "Report ABCD1234.pdf"
  // "Report-ABCD1234.pdf"
  // "Report_ABCD1234.pdf"
  // "Report.ABCD1234.pdf"
  // "Report:ABCD1234.pdf"
  // "Report ProjectCohort_ABCD1234.pdf"
  const reportFilenamePattern = /[^A-Za-z0-9]([A-Za-z0-9]+)\.pdf$/;

  const service = function PostReportService(
    $timeout,
    hostingDomain,
    Upload,
    Checkpoint,
    Task,
  ) {
    'use strict';

    return {
      setProgram(program) {
        this.program = program;
      },

      /**
       * @returns {Array} flat, of all project and survey checkpoint templates
       *   in the program.
       */
      listCheckpointTemplates() {
        return this.program.surveys.reduce(
          (accumulator, current) =>
            accumulator.concat(current.survey_tasklist_template),
          this.program.project_tasklist_template,
        );
      },

      /**
       * Get either a checkpoint template or a task template.
       * @param {string} label - checkpoint or task label
       * @returns {Object} matching checkpoint or task template
       */
      getTemplateByLabel(label) {
        const checkpointTemplates = this.listCheckpointTemplates();
        let match = checkpointTemplates.find(c => c.label === label);
        if (match) {
          return match;
        } // else the label may be for a task

        const groupedTaskTemplates = checkpointTemplates.map(c => c.tasks);
        const taskTemplates = [].concat(...groupedTaskTemplates);
        match = taskTemplates.find(t => t.label === label);
        if (match) {
          return match;
        }
        throw new Error(`Label not found: ${label}`);
      },

      /**
       * @returns {Array} of task templates within specified checkpoint
       */
      listTaskTemplates(checkpointLabel) {
        const checkpointTemplate = this.getTemplateByLabel(checkpointLabel);
        return checkpointTemplate.tasks;
      },

      /**
       * Additionally scoped by program and cohort per the view.
       * @param {string} label - checkpoint label
       * @returns {Array} of checkpoint resources from API
       */
      getCheckpointsByLabel(programLabel, cohortLabel, checkpointLabel) {
        return Checkpoint.query({
          program_label: programLabel,
          cohort_label: cohortLabel,
          label: checkpointLabel,
        });
      },

      /**
       * Expects files are named with a certain convention, see
       * reportFilenamePattern.
       * @param {Object} file - from ngFileUpload
       * @returns {string} full uid for a project cohort.
       */
      projectCohortFromFile(file) {
        const [match, shortId] = reportFilenamePattern.exec(file.name) || [];
        return `ProjectCohort_${shortId}`;
      },

      /**
       * Get position of task id within checkpoint templates list of task_ids.
       * @param {string} cLabel - checkpoint label
       * @param {string} tLabel - task label
       * @returns {number} index of task within checkpoint, may be -1 if task not
       *   found.
       */
      getTaskIndex(cLabel, tLabel) {
        const checkpointTemplate = this.getTemplateByLabel(cLabel);
        const taskTemplate = this.getTemplateByLabel(tLabel);
        return checkpointTemplate.tasks.indexOf(taskTemplate);
      },

      /**
       * Upload a single file to the specified task.
       * @param {string} taskId - full task uid
       * @param {Object} file - ngFileUpload file
       * @returns {Object} promise re: upload request
       */
      uploadFile(taskId, file) {
        const task = new Task({
          uid: taskId,
          data_type: 'file',
          // Needed by server to send task notification with useful links.
          project_cohort_id: this.projectCohortFromFile(file),
        });

        file.upload = Upload.upload({
          url: `//${hostingDomain}/api/tasks/${taskId}/attachment`,
          data: { file },
        }).then(
          function uploadSuccessCallback(response) {
            // Send a PUT to mark the task as complete.
            // Must add the attachment status property, which doesn't come from
            // the server, so that the task service identifies this task as
            // complete.
            response.data.status = Task.FILE_SUBMITTED;
            task.attachment = angular.toJson(response.data);
            Task.put(task);

            // This is from ngFileUpload's code; not sure if it's necessary.
            $timeout(() => {
              file.result = response.data;
            });
          },
          null, // don't catch errors here
          function uploadNotifyCallback(evt) {
            file.progress = Math.min(
              100,
              parseInt((100.0 * evt.loaded) / evt.total),
            );
          },
        );

        return file.upload;
      },
    };
  };

  /**
   * @ngdoc service
   * @name neptuneApp.service:nepPostReportService
   * @description
   */
  window.ngModule.service('PostReportService', service);
}
