"""
DataTable
===========

Metadata for csv tables uploaded into or created by the Data Wizard. Also
tracks user's decisions on how to clean up uploaded data.
"""

from google.appengine.ext import ndb
import json

from gae_models import StorageObject
import util


class DataTable(StorageObject):
    """Metadata for csv tables saved by the Data Wizard."""

    # School associated with the data.
    organization_id = ndb.StringProperty()
    # Column names defining a unique index.
    index_columns = ndb.StringProperty(repeated=True)
    num_rows = ndb.IntegerProperty(default=0)

    wizard_step = ndb.StringProperty(default='select_indices')

    # Which radio option user chose for indexing the table.
    index_choice = ndb.StringProperty()  # e.g. 'student-term-course'

    # How their column names map to ours. Json string with structure
    # {theirIdName: "student_id", ... }
    column_map_json = ndb.TextProperty(default=r'{}')

    # Which radio option user chose for reviewing duplicates or not,
    # and if they chose to review, which specific rows to drop.
    should_review_duplicate_rows = ndb.BooleanProperty(default=False)
    should_review_duplicate_indices = ndb.BooleanProperty(default=False)
    row_duplicates = ndb.IntegerProperty(repeated=True)
    row_drops = ndb.IntegerProperty(repeated=True)

    # How their values map to ours in enumerated columns. Json with structure
    # {"gender": {"male": "M", ... }, ... }
    value_maps_json = ndb.TextProperty(default=r'{}')

    # How to change non-conforming values in columns with required syntax.
    # Json with structure {"graduation_data": {"5": "2016-02-29", ...} ...}
    value_replacements_json = ndb.TextProperty(default=r'{}')

    net_rows = ndb.ComputedProperty(
        lambda s: s.num_rows - (len(s.row_drops) if s.row_drops else 0))

    # If True, represents the cleaned output of the Data Wizard. Shares user
    # and filename with raw original table.
    finalized = ndb.BooleanProperty(default=False)
    # Only used if finalized is True, id of the raw, as-uploaded DataTable this
    # came from.
    raw_table_id = ndb.StringProperty()

    # Affects property_types() and to_client_dict().
    json_props = ['column_map_json', 'value_maps_json',
                  'value_replacements_json']

    @property
    def column_map(self):
        return (json.loads(self.column_map_json)
                if self.column_map_json else None)

    @column_map.setter
    def column_map(self, obj):
        self.column_map_json = json.dumps(obj)
        return obj

    @property
    def value_maps(self):
        return (json.loads(self.value_maps_json)
                if self.value_maps_json else None)

    @value_maps.setter
    def value_maps(self, obj):
        self.value_maps_json = json.dumps(obj)
        return obj

    @property
    def value_replacements(self):
        return (json.loads(self.value_replacements_json)
                if self.value_replacements_json else None)

    @value_replacements.setter
    def value_replacements(self, obj):
        self.value_replacements_json = json.dumps(obj)
        return obj
