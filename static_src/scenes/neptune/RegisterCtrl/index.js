// Angular controller for authorization (login and signup) modals

const RegisterCtrl = ngModule => {
  ngModule.controller(
    'RegisterCtrl',
    ($scope, $http, $state, hostingDomain, showAllWarnings, Program, User) => {
      'use strict';

      // Allows display of a welcome/orientation banner, "You're registering for
      // Program X". If the program 404s, refresh w/o the program param.
      if ($state.params.program) {
        $scope.program = Program.get({ label: $state.params.program });
        $scope.program.$promise.catch(error =>
          $state.go('.', { program: null }),
        );
      }

      $scope.email = $state.params.email;

      const user = User.getCurrent();
      if (User.loggedIn()) {
        if ($scope.program) {
          $state.go('programRegistration', {
            programLabel: $state.params.program,
          });
        } else {
          $state.go('dashboard');
        }
      }

      $scope.mode = 'registerForm';

      $scope.submit = function () {
        if ($scope.registerForm.$invalid) {
          showAllWarnings($scope.registerForm);
          return;
        }

        if ($scope.role === 'student') {
          $scope.studentMessage = true;
          return;
        }

        $scope.errorCode = '';
        $scope.busy = true;
        $http
          .post(
            `//${hostingDomain}/api/register`,
            // Registration emails can be customized to the program.
            {
              email: $scope.email,
              role: $scope.role,
              program_label: $state.params.program,
            },
          )
          .then(
            function successCallback(response) {
              $scope.busy = false;
              $scope.mode = 'checkEmail';
            },
            function errorCallback(error) {
              $scope.busy = false;
              $scope.errorCode = error.data;
            },
          );
      };

      $scope.reload = $state.reload;
    },
  );
};

export default RegisterCtrl;
