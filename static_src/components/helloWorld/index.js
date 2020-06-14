import './index.scss';

const helloWorld = ngModule => {
  function controller($log, User) {
    const vm = this;
    vm.name = 'User';

    $log.info('ng-annotate-loader is working.');
  }

  const template = `
    <div class="helloWorld">
      Hello, {{ $ctrl.name }}
    </div>
  `;

  ngModule.component('helloWorld', {
    controller,
    template,
  });
};

export default helloWorld;
