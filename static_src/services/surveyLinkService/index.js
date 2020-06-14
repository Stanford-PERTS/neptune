// Service for getting unique survey links to Qualtrics.
//
// Usage:
//
// var surveyLink = new SurveyLink({programLabel: 'foo', session: 1});
// surveyLink.$getUnique(function (surveyLink) {
//   surveyLink.url;  // unique url available here
// });

const surveyLinkService = ngModule => {
  ngModule.service('SurveyLink', function SurveyLink($resource, hostingDomain) {
    const SurveyLinkResource = $resource(
      `//${hostingDomain}/api/survey_links/:programLabel/:surveyOrdinal/get_unique`,
      {
        programLabel: '@program_label',
        surveyOrdinal: '@survey_ordinal',
      },
      {
        // Has exactly the same behavior as resource.$save(), a POST
        // request, but has a better name, because you're actually
        // consuming/popping/deleting a survey link from the server, not
        // creating a new one based on local data, so "save" is the wrong
        // idea.
        getUnique: {
          method: 'POST',
        },
      },
    );

    return SurveyLinkResource;
  });
};

export default surveyLinkService;
