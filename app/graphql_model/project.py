"""GraphQL Project schema."""

import graphene
from graphene_gae import NdbObjectType

from .config import default_n
from gae_models import DatastoreModel, graphql_util
import model


class Project(NdbObjectType):
    class Meta:
        model = model.Project
        interfaces = (graphql_util.DatastoreType, )
        exclude_fields = []
        default_resolver = graphql_util.resolve_client_prop

    last_active = graphql_util.DatastoreDateTimeScalar()

    organization_name = graphene.String()
    program_name = graphene.String()
    program_description = graphene.String()
    organization_status = graphene.String()


ProjectResource = graphene.Field(
    Project,
    args={
        'uid': graphene.Argument(graphene.String),
    },
    resolver=lambda root, info, **kwargs: model.Project.get_by_id(kwargs['uid'])
)


ProjectCollection = graphene.Field(
    graphene.List(Project),
    resolver=lambda root, info: model.Project.get(n=default_n),
)
