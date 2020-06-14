"""
Dataset
===========

Generic text data files that are associated with parent entities that govern
their ownership.
"""

from google.appengine.api import app_identity
from google.appengine.ext import ndb
import cloudstorage as gcs
import json
import hashlib
import os

from gae_models import StorageObject


class Dataset(StorageObject):
    """Generic text data files."""

    # Anyone owning the parent also owns the dataset. A null parent id means the
    # dataset is only accessible by super admins.
    parent_id = ndb.StringProperty()
    # Makes it easier to query for datasets with no parent.
    has_parent = ndb.ComputedProperty(lambda self: bool(self.parent_id))

    allowed_content_types = {
        'application/json': lambda d: json.dumps(d),
        'text/csv': lambda d: d.encode('utf-8'),
    }

    @classmethod
    def property_types(klass):
        # Tell the api to accept boolean query params for this computed prop.
        types = super(klass, klass).property_types()
        types['has_parent'] = bool
        return types

    @classmethod
    def create(klass, filename, data, content_type, parent_id=None, **kwargs):
        if content_type not in klass.allowed_content_types:
            raise Exception("Forbidden content type: {}".format(content_type))

        ds = super(klass, klass).create(
            filename=filename,
            content_type=content_type,
            parent_id=parent_id,
            **kwargs
        )

        ds.data = data  # will write this to gcs on put; not for datastore

        ds.gcs_path = '/{bucket}{namespace}/{file_hash}'.format(
            bucket=app_identity.get_application_id() + '-datasets',
            namespace=os.environ['GCS_UPLOAD_PREFIX'],
            file_hash=hashlib.md5(Dataset._dumps(ds)).hexdigest(),
        )

        return ds

    @classmethod
    def _dumps(klass, dataset):
        return klass.allowed_content_types[dataset.content_type](dataset.data)

    def before_put(self, *args, **kwargs):
        if not hasattr(self, 'data'):
            # This property only exists immediately after creation. Putting an
            # entity which was loaded from the db won't have it, so do nothing.
            return

        open_kwargs = {
            'content_type': self.content_type,
            'retry_params': gcs.RetryParams(backoff_factor=1.1),
            'options': {
                'Content-Disposition': 'attachment; filename={}'.format(
                    self.filename),
                # Theoretically allows figuring out an attachment history for
                # a given task.
                'x-goog-meta-dataset-id': self.uid,
            }
        }

        with gcs.open(self.gcs_path, 'w', **open_kwargs) as gcs_file:
            gcs_file.write(Dataset._dumps(self))
            # Grab the size so it can be saved on the entity.
            self.size = gcs_file.tell()
