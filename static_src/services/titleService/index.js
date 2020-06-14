const taskService = ngModule => {
  ngModule.service('Title', function Title($rootScope, $state, $transitions) {
    const title = {
      base: 'PERTS',
      state: '',
    };

    // Update the title every time the state changes
    $transitions.onSuccess({}, handleStateChanges);

    return {
      init: updateTitle,
      setDynamic,
    };

    // Grab the current state's title. You can add a title to a state by
    // adding one to it's data.title property like this:
    //
    //   data: {
    //     title: 'Tasks'
    //   }
    function handleStateChanges() {
      title.state =
        $state.current.data && $state.current.data.title
          ? $state.current.data.title
          : '';
      updateTitle();
    }

    // Set the dynamic portion of the title. This can be things like the
    // organization name, program name, etc. Child states inherit data
    // properties so we should only have to set a dynamic property once
    // and child states will also have access to this portion of the title.
    function setDynamic(title) {
      $state.current.data.dynamic = title;
      updateTitle();
    }

    // updateTitle pipe separates the title elements and updates $rootScope.
    // Title order follows the current convention on perts.net.
    function updateTitle() {
      const dynamicTitle =
        $state.current.data && $state.current.data.dynamic
          ? $state.current.data.dynamic
          : '';

      $rootScope.title = [title.state, dynamicTitle, title.base]
        .filter(function filterOutEmpty(title) {
          return title;
        })
        .join(' | ');
    }
  });
};

export default taskService;
