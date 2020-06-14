import {
  clearLocalStorage,
  handleApiResponse,
  retrieveUserFromLocalStorage,
  saveUserToLocalStorage,
} from 'services/config';

const userService = ngModule => {
  ngModule.service('User', function User(
    $http,
    $resource,
    $state,
    $window,
    hostingDomain,
  ) {
    let user = { uid: null, user_type: 'public' };

    const UserResource = $resource(
      `//${hostingDomain}/api/users/:id`,
      { id: '@uid' },
      {
        queryByAssociation: {
          url: `//${hostingDomain}/api/organizations/:id/associated_users`,
          method: 'GET',
          isArray: true,
        },
        queryByOrganization: {
          url: `//${hostingDomain}/api/organizations/:id/users`,
          method: 'GET',
          isArray: true,
        },
        queryByProgram: {
          url: `//${hostingDomain}/api/programs/:label/users`,
          method: 'GET',
          isArray: true,
        },
        getFromAuthToken: {
          url: `//${hostingDomain}/api/auth_tokens/:token/user`,
          method: 'GET',
        },
        getAccountManager: {
          url: `//${hostingDomain}/api/projects/:projectId/account_manager`,
          method: 'GET',
        },
        getLiaison: {
          url: `//${hostingDomain}/api/:parentUrlKind/:id/liaison`,
          method: 'GET',
        },
        removeFromOrganization: {
          url: `//${hostingDomain}/api/organizations/:orgId/users/:id`,
          method: 'DELETE',
        },
        // Requires an organization as the body.
        requestToJoinOrganization: {
          url: `//${hostingDomain}/api/users/:id/associated_organizations`,
          method: 'POST',
        },
        rejectFromOrganization: {
          url: `//${hostingDomain}/api/users/:id/associated_organizations/:orgId`,
          method: 'DELETE',
        },
        // Requires an organization as the body.
        joinOrganization: {
          url: `//${hostingDomain}/api/users/:id/organizations`,
          method: 'POST',
        },
        // Custom PUT action
        update: {
          method: 'PUT',
        },
      },
    );

    UserResource.setCurrent = function (userObj) {
      if (userObj) {
        user = new UserResource(userObj);
        saveUserToLocalStorage(userObj);
      }
    };

    UserResource.getCurrent = function () {
      return user;
    };

    UserResource.loggedIn = function () {
      return user && user.user_type !== 'public';
    };

    UserResource.isSuperAdmin = function () {
      return user && user.user_type === 'super_admin';
    };

    UserResource.isNonAdmin = function () {
      // Matches either value while we transition. See #985.
      return user && ['org_admin', 'user'].includes(user.user_type);
    };

    UserResource.login = function (email, password) {
      return $http({
        url: `//${hostingDomain}/api/login`,
        method: 'POST',
        data: { email, password, auth_type: 'email' },
      })
        .then(handleApiResponse)
        .then(response => {
          UserResource.setCurrent(response);
          return response;
        })
        .catch(error => {
          throw error;
        });
    };

    UserResource.logout = function () {
      user = null;
      clearLocalStorage();
      $window.location.href = '/';
    };

    UserResource.imitate = function (email) {
      return (
        $http
          .get(`//${hostingDomain}/api/login/${email}`)
          .then(handleApiResponse)
          .then(response => {
            UserResource.setCurrent(response);
            return response;
          })
          // Full window refresh to update user object and update session
          // cookies
          .then(() => ($window.location.href = '/'))
      );
    };

    // Attempt to retrieve logged in user from localStorage
    UserResource.setCurrent(retrieveUserFromLocalStorage());

    return UserResource;
  });
};

export default userService;
