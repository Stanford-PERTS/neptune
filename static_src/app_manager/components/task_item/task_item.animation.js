(function () {
  'use strict';

  window.ngModule.animation('.slide', () => {
    const NG_HIDE_CLASS = 'ng-hide';
    return {
      beforeAddClass(element, className, done) {
        if (className === NG_HIDE_CLASS) {
          element.slideUp(done);
        }
      },
      removeClass(element, className, done) {
        if (className === NG_HIDE_CLASS) {
          element.hide().slideDown(done);
        }
      },
    };
  });
})();
