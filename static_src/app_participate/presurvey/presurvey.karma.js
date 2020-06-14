/* global describe, beforeEach, module, inject, it, expect, spyOn */

describe('nepPresurvey', function () {
  'use strict';

  // Services we'll inject for tests to use directly.
  let $rootScope;
  let $q;
  let $componentController;
  let vm;

  // Tests will change this to simulate various responses from the server.
  let serverLink;

  // Constants and mocks
  const mockProgram = {
    label: 'demo-program',
    surveys: [{ anonymous_link: 'https://sshs.qualtrics.com/anonymous' }],
  };

  const mockLoaded = {
    participant: { uid: 'Participant_001' },
    program: mockProgram,
    projectCohort: {
      uid: 'ProjectCohort_001',
      project_id: 'Project_001',
      cohort_label: '2018',
    },
    session: 1,
    survey: { uid: 'Survey_001' },
    pdArr: [],
  };

  function SurveyLink() {}
  SurveyLink.prototype.$getUnique = function (params) {
    if (serverLink === null) {
      return $q.reject({ status: 404 });  // A test explicitly set no data.
    } else if (serverLink === undefined) {
      throw new Error("Must set serverLink.");
    } else {
      return $q.when(serverLink);  // A test populated the server with data.
    }
  };

  // Mocks a $resource, must save provided properties when instantiated.
  function ParticipantData(params) {
    angular.extend(this, params);
  }
  ParticipantData.prototype.$save = function () {
    return $q.when(this);
  };

  beforeEach(function () {
    angular.module('templates-app_participate', []);  // b/c html2js

    module('appParticipate');

    // Injectables used in the component.
    module(function ($provide) {
      $provide.value('serverTime', new Date());

      serverLink = undefined;
      $provide.service('SurveyLink', function () {
        return SurveyLink;
      });

      $provide.service('ParticipantData', function () {
        return ParticipantData;
      });
    });

    // Injectables used directly in tests.
    inject(function (_$rootScope_, _$q_, _$componentController_, _addQTools_) {
      $rootScope = _$rootScope_;
      $q = _$q_;
      $componentController = _$componentController_;

      _addQTools_($q);
    });

    vm = $componentController('nepPresurvey', null);
  });

  it('should use existing pd link', function (done) {
    const existingLinkPd = { key: 'link', value: 'foo', survey_ordinal: 1 };
    const loaded = angular.copy(mockLoaded);
    loaded.pdArr = [existingLinkPd];  // code should find this and use it

    vm.getSurveyLink(loaded)
      .then(function (loaded) {
        expect(loaded.linkPd).toBe(existingLinkPd);
      })
      .assertFulfilled()
      .finally(done);

    $rootScope.$digest();
  });

  it('should save a survey link pd if server 200s', function (done) {
    const loaded = angular.copy(mockLoaded);

    // Tell the "server" to return data. Code should use it.
    const mockLink = { url: 'https://sshs.qualtrics.com/unique' };
    serverLink = mockLink;

    spyOn(ParticipantData.prototype, '$save').and.callThrough();

    vm.getSurveyLink(loaded)
      .then(function (loaded) {
        expect(loaded.linkPd.value).toEqual(mockLink.url);
        expect(loaded.pdArr).toContain(loaded.linkPd);
        expect(ParticipantData.prototype.$save).toHaveBeenCalled();
      })
      .assertFulfilled()
      .finally(done);

    $rootScope.$digest();
  });

  it('should use anonymous link on 404 w/o saving', function (done) {
    const loaded = angular.copy(mockLoaded);

    // Tell the "server" it has no data. Code should get anon link from program.
    serverLink = null;

    spyOn(ParticipantData.prototype, '$save').and.callThrough();

    vm.getSurveyLink(loaded)
      .then(function (loaded) {
        expect(loaded.linkPd.value).toEqual(mockProgram.surveys[0].anonymous_link);
        expect(loaded.pdArr).toContain(loaded.linkPd);
        expect(ParticipantData.prototype.$save).not.toHaveBeenCalled();
      })
      .assertFulfilled()
      .finally(done);

    $rootScope.$digest();
  });

});
