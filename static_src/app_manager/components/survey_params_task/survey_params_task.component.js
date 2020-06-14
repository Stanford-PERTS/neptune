(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name neptuneApp.component:nepSurveyParamsTask
   * @description
   *
   */

  window.ngModule.component('nepSurveyParamsTask', {
    bindings: {
      task: '<',

      /**
       * Parent can bind to this event. Called whenever inputs change.
       * @type {Function}
       */
      surveyParamsChange: '&',
    },
    transclude: true,
    controller: SurveyParamsTaskController,
    template: '<div ng-transclude></div>',
  });

  function SurveyParamsTaskController($scope) {
    const vm = this;

    vm.params = {};
    // Important this start undefined so we can detect a pre-initialized state.
    let previousParams;

    vm.$onInit = function () {
      // Parse the task attachment and populate the view.
      angular.extend(vm.params, angular.fromJson(vm.task.attachment || '{}'));

      // Make sure our change detection doesn't fire on init.
      previousParams = angular.copy(vm.params);
    };

    vm.$postLink = function () {
      // Get materializecss to move form labels out of the way if fields are
      // already filled.
      initializeForm(vm.surveyParamsForm);

      // CAM found, with required radio inputs, the form was validating _after_
      // the $doCheck triggered by the change. Our validation would run on a
      // stale version of the form, but never run again once the form finished
      // validation. The observed effect was selecting one from a required
      // radio group would not pass our validation
      // (nepTaskItem.validateInputForm()). My solution is to set up a
      // dedicated watch on form validity to catch this edge case.
      $scope.$watch(() => vm.surveyParamsForm.$valid, (
        newValue,
        oldValue,
      ) => {
        // Only trigger when form changes from invalid to valid, otherwise
        // the UI would raise errors about pristine inputs.
        if (newValue && !oldValue) {
          vm.updateSurveyParams();
        }
      });
    };

    /**
     * Check if form has changed; easier than writing an ng-change into
     * every control. On change, uses methods of nepTaskItem to validate
     * and update the task.
     */
    vm.$doCheck = function () {
      // This runs a bunch of times as the page is starting up. However, until
      // we've run $onInit and the form is up and running, we don't want to
      // do anything.
      if (!vm.surveyParamsForm || previousParams === undefined) {
        return;
      }

      // Invalid user input doesn't make it into the model. If we only checked
      // the model, the UI couldn't respond to invalid user input. If we only
      // checked invalid input, the UI couldn't respond to valid changes. If
      // we responded to all invalid input (instead of just dirty invalid)
      // then the UI would raise errors about pristine blanks.
      const modelChanged = !angular.equals(vm.params, previousParams);
      const dirtyInvalid =
        vm.surveyParamsForm.$dirty && vm.surveyParamsForm.$invalid;
      if (modelChanged || dirtyInvalid) {
        vm.updateSurveyParams();
        previousParams = angular.copy(vm.params);
      }
    };

    /**
     * Publish changes to parent component.
     */
    vm.updateSurveyParams = function () {
      vm.surveyParamsChange({
        paramsJson: angular.toJson(vm.params),
        form: vm.surveyParamsForm,
      });
    };

    /**
     * Sum a series of user-provided percentages.
     * @param {...Array} numbers to be summed
     * @returns {number} sum rouded to the nearest integer
     */
    vm.roundedSum = function (...nums) {
      const floatSum = nums
        .map(parseFloat)
        .map(x => (isNaN(x) ? 0 : x))
        .reduce((sum, x) => sum + x, 0);
      return Math.round(floatSum);
    };

    /**
     * Move materalizecss labels out of the way.
     * @param {Object} the form to fix up
     */
    function initializeForm(form) {
      form.$$controls.forEach(function setTouched(control) {
        if (vm.params.hasOwnProperty(control.$name)) {
          control.$setTouched();
        }
      });
    }
  }
})();
