"""DataRequest: Invitation to upload specific data through the Data Wizard."""

from google.appengine.ext import ndb
import json

from gae_models import DatastoreModel
import util


class DataRequest(DatastoreModel):
    # Email of user being invited.
    # N.B. This is an email address and not a user id because the recipient
    # may not have an account yet!
    email = ndb.StringProperty()
    title = ndb.StringProperty()
    description = ndb.TextProperty()
    column_ids = ndb.StringProperty(repeated=True)  # data being requested

    @property
    def link(self):
        return '/wizard/data_requests/{}'.format(self.short_uid)

    # Sets of allowed index columns. For example, for course data:
    # [
    #   ["student", "course"],
    #   ["student", "course", "term"]
    # ]
    index_ids_json = ndb.TextProperty(default=r'{}')

    # Affects property_types() and to_client_dict().
    json_props = ['index_ids_json']

    @property
    def index_ids(self):
        return (json.loads(self.index_ids_json)
                if self.index_ids_json else None)

    @index_ids.setter
    def index_ids(self, obj):
        self.index_ids_json = json.dumps(obj)
        return obj
