angular.module('neptuneApp').directive('notification', [
  '$rootScope', '$location', '$q', 'Notification',
  function ($rootScope, $location, $q, Notification) {

    'use strict';

    var directiveScope = {
      'notification': '='
    };

    var link = function (scope, element, attrs) {

      scope.view = function () {
        scope.busy = true;  // @todo: currently unused

        $rootScope.showNotifications = false;  // closes side bar

        // If this is an autodismiss notification, first dismiss and save, then
        // go.
        var p;  // $q.when(undefined) resolves immediately
        if (scope.notification.autodismiss && !scope.notification.dismissed) {
          p = scope.dismiss();
        }
        $q.when(p).then(function () {
          $location.path(scope.notification.link);  // can't use $state w/ URL
        });
      };

      scope.dismiss = function () {
        scope.notification.dismissed = true;
        $rootScope.notifications.remove(scope.notification);
        $rootScope.dismissedNotifications.push(scope.notification);
        return scope.notification.$update();
      };
    };

    return {
      restrict: 'A',
      scope: directiveScope,
      templateUrl: 'shared/notification.html',
      link: link
    };
  }
]);
