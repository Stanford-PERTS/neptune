/**
 * Dashboard Component
 */

import getShortUid from 'utils/getShortUid';
import template from './dashboard.view.html';

(function () {
  'use strict';
  window.ngModule.component('nepDashboard', {
    template,
    controller(
      $q,
      $scope,
      $state,
      $transitions,
      $window,
      Dashboard,
      Checkpoint,
      ModalService,
      Organization,
      Program,
      ProjectCohort,
      User,
    ) {
      const vm = this;

      // Track transition change deregister functions
      const deregisterTransitions = [];

      /**
       * onInit
       */
      vm.$onInit = function () {
        // Tracks which program, cohort, etc., have been selected
        vm.selected = {
          // program
          // cohort,
          view: 'list', // list, statistics, advanced, search
          orderBy: 'project.organization_name',
          filters: {
            priority: 'any',
            orgApproved: 'any',
            orgRejected: 'no',
            termsAccepted: 'any',
            programApproved: 'any',
            projectCohortStatus: 'yes',
            orgName: '',
          },
        };

        // Is data loading?
        vm.loading = true;

        // Authenticated user
        vm.user = User.getCurrent();
        vm.isSuperAdmin = vm.user.user_type === 'super_admin';

        // Place projectCohortId on $scope
        vm.projectCohortId = getShortUid($state.params.projectCohortId);

        // Update $scope's projectCohort on state changes
        deregisterTransitions.push(
          $transitions.onSuccess({ to: 'dashboard.**' }, transition => {
            vm.projectCohortId = transition.params('to').projectCohortId;
          }),
        );

        deregisterTransitions.push(
          $transitions.onSuccess({ to: 'dashboard' }, () => {
            vm.projectCohortId = null;
          }),
        );

        // Close Admin Panels when navigating to tasks
        deregisterTransitions.push(
          $transitions.onSuccess({ to: 'dashboard.tasks.**' }, () => {
            vm.closeAdminPanel();
          }),
        );

        if (vm.isSuperAdmin) {
          // Handle PERTS Admins (super_admin)
          placeVisibleProjectCohortOnScope()
            .then(() => Program.queryAllPrograms())
            .then(placeProgramsOnScope)
            .then(selectActiveProgram)
            .then(placeCohortsOnScope)
            .then(() => {
              // search by organization
              if ($state.params.organization_id) {
                vm.selected.view = 'search';
                return vm.query({
                  organization_id: $state.params.organization_id,
                });
              }

              // search by program_label
              if ($state.params.program_label) {
                return vm.query({ program_label: $state.params.program_label });
              }

              // single project cohort
              if (vm.projectCohortId) {
                return vm.query({ project_cohort_id: vm.projectCohortId });
              }
            })
            .then(() => {
              if ($state.params.adminPanelId && $state.params.adminPanel) {
                maintainAdminPanelState(
                  $state.params.adminPanelId,
                  $state.params.adminPanel,
                );
              }
            })
            .then(vm.updateSelectedCount)
            .then(() => {
              vm.loading = false;
            });

          vm.loadingOrganizations = true;
          Organization.getAllNames({}).$promise.then(organizations => {
            vm.organizations = organizations;
            vm.loadingOrganizations = false;
          });
        } else {
          // Handle Org Admins (not super_admin)
          vm.selected.filters = {};
          vm.query();
        }

        // At the moment, dashboard data is not the same as tasklist data. When
        // a checkpoint has been updated, we need to recalculate the visible
        // checkpoints for the associated projectDataRow.
        $scope.$on('/Checkpoint/updated', () => {
          if (vm.projectCohortId) {
            const pc = vm.projectDataRows.find(
              row => row.projectCohort.short_uid === vm.projectCohortId,
            );
            Dashboard.updateProjectDataRow(pc);
          }
        });
      };

      /**
       * Wrapper around Dashboard.query that handles data binding and ui.
       * @param  {Object} params query options
       * @return {Array}         rows of Dashboard data (project cohorts)
       */
      vm.query = function (params) {
        vm.loading = true;

        return Dashboard.query(params).then(dataRows => {
          vm.projectDataRows = dataRows;
          vm.loading = false;

          return dataRows;
        });
      };

      // Show Functions. Since some of the logic to determine whether parts of
      // the app should show/hide are getting complicated, we're using helper
      // functions.
      vm.showSelectProgram = () => vm.isSuperAdmin && !vm.projectCohortId;

      vm.showSelectCohort = () => {
        if (
          vm.loading ||
          vm.projectCohortId ||
          vm.selected.view === 'advanced'
        ) {
          return false;
        }

        if (vm.selected.program) {
          return true;
        }

        return false;
      };

      vm.showSelectView = () => {
        if (vm.loading || vm.projectCohortId) {
          return false;
        }

        if (vm.selected.program) {
          return true;
        }

        return false;
      };

      vm.showListOptions = () => {
        if (vm.loading || vm.projectCohortId) {
          return false;
        }

        if (vm.selected.program && vm.selected.view === 'list') {
          return true;
        }

        return false;
      };

      vm.showSelectProgramPrompt = () => {
        if (vm.selected.view === 'search') {
          return false;
        }

        if (vm.isSuperAdmin && !vm.selected.program && !vm.loading) {
          return true;
        }

        return false;
      };

      vm.showCohortsNoMatches = () => {
        // The check for no project cohorts happen in the template since we
        // cannot access that variable in this scope.
        if (
          vm.isSuperAdmin &&
          !vm.loading &&
          vm.selected.program &&
          vm.selected.view === 'list'
        ) {
          return true;
        }

        return false;
      };

      vm.showCohortNoEnrolled = () => {
        // The check for no project cohorts happen in the template since we
        // cannot access that variable in this scope.
        if (!vm.isSuperAdmin && !vm.loading) {
          return true;
        }

        return false;
      };

      vm.showAssociatedOrganizations = () => {
        if (vm.loading || vm.projectCohortId) {
          return false;
        }

        if (!vm.isSuperAdmin && vm.assc_organizations) {
          return true;
        }

        return false;
      };

      vm.showView = (view = null) => {
        if (
          vm.isSuperAdmin &&
          vm.selected.program &&
          vm.selected.view === view &&
          !vm.loading
        ) {
          return true;
        }

        return false;
      };

      vm.showCohortList = () => ['list', 'search'].includes(vm.selected.view);

      // Handlers
      vm.changeSelectedProgram = () => {
        if (vm.selected.program && vm.selected.program.label) {
          $state.go('dashboard.program', {
            // set via the program select drop down
            program_label: vm.selected.program.label,
          });
        } else {
          // when user deselects a program
          $state.go('dashboard');
        }
      };

      vm.changeSelectedCohort = () => {
        syncSelectedCohortFilter();
      };

      // Sync selected cohort to filters list. In order to avoid changing the
      // way that the selectedFilter function works (and interacts with the
      // Program Statistics component) we need to sync up the selected cohort
      // with the filters object.
      function syncSelectedCohortFilter() {
        vm.selected.filters.cohort = vm.selected.cohort;
      }

      // Data on Scope
      function placeVisibleProjectCohortOnScope() {
        // @todo: For super admins specifically, loading data for the dashboard
        // doesn't work when there's no program selected. That means for a
        // hard load of a tasklist view (dashboard.tasks.checkpoint.task), when
        // the program dropdown i.e. vm.selected.program has no value, loading
        // doesn't work. This is a workaround that sets the selected program
        // based on the current project cohort, if there is one. A proper fix
        // would add a method to the Dashboard service which could load
        // everything necessary for a single project cohort.
        if ($state.params.projectCohortId) {
          vm.projectCohort = ProjectCohort.get({
            id: $state.params.projectCohortId,
          });
          return vm.projectCohort.$promise;
        }
        return $q.when();
      }

      function placeProgramsOnScope(programs) {
        vm.programs = programs;
        return programs;
      }

      function selectActiveProgram(programs) {
        // When viewing a single project cohort, we need to mark its program
        // as the currently selected program so that, if we navigate to one of
        // the admin panels, we know what program list to display project
        // cohort within.
        if ($state.params.projectCohortId) {
          vm.selected.program = programs.find(
            p => p.label === vm.projectCohort.program_label,
          );
        }

        // Sync up selected program (from params) with vm.selected.program.
        if ($state.params.program_label) {
          vm.selected.program = programs.find(
            p => p.label === $state.params.program_label,
          );
        }

        return programs;
      }

      function placeCohortsOnScope() {
        if (!vm.selected.program) {
          return null;
        }

        return Program.cohorts(vm.selected.program).then(
          cohorts => (vm.cohorts = cohorts),
        );
      }

      vm.updateSelectedCount = function () {
        vm.projectDataRowsSelected = vm.projectDataRows
          ? vm.projectDataRows.filter(pc => pc.selected).length
          : 0;
      };

      vm.selectAllVisible = function (visibleDataRows) {
        visibleDataRows.forEach(pc => {
          pc.selected = true;
        });
        vm.updateSelectedCount();
      };

      vm.deselectAllVisible = function (visibleDataRows) {
        visibleDataRows.forEach(pc => {
          pc.selected = false;
        });
        vm.updateSelectedCount();
      };

      vm.approveParticipation = function () {
        const projectDataRows = vm.projectDataRows.filter(p => p.selected);
        ModalService.showModal({
          template: require('./approve_participation_modal.view.html'),
          controller: 'ApproveParticipationController',
          bodyClass: 'neptune-modal-open',
          inputs: {
            program: vm.selected.program,
            projectDataRows,
          },
        });
      };

      /**
       * openEmailModal opens the email modal, providing it with the liaisons
       * from the selected projectDataRows.
       */
      vm.openEmailModal = function () {
        const selectedProjectDataRows = vm.projectDataRows.filter(
          p => p.selected,
        );

        Dashboard.getLiaisonsByProjects(selectedProjectDataRows).then(
          projectDataRows => {
            ModalService.showModal({
              template: require('./email_modal.view.html'),
              controller: 'EmailModalController',
              bodyClass: 'neptune-modal-open',
              inputs: {
                projectDataRows,
              },
            });
          },
        );
      };

      /**
       * onDestroy
       */
      vm.$onDestroy = function () {
        deregisterTransitions.forEach(deregister => deregister());
      };

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
       * @param {Object} projectDataRow - a composite object with API resources.
       * @param {number} index - the index in the full array of the value
       *   currently being considered (not used)
       * @param {Array} array - the full array of values being filtered (not
       *   used).
       * @param {Object} filters - optional, if undefined uses vm.filters,
       *   otherwise uses provided object.
       * @return {boolean}
       */
      vm.selectedFilter = function (projectDataRow, index, array, filters) {
        const filterState = [];
        if (filters === undefined) {
          // We're in normal dashboard mode. Consider context in the vm.

          // We're viewing a single Project Cohort
          if (vm.projectCohortId) {
            filterState.push(
              projectDataRow.projectCohort.short_uid === vm.projectCohortId,
            );
            // immediately return, since we're only viewing one project cohort
            return filterState.every(identity => identity);
          }

          filters = vm.selected.filters;
        } // else we're using provided filters, act like a pure function.

        // Always filter out public organizations.
        filterState.push(
          projectDataRow.project.organization_name !== 'Organization_public',
        );

        if (!vm.isSuperAdmin) {
          return filterState.every(identity => identity);
        }
        // All filters below are only applied to super (PERTS) admins.

        // Cohort
        if (vm.selected.cohort) {
          filterState.push(
            projectDataRow.program_cohort.label === vm.selected.cohort.label,
          );
        }

        // Organization Approval
        if (filters.orgApproved === 'yes') {
          filterState.push(
            projectDataRow.project.organization_status ===
              Organization.APPROVED_STATUS,
          );
        }

        if (filters.orgApproved === 'no') {
          filterState.push(
            projectDataRow.project.organization_status !==
              Organization.APPROVED_STATUS,
          );
        }

        // Organization Rejected
        if (filters.orgRejected === 'yes') {
          filterState.push(
            projectDataRow.project.organization_status === 'rejected',
          );
        }

        if (filters.orgRejected === 'no') {
          filterState.push(
            projectDataRow.project.organization_status !== 'rejected',
          );
        }

        // Terms of Use Accepted
        if (filters.termsAccepted === 'yes') {
          filterState.push(
            projectDataRow.projectCheckpoint.status !==
              Checkpoint.INCOMPLETE_STATUS,
          );
        }

        if (filters.termsAccepted === 'no') {
          filterState.push(
            projectDataRow.projectCheckpoint.status ===
              Checkpoint.INCOMPLETE_STATUS,
          );
        }

        // Program Approved
        if (filters.programApproved === 'yes') {
          filterState.push(
            projectDataRow.projectCheckpoint.status ===
              Checkpoint.COMPLETE_STATUS,
          );
        }

        if (filters.programApproved === 'no') {
          filterState.push(
            projectDataRow.projectCheckpoint.status !==
              Checkpoint.COMPLETE_STATUS,
          );
        }

        // Project Priority Status
        if (filters.priority === 'yes') {
          filterState.push(projectDataRow.project.priority);
        }

        if (filters.priority === 'no') {
          filterState.push(!projectDataRow.project.priority);
        }

        // Project Cohort Status
        if (filters.projectCohortStatus === 'yes') {
          filterState.push(projectDataRow.projectCohort.status_vm === 'open');
        }

        if (filters.projectCohortStatus === 'no') {
          filterState.push(projectDataRow.projectCohort.status_vm === 'closed');
        }

        // Organization Name Search
        if (filters.orgName && filters.orgName.length) {
          filterState.push(
            projectDataRow.project.organization_name
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
          return vm.selectedFilter(projectDataRow, index, array, filters);
        };
      };

      /**
       * Toggle Admin Panel flag.
       * @param  {Object} dataRow   single row of Dashboard data (project cohort)
       * @param  {string} panelName name of admin panel to open
       */
      vm.toggleAdminPanel = function (projectCohort, panelName) {
        // Only one admin panel open per project cohort card.
        projectCohort.adminPanel = projectCohort.adminPanel || false;
        projectCohort.adminPanel =
          projectCohort.adminPanel === panelName ? false : panelName;

        if (projectCohort.adminPanel) {
          // When opening an admin panel, if we're not currently at
          // `dashboard.programs`, then we need to route there so that the
          // project cohort card & panel appear in the cohort list with other
          // project cohort cards.
          //
          // We do not want to change routes if we're already displaying the
          // list because that would close any already open panels, and we want
          // to allow multiple to be open.
          //
          // Note: We're making the assumption that the user will want to see
          // this project cohort within the context of the program.

          if (!$state.is('dashboard.program') && vm.selected.program) {
            $state.go('dashboard.program', {
              program_label: vm.selected.program.label,
              adminPanelId: projectCohort.projectCohort.uid,
              adminPanel: panelName,
            });
          }
        }
      };

      /**
       * If we are navigating from a single project cohort view to a list view,
       * it might be because we're clicked on an action button to open an admin
       * panel. This function sets an admin panel based on provided uid and
       * panel name.
       * @param  {string} projectCohortId UID of project cohort
       * @param  {string} panelName       admin panel name
       */
      function maintainAdminPanelState(projectCohortId, panelName) {
        vm.projectDataRows.every(dataRow => {
          if (dataRow.projectCohort.uid === projectCohortId) {
            dataRow.adminPanel = panelName;
            // once we find the row, short circuit out
            return false;
          }

          return true;
        });
      }

      /**
       * Set flag for all admin panels to false (closed).
       */
      vm.closeAdminPanel = function () {
        Dashboard.closeAdminPanels();
      };

      /**
       * angucomplete-alt (organization search) support functions.
       */
      // Returns an array of projectDataRows with a matching organization name.
      vm.orgSearch = function (name, projectDataRows) {
        return projectDataRows.filter(r =>
          r.project.organization_name
            .toLowerCase()
            .includes(name.toLowerCase()),
        );
      };

      vm.orgSearchAll = function (name, organizations) {
        return organizations.filter(o =>
          o.name.toLowerCase().includes(name.toLowerCase()),
        );
      };

      // When user inputs text into search field, update the view filter
      vm.inputChanged = function (str) {
        vm.selected.filters.orgName = str;
      };

      // When we select an organization search result, set it's associated
      // projectDataRow as active.
      vm.orgSearchChange = function ({ originalObject: projectDataRow }) {
        // vm.projectCohortId = projectDataRow.projectCohort.short_uid;
        $state.go('dashboard.tasks', {
          projectCohortId: projectDataRow.projectCohort.short_uid,
        });
      };

      vm.orgSearchChangeAll = function ({ originalObject: organization }) {
        $state.go('dashboard.organization', {
          organization_id: organization.uid,
        });
      };

      vm.orgSearchClear = function (program) {
        vm.projectDataRows = [];
        vm.selected.program = program || null;
        if (vm.selected.view === 'search') {
          vm.selected.view = 'list';
        }
        $state.go('dashboard');
      };
    },
  });
})();
