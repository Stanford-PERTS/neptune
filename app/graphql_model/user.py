"""GraphQL User schema."""

import graphene
from graphene_gae import NdbObjectType

from .config import default_n
from gae_models import DatastoreModel, graphql_util
import model

# Example of creating an object with subtypes for a json string field.
# Not being used currently b/c graphql_util.PassthroughScalar seems to work
# fine.

# class NotificationOptionValue(graphene.Enum):
#     yes = "yes"
#     no = "no"


# class NotificationOptionType(graphene.ObjectType):
#     email = NotificationOptionValue()
#     sms = NotificationOptionValue()

#     def resolve_email(self, info):
#         return self.get('email', None)

#     def resolve_sms(self, info):
#         return self.get('sms', None)


class User(NdbObjectType):
    class Meta:
        model = model.User
        interfaces = (graphql_util.DatastoreType, )
        exclude_fields = ['notification_option_json']
        default_resolver = graphql_util.resolve_client_prop

    hashed_password = graphene.Boolean()
    last_login = graphql_util.DatastoreDateTimeScalar()
    # notification_option = graphene.Field(NotificationOptionType)
    notification_option = graphql_util.PassthroughScalar()

    def resolve_hashed_password(self, info):
        # Don't send the true value of hashed password to the client.
        if not getattr(self, '_client_dict', None):
            self._client_dict = self.to_client_dict()
        return self._client_dict['hashed_password']


UserResource = graphene.Field(
    User,
    args={
        'uid': graphene.Argument(graphene.String),
    },
    resolver=lambda root, info, **kwargs: model.User.get_by_id(kwargs['uid'])
)


UserCollection = graphene.Field(
    graphene.List(User),
    resolver=lambda root, info: model.User.get(order='name', n=default_n),
)
