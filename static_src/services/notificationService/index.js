// Angular service for handing Notification object in Angular module
const notificationService = ngModule => {
  ngModule.service('Notification', function Notification(
    $resourceWith,
    hostingDomain,
  ) {
    const NoteResource = $resourceWith(
      `//${hostingDomain}/api/notifications/:id`,
      { id: '@uid' },
      {
        queryByUser: {
          url: `//${hostingDomain}/api/users/:id/notifications`,
          method: 'GET',
          isArray: true,
        },
      },
    );

    return NoteResource;
  });
};

export default notificationService;
