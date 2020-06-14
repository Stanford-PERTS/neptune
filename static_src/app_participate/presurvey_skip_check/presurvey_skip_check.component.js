(function() {
  'use strict';

  /**
   * @ngdoc component
   * @name appParticipate.component:nepPresurveySkipCheck
   * @description
   *   If the participant is requesting survey 2 but they didn't do survey 1,
   *   then try to direct them back to survey 1.
   */

  window.ngModule.component('nepPresurveySkipCheck', {
    require: {
      // Allows $ctrl.parent.nextPresurveyState in markup.
      parent: '^nepPresurvey',
    },
    controller: PresurveySkipCheckController,
    template: require('./presurvey_skip_check.view.html'),
  });

  function PresurveySkipCheckController(
    $q,
    portalCookies,
    ParticipantData,
    Survey,
  ) {
    const vm = this;

    this.$onInit = function() {
      const code = portalCookies.get('code');
      const session = Number(portalCookies.get('session')); // coerce to int
      const token = portalCookies.get('token');

      vm.parent.getLoadedData().then(loaded => {
        // Don't check people who are doing session 1.
        if (session === 1) {
          vm.parent.nextPresurveyState();
          return;
        }

        // Don't check people who have already done session 1.
        const theyAlreadyDid1 = loaded.pdArr.find(
          pd =>
            pd.key === 'progress' &&
            pd.survey_ordinal === 1 &&
            parseInt(pd.value, 10) === 100,
        );
        if (theyAlreadyDid1) {
          vm.parent.nextPresurveyState();
          return;
        }

        // else display the check
        vm.parent.toggleMask(false);
      });
    };

    vm.submit = function(theyDid1) {
      let p = $q.when();
      if (!theyDid1) {
        // They didn't do 1 yet. Change the cookies so they get session 1 and
        // make sure they have a link for it.
        p = vm.parent
          .getLoadedData()
          .then(loaded => {
            loaded.session = 1;

            loaded.survey = Survey.queryOne({
              project_cohort_id: loaded.projectCohort.uid,
              ordinal: loaded.session,
            }).$promise;

            return $q.all(loaded);
          })
          .then(vm.parent.getSurveyLink)
          .then(vm.parent.setLoadedData);
      } // else, fine, let them do what they're asking for.
      p.then(() => {
        vm.parent.nextPresurveyState();
      });
    };
  }
})();
