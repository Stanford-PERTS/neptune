import moment from 'moment';
import getKind from 'utils/getKind';
import isStringNumeric from 'utils/isStringNumeric';
import parseLocalDateStr from 'utils/parseLocalDateStr';

(function () {
  'use strict';

  /**
   * @TODO Handle collapsing/expanding tasks, currently hardcoded `active`.
   * @TODO Handle errors.
   */

  window.ngModule.component('nepTaskItem', {
    bindings: {
      task: '<',

      /**
       * Parent Organization object. Needed for letter of agreement links.
       * @type {Object}
       */
      parentOrganization: '<',

      /**
       * Program resource. Needed for organization tasks, where the task
       * definition in organization_tasks.py doesn't know what the program
       * will be.
       * @type {string}
       */
      program: '<',

      /**
       * Parent ProjectCohort object. Needed for some task behavior.
       * @type {Object}
       */
      parentProjectCohort: '<',

      /**
       * Parent Survey object. Needed for some task behavior. Uses expression
       * binding (&) b/c it uses a parent controller method.
       * @type {Object}
       */
      parentSurvey: '&',

      /**
       * Task complete button callback function.
       * @type {Function}
       */
      taskComplete: '&',
    },
    controller: TaskItemController,
    template: require('./task_item.view.html'),
  });

  function TaskItemController(
    $scope,
    $element,
    $sce,
    $q,
    $state,
    $transitions,
    $timeout,
    Liaison,
    Upload,
    ProjectCohort,
    Survey,
    Task,
  ) {
    const vm = this;

    $transitions.onSuccess({ to: '**.tasks' }, transition => {
      vm.statefulExpand(transition.params());
    });

    vm.$onInit = function () {
      vm.today = new Date().toISOString();

      vm.statefulExpand($state.params);

      // Add the current project cohort id to the task, which allows
      // contextualized notification links when the task is PUT.
      vm.task.project_cohort_id = vm.parentProjectCohort.uid;

      // If Task Parent is a Survey, place parentSurvey onto scope and possibly
      // lock the task from interaction.
      if (getKind(vm.task.parent_id) === 'Survey') {
        vm.parentSurvey = Survey.get({ id: vm.task.parent_id });
      }

      vm.isClosed = isClosed();
    };

    vm.$onChanges = function (changes) {
      if (changes.task && changes.task.currentValue) {
        // If the project cohort is closed, lock down all interaction with
        // tasks by swapping in a button that does nothing.
        // N.B. Don't rely on vm.isClosed here b/c $onChanges runs before
        // $onInit.
        const Button = isClosed() ? DisabledButton : TaskButton;

        // Task Button
        vm.button = new Button(vm.taskComplete);
        vm.button.setDisabled(vm.task.isTouched);

        // Set Task Button Text
        if (vm.task.data_type === 'textarea') {
          vm.button.setActionStatement('Save My Entry');
        } else if (vm.task.data_type.includes('input')) {
          vm.inputType = vm.task.data_type.split(':')[1];
          vm.button.setActionStatement('Save My Entry');
        } else if (vm.task.data_type.includes('radio')) {
          vm.inputType = vm.task.data_type.split(':')[1];
          vm.button.setActionStatement('Save Selection');
        } else {
          vm.button.setActionStatement(
            $sce.trustAsHtml(vm.task.action_statement),
          );
        }

        // Disable the save button if we're asking for any kind of input.
        if (vm.task.data_type !== 'button') {
          if (!vm.task.attachment) {
            vm.button.setDisabled(true);
          }
        }

        // Type coercion.
        if (vm.task.data_type === 'input:number') {
          // Putting a string in a <input type="number"> raises an error, and
          // all task attachments are strings as far as the server is
          // concerned. Coerce for angular.
          vm.task.attachment = isStringNumeric(vm.task.attachment)
            ? parseInt(vm.task.attachment, 10)
            : undefined;
        } else if (vm.task.data_type === 'input:date') {
          // https://stackoverflow.com/questions/25725882/locale-detection-with-moment-js
          const locale =
            window.navigator.userLanguage || window.navigator.language;
          moment.locale(locale);

          if (vm.task.attachment) {
            vm.task.attachment = moment.utc(vm.task.attachment).toDate();
            // https://momentjs.com/docs/#/customization/long-date-formats/
            vm.task.attachmentFormatted = moment(vm.task.attachment).format(
              'l',
            );
          }
          vm.initialDate = vm.task.attachmentFormatted;
        }

        // Vary placeholder for different input types.
        if (vm.task.data_type === 'input:number') {
          vm.placeholder = 'Enter a number here';
        } else if (vm.task.data_type === 'input:url') {
          vm.placeholder = 'http://';
        }

        // Setup Radio Tasks
        vm.setupRadioTasks();

        // Setup File Uploads
        vm.setupFileTasks();

      }

      if (vm.program) {
        const c = vm.program.cohorts[vm.parentProjectCohort.cohort_label];
        c.participationOpenDate = parseLocalDateStr(c.open_date);
        c.participationCloseDate = parseLocalDateStr(c.close_date);
        c.displayCloseDate = moment(angular.copy(c.participationCloseDate))
          .subtract(1, 'days')
          .toDate();
        vm.cohort = c;
      }
    };

    vm.validateInputForm = function (form) {
      // Various states we want to react to, in order of importance. The
      // highest priority applicable error gets set in the view.
      // https://docs.angularjs.org/api/ng/type/form.FormController
      const errors = ['required', 'url', 'number', 'email'];
      let valid = true;
      vm.inputError = undefined;

      errors.reverse().forEach(errorType => {
        if (form.$error[errorType]) {
          valid = false;
          vm.inputError = errorType; // triggers appropriate text in the view
        }
      });

      // Loop through each named form control for additional checks.
      form.$$controls.forEach(control => {
        // Numbers should never be negative; treat it like a number error.
        if (vm.task.data_type === 'input:number' && control.$modelValue < 0) {
          valid = false;
          vm.inputError = 'number';
        }
      });

      // Any failed checks will switch valid from true to false.
      vm.button.setDisabled(!valid);
    };

    vm.dateChange = function () {
      // Typically, we would set ng-model="$ctrl.attachment" and allow Angular
      // to handle updates. But the angular-moment-picker addon's `start-date`
      // prop isn't working. This means values from the datastore can't populate
      // the date selector. To work around this, we need to set the `value` prop
      // for the input field. Unfortunately, `ng-model` takes preference over
      // `value` and $ctrl.attachment needs to be in ISO format while the UI
      // version of the date is in MM/DD/YYYY format. So, we manually update
      // attachment when the user changes the date field.
      vm.task.attachment = moment(
        vm.task.attachmentFormatted,
        'l',
      ).toISOString();

      // Only enable the save button when the user has changed the date.
      if (vm.initialDate !== vm.task.attachmentFormatted) {
        vm.button.setDisabled(false);
      } else {
        vm.button.setDisabled(true);
      }
    };

    vm.statefulExpand = function (stateParams) {
      // Expand if the param matches, but don't collapse if it doesn't. We want
      // people to be able to have more than one open.
      if (stateParams.taskId === vm.task.uid) {
        vm.task.isExpanded = true;
      }
    };

    vm.setAttachment = function (attachment) {
      // Merely set the attachment in memory programmatically, don't trigger
      // anything like a user action would, including a server update.
      // Intended to be called in expression bindings in components inside
      // task bodies, like nepLiaisonTaskSetter.
      vm.task.attachment = attachment;
    };

    vm.setValidity = function (valid, errorType) {
      // Child components can bind to this and control whether the button
      // is clickable.
      if (!vm.button) {
        return;
      }
      vm.button.setDisabled(!valid);
      if (!valid) {
        vm.inputError = errorType;
      }
    };

    vm.toggleExpanded = function () {
      if ($state.params.taskId === vm.task.uid) {
        // Close the current task by going to the parent checkpoint state.
        $state.go('^');
        vm.task.isExpanded = false;
      } else {
        // Going to sibling or child state?
        const targetState = $state.params.taskId ? '.' : '.tasks';
        // The action depends on the current value of isExpanded.
        if (vm.task.isExpanded) {
          // Expanded task: stay in the current state, but collapse the task.
          vm.task.isExpanded = false;
        } else {
          // Collapsed task: go to that state, which also expands it.
          $state.go(targetState, { taskId: vm.task.uid });
        }
      }
    };

    vm.setupRadioTasks = function () {
      if (vm.task.data_type === 'radio' && vm.task.select_options) {
        // Angular expressions are handled specially
        if (typeof vm.task.select_options === 'string') {
          // In order for $scope.$eval to be able to access an injected
          // dependency, it needs to be placed on scope with the following
          // pattern:
          //
          //   vm.Liaison = Liaison;
          //
          // The evaluated statement then needs to refer to that injected
          // dependency with the following pattern:
          //
          //   $ctrl.Liaison

          // Place Liaison service on scope so it can be used by $scope.$eval
          if (vm.task.select_options.includes('Liaison')) {
            vm.Liaison = Liaison;
            // We are specifying a default option for Liaison task, so we don't
            // need to wait until making a selection to enable the button.
            vm.button.setDisabled(false);
          }

          vm.task.select_options = $scope.$eval(vm.task.select_options);
        }
      }
    };

    vm.setupFileTasks = function () {
      if (vm.task.data_type.includes('file') && vm.task.attachment) {
        try {
          vm.task.attachmentParsed = angular.fromJson(vm.task.attachment);
          vm.task.attachmentStatus = 'success';
        } catch (e) {
          console.error(
            'Invalid JSON syntax in task attachment:',
            vm.task.attachment,
          );
        }
      }
    };

    // https://angular-file-upload-cors-srv.appspot.com/
    // http://jsfiddle.net/danialfarid/0mz6ff9o/135/
    vm.uploadFile = function (file, invalidFiles) {
      if (invalidFiles.length) {
        // Assumption, only allowing a single file upload.
        vm.inputError = invalidFiles[0].$error;
        vm.inputErrorParam = invalidFiles[0].$errorParam;
      }

      if (!file) {
        return;
      }

      // We need to clear out inputError to remove any error messages from
      // previous failed attempts at uploading a file.
      vm.inputError = '';
      vm.inputErrorParam = '';

      file.upload = Upload.upload({
        url: `/api/tasks/${vm.task.uid}/attachment`,
        data: { file },
      });

      file.upload.then(
        function success(response) {
          response.data.status = Task.FILE_SUBMITTED;
          vm.task.attachment = angular.toJson(response.data);
          vm.task.attachmentParsed = response.data;
          vm.task.attachmentStatus = 'success';

          vm.taskComplete();
        },
        function error(response) {
          vm.task.attachmentStatus = 'error';
          vm.task.errorMsg =
            'There was an error uploading your file. Please try again.';

          if (response.status > 0) {
            console.error(`${response.status}: ${response.data}`);
          }
        },
        function progress(evt) {
          vm.task.attachmentStatus = 'uploading';
          vm.task.attachmentProgress = Math.min(
            100,
            parseInt((100.0 * evt.loaded) / evt.total, 10),
          );
          // file.progress = Math.min(100, parseInt(100.0 * evt.loaded / evt.total, 10));
        },
      );
    };

    function isClosed() {
      return vm.parentProjectCohort.status === ProjectCohort.CLOSED_STATUS;
    }

    function TaskButton(taskComplete) {
      this.taskComplete = taskComplete;

      // Set defaults
      this.text = "I've done this";
      this.instructions = `Click "${this.text}" to complete this task.`;
      this.isDisabled = false;
    }

    TaskButton.prototype.setDisabled = function (isDisabled) {
      this.isDisabled = Boolean(isDisabled);
    };

    TaskButton.prototype.setActionStatement = function (actionStatement) {
      if (!actionStatement) {
        return;
      }
      this.text = actionStatement;
      this.instructions = `Click "${this.text}" to complete this task.`;
    };

    TaskButton.prototype.click = function () {
      this.setDisabled(true);

      // Special behavior for monitor type, which stores survey status as
      // the task attachment. Clicking the button is sufficient
      // to mark the task and survey as complete.
      // See the Task service -> isComplete().
      if (vm.task.data_type === 'monitor') {
        vm.task.attachment = Task.COMPLETE_STATUS;
      }

      this.taskComplete();
    };

    function DisabledButton() {
      // Set defaults
      this.text = 'Closed';
      this.instructions = '';
      this.isDisabled = true;
    }

    DisabledButton.prototype.setDisabled = () => {};

    DisabledButton.prototype.setActionStatement = () => {};

    DisabledButton.prototype.click = () => {};
  }
})();
