// Validates if the provided string is numeric
// http://stackoverflow.com/a/1830844
function isStringNumeric(s) {
  return !isNaN(parseFloat(s)) && isFinite(s);
}

export default isStringNumeric;
