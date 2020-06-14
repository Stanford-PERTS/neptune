import isEmpty from 'lodash/isEmpty';
import parse from 'parse-link-header';

/**
 * Extract query string parameters from an unparsed Link header string.
 * @param {string} linkHeader - value of Link header from a response.
 * @param {string} rel - either first, previous, self, next, or last.
 * @returns {Object|undefined} query params from the url of that part of the
 *     header.
 */
export default function getLinkRel(linkHeader, rel) {
  if (isEmpty(linkHeader)) {
    return undefined;
  }
  const parsed = parse(linkHeader);
  return parsed[rel];
}
