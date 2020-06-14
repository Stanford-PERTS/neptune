"""GraphQL Survey schema."""

import graphene
from graphene_gae import NdbObjectType

from .config import default_n
from gae_models import DatastoreModel, graphql_util
import model


class Survey(NdbObjectType):
    class Meta:
        model = model.Survey
        exclude_fields = []
        interfaces = (graphql_util.DatastoreType,)
        default_resolver = graphql_util.resolve_client_prop

    # These are drawn from the client dictionary.
    name = graphene.String()


SurveyResource = graphene.Field(
    Survey,
    args={
        'uid': graphene.Argument(graphene.String),
    },
    resolver=lambda root, info, **kwargs: model.Survey.get_by_id(kwargs['uid'])
)


SurveyCollection = graphene.Field(
    graphene.List(Survey),
    resolver=lambda root, info: model.Survey.get(order='ordinal',
                                                 n=default_n),
)
