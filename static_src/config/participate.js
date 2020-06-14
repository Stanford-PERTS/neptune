const PERTS = window.PERTS || {};

// These should match with the variables declared in `static_src/neptune.html`
//
// We can't make references to `window` without a fallback or else Jest tests
// will fail.
//
export const SERVER_TIME = PERTS.SERVER_TIME || new Date().toISOString();
export const HOSTING_PROTOCOL = PERTS.HOSTING_PROTOCOL || 'http';
export const HOSTING_DOMAIN = PERTS.HOSTING_DOMAIN || 'localhost:8888';
export const TRITON_DOMAIN = PERTS.TRITON_DOMAIN || 'localhost:10080';
export const YELLOWSTONE_PROTOCOL = PERTS.YELLOWSTONE_PROTOCOL || 'http';
export const YELLOWSTONE_DOMAIN = PERTS.YELLOWSTONE_DOMAIN || 'localhost:9080';

const config = ngModule => {
  ngModule.value('serverTime', SERVER_TIME);
  ngModule.value('hostingDomain', HOSTING_DOMAIN);
  ngModule.value('tritonDomain', TRITON_DOMAIN);
  ngModule.value('yellowstoneDomain', YELLOWSTONE_DOMAIN);

  ngModule.config(
    ($httpProvider, $interpolateProvider, $provide, $sceDelegateProvider) => {
      // Enable Sentry logging
      if (window.Raven) {
        $provide.decorator(
          '$exceptionHandler',
          $delegate =>
            function(exception, cause) {
              // log error to Sentry
              window.Raven.captureException(exception);
              // pass through error to Angular
              $delegate(exception, cause);
            },
        );
      }

      // Change the default bracket notation, which is normally {{ foo }},
      // so that it doesn't interfere with jinja (server-side templates).
      // That means angular interpolation is done like this: {[ foo ]}.
      $interpolateProvider.startSymbol('{[');
      $interpolateProvider.endSymbol(']}');

      // allow unnecessary square-bracket notation
      const defs = $httpProvider.defaults;
      defs.useXDomain = true;
      delete defs.headers.common['X-Requested-With'];
      defs.headers.common.Accept = 'application/json';
      defs.headers.common['Content-Type'] = 'application/json';

      // Allows YouTube video embedding, needed by the nepHelpVideo directive.
      // https://docs.angularjs.org/api/ng/provider/$sceDelegateProvider
      $sceDelegateProvider.resourceUrlWhitelist([
        'self',
        '*://www.youtube-nocookie.com/**',
      ]);
    },
  );
};

export default config;
