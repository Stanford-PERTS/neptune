/* global describe, beforeEach, module, inject, it, expect */

describe('nepPortal', function() {
  'use strict';

  var $rootScope;
  var $q;
  var $componentController;
  var vm;

  var mockProgram = {
    label: 'demo-program',
    surveys: ['survey1'],  // only length matters
  };

  beforeEach(function () {
    // NOTE! html2js means that appParticipate depends on the module
    // templates-app_participate. However! This doesn't work:
    // angular.mock.module('templates-app_participate');
    // Don't know why. This does:
    angular.module('templates-app_participate', []);

    // Load our module.
    module('appParticipate');

    // Mock services used by this component.
    module(function ($provide) {
      $provide.service('Program', function () {
        this.get = function (params) {
          return { $promise: $q.when(mockProgram) };
        };
      });
    });

    // Inject utility for accessing component controller, misc services.
    inject(function (_$rootScope_, _$q_, _$componentController_, _addQTools_) {
      $rootScope = _$rootScope_;
      $q = _$q_;
      $componentController = _$componentController_;

      _addQTools_($q);
    });

    // All these tests required the controller and some contextual data.
    vm = $componentController('nepPortal', null);
    vm.participationInfo = {program_label: mockProgram.label};
  });

  it('should validate correct numeric session', function(done) {
    // Expected inputs of the validate function.
    vm.validateSession(1).assertFulfilled().finally(done);
    // Must call $digest() for any $q-based promises to resolve :-(
    $rootScope.$digest();
  });

  it('should invalidate too-large numeric session', function(done) {
    vm.validateSession(10).assertRejected().finally(done);
    $rootScope.$digest();
  });

  it('should invalidate less-than-one numeric session', function(done) {
    vm.validateSession(0).assertRejected().finally(done);
    $rootScope.$digest();
  });

  it('should validate special missing value', function (done) {
    vm.validateSession('__missing_session__').assertFulfilled().finally(done);
    $rootScope.$digest();
  });

  it('should interpret various typos in participation codes', function () {
    var tests = {
      'trout viper 1': ['trout viper', 1],        // normal
      'TrOuT vIpEr 1': ['trout viper', 1],        // strange case
      ' trout   viper  1  ': ['trout viper', 1],  // untrimmed, multiple spaces
      'trout\tviper  1  ': ['trout viper', 1],    // strange whitespace
      'trout viper1': ['trout viper', 1],         // no space before digit
      'trout viper1foo': ['trout viper', 1],      // unexpected suffix
      'trout viper99': ['trout viper', 99],       // large session
      'trout viper 02': ['trout viper', 2],       // no octal

      // similar but without session number
      ' trout   viper ': ['trout viper', undefined],
      'TrOuT vIpEr': ['trout viper', undefined],
    };
    for (let input in tests) {
      if (tests.hasOwnProperty(input)) {
        vm.session = undefined;
        let [codeOutput, sessionOutput] = tests[input];
        expect(vm.splitCode(vm.stripCode(input))).toEqual(codeOutput);
        expect(vm.session).toEqual(sessionOutput);
      }
    }
  });

  it('should reject input that is uninterpretable', function (done) {
    vm.splitCode('76 trombones').assertRejected().finally(done);
    $rootScope.$digest();
  });

  it('should accept valid tokens', function (done) {
    const validToken = "I've got \u2665";
    vm.validateToken(validToken).assertFulfilled().finally(done);
    $rootScope.$digest();
  });

  it('should reject empty string', function (done) {
    vm.validateToken('').assertRejected().finally(done);
    $rootScope.$digest();
  });

  it('should reject non-strings', function (done) {
    $q.all([
      vm.validateToken(5).assertRejected(),
      vm.validateToken(null).assertRejected(),
      vm.validateToken(undefined).assertRejected(),
    ]).finally(done);
    $rootScope.$digest();
  });

  it('should reject overly long tokens', function (done) {
    const longToken = (new Array(200)).join('a');
    vm.validateToken(longToken).assertRejected().finally(done);
    $rootScope.$digest();
  });
});
