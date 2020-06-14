const graphQlService = ngModule => {
  class GraphQL {
    constructor($http, User, hostingDomain) {
      this.$http = $http;
      this.User = User;
      this.hostingDomain = hostingDomain;
    }

    query(params) {
      if (!params || angular.equals(params, {})) {
        const userId = this.User.getCurrent().uid;

        return this.$http({
          method: 'GET',
          url: `//${this.hostingDomain}/api/users/${userId}/dashboard`,
        }).then(res => res.data.project_cohorts);
      } else if (params.project_cohort_id) {
        return this.$http({
          method: 'GET',
          url: `//${this.hostingDomain}/api/tasklists/${
            params.project_cohort_id
          }`,
        }).then(res => res.data.project_cohort);
      } else if (params.program_label || params.organization_id) {
        return this.$http({
          method: 'GET',
          url: `//${this.hostingDomain}/api/dashboard`,
          params,
        }).then(res => {
          if (params.cohort_label) {
            res = prepareProgramCohortResponse(res);
          }
          return res.data.project_cohorts;
        });
      }
    }
  }

  /**
   * To optimize our killer query: loading all project cohorts on the admin
   * dashboard, this returns a slightly different format. Restructure it to
   * match other dashboard queries. This mostly involves repeating values in
   * various convenient places, which the server omits to save on network time.
   * @param   {Object} response with both `project_cohorts` and `program_cohort`
   *                   properties.
   * @returns {Object} typical dashboard response
   */
  function prepareProgramCohortResponse(response) {
    response = angular.copy(response);
    const cohort = response.data.program_cohort;
    delete response.data.program_cohort;
    response.data.project_cohorts.forEach(pc => {
      pc.organization.uid = pc.organization_id;
      pc.program_label = cohort.program_label;
      pc.program_cohort = cohort;
      pc.project.program_name = cohort.program_name;
    });
    return response;
  }

  ngModule.service('GraphQL', GraphQL);
};

export default graphQlService;
