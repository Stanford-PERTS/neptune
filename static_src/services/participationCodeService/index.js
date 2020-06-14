const participationCodeService = ngModule => {

  /**
   * @ngdoc service
   * @name nepApi.service:ParticipationCode
   * @description
   *    The server's response includes properties of the corresponding project
   *    cohort or reporting unit necessary for starting the participant's
   *    survey (in face, for neptune codes, the response _is_ a project
   *    cohort).
   */

  ngModule.service('ParticipationCode', function ParticipationCode(
    $resource,
    hostingDomain,
  ) {
    const ParticipationCodeResource = $resource(
      `//${hostingDomain}/api/codes/:code`,
    );

    // We'd like to express a code in a url in dash case: "trout-viper",
    // which means replacing spaces with dashes. But Angular doesn't provide
    // a way to transform GET parameters. So monkey-patch the get method.
    ParticipationCodeResource._get = ParticipationCodeResource.get;
    ParticipationCodeResource.get = function (params) {
      if (params.code) {
        params.code = params.code.replace(/ /g, '-');
      }
      return ParticipationCodeResource._get(params);
    };

    return ParticipationCodeResource;
  });
};

export default participationCodeService;
