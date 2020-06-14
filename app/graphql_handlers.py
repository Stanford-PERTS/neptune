from google.appengine.api import memcache
from google.appengine.api import taskqueue
import graphene
import json
import logging

from gae_handlers import ApiHandler
from model import Organization, Program, ProjectCohort, User
from permission import owns
import graphql_model
import graphql_queries
import util


class NeptuneQuery(graphene.ObjectType):
    checkpoints = graphql_model.CheckpointCollection
    checkpoint = graphql_model.CheckpointResource
    organizations = graphql_model.OrganizationCollection
    organization = graphql_model.OrganizationResource
    projects = graphql_model.ProjectCollection
    project = graphql_model.ProjectResource
    # project_cohorts_by_owner = graphql_model.ProjectCohortOwnerCollection
    project_cohorts = graphql_model.ProjectCohortCollection
    project_cohort = graphql_model.ProjectCohortResource
    program_cohorts = graphql_model.ProgramCohortCollection
    program_cohort = graphql_model.ProgramCohortResource
    surveys = graphql_model.SurveyCollection
    survey = graphql_model.SurveyResource
    tasks = graphql_model.TaskCollection
    task = graphql_model.TaskResource
    users = graphql_model.UserCollection
    user = graphql_model.UserResource


NeptuneSchema = graphene.Schema(query=NeptuneQuery, auto_camelcase=False)


class GraphQLBase(ApiHandler):
    requires_auth = True

    def post(self):
        """Run any valid GraphQL query in the request body, for supers only.

        Example: All HG17 Project Cohorts (Admin Dashboard)
        See also: http://graphql.org/learn/serving-over-http/#post-request
        POST body as application/json

        {
            "query": "
                query GetAllProjectCohorts($program_label: String!) {
                  projectCohorts(program_label: $program_label) {
                    uid,
                    organization {
                      uid,
                      name,
                      liaison {
                        uid,
                        name,
                        email,
                      },
                      status,
                    },
                    checkpoints {
                      uid,
                      name,
                      ordinal,
                      status,
                    },
                  }
                }
            ",
            "variables": {"program_label": "hg17"}
        }
        """
        if not self.get_current_user().super_admin:
            return self.http_forbidden()

        params = self.get_params({
            'query': str,
            'variables': 'json',
            'operation_name': str,
        })

        result = NeptuneSchema.execute(
            params['query'],
            variable_values=params.get('variables', None),
            operation_name=params.get('operation_name', None),
        )

        if result.errors:
            raise Exception(result.errors)  # triggers 500, logged error

        self.write(result.data)


class TasklistHandler(ApiHandler):
    requires_auth = True

    def get(self, project_cohort_id):
        """Run a hard-coded query, for org admins, ideal for one tasklist."""
        project_cohort_id = ProjectCohort.get_long_uid(project_cohort_id)

        pc = ProjectCohort.get_by_id(project_cohort_id)
        if not pc:
            return self.http_not_found()

        if not owns(self.get_current_user(), project_cohort_id):
            return self.http_forbidden("You don't own this program.")

        result = NeptuneSchema.execute(
            graphql_queries.single_tasklist,
            variable_values={'uid': project_cohort_id},
        )

        if result.errors:
            raise Exception(result.errors)

        self.write(result.data)


class DashboardByOwner(ApiHandler):
    requires_auth = True

    def get(self, **kwargs):
        """Get everything for all "program cards" with checkpoint progress.

        Args:
            organization_id str optional
            user_id str optional
        """
        # Translate to long uids.
        id_kinds = (('user_id', User), ('organization_id', Organization))
        for key, klass in id_kinds:
            if key in kwargs:
                kwargs[key] = klass.get_long_uid(kwargs[key])

        # Make sure requesting user owns any specified ids.
        user = self.get_current_user()
        for key, id in kwargs.items():
            if not owns(user, id):
                return self.http_forbidden()

        result = NeptuneSchema.execute(
            graphql_queries.dashboard,
            variable_values=kwargs,
        )

        if result.errors:
            raise Exception(result.errors)

        self.write(result.data)


class SuperDashboard(ApiHandler):
    requires_auth = True

    def get(self, queue_cache_task=True):
        """Get everything for all "program cards" with checkpoint progress.

        Args:
            queue_cache_task - bool, default True, only False when this code is
                re-used within a task, to avoid recursion.

        Different from DashboardByOwner because it uses query string parameters:
        * program_label
        * cohort_label
        * organization_id
        """
        if not self.get_current_user().super_admin:
            return self.http_forbidden()

        params = self.get_params({
            'organization_id': str,
            'program_label': str,
            'cohort_label': str,
        })
        cache_key = util.cached_query_key('SuperDashboard', **params)

        cached = memcache.get(cache_key)
        if cached:
            self.response.write(cached)  # already a JSON string
            return
        # else run the query...

        program_label = params.get('program_label', None)
        if program_label:
            config = Program.get_config(program_label)
            if not config.get('listed', True):
                # This program is unlisted, don't allow it to be queried.
                # But don't respond with an error code, because when this runs
                # as a task that would cause it to retry.
                logging.info("Skipping query for unlisted program.")
                self.write([])
                return

        # Queue a task to run this same code in case we're hit by the 30
        # second limit.
        if queue_cache_task:
            taskqueue.add(
                url='/task/cache_dashboard',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                payload=self.request.query_string,
            )

        program_cohort_set = (params.get('program_label', None) and
                              params.get('cohort_label', None))
        query = (graphql_queries.program_cohort_dashboard
                 if program_cohort_set else graphql_queries.dashboard)

        result = NeptuneSchema.execute(
            # graphql_queries.dashboard,
            query,
            variable_values=params,
        )

        if result.errors:
            raise Exception(result.errors)

        memcache.set(cache_key, json.dumps(result.data))

        self.write(result.data)
