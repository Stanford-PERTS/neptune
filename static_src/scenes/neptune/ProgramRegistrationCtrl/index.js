import keyBy from 'lodash/keyBy';

// Angular controller for program registration. Serves only to let the user
// choose either an existing organization or create a new one. Redirects to
// the dashboard with a new org in the case that someone has no existing orgs.
//
// N.B. Right now this treats any org that has a ProjectCohort in the program
// as unavailable for registration. The correct behavior involves choosing
// among available cohorts. I'm taking a shortcut here because we have only
// one cohort.

const ProgramRegistrationCtrl = ngModule => {
  ngModule.controller(
    'ProgramRegistrationCtrl',
    (
      $scope,
      $state,
      $sce,
      $q,
      Organization,
      Program,
      Project,
      ProjectCohort,
      User,
    ) => {
      'use strict';

      const INVALID_COHORT_MESSAGE = 'invalid cohort';

      // Necessary to mock the project cohort dashboard.
      $scope.organization = { name: 'Pending Organization' };

      const user = User.getCurrent();

      $scope.busy = false;

      // Organizations which may join the program (not already involved);
      $scope.availableOrgs = [];

      $scope.involvedPcs = [];

      Program.get({ label: $state.params.programLabel })
        .$promise.then(putProgramOnScope)
        .then(getOrgs)
        .then(putOrgsOnScope)
        .catch(handleInvalidProgram)
        .catch(handleInvalidCohort);

      // Load program to display name, description.
      function putProgramOnScope(program) {
        if (!validateCohort(program, $state.params.cohortLabel)) {
          return $q.reject(new Error(INVALID_COHORT_MESSAGE));
        }

        $scope.program = program;

        // Necessary to mock the project cohort dashboard.
        // For the Program Title to pass to the Program Card
        // Example: Growth Mindset for College Students (Spring 2017)
        $scope.cohortName =
          $scope.program.cohorts[$state.params.cohortLabel].name;
        $scope.programTitle = `${$scope.program.name} (${$scope.cohortName})`;

        $scope.displayCheckpointMetas = mockCheckpoints(program);
        $scope.checkpointBody = $sce.trustAsHtml(
          $scope.displayCheckpointMetas[0].body,
        );
      }

      function validateCohort(program, cohortLabel) {
        const cohort = program
          .registrableCohorts()
          .find(c => c.label === $state.params.cohortLabel);
        return Boolean(cohort);
      }

      function getOrgs() {
        return Organization.queryByUser({ id: User.getCurrent().uid }).$promise;
      }

      // The api provides both owned and associated orgs. Filter out the merely
      // associated ones, because they don't have rights to start projects for
      // those orgs.
      function putOrgsOnScope(allOrgs) {
        $scope.orgsById = keyBy(allOrgs, 'uid');

        // Remove any which are merely associated.
        const ownedOrgs = allOrgs.filter(org =>
          user.owned_organizations.includes(org.uid),
        );

        // Find out if any are already involved in the program.
        ownedOrgs.forEach(org => {
          ProjectCohort.queryByOrganization({ id: org.uid }, pcs => {
            const involvedPcs = pcs.filter(
              pc =>
                pc.program_label === $scope.program.label &&
                pc.cohort_label === $state.params.cohortLabel,
            );
            if (involvedPcs.length > 0) {
              // There are project cohorts with this org and program already.
              // Consider the org as not available for registration.
              // Instead, display a link to that project cohort's dashboard.
              $scope.involvedPcs = $scope.involvedPcs.concat(involvedPcs);
            } else {
              // There are no project cohorts with this org and program.
              // Consider the org as available for registration.
              $scope.availableOrgs.push(org);
            }
          });
        });
      }

      function handleInvalidProgram(reason) {
        if (reason.status !== 404) {
          return $q.reject(reason);
        }
        $state.go('.invalidCohort');
      }

      function handleInvalidCohort(reason) {
        if (reason.message !== INVALID_COHORT_MESSAGE) {
          return $q.reject(reason);
        }
        $state.go('.invalidCohort');
      }

      $scope.validate = function (org, orgIsValid, invalidMessage) {
        const user = User.getCurrent();
        $scope.organization = org;
        $scope.orgSelected = true;
        if (org.uid && user.owned_organizations.includes(org.uid)) {
          $scope.orgIsNew = false;
          $scope.alreadyAssociated = true;
        } else {
          $scope.orgIsNew = orgIsValid;
          $scope.alreadyAssociated = false;
        }
        $scope.invalidMessage = invalidMessage;
      };

      $scope.joinOrganization = function (org) {
        $scope.busy = true;
        const user = User.getCurrent();
        User.requestToJoinOrganization({ id: user.uid }, org, updatedUser => {
          // Record the new associations for the user.
          User.setCurrent(updatedUser);
          $state.go('.pending', { orgId: org.uid });
        });
      };

      const joinCohort = function (project) {
        const pc = new ProjectCohort({
          project_id: project.uid,
          organization_id: project.organization_id,
          program_label: project.program_label,
          cohort_label: $state.params.cohortLabel,
          liaison_id: project.liaison_id,
        });
        pc.$save(() => {
          $state.go('dashboard.tasks', { projectCohortId: pc.short_uid });
        });
      };

      const addProject = function (org) {
        $scope.busy = true;
        const p = new Project({
          organization_id: org.uid,
          program_label: $scope.program.label,
          liaison_id: User.getCurrent().uid,
        });
        p.$save(() => {
          joinCohort(p);
        });
      };

      $scope.addNewOrganization = function (org) {
        // Save the new org to the server.
        $scope.busy = true;
        org.$save(newOrg => {
          const user = User.getCurrent();
          user.owned_organizations.push(newOrg.uid);
          addProject(newOrg);
        });
      };

      $scope.addExistingOrganization = function (org) {
        $scope.busy = true;

        Project.queryByOrganization(
          {
            id: org.uid,
            program_label: $scope.program.label,
          },
          project => {
            if (project.length === 1) {
              // This organization has joined a previous cohort of this project.
              // Don't add a new project, just add a new pc.
              joinCohort(project[0]);
            } else {
              // This organization is joining their first cohort of this project.
              // Add a new project, which will then add a new pc.
              addProject(org);
            }
          },
        );
      };

      function mockCheckpoints(program) {
        // @todo: This is a hack. But it's a fast and effective hack. Watch out
        // for nasty maintenance issues and consider refactoring.
        // Mocks "meta" structure currently required by the
        // checkpointsSummaryItem directive. Mocks icon calculation for the same
        // by providing parent ids. Duplicates project-skipping logic in the
        // ProjectCohortTasklistsCtrl.
        let step = 1;

        const body =
          '<p>' +
          '  Welcome! We’re excited you’re here. This page will help you find ' +
          '  and register your organization in our system.' +
          '</p>';
        const metas = [
          {
            className: 'active',
            status: 'incomplete',
            status_vm: 'incomplete',
            name: 'Organization',
            parent_id: 'Organization_foo',
            body,
            step,
            isVisible: true,
          },
        ];
        $scope.program.surveys.forEach(survey => {
          survey.survey_tasklist_template.forEach(checkpoint => {
            checkpoint.parent_id = 'Survey_foo';
            checkpoint.className = 'closed';
            checkpoint.status = 'incomplete';
            checkpoint.status_vm = 'incomplete';
            checkpoint.step = ++step;
            checkpoint.isVisible = true;
            metas.push(checkpoint);
          });
        });
        return metas;
      }
    },
  );
};

export default ProgramRegistrationCtrl;
