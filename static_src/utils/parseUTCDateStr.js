/**
 * Parse date string in UTC.
 *
 * @param {string} dateStr in YYYY-MM-DD format.
 * @returns {Date}
 */

import moment from 'moment';

function parseUTCDateStr(dateStr) {
  return moment.utc(dateStr, 'YYYY-MM-DD').toDate();
}

export default parseUTCDateStr;
