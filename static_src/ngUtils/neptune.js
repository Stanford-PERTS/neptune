import compareTo from './compareTo';
// import keyLength from './keyLength'; // TODO needed?
import queryByCache from './queryByCache';
import queryOne from './queryOne';
import showAllWarnings from './showAllWarnings';
// import materializeModal from './materializeModal'; // TODO needed?
import nepBindMarkup from './nepBindMarkup';
import stringToNumber from './stringToNumber';
import trustAsHtml from './trustAsHtml';

const registerNgUtils = ngModule => {
  compareTo(ngModule);
  // keyLength(ngModule);
  queryByCache(ngModule);
  queryOne(ngModule);
  showAllWarnings(ngModule);
  // materializeModal(ngModule);
  nepBindMarkup(ngModule);
  stringToNumber(ngModule);
  trustAsHtml(ngModule);
};

export default registerNgUtils;
