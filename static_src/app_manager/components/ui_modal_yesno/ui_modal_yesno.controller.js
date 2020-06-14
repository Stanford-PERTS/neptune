// This ui component provides a custom modal layout for use with ModalService.
// Example usage:
// ModalService
// .showModal({
// templateUrl: 'components/ui_modal_yesno/ui_modal_yesno.view.html',
// controller: 'UiModalYesNoController',
// bodyClass: 'neptune-modal-open',
// inputs: {
// prompt: 'Are you sure you want to do the thing?',
// // Note: although options are optional, you must at least pass an
// // empty `options` property since options is specified as a provider.
// options: {
// danger: true, // if you'd like to display a warning yes/no
// },
// },
// }).then(function (modal) {
// modal.close.then(function (confirmed) {
// if (confirmed) {
// // PLACE YOUR CODE HERE THAT WILL OCCUR IF THE USER PRESSES THE
// // YES BUTTON ON THE YES/NO MODAL.
// }
// });
// });

(function () {
  'use strict';

  window.ngModule.controller(
    'UiModalYesNoController',
    function UiModalYesNoController($scope, close, prompt, options) {
      // Text explaining what the user is answering Yes/No to
      $scope.prompt = prompt;

      // Optional settings
      $scope.options = options;

      $scope.closeModal = function (returnValue) {
        close(returnValue);
        $scope.$destroy();
      };
    },
  );
})();
