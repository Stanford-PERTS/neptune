// Provide a form for users to send invitations to colleagues.

angular.module('neptuneApp').directive(
  'nepOrganizationInvitation',
  function (getShortUid, Invitation, User, Liaison) {

    'use strict';

    var directiveScope = {
      organization: '=',
      invitationComplete: '&'
    };

    return {
      restrict: 'A',
      scope: directiveScope,
      templateUrl: 'shared/organization_invitation.html',
      link: link
    };

    function link(scope, element, attrs) {
      scope.invite = function (email) {
        var invitation = new Invitation({
          email: email,
          organization_id: scope.organization.uid,
          continue_url: '/organizations/' + getShortUid(scope.organization.uid),
        });
        // POST to server
        invitation.$save(function (recipient) {
          scope.sent = true;
          scope.email = '';
          Liaison.addToOrg(scope.organization.uid, recipient);
          scope.invitationComplete({recipient: recipient});
        });
      };
    }
  }
);
