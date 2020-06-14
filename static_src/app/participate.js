export default ngModule => {
  function controller() {
    this.theSystemIsDown = false;
  }

  const template = `
    <div id="header">
      <a ui-sref="portal" ng-hide="$state === undefined || $state.is('portal')">&lt; Start Over</a>
    </div>

    <div ng-show="$ctrl.theSystemIsDown" class="system-down">
      PERTS websites will be closed for maintenance for 2 hours on Sunday, April
      28th, at 4pm pacific time.
    </div>

    <main>
      <ui-view></ui-view>
    </main>

    <div id="footer">
      <p>
        <!-- Company name intentionally omitted. -->
        &copy; {{ server_time.year }} All Rights Reserved.
      </p>
    </div>
  `;

  ngModule.component('app', {
    controller,
    template,
  });
};
