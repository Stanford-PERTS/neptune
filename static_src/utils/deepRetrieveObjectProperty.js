/**
 * Traverses into the `obj` using the `propertyString` to find the desired
 * property within `obj`. For example, given:
 *
 * obj = {
 *   liaison: { name: 'Java Script', email: 'java@script.com' },
 *   program: { name: 'Social-Belonging', label: 'cb17' },
 * };
 *
 * propertyString = 'liaison.email';
 *
 * We would be returned 'java@script.com'.
 *
 * @param  {Object} obj            The Object we want to traverse
 * @param  {String} propertyString The location within the Object we want
 * @return {Object}                If found, the value at property location
 * @return {undefined}             If not found
 */
function deepRetrieveObjectProperty(obj, propertyString) {
  let currentObjectLocation = obj;
  const props = propertyString.split('.');

  props.every(currentProp => {
    if (currentObjectLocation[currentProp] === undefined) {
      currentObjectLocation = undefined;
      // Taking advantage of the fact that `.every` will stop interating
      // as soon as the callback returns `false`.
      return false;
    }

    currentObjectLocation = currentObjectLocation[currentProp];
    return true;
  });

  return currentObjectLocation;
}

export default deepRetrieveObjectProperty;
