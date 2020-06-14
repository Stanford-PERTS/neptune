(function () {
  'use strict';

  window.ngModule.component('uiFilterOptions', {
    bindings: {
      filters: '<',
    },
    template: `
      <ui-card class="CardOptions">
        <div class="FilterOptions">
          <div class="FilterOptionsName">Priority</div>
          <ui-filter-options-option
            class="first"
            filters="$ctrl.filters"
            filter="'priority'"
            value="'any'"
          >
            Any
          </ui-filter-options-option>
          <ui-filter-options-option
            filters="$ctrl.filters"
            filter="'priority'"
            value="'yes'"
          >
            <i class="fa fa-star"></i>
          </ui-filter-options-option>
          <ui-filter-options-option
            class="last"
            filters="$ctrl.filters"
            filter="'priority'"
            value="'no'"
          >
            <i class="fa fa-star-o"></i>
          </ui-filter-options-option>
        </div>

        <div class="FilterOptions">
          <div class="FilterOptionsName">Org Approved?</div>
          <ui-filter-options-option
            class="first"
            filters="$ctrl.filters"
            filter="'orgApproved'"
            value="'any'"
          >
            Any
          </ui-filter-options-option>
          <ui-filter-options-option
            filters="$ctrl.filters"
            filter="'orgApproved'"
            value="'yes'"
          >
            Yes
          </ui-filter-options-option>
          <ui-filter-options-option
            class="last"
            filters="$ctrl.filters"
            filter="'orgApproved'"
            value="'no'"
          >
            No
          </ui-filter-options-option>
        </div>

        <div class="FilterOptions">
          <div class="FilterOptionsName">Org Rejected?</div>
          <ui-filter-options-option
            class="first"
            filters="$ctrl.filters"
            filter="'orgRejected'"
            value="'any'"
          >
            Any
          </ui-filter-options-option>
          <ui-filter-options-option
            filters="$ctrl.filters"
            filter="'orgRejected'"
            value="'yes'"
          >
            Yes
          </ui-filter-options-option>
          <ui-filter-options-option
            class="last"
            filters="$ctrl.filters"
            filter="'orgRejected'"
            value="'no'"
          >
            No
          </ui-filter-options-option>
        </div>

        <div class="FilterOptions">
          <div class="FilterOptionsName">Terms Accepted?</div>
          <ui-filter-options-option
            class="first"
            filters="$ctrl.filters"
            filter="'termsAccepted'"
            value="'any'"
          >
            Any
          </ui-filter-options-option>
          <ui-filter-options-option
            filters="$ctrl.filters"
            filter="'termsAccepted'"
            value="'yes'"
          >
            Yes
          </ui-filter-options-option>
          <ui-filter-options-option
            class="last"
            filters="$ctrl.filters"
            filter="'termsAccepted'"
            value="'no'"
          >
            No
          </ui-filter-options-option>
        </div>

        <div class="FilterOptions">
          <div class="FilterOptionsName">Program Approved?</div>
          <ui-filter-options-option
            class="first"
            filters="$ctrl.filters"
            filter="'programApproved'"
            value="'any'"
          >
            Any
          </ui-filter-options-option>
          <ui-filter-options-option
            filters="$ctrl.filters"
            filter="'programApproved'"
            value="'yes'"
          >
            Yes
          </ui-filter-options-option>
          <ui-filter-options-option
            class="last"
            filters="$ctrl.filters"
            filter="'programApproved'"
            value="'no'"
          >
            No
          </ui-filter-options-option>
        </div>

        <div class="FilterOptions">
          <div class="FilterOptionsName">Cohort Accepted?</div>
          <ui-filter-options-option
            class="first"
            filters="$ctrl.filters"
            filter="'projectCohortStatus'"
            value="'any'"
          >
            Any
          </ui-filter-options-option>
          <ui-filter-options-option
            filters="$ctrl.filters"
            filter="'projectCohortStatus'"
            value="'yes'"
          >
            Yes
          </ui-filter-options-option>
          <ui-filter-options-option
            class="last"
            filters="$ctrl.filters"
            filter="'projectCohortStatus'"
            value="'no'"
          >
            No
          </ui-filter-options-option>
        </div>
      </ui-card>
    `,
  });
})();
