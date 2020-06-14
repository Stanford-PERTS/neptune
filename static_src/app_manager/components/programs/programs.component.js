/**
 * Programs Component
 */

(function () {
  'use strict';

  window.ngModule.component('nepPrograms', {
    bindings: {

      /**
       * To display Project Cohort by user, provide a User.
       * @type {Object}
       */
      user: '<',

      /**
       * To display Project Cohort by organization, provide an Organization.
       * -- @TODO implement
       * @type {Object}
       */
      organization: '<',

      /**
       * Provide true to force a redirect to the Project Cohort view if
       * there is only 1 Project Cohort found.
       * @type {Boolean}
       */
      redirectOnOne: '<',
    },
    controller: ProgramsController,
    template: require('./programs.view.html'),
  });

  function ProgramsController(
    $state,
    $q,
    Organization,
    Program,
    ProjectCohort,
    yellowstoneDomain,
  ) {
    const vm = this;

    vm.$onInit = function () {
      vm.yellowstoneDomain = yellowstoneDomain;

      const organizations = Organization.queryByUser({ id: vm.user.uid });

      organizations.$promise
        .then(filterOwnedOrganizations)
        .then(getAllProjectCohortsByOrganization)
        .then(mapProgramsIntoProjectCohorts)
        .then(placeProjectCohortsOnScope)
        .then(redirectIfOnlyOneProjectCohort);
    };

    /**
     * Filter an Array of organizations to only user's owned_organizations.
     * @param  {Array} organizations Array of organizations
     * @return {Array}               Array of organizations
     */
    function filterOwnedOrganizations(organizations) {
      return organizations.filter(org =>
        vm.user.owned_organizations.includes(org.uid),
      );
    }

    /**
     * Retrieves an array of Project Cohorts that are associated with the
     * provided array of Organizations.
     * @param  {Array} organizations array of Organizations
     * @return {Array}               array of Project Cohorts
     */
    function getAllProjectCohortsByOrganization(organizations) {
      // Use $q.all to wait on all Project Cohort information...
      return (
        $q
          .all(
            organizations.map(org =>
              ProjectCohort.queryByOrganizationWithOrg(org),
            ),
          )
          // ...so that we can flatten the results arrays before returning.
          .then(function flatten(arrays) {
            return arrays.reduce((a, b) => a.concat(b), []);
          })
      );
    }

    /**
     * Maps the Program information for each Project Cohort into the
     * `program` property of each project cohort in the projectCohorts
     * array.
     * @param  {Array} projectCohorts array of Project Cohorts
     * @return {Array}                array of Project Cohorts
     */
    function mapProgramsIntoProjectCohorts(projectCohorts) {
      return $q.all(
        projectCohorts.map(pc =>
          Program.get({ label: pc.program_label }).$promise.then(program => {
            pc.program = program;
            return pc;
          }),
        ),
      );
    }

    /**
     * Places the Project Cohorts onto $scope for UI access.
     * @param  {Array} projectCohorts array of Project Cohorts
     * @return {Array}                array of Project Cohorts
     */
    function placeProjectCohortsOnScope(projectCohorts) {
      vm.projectCohorts = projectCohorts;
      return projectCohorts; // return back for Promise chaining
    }

    /**
     * If there is only 1 Project Cohort and redirectOnOne is set to true,
     * then redirect to that Project Cohort's view.
     * @param  {Array} projectCohorts array of Project Cohorts
     * @return {Array}                array of Project Cohorts
     */
    function redirectIfOnlyOneProjectCohort(projectCohorts) {
      if (projectCohorts.length === 1 && vm.redirectOnOne) {
        $state.go('projectCohorts', {
          projectCohortId: projectCohorts[0].short_uid,
        });
      }

      return projectCohorts; // return back for Promise chaining
    }
  }
})();
