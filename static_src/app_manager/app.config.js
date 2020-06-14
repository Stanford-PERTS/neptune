(function() {
  'use strict';

  angular
    .module('neptuneApp')
    .config([
      'perts', '$interpolateProvider', '$locationProvider', '$httpProvider',
      '$stateProvider', '$sceDelegateProvider', '$logProvider', '$provide',
      function (perts, $interpolateProvider, $locationProvider, $httpProvider,
        $stateProvider, $sceDelegateProvider, $logProvider, $provide) {

        // Enable Sentry logging
        if (window.Raven) {
          $provide.decorator('$exceptionHandler', function ($delegate) {
            return function (exception, cause) {
              // log error to Sentry
              window.Raven.captureException(exception);
              // pass through error to Angular
              $delegate(exception, cause);
            };
          });
        }

        // Enable $log.debug output
        $logProvider.debugEnabled(false);
        $logProvider.debugEnabled(perts.env && perts.env.debugEnabled);

        // Change the default bracket notation, which is normally {{ foo }},
        // so that it doesn't interfere with jinja (server-side templates).
        // That means angular interpolation is done like this: {[ foo ]}.
        $interpolateProvider.startSymbol('{[');
        $interpolateProvider.endSymbol(']}');

        // Angular url location w/o preceeding '#'
        $locationProvider.html5Mode(true);
        $locationProvider.hashPrefix('!');

        /* jshint sub: true */  // allow unnecessary square-bracket notation
        var defs = $httpProvider.defaults;
        defs.useXDomain = true;
        delete defs.headers.common['X-Requested-With'];
        defs.headers.common['Accept'] = 'application/json';
        defs.headers.common['Content-Type'] = 'application/json';

        /* global GaeMiniProfiler */
        // Intercept angular $http calls and report them to GaeMiniProfiler so
        // they can be added to the tool in the corner. GaeMiniProfiler attempts
        // to intercept these in jQuery via $(document).ajaxComplete, but that
        // doesn't work for angular.
        $httpProvider.interceptors.push(function () {
          return {
            response: function(resp) {
              const requestId = resp.headers('X-MiniProfiler-Id') || '';
              // GaeMiniProfiler might not exist, depending on environment.
              if (requestId && GaeMiniProfiler) {
                const queryString = resp.headers('X-MiniProfiler-QS') || '';
                GaeMiniProfiler.fetch(requestId, queryString);
              }
              return resp;
            }
          };
        });

        // Allows YouTube video embedding, needed by the nepHelpVideo directive.
        // https://docs.angularjs.org/api/ng/provider/$sceDelegateProvider
        $sceDelegateProvider.resourceUrlWhitelist([
          'self',
          '*://www.youtube-nocookie.com/**'
        ]);
      }]);
}());
