"""GraphQL Task schema."""

import graphene
from graphene_gae import NdbObjectType

from .config import default_n
from gae_models import DatastoreModel, graphql_util
import model


class Task(NdbObjectType):
    class Meta:
        model = model.Task
        exclude_fields = ['short_uid']
        interfaces = (graphql_util.DatastoreType,)
        default_resolver = graphql_util.resolve_client_prop

    # These are in the datastore but need custom typing.
    due_date = graphql_util.DatastoreDateScalar()
    completed_date = graphql_util.DatastoreDateScalar()

    # These are drawn from the client dictionary.
    action_statement = graphene.String()
    body = graphene.String()
    counts_as_program_complete = graphene.Boolean()
    data_admin_only_visible = graphene.Boolean()
    data_type = graphene.String()
    name = graphene.String()
    non_admin_may_edit = graphene.Boolean()
    parent_id = graphene.ID()
    select_options = graphql_util.PassthroughScalar()
    short_parent_id = graphene.ID()


TaskResource = graphene.Field(
    Task,
    args={
        'uid': graphene.Argument(graphene.String),
    },
    resolver=lambda root, info, **kwargs: model.Task.get_by_id(kwargs['uid'])
)


TaskCollection = graphene.Field(
    graphene.List(Task),
    resolver=lambda root, info: model.Task.get(order='ordinal', n=default_n),
)
