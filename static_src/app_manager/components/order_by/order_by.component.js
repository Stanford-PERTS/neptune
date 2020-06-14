(function () {
  'use strict';

  /**
   * @ngdoc component
   * @name neptuneApp.component:orderByComponent
   * @description
   *   The orderBy component adds a sorting arrow that can be interacted with
   *   by the user in order to indicate what column in a table they would like
   *   to order the table data by.
   *
   *     <order-by name='' active='' cb=''></order-by>
   *
   *   If the `name` and `active` are equal (ignoring a possible leading `-`,
   *   which indicates descending order), then this orderBy component is the
   *   active orderBy component.
   *
   *   This component does not handle data sorting, it is up to the parent
   *   component to do so through the use of the callback function.
   */

  window.ngModule.component('orderBy', {
    bindings: {

      /**
       * The name given to this instance of the orderBy component. This can
       * be anything, but it should match up with references in the parent
       * component that is handling the actual data sorting.
       * @type {String}
       */
      name: '<',

      /**
       * The name of the currently active orderBy component.
       * @type {String}
       */
      active: '<',

      /**
       * The callback invoked when this orderBy component is clicked.
       * @type {Function}
       */
      cb: '&',
    },
    controller: OrderByComponent,
    template: require('./order_by.view.html'),
  });

  function OrderByComponent() {
    const vm = this;

    vm.state = {

      /**
       * Is this component the active orderBy component?
       * @type {Boolean}
       */
      active: false,

      /**
       * Is this component orderBy ascending?
       * @type {Boolean}
       */
      asc: true,
    };

    /**
     * Recalculate if this is the active component and whether sorting is
     * ascending or descending any time the bindings change.
     * @return {undefined}
     */
    vm.$onChanges = function () {
      determineActive();
      determineOrder();
    };

    /**
     * Determines if this component is the active orderBy component. vm.active
     * would be contained in the string vm.name, ignoring leading `-` char.
     * @affects state.active
     * @return {undefined}
     */
    function determineActive() {
      const activePattern = new RegExp(
        `${vm.active}$`
          .replace(/^-/, '') // ignore leading '-'
          .replace('.', '\\.'),
      ); // escape dots (eg `project.organization_name`)
      vm.state.active = activePattern.test(vm.name);
    }

    /**
     * Determines the sort order (asc or desc) or this component. This really
     * only matters when this is the active orderBy component.
     * @affects state.asc
     * @return {undefined}
     */
    function determineOrder() {
      if (vm.state.active) {
        vm.state.asc = vm.active.charAt(0) !== '-';
      }
    }

    /**
     * Event handler. Relays the new orderBy state via the callback.
     * @affects state.asc
     * @return {undefined}
     */
    vm.sortClick = function () {
      if (vm.state.active) {
        // if we clicked the active orderBy component, then reverse the active
        // orderBy direction
        vm.state.asc = !vm.state.asc;
        const newOrderByChar = vm.state.asc ? '' : '-';
        vm.cb({ newOrderBy: `${newOrderByChar}${vm.name}` });
      } else {
        // else, just sort by this orderBy component's default (aka name)
        vm.cb({ newOrderBy: vm.name });
      }
    };
  }
})();
