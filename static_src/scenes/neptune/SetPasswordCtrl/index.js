// Angular controller for authorization (login and signup) modals

const SetPasswordCtrl = ngModule => {
  ngModule.controller(
    'SetPasswordCtrl',
    (
      $scope,
      $state,
      $http,
      $stateParams,
      $window,
      hostingDomain,
      showAllWarnings,
      passwordRegex,
      Program,
      User,
      yellowstoneDomain,
    ) => {
      'use strict';

      $scope.yellowstoneDomain = yellowstoneDomain;

      $scope.existingUserMessage = 'Reset your password';
      $scope.newUserMessage = 'Confirm new account';

      // Allows display of a welcome/orientation banner, "You're registering for
      // Program X". If the program 404s, refresh w/o the program param.
      if ($stateParams.program) {
        $scope.program = Program.get({ label: $stateParams.program });
        $scope.program.$promise.catch(error =>
          $state.go('.', { program: null }),
        );
        $scope.cohort = $stateParams.cohort || undefined;
      }

      $scope.passwordRegex = passwordRegex;
      $scope.userIsNew = null;

      $scope.user = User.getFromAuthToken(
        { token: $stateParams.authToken },
        function successCallback(response) {
          $scope.mode = 'set_password';
          $scope.userIsNew = !$scope.user.hashed_password;
          $scope.message = $scope.userIsNew
            ? $scope.newUserMessage
            : $scope.existingUserMessage;
          console.log($scope.message);
          $scope.name = $scope.user.name;
          $scope.phoneNumber = $scope.user.phone_number;
        },
        function errorCallback(response) {
          // 'not found', 'used', or 'expired'
          $scope.mode = 'invalid_token';
          $scope.errorMode = getErrorMode(response.data);
        },
      );

      $scope.weakWords = ['PERTS', 'Perts', 'perts'];

      $scope.submit = function () {
        $scope.errorCode = '';
        $scope.busy = true;
        $http
          .post(`//${hostingDomain}/api/set_password`, {
            password: $scope.password,
            auth_token: $stateParams.authToken,
            name: $scope.name,
            phone_number: $scope.phoneNumber,
          })
          .then(
            function successCallback(response) {
              $scope.busy = false;

              if ($scope.userIsNew) {
                // This is a registration process. The user has just been in their
                // email, clicked a link, and set a password. The next step is to
                // log them in and bring them to the right place.

                // Either a program flag or a continue_url means we need special
                // redirection, but default to the dashboard.
                const continueUrl = $scope.program
                  ? getProgramRegistrationPath($scope.program.label, $scope.cohort)
                  : $stateParams.continue_url || '/dashboard';

                // Log in the user, using the normal /login endpoint and then do a
                // full refresh to make sure all the jinja-based templates see the
                // new session.
                loginAndRedirect(continueUrl);
              } else {
                // This is a "forgot my password" reset. Don't leave the page; rather
                // assure the user their password has been changed, and allow them
                // to log in with it. Automatically logging in at this point would be
                // disorienting.
                $scope.mode = 'submission_successful';
              }
            },
            function errorCallback(error) {
              $scope.busy = false;
              $scope.mode = 'invalid_token';
              $scope.errorMode = getErrorMode(error.data);
            },
          );
      };

      const getUseCase = function () {
        if ($scope.program) {
          return 'registration';
        }
        // 'invitation' or 'reset'
        return $stateParams.case || '';
      };

      function getErrorMode(tokenError) {
        return `${getUseCase()}:${tokenError}`;
      }

      function loginAndRedirect(url) {
        User.login($scope.user.email, $scope.password)
          .then(() => {
            $window.location.href = url;
          })
          .catch(error => {
            $scope.busy = false;
            $scope.errorCode = error.data;
          });
      }
    },
  );
};

function getProgramRegistrationPath(programLabel, cohortLabel) {
  let path = `/program_registration/${programLabel}`;
  if (cohortLabel) {
    path += `/${cohortLabel}`;
  }
  return path;
}

export default SetPasswordCtrl;
