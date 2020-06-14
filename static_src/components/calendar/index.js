const calendar = ngModule => {
  /**
   * @ngdoc component
   * @name neptuneApp.component:nepCalendar
   * @description
   *   Simple date picker.
   */

  ngModule.component('nepCalendar', {
    bindings: {
      /**
       * Date to display in the calendar.
       * @type {Date}
       */
      date: '<',
      /**
       * Minimum date allowed.
       * @type {Date}
       */
      min: '<',
      /**
       * Maximum date allowed.
       * @type {Date}
       */
      max: '<',
      /**
       * Event for parent to bind, called when date changes.
       * @type {Function}
       */
      dateChange: '&',
    },
    template: `
      <input
        class="calendar"
        type="date"
        ng-model="$ctrl.date"
        ng-change="$ctrl.dateChange({date: $ctrl.date})"
        min="{{$ctrl.min | date:'yyyy-MM-dd'}}"
        max="{{$ctrl.max | date:'yyyy-MM-dd'}}"
      >
    `,
  });
};

export default calendar;
