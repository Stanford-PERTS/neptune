// Service for getting participation stats from the API.
//
// Usage:
//
// var stats = Participation.queryBySurvey({id: surveyId});
//
// Todo:
//
// * Make it work for higher level relationships, e.g. projects.

const ParticipationService = ngModule => {
  ngModule.service('Participation', function Participation(
    $resource,
    hostingDomain,
  ) {
    const ParticipationResource = $resource(
      // @todo(chris): this endpoint doesn't exist! But I like using $resource,
      // so what's the best way to write this?
      `//${hostingDomain}/api/participation`,
      {}, // no params in default url, so blank object here
      {
        queryByProjectCohort: {
          url: `//${hostingDomain}/api/project_cohorts/:id/participation`,
          method: 'GET',
          isArray: true,
        },
        queryBySurvey: {
          url: `//${hostingDomain}/api/surveys/:id/participation`,
          method: 'GET',
          isArray: true,
        },
      },
    );

    return ParticipationResource;
  });
};

export default ParticipationService;
