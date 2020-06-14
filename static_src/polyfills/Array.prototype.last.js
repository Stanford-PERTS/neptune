// Array helper function, not an actual polyfill since it's not in ECMA.
// Returns last element of the array.

import last from 'lodash/last';

if (!Array.prototype.last) {
  Array.prototype.last = function () {
      'use strict';
      return last(this);
  };
}
