import {
  NEPTUNE_COOKIES_AUTH_TOKEN,
  NEPTUNE_COOKIES_AUTH_USER,
} from 'config/neptune';

/**
 * Set locaStorage auth token to received auth token.
 * @param   {Object}    response fetch response object
 * @returns {undefined}
 */
export const setJwtToken = response => {
  response.headers().authorization &&
    localStorage.setItem(
      NEPTUNE_COOKIES_AUTH_TOKEN,
      response.headers().authorization.substr(7), // always begins "Bearer"
    );
};

/**
 * Get localStorage auth token.
 * @return {String} jwt auth token
 */
export const getJwtToken = () =>
  localStorage.getItem(NEPTUNE_COOKIES_AUTH_TOKEN);

export const getAuthorization = () => `Bearer ${getJwtToken()}`;

export const saveUserToLocalStorage = user => {
  try {
    localStorage.setItem(NEPTUNE_COOKIES_AUTH_USER, JSON.stringify(user));
  } catch (e) {
    localStorage.setItem(NEPTUNE_COOKIES_AUTH_USER, null);
  }
};

export const retrieveUserFromLocalStorage = () => {
  let currentUser;

  try {
    // attempt to retrieve user from localStorage
    currentUser = JSON.parse(localStorage.getItem(NEPTUNE_COOKIES_AUTH_USER));
  } catch (e) {
    currentUser = null;
  }

  return currentUser;
};

export const clearLocalStorage = () => {
  localStorage.removeItem(NEPTUNE_COOKIES_AUTH_USER);
  localStorage.removeItem(NEPTUNE_COOKIES_AUTH_TOKEN);
};

/**
 * Handles Neptune/Triton API responses.
 * @param  {Object} response fetch response object
 * @return {[type]}          [description]
 */
export const handleApiResponse = response => {
  setJwtToken(response);
  return response.data;
};
