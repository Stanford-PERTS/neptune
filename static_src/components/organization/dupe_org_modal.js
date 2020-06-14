export default function DupeOrgModalController(
  $scope,
  $q,
  Organization,
  User,
  organization,
  close,
  update,
) {
  const today = (new Date()).toISOString().substr(0, 10);
  const emailStr = organization.users.map(u => u.email).join(', ');
  $scope.orgNotes = `Rejected on ${today} as a duplicate organization. ` +
    `Removed users:\n\n${emailStr}`;

  $scope.close = function () {
    close();

    // We also need to clean up $scope
    $scope.$destroy();
  };

  $scope.reject = function () {
    $scope.updating = true;

    // Org rejected, notes set, named changed,
    // Any users on Fake U are removed.

    organization.notes = $scope.orgNotes;
    organization.status = Organization.REJECTED_STATUS;
    organization.name += ' (DUPLICATE)';

    // Note that organization is a shared reference with the
    // nepOrganization.organization so changes here should reflect there,
    // so all we have to do is call the passed-in update() function.
    update()
      .then(() =>
        $q.all(organization.users.map(user =>
          User.removeFromOrganization({
            id: user.uid,
            orgId: organization.uid,
          }).$promise
        ))
      )
      .then(() => {
        $scope.updating = false;
        $scope.close();
      });
  };
}
