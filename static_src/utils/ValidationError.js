/** Represents an mistake made by the user the UI should communicate. */
class ValidationError extends Error {

  /**
   * Create an error.
   * @param  {String}    message description of the error
   * @return {error}             to be used to throw or reject
   */
  constructor(message = '') {
    super(message);
    this.message = message;
    this.name = 'ValidationError';
  }
}

export default ValidationError;
