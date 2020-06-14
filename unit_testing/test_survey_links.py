"""Test SurveyLink entities and their interaction with cloud storage."""

import cloudstorage as gcs
import logging
import random
import string

from unit_test_helper import ConsistencyTestCase
from model import SurveyLink


def generate_csv_content(num_links):
    """Mock the contents of a Qualtrics unique link csv file.

    Args:
        num_links: int how many rows other than the header to generate

    Returns:
        a tuple with
        * the file contents as a string
        * a list of the unique link urls, in the same order as the csv rows
    """
    csv_rows = [
        '"Response ID","Last Name","First Name","External Data Reference","Email","Status","End Date","Link","Link Expiration"'
    ]
    # Based on unique link csv export as of 2017-02-21.
    link_row_template = (
        '"","","","","{rnd_str}@{rnd_str}.com","Email Not Sent Yet","",'
        '"{url}","2050-02-16 16:10:00"'
    )
    url_template = (
        'https://sshs.qualtrics.com/SE?'
        'Q_DL={rnd_str}_{rnd_str}_MLRP_{rnd_str}&Q_CHL=gl'
    )
    urls = []
    for x in range(num_links):
        rnd_str = ''.join(random.choice(string.ascii_lowercase)
                          for x in range(10))
        url = url_template.format(rnd_str=rnd_str)
        row_str = link_row_template.format(rnd_str=rnd_str, url=url)
        csv_rows.append(row_str)
        urls.append(url)
    content = "\n".join(csv_rows)
    return (content, urls)


class TestSurveyLinksInconsistent(ConsistencyTestCase):
    """Survey link queries behave correctly under eventual consistency."""

    consistency_probability = 0

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestSurveyLinksInconsistent, self).set_up()

        # Needed for gcs interaction.
        self.testbed.init_app_identity_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_blobstore_stub()

    def test_create_links(self):
        """Can import a csv from cloud storage."""
        program_label = 'demo-program'
        content, urls = generate_csv_content(101)
        path = SurveyLink.import_path(program_label, 1, 'links.csv')
        with gcs.open(path, 'w') as fh:
            # Choose 101 to prove that we can 1) do more than a single batch of
            # 100 and 2) do a partial batch (the last one).
            fh.write(content)
        num_imported = SurveyLink.import_links(program_label, 1, 'links.csv')

        self.assertEqual(num_imported, 101)

        gcs.delete(path)

    def test_get_unique(self):
        """Impossible for the same link to be assigned twice."""
        kwargs = {'program_label': 'demo-program', 'survey_ordinal': 1}
        link1 = SurveyLink(id='foo', **kwargs)
        link2 = SurveyLink(id='bar', **kwargs)
        link1.put()
        link2.put()

        # Get each to sync up the datastore.
        link1.key.get()
        link2.key.get()

        # Delete one to try to trick the datastore.
        link1.key.delete()

        # Getting one should return 'bar' (but maybe not find any?).
        linkA_fetched = SurveyLink.get_unique('demo-program', 1)
        logging.info(linkA_fetched)
        self.assertNotEqual(linkA_fetched.url, link1.url)

        # Getting a second should definitely return None.
        linkB_fetched = SurveyLink.get_unique('demo-program', 1)
        logging.info(linkB_fetched)
        self.assertIsNone(linkB_fetched)

    def test_scoping(self):
        """Links for different sessions and programs shouldn't cross."""
        link1 = SurveyLink(id='foo1', program_label='foo', survey_ordinal=1)
        link2 = SurveyLink(id='foo2', program_label='foo', survey_ordinal=2)
        link3 = SurveyLink(id='bar1', program_label='bar', survey_ordinal=1)
        link1.put()
        link2.put()
        link3.put()

        # Get each to sync up the datastore.
        link1.key.get()
        link2.key.get()
        link3.key.get()

        self.assertEqual(SurveyLink.get_unique('foo', 1).url, link1.url)
        self.assertEqual(SurveyLink.get_unique('foo', 2).url, link2.url)
        self.assertEqual(SurveyLink.get_unique('bar', 1).url, link3.url)


class TestSurveyLinksConsistent(ConsistencyTestCase):
    """Survey link queries don't show duplicates."""

    # To know that there are no duplicate SurveyLink entities in the datastore,
    # we need to list all of them. The only way to do that is with a
    # consistent stub.
    consistency_probability = 1

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestSurveyLinksConsistent, self).set_up()

        # Needed for gcs interaction.
        self.testbed.init_app_identity_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_blobstore_stub()

    def test_duplicate_links_overwrite(self):
        """Importing links should be idempotent."""
        program_label = 'demo-program'
        content, urls = generate_csv_content(101)
        path = SurveyLink.import_path(program_label, 1, 'links.csv')
        with gcs.open(path, 'w') as fh:
            fh.write(content)

        # Import the same csv twice.
        SurveyLink.import_links(program_label, 1, 'links.csv')
        SurveyLink.import_links(program_label, 1, 'links.csv')

        # Still only 101.
        keys = [k for k in SurveyLink.query().iter(keys_only=True)]
        self.assertEqual(len(keys), 101)

        gcs.delete(path)
