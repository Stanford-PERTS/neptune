import template from './index.html';

const checkpointsEncourage = ngModule => {

  /**
   * @name neptuneApp.component:nepCheckpointsEncourage
   * @description
   *   This panel will display below the checkpoint tasks to let the user know
   *   if they have completed the tasks. If they have completed, this panel
   *   will also provide a link to the next checkpoint.
   */

   ngModule.component('nepCheckpointsEncourage', {
    bindings: {
      status: '<',
      disabled: '<',
      click: '&',
    },
    template,
  });

};

export default checkpointsEncourage;
