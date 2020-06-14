const invitationService = ngModule => {
  ngModule.service('Invitation', function Invitation($resource, hostingDomain) {
    // Can POST with these properties, defined in api_handlers.Invitations:
    // 'to_address': unicode,
    // 'subject': unicode,
    // 'template': str,
    // 'template_data': 'json',
    // 'continue_url': str,
    // 'organization_id': str,

    return $resource(`//${hostingDomain}/api/invitations`);
  });
};

export default invitationService;
