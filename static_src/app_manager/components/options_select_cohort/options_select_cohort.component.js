(function () {
  'use strict';

  function OptionsSelectCohortController($state, $transitions, Program) {
    const vm = this;

    vm.$onInit = function () {
      // Give route/params access to template.
      vm.$state = $state;

      vm.loading = true;

      vm.cohorts = [];

      if (vm.options.cohort) {
        vm.selected = vm.options.cohort;
      } else {
        placeCohortsOnScope(vm.program).then(() => (vm.loading = false));
      }
    };

    vm.$onChanges = function () {
      // Different programs may have different cohort labels, so update our
      // list of options when the program changes.
      placeCohortsOnScope(vm.program);
    };

    function placeCohortsOnScope(program) {
      return Program.cohorts(program).then(cohorts => {
        vm.cohorts = cohorts.sort((a, b) => {
          // Descending order, newest cohort at the top.
          if (a.label < b.label) {
            return 1;
          }
          if (a.label > b.label) {
            return -1;
          }
          return 0;
        });
        selectActiveCohort();
      });
    }

    function selectActiveCohort() {
      // Select the active cohort if we find one in params
      if ($state.params.cohort_label) {
        vm.selected = vm.cohorts.find(
          c => c.label === $state.params.cohort_label,
        );
      }
    }

    // Determines when we should clear the cohort select drop down.
    function shouldClearCohort() {
      if (
        $state.is('dashboard') ||
        $state.params.organization_id ||
        !$state.params.cohort_label
      ) {
        return true;
      }
    }

    const deregister = $transitions.onSuccess({}, () => {
      if (shouldClearCohort()) {
        vm.selected = null;
      } else {
        selectActiveCohort();
      }
    });

    vm.$onDestroy = function () {
      deregister();
    };

    vm.changeCohort = function () {
      // update selected cohorts
      vm.options.cohort = vm.selected;

      // Update URL so that we can direct link to cohorts
      // https://ui-router.github.io/ng1/docs/0.3.1/index.html#/api/ui.router.state.$state
      // https://stackoverflow.com/a/25649813
      //
      // N.B. The `notify: false` option to $state.go() didn't work last time
      // it was tried. But since we re-query on every cohort change, it
      // shouldn't be necessary.

      if (vm.selected) {
        $state.go('.', { cohort_label: vm.selected.label });
      } else {
        $state.go('.', { cohort_label: null });
      }
    };
  }

  window.ngModule.component('nepOptionsSelectCohort', {
    bindings: {
      program: '<',
      options: '<', // dashboard options
    },
    controller: OptionsSelectCohortController,
    template: require('./options_select_cohort.view.html'),
  });
})();
