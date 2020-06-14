angular.module('neptuneApp')
  .directive('userTable', [function () {
    'use strict';

    return {
      restrict: 'A',
      replace: true,
      transclude: true,
      scope: {
        'users': '='
      },
      templateUrl: 'shared/user_table.html',

      link: function(scope, element, attrs) {
        //
      }
    };

  }]);
