/**
 * @ngdoc factory
 * @name nepApi.factory:queryOne
 * @description
 *    Generic method for resource classes to expect and return only one
 *    result from an api endpoint that typically returns a list of results.
 *    This is convenient when you know your query parameters define a unique
 *    entity but the api doesn't index them this way.
 *
 *    Simply inject then assign as a method of a resource class. Behaves
 *    exactly like normal $resource methods:
 *    * Immediately returns an object which is later filled in with data.
 *    * Returned object has a $promise property which resolves with the
 *      retrieved object, or is rejected if the result set doesn't have a
 *      length of one.
 *    * You can also specify a callback which is called with the retrieved
 *      object.
 *
 *    Example:
 *
 *    // Define a Widget resource class.
 *    var Widget = $resource(...);
 *    Widget.queryOne = queryOne;
 *
 *    // Query the api but expect only one result.
 *    myWidget = Widget.queryOne({foo: bar});
 *
 *    // Use the promise.
 *    myWidget.$promise.then(...);
 *
 *    // Or use a callback.
 *    Widget.queryOne({foo: bar}, function (myWidget) {
 *      ...
 *    });
 */

const queryOne = ngModule => {
  ngModule.factory(
    'queryOne',
    // Do not use arrow function because we need `this`.
    // eslint-disable-next-line
    function($q) {
      return function (queryParams, callback) {
        // `this` will be the resource class the function is assigned to.
        const results = this.query(queryParams);

        // The object that is returned immediately, and later extended with data.
        const one = {};

        // Define the object's promise based on the query result promise. It
        // either resolves with the object or is rejected with the underlying
        // query results.
        one.$promise = results.$promise.then(results => {
          if (results.length === 1) {
            // As expected, we have a result list with one object in it.

            // Now that the data has arrived...
            // 1. Fill the object (reference already returned) with data.
            angular.extend(one, results[0]);
            // 2. Execute the callback, if provided.
            if (typeof callback === 'function') {
              callback(one);
            }

            // Resolve the promise with the object.
            return one;
          }
          // Either zero results or more than one. Treat as an error; reject.
          return $q.reject(results);
        });

        // Immediately return an object with the promise property but no data.
        return one;
      };
    },
  );
};

export default queryOne;
