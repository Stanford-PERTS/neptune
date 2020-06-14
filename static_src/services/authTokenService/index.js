// Service for getting auth tokens.
//
// Usage:
//
// (new AuthToken()).$save(authToken => console.log(authToken.token));

const authTokenService = ngModule => {
  ngModule.service('AuthToken', function AuthToken($resource, hostingDomain) {
    const AuthTokenResource = $resource(`//${hostingDomain}/api/auth_tokens`);
    return AuthTokenResource;
  });
};

export default authTokenService;
