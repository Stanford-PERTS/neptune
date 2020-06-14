// Resources with no dependencies.
import './polyfills/neptune';
import './assets/js/moment-2.10.6-moment-with-locales.js';

// MaterializeCSS javascript requires global jQuery.
import $ from 'jquery';
window.$ = $;
import 'materialize-css';

import angular from 'angular';

// Resources that depend on angular.
import './assets/js/angular-moment-picker-0.10.2.min.js';
import 'angucomplete-alt';
import 'angular-modal-service';
import 'ng-file-upload';
import ngResource from 'angular-resource';
import 'angular-tooltips';
import uiRouter from '@uirouter/angularjs';

// Neptune code.
import config from './config/neptune';
import registerApp from './app/neptune';
import registerNgUtils from './ngUtils/neptune';
import registerComponents from './components/neptune';
import registerServices from './services/neptune';
import registerRoutes from './routes/neptune';
import registerScenes from './scenes/neptune';

import './styles/neptune.scss';
import './assets/css/angular-moment-picker.min.scss';

const ngModule = angular.module('app', [
  '720kb.tooltips',
  'angucomplete-alt',
  'angularModalService',
  'moment-picker',
  'ngFileUpload',
  ngResource,
  uiRouter,
]);

// Place ngModule on window so that legacy, es5 style, components can access.
window.ngModule = ngModule;

// require, instead of import, because imports happen first, and we need these
// legacy files to 'import' after we have created our main Angular module.
require('./neptuneLegacy');

config(ngModule);
registerApp(ngModule);
registerNgUtils(ngModule);
registerComponents(ngModule);
registerServices(ngModule);
registerRoutes(ngModule);
registerScenes(ngModule);

ngModule.run(($state, $transitions, $window, User) => {
  // Public users (those who aren't signed in) are restricted from most
  // states, with some exceptions. If restricted, redirect them to /login,
  // with a parameter so they can return to where they were.
  $transitions.onStart(
    {}, // empty match objects matches all states
    transition => {
      const toState = transition.to();
      const toParams = transition.params();
      if (!User.loggedIn()) {
        let publicAllowed = false;
        if (typeof toState.isPublic === 'boolean') {
          publicAllowed = toState.isPublic;
        } else if (typeof toState.isPublic === 'function') {
          publicAllowed = toState.isPublic(User.getCurrent(), toParams);
        }

        if (!publicAllowed) {
          // Successfully passing the parameter `continue` here requires that
          // it be defined in the `param` section of the state in
          // app_states.js.
          const path = $window.location.pathname + $window.location.hash;
          $state.go('login', { continue_url: path });
          event.preventDefault();
        }
      }
    },
  );
});

export default ngModule;
