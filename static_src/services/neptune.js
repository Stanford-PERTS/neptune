import registerHttpAuthInterceptors from './httpAuthorization';
import resourceWithProvider from './resourceWithProvider';

import authTokenService from './authTokenService';
import checkpointService from './checkpointService';
import emailService from './emailService';
import graphQLService from './graphQLService';
import invitationService from './invitationService';
import liaisonService from './liaisonService';
import organizationService from './organizationService';
import participantDataService from './participantDataService';
import participantService from './participantService';
import participationCodeService from './participationCodeService';
import participationService from './participationService';
import programService from './programService';
import projectCohortService from './projectCohortService';
import projectService from './projectService';
import notificationService from './notificationService';
import surveyLinkService from './surveyLinkService';
import surveyService from './surveyService';
import userService from './userService';
import taskService from './taskService';
import titleService from './titleService';

const registerServices = ngModule => {
  registerHttpAuthInterceptors(ngModule);
  resourceWithProvider(ngModule);

  authTokenService(ngModule);
  checkpointService(ngModule);
  emailService(ngModule);
  graphQLService(ngModule);
  invitationService(ngModule);
  liaisonService(ngModule);
  notificationService(ngModule);
  organizationService(ngModule);
  participantDataService(ngModule);
  participantService(ngModule);
  participationCodeService(ngModule);
  participationService(ngModule);
  programService(ngModule);
  projectCohortService(ngModule);
  projectService(ngModule);
  surveyLinkService(ngModule);
  surveyService(ngModule);
  userService(ngModule);
  taskService(ngModule);
  titleService(ngModule);
};

export default registerServices;
