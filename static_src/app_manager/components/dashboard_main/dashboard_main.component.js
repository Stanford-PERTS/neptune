(function () {
  'use strict';

  function DashboardMainController(
    $scope,
    $state,
    Checkpoint,
    Organization,
    User,
  ) {
    const vm = this;

    vm.$onInit = function () {
      vm.$state = $state;

      initUser();

      // search by program_label
      if ($state.params.program_label) {
        if ($state.params.cohort_label) {
          vm.query({
            params: {
              program_label: $state.params.program_label,
              cohort_label: $state.params.cohort_label,
            },
          });
          // A side-effect of query() is calling changeSelected(). See nepDash.
        } else {
          // If the program changes but we don't query, call this directly:
          vm.changeSelected({ params: $state.params });
        }
      }

      // search by organization
      if ($state.params.organization_id) {
        vm.query({
          params: { organization_id: $state.params.organization_id },
        });
      }

      // search by project cohort id
      if ($state.params.projectCohortId) {
        const cardRowExists = vm.cardRows.find(
          r => r.projectCohort.short_uid === $state.params.projectCohortId,
        );

        // Don't query for cardRow data if it already exists. This avoids
        // loading when navigating from tasks > participation > reports panels.
        if (!cardRowExists) {
          vm.query({
            params: {
              project_cohort_id: $state.params.projectCohortId,
            },
          });
        }
      }

      // this will only be rendered for non-admins on the `dashboard` route
      if (!vm.isSuperAdmin) {
        vm.query({});
      }
    };

    function initUser() {
      vm.user = User.getCurrent();
      vm.isSuperAdmin = User.isSuperAdmin();
    }

    vm.sufficientCardOptionsSpecified = function () {
      // We show either data or a prompt based on whether the user has been
      // specific enough about what they want to look at. Sufficient
      // specificity means either an org or a program cohort. This only applies
      // to a non-specialized dashboard views, i.e. the project cohorts list,
      return (
        !vm.options.view &&
        ((vm.options.program && vm.options.cohort) ||
          $state.params.organization_id)
      );
    };

    // Update cards matching for bulk options component
    $scope.$watch(() => {
      vm.options.cardsMatching = $scope.$eval(
        '$ctrl.cardRows | filter: $ctrl.selectedCards',
      );
    });

    /**
     * Filters
     */

    /**
     * Custom ng-repeat filter to decide which project/organizations to
     * display. Normally operates based on the combined yes/no/all settings
     * in vm.filters. Can also run only one filter if `filters` is specified.
     * The first three arguments must match angular's "predicate function"
     * interface: value, index, array.
     * https://docs.angularjs.org/api/ng/filter/filter
     * @param {Object} cardRow - a composite object with API resources.
     * @param {number} index - the index in the full array of the value
     *   currently being considered (not used)
     * @param {Array} array - the full array of values being filtered (not
     *   used).
     * @param {Object} filters - optional, if undefined uses vm.filters,
     *   otherwise uses provided object.
     * @return {boolean}
     */
    vm.selectedCards = function (cardRow, index, array, filters) {
      const filterState = [];
      if (filters === undefined) {
        // We're in normal dashboard mode. Consider context in the vm.

        // We're viewing a single Project Cohort
        if ($state.params.projectCohortId) {
          filterState.push(
            cardRow.projectCohort.short_uid === $state.params.projectCohortId,
          );
          // immediately return, since we're only viewing one project cohort
          return filterState.every(identity => identity);
        }

        filters = vm.options.filters;
      } // else we're using provided filters, act like a pure function.
      // Always filter out public organizations.
      filterState.push(
        cardRow.project.organization_name !== 'Organization_public',
      );

      if (!vm.isSuperAdmin) {
        return filterState.every(identity => identity);
      }
      // All filters below are only applied to super (PERTS) admins.

      // Organization
      if (vm.options.organizationId) {
        filterState.push(
          cardRow.organization.uid === vm.options.organizationId,
        );

        // If we are searching, then we want to return all matching cards,
        // including closed/rejected. So skip all of the filtering below.
        return filterState.every(identity => identity);
      }

      // Program
      if (vm.options.program) {
        filterState.push(
          cardRow.projectCohort.program_label === vm.options.program,
        );
      }

      // Cohort
      if (vm.options.cohort) {
        filterState.push(cardRow.program_cohort.label === vm.options.cohort);
      }

      // Organization Approval
      if (filters.orgApproved === 'yes') {
        filterState.push(
          cardRow.organization.status === Organization.APPROVED_STATUS,
        );
      }

      if (filters.orgApproved === 'no') {
        filterState.push(
          cardRow.organization.status !== Organization.APPROVED_STATUS,
        );
      }

      // Organization Rejected
      if (filters.orgRejected === 'yes') {
        filterState.push(cardRow.organization.status === 'rejected');
      }

      if (filters.orgRejected === 'no') {
        filterState.push(cardRow.organization.status !== 'rejected');
      }

      // Terms of Use Accepted
      if (filters.termsAccepted === 'yes') {
        filterState.push(
          cardRow.projectCheckpoint.status !== Checkpoint.INCOMPLETE_STATUS,
        );
      }

      if (filters.termsAccepted === 'no') {
        filterState.push(
          cardRow.projectCheckpoint.status === Checkpoint.INCOMPLETE_STATUS,
        );
      }

      // Program Approved
      if (filters.programApproved === 'yes') {
        filterState.push(
          cardRow.projectCheckpoint.status === Checkpoint.COMPLETE_STATUS,
        );
      }

      if (filters.programApproved === 'no') {
        filterState.push(
          cardRow.projectCheckpoint.status !== Checkpoint.COMPLETE_STATUS,
        );
      }

      // Project Priority Status
      if (filters.priority === 'yes') {
        filterState.push(cardRow.project.priority);
      }

      if (filters.priority === 'no') {
        filterState.push(!cardRow.project.priority);
      }

      // Project Cohort Status
      if (filters.projectCohortStatus === 'yes') {
        filterState.push(cardRow.projectCohort.status_vm === 'open');
      }

      if (filters.projectCohortStatus === 'no') {
        filterState.push(cardRow.projectCohort.status_vm === 'closed');
      }

      // Organization Name Search
      if (filters.orgName && filters.orgName.length) {
        filterState.push(
          cardRow.project.organization_name
            .toLowerCase()
            .includes(filters.orgName.toLowerCase()),
        );
      }

      return filterState.every(identity => identity);
    };

    /**
     * Partially apply the filters argument to get a filter function.
     * @param {Object} filters - the rules for how the filter should work,
     *   see vm.filters.
     * @return {Function}
     */
    vm.getFilter = function (filters) {
      return function (projectDataRow, index, array) {
        return vm.selectedCards(projectDataRow, index, array, filters);
      };
    };
  }

  window.ngModule.component('nepDashboardMain', {
    bindings: {
      cardRows: '<',
      options: '<',

      changeSelected: '&',
      updateSelectedCount: '&',
      query: '&',
    },
    controller: DashboardMainController,
    template: require('./dashboard_main.view.html'),
  });
})();
