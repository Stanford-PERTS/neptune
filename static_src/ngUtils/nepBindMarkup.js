/**
 * Use when you have angular markup as a string and want to render it. We
 * use this in tasks whose templates are retrieved over AJAX.
 *
 * Angular expressions in the string are evaluated against the parent scope
 * because this directive doesn't declare an isolate scope.
 *
 * For example, if you have '{{ $ctrl.foo }} bar' (note: that's a string)
 * stored in scope.fooMarkup, and 'foo' stored in scope.foo, you can write
 * this in your view:
 *     <div nep-bind-markup="$ctrl.fooMarkup"></div>
 * and get this:
 *     <div>foo bar</div>
 */

const nepBindMarkup = ngModule => {
  ngModule.directive('nepBindMarkup', $compile => {
    return {
      restrict: 'A',
      link(scope, element, attrs) {
        const ngMarkup = scope.$eval(attrs.nepBindMarkup);
        element.append($compile(`<div>${ngMarkup}</div>`)(scope));
      },
    };
  });
};

export default nepBindMarkup;
