// Provide a form for users to send invitations to colleagues.

import getShortUid from 'utils/getShortUid';
import template from './index.html';

const nepOrganizationInvitation = ngModule => {
  ngModule.directive(
    'nepOrganizationInvitation',
    (Invitation, User, Liaison) => {
      const directiveScope = {
        organization: '=',
      };

      return {
        restrict: 'A',
        scope: directiveScope,
        template,
        link,
      };

      function link(scope, element, attrs) {
        scope.invite = function (email) {
          const invitation = new Invitation({
            email,
            organization_id: scope.organization.uid,
            continue_url: `/organizations/${getShortUid(
              scope.organization.uid,
            )}`,
          });
          // POST to server
          invitation.$save(recipient => {
            scope.sent = true;
            scope.email = '';
            Liaison.addToOrg(scope.organization.uid, recipient);
          });
        };
      }
    },
  );
};

export default nepOrganizationInvitation;
