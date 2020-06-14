import forEachObj from 'utils/forEachObj';

const registerRoutes = ngModule => {
  function routeConfiguration(
    $locationProvider,
    $stateProvider,
    $urlRouterProvider,
    $urlMatcherFactoryProvider,
  ) {
    // html5mode
    $locationProvider.html5Mode(true);

    // Make trailing slash optional for all routes
    // https://ui-router.github.io/docs/0.3.1/#/api/ui.router.util.$urlMatcherFactory#methods_strictmode
    $urlMatcherFactoryProvider.strictMode(false);

    // Invalid routes are sent to index
    $urlRouterProvider.otherwise('/');

    // Build a custom parameter type for particpation codes, so the code
    // 'trout viper' goes into the URL as '/participate/trout-viper' and
    // vice versa.
    $urlMatcherFactoryProvider.type('participationCode', {
      encode(modelValue) {
        return typeof modelValue === 'string'
          ? modelValue.replace(/ /g, '-')
          : modelValue;
      },
      decode(urlValue) {
        return typeof urlValue === 'string'
          ? urlValue.replace(/[-+]/g, ' ')
          : urlValue;
      },
      // Excluding slashes is critical, otherwise this parameter will swallow
      // up later portions of the URL.
      pattern: /[^/]+/,
    });

    // Routes
    $stateProvider

      .state('participate', {
        url: '/?date_override&ready_override',
        // Before redirecting to the portal child state, duplicate the
        // functionality of nepPortal.storeQueryString(), since ui-router would
        // otherwise dump the query string.
        redirectTo($transition) {
          const $location = $transition.injector().get('$location');
          const portalCookies = $transition.injector().get('portalCookies');
          forEachObj($location.search(), (key, value) => {
            portalCookies.put(key, value);
          });

          // Where we actually want to go.
          return { state: 'portal', params: $transition.params() };
        },
      })
      .state('portal', {
        url: '/portal?date_override&ready_override',
        isPublic: true,
        views: {
          '@': {
            component: 'nepPortal',
          },
        },
      })
      .state('portal.code', {
        url: '/{code:participationCode}', // custom type, space to dash case
        isPublic: true,
      })
      .state('portal.code.session', {
        url: '/:session',
        params: { tokenError: null },
        isPublic: true,
      })
      .state('portal.code.session.token', {
        url: '/:token',
        isPublic: true,
      })
      .state('presurvey', {
        url: '/presurvey?date_override&ready_override',
        isPublic: false, // participant id should be recorded... somehwere...
        views: {
          '@': {
            component: 'nepPresurvey',
          },
        },
      })
      .state('presurvey.consent', {
        url: '/presurvey/consent',
        isPublic: false,
        views: {
          presurveyPage: {
            component: 'nepPresurveyConsent',
          },
        },
      })
      .state('presurvey.previewAgreement', {
        url: '/preview_agreement',
        isPublic: false,
        views: {
          presurveyPage: {
            component: 'nepPresurveyPreviewAgreement',
          },
        },
      })
      .state('presurvey.skipCheck', {
        // No URL because this is an abstract/logic-only state that forwards
        // people to other places. We don't want users to use the back button to
        // arrive here. But it has a conceptual place in the URL scheme.
        // url: '/skip_check',
        isPublic: false,
        views: {
          presurveyPage: {
            component: 'nepPresurveySkipCheck',
          },
        },
      })
      .state('presurvey.iesCheck', {
        // No view; see comment for skipCheck.
        // url: '/ies_check',
        isPublic: false,
        views: {
          presurveyPage: {
            component: 'nepPresurveyIesCheck',
          },
        },
      })
      .state('presurvey.epBlockSwitcher', {
        // No view; see comment for skipCheck.
        // url: '/ep_validation',
        isPublic: false,
        views: {
          presurveyPage: {
            component: 'nepEpBlockSwitcher',
          },
        },
      })
      .state('presurvey.epAssent', {
        url: '/ep_assent',
        isPublic: false,
        views: {
          presurveyPage: {
            component: 'nepEpAssent',
          },
        },
      });
  }

  ngModule.config(routeConfiguration);
};

export default registerRoutes;
