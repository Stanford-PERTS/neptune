// Helper to deal with users and liaisons.

const liaisonService = ngModule => {
  ngModule.service('Liaison', function Liaison($q, $sce, User) {
    const optionsCache = {}; // indexed by org id

    // Add user to organization's optionsCache
    function addToOrg(orgId, user) {
      optionsCache[orgId] = optionsCache[orgId] || [];
      optionsCache[orgId].push(userToOption(user));
    }

    // Get the requested organization's users in a format usable for display
    // in an HTML form.
    function options(orgId) {
      // Clear out any existing cache for the specified organization.
      const opts = (optionsCache[orgId] = []);

      // Query for Organization users and place them into the optionsCache
      User.queryByOrganization({ id: orgId }).$promise.then(
        function placeUsersIntoCache(users) {
          users.forEach((user) => {
            addToOrg(orgId, user);
          });
          return users;
        },
      );

      // Return the optionsCache
      return opts;
    }

    // Convert a User object into a options object that can be used to
    // display user selections in an HTML form.
    function userToOption(user) {
      return {
        value: user.uid,
        label: user.email,
        // Users with no hashed password haven't set up their account yet,
        // so they're not a valid choice.
        disabled: !user.hashed_password,
      };
    }

    return {
      addToOrg,
      options,
    };
  });
};

export default liaisonService;
