import template from './index.html';

// nepHelpVideo Directive
// ------------------
// This directive takes:
// `video-id` attribute (YouTube Video ID)
// and embeds the corresponding YouTube video iframe.
// Usage example:
// <div nep-help-video video-id="6XfBDoDYhAA"></div>

const nepHelpVideo = ngModule => {
  const helpVideoDirective = () => {
    function helpVideoController($scope) {
      // enforce video-id parameter is a string
      // default to PERTS video
      $scope.videoSrc = angular.isString($scope.videoId)
        ? `https://www.youtube-nocookie.com/embed/${$scope.videoId}?rel=0`
        : 'https://www.youtube-nocookie.com/embed/6XfBDoDYhAA?rel=0';
    }

    return {
      scope: {
        videoId: '@',
      },
      template,
      controller: helpVideoController,
      restrict: 'A',
    };
  };

  ngModule.directive('nepHelpVideo', helpVideoDirective);
};

export default nepHelpVideo;
