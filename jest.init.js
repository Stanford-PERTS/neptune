import angular from 'angular';
import 'angular-mocks';

// import main app module
import ngModule from './static_src/neptune';

beforeEach(() => {
  // setup angular mock for all tests
  angular.mock.module(ngModule.name);
});
