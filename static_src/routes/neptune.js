import loginTemplate from 'scenes/neptune/LoginCtrl/index.html';
// import offlineNotificationTemplate from 'scenes/neptune/OfflineNotificationCtrl/index.html';
import registerTemplate from 'scenes/neptune/RegisterCtrl/index.html';
import resetPasswordTemplate from 'scenes/neptune/ResetPasswordCtrl/index.html';
import setPasswordTemplate from 'scenes/neptune/SetPasswordCtrl/index.html';

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

    // Routes
    $stateProvider

      // Routes: Index
      .state('index', {
        url: '/',
        isPublic: true,
        views: {
          // Note: use of '@' means absolute position of ui-view
          // As opposed to children view
          '@': {
            component: 'nepIndex',
          },
        },
      })

      // Routes: Login
      .state('login', {
        url: '/login?program&email&continue_url',
        // This `params` definition is required to use the toParams argument
        // of $state.go().
        // https://github.com/angular-ui/ui-router/wiki/Quick-Reference#stategoto--toparams--options
        params: { program: null, email: null, continue_url: null },
        isPublic: true,
        views: {
          '@': {
            controller: 'LoginCtrl',
            template: loginTemplate,
          },
        },
        data: {
          title: 'Login',
        },
      })

      // Routes: Registration
      .state('register', {
        url: '/register?program&email',
        params: { program: null, email: null },
        isPublic: true,
        views: {
          '@': {
            template: registerTemplate,
            controller: 'RegisterCtrl',
          },
        },
        data: {
          title: 'Register',
        },
      })

      .state('reset_password', {
        url: '/reset_password',
        isPublic: true,
        views: {
          '@': {
            template: resetPasswordTemplate,
            controller: 'ResetPasswordCtrl',
          },
        },
        data: {
          title: 'Reset Password',
        },
      })

      .state('set_password', {
        url: '/set_password/:authToken?program&cohort&continue_url&case',
        params: { program: null, cohort: null, continue_url: null, case: null },
        isPublic: true,
        views: {
          '@': {
            template: setPasswordTemplate,
            controller: 'SetPasswordCtrl',
          },
        },
        data: {
          title: 'Set Password',
        },
      })

      // Routes: Program Registration

      // Allow user to see a list of programs available for registration.
      .state('programRegistration', {
        url: '/program_registration/:programLabel',
        // squash allows this state to match a URL w/o a trailing slash if
        // the optional param is omitted
        params: { programLabel: { value: null, squash: true } },
        views: {
          '@': {
            component: 'nepProgramRegistration',
          },
        },
        data: {
          title: 'Add Program',
        },
      })

      // Where you join programs and add organizations.
      .state('programRegistration.chooseOrg', {
        url: '/:cohortLabel',
        views: {
          '@': {
            template: require('../scenes/neptune/ProgramRegistrationCtrl/project_cohort.html'),
            controller: 'ProgramRegistrationCtrl',
          },
          'content@programRegistration.chooseOrg': {
            template: require('../scenes/neptune/ProgramRegistrationCtrl/project_cohort_tasklists.html'),
          },
          'checkpointTasks@programRegistration.chooseOrg': {
            template: require('../scenes/neptune/ProgramRegistrationCtrl/index.html'),
          },
        },
        data: {
          title: 'Program Registration',
        },
      })
      .state('programRegistration.chooseOrg.invalidCohort', {
        views: {
          '@': {
            template: require('../app_manager/controllers/program_registration_invalid_cohort.html'),
          },
        },
      })
      // Where we break the bad news that you have to wait to be approved to
      // join an org.
      .state('programRegistration.chooseOrg.pending', {
        url: '/pending/:orgId',
        params: { orgId: null },
        views: {
          '@': {
            template: require('../scenes/neptune/ProgramRegistrationPendingCtrl/index.html'),
            controller: 'ProgramRegistrationPendingCtrl',
          },
        },
        data: {
          title: 'Program Registration',
        },
      })

      // Route: Notifications
      .state('notifications', {
        url: '/notifications?n&cursor&order',
        views: {
          '@': 'nepNotifications',
        },
      })

      // Routes: Dashboard
      .state('dashboard', {
        url: '/dashboard',
        views: {
          '@': 'nepDash',
          'DashboardPrompt@dashboard': 'uiProgramSelectPromptCard',
        },
        data: {
          title: 'Dashboard',
        },
      })

      .state('dashboard.query', {
        url: '/q?program_label&cohort_label&view&organization_id',
        views: {
          DashboardMain: 'nepDashboardMain',
          DashboardPrompt: 'nepBlank',
        },
      })

      .state('dashboard.tasks', {
        url: '/:projectCohortId/tasks',
        views: {
          DashboardMain: 'nepDashboardMain',
          DashboardPrompt: 'nepBlank',
          ProjectCohortPanel: 'nepProjectCohort',
        },
      })

      .state('dashboard.tasks.checkpoints', {
        url: '/:checkpointId',
        views: {
          ProjectCohortPanel: 'nepProjectCohort',
          tasklist: 'nepTaskList',
        },
        data: {
          title: 'Tasks',
        },
      })

      .state('dashboard.tasks.checkpoints.tasks', {
        url: '/:taskId',
        views: {
          ProjectCohortPanel: 'nepProjectCohort',
          tasklist: 'nepTaskList',
        },
        data: {
          title: 'Tasks',
        },
      })

      .state('dashboard.participation', {
        url: '/:projectCohortId/participation',
        views: {
          DashboardMain: 'nepDashboardMain',
          DashboardPrompt: 'nepBlank',
          ProjectCohortPanel: 'nepProjectCohortParticipation',
        },
      })

      .state('dashboard.reports', {
        url: '/:projectCohortId/reports',
        views: {
          DashboardMain: 'nepDashboardMain',
          DashboardPrompt: 'nepBlank',
          ProjectCohortPanel: 'nepProjectCohortReports',
        },
      })

      .state('dashboard.organizationPanel', {
        url: '/:projectCohortId/organization',
        views: {
          DashboardMain: 'nepDashboardMain',
          DashboardPrompt: 'nepBlank',
          ProjectCohortPanel: 'nepOrganization',
        },
      })

      .state('dashboard.organizationUsers', {
        url: '/:projectCohortId/organization/users',
        views: {
          DashboardMain: 'nepDashboardMain',
          DashboardPrompt: 'nepBlank',
          ProjectCohortPanel: 'nepOrganizationUsers',
        },
      })

      .state('dashboard.notes', {
        url: '/:projectCohortId/notes',
        views: {
          DashboardMain: 'nepDashboardMain',
          DashboardPrompt: 'nepBlank',
          ProjectCohortPanel: 'nepProjectCohortNotes',
        },
      })

      .state('organizations', {
        url: '/organizations',
        views: {
          '@': 'nepOrganizations',
        },
      })

      .state('organizations.details', {
        url: '/:organizationId',
        views: {
          '@': 'nepOrganizationGet',
          'panel@organizations.details': 'nepOrganization',
        },
      })

      .state('organizations.details.users', {
        url: '/users',
        views: {
          panel: 'nepOrganizationUsers',
        },
      })

      .state('user', {
        url: '/user',
        views: {
          '@': {
            component: 'nepUser',
          },
        },
        data: {
          title: 'User Profile',
        },
      })

      .state('user.profile', {
        url: '/:userId',
        views: {
          '@': {
            component: 'nepUser',
          },
        },
        data: {
          title: 'User Profile',
        },
      })

      .state('reports', {
        url: '/reports',
        views: {
          '@': {
            component: 'nepReports',
          },
        },
      })

      .state('reports.returning', {
        url: '/returning',
        views: {
          report: 'nepReportsReturning',
        },
      });
  }

  ngModule.config(routeConfiguration);
};

export default registerRoutes;
