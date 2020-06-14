const projectCohortService = ngModule => {
  ngModule.service('ProjectCohort', function ProjectCohort(
    $resourceWith,
    $http,
    queryOne,
    hostingDomain,
  ) {
    const ProjectCohortResource = $resourceWith(
      `//${hostingDomain}/api/project_cohorts/:id`,
      { id: '@uid' },
      {
        queryByProject: {
          url: `//${hostingDomain}/api/projects/:id/project_cohorts`,
          method: 'GET',
          isArray: true,
        },
        queryByOrganization: {
          url: `//${hostingDomain}/api/organizations/:id/project_cohorts`,
          method: 'GET',
          isArray: true,
        },
      },
    );

    ProjectCohortResource.queryOne = queryOne;

    /**
     * Custom queryByOrganizationWithOrg that injects the Organization info
     * into the `organization` property of each retrieved Project Cohort.
     * @param  {[type]} organization [description]
     * @return {[type]}              [description]
     */
    ProjectCohortResource.queryByOrganizationWithOrg = function(organization) {
      return $http({
        url: `//${hostingDomain}/api/organizations/${
          organization.uid
        }/project_cohorts`,
        method: 'GET',
        isArray: true,
        transformResponse: addOrganizationToProjectCohort,
      }).then(function success(response) {
        return response.data;
      });

      function addOrganizationToProjectCohort(data) {
        const transformed = angular.fromJson(data);

        transformed.forEach(pc => {
          pc.organization = organization;
        });

        return transformed;
      }
    };

    ProjectCohortResource.OPEN_STATUS = 'open';
    ProjectCohortResource.CLOSED_STATUS = 'closed';

    // |     value         |                     description                   |
    // |-------------------|---------------------------------------------------|
    // | 'custom'          | redirects to an org-set URL for identification    |
    // | 'name_or_id'      | a single text field, prompting "enter name or id" |
    // | 'first_mi_last'   | prompt for first, middle initial, and last,       |
    // |                   | stripped to initials plus last name, e.g. 'jdoe'  |
    // | 'email_confirm'   | two email fields, which must match                |
    // | 'skipped'         | nothing displayed, no token collected             |

    ProjectCohortResource.PORTAL_TYPES = [
      'custom',
      'name_or_id',
      'first_mi_last',
      'email_confirm',
      'skipped',
    ];

    return ProjectCohortResource;
  });
};

export default projectCohortService;
