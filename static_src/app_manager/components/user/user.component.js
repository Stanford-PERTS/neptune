(function () {
  'use strict';

  window.ngModule.component('nepUser', {
    controller($state, User) {
      const vm = this;

      // form validation
      vm.form = {};

      vm.$onInit = () => {
        // retrieve userId from params
        let userId = $state.params.userId;

        // retrieve authenticated user
        const authenticatedUser = User.getCurrent();

        // redirect to user's user profile if no userId found
        if (!userId) {
          userId = authenticatedUser.short_uid;
          $state.go('user.profile', { userId });
        }

        // retrieve user
        User.get({ id: userId })
          .$promise.then(user => {
            vm.user = user;

            vm.isSuperAdmin = User.isSuperAdmin();

            // parse notification_option JSON string
            try {
              vm.user.notification_option_vm = angular.fromJson(
                vm.user.notification_option,
              );
            } catch (e) {
              vm.user.notification_option_vm = {};
            }

            // defaults
            // the default `notification_option` from server is null
            vm.user.notification_option_vm =
              vm.user.notification_option_vm || {};

            // users by default receive notifications, the server default is
            // null for this settings field, so if we get nothing, treat it as
            // a yes
            vm.user.notification_option_vm.email =
              vm.user.notification_option_vm.email || 'yes';
          })
          .catch(() => {
            // an error most likely indicates no permission for requested user
            $state.go('dashboard');
          });

        // Update user
        vm.update = function () {
          vm.updating = true;
          vm.error = false;

          vm.user.notification_option = vm.user.notification_option_vm;

          vm.user
            .$update()
            .then(user => {
              vm.updating = false;
              vm.success = 'User profile saved';

              vm.user.notification_option_vm = angular.fromJson(
                user.notification_option,
              );
            })
            .catch(() => {
              vm.updating = false;
              vm.error = 'Error saving user profile changes';
            });
        };
      };

      // Provides a way for child input components to link their local 'form'
      // scope to the User component's scope so that we can disable the update
      // button when any of the form elements are marked invalid.
      vm.linkForm = function (form) {
        vm.form = form;
      };

      vm.imitate = function (email) {
        vm.imitating = true;
        User.imitate(email).catch(error => {
          vm.imitating = false;
          vm.imitateError = 'Email not found';
        });
      };
    },
    template: `
    <div class="User">
      <div class="ContentWrapper">
        <div class="ContentMain">

          <ui-card>
            <ui-card-title>User Settings</ui-card-title>

            <ui-input-text
              label="Name"
              model="$ctrl.user.name"
              link-form="$ctrl.linkForm(form)"
              required="true"
            ></ui-input-text>

            <ui-input-text
              label="Email"
              model="$ctrl.user.email"
              disabled="true"
            ></ui-input-text>

            <ui-input-text
              label="Phone"
              model="$ctrl.user.phone"
              disabled="true"
            ></ui-input-text>

            <ui-input-select
              label="Receive Notification Emails?"
              model="$ctrl.user.notification_option_vm.email"
            >
              <option value="no">No</option>
              <option value="yes">Yes</option>
            </ui-input-select>

            <ui-button
              full-width="true"
              ng-click="$ctrl.update()"
              loading="$ctrl.updating"
              disabled="$ctrl.form.$invalid"
            >
              Update Profile
            </ui-button>

            <ui-input-error type="form" ng-show="$ctrl.error">
              {{ $ctrl.error }}
            </ui-input-error>
            <ui-input-success type="form" message="$ctrl.success">
            </ui-input-success>
          </ui-card>

          <ui-card ng-if="$ctrl.isSuperAdmin">
            <ui-card-title>Imitate User</ui-card-title>

            <ui-input-text
              label="Email"
              model="$ctrl.imitateEmail"
              type="email"
            ></ui-input-text>
            <ui-button
              full-width="true"
              ng-click="$ctrl.imitate($ctrl.imitateEmail)"
              loading="$ctrl.imitating"
              disabled="!$ctrl.imitateEmail"
            >
              Imitate User
            </ui-button>

            <ui-input-error type="form" ng-show="$ctrl.imitateError">
              {{ $ctrl.imitateError }}
            </ui-input-error>
          </ui-card>

        </div>
      </div>
    </div>
    `,
  });
})();
