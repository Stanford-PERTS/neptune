import moment from 'moment';

(function () {
  'use strict';

  /**
   * @ngdoc controller
   * @name neptuneApp.controller:ParticipationDownloadModalController
   * @description
   *   Shows the user a message warning them about privacy concerns regarding
   *   downloading student data before providing a link to download.
   */

  window.ngModule.controller(
    'ParticipationDownloadModalController',
    ParticipationDownloadModalController,
  );

  function ParticipationDownloadModalController(
    $scope,
    close,
    User,
    AuthToken,
    ProjectCohort,
    hostingDomain,
    projectCohort,
    startDate,
    endDate,
  ) {
    $scope.href = undefined;

    $scope.projectCohort = projectCohort;

    // Pre-load the form with last time's responses, if applicable.
    $scope.survey = getLastResponseData(projectCohort.data_export_survey) || {};

    $scope.startDate = startDate;
    $scope.endDate = endDate;

    if (User.isSuperAdmin()) {
      // Don't bother super admins.
      $scope.skipSurvey = true;
      // We give a link for downloading right away. Normally we'd require the
      // survey is complete/valid.
      getHref().then((href) => ($scope.href = href));
    }

    /**
     * Closes the modal window.
     */
    $scope.close = function () {
      close();

      // foo

      // We also need to clean up $scope
      $scope.$destroy();
    };

    /**
     * Used for requiring at least one of a group of checkboxes are marked.
     * @param {Object} obj
     * @returns {boolean} true if obj does not include some property with
     *     boolean true.
     */
    $scope.anyChecked = function (obj) {
      let anyChecked = false;
      angular.forEach(obj, (v, k) => {
        if (v === true) {
          anyChecked = true;
        }
      });
      return anyChecked;
    };

    $scope.clearEvaluationResponses = function (useForEvaluation) {
      console.log('clear', useForEvaluation);
      if (!useForEvaluation) {
        $scope.survey.evaluation = {};
      }
    };

    $scope.$watch('downloadSurveyForm.$valid', (valid) => {
      if (valid && !$scope.href) {
        getHref().then((href) => ($scope.href = href));
      }
    });

    /**
     * Called when someone clicks download.
     */
    $scope.saveSurvey = function () {
      // Don't log download activity by supers.
      if (!User.isSuperAdmin()) {
        // Don't re-record unchanged data.
        const unchanged = angular.equals(
          getLastResponseData(projectCohort.data_export_survey),
          $scope.survey,
        );
        const data = unchanged ? {} : $scope.survey;

        projectCohort.data_export_survey[moment.utc().format()] = {
          // Always log the time and submitter.
          submitter_id: User.getCurrent().uid,
          submitter_email: User.getCurrent().email,
          data,
        };
        ProjectCohort.put(projectCohort);
      }

      close(); // modal
    };

    function getHref() {
      return new AuthToken()
        .$save()
        .then(
          (authToken) =>
            `//${hostingDomain}/api/project_cohorts/${projectCohort.uid}/completion/ids.csv?` +
            `token=${authToken.token}&` +
            `start=${moment.utc(startDate).format()}&` +
            `end=${moment.utc(endDate).format()}&`,
        );
    }

    /**
     * @param {Object} responses - from projectCohort.data_export_survey
     * @returns {Object} most recent response's data field (matches our form)
     */
    function getLastResponseData(responses) {
      let lastDateStr = '';
      let lastResponse;
      angular.forEach(responses, (response, dateStr) => {
        if (dateStr > lastDateStr && !angular.equals(response.data, {})) {
          lastDateStr = dateStr;
          lastResponse = response.data;
        }
      });
      return lastResponse;
    }
  }
})();
