/* global window, setInterval, clearInterval, angular */

import $ from 'jquery';
import template from './index.html';


function scrollTabs(el) {
  const direction = $(el.target).is('#tab-arrow-right') ? '+=' : '-=';
  const tabsWidth = $('.nep-tabs').width();

  $('.nep-tabs').animate({
    scrollLeft: direction + tabsWidth,
  }, {
    // increase duration based on distance to travel
    duration: tabsWidth * 5,
    easing: 'swing',
    queue: false,
  });
}

function scrollStop() {
  $('.nep-tabs').stop();
}

// Add event handlers for hover and click. Adding the click handler for
// mobile devices since just adding hover doesn't allow the user to scroll
// more than once.
function addScrollArrowHoverEventHandlers() {
  $('a.tab-arrow').hover(scrollTabs, scrollStop);
  $('a.tab-arrow').click(scrollTabs);
}

// checkWidths compares the checkpointsContainer (.tabs) div with all of
// the checkpointTabs (.tab) divs. If the total with of the individual
// tabs is greater than the width of the containing div, this means that
// we need the ability to scroll horizontally, so the arrow navigation
// will be displayed.
function checkWidths() {
  const checkpointsContainer = $('.nep-tabs');
  const checkpointsTabs = $('.tab');

  const checkpointsContainerWidth = checkpointsContainer.width();
  let checkpointsTabsWidth = 0;

  checkpointsTabs.each((i, el) => {
    checkpointsTabsWidth += $(el).width();
  });

  if (checkpointsTabsWidth > checkpointsContainerWidth) {
    $('.tab-arrow').show();
  } else {
    $('.tab-arrow').hide();
  }
}

function showNavigationArrows() {
  // Hide navigation arrows, unless we need them.
  $('.tab-arrow').hide();

  // Initially determine hide/show of navigation arrows.
  // Wait until the checkpoints tabs exist before calling checkWidths.
  const tabsExist = setInterval(() => {
    const checkpointsTabs = $('.tab');
    if (checkpointsTabs.length) {
      checkWidths();
      clearInterval(tabsExist);
    }
  }, 100);

  // And check if we need navigation arrows on resize.
  $(window).resize(checkWidths);
}

// Scroll the tabs div to the active checkpoint so the active checkpoint is
// never hidden from view (unless the user scrolls on their own).
function scrollToActiveCheckpoint(checkpointId) {
  if (checkpointId) {
    // Since we don't know when the tabs and active checkpoint will be added
    // to the DOM, we keep checking for them until we find them.
    const tabsExist = setInterval(() => {
      const tabs = $('.nep-tabs');
      const activeCheckpoint = $(`#checkpoint_${checkpointId}`);

      if (tabs.length && activeCheckpoint.length) {
        tabs.animate({ scrollLeft: activeCheckpoint.position().left });
        clearInterval(tabsExist);
      }
    }, 100);
  }
}

const ckpts = [
  {
    name: 'Organization',
    ordinal: 1,
    status: 'complete',
    uid: 'Checkpoint_001',
    tasks: [],
    isVisible: true,
  },
  {
    name: 'Prepare to Participate',
    ordinal: 2,
    status: 'incomplete',
    uid: 'Checkpoint_002',
    tasks: [],
    isVisible: true,
  },
];

function controller($state, $transitions) {

  const vm = this;

  vm.$onInit = function  () {
    vm.checkpoints = ckpts;

    // Flag to help display Organization as active checkpoint during
    // program registration.
    vm.isProgramRegistrationRoute = $state.includes('programRegistration');

    // Scroll on initial view loading
    scrollToActiveCheckpoint($state.params.checkpointId);

    // Add scroll arrow event handlers
    addScrollArrowHoverEventHandlers();

    // Determine if navigation arrows should be displayed
    showNavigationArrows();
  };

  // Scroll on transition change
  $transitions.onSuccess({ to: '**.checkpoints' }, (transition) => {
    const fromId = transition.params('from').checkpointId;
    const toId = transition.params('to').checkpointId;

    if (fromId !== toId) {
      scrollToActiveCheckpoint($state.params.checkpointId);
    }
  });
}

const checkpoints = ngModule => {

  /**
   * @ngdoc component
   * @name neptuneApp.component:nepCheckpoints
   * @description
   *    Checkpoints component for displaying the list of checkpoints, their
   *    status, icon, and provide navigation to each of the checkpoint states.
   */

  ngModule.component('nepCheckpoints', {
    bindings: {
      checkpoints: '<',
    },
    controller,
    template,
  });
};

export default checkpoints;

