const trustAsHtml = ngModule => {
  ngModule.filter('trustAsHtml', $sce => $sce.trustAsHtml);
};

export default trustAsHtml;
