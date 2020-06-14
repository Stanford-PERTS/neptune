// http://odetocode.com/blogs/scott/archive/2014/10/13/confirm-password-validation-in-angularjs.aspx

const compareTo = ngModule => {
  ngModule.directive('compareTo', () => {
    return {
      require: 'ngModel',
      scope: {
        otherModelValue: '=compareTo',
      },
      link(scope, element, attributes, ngModel) {
        ngModel.$validators.compareTo = function(modelValue) {
          return modelValue === scope.otherModelValue;
        };

        scope.$watch('otherModelValue', () => {
          ngModel.$validate();
        });
      },
    };
  });
};

export default compareTo;
