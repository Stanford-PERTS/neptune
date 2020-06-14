// Breaks on capital letters only. Not tested with numbers, etc.
// Standing defaults to false.

function camelToSeparated(camel, separator, standing) {
  if (standing !== true) {
    standing = false;
  }

  const regexp = /[A-Z]/g;
  const breakPoints = [];
  const substrings = [];
  let match;

  while ((match = regexp.exec(camel)) !== null) {
    breakPoints.push(regexp.lastIndex);
  }
  breakPoints.forEach((breakPoint, index) => {
    const previousBreak = index ? breakPoints[index - 1] - 1 : 0;
    substrings.push(camel.slice(previousBreak, breakPoint - 1).toLowerCase());
  });
  substrings.push(camel.slice(breakPoints.last() - 1).toLowerCase());

  // If this is StandingCamel (as opposed to drinkingCamel), ignore the
  // first break point.
  if (standing) {
    substrings.shift();
  }

  return substrings.join(separator);
}

export default camelToSeparated;
