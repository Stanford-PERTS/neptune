import camelToSeparated from './camelToSeparated';
import getKind from './getKind';

function getUrlKind(uid) {
  const kind = getKind(uid);
  const standing = true;
  // plural snake case
  return `${camelToSeparated(kind, '_', standing)}s`;
}

export default getUrlKind;
