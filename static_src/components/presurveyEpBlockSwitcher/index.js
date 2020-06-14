import parseUTCDateStr from 'utils/parseUTCDateStr';

/**
 * FOR TRITON/COPILOT/ENGAGEMENT PROJECT ONLY
 *
 * Generally sets parameters that control survey flow in Qualtrics, switching
 * blocks on and off.
 *
 * * If the participant hasn't seen the validation block in the past 50 days,
 *   send them to Qualtrics with a flag to show the block.
 * * Handle transition from the parameter
 *   `show_open_response_questions` (true/false) to `open_response_lcs`
 *   (comma-separated learning condition ids).
 * * Add some pd values that we use to switch blocks on an off, like
 *   demographics and baseline.
 *
 * @param {Object} ngModule angular module "participate"
 * @returns {undefined}
 * @see https://github.com/PERTS/triton/issues/697
 */
const presurveyBlockSwitcher = ngModule => {
  function controller($q) {
    const vm = this;

    vm.$onInit = function() {
      vm.parent
        .getLoadedData()
        .then(loaded =>
          $q
            .when(vm.getSawValidationDate(loaded))
            .then(vm.applyValidationInterval)
            .then(vm.parent.setSurveyParams),
        )
        .then(loaded => {
          // The purpose of this section is to mutate the pc's survey params
          // because the interface is changing. This is non-ideal, and should
          // change to pure functions when the interface is stable. Specifically
          // Qualtrics is ahead of Copilot, and the params sent by Copilot need
          // updating.
          const params = loaded.projectCohort.survey_params;
          return $q
            .when(vm.transformLearningConditionParam(params))
            .then(vm.chooseOneLearningCondition)
            .then(vm.parent.setSurveyParams);
        })
        .then(loaded => {
          // Make sure to inspect `allPdArr` and not just `pdArr`, which is
          // scoped to the classroom.
          const params = vm.getPdParams(loaded.allPdArr);
          return vm.parent.setSurveyParams(params);
        })
        .then(vm.parent.nextPresurveyState)
        .catch(vm.parent.presurveyError);
    };

    vm.getSawValidationDate = function(loaded) {
      // Consider any event where this participant saw the validation block,
      // regardless of classroom (project cohort / code) or session (currently
      // always 1 but who knows). Make sure to inspect `allPdArr` and not just
      // `pdArr`, which is scoped to the classroom.
      const sawPd = loaded.allPdArr.find(pd => pd.key === 'saw_validation');
      return sawPd ? parseUTCDateStr(sawPd.value) : undefined;
    };

    vm.applyValidationInterval = function(sawDate) {
      const fiftyDays = 50 * 24 * 60 * 60 * 1000;
      const today = new Date();
      if (!sawDate || today - fiftyDays >= sawDate) {
        return { show_validation: 'true' };
      }
      return {}; // no params to set
    };

    const chooseOne = arr => arr[Math.floor(Math.random() * arr.length)];

    /**
     * - May have the param `show_open_response_questions` as a true/false
     * - May have the param `open_response_lcs` as a true/false
     * @param  {Object} params query string params for qualtrics
     * @return {Object}        transformed params
     */
    vm.transformLearningConditionParam = function(params) {
      // Move to the correct param name.
      if ('show_open_response_questions' in params) {
        if (!('open_response_lcs' in params)) {
          params.open_response_lcs = params.show_open_response_questions;
        } // else don't override the more current param
        delete params.show_open_response_questions;
      }

      // Convert old values.
      if (params.open_response_lcs === true) {
        // Assume this means all active learning conditions have open
        // responses on.
        params.open_response_lcs = params.learning_conditions;
      } else if (params.open_response_lcs === false) {
        params.open_response_lcs = '[]';
      }
      // else it's not an old value, leave it alone

      // At this point we should be sure to have certain params.
      if (
        params.learning_conditions === undefined ||
        params.open_response_lcs === undefined
      ) {
        return $q.reject('misconfigured');
      }

      return params;
    };

    vm.chooseOneLearningCondition = function(params) {
      // Choose just one learning condition so the survey isn't too long.
      // This will change once Copilot can switch individual open responses
      // options on and off.
      const lcs = JSON.parse(params.open_response_lcs);
      params.open_response_lcs = lcs.length
        ? JSON.stringify([chooseOne(lcs)])
        : '[]';

      return params;
    };

    vm.getPdParams = function(allPdArr) {
      const keys = ['saw_baseline', 'saw_demographics'];
      const params = {};

      allPdArr.forEach(pd => {
        if (keys.includes(pd.key)) {
          params[pd.key] = pd.value;
        }
      });

      return params;
    };
  }

  ngModule.component('nepEpBlockSwitcher', {
    controller,
    require: {
      parent: '^nepPresurvey',
    },
  });
};

export default presurveyBlockSwitcher;
