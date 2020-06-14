(function () {
  'use strict';

  /**
   * @ngdoc service
   * @name neptuneApp.service:DashboardService
   * @description
   *   The DashboardService contains functions to query and wrangle dashboard
   *   data agnostic of event-driven UI stuff.
   */

  class DashboardService {
    constructor(
      $q,
      Checkpoint,
      Email,
      GraphQL,
      Organization,
      Program,
      Project,
      ProjectCohort,
      Survey,
      Task,
      User,
    ) {
      // service dependencies
      this.$q = $q;
      this.Checkpoint = Checkpoint;
      this.Email = Email;
      this.GraphQL = GraphQL;
      this.Organization = Organization;
      this.Program = Program;
      this.ProjectCohort = ProjectCohort;
      this.Project = Project;
      this.Survey = Survey;
      this.Task = Task;
      this.User = User;

      /**
       * The combined Dashboard data, an array containing all Dashboard data.
       * Each element of the array is a single Project joined together with its
       * corresponding Organization Checkpoint and Project Checkpoint.
       *
       * For consistency, we try to refer to a single instance of these elements
       * as a `projectDataRow`.
       *
       * [
       *   ...,
       *   {
       *     project,
       *     orgCheckpoint, (organization_id === project.organization_id)
       *     projectCheckpoint (project_id === project.uid)
       *   },
       *   ...
       * ]
       * @type {Array}
       */
      this.data = [];

      /**
       * Promise that can be used to determine if Dashboard data has loaded.
       * @type {Promise}
       */
      this.loaded = this.$q.defer();
    }

    /**
     * If the dashboard has been re-mounted, don't use old loaded promises from
     * the service, because it has already resolved and code won't wait for new
     * data.
     */
    resetLoaded() {
      this.loaded = this.$q.defer();
    }

    /**
     * Query server for data & prepare data for use on Dashboard.
     * @param  {Object} params query options, passed through to GraphQL.query
     * @return {Array}         rows of Dashboard data (project cohorts)
     */
    query(params) {
      return this.GraphQL.query(params)
        .then(response =>
          // If a plain object received, wrap it in an array.
           Array.isArray(response) ? response : [response]
        )
        .then(newDataRows => {
          this.prepareDataRows(newDataRows);
          // These rows are "linked" in the sense that they are the same object
          // references that were previously used.
          const linkedDataRows = this.addToData(newDataRows);
          this.loaded.resolve(linkedDataRows);
          return linkedDataRows;
        });
    }

    addToData(dataRows = []) {
      return dataRows.map(dataRow => {
        const existing = this.data.find(
          d => d.projectCohort.uid === dataRow.projectCohort.uid,
        );
        const existingIndex = this.data.indexOf(existing);

        if (existingIndex > -1) {
          // maintain ui state across queries
          const existingIsSelected = existing.selected;
          const existingAdminPanel = existing.adminPanel;

          // Don't just assign the new row to the cache. That results in various
          // components having different copies of objects with the same id.
          angular.merge(existing, dataRow);

          existing.selected = existingIsSelected;
          existing.adminPanel = existingAdminPanel;

          return existing;
        }
        this.data.push(dataRow);
        return dataRow;
      });
    }

    /**
     * Move all properties that make up a Project Cohort into a property of the
     * dataRow called `projectCohort`. This is a temporary function to match up
     * the format of data coming from GraphQL to what we are currently expecting
     * in our app.
     * @param  {Object} dataRow single row of GraphQL data
     * @return {Object}         single row of Dashboard data (project cohort)
     */
    reorganizeDataRowStructure(dataRow) {
      const decoratedProps = [
        // Don't remove props added by GraphQL
        'checkpoints',
        'liaison',
        'organization',
        'program',
        'program_cohort',
        'project',
        'surveys',
        // Don't remove the new prop we're adding below
        'projectCohort',
      ];

      dataRow.projectCohort = {};

      // Move all props except for those decoratedProps
      for (const prop in dataRow) {
        if (dataRow.hasOwnProperty(prop) && !decoratedProps.includes(prop)) {
          dataRow.projectCohort[prop] = dataRow[prop];
          delete dataRow[prop];
        }
      }

      return dataRow;
    }

    /**
     * Pulls checkpoints from the `checkpoints` property and places them into
     * the `organizationCheckpoint`, `projectCheckpoint`, or `surveyCheckpoints`
     * properties. This is used to do things such as easily identifying if an
     * organization has been approved.
     * @param  {Object} dataRow single row of Dashboard data (project cohort)
     * @return {Object}         single row of Dashboard data (project cohort)
     */
    groupCheckpoints(dataRow) {
      dataRow.checkpoints.forEach(checkpoint => {
        switch (checkpoint.parent_kind) {
          case 'Organization':
            dataRow.organizationCheckpoint = checkpoint;
            return;

          case 'Project':
            dataRow.projectCheckpoint = checkpoint;
            return;

          case 'Survey':
            const survey = dataRow.surveys.find(
              s => s.uid === checkpoint.survey_id,
            );
            checkpoint.surveyOrdinal = survey.ordinal;
            dataRow.surveyCheckpoints = dataRow.surveyCheckpoints || [];
            dataRow.surveyCheckpoints.push(checkpoint);
            dataRow.surveyCheckpoints.sort((a, b) => {
              // Prefer to order by survey ordinal.
              if (a.surveyOrdinal !== b.surveyOrdinal) {
                return a.surveyOrdinal - b.surveyOrdinal;
              }
              // Otherwise order by checkpoint ordinal.
              return a.ordinal - b.ordinal;
            });


          default:

        }
      });

      return dataRow;
    }

    /**
     * Calls all of the individual data prep/manipulation functions required to
     * use the Dashboard data.
     * @param  {Array} dataRows rows of Dashboard data (project cohorts)
     * @return {Array}          rows of Dashboard data (project cohorts)
     */
    prepareDataRows(dataRows) {
      dataRows.forEach(pc => {
        this.reorganizeDataRowStructure(pc);
        this.groupCheckpoints(pc);
        this.calculateCheckpoints(pc);
        this.addProjectCohortVisibleStatusSingle(pc.projectCohort);
        // Tasks for visible checkpoints and the invisible project checkpoint.
        pc.checkpoints.concat(pc.projectCheckpoint).forEach(c => {
          (c.tasks || []).forEach(this.Task.addTaskMetaData);
        });
      });
      return dataRows;
    }

    /**
     * Add a _vm version of projectCohort.status that is a duplicate of
     * the actual status. This allows super_admins to toggle the project
     * cohort status on the project cohort status panel while not
     * altering the visible status. We will then update the visible
     * version any time we get a project cohort response back from the
     * server
     */
    addProjectCohortVisibleStatusSingle(projectCohort) {
      projectCohort.status_vm = projectCohort.status;
      return projectCohort;
    }

    addProjectCohortVisibleStatus(projectDataRows) {
      projectDataRows.forEach(projectDataRow => {
        projectDataRow.projectCohort.status_vm =
          projectDataRow.projectCohort.status;
      });
      return projectDataRows;
    }

    /**
     * Calculate visible checkpoints.
     */
    calculateCheckpoints(projectDataRow) {
      // Organization checkpoint, visible == actual
      projectDataRow.organizationCheckpoint.status_vm =
        projectDataRow.organizationCheckpoint.status;

      // We want to collapse the Project checkpoint into the first Survey
      // checkpoint. To do this, we first assign each Survey visible status to
      // its actual status. We then go back and combine the Project with the
      // Survey checkpoint (sorted by ordinal).
      projectDataRow.surveyCheckpoints.forEach(
        cp => (cp.status_vm = cp.status),
      );

      const projectCheckpoint = projectDataRow.projectCheckpoint;
      const collapsedSurveyCheckpoint = projectDataRow.surveyCheckpoints[0];
      const superAdmin = this.User.isSuperAdmin();

      // If actual is waiting, PERTS admins should see waiting, but we report
      // completed to Org Admins since they don't need to do anything.
      if (projectCheckpoint.status === this.Checkpoint.WAITING_STATUS) {
        if (superAdmin) {
          projectCheckpoint.status_vm = this.Checkpoint.WAITING_STATUS;
        } else {
          projectCheckpoint.status_vm = this.Checkpoint.COMPLETE_STATUS;
        }
      }

      // If actual is waiting, PERTS admins should see waiting, but we report
      // completed to Org Admins since they don't need to do anything.
      if (collapsedSurveyCheckpoint.status === this.Checkpoint.WAITING_STATUS) {
        if (superAdmin) {
          collapsedSurveyCheckpoint.status_vm = this.Checkpoint.WAITING_STATUS;
        } else {
          collapsedSurveyCheckpoint.status_vm = this.Checkpoint.COMPLETE_STATUS;
        }
      }

      // Actual complete == visual complete
      if (projectCheckpoint.status === this.Checkpoint.COMPLETE_STATUS) {
        projectCheckpoint.status_vm = this.Checkpoint.COMPLETE_STATUS;
      }

      // Actual complete == visual complete
      if (
        collapsedSurveyCheckpoint.status === this.Checkpoint.COMPLETE_STATUS
      ) {
        collapsedSurveyCheckpoint.status_vm = this.Checkpoint.COMPLETE_STATUS;
      }

      // And the actual collapsing...
      if (
        projectCheckpoint.status_vm === this.Checkpoint.WAITING_STATUS ||
        // If either checkpoint is waiting, then display waiting.
        collapsedSurveyCheckpoint.status_vm === this.Checkpoint.WAITING_STATUS
      ) {
        collapsedSurveyCheckpoint.status_vm = this.Checkpoint.WAITING_STATUS;
      } else if (
        projectCheckpoint.status_vm === this.Checkpoint.COMPLETE_STATUS &&
        collapsedSurveyCheckpoint.status_vm === this.Checkpoint.COMPLETE_STATUS
      ) {
        // If both checkpoints are complete, then display complete.
        collapsedSurveyCheckpoint.status_vm = this.Checkpoint.COMPLETE_STATUS;
      } else {
        // Else, display incomplete.
        collapsedSurveyCheckpoint.status_vm = this.Checkpoint.INCOMPLETE_STATUS;
      }

      // Finally, set the checkpoints property to the Organization checkpoint
      // plus all of the Survey checkpoints.
      projectDataRow.checkpoints = [
        projectDataRow.organizationCheckpoint,
        ...projectDataRow.surveyCheckpoints,
      ];

      return projectDataRow;
    }

    /**
     * Recalculates the visible checkpoints for the provided projectDataRow.
     */
    updateProjectDataRow(projectDataRow) {
      // query organization checkpoint
      const organizationCheckpoint = this.Checkpoint.queryByOrganization({
        id: projectDataRow.organization.uid,
      }).$promise;

      // query project checkpoint
      const projectCheckpoint = this.Checkpoint.queryByProject({
        id: projectDataRow.project.uid,
      }).$promise;

      // query survey checkpoints
      const surveyCheckpoints = this.$q.all(
        projectDataRow.surveyCheckpoints.map(
          cp =>
            this.Checkpoint.get({
              id: cp.uid,
            }).$promise,
        ),
      );

      // recalculate visible checkpoints
      this.$q
        .all({
          organizationCheckpoint,
          projectCheckpoint,
          surveyCheckpoints,
        })
        .then(checkpoints => {
          projectDataRow.organizationCheckpoint =
            checkpoints.organizationCheckpoint[0];
          projectDataRow.projectCheckpoint = checkpoints.projectCheckpoint[0];
          projectDataRow.surveyCheckpoints = checkpoints.surveyCheckpoints;
          return projectDataRow;
        })
        .then(projectDataRow => this.calculateCheckpoints(projectDataRow));
    }

    /**
     * Returns the dataRow from Dashboard data array where the Project Cohort's
     * short UID matches the provided.
     * @param  {string}  shortUid short UID of desired project cohort
     * @param  {boolean} includeEverything default false, if true returns
     *                   tasklist data which includes tasks, otherwise dashboard
     *                   data which doesn't.
     * @return {Object}  promise with single row of Dashboard data (project cohort)
     */
    getProjectDataRow(shortUid, includeEverything = false) {
      return this.loaded.promise.then(() => {
        const dataRow = this.data.find(
          p => p.projectCohort.short_uid === shortUid,
        );
        if (includeEverything && !dataRow.checkpoints[0].tasks) {
          // Check that this data row is from the /api/tasklist endpoint and
          // includes tasks within each checkpoint. Otherwise re-query.
          // Assume you can just check the first checkpoint.
          return (
            this.query({ project_cohort_id: shortUid })
              // Unwrap the data from its array because we know there'so only one.
              .then(response => response[0])
          );
        }
        return this.$q.when(dataRow);
      });
    }

    /**
     */
    getProgram(projectDataRow) {
      // Don't requery for program information
      if (!projectDataRow || projectDataRow.program) {
        return;
      }

      return this.$q
        .when()
        .then(() => this.Program.get({
            label: projectDataRow.program_cohort.program_label,
          }).$promise)
        .then(program => {
          projectDataRow.program = program;
          return projectDataRow;
        });
    }

    /**
     */
    getOrganization(projectDataRow) {
      return this.$q
        .when()
        .then(() => this.Organization.get({
            id: projectDataRow.projectCohort.organization_id,
          }).$promise)
        .then(organization => {
          projectDataRow.organization = organization;
          return projectDataRow;
        });
    }

    /**
     */
    getOrganizationApprovalTask(projectDataRow) {
      return this.$q
        .when()
        .then(() => this.Organization.getTaskOrdinalAndIndexByLabel())
        .then(taskOrdinalAndIndex => {
          // get the Org Approval Task ID from the Org Checkpoints
          const taskIds = projectDataRow.organizationCheckpoint.task_ids;
          const taskIndex = taskOrdinalAndIndex.index;
          return angular.fromJson(taskIds)[taskIndex];
        })
        .then(taskId =>
          // get the Org Approval Task
           this.Task.get({ id: taskId })
        )
        .then(orgApprovalTask => {
          // add Org Approval Task to projectDataRow
          projectDataRow.orgApprovalTask = orgApprovalTask;
          return projectDataRow;
        });
    }

    /**
     * Given a projectDataRow, return the task object of the approval task.
     *
     * @param  {Object} projectDataRow Single project element of `data` array.
     * @param  {boolean} toLink        Is the task for display purposes?
     * @return {Object} Approval task.
     */
    getParticipationApprovalTask(projectDataRow, toLink = true) {
      // Checkpoint uid and task label of actual approval task
      const id = projectDataRow.projectCheckpoint.uid;
      // `loa_approval` refers to Letter of Approval, which was an older version
      // of the task. This was kept so that references to the label don't break.
      const label = 'loa_approval';

      return this.Checkpoint.getTaskWithLabel({ id, label }).then(task => {
        if (toLink) {
          // Pass back the retrieved task with the constructed second
          // checkpoint uid that we display in the tasklist.
          task.checkpoint_id = projectDataRow.checkpoints[1].uid;
        }

        return task;
      });
    }

    /**
     */
    getInviteUsersTask(projectDataRow) {
      const id = projectDataRow.checkpoints[0].uid;
      const label = 'organization__invite';
      return this.Checkpoint.getTaskWithLabel({ id, label });
    }

    /**
     * updateOrganization updates the organization and all related parts of the
     * associated projectDataRow.
     *
     * @param  {Object} projectDataRow Single project element of `data` array.
     * @return {undefined}
     */
    updateOrganization(projectDataRow) {
      return this.$q
        .when()
        .then(() => {
          // Update organization
          const { organization } = projectDataRow;
          return this.Organization.put(organization);
        })
        .then(org => {
          // The above updates related org, The server will also update the
          // associated project, but will only return the org. So also modify
          // our copy of the project to keep the client model up to date.
          projectDataRow.project.organization_status = org.status;
          projectDataRow.project.organization_name = org.name;

          // Our POID is a serialization of several other properties, as defined
          // by the server. In case it has updated the poid, explicitly store it
          // from the response.
          projectDataRow.organization.poid = org.poid;
          
          return projectDataRow;
        })
        .then(() => {
          const { orgApprovalTask, organization } = projectDataRow;

          // Rejected orgs should never have a complete approval task.
          if (organization.status === this.Organization.REJECTED_STATUS) {
            // Note!! the task service _transforms_ the status property based
            // on the attachment and the data type, so setting the status here
            // will have unpredictable effects. In this case, the date type is
            // 'input:text' and so the falsey attachment is transformed to an
            // incomplete status.
            orgApprovalTask.attachment = ''; // status will be incomplete
          } else {
            // Update Task attachment with POID. Status will be complete, see
            // notes above.
            orgApprovalTask.attachment = organization.poid;
          }

          return this.Task.put(orgApprovalTask);
        })
        .then(() =>
          // Update Checkpoint
           this.Checkpoint.updateStatus({
            id: projectDataRow.orgApprovalTask.checkpoint_id,
          })
        )
        .then(updatedCheckpoint => {
          // Update Checkpoint, client model
          projectDataRow.organizationCheckpoint = updatedCheckpoint;
        })
        .then(() => projectDataRow)
        .catch(error => this.$q.reject(error));
    }

    /**
     * Update Project and ProjectCohort of the provided dataRow.
     * @param  {Object} dataRow single row of Dashboard data (project cohort)
     * @return {Object}         single row of Dashboard data (project cohort)
     */
    updateProjectAndProjectCohort(dataRow) {
      const { project, projectCohort } = dataRow;

      return this.$q
        .all([
          this.Project.put(project),
          this.ProjectCohort.put(projectCohort).then(() =>
            this.addProjectCohortVisibleStatusSingle(projectCohort),
          ),
        ])
        .catch(error => this.$q.reject(error));
    }

    /**
     * getLiaisonData gets the Liaison details of the provided projectDataRow
     * and adds it to the projectDataRow.
     */
    getLiaison(projectDataRow) {
      let orgPromise;
      if (projectDataRow.organization.liaison_id) {
        orgPromise = this.$q.when(projectDataRow.organization);
      } else {
        const organizationId = projectDataRow.projectCohort.organization_id;
        orgPromise = this.Organization.get({ id: organizationId }).$promise;
      }

      return orgPromise
        .then(organization => this.User.get({ id: organization.liaison_id }).$promise)
        .then(liaison => {
          projectDataRow.liaison = liaison;
          return projectDataRow;
        });
    }

    /**
     * getLiaisonEmails gets the Liaison emails of the provided projectDataRow.
     * Note: emails are retrieved based on email address. If liaison changes,
     * there isn't currently a way to view emails sent to the previous liaison.
     */
    getLiaisonEmails(projectDataRow) {
      const liaison = projectDataRow.liaison;
      return this.Email.query({ to_address: liaison.email }).$promise.then(
        emails => {
          projectDataRow.emails = emails.sort((a, b) => {
            if (a.created < b.created) {
              return 1;
            } else if (a.created > b.created) {
              return -1;
            }
              return 0;

          });
          return projectDataRow;
        },
      );
    }

    /**
     * getLiaisonsByProjects retrieves an array of the Liaison name, email and
     * associated org (the organization associated with the projectDataRow) of
     * the provided projectDataRows.
     *
     * @param  {Object} projectDataRow Single project element of `data` array.
     * @return {Array}
     */
    getLiaisonsByProjects(projectDataRows) {
      const organizationIds = projectDataRows.map(p => p.organization.uid);

      if (organizationIds.length === 0) {
        return this.$q.when([]);
      }

      return (
        this.Organization.query({ uid: organizationIds })
          .$promise// place organizations into an object with organizations property
          .then(organizations => {
            return { organizations };
          })
          // get associated liaisons and add to data object's liaisons property
          .then(({ organizations }) => {
            const liaisonIds = organizations.map(o => o.liaison_id);
            const liaisons = this.User.query({ uid: liaisonIds }).$promise;
            return this.$q.all({
              organizations,
              liaisons,
            });
          })
          .then(({ organizations, liaisons }) => {
            projectDataRows.forEach(p => {
              p.organization = organizations.find(
                o => p.organization.uid === o.uid,
              );
              p.liaison = liaisons.find(
                l => p.organization.liaison_id === l.uid,
              );
            });
            return projectDataRows;
          })
      );
    }

    /**
     * togglePriority toggles the priority of the Project associated with the
     * provided projectDataRow.
     *
     * @param  {Object} projectDataRow Single project element of `data` array.
     */
    togglePriority(projectDataRow) {
      const { project } = projectDataRow;
      project.priority = !project.priority;
      return this.Project.put(project);
    }

    /**
     * Set flag for all admin panels to false (closed).
     */
    closeAdminPanels() {
      this.data.forEach(dataRow => (dataRow.adminPanel = false));
    }
  }

  window.ngModule.service('Dashboard', DashboardService);
})();
