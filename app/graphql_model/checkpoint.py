"""GraphQL Checkpoint schema."""

import graphene

from .config import default_n
from .task import Task
from gae_models import DatastoreModel, SqlModel, graphql_util
import model


class Checkpoint(graphene.ObjectType):
    class Meta:
        interfaces = (graphql_util.SqlType, )
        # default_resolver = lambda k, default, root, info: getattr(root, k, default)

    label = graphene.String()
    parent_id = graphene.ID()
    parent_kind = graphene.String()
    name = graphene.String()
    ordinal = graphene.Int()
    status = graphene.String()
    survey_id = graphene.ID()
    project_cohort_id = graphene.ID()
    cohort_label = graphene.String()
    project_id = graphene.ID()
    program_label = graphene.String()
    organization_id = graphene.ID()
    task_ids = graphene.String()
    body = graphene.String()

    def resolve_body(self, info, *args, **kwargs):
        # Note: this is a bad design if there are many fields being
        # pulled from the client dict!
        return self.to_client_dict().get('body', None)

    tasks = graphene.List(Task)

    def resolve_tasks(self, info):
        return model.Task.get(
            ancestor=DatastoreModel.id_to_key(self.parent_id),
            checkpoint_id=self.uid,
            order='ordinal',
            n=default_n,
        )


CheckpointResource = graphene.Field(
    Checkpoint,
    args={
        'uid': graphene.Argument(graphene.String),
    },
    resolver=lambda root, info, **kwargs: model.Checkpoint.get_by_id(
      kwargs['uid'],
    )
)


CheckpointCollection = graphene.Field(
    graphene.List(Checkpoint),
    resolver=lambda root, info: model.Checkpoint.get(order='ordinal',
                                                     n=default_n),
)
