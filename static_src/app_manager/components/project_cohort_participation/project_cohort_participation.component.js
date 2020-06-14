import moment from 'moment';
import getShortUid from 'utils/getShortUid';
import parseUTCDateStr from 'utils/parseUTCDateStr';

(function () {
  'use strict';

  window.ngModule.component('nepProjectCohortParticipation', {
    controller: ProjectCohortParticipationController,
    template: require('./project_cohort_participation.view.html'),
  });

  function ProjectCohortParticipationController(
    $state,
    $q,
    Program,
    ProjectCohort,
    Participation,
    ModalService,
  ) {
    const vm = this;

    vm.progressMarkers = [1, 33, 66, 100];

    vm.$onInit = function () {
      getProjectCohort()
        .then(getProgram)
        .then(placeOnScope)
        .then(getCohort)
        .then(parseCohortDates)
        .then(getParticipation)
        .then(wrangleParticipation);
    };

    vm.startDateChange = function (date) {
      if (!date) {
        wrangleParticipation([]);
        return;
      }
      vm.startDate = date;
      getParticipation().then(wrangleParticipation);
    };

    vm.endDateChange = function (date) {
      if (!date) {
        wrangleParticipation([]);
        return;
      }
      vm.endDate = date;
      getParticipation().then(wrangleParticipation);
    };

    vm.dirtyCalendars = function () {
      return (
        !moment(vm.startDate).isSame(vm.participationOpenDate) ||
        !moment(vm.endDate).isSame(vm.originalEndDate)
      );
    };

    vm.resetCalendars = function () {
      vm.startDate = angular.copy(vm.participationOpenDate);
      vm.endDate = angular.copy(vm.originalEndDate);
      getParticipation().then(wrangleParticipation);
    };

    vm.openDownloadModal = function () {
      ModalService.showModal({
        template: require('./download_modal.view.html'),
        controller: 'ParticipationDownloadModalController',
        bodyClass: 'neptune-modal-open',
        inputs: {
          projectCohort: vm.projectCohort,
          startDate: vm.startDate,
          endDate: vm.endDate,
        },
      });
    };

    function getProjectCohort() {
      const projectCohortId = getShortUid($state.params.projectCohortId);
      const pc = ProjectCohort.get({ id: projectCohortId });
      return $q.all({ projectCohort: pc.$promise });
    }

    function getProgram(loaded) {
      loaded.program = Program.get({
        label: loaded.projectCohort.program_label,
      }).$promise;
      return $q.all(loaded);
    }

    function placeOnScope(loaded) {
      vm.projectCohort = loaded.projectCohort;
      vm.program = loaded.program;
      return loaded;
    }

    function getCohort(loaded) {
      loaded.cohort = loaded.program.cohorts[loaded.projectCohort.cohort_label];
      return loaded;
    }

    function parseCohortDates(loaded) {
      // These will serve as min and max limits on the date input.
      vm.participationOpenDate = parseUTCDateStr(loaded.cohort.open_date);
      // Add one so we can set the expected value
      // in the calendar and not have it be invalid.
      const closeDate = parseUTCDateStr(loaded.cohort.close_date);
      vm.participationCloseDate = moment(closeDate)
        .add(1, 'days')
        .toDate();

      // These will be the value the date inputs hold.
      vm.startDate = angular.copy(vm.participationOpenDate);
      vm.endDate = angular.copy(closeDate);

      // Won't be changed by user input, so we can detect a dirty state.
      vm.originalEndDate = angular.copy(vm.endDate);

      return loaded;
    }

    function getParticipation() {
      const params = {
        id: $state.params.projectCohortId,
        start: moment.utc(vm.startDate).format(),
        // end: moment.utc(vm.endDate).add(1, 'days').format(),
        end: moment.utc(vm.endDate).format(),
      };
      return Participation.queryByProjectCohort(params).$promise;
    }

    function wrangleParticipation(participation) {
      // Wrangle into the following structure, convenient for table display:
      // {
      //   1: {
      //     1: n,
      //     33: n,
      //     66: n,
      //     100: n,
      //   },
      //   2: { ... },
      //   ...
      // }

      // Initialize the table with zeroes in all the right cells, depending
      // on how many surveys there are and what our progress markers/percents
      // are.
      vm.tableParticipation = {};
      vm.program.surveys.forEach((survey, index) => {
        const column = {};
        vm.progressMarkers.forEach(pct => {
          column[pct] = 0;
        });
        vm.tableParticipation[index + 1] = column;
      });

      // Fill in cells if we have data.
      participation.forEach(p => {
        vm.tableParticipation[p.survey_ordinal][p.value] = p.n;
      });
    }
  }
})();
