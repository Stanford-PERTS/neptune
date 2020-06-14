function round(value, decimals) {
  return Number(`${Math.round(`${value}e${decimals}`)}e-${decimals}`);
}

function displayPercent(numer, denom, dbz) {
  // This makes the fuction play nice with one-time binding, because
  // angular considers a value "stable" as soon as it's not undefined.
  if (numer === undefined || denom === undefined) {
    return;
  }
  dbz = dbz === undefined ? '--' : dbz; // divide by zero symbol
  return denom === 0 ? dbz : round(numer / denom * 100, 0);
}

export default displayPercent;
