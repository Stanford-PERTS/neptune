import getShortUid from 'utils/getShortUid';

(function () {
  'use strict';

  window.ngModule.component('nepOrganizationUsers', {
    bindings: {
      organizationId: '<',
      projectCohortId: '<',
      closeAdminPanel: '&',
    },
    controller(
      $state,
      $log,
      $q,
      $window,
      Dashboard,
      ModalService,
      Organization,
      User,
    ) {
      const vm = this;

      vm.$onInit = function () {
        vm.loading = true;

        $q.when()
          .then(() => {
            vm.projectCohortId =
              vm.projectCohortId || $state.params.projectCohortId;

            if (vm.projectCohortId) {
              return Dashboard.getProjectDataRow(vm.projectCohortId, true).then(
                projectDataRow => {
                  vm.projectDataRow = projectDataRow;
                  vm.organization = projectDataRow.organization;
                  return projectDataRow;
                },
              );
            }
            return Organization.get({ id: vm.organizationId }).$promise.then(
              organization => {
                vm.organization = organization;
                return organization;
              },
            );
          })
          .then(() =>
            $q.all([
              vm.updateOrganizationOwners(vm.organization),
              vm.updateAssociatedUsers(vm.organization),
            ]),
          )
          .then(() => {
            vm.loading = false;
          });
      };

      // Bind the following functions to `this` so they retain access to proper
      // scope as action button callbacks.
      vm.isSelf = isSelf.bind(vm);
      vm.makeUserLiaison = makeUserLiaison.bind(vm);
      vm.removeUser = removeUser.bind(vm);
      vm.acceptUserRequest = acceptUserRequest.bind(vm);
      vm.declineUserRequest = declineUserRequest.bind(vm);

      function isSelf(user) {
        return User.getCurrent().uid === user.uid;
      }

      /**
       * Query for Organization Owners and place those users on scope.
       * @return {Array} Users (Organization Owners)
       */
      vm.updateOrganizationOwners = function (organization) {
        return queryOwnersByOrganization(organization)
          .then(mapLiaisonIntoUsers)
          .then(users => {
            vm.usersOwners = users;
            return users;
          });
      };

      /**
       * Query for Associated Users and place those users on scope.
       * @return {Array} Users (Associated Users)
       */
      vm.updateAssociatedUsers = function (organization) {
        return queryRequestedByOrganization(organization).then(users => {
          vm.usersRequested = users;
          return users;
        });
      };

      /**
       * Query for Org Owners (Users) using the provided Organization.
       * @param  {Object} organization an Organization
       * @return {Array}               array of Users
       */
      function queryOwnersByOrganization(organization) {
        return User.queryByOrganization({ id: organization.uid }).$promise;
      }

      /**
       * Query for Requested (Users) using the provided Organization.
       * -- requested users are those that have requested access to join
       * @param  {Object} organization an Organization
       * @return {Array}               array of Users
       */
      function queryRequestedByOrganization(organization) {
        return User.queryByAssociation({ id: organization.uid }).$promise;
      }

      /**
       * Adds an isLiaison flag to each user.
       * @param  {Boolean} users true if the user is the organization's liaison
       * @return {Array}         array of Users
       */
      function mapLiaisonIntoUsers(users) {
        users.forEach(user => {
          user.isLiaison = user.uid === vm.organization.liaison_id;
        });

        return users;
      }

      /**
       * Make the specified user the organization liaison.
       * @param  {Object} user User
       */
      function makeUserLiaison(user) {
        ModalService.showModal({
          template: require('../ui_modal_yesno/ui_modal_yesno.view.html'),
          controller: 'UiModalYesNoController',
          bodyClass: 'neptune-modal-open',
          inputs: {
            prompt:
              'Are you sure you want to make this user the organization liaison?',
            options: {},
          },
        }).then(modal => {
          modal.close.then(confirmed => {
            if (confirmed) {
              vm.organization.liaison_id = user.uid;
              Organization.put(vm.organization).then(organization => {
                vm.updateOrganizationOwners(organization);
              });
            }
          });
        });
      }

      /**
       * Remove the specified user from this organization. Does not delete the
       * user.
       * @param  {Object} user User
       */
      function removeUser(user) {
        const isSelf = User.getCurrent().uid === user.uid;
        const prompt = isSelf
          ? 'Are you sure you want to remove yourself from this organization?'
          : 'Are you sure you want to remove this user from the organization?';

        ModalService.showModal({
          template: require('../ui_modal_yesno/ui_modal_yesno.view.html'),
          controller: 'UiModalYesNoController',
          bodyClass: 'neptune-modal-open',
          inputs: {
            prompt,
            options: {
              danger: isSelf,
            },
          },
        }).then(modal => {
          modal.close.then(confirmed => {
            if (confirmed) {
              User.removeFromOrganization({
                id: user.uid,
                orgId: vm.projectDataRow.organization.uid,
              }).$promise.then(() => {
                // Can't update the org owners by re-querying the serve immediately
                // b/c of eventual consistency. Modify the client model directly.
                vm.usersOwners.remove(user);

                // If user has removed themself from the org, send home.
                if (isSelf) {
                  // Forces a reload of user and app data.
                  $window.location.href = '/';
                }
              });
            }
          });
        });
      }

      /**
       * Make API call to accept the User's request to join Organization.
       * @param  {Object} user User
       * @return {Object}      User
       */
      function acceptUserRequest(user) {
        const joinOrganizationPromise = User.joinOrganization(
          { id: user.uid },
          vm.projectDataRow.organization,
        ).$promise;

        joinOrganizationPromise.then(() => {
          vm.updateAssociatedUsers(vm.organization);
        });
        joinOrganizationPromise.then(() => {
          vm.updateOrganizationOwners(vm.organization);
        });

        joinOrganizationPromise.catch(acceptUserError);

        return user;
      }

      /**
       * Make API call to decline the User's request to join Organization.
       * @param  {Object} user User
       * @return {Object}      User
       */
      function declineUserRequest(user) {
        const rejectFromOrganizationPromise = User.rejectFromOrganization({
          id: user.uid,
          orgId: vm.organization.uid,
        }).$promise;

        rejectFromOrganizationPromise.then(() => {
          vm.updateAssociatedUsers(vm.organization);
        });
        rejectFromOrganizationPromise.catch(declineUserError);

        return user;
      }

      /**
       * Handle User.rejectFromOrganization errors.
       */
      function declineUserError(error) {
        $log.error('User.rejectFromOrganization error', error);
      }

      /**
       * Handle User.joinOrganization errors.
       */
      function acceptUserError(error) {
        $log.error('User.joinOrganization error', error);
      }

      vm.openAddUserPanel = function () {
        Dashboard.getInviteUsersTask(vm.projectDataRow).then(task => {
          vm.closeAdminPanel();
          $state.go('dashboard.tasks.checkpoints.tasks', {
            projectCohortId: vm.projectDataRow.projectCohort.short_uid,
            checkpointId: getShortUid(task.checkpoint_id),
            taskId: task.uid,
          });
        });
      };
    },
    template: `
      <ui-card-panel loading="$ctrl.loading" error="$ctrl.error">

        <!-- Organization Users -->
        <div class="OrganizationUsersHeading">
          <h3>Organization Users</h3>

          <a
            class="btn"
            ng-click="$ctrl.openAddUserPanel()"
            ng-if="$ctrl.projectCohortId"
          >
            Invite User
          </a>
        </div>

        <table class="bordered striped">
          <thead>
            <tr>
              <th data-field="name">Name</th>
              <th data-field="email">Email</th>
              <th data-field="phone">Phone</th>
              <th data-field="actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr ng-repeat="user in $ctrl.usersOwners track by $index">
              <td>
                {{ user.name }}
                <span ng-show="user.isLiaison">(Liaison)</span>
              </td>
              <td>{{ user.email }}</td>
              <td>{{ user.phone_number }}</td>
              <td>
                <a class="btn"
                   ng-hide="user.isLiaison || !user.hashed_password"
                   ng-click="$ctrl.makeUserLiaison(user)">Make Liaison</a>
                <a class="btn"
                   ng-hide="user.isLiaison || user.hashed_password"
                   tooltips
                   tooltip-template="This user hasn't accepted their invitation yet."
                   tooltip-class="tooltip-status"
                   tooltip-smart="true"
                   disabled="disabled">Make Liaison</a>
                <a class="btn disabled"
                   tooltips
                   tooltip-template="You cannot remove the liaison. Make another user the liaison first."
                   tooltip-class="tooltip-status"
                   tooltip-smart="true"
                   ng-show="user.isLiaison">
                    Remove User
                </a>
                <a class="btn"
                   ng-hide="user.isLiaison"
                   ng-click="$ctrl.removeUser(user)">
                    Remove User
                    <i
                      ng-show="$ctrl.isSelf(user)"
                      class="fa fa-exclamation-triangle">
                    </i>

                </a>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Associated Users -->
        <div ng-show="$ctrl.usersRequested.length > 0">
          <h3>Users Who Have Requested To Join</h3>

          <table class="bordered striped">
            <thead>
              <tr>
                <th data-field="name">Name</th>
                <th data-field="email">Email</th>
                <th data-field="phone">Phone</th>
                <th data-field="actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr ng-repeat="user in $ctrl.usersRequested track by $index">
                <td>{{ user.name }}</td>
                <td>{{ user.email }}</td>
                <td>{{ user.phone_number }}</td>
                <td><a class="btn" ng-click="$ctrl.acceptUserRequest(user)">Accept</a></td>
                <td><a class="btn" ng-click="$ctrl.declineUserRequest(user)">Decline</a></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Inviting Users -->
        <div ng-if="!$ctrl.projectCohortId">
          <h3>Invite Users</h3>

          <div
            nep-organization-invitation
            organization="$ctrl.organization"
            invitation-complete="$ctrl.updateOrganizationOwners($ctrl.organization)"
          ></div>
        </div>

      </ui-card-panel>
    `,
  });
})();
