/* global describe, beforeEach, module, inject, it, expect */

describe('nepUtil module', function() {
  'use strict';

  beforeEach(function () {
    // Load our module.
    module('nepUtil');
  });

  it('should parse a UTC date str', function() {
    inject(function (_parseUTCDateStr_) {
      var exact = new Date(Date.UTC(2017, 0, 1));
      var parsed = _parseUTCDateStr_('2017-01-01');
      // Date objects are never equal, but they should equate in terms of
      // seconds since the epoch.
      expect(Number(exact)).toEqual(Number(parsed));
    });
  });

  it('should parse a local date str', function() {
    inject(function (_parseLocalDateStr_) {
      var exact = new Date(2017, 0, 1);
      var parsed = _parseLocalDateStr_('2017-01-01');
      // Date objects are never equal, but they should equate in terms of
      // seconds since the epoch.
      expect(Number(exact)).toEqual(Number(parsed));
    });
  });
});
