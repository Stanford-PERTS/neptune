"""GraphQL Organization schema."""

import graphene
from graphene_gae import NdbObjectType

from .config import default_n
from .user import User
from gae_models import DatastoreModel, graphql_util
import model


class Organization(NdbObjectType):
    class Meta:
        model = model.Organization
        interfaces = (graphql_util.DatastoreType, )
        exclude_fields = []
        default_resolver = graphql_util.resolve_client_prop

    liaison = graphene.Field(User)

    users = graphene.List(User)

    poid = graphql_util.PassthroughScalar()

    def resolve_liaison(self, info):
        return model.User.get_by_id(self.liaison_id)

    def resolve_users(self, info):
        return model.User.get(
            owned_organizations=self.uid,
            order='email',
            n=default_n,
        )


OrganizationResource = graphene.Field(
    Organization,
    args={
        'uid': graphene.Argument(graphene.String),
    },
    resolver=lambda root, info, **kwargs: model.Organization.get_by_id(
        kwargs['uid'],
    )
)


OrganizationCollection = graphene.Field(
    graphene.List(Organization),
    resolver=lambda root, info: model.Organization.get(order='name',
                                                       n=default_n),
)
