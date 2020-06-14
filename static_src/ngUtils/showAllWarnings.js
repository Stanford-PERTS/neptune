import forEachObj from 'utils/forEachObj';

const showAllWarnings = ngModule => {
  ngModule.factory('showAllWarnings', () => form => {
    // The form.$error object stores invalid ng-model fields in lists keyed
    // by the type of error. For instance, if you have two blank required
    // fields, and one field whose entry doesn't match the ng-pattern, then
    // $error is {required: [field, field], pattern: [field]}
    forEachObj(form.$error, (errorType, fields) => {
      fields.forEach(errorField => {
        errorField.$setTouched();
        errorField.$setDirty();
      });
    });
  });
};

export default showAllWarnings;
