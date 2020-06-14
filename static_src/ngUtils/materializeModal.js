const materializeModal = ngModule => {
  ngModule.factory(
    'materializeModal',
    // The jquery plugin from materializecss for opening modals doesn't work.
    // This imitates the effect of such.
    // Example:
    // function MyController(materializeModal) {
    //   this.myModal = materializeModal($('#my-div'));
    //   this.myModal('open');
    //   this.myModal('close');
    // }
    element =>
      function materializeModal(openOrClose) {
        $(element).css({
          'z-index': openOrClose === 'open' ? 1003 : '',
          display: openOrClose === 'open' ? 'block' : '',
          opacity: openOrClose === 'open' ? 1 : '',
          transform: openOrClose === 'open' ? 'scaleX(1)' : '',
          top: openOrClose === 'open' ? '10%' : '',
        });
      },
  );
};

export default materializeModal;
