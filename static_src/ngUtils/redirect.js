const redirect = ngModule => {
  ngModule.factory('redirect', $window => {
    return function (url) {
      if ($window.debugRedirect) {
        const div = $window.document.createElement('div');
        div.id = 'redirect-to';
        div.innerHTML = url;
        div.style.display = 'none';
        $window.document.body.appendChild(div);
        console.warn(
          'window.debugRedirect is set to true; the `redirect` factory ' +
          'function will not change the currect location; the destination ' +
          'url is recorded in `div#redirect-to`.',
          url.toString(),
        );
      } else {
        $window.location.href = url;
      }
    };
  });
};

export default redirect;
