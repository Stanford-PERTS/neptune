import DupeOrgModalController from './dupe_org_modal';
import template from './index.html';

function controller($state, Dashboard, ModalService, Organization, User) {
  const vm = this;
  let cardRow;

  vm.$onInit = function () {
    vm.loading = true;
    let orgPromise;

    vm.user = User.getCurrent();
    vm.isSuperAdmin = User.isSuperAdmin();
    vm.projectCohortId =
      vm.projectCohortId || $state.params.projectCohortId;

    // What properties can we use to load data? They vary based on where
    // this component is being loaded:
    //
    // 1. /dashboard (pcId passed as prop)
    // 2. /dashboard/:pcId/organization (pcId in route)
    // 3. /organizations/:orgId

    // Retrieve organization data
    if (vm.projectCohortId) {
      orgPromise = Dashboard.getProjectDataRow(vm.projectCohortId, true)
        .then(row => Dashboard.getOrganizationApprovalTask(row))
        .then(row => {
          cardRow = row;
          // Copy the projectDataRow and work with that in the form so that
          // changes don't affect the cards visibility until after it's been
          // saved.
          vm.organization = angular.copy(row.organization);
        });
    } else {
      orgPromise = Organization.get({ id: vm.organizationId }).$promise
        .then(organization => {
          vm.organization = organization;
        });
    }

    // Get all of the various tracking ids, so we can encourage uniqueness
    // in the UI.
    orgPromise
      .then(() => Organization.getAllPoids().$promise)
      .then(allPoids => {
        // indexByPoidType creates an key-value lookup object. Keyed by the
        // `poidType`, values are organization uid.
        const indexByPoidType = (sourceArray, poidType) => {
          const byId = {};

          sourceArray.forEach(element => {
            const id = element.poid[poidType];
            const orgId = element.uid;

            // Exclude if the orgId matches the current organization.uid because
            // we don't want only want to flag when there's a match on *other*
            // organization poids.
            if (id && orgId !== vm.organization.uid) {
              byId[id] = orgId;
            }
          });

          return byId;
        };

        vm.ncesDistrictIds = indexByPoidType(allPoids, 'nces_district_id');
        vm.ncesSchoolIds = indexByPoidType(allPoids, 'nces_school_id');
        vm.ipedsIds = indexByPoidType(allPoids, 'ipeds_id');
        vm.opeIds = indexByPoidType(allPoids, 'ope_id');

        vm.loading = false;
      });
  };

  vm.openDupeModal = function () {
    ModalService.showModal({
      template: require('./dupe_org_modal.html'),
      controller: DupeOrgModalController,
      bodyClass: 'neptune-modal-open',
      inputs: {
        organization: vm.organization,
        update: vm.update,
      },
    });
  };

  vm.update = function () {
    vm.updating = true;
    vm.error = false;
    let updatePromise;

    // @todo: updating the approval task won't work from the org route
    // because the pcId will be undefined, and the current form of
    // Dashboard.updateOrganization() needs it (the whole row).

    if (vm.projectCohortId && vm.isSuperAdmin) {
      // Using angular.copy instead of angular.merge since angular.merge
      // doesn't play nicely with the $resource object. (Results in a
      // maximum call stack error due to circular reference.)
      const rowWithUpdatedOrg = angular.copy(cardRow);
      rowWithUpdatedOrg.organization = angular.copy(vm.organization);

      updatePromise = Dashboard.updateOrganization(rowWithUpdatedOrg)
        .then(() => {
          // Now we can update the organization being displayed so that any
          // changes that affected visibility filters will take place.
          cardRow.organization = angular.copy(vm.organization);

          // Copy organization name over to project since it's used for
          // displaying on project cohort cards.
          cardRow.project.organization_name =
            angular.copy(vm.organization.name);
        });
    } else {
      updatePromise = Organization.put(vm.organization);
    }

    return updatePromise
      .then(() => {
        vm.success = 'Organization details have been updated.';
        vm.updating = false;
        vm.error = false;
      })
      .catch(error => {
        vm.updating = false;
        vm.error = error;
      });
  };

  // Create an existence-checker for each kind of id.
  ['ncesDistrictId', 'ncesSchoolId', 'ipedsId', 'opeId'].forEach(p => {
    vm[`${p}Exists`] = id => {
      if (!id) {
        // Don't report a problem on a blank id; most of these external db
        // id fields will be blank.
        return false;
      }
      const idArr = vm[`${p}s`];
      return idArr === undefined ? false : idArr[id];
    };

    // Returns the organization uid of the org that has duplicate poid.
    // Returns false if no duplicate.
    vm[`${p}DuplicateId`] = poid => {
      const poidArr = vm[`${p}s`];
      return poidArr && poidArr[poid];
    };
  });
}

const organization = ngModule => {
  ngModule.component('nepOrganization', {
    bindings: {
      organizationId: '<',
      projectCohortId: '<',
    },
    controller,
    template,
  });
};

export default organization;
