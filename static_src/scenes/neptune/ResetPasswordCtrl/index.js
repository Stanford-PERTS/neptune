// Angular controller for authorization (login and signup) modals

const ResetPasswordCtrl = ngModule => {
  ngModule.controller('ResetPasswordCtrl', (
    $scope,
    $http,
    hostingDomain,
    showAllWarnings,
  ) => {
    'use strict';

    $scope.mode = 'emailForm';

    $scope.submit = function () {
      if ($scope.resetPasswordForm.$invalid) {
        showAllWarnings($scope.resetPasswordForm);
        return;
      }

      $scope.errorCode = '';
      $scope.busy = true;
      $http
        .post(`//${hostingDomain}/api/reset_password`, {
          email: $scope.email,
        })
        .then(
          function successCallback() {
            $scope.mode = 'checkEmail';
          },
          function errorCallback(error) {
            $scope.busy = false;
            $scope.errorCode = error.data;
          },
        );
    };
  });
};

export default ResetPasswordCtrl;
