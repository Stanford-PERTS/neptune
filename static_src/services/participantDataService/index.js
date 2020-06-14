// Service for getting participants' data ("pd").
//
// Usage:
//
// var pdArr = ParticipantData.query({participantId: participantId});
// var pd = new ParticipantData({key: 'foo', value: 'bar', ...}); pd.$save();

const participantDataService = ngModule => {
  ngModule.service('ParticipantData', function ParticipantData(
    $resource,
    hostingDomain,
  ) {
    const ParticipantDataResource = $resource(
      // Note that calls to GET /api/participants/X/data require
      // the query string param `project_cohort_id`.
      `//${hostingDomain}/api/participants/:participantId/data/:key`,
      {
        participantId: '@participant_id',
        key: '@key',
      },
    );

    return ParticipantDataResource;
  });
};

export default participantDataService;
