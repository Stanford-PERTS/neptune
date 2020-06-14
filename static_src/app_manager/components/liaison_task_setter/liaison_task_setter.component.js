(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name neptuneApp.component:nepLiaisonTaskSetter
   * @description
   *   Compares the task attachment and org liaison and decides if the
   *   attachment should be changed.
   */

  window.ngModule.component('nepLiaisonTaskSetter', {
    bindings: {

      /**
       * Task update event, for explicit updates rather than two-way binding.
       * @type {Function}
       */
      setLiaison: '&',

      /**
       * Parent task
       * @type {string}
       */
      taskAttachment: '<',

      /**
       * Org liaison id
       * @type {string}
       */
      liaisonId: '<',
    },
    controller: LiaisonTaskSetterController,
    template: '', // this is a logic-only component, has no view
  });

  function LiaisonTaskSetterController() {
    this.$onInit = function () {
      if (!this.liaisonId) {
        return;
      }

      if (!this.taskAttachment || this.taskAttachment !== this.liaisonId) {
        // The parent organization has a liaison set but this task has no value
        // yet OR the liaison id has changed since the task was set.
        this.setLiaison({ liaisonId: this.liaisonId });
        // Don't call taskComplete() or similar, or trigger the /Task/update
        // event. The goal is not to complete the task, merely fill in a
        // value the user can then confirm or change.
      }
    };
  }
})();
