const keyLength = ngModule => {
  ngModule.filter(
    'keyLength',
    obj => (angular.isObject(obj) ? Object.keys(obj).length : 0),
  );
};

export default keyLength;
