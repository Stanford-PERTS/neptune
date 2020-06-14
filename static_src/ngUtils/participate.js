import addQTools from './addQTools';
import queryOne from './queryOne';
import redirect from './redirect';
import stringToNumber from './stringToNumber';

const registerUtils = ngModule => {
  // TODO determine if this is needed
  addQTools(ngModule);
  queryOne(ngModule);
  redirect(ngModule);
  stringToNumber(ngModule);
};

export default registerUtils;
