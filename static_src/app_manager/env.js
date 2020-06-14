/**
 * env.js can be used to set variables that will changed depending on the
 * environment. The properties on window.perts will be copied into the
 * Angular constant `perts` so that it can then be injected as a dependency
 * where needed.
 */

/* global util */

(function(window, util) {

  'use strict';

  window.perts = window.perts || {};
  window.perts.env = window.perts.env || {};

  // Production Domain
  window.perts.env.productionDomain = 'www.neptune.org';

  // Use util's setProductionDomain
  util.setProductionDomain(window.perts.env.productionDomain);

  // Enabled debug mode
  // Setting to false will disable all Angular $log.debug
  window.perts.env.debugEnabled = util.isDevelopment();

}(this, util));
