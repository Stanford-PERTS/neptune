const stringToNumber = ngModule => {
  // Cribbed from:
  // https://docs.angularjs.org/error/ngModel/numfmt
  ngModule.directive('stringToNumber', () => {
    return {
      require: 'ngModel',
      link(scope, element, attrs, ngModel) {
        ngModel.$parsers.push(value => `${value}`);
        ngModel.$formatters.push(value => parseFloat(value));
      },
    };
  });
};

export default stringToNumber;
