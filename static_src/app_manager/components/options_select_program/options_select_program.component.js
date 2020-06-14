(function () {
  'use strict';

  function OptionsSelectProgramController($state, $transitions, Program) {
    const vm = this;

    vm.$onInit = function () {
      vm.loading = true;

      Program.queryAllPrograms().then(programs => {
        vm.programs = programs;
        selectActiveProgram();
        vm.loading = false;
      });
    };

    function selectActiveProgram() {
      // Select the active program if we find one in params
      if ($state.params.program_label) {
        vm.selected = vm.programs.find(
          p => p.label === $state.params.program_label,
        );
      }
    }

    // Determines when we should clear the program select drop down.
    function shouldClearProgram() {
      if ($state.is('dashboard') || $state.params.organization_id) {
        return true;
      }
    }

    const deregister = $transitions.onSuccess({}, () => {
      if (shouldClearProgram()) {
        vm.selected = null;
      } else {
        selectActiveProgram();
      }
    });

    vm.$onDestroy = function () {
      deregister();
    };

    vm.changeProgram = function () {
      if (vm.selected && vm.selected.label) {
        // navigate to program
        $state.go('dashboard.query', {
          program_label: vm.selected.label,
          // set to null so we don't let cohort or organization filtering linger
          cohort_label: null,
          organization_id: null,
        });
      } else {
        // or navigate back to dashboard if selection cleared out
        $state.go('dashboard');
      }
    };
  }

  window.ngModule.component('nepOptionsSelectProgram', {
    bindings: {
      cardRows: '<',
      options: '<', // dashboard options

      selectAllVisible: '&',
      deselectAllVisible: '&',
    },
    controller: OptionsSelectProgramController,
    template: require('./options_select_program.view.html'),
  });
})();
