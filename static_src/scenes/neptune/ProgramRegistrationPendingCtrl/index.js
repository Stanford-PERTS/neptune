// Angular controller for end state of program registration when the
// user has applied to join an existing org.
import getUrlKind from 'utils/getUrlKind';

const ProgramRegistrationPendingCtrl = ngModule => {
  ngModule.controller(
    'ProgramRegistrationPendingCtrl',

    ($scope, $stateParams, Organization, Program, User) => {
      'use strict';

      const orgId = $stateParams.orgId;
      $scope.program = Program.get({ label: $stateParams.programLabel });
      $scope.pendingOrg = Organization.get({ id: orgId }, () => {
        $scope.liaison = User.getLiaison({
          parentUrlKind: getUrlKind(orgId),
          id: orgId,
        });
      });
    },
  );
};

export default ProgramRegistrationPendingCtrl;
