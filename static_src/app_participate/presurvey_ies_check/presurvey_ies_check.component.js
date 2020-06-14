import sha1 from 'crypto-js/sha1';

(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name appParticipate.component:nepPresurveyIesCheck
   * @description
   *   FOR CG17 ONLY
   *   If the participant is recognized as having been invited to participate
   *   the PERTS IES study on Mariposa, add a special variable that will tell
   *   Qualtrics to skip the intervention content so as not to contaminate that
   *   sample.
   */

  window.ngModule.component('nepPresurveyIesCheck', {
    require: {
      // Allows $ctrl.parent.nextPresurveyState in markup.
      parent: '^nepPresurvey',
    },
    controller: PresurveyIesCheckController,
    // templateUrl: 'presurvey_ies_check/presurvey_ies_check.view.html'
  });

  function PresurveyIesCheckController(
    $q,
    $http,
    hostingDomain,
    portalCookies,
  ) {
    const vm = this;

    vm.$onInit = function () {
      const token = portalCookies.get('token');

      const salt = 'FkHs_B5KTzLn-YWtkXj4';

      const hashedToken = sha1(token + salt).toString();

      $http
        .get(`//${hostingDomain}/static/known_ies_student_ids.json`)
        .then(response => {
          if (response.data.includes(hashedToken)) {
            return vm.parent.setSurveyParams({
              skip_to_completion_code: 'true',
            });
          }
        })
        .then(vm.parent.nextPresurveyState);
    };
  }
})();
