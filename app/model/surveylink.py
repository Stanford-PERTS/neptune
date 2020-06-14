"""SurveyLink: A URL to a survey that is unique to a participant."""

from google.appengine.api import app_identity
from google.appengine.ext import ndb
import csv
import logging

from .program import Program
import cloudstorage as gcs


class SurveyLink(ndb.Model):
    # The key name / entity id _is_ the url. We assume that Qualtrics "unique
    # links" are globally unique.
    program_label = ndb.StringProperty()
    survey_ordinal = ndb.IntegerProperty()
    url = ndb.ComputedProperty(lambda self: self.key.id())

    @classmethod
    def import_path(klass, program_label, survey_ordinal, file_name=None):
        bucket = app_identity.get_application_id() + '-import-links'
        path = '/{bucket}/{program_label}/{survey_ordinal}/'.format(
            bucket=bucket, program_label=program_label,
            survey_ordinal=survey_ordinal
        )
        if file_name:
            path += file_name
        return path

    @classmethod
    def list_gcs_files(klass, program_label, survey_ordinal, file_name=None):
        prefix = klass.import_path(program_label, survey_ordinal, file_name)
        return [x.filename for x in gcs.listbucket(path_prefix=prefix)]

    @classmethod
    def import_links(klass, program_label, survey_ordinal, file_name):
        """Generate SurveyLink entities based on a csv file in cloud storage.

        Needs to be able to work with large file sizes (100k rows).
        """
        num_imported = 0
        batch_size = 100  # to reduce RPCs
        link_batch = []

        paths = klass.list_gcs_files(program_label, survey_ordinal, file_name)
        for path in paths:
            with gcs.open(path, 'r') as fh:
                csv_reader = csv.DictReader(fh)
                # `row` garbage collected with each loop.
                for row in csv_reader:
                    link = SurveyLink(
                        id=row['Link'],
                        program_label=program_label,
                        survey_ordinal=survey_ordinal,
                    )
                    link_batch.append(link)

                    # Save the batch.
                    if len(link_batch) == batch_size:
                        ndb.put_multi(link_batch)
                        num_imported += len(link_batch)
                        # `link_batch` garbage collected every 100 loops.
                        link_batch = []

        # If there's a partially-full batch, save that too.
        if len(link_batch) > 0:
            ndb.put_multi(link_batch)
            num_imported += len(link_batch)

        return num_imported

    @classmethod
    def get_unique(klass, program_label, survey_ordinal):
        """Get a SurveyLink which will never be issued to anyone else.

        Args:
            program_label str
            survey_ordinal int

        Returns:
            A SurveyLink entity that is guaranteed to have been just deleted,
            or None if no SurveyLink entities could be found.
        """
        real_link = None
        tries = 0

        while not real_link and tries < 50:
            # Get a link with eventual consistency (b/c we don't have an id).
            query = klass.query(SurveyLink.program_label == program_label,
                                SurveyLink.survey_ordinal == survey_ordinal)
            possible_link = query.get()
            tries += 1

            # The link might not really exist. Check with strong consistency.
            if possible_link:
                real_link = possible_link.datastore_pop()  # might return None

        return real_link if real_link else None

    @ndb.transactional
    def datastore_pop(self):
        """Ensure entity exists, then delete it, atomically.

        Wrapping in a transaction means no race condition between verifying
        that the entity does, in fact, exist, and deleting it.
        """
        entity = self.key.get()
        if entity:
            self.key.delete()
            return self
        else:
            return None

    def to_client_dict(self):
        return {'url': self.url, 'program_label': self.program_label,
                'survey_ordinal': self.survey_ordinal}
