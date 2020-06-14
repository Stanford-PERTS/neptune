/**
 * Dashboard Component
 */

import template from './dashboard_advanced.view.html';

(function () {
  'use strict';
  window.ngModule.component('nepDashboardAdvanced', {
    bindings: {
      program: '<',
    },
    controller() {
      const vm = this;

      vm.$onInit = function () {};
    },
    template,
  });
})();
