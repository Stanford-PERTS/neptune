(function () {
  'use strict';

  function OptionsBatchController(Dashboard, ModalService) {
    const vm = this;

    function cardsSelected() {
      return vm.cardRows.filter(c => c.selected);
    }

    /**
     * Open modal to approve the selected cardRows for participation.
     */
    vm.approveParticipation = function () {
      ModalService.showModal({
        template: require('../dashboard/approve_participation_modal.view.html'),
        controller: 'ApproveParticipationController',
        bodyClass: 'neptune-modal-open',
        inputs: {
          program: vm.options.program,
          projectDataRows: cardsSelected(),
        },
      });
    };

    /**
     * Open modal to send emails to selected cardRows' liaisons.
     */
    vm.openEmailModal = function () {
      Dashboard.getLiaisonsByProjects(cardsSelected()).then(cardRows => {
        ModalService.showModal({
          template: require('../dashboard/email_modal.view.html'),
          controller: 'EmailModalController',
          bodyClass: 'neptune-modal-open',
          inputs: {
            projectDataRows: cardRows,
          },
        });
      });
    };
  }

  window.ngModule.component('nepOptionsBatch', {
    bindings: {
      cardRows: '<',
      options: '<', // dashboard options

      selectAllVisible: '&',
      deselectAllVisible: '&',
    },
    controller: OptionsBatchController,
    template: require('./options_batch.view.html'),
  });
})();
