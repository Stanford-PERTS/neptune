// Angular controller for authorization (login and signup) modals

angular.module('neptuneApp').controller(
  'LoginCtrl',
  function ($scope, $http, $window, $state, showAllWarnings, passwordRegex,
            yellowstoneDomain, Program, User) {

    'use strict';

    // Allows display of a welcome/orientation banner, "You're registering for
    // Program X". If the program 404s, refresh w/o the program param.
    if ($state.params.program) {
      $scope.program = Program.get({label: $state.params.program});
      $scope.program.$promise.catch(error => $state.go('.', {program: null}));
    }

    $scope.yellowstoneDomain = yellowstoneDomain;

    $scope.user = {
      email: $state.params.email,
    };

    $scope.passwordRegex = passwordRegex;

    // If a logged in user follows the /login?program=xxnn link provided, this
    // will direct them to the appropriate program registration state.
    if (User.loggedIn() && $state.params.program) {
      $state.go('programRegistration',
        { programLabel: $state.params.program },
        { location: 'replace' }
      );
      return;
    }

    // If a logged in user attempts to go to /login, they will be redirected to
    // the dashboard.
    if (User.loggedIn()) {
      $state.go('dashboard', {}, { location: 'replace' });
      return;
    }

    $scope.submitEmailLogin = function () {
      // Clear password errors so any previous login attempt form $invalid flag
      // is reset. Else, the first incorrect password will cause the user
      // to no longer be able to log in.
      $scope.emailLoginForm.password.$setValidity('password', true);

      // Trigger an invalid password if the password is blank
      if (!$scope.user.password) {
        $scope.emailLoginForm.password.$setValidity('password', false);
      }

      if ($scope.emailLoginForm.$invalid) {
        showAllWarnings($scope.emailLoginForm);
        return;
      }

      $scope.errorCode = '';
      $scope.busy = true;
      $scope.user.auth_type = 'email';
      $http.post('/api/login', $scope.user)
        .then(function successCallback(response) {
          User.setCurrent(response.data);
          // Either a program flag or a continue_url means we need special
          // redirection, but default to the dashboard.
          var continueUrl = $scope.program ?
            '/program_registration/' + $scope.program.label :
            $state.params.continue_url || '/dashboard';
          // Hard refresh to make sure all the jinja templates render with
          // awareness of the user.
          $window.location.href = continueUrl;
        }, function errorCallback(error) {
          $scope.busy = false;
          $scope.errorCode = error.data;
          $scope.emailLoginForm.password.$setValidity('password', false);
        });
    };

  }
);
