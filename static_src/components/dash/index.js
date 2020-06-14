/* global setInterval, clearInterval */

import $ from 'jquery';
import template from './index.html';

function controller($state, $timeout, $location, Dashboard, User) {
  const vm = this;

  function setLoading(isLoading = false) {
    vm.loading = isLoading;
  }

  function initUser() {
    vm.user = User.getCurrent();
    vm.isSuperAdmin = User.isSuperAdmin();
  }

  function initOptions() {
    vm.options = {
      // organization_id,
      // program,
      // cohort,
      view: null, // null: list, statistics, advanced
      cardsMatching: [], // pc cards matching filters
      cardsSelected: 0, // number of pc cards selected
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
  }

  function attemptScrollTo() {
    const hash = $location.hash();
    if (!hash) {
      return;
    }

    let tries = 10;
    const handle = setInterval(() => {
      if (tries > 0) {
        tries -= 1;
      } else {
        clearInterval(handle);
      }

      const targetCard = $(`#${hash}`);
      if (targetCard.length) {
        $('html, body').scrollTop(
          targetCard.offset().top - $('nep-navbar').height(),
        );
        clearInterval(handle);
      }
    }, 50);
  }

  vm.resetDashboard = function () {
    initOptions();
    $state.go('dashboard');
  };

  /**
   * Wrapper around Dashboard.query that handles ui.
   * @param  {Object} params query options
   * @return {Array}         rows of Dashboard data (project cohorts)
   */
  vm.query = function (params) {
    setLoading(true);

    if (vm.isSuperAdmin) {
      vm.changeSelected(params);
    }

    return Dashboard.query(params).then(dataRows => {
      vm.updateSelectedCount();
      setLoading(false);
      attemptScrollTo();
      return dataRows;
    });
  };

  vm.changeSelected = function (params) {
    if (params.program_label) {
      vm.changeSelectedProgram(params.program_label);
      // clear out other options
      vm.changeSelectedOrganization(null);
    }

    if (params.cohort_label) {
      vm.changeSelectedCohort(params.cohort_label);
      // clear out other options
      vm.changeSelectedOrganization(null);
    } else {
      vm.changeSelectedCohort(null);
    }

    if (params.organization_id) {
      vm.changeSelectedOrganization(params.organization_id);
      // clear out other options
      vm.changeSelectedProgram(null);
      vm.changeSelectedCohort(null);
    }
  };

  vm.changeSelectedProgram = function (program) {
    vm.options.program = program;
  };

  vm.changeSelectedCohort = function (cohort_label) {
    vm.options.cohort = cohort_label;
  };

  vm.changeSelectedOrganization = function (organizationId) {
    vm.options.organizationId = organizationId;
  };

  vm.updateSelectedCount = function () {
    if (!vm.cardRows) {
      return;
    }

    vm.options.cardsSelected = vm.cardRows.filter(
      cardRow => cardRow.selected,
    ).length;
  };

  vm.selectAllVisible = function () {
    vm.options.cardsMatching.forEach(card => {
      card.selected = true;
    });

    vm.updateSelectedCount();
  };

  vm.deselectAllVisible = function () {
    vm.options.cardsMatching.forEach(card => {
      card.selected = false;
    });
    vm.updateSelectedCount();
  };

  vm.showProgramSelectPrompt = function () {
    if (vm.options.program || vm.options.organizationId) {
      return false;
    }

    if (vm.isSuperAdmin && !vm.loading) {
      return true;
    }

    return false;
  };

  vm.$onInit = function () {
    setLoading(false);

    Dashboard.resetLoaded();

    initUser();
    initOptions();

    vm.cardRows = Dashboard.data;
  };
}

const dash = ngModule => {
  ngModule.component('nepDash', {
    controller,
    template,
  });
};

export default dash;
