import getKind from 'utils/getKind';
import isStringNumeric from 'utils/isStringNumeric';

const taskService = ngModule => {
  ngModule.service('Task', function Task($http, $resourceWith, hostingDomain) {
    const TaskResource = $resourceWith(
      `//${hostingDomain}/api/tasks/:id`,
      { id: '@uid' },
      {
        update: {
          url: `//${hostingDomain}/api/tasks/:id`,
          method: 'PUT',
          transformRequest,
          transformResponse,
        },
        queryByOrganization: {
          url: `//${hostingDomain}/api/organizations/:id/tasks?n=100`,
          method: 'GET',
          isArray: true,
          transformResponse,
        },
        queryByProject: {
          url: `//${hostingDomain}/api/projects/:id/tasks?n=100`,
          method: 'GET',
          isArray: true,
          transformResponse,
        },
        queryBySurvey: {
          url: `//${hostingDomain}/api/surveys/:id/tasks?n=100`,
          method: 'GET',
          isArray: true,
          transformResponse,
        },
        queryByUser: {
          url: `//${hostingDomain}/api/users/:id/tasks?n=100`,
          method: 'GET',
          isArray: true,
          transformResponse,
        },
      },
    );

    /**
     * Determine which queryBy $resource call to use.
     * @param  {Object}   parent   Parent of task
     * @param  {Function} callback
     * @return {Object}            $resource "class" object
     */

    TaskResource.queryBy = function (parent, callback) {
      const kind = getKind(parent.uid);
      return this[`queryBy${kind}`]({ id: parent.uid }, callback);
    };

    TaskResource.COMPLETE_STATUS = 'complete';
    TaskResource.INCOMPLETE_STATUS = 'incomplete';
    TaskResource.FILE_SUBMITTED = 'submitted';
    TaskResource.FILE_ACCEPTED = 'accepted';
    TaskResource.FILE_REJECTED = 'rejected';

    /**
     * Angular transformResponse function.
     * https://docs.angularjs.org/api/ngResource/service/$resource
     * @param  {String} data serialized task array data
     * @return {Array}       deserialized task array data
     */
    function transformResponse(data) {
      const transformed = angular.fromJson(data);

      // Add meta data to tasks
      if (Array.isArray(transformed)) {
        transformed.forEach(task => {
          TaskResource.addTaskMetaData(task);
        });
      } else {
        TaskResource.addTaskMetaData(transformed);
      }

      return transformed;
    }

    /**
     * Add convenience variables onto a task for easier reference.
     *  - isComplete: task is complete, correct option
     *  - isTouched: task has been interacted with, correct or not
     */
    TaskResource.addTaskMetaData = function (task) {
      task.isComplete = task.status === TaskResource.COMPLETE_STATUS;

      // We want to cast `null` attachment values to false.
      task.isTouched = Boolean(task.isComplete || task.attachment);

      return task;
    };

    /**
     * Angular transformRequest function.
     * https://docs.angularjs.org/api/ngResource/service/$resource
     * @param  {Object} task task object to be transformed before update
     * @return {Object}      transformed task object
     */
    function transformRequest(task) {
      // Set the status of the task based on task.data_type
      task.status = transformIsComplete(isComplete(task));
      return angular.toJson(task);
    }

    /**
     * Helper function that converts true/false to 'complete'/'incomplete'
     * for posting back to the server for storing in the task.status field.
     * @param  {Boolean} status task status
     * @return {String}         'complete' if true, 'incomplete' if false
     */

    function transformIsComplete(status) {
      return status
        ? TaskResource.COMPLETE_STATUS
        : TaskResource.INCOMPLETE_STATUS;
    }

    /**
     * Determines if the provided task should be marked as complete or not.
     * This function is called on a Task update, so it's used to determine
     * if the task will be marked complete based on user input, not the
     * current state of the task from the server.
     * @param  {Object} task task object
     * @return {Boolean}
     */

    function isComplete(task) {
      switch (task.data_type) {
        // Buttons
        // -- complete as long as it's pressed, and we shouldn't be here if
        // -- the user didn't press the button ^_^
        case 'button':
          return true;

        // -- complete if the attachment is 'complete'; these kinds of
        // -- tasks can store other attachment values while still being
        // -- incomplete
        case 'monitor':
          return task.attachment === TaskResource.COMPLETE_STATUS;

        // File Uploads
        // -- complete if file submitted or accepted
        case 'file':
          try {
            const taskAttachment = angular.fromJson(task.attachment);
            const file = taskAttachment.gcs_path; // make sure there is a file
            const submitted =
              taskAttachment.status === TaskResource.FILE_SUBMITTED;
            const accepted =
              taskAttachment.status === TaskResource.FILE_ACCEPTED;
            return submitted || accepted;
          } catch (e) {
            // incomplete if there were errors
            return false;
          }

        // Input Fields or Textarea
        // -- complete as long as there is something entered
        case 'input':
        case 'input:text':
        case 'input:url':
        case 'input:date':
        case 'textarea':
          return Boolean(task.attachment);

        case 'survey_params':
          var valid = true;
          try {
            // The task attachment should be a flat JSON dictionary.
            angular.fromJson(task.attachment);
          } catch (e) {
            // Catch to make sure a parse error doesn't break the page.
            // Logged in nepProjectCohort.handleSpecialTaskUpdates().
            valid = false;
          }
          return valid;

        // Input Field, expecting a Number
        // -- complete if the value is a number
        case 'input:number':
          if (task.attachment && isStringNumeric(task.attachment)) {
            return true;
          }
          task.attachment = null; // null out, don't store non-numbers
          return false;

        // Radio or Quiz
        // -- complete if selected option doesn't contain the string
        // -- 'incorrect'. The difference in types is only in what
        // -- .btn-instruction appears.

        // Normal, any answer is okay.
        case 'radio':
        // Some answers are wrong.
        case 'radio:quiz':
        // No answer is wrong, per se, but some won't complete the task.
        case 'radio:conditional':
          return task.attachment && !task.attachment.includes('incorrect');
      }
    }

    return TaskResource;
  });
};

export default taskService;
