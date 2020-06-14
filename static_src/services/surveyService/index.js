const surveyService = ngModule => {
  ngModule.service('Survey', function Survey(
    $resourceWith,
    Task,
    hostingDomain,
    queryOne,
  ) {
    const SurveyResource = $resourceWith(
      `//${hostingDomain}/api/surveys/:id`,
      { id: '@uid' },
      {
        queryByOrganization: {
          url: `//${hostingDomain}/api/organizations/:id/surveys?order=ordinal`,
          method: 'GET',
          isArray: true,
        },
        queryByProject: {
          url: `//${hostingDomain}/api/projects/:id/surveys?order=ordinal`,
          method: 'GET',
          isArray: true,
        },
        queryByProjectCohort: {
          url: `//${hostingDomain}/api/project_cohorts/:id/surveys?order=ordinal`,
          method: 'GET',
          isArray: true,
        },
      },
    );

    SurveyResource.queryOne = queryOne;

    SurveyResource.NOT_READY_STATUS = 'not ready';
    SurveyResource.READY_STATUS = 'ready';
    SurveyResource.COMPLETE_STATUS = Task.COMPLETE_STATUS; // 'complete'

    return SurveyResource;
  });
};

export default surveyService;
