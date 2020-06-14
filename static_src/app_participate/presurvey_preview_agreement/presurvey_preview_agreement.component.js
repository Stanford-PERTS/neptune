(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name appParticipate.component:nepPresurveyPreviewAgreement
   * @description
   *   If the overrides are set, then this is a program preview, and we should
   *   warn people to respect it.
   */

  window.ngModule.component('nepPresurveyPreviewAgreement', {
    require: {
      // Allows $ctrl.parent.nextPresurveyState in markup.
      parent: '^nepPresurvey',
    },
    controller: PresurveyPreviewAgreementController,
    template: require('./presurvey_preview_agreement.view.html'),
  });

  function PresurveyPreviewAgreementController($state) {
    const vm = this;

    vm.$onInit = function () {
      if ($state.params.date_override || $state.params.ready_override) {
        vm.parent.toggleMask(false);
      } else {
        vm.parent.getLoadedData().then(vm.parent.nextPresurveyState);
      }
    };
  }
})();
