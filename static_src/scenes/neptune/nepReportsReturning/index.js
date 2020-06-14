import some from 'lodash/some';
import values from 'lodash/values';

import template from './index.html';

const nepReportsReturning = ngModule => {
  function controller(
    $q,
    ModalService,
    Organization,
    Program,
    ProjectCohort,
    User,
  ) {
    const vm = this;

    // Lookups. To determine if an organization has participated or is
    // participating in particular programs/cohorts. Both objects are like:
    //
    // {
    //   Organization_1234: {
    //     cg17: {
    //       2017_spring: true,
    //     }
    //   }
    // }
    vm.participated = {};
    vm.participating = {};

    // Returning orgs: `participated` cohort followed by another enrollment at
    // any point later.
    vm.returning = {};
    // New orgs: their first enrollment is in the latest cohort available.
    vm.new = {};

    // Track the number of organization cards that have been selected.
    vm.cardsSelected = 0;

    // Loading flags for each query type.
    vm.loadingPrograms = true;
    vm.loadingOrganizations = true;
    vm.loadingProjectCohorts = {};

    vm.$onInit = function () {
      const pPromise = Program.queryAllPrograms()
        .then(programs => sortAlpha(programs, 'label'))
        .then(programs => convertProgramsCohortsToArray(programs))
        .then(programs => determineLongestRunningProgram(programs))
        .then(programs => (vm.programs = programs))
        .then(() => (vm.loadingPrograms = false))
        .then(() => queryProjectCohortData());

      const oPromise = Organization.query({})
        .$promise.then(organizations =>
          organizations.filter(o => o.status !== Organization.REJECTED_STATUS),
        )
        .then(organizations => sortAlpha(organizations, 'name'))
        .then(organizations => (vm.organizations = organizations))
        .then(() => (vm.loadingOrganizations = false));

      $q.all([pPromise, oPromise]).then(() => {
        queryLiaisonData();
        calculateReturningStats();
        calculateNewStats();
      });
    };

    vm.isLoading = function () {
      return (
        vm.loadingPrograms ||
        vm.loadingOrganizations ||
        some(vm.loadingProjectCohorts, Boolean)
      );
    };

    /**
     * Sorts the provided entities, on the provided property, alphabetically.
     * @param  {Array} entities        entities to sort
     * @param  {String} propertyToSort the property to sort on
     * @return {Array}                 the sorted array
     */
    function sortAlpha(entities, propertyToSort) {
      return entities.sort((a, b) =>
        a[propertyToSort].localeCompare(b[propertyToSort]),
      );
    }

    /**
     * Convert cohorts object to array for ng-repeat use.
     * @param  {Array} programs Neptune programs
     * @return {Array}          Neptune programs, with cohorts as an array
     */
    function convertProgramsCohortsToArray(programs) {
      programs.forEach(p => {
        p.cohorts = sortAlpha(values(p.cohorts), 'label');
      });
      return programs;
    }

    /**
     * Determines the number of cohorts in the longest running program. This
     * helps with displaying our report so we know how wide to make each cohort
     * column in the report.
     * @param  {Array} programs Neptune programs
     * @return {Array}          the provided array
     */
    function determineLongestRunningProgram(programs) {
      let longest = 0;
      programs.forEach(p => {
        if (p.cohorts.length > longest) {
          longest = p.cohorts.length;
        }
      });
      vm.longestProgramLength = longest;
      return programs;
    }

    /**
     * Returns the width of the display column. This is used in the template to
     * set the td width of cohorts status.
     * @return {String} width in percentage followed by '%' symbol
     */
    vm.cohortColumnWidth = function () {
      return `${(1 / (vm.longestProgramLength + 1)) * 100}%`;
    };

    /**
     * Queries for project cohort data. Since this is a large report, and to
     * avoid triton cohorts from being queried (which happens if you don't
     * specify a program_label), we load each program separately. This also
     * allows us to display loading indicators for each query.
     * @return {undefined}
     */
    function queryProjectCohortData() {
      const programLabels = vm.programs.map(p => p.label);

      // Set loading flags for each program
      programLabels.forEach(label => (vm.loadingProjectCohorts[label] = true));

      // Query for ProjectCohorts in each program
      return $q.all(
        programLabels.map(programLabel =>
          ProjectCohort.query({
            status: 'open',
            program_label: programLabel,
          })
            .$promise.then(projectCohorts =>
              createOrganizationParticipationLookup(projectCohorts),
            )
            .then(() => {
              vm.loadingProjectCohorts[programLabel] = false;
            }),
        ),
      );
    }

    /**
     * Iterates over each project cohort and marks the associated organization
     * either as participated or participating. See called functions for more.
     * @param  {Array} projectCohorts array of project cohorts
     * @return {Array}                the provided array
     */
    function createOrganizationParticipationLookup(projectCohorts) {
      projectCohorts.forEach(
        pc =>
          // If the task_ids array has length, there are associated reports that
          // have been uploaded to the project cohort, meaning we count them
          // as having participated.
          pc.completed_report_task_ids.length
            ? markParticipated(pc)
            : markParticipating(pc),
      );

      return projectCohorts;
    }

    /**
     * Marks the organization associated with the provided project cohort as
     * participated. Participated means it's flagged with participated in the
     * datastore -- which means the project cohort has had some student
     * participation.
     * @param  {Object} projectCohort the project cohort
     * @return {undefined}
     */
    function markParticipated(projectCohort) {
      vm.participated[projectCohort.organization_id] =
        vm.participated[projectCohort.organization_id] || {};
      vm.participated[projectCohort.organization_id][
        projectCohort.program_label
      ] =
        vm.participated[projectCohort.organization_id][
          projectCohort.program_label
        ] || {};
      vm.participated[projectCohort.organization_id][
        projectCohort.program_label
      ][projectCohort.cohort_label] = true;
    }

    /**
     * Marks the organization associated with the provided project cohort as
     * participating. Participating just means it's enrolled and not marked as
     * having participated.
     * @param  {Object} projectCohort the project cohort
     * @return {undefined}
     */
    function markParticipating(projectCohort) {
      vm.participating[projectCohort.organization_id] =
        vm.participating[projectCohort.organization_id] || {};
      vm.participating[projectCohort.organization_id][
        projectCohort.program_label
      ] =
        vm.participating[projectCohort.organization_id][
          projectCohort.program_label
        ] || {};
      vm.participating[projectCohort.organization_id][
        projectCohort.program_label
      ][projectCohort.cohort_label] = true;
    }

    /**
     * Queries for liaison data and adds to organization
     * @return {undefined}
     */
    function queryLiaisonData() {
      vm.organizations
        .filter(organization => vm.displayOrganization(organization))
        .forEach(organization => {
          User.get({ id: organization.liaison_id }).$promise.then(
            user => (organization.liaison = user),
          );
        });
    }

    /**
     * Determines if the organization should be displayed. This function is used
     * in the template.
     * @param  {Object} organization the organization
     * @return {Boolean}             true if the organization should display
     */
    vm.displayOrganization = function (organization) {
      const anyParticipation =
        vm.participated[organization.uid] || vm.participating[organization.uid];

      const selectedProgramParticipation = vm.selected
        ? vm.displayProgramRow(organization, vm.selected)
        : true;

      return anyParticipation && selectedProgramParticipation;
    };

    /**
     * Determines if the organization's associated program row should display.
     * This function is used in the template. Each organization displays a row
     * for each program is has participated in or is enrolled in.
     * @param  {Object} organization the organization
     * @param  {Object} program      the associated program
     * @return {Boolean}             true if the row should display
     */
    vm.displayProgramRow = function (organization, program) {
      return (
        (vm.participated[organization.uid] &&
          vm.participated[organization.uid][program.label]) ||
        (vm.participating[organization.uid] &&
          vm.participating[organization.uid][program.label])
      );
    };

    /**
     * Determines which status icon to display. This function is used in the
     * template. Each organization displays a row for each program and column
     * for each program's cohort.
     * @param  {Object} organization the organization
     * @param  {Object} program      the associated program
     * @param  {Object} cohort       the associated cohort
     * @return {String}              the icon class(es)
     */
    vm.displayIcon = function (organization, program, cohort) {
      if (participatedIn(organization, program, cohort)) {
        return 'fa-check-circle participated';
      }

      if (participatingIn(organization, program, cohort)) {
        return 'fa-adjust participating';
      }

      return 'fa-circle-o';
    };

    /**
     * Returns true if the organization/program/cohort combination appears in
     * the `participated` lookup object.
     * @param  {Object} organization organization
     * @param  {Object} program      program
     * @param  {Object} cohort       cohort
     * @return {Boolean}             true if appears, false if not
     */
    function participatedIn(organization, program, cohort) {
      return (
        vm.participated[organization.uid] &&
        vm.participated[organization.uid][program.label] &&
        vm.participated[organization.uid][program.label][cohort.label]
      );
    }

    /**
     * Returns true if the organization/program/cohort combination appears in
     * the `participating` lookup object.
     * @param  {Object} organization organization
     * @param  {Object} program      program
     * @param  {Object} cohort       cohort
     * @return {Boolean}             true if appears, false if not
     */
    function participatingIn(organization, program, cohort) {
      return (
        vm.participating[organization.uid] &&
        vm.participating[organization.uid][program.label] &&
        vm.participating[organization.uid][program.label][cohort.label]
      );
    }

    /**
     * Returns the index of the first cohort within a program that an
     * organization has participated in.
     * @param  {Object} organization organization
     * @param  {Object} program      program
     * @return {Number}              index of cohort participated in, else -1
     */
    function participatedInIndex(organization, program) {
      // return first index of cohort that organization participated in
      for (let i = 0; i < program.cohorts.length; i += 1) {
        if (participatedIn(organization, program, program.cohorts[i])) {
          return i;
        }
      }

      return -1;
    }

    /**
     * Returns the index of the last cohort within a program that an
     * organization has participated or enrolled (participating) in.
     * @param  {Object} organization organization
     * @param  {Object} program      program
     * @return {Number}              index of cohort enrolled in, else -1
     */
    function participatingInIndex(organization, program) {
      for (let i = program.cohorts.length - 1; i >= 0; i -= 1) {
        if (
          participatedIn(organization, program, program.cohorts[i]) ||
          participatingIn(organization, program, program.cohorts[i])
        ) {
          return i;
        }
      }

      return -1;
    }

    /**
     * Returns the number of organizations matching the currently selected
     * program filter.
     * @return {Number} number of organizations
     */
    vm.totalOrganizationsEnrolled = function () {
      return vm.organizations.filter(o => vm.displayOrganization(o)).length;
    };

    /**
     * Calculates the number of returning organizations for each program. A
     * returning organization is considered one which had a cohort in which it
     * is considered having `participated` followed by another enrollment.
     * These do not need to be consecutive.
     * @return {undefined}
     */
    function calculateReturningStats() {
      // initialize returning stats for each program
      vm.programs.forEach(program => (vm.returning[program.label] = 0));

      // for each organization
      vm.organizations.forEach(organization => {
        // for each program
        vm.programs.forEach(program => {
          // determine if participated cohort happened && happened before
          // another enrolled cohort
          const pedIndex = participatedInIndex(organization, program);
          const pingIndex = participatingInIndex(organization, program);

          if (pedIndex > -1 && pingIndex > -1) {
            if (pedIndex < pingIndex) {
              vm.returning[program.label] += 1;
            }
          }
        });
      });
    }

    /**
     * Calculates the number of new organizations for each program. A new
     * organization is one in which it's first enrollment is the latest cohort
     * of a program.
     * @return {undefined}
     */
    function calculateNewStats() {
      // initialize returning stats for each program
      vm.programs.forEach(program => (vm.new[program.label] = 0));

      // for each organization
      vm.organizations.forEach(organization => {
        // for each program
        vm.programs.forEach(program => {
          // determine if the participating cohort happened && happened in the
          // last available cohort
          const pingIndex = participatingInIndex(organization, program);

          if (pingIndex > -1) {
            if (pingIndex === program.cohorts.length - 1) {
              vm.new[program.label] += 1;
            }
          }
        });
      });
    }

    /**
     * Counts organizations card selected and sets `cardSelected`, which is used
     * in the template display.
     * @return {undefined}
     */
    function calculateCardSelected() {
      vm.cardsSelected = vm.organizations.filter(o => o.selected).length;
    }

    /**
     * Toggles the selected state of the provided organization.
     * @param  {Object} organization organization
     * @return {undefined}
     */
    vm.toggle = function (organization) {
      organization.selected = !organization.selected;
      calculateCardSelected();
    };

    /**
     * Sets selected state to true of all currently displayed organizations.
     * @return {undefined}
     */
    vm.selectAllVisible = function () {
      vm.organizations
        .filter(o => vm.displayOrganization(o))
        .forEach(o => (o.selected = true));
      calculateCardSelected();
    };

    /**
     * Sets selected state to false of all organizations.
     * @return {undefined}
     */
    vm.deselectAll = function () {
      vm.organizations.forEach(o => (o.selected = false));
      calculateCardSelected();
    };

    /**
     * Passes the selected organizations data to email modal controller/window.
     * @return {undefined}
     */
    vm.openEmailModal = function () {
      // Convert selected organization into expected object format
      const dataRows = vm.organizations
        .filter(o => o.selected)
        .map(organization => {
          return {
            organization,
            liaison: organization.liaison,
          };
        });

      // Open email modal
      ModalService.showModal({
        template: require('../../../app_manager/components/dashboard/email_modal.view.html'),
        controller: 'EmailModalController',
        bodyClass: 'neptune-modal-open',
        inputs: {
          projectDataRows: dataRows,
        },
      });
    };
  }

  ngModule.component('nepReportsReturning', {
    controller,
    template,
  });
};

export default nepReportsReturning;
