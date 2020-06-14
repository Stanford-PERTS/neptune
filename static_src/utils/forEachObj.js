function forEachObj(obj, f, thisObj) {
  Object.keys(obj).forEach((k, i) => {
    f.call(thisObj, k, obj[k]);
  });
}

export default forEachObj;
