// $resource had been configured use transform `uid` to `id`. Since we'll
// be phasing $resource out, let's make this backward/future compatible
// and accept either.

function idOrUid(entity) {
  if (!entity || typeof entity !== 'string') {
    return undefined;
  }

  return entity.id || entity.uid;
}

export default idOrUid;
