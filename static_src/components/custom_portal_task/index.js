function controller($scope) {

  const vm = this;

  vm.$onInit = function () {
    $scope.$on('/Task/updated', (event, updatedTask) => {
      if (updatedTask.label.includes('portal_quiz')) {
        vm.portalType = updatedTask.attachment;

        const notApplicableText = 'N/A';

        if (vm.portalType === 'custom') {
          if (vm.task.attachment === notApplicableText) {
            vm.task.attachment = '';
          }
          vm.task.disabled = false;
          vm.taskComplete();
        } else {
          // Ensure there's some truthy attachment so that other code
          // recognizes this task as complete.
          if (!vm.task.attachment) {
            vm.task.attachment = notApplicableText;
          }
          // Disable the task, since there's no action to take.
          vm.task.disabled = true;
          vm.taskComplete();
        }
      }
    });

  };
}

const customPortalTask = ngModule => {

  /**
   * @ngdoc component
   * @name neptuneApp.component:nepCustomPortalTask
   * @description
   *    Changes state in response to the portal type task.
   */

   ngModule.component('nepCustomPortalTask', {
    bindings: {

      /**
       * Portal type of related ProjectCohort. Changes body text.
       * @type {String}
       */
      portalType: '<',
      task: '<',
      taskComplete: '&',
    },
    transclude: true,
    controller,
    template: '<div ng-transclude></div>',
  });
};

export default customPortalTask;
