import portalCookiesFactory from './portalCookiesFactory';
import resourceWithProvider from './resourceWithProvider';

import organizationService from './organizationService';
import participantDataService from './participantDataService';
import participantService from './participantService';
import participationCodeService from './participationCodeService';
import projectCohortService from './projectCohortService';
import programService from './programService';
import surveyLinkService from './surveyLinkService';
import surveyService from './surveyService';
import taskService from './taskService';

const registerServices = ngModule => {
  portalCookiesFactory(ngModule);
  resourceWithProvider(ngModule);

  organizationService(ngModule);
  participantDataService(ngModule);
  participantService(ngModule);
  participationCodeService(ngModule);
  projectCohortService(ngModule);
  programService(ngModule);
  surveyLinkService(ngModule);
  surveyService(ngModule);
  taskService(ngModule);
};

export default registerServices;
