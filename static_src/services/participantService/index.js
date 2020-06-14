// Service for getting participants.
//
// Usage:
//
// var participant = Participant.get({id: participantId});
// var matching = Participant.query({name: 'smarcher', organization_id: 'ISIS'})

const participantService = ngModule => {
  ngModule.service('Participant', function Participant(
    $resource,
    hostingDomain,
    tritonDomain,
  ) {
    const ParticipantResource = $resource(
      // Important Notes:
      // GET /api/participants requires params `name` and `organization_id`
      // POST /api/participants ditto

      `//${hostingDomain}/api/participants/:id`,
      { id: '@uid' },
      {
        getTritonParticipant: {
          url: `//${tritonDomain}/api/codes/:code/participants/:token`,
          method: 'GET',
        },
      },
    );

    return ParticipantResource;
  });
};

export default participantService;
