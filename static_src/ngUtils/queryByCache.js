// Factory for caching API responses.

// The problem: two unrelated scopes on the same page want a list of some
// api resource. When one list is updated client side (e.g. after POSTing a
// new object), the other list should update.

// Desired feature #1: allow the $resource service to do normal HTTP caching,
// or not. We don't want to roll our own caching of data.

// Desired feature #2: it shouldn't be hard to call. If you query the api, you
// should get the results, period.

// Solution: cache the array that holds the results, but not the results
// themselves. All returned result sets are linked by simple reference.
// Namespace by a key so many API services can use the same trick.

const queryByCache = ngModule => {
  ngModule.factory('queryByCache', () => () => {
    const cache = {};

    return function(unresolvedResults, key) {
      if (!cache.hasOwnProperty(key)) {
        cache[key] = [];
      }

      // This is the array we want to keep a reference to in all contexts to
      // allow dynamic updating across controllers and scopes.
      const preservedReference = cache[key];

      // Other code might expect to be able to chain off the ajax call, so
      // keep the promise around too.
      // Note that the resolve value here is wrong; it's not the preserved
      // reference.
      preservedReference.$promise = unresolvedResults.$promise;

      // Wait until the ajax call completes and we have access to the results.
      unresolvedResults.$promise.then(results => {
        // Empty it out, but don't lose the reference ("truncation").
        preservedReference.length = 0;

        // Transfer the contents of the result set. Use push() to keep the
        // reference, but apply it so we can put all the contents in at once.
        // Push takes many arguments! who knew? arr.push(1, 2, ...)
        Array.prototype.push.apply(preservedReference, results);
      });

      return preservedReference;
    };
  });
};

export default queryByCache;
