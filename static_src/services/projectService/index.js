const projectService = ngModule => {
  ngModule.service('Project', function Project(
    $resourceWith,
    hostingDomain,
    queryByCache,
  ) {
    const ProjectResource = $resourceWith(
      `//${hostingDomain}/api/projects/:id`,
      { id: '@uid' },
      {
        _queryByOrganization: {
          url: `//${hostingDomain}/api/organizations/:id/projects`,
          method: 'GET',
          isArray: true,
        },
        queryByProgram: {
          url: `//${hostingDomain}/api/programs/:label/projects`,
          method: 'GET',
          isArray: true,
        },
      },
    );

    ProjectResource.queryByOrganization = function (params, callback) {
      const resultSet = this._queryByOrganization(params, callback);
      return queryByCache(resultSet, `${params.id}/projects`);
    };

    return ProjectResource;
  });
};

export default projectService;
