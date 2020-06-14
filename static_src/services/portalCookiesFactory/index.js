import forEachObj from 'utils/forEachObj';

const portalCookiesFactory = ngModule => {
  ngModule.factory(
    'portalCookies',
    ModuleCookies => new ModuleCookies('appParticipate'),
  );

  /**
   * @ngdoc factory
   * @name nepCookies.factory:ModuleCookies
   * @description
   *    ModuleCookies is a constructor. Use it to make your own factory with
   *    your module name as the namespace. See example use above.
   */

  ngModule.factory('ModuleCookies', $cookies => {
    function ModuleCookies(moduleName) {
      this.moduleName = moduleName;
    }

    ModuleCookies.prototype.fullCookieName = function (partialName) {
      return `${this.moduleName}.${partialName}`;
    };

    ModuleCookies.prototype.partialCookieName = function (fullName) {
      return fullName.slice(this.moduleName.length + 1); // +1 for the dot
    };

    ModuleCookies.prototype.get = function (key) {
      return $cookies.get(this.fullCookieName(key));
    };

    ModuleCookies.prototype.put = function (key, value) {
      return $cookies.put(this.fullCookieName(key), value, { path: '/' });
    };

    ModuleCookies.prototype.remove = function (key) {
      return $cookies.remove(this.fullCookieName(key), { path: '/' });
    };

    ModuleCookies.prototype.getAll = function () {
      // Ignores cookies outside the namespace.

      const r = new RegExp(`^${this.moduleName}`);
      const cookieHash = {};
      forEachObj(
        $cookies.getAll(),
        function (key, value) {
          if (r.test(key)) {
            cookieHash[this.partialCookieName(key)] = value;
          }
        },
        this,
      );

      return cookieHash;
    };

    ModuleCookies.prototype.removeAll = function () {
      forEachObj(
        this.getAll(),
        function (key, value) {
          this.remove(key);
        },
        this,
      );
    };

    return ModuleCookies;
  });
};

export default portalCookiesFactory;
