import blank from 'components/blank';
import calendar from 'components/calendar';
import checkpoints from 'components/checkpoints';
import checkpointsEncourage from 'components/checkpoints_encourage';
import customPortalTask from 'components/custom_portal_task';
import dash from 'components/dash';
import organization from 'components/organization';
import nepHelpVideo from 'components/nepHelpVideo';

const registerComponents = ngModule => {
  blank(ngModule);
  calendar(ngModule);
  checkpoints(ngModule);
  checkpointsEncourage(ngModule);
  customPortalTask(ngModule);
  dash(ngModule);
  organization(ngModule);
  nepHelpVideo(ngModule);
};

export default registerComponents;
