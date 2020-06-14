import getKind from 'utils/getKind';
import getLinkRel from 'utils/getLinkRel';

const nepNotifications = ngModule => {
  ngModule.filter(
    'startFrom',
    () =>
      function (input, start) {
        start = Number(start);
        return input && input.slice(start);
      },
  );

  function controller(
    $http,
    $location,
    $state,
    hostingDomain,
    Organization,
    ProjectCohort,
    User,
  ) {
    const vm = this;
    vm.$location = $location;
    vm.organizationsByContextId = {};

    vm.$onInit = function () {
      vm.loading = true;
      vm.user = User.getCurrent();

      vm.queryForNotifications().then(() => {
        vm.loading = false;
      });
    };

    vm.queryForNotifications = function () {
      const n = $location.search().n ? Number($location.search().n) : 10;
      const cursor = $location.search().cursor ? $location.search().cursor : '';
      const order = $location.search().order
        ? $location.search().order
        : '-created';

      const url = `//${hostingDomain}/api/users/${
        vm.user.uid
      }/notifications?n=${n}&cursor=${cursor}&order=${order}`;
      // console.log('url', url);

      return $http.get(url).then(response => {
        vm.notifications = response.data;
        vm.notifications.forEach(vm.queryForOrganization);

        // vm.notifications.forEach(n => console.log('  ', n.created, '  ', n.uid));

        vm.link = response.headers().link;

        // console.log('link first', getLinkRel(vm.link, 'first'));
        // console.log('link previous', getLinkRel(vm.link, 'previous'));
        // console.log('link next', getLinkRel(vm.link, 'next'));
        // console.log('link last', getLinkRel(vm.link, 'last'));
      });
    };

    vm.go = function (rel) {
      const { n, cursor, order } = getLinkRel(vm.link, rel);
      $state.go('notifications', { n, cursor, order });
    };

    vm.queryForOrganization = function (notification) {
      const { context_id } = notification;

      if (getKind(context_id) === 'ProjectCohort') {
        ProjectCohort.get({ id: context_id })
          .$promise.then(
            pc => Organization.get({ id: pc.organization_id }).$promise,
          )
          .then(org => {
            vm.organizationsByContextId[context_id] = org;
          });
      }

      if (getKind(context_id) === 'Organization') {
        Organization.get({ id: context_id }).$promise.then(org => {
          vm.organizationsByContextId[context_id] = org;
        });
      }
    };

    vm.markDismissed = function (notification) {
      notification.dismissed = true;
      Notification.put(notification);
    };

    vm.markAllDismissed = function () {
      vm.notifications.forEach(notification => {
        if (!notification.dismissed) {
          vm.markDismissed(notification);
        }
      });
    };

    vm.toggleDismissed = function (notification) {
      notification.dismissed = !notification.dismissed;
      Notification.put(notification);
    };
  }

  const template = `
    <div class="Notifications">
      <div class="ContentWrapper">
        <div class="ContentMain">
          <ui-card>
            <h1>Notifications</h1>
          </ui-card>

          <ui-card ng-show="$ctrl.loading" class="loading">
            <div><i class="fa fa-lg fa-spinner fa-spin"></i></div>
          </ui-card>

          <ui-card ng-show="!$ctrl.loading && $ctrl.notifications.length === 0">
            You have no notifications.
          </ui-card>

          <div ng-repeat="notification in $ctrl.notifications">
            <ui-card
              disabled="notification.dismissed"
            >
              <div>
                <strong>Organization:</strong>
                {{ $ctrl.organizationsByContextId[notification.context_id].name }}
              </div>
              <div>
                <strong>Date:</strong>
                {{ notification.created | date:'short' }}
              </div>
              <div>
                <strong>Subject:</strong>
                {{ notification.subject }}
              </div>
              <hr />
              {{ notification.body }}
            </ui-card>

            <ui-card-panel>
              <div class="flex">
                <a href="{{ ::notification.link }}" class="margin-right">
                  <ui-action-button>View</ui-action-button>
                </a>

                <a
                  href="{{ ::notification.link }}"
                  ng-click="$ctrl.markDismissed(notification)"
                  ng-class="{ disabled: notification.dismissed }"
                  class="margin-right"
                >
                  <ui-action-button disabled="notification.dismissed">
                    View &amp; Mark Read
                  </ui-action-button>
                </a>

                <div class="push-right">
                  <ui-action-button
                    ng-click="$ctrl.toggleDismissed(notification)"
                    ng-hide="notification.dismissed"
                  >
                    Mark Read
                  </ui-action-button>

                  <ui-action-button
                    ng-click="$ctrl.toggleDismissed(notification)"
                    ng-show="notification.dismissed"
                  >
                    Mark Unread
                  </ui-action-button>
                </div>
              </div>
            </ui-card-panel>
          </div>
        </div>

        <div class="ContentOptions">
          <ui-card class="" ng-show="!$ctrl.loading && $ctrl.notifications.length !== 0">
            <div class="FilterOptions">
              <div class="FilterOptionsName">
                Batch Controls
              </div>

              <ui-action-button ng-click="$ctrl.markAllDismissed()">
                Mark All Read
              </ui-action-button>
            </div>
          </ui-card>

          <ui-card class="Paging">
            <a ng-click="$ctrl.go('first')">
              <ui-action-button>
                <i class="fa fa-fast-backward"></i>
              </ui-action-button>
            </a>
            <!--
            <a ng-click="$ctrl.go('previous')">
              <ui-action-button>
                <i class="fa fa-backward"></i>
              </ui-action-button>
            </a>
            -->
            <a ng-click="$ctrl.go('next')">
              <ui-action-button>
                <i class="fa fa-forward"></i>
              </ui-action-button>
            </a>

            <!--
              On server, rest.py will return us a reverse-ordered query, which
              is just going to be confusing, so let's disable this nav option.
            <!--
            <a ng-click="$ctrl.go('last')">
              <ui-action-button>
                <i class="fa fa-fast-forward"></i>
              </ui-action-button>
            </a>
            -->
          </ui-card>
        </div>
      </div>
    </div>
  `;

  ngModule.component('nepNotifications', {
    controller,
    template,
  });
};

export default nepNotifications;
