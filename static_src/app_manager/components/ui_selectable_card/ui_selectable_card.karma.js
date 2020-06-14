/* global describe, beforeEach, module, inject, it, expect, console */

describe('uiSelectableCard Component', () => {
  'use strict';

  // mock the neptuneApp module
  beforeEach(angular.mock.module('neptuneApp'));

  // The currentUser, Title service, and Notification API calls probably should
  // be reorganized in a way that we don't need to mock them in every test file.

  // TODO: how can we drop the need to provide currentUser on all tests?
  beforeEach(module('neptuneApp', $provide => {
    $provide.value('currentUser', { uid: 'User_1234567890' });
  }));

  // TODO: how can we drop the need to mock notification on all tests?
  var httpBackend;

  beforeEach(inject($httpBackend => {
    httpBackend = $httpBackend;
    httpBackend.whenGET(
      /\/api\/users\/(.+)\/notifications\?dismissed=false/, undefined, ['id'])
      .respond([]);
  }));

  // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  var element;
  var scope;

  beforeEach(inject(($rootScope, $compile) => {
    scope = $rootScope.$new();
    element = angular.element('<ui-selectable-card>Lorem ipsum</ui-selectable-card>');
    element = $compile(element)(scope);
    scope.$apply();
  }));

  it('should render the provided content', () => {
    const div = element.find('div');
    expect(div.html()).toContain('Lorem ipsum');
  });

});
