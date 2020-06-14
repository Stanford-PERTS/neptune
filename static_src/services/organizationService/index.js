// Angular service for handing Organization object in Angular module

const organizationService = ngModule => {
  ngModule.service('Organization', function Organization(
    $q,
    $resourceWith,
    hostingDomain,
    queryOne,
  ) {
    const OrgResource = $resourceWith(
      `//${hostingDomain}/api/organizations/:id`,
      { id: '@uid' },
      {
        queryByUser: {
          url: `//${hostingDomain}/api/users/:id/organizations`,
          method: 'GET',
          isArray: true,
        },

        // Everyone should be able to see the names and place ids of orgs in
        // the system, even if they don't own, and therefore can't GET, the
        // org. This is important for program admins viewing their projects.
        getName: {
          url: `//${hostingDomain}/api/organizations/:id/name`,
          method: 'GET',
          isArray: false,
        },
        getAllNames: {
          url: `//${hostingDomain}/api/organizations/names`,
          method: 'GET',
          isArray: true,
        },
        getPlaceId: {
          url: `//${hostingDomain}/api/organizations/:id/google_maps_place_id`,
          method: 'GET',
          isArray: false,
        },
        getAllPlaceIds: {
          url: `//${hostingDomain}/api/organizations/google_maps_place_ids`,
          method: 'GET',
          isArray: true,
        },
        getAllPoids: {
          url: `//${hostingDomain}/api/organizations/poids`,
          method: 'GET',
          isArray: true,
        },
      },
    );

    OrgResource.queryOne = queryOne;

    OrgResource.paramsFromPlace = function (place) {
      const params = {
        name: place.name,
        mailing_address: place.formatted_address,
        phone_number: place.formatted_phone_number,
        website_url: place.website,
        google_maps_place_id: place.place_id,
      };
      // Address components have a pretty complicated structure.
      // https://developers.google.com/maps/documentation/geocoding/intro#Types
      place.address_components.forEach(component => {
        if (component.types.includes('administrative_area_level_1')) {
          params.state = component.short_name; // e.g. 'WA'
        }
        if (component.types.includes('country')) {
          params.country = component.long_name;
        }
        if (component.types.includes('postal_code')) {
          params.postal_code = component.long_name;
        }
      });
      return params;
    };

    OrgResource.getLongUid = function (shortOrLongUid) {
      if (shortOrLongUid.includes('_')) {
        return shortOrLongUid; // already long;
      }
      return `Organization_${shortOrLongUid}`;
    };

    /**
     * We need a way to determine where a given task, based on
     * its label, lies within the config, so that we can use that info to
     * search inside tasklists which are provided by the function
     * Checkpoint.queryOrganizationCheckpointsByProgram which is hitting an
     * API endpoint that only provide task IDs.
     *
     * This function will provide the ordinal (index into checkpoints) and
     * index (index into tasks) where the task with requested label reside.
     */
    OrgResource.getTaskOrdinalAndIndexByLabel = function () {
      // mocked since I'm not sure how to query for org config
      return $q.when({
        ordinal: 1,
        index: 2,
      });
    };

    OrgResource.UNAPPROVED_STATUS = 'unapproved';
    OrgResource.APPROVED_STATUS = 'approved';
    OrgResource.REJECTED_STATUS = 'rejected';

    return OrgResource;
  });
};

export default organizationService;
