// When a parent route specified a component for a named ui-view, the children
// components will render that same component unless they override it. This
// component allows us to specify an blank override when we don't want to render
// anything in a named ui-view.

const blank = ngModule => {
  ngModule.component('nepBlank', { template: '' });
};

export default blank;
