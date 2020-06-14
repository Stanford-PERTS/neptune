// Note: this isn't exactly a polyfill since it's an addition to the language.

// Removes the first instance of x within a, matching done by Array.indexOf().
// If x is not found, does nothing.

Array.prototype.remove  = function (x) {
    'use strict';
    var i = this.indexOf(x);
    if (i !== -1) { this.splice(i, 1); }
    return this;
};
