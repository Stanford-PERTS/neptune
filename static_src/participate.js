import './polyfills/participate';

import angular from 'angular';
import ngCookies from 'angular-cookies';
import ngResource from 'angular-resource';
import uiRouter from '@uirouter/angularjs';

import config from './config/participate';
import registerApp from './app/participate';
import registerNgUtils from './ngUtils/participate';
import registerComponents from './components/participate';
import registerServices from './services/participate';
import registerRoutes from './routes/participate';
import registerScenes from './scenes/participate';

import './styles/participate.scss';

const ngModule = angular.module('app', [ngCookies, ngResource, uiRouter]);

// Place ngModule on window so that legacy, es5 style, components can access.
window.ngModule = ngModule;

// require, instead of import, because imports happen first, and we need these
// legacy files to 'import' after we have created our main Angular module.
require('./participateLegacy');

config(ngModule);
registerApp(ngModule);
registerNgUtils(ngModule);
registerComponents(ngModule);
registerServices(ngModule);
registerRoutes(ngModule);
registerScenes(ngModule);

export default ngModule;
