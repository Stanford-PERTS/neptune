const nepIndex = ngModule => {
  ngModule.component('nepIndex', {
    controller($scope, $state, User) {
      const vm = this;

      vm.$onInit = function() {
        if (User.loggedIn()) {
          $state.go('dashboard', {}, { location: 'replace' });
        } else {
          $state.go('login', { location: 'replace' });
        }
      };
    },
    template: `
        </div class="index-page">
          <div class="container">
            <div class="row">
              <div class="col s12">
                <div class="card">
                  <div class="card-stacked">
                    <div class="card-content center-align">
                      <span class="card-title">Welcome to the PERTS Research Platform</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col s12">
                <div class="card">
                  <div class="card-stacked">
                    <div class="card-content">
                      <a ui-sref="login" class="waves-effect waves-light btn">Log in</a>
                      <span class="btn-instructions">If you already have an account</span>
                      <br><br>
                      <a ui-sref="register({program: 'cg17'})"
                         class="waves-effect waves-light btn">Register</a>
                      <span class="btn-instructions">If you'd like to join Growth Mindset for College Students</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `,
  });
};

export default nepIndex;
