/* global module */

// Preprocessor for SCSS files. Jest doesn't know how to handle the importing of
// SCSS files, and we won't test the SCSS code, so we just filter out all of the
// content of the files.

module.exports = {
  process() {
    return '';
  },
};
