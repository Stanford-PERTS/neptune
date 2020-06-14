/**
 * Parse date string in the client's local time zone.
 *
 * @param {string} dateStr in YYYY-MM-DD format.
 * @returns {Date}
 */

import moment from 'moment';

function parseLocalDateStr(dateStr) {
  return moment(dateStr, 'YYYY-MM-DD').toDate();
}

export default parseLocalDateStr;
