// Uses the purpose-generic google maps place search code and applies it to
// creating organization entities in Neptune.

// Provides a org change event with arguments `org`, `isOrgValid` and
// `invalidMessage`.

// Example where parentFunction is defined within the calling scope:
// <div nep-organization-search
//      on-org-change="parentFunction(org, isOrgValid, invalidMessage)">
// </div>

angular.module('neptuneApp').directive('nepOrganizationSearch', [
  'User', 'Organization',
  function (User, Organization) {

    'use strict';

    var directiveScope = {
      orgChange: '&onOrgChange'
    };

    return {
      restrict: 'A',
      scope: directiveScope,
      templateUrl: 'shared/organization_search.html',
      link: link
    };

    function link(scope, element, attrs) {

      var user = User.getCurrent();

      scope.mapLoading = true;

      // Index orgs by google maps place id so we can check if results from the
      // map exist in our system. Will be filled in during selectPlaceAsOrg().
      scope.orgsByPlace = {};

      // Provided as a callback to the map directive. Called when the user
      // selects an autocompleted place on the map. Identifies it as either
      // 1) a new org 2) an existing org the user already is associated to or
      // 3) an existing org the user may apply to join.
      scope.selectPlaceAsOrg = function (place) {
        // Called when the user selects a place on the map.
        scope.errorMessage = '';
        scope.orgIsNew = undefined;
        scope.alreadyAssociatedToOrg = undefined;

        // Query our server to see if this organization exists.
        // Note that this returns "thin" org entities, which only have a uid
        // and their place id.
        Organization.getAllPlaceIds(function (orgs) {

          scope.orgsByPlace = util.indexBy(orgs, 'google_maps_place_id');

          // Convert from a google maps place to one of our orgs.
          var orgParams = Organization.paramsFromPlace(place);

          // Assume the current user, who is creating this organization, will be
          // the contact for the org.
          orgParams.liaison_id = user.uid;
          scope.selectedOrganization = new Organization(orgParams);

          if (place.place_id in scope.orgsByPlace) {
            // The de novo constructed org has no uid. Fill it in from the one
            // we already know about.
            scope.selectedOrganization.uid = scope.orgsByPlace[place.place_id].uid;
            scope.orgChange({
              org: scope.selectedOrganization,
              orgIsValid: false,
              invalidMessage: "This organization has already been " +
                              "registered with PERTS."
            });
          } else {
            scope.orgChange({
              org: scope.selectedOrganization,
              orgIsValid: true,
              invalidMessage: ""
            });
          }
        });
      };

    }

  }
]);
