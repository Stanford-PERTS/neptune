(function () {
  'use strict';

  window.ngModule.component('uiInputSuccess', {
    bindings: {
      type: '@',
      message: '=',
    },
    controller($scope, $timeout) {
      const vm = this;
      let timer;

      // stop displaying the message after a delay
      $scope.$watch(
        function valueToWatch() {
          return vm.message;
        },
        function onChange() {
          // prevents overlapping timers
          if (vm.message === null) {
            return;
          }
          $timeout.cancel(timer);
          timer = $timeout(() => {
            vm.message = null;
          }, 6000);
        },
      );
    },
    template: `
      <div
        class="{{ $ctrl.type === 'form' ? 'FormSuccess' : 'InputSuccess' }}"
        ng-show="$ctrl.message"
      >
        {{ $ctrl.message }}
      </div>
    `,
  });
})();
