import {
  clearLocalStorage,
  getAuthorization,
  setJwtToken,
} from 'services/config';

const isNotLoginRoute = () => {
  const loginRouteRegex = /\/login(\?.*)*$/;
  return !loginRouteRegex.test(window.location.href);
};

const registerHttpAuthInterceptorsFactory = ngModule => {
  ngModule.factory('httpAuthorizationInterceptors', $q => {
    return {
      request(config) {
        config.headers.Authorization = getAuthorization();
        return config;
      },
      response(response) {
        setJwtToken(response);
        return response;
      },
      responseError(rejection) {
        // Check if our jwt token is no longer valid
        if (isNotLoginRoute() && rejection.status === 401) {
          clearLocalStorage();
          window.location.href = '/login';
          // Stall the thread with a never-resolving promise so loading
          // animations display while the page goes to /login.
          return $q.defer().promise;
        }
        return $q.reject(rejection);
      },
    };
  });
};

const registerHttpAuthInterceptors = ngModule => {
  registerHttpAuthInterceptorsFactory(ngModule);
  ngModule.config($httpProvider => {
    $httpProvider.interceptors.push('httpAuthorizationInterceptors');
  });
};

export default registerHttpAuthInterceptors;
