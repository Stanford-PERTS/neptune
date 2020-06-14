import LoginCtrl from './neptune/LoginCtrl';
import ProgramRegistrationCtrl from './neptune/ProgramRegistrationCtrl';
import ProgramRegistrationPendingCtrl from './neptune/ProgramRegistrationPendingCtrl';
import RegisterCtrl from './neptune/RegisterCtrl';
import ResetPasswordCtrl from './neptune/ResetPasswordCtrl';
import SetPasswordCtrl from './neptune/SetPasswordCtrl';

import nepIndex from './neptune/nepIndex';
import nepNotifications from './neptune/nepNotifications';
import nepOrganizationInvitation from './neptune/nepOrganizationInvitation';
import nepOrganizationSearch from './neptune/nepOrganizationSearch';
import nepPlaceSearch from './neptune/nepPlaceSearch';
import nepReports from './neptune/nepReports';
import nepReportsReturning from './neptune/nepReportsReturning';
import nepFooter from './neptune/nepFooter';

const registerScenes = ngModule => {
  LoginCtrl(ngModule);
  ProgramRegistrationCtrl(ngModule);
  ProgramRegistrationPendingCtrl(ngModule);
  RegisterCtrl(ngModule);
  ResetPasswordCtrl(ngModule);
  SetPasswordCtrl(ngModule);

  nepIndex(ngModule);
  nepNotifications(ngModule);
  nepOrganizationInvitation(ngModule);
  nepOrganizationSearch(ngModule);
  nepPlaceSearch(ngModule);
  nepReports(ngModule);
  nepReportsReturning(ngModule);
  nepFooter(ngModule);
};

export default registerScenes;
