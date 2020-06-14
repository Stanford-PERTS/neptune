"""Test Project entities."""

from MySQLdb import IntegrityError
import logging
import unittest

from unit_test_helper import ConsistencyTestCase
from model import Checkpoint, Program, Project, ParticipantData
import mysql_connection


class TestSqlModel(ConsistencyTestCase):
    """Test general features of MySQL-backed objects."""

    consistency_probability = 0

    context_params = {
        'cohort_label': '2017_spring',
        'key': 'progress',
        'participant_id': 'Participant_0123456789ABCDEF',
        'program_label': 'demo-program',
        'project_cohort_id': 'ProjectCohort_12345678',
        'code': 'trout viper',
        'project_id': 'Project_12345678',
        'survey_id': 'Survey_1',
        'survey_ordinal': 1,
    }

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestSqlModel, self).set_up()
        with mysql_connection.connect() as sql:
            sql.reset({
                'checkpoint': Checkpoint.get_table_definition(),
                'participant_data': ParticipantData.get_table_definition(),
            })

    def tearDown(self):
        Program.reset_mocks()
        super(TestSqlModel, self).tearDown()

    def test_get_checkpoint_by_id(self):
        project = Project.create(program_label='demo-program',
                                 organization_id='Organization_Foo')
        project.put()
        checkpoints = Checkpoint.get(parent_id=project.uid)
        self.assertIsNotNone(Checkpoint.get_by_id(checkpoints[0].uid))

    def test_select_checkpoints_with_offset(self):
        """Can use queries like "LIMIT 20,10" to get "pages" of records."""

        # Create two checkpoints.
        program_label = 'demo-program'
        Program.mock_program_config(program_label, {
            'project_tasklist_template': [
                {'name': 'Foo', 'label': 'checkpoint_foo', 'tasks': []},
                {'name': 'Bar', 'label': 'checkpoint_bar', 'tasks': []},
            ]
        })
        project = Project.create(program_label=program_label,
                                 organization_id='Organization_Foo')
        project.put()

        # Select each of the two checkpoints in different queries with one-row
        # pages.
        r1 = Checkpoint.get(program_label=program_label, n=1, offset=0)
        r2 = Checkpoint.get(program_label=program_label, n=1, offset=1)
        self.assertNotEqual(r1[0].uid, r2[0].uid)

    def test_update_checkpoint(self):
        project = Project.create(program_label='demo-program',
                                 organization_id='Organization_Foo')
        project.put()
        checkpoint = Checkpoint.get(parent_id=project.uid)[0]
        checkpoint.name = 'foo'
        checkpoint.put()
        fetched = Checkpoint.get_by_id(checkpoint.uid)
        self.assertEqual(fetched.name, 'foo')

    def test_put_insert(self):
        """put() a new uid: succeeds."""
        params = dict(self.context_params, value='1')
        pd = ParticipantData.create(**params)
        pd.put()

        # Db shows saved values, and db-provided defaults like timestamps
        # are present in the saved object.
        fetched = ParticipantData.get_by_id(pd.uid)
        self.assertEqual(pd.to_dict(), fetched.to_dict())

    def test_put_insert_duplicate(self):
        """put() a new uid but matching an index: raises."""
        params = dict(self.context_params, value='1')
        pd = ParticipantData.create(**params)
        pd.put()

        dupe_params = dict(self.context_params, value='2')
        dupe_pd = ParticipantData.create(**params)

        with self.assertRaises(IntegrityError):
            dupe_pd.put()

    def test_put_update(self):
        """put() an exisiting uid: succeeds."""
        params = dict(self.context_params, value='1')
        pd = ParticipantData.create(**params)
        pd.put()

        pd.value = '2'
        pd.put()

        # Db shows values.
        fetched = ParticipantData.get_by_id(pd.uid)
        self.assertEqual(pd.to_dict(), fetched.to_dict())

    def test_put_update_duplicate(self):
        """put() an existing uid but matching an index: raises."""
        params1 = dict(self.context_params, value='1', survey_id='Survey_1')
        pd1 = ParticipantData.create(**params1)
        pd1.put()

        params2 = dict(self.context_params, value='1', survey_id='Survey_2')
        pd2 = ParticipantData.create(**params2)
        pd2.put()


        with self.assertRaises(IntegrityError):
            # Now changing 1 so that it collides with 2.
            pd1.survey_id = 'Survey_2'
            pd1.put()

    def test_put_for_index_insert(self):
        """put_for_index() a new uid: succeeds."""
        params = dict(self.context_params, value='1')
        pd = ParticipantData.create(**params)
        synced_pd = ParticipantData.put_for_index(pd, 'participant-survey-key')

        # Returns same uid.
        self.assertEqual(pd.uid, synced_pd.uid)

        # Db shows values.
        fetched = ParticipantData.get_by_id(pd.uid)
        self.assertEqual(synced_pd.to_dict(), fetched.to_dict())

    def test_put_for_index_insert_duplicate(self):
        """put_for_index() a new uid but matching an index: succeeds."""
        params = dict(self.context_params, value='1')
        pd = ParticipantData.create(**params)
        pd.put()

        dupe_params = dict(self.context_params, value='2')
        dupe_pd = ParticipantData.create(**params)

        synced_pd = ParticipantData.put_for_index(dupe_pd, 'participant-survey-key')

        # Returns original uid, not the new one.
        self.assertEqual(synced_pd.uid, pd.uid)

        # Db shows values
        fetched = ParticipantData.get_by_id(pd.uid)
        self.assertEqual(synced_pd.to_dict(), fetched.to_dict())

    def test_put_for_index_update(self):
        """put_for_index() an exisiting uid: succeeds."""
        params = dict(self.context_params, value='1')
        pd = ParticipantData.create(**params)
        pd.put()

        pd.value = '2'
        synced_pd = ParticipantData.put_for_index(pd, 'participant-survey-key')

        # Returns same uid.
        self.assertEqual(synced_pd.uid, pd.uid)

        # Db shows values.
        fetched = ParticipantData.get_by_id(pd.uid)
        self.assertEqual(synced_pd.to_dict(), fetched.to_dict())

    def test_put_for_index_update_duplicate(self):
        """put_for_index() existing uid but matches an index raises."""
        params1 = dict(self.context_params, value='1', survey_id='Survey_1')
        pd1 = ParticipantData.create(**params1)
        pd1.put()

        params2 = dict(self.context_params, value='1', survey_id='Survey_2')
        pd2 = ParticipantData.create(**params2)
        pd2.put()


        with self.assertRaises(IntegrityError):
            # Now changing 1 so that it collides with 2.
            pd1.survey_id = 'Survey_2'
            synced_pd1 = ParticipantData.put_for_index(
                pd1, 'participant-survey-key')

    def test_delete_returns_affected_rows(self):
        params = dict(self.context_params, value='1')
        pd = ParticipantData.create(**params)
        ParticipantData.put(pd)
        affected_rows = ParticipantData.delete_multi([pd])
        self.assertEqual(affected_rows, 1)

    def test_put_multi(self):
        """If no indexes collide: succeeds, otherwise: raises."""
        params1 = dict(self.context_params, value='1', survey_id='Survey_1')
        pd1 = ParticipantData.create(**params1)

        params2 = dict(self.context_params, value='1', survey_id='Survey_2')
        pd2 = ParticipantData.create(**params2)

        affected_rows = ParticipantData.put_multi([pd1, pd2])

        self.assertEqual(affected_rows, 2)

        self.assertIsNotNone(ParticipantData.get_by_id(pd1.uid))
        self.assertIsNotNone(ParticipantData.get_by_id(pd2.uid))

        pd3 = ParticipantData.create(**params1)

        with self.assertRaises(IntegrityError):
            ParticipantData.put_multi([pd3])
