/**
 * Given a UID or Short UID, returns the Short UID.
 * @param  {String} uid UID or Short UID
 * @return {String}     Short UID
 */

function getShortUid(uid) {
  if (!uid) {
    return undefined;
  }

  const splitIdentifier = uid.split('_');
  return splitIdentifier.length === 2 ? splitIdentifier[1] : uid;
}

export default getShortUid;
