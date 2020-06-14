const resourceWithProvider = ngModule => {
  ngModule.provider('$resourceWith', function ResourceWithProvider() {
    this.$get = [
      '$resource',
      function decorateResourceWith($resource) {
        function resourceFactory(url, paramDefaults = {}, actions = {}) {
          // Add `update` to all our $resource based services.
          actions.update = actions.update || {
            method: 'PUT',
          };

          const resource = $resource(url, paramDefaults, actions);

          // Adds a `put` method to $resource. This allows us to perform an
          // update like this:
          //
          //   return Organization.put(organization);
          //
          // instead of this:
          //
          //   return Organization
          //    .update({ id: organization.uid }, organization)
          //    .$promise;

          resource.put = function(entity) {
            return resource.update({ id: entity.uid }, entity).$promise;
          };

          return resource;
        }

        return resourceFactory;
      },
    ];
  });
};

export default resourceWithProvider;
