(function () {
  'use strict';

  window.ngModule.component('nepOptionsSelectSort', {
    bindings: {
      options: '<', // dashboard options
    },
    template: require('./options_select_sort.view.html'),
  });
})();
