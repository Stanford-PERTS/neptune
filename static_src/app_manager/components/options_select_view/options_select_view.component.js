(function () {
  'use strict';

  function OptionsSelectViewController() {
    const vm = this;

    vm.$onInit = function () {};
  }

  window.ngModule.component('nepOptionsSelectView', {
    bindings: {
      options: '<', // dashboard options
    },
    controller: OptionsSelectViewController,
    template: require('./options_select_view.view.html'),
  });
})();
