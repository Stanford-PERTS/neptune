(function () {
  'use strict';

  function OptionsSearchController($scope, $state, $transitions, Organization) {
    const vm = this;

    vm.$onInit = function () {
      // Allow template to access the route
      vm.$state = $state;

      // Query for organization names only when route is `dashboard`
      if (vm.showSearchAll()) {
        getAllOrganizationNames();
      }
    };

    const deregister = [];

    // Query for organization names when route changes to `dashboard`
    deregister.push(
      $transitions.onSuccess(
        {

          /* any state change, we let the function decide */
        },
        () => {
          if (vm.showSearchAll()) {
            getAllOrganizationNames();
          }
        },
      ),
    );

    // Clear org search filter when leaving a dashboard.query
    deregister.push(
      $transitions.onExit({ from: 'dashboard.query' }, () => {
        $scope.$broadcast('angucomplete-alt:clearInput');
        vm.options.filters.orgName = null;
      }),
    );

    function getAllOrganizationNames() {
      vm.loading = true;

      Organization.getAllNames({}).$promise.then(organizations => {
        vm.organizations = organizations;
        vm.loading = false;
      });
    }

    vm.$onDestroy = function () {
      deregister.forEach(dereg => dereg());
    };

    // Show all?
    vm.showSearchAll = function () {
      return (
        $state.is('dashboard') ||
        $state.params.projectCohortId ||
        $state.params.organization_id
      );
    };

    // All Search

    vm.searchAll = function (name, organizations) {
      return organizations.filter(o =>
        o.name.toLowerCase().includes(name.toLowerCase()),
      );
    };

    vm.searchAllSelected = function (searchObject) {
      if (!searchObject) {
        return;
      }

      const organization = searchObject.originalObject;

      $state.go('dashboard.query', {
        organization_id: organization.uid,
      });
    };

    vm.showSearchAllClear = function () {
      return $state.params.organization_id;
    };

    vm.searchAllClear = function () {
      vm.resetDashboard();
    };

    // Program Limited Search

    vm.inputChanged = function (str) {
      vm.options.filters.orgName = str;
    };

    vm.searchProgram = function (name, cardRows) {
      return cardRows.filter(cardRow =>
        cardRow.project.organization_name
          .toLowerCase()
          .includes(name.toLowerCase()),
      );
    };

    vm.searchProgramSelected = function (searchParams) {
      // Check for an empty call. Using 'angucomplete-alt:clearInput' calls this
      // function without any parameters.
      if (!searchParams) {
        return;
      }

      const cardRow = searchParams.originalObject;

      $state.go('dashboard.tasks', {
        projectCohortId: cardRow.projectCohort.short_uid,
      });
    };

    vm.showSearchProgramClear = function () {
      return vm.options.filters.orgName && vm.options.filters.orgName.length;
    };

    vm.searchProgramClear = function () {
      $scope.$broadcast('angucomplete-alt:clearInput');
      vm.options.filters.orgName = null;

      // TODO REDIRECT If we're viewing a single project cohort, redirect back
      // to dashboard.query using the current card's program.
    };
  }

  window.ngModule.component('nepOptionsSearch', {
    bindings: {
      cardRows: '<',
      options: '<',

      resetDashboard: '&',
    },
    controller: OptionsSearchController,
    template: require('./options_search.view.html'),
  });
})();
