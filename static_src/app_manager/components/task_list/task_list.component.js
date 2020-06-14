import $ from 'jquery';

(function () {
  'use strict';

  window.ngModule.component('nepTaskList', {
    require: {
      parent: '^^nepProjectCohort',
    },
    controller: TaskListController,
    template: require('./task_list.view.html'),
  });

  function TaskListController($state, $sce, $transitions, $anchorScroll) {
    const vm = this;

    vm.$onInit = function () {
      vm.checkpointId = $state.params.checkpointId;

      vm.parent.loaded
        .then(placeCurrentCheckpointOnScope)
        .then(placeCheckpointBodyOnScope)
        .then(expandNextTaskOfCheckpoint)
        .then(scrollToTopOnCheckpointChange)
        .then(adjustForFixedElements);
    };

    // Program cards and checkpoints are position:fixed and task lists will
    // scroll under them. In order for this to work, we need to calculate the
    // height of the program card + checkpoint divs and programmtically adjust
    // the margin-top of the rest of the page's content (that starts with the
    // checkpoint-body div).
    function adjustForFixedElements() {
      $(document).ready(() => {
        modifyCheckpointBodyMargin();
      });

      $(window).resize(() => {
        modifyCheckpointBodyMargin();
      });
    }

    function modifyCheckpointBodyMargin() {
      const baseMargin = 2;
      const fixed = $('.fixed');
      // Small screen won't use position:fixed. In that case, we don't want to
      // apply the margin-top offset.
      const isPositionFixed = fixed.css('position') === 'fixed';

      if (fixed.length && isPositionFixed) {
        const height = fixed.height();
        $('.checkpoint-body').css('margin-top', height + baseMargin);
      } else {
        $('.checkpoint-body').css('margin-top', baseMargin);
      }
    }

    // Place Current Checkpoint on Scope
    function placeCurrentCheckpointOnScope() {
      vm.checkpoint = vm.parent.checkpoints.find(
        checkpoint => checkpoint.short_uid === vm.checkpointId,
      );
    }

    // Place Checkpoint Body on Scope
    function placeCheckpointBodyOnScope() {
      vm.checkpoint.body_vm = $sce.trustAsHtml(vm.checkpoint.body);
    }

    // Expand Next Task of Checkpoint
    // If no task is specified by params, then we will expand the first task
    // that is incomplete of the current Checkpoint.
    function expandNextTaskOfCheckpoint() {
      if (!$state.params.taskId) {
        const nextTaskOfCheckpoint = vm.parent.tasks.find(
          task =>
            task.checkpoint_id_vm === vm.checkpoint.uid &&
            task.status === 'incomplete' &&
            task.non_admin_may_edit
        );

        // If we've found a task that meets the above criteria, then redirect
        // to that Task's state.
        if (nextTaskOfCheckpoint) {
          $state.go(
            '.tasks',
            { taskId: nextTaskOfCheckpoint.uid },
            { location: 'replace' },
          );
        }
      }
    }

    // Scroll To Top On Checkpoint Changes
    function scrollToTopOnCheckpointChange() {
      const matcher = { to: '**.checkpoints' };
      var deregister = $transitions.onSuccess(matcher, transition => {
        const fromId = transition.params('from').checkpointId;
        const toId = transition.params('to').checkpointId;
        if (toId !== fromId) {
          $anchorScroll();
          // Deregister this hook, otherwise, as the user clicks from checkpoint
          // to checkpoint, each view change registers another hook, and we get
          // multiple useless firings.
          // https://github.com/angular-ui/ui-router/issues/2523#issuecomment-180926351
          deregister();
        }
      });
    }

    // Goto Next Checkpoint
    // Starting with the current checkpoint, find and redirect to the next
    // incomplete and isVisible checkpoint. If none are found, we just redirect
    // to the last checkpoint.
    vm.gotoNextCheckpoint = function (checkpoint) {
      let nextCheckpointIndex = vm.parent.checkpoints.indexOf(checkpoint) + 1;
      let nextCheckpoint = vm.parent.checkpoints[nextCheckpointIndex];

      while (
        (nextCheckpoint.status === 'complete' || !nextCheckpoint.isVisible) &&
        nextCheckpointIndex < vm.parent.checkpoints.length - 1
      ) {
        nextCheckpointIndex++;
        nextCheckpoint = vm.parent.checkpoints[nextCheckpointIndex];
      }

      $state.go('dashboard.tasks.checkpoints', {
        checkpointId: nextCheckpoint.short_uid,
      });
    };
  }
})();
