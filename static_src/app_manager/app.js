// Application-wide functions
// Neptune Platform

/* global console, FastClick */

(function () {
  'use strict';

  var neptuneApp = angular.module(
    'neptuneApp',
    ['ngAnimate', 'ngResource', 'ui.router', 'ngFileUpload', 'zxcvbn',
      'nepApi', 'nepUtil', '720kb.tooltips', 'ig.linkHeaderParser',
      'angucomplete-alt', 'templates-app_manager', 'angularModalService',
      'moment-picker']
  );

  // Copy window.perts variables into Angular perts constant
  var perts = {};
  if (window.perts) { perts = angular.copy(window.perts); }
  neptuneApp.constant('perts', perts);

  neptuneApp.value('passwordRegex', /\S{10,}/);

  // Angular 'run' occurs after all assets loading,
  // can replace jQuery function((){...}());
  // Put all universal javascript inside this function
  neptuneApp.run([
    '$window', '$rootScope', '$state', '$transitions', 'currentUser', 'User', 'Notification', 'Title',
    function ($window, $rootScope, $state, $transitions, currentUser, User, Notification, Title) {

    // Prevent delay on iPhone taps
    FastClick.attach(document.body);

    // Links user from server into Angular; currentUser is set as a value on
    // the module in base.html. It shouldn't be used anywhere else. Instead,
    // get the current user through the User service: User.getCurrent().
    User.setCurrent(currentUser);
    var user = User.getCurrent();

    // Public users (those who aren't signed in) are restricted from most
    // states, with some exceptions. If restricted, redirect them to /login,
    // with a parameter so they can return to where they were.
    $transitions.onStart({},  // empty match objects matches all states
                         function (transition) {
      var toState = transition.to();
      var toParams = transition.params();
      if (user.user_type === 'public') {
        var publicAllowed = false;
        if (typeof toState.isPublic === 'boolean') {
          publicAllowed = toState.isPublic;
        } else if (typeof toState.isPublic === 'function') {
          publicAllowed = toState.isPublic(user, toParams);
        }

        if (!publicAllowed) {
          // Successfully passing the parameter `continue` here requires that
          // it be defined in the `param` section of the state in
          // app_states.js.
          var path = $window.location.pathname + $window.location.hash;
          $state.go("login", {continue_url: path});
          event.preventDefault();
        }
      }
    });

    // App Title
    Title.init();

    // App State: Notifications and Mobile Nav Side Panels
    $rootScope.hideSidePanels = function() {
      $rootScope.isMobileNavActive = false;
      $rootScope.isNotificationsActive = false;
    };

    $rootScope.hideSidePanels(); // initially hide side panels

    $rootScope.showMobileNav = function() {
      $rootScope.hideSidePanels();
      $rootScope.isMobileNavActive = true;
    };

    $rootScope.showNotifications = function() {
      $rootScope.hideSidePanels();
      $rootScope.isNotificationsActive = true;
    };

    // Notifications management

    // All users want to see their notifications all the time, so keep them
    // in the root scope.
    $rootScope.notifications = currentUser.uid ? Notification.queryByUser(
      {id: currentUser.uid, dismissed: false}) : [];
    $rootScope.dismissedNotifications = [];

    $rootScope.showDismissedNotifications = function () {
      $rootScope.dismissedNotifications = Notification.queryByUser(
        {id: currentUser.uid, dismissed: true});
    };
    $rootScope.hideDismissedNotifications = function () {
      $rootScope.dismissedNotifications = [];
    };

    $rootScope.toggleNotifications = function () {
      $rootScope.showNotifications = !$rootScope.showNotifications;
    };

  }]);

}());
