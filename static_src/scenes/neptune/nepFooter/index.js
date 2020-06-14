import template from './index.html';

const nepFooter = ngModule => {
  function controller(serverTime, yellowstoneDomain) {
    const vm = this;

    window.vm = vm;

    vm.$onInit = () => {
      vm.year = new Date(serverTime).getFullYear();
      vm.domain = yellowstoneDomain;
    };
  }

  ngModule.component('nepFooter', {
    controller,
    template,
  });
};

export default nepFooter;
