"""GraphQL ProjectCohort schema."""

from google.appengine.api import memcache
from graphene_gae import NdbObjectType
import graphene
import logging

from .checkpoint import Checkpoint
from .config import default_n
from .organization import Organization
from .program_cohort import ProgramCohort, program_cohort_resource_resolver
from .project import Project
from .survey import Survey
from .user import User
from gae_models import DatastoreModel, graphql_util
import model
import util


def init_cached_property(root, prop):
    if not getattr(root, '_cached_properties', None):
        root._cached_properties = root.get_cached_properties()
    return root._cached_properties[prop]


class ProjectCohort(NdbObjectType):
    class Meta:
        model = model.ProjectCohort
        interfaces = (graphql_util.DatastoreType, )
        exclude_fields = ['survey_params_json', 'data_export_survey_json']
        default_resolver = graphql_util.resolve_client_prop

    survey_params = graphql_util.PassthroughScalar()
    data_export_survey = graphql_util.PassthroughScalar()

    surveys = graphene.List(Survey)

    checkpoints = graphene.List(Checkpoint)

    liaison = graphene.Field(User)

    organization = graphene.Field(Organization)

    program_cohort = graphene.Field(ProgramCohort)

    project = graphene.Field(Project)

    def resolve_surveys(self, info):
        if info.operation.name.value == 'ProgramCohortDashboard':
            return init_cached_property(self, 'surveys')
        return model.Survey.get(project_cohort_id=self.uid, order='ordinal',
                                n=default_n)

    def resolve_checkpoints(self, info):
        if info.operation.name.value == 'ProgramCohortDashboard':
            return init_cached_property(self, 'checkpoints')
        return model.Checkpoint.for_tasklist(self)

    def resolve_liaison(self, info):
        return model.User.get_by_id(self.liaison_id)

    def resolve_organization(self, info):
        if info.operation.name.value == 'ProgramCohortDashboard':
            return init_cached_property(self, 'organization')
        return model.Organization.get_by_id(self.organization_id)

    def resolve_program_cohort(self, info):
        return program_cohort_resource_resolver(self.program_label,
                                                self.cohort_label)

    def resolve_project(self, info):
        if info.operation.name.value == 'ProgramCohortDashboard':
            return init_cached_property(self, 'project')
        return model.Project.get_by_id(self.project_id)


ProjectCohortResource = graphene.Field(
    ProjectCohort,
    args={
        'uid': graphene.Argument(graphene.String),
    },
    resolver=lambda root, info, **kwargs: model.ProjectCohort.get_by_id(
        kwargs['uid'],
    )
)


def pc_collection_resolver(root, info, **kwargs):
    """Query project cohorts with lots of associated data and agressive caching.

    Can be called three ways, based on what's in kwargs:

    1. 'user_id' - /api/users/X/dashboard, all pc's owned by a user
    2. 'organization_id' - /api/organizations/X/dashboard, all pc's in an org
    3. 'program_label' and 'cohort_label' - /api/dashboard, all pc's in that
       cohort.
    """
    # Most kwargs can be passed directly to get(), but if this is a query for
    # project cohorts owned by a certain user, there's one extra step.
    user_id = kwargs.pop('user_id', None)
    if user_id:
        user = model.User.get_by_id(user_id)
        if not user.owned_organizations:
            return []
        kwargs['organization_id'] = user.owned_organizations

    util.profiler.add_event("querying pcs")
    pcs = list(model.ProjectCohort.get(n=default_n, **kwargs))

    # Get cached properties for these project cohorts all at once. See
    # graphql_util.resolve_client_prop().
    pcs_by_memkey = {util.cached_properties_key(pc.uid): pc for pc in pcs}

    # memcache.get_multi only returns results for keys it finds; those it
    # doesn't find are missing (rather than being set to None)
    mem_results = memcache.get_multi(pcs_by_memkey.keys())
    for memkey, props in mem_results.items():
        pc = pcs_by_memkey[memkey]
        pc._cached_properties = props

    # Go to the db for pc's which didn't have memcache results. Refresh
    # memcache all at once with the results.
    uncached = {memkey: pc for memkey, pc in pcs_by_memkey.items()
                if memkey not in mem_results.keys()}
    util.profiler.add_event("batch cached pc props")
    cached_pc_props_by_id = model.ProjectCohort.batch_cached_properties_from_db(
        project_cohorts=uncached.values()
    )

    # Inform memcache about all the properties we fetched from the db.
    to_set = {}
    for memkey, pc in uncached.items():
        props = cached_pc_props_by_id[pc.uid]
        pc._cached_properties = props
        to_set[memkey] = props
    memcache.set_multi(to_set)

    # Projects have their own cached properties which we can also batch, with
    # data that's already been fetched.
    util.profiler.add_event("batch cached project props")
    cached_project_props_by_id = model.Project.batch_cached_properties_from_db(
        projects=[pc._cached_properties['project'] for pc in pcs],
        organizations=[pc._cached_properties['organization'] for pc in pcs],
    )
    for pc in pcs:
        props = cached_project_props_by_id[pc.project_id]
        pc._cached_properties['project']._cached_properties = props

    util.profiler.add_event("handing off to graphql")
    return pcs


ProjectCohortCollection = graphene.Field(
    graphene.List(ProjectCohort),
    args={
        'organization_id': graphene.Argument(graphene.String),
        'program_label': graphene.Argument(graphene.String),
        'cohort_label': graphene.Argument(graphene.String),
        'user_id': graphene.Argument(graphene.String),
    },
    resolver=pc_collection_resolver,
)
