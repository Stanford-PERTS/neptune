const addQTools = ngModule => {
  ngModule.factory('addQTools', $q => {
    if (window.__karma__ === undefined) {
      console.error('Only use addQTools in testing!');
    }
    $q.prototype.assertFulfilled = function() {
      // Add a catch with an always-failing expect() so the assert fails
      // if the promise is ever rejected.
      return this.catch(error =>
        expect(`rejected reason: ${error}`).toBe('should not reject'),
      );
    };

    $q.prototype.assertRejected = function() {
      // Add a then with an always-failing expect() so the assert fails
      // if the proimse is NOT rejected.
      return this.then(value =>
        expect(`resolved value: ${value}`).toBe('should not resolve'),
      );
    };
  });
};

export default addQTools;
