(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name appParticipate.component:nepPresurveyConsent
   * @description
   *   ???
   */

  window.ngModule.component('nepPresurveyConsent', {
    require: {
      // Allows $ctrl.parent.nextPresurveyState in markup.
      parent: '^nepPresurvey',
    },
    controller: PresurveyConsentController,
    template: require('./presurvey_consent.view.html'),
  });

  PresurveyConsentController.$inject = [];

  function PresurveyConsentController() {
    const vm = this;

    vm.$onInit = function () {};
  }
})();
