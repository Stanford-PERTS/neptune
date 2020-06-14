"""Test Project entities."""

import datetime
import logging
import unittest

from google.appengine.api import memcache
from unit_test_helper import ConsistencyTestCase
from model import Participant, ParticipantData, SqlModel
import mysql_connection


class TestParticipantData(ConsistencyTestCase):
    """Test features of participant data, backed by MySQL."""

    consistency_probability = 0

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestParticipantData, self).set_up()
        with mysql_connection.connect() as sql:
            sql.reset({
                'participant_data': ParticipantData.get_table_definition(),
            })

    def test_create_portal_pd(self, testing=False):
        """Set all the pd potentially required by the portal."""
        # Using the same project and project cohort ids from the mock function.
        context_params = {
            'participant_id': 'Participant_0123456789ABCDEF',
            'program_label': 'demo-program',
            'project_id': 'Project_12345678',
            'cohort_label': '2017_spring',
            'project_cohort_id': 'ProjectCohort_12345678',
            'code': 'trout viper',
            'testing': testing,
        }
        portal_pd = [
            {
                'key': 'link',
                'value': '',
                'survey_id': 'Survey_1',
                'survey_ordinal': 1,
            },
            {
                'key': 'progress',
                'value': '100',
                'survey_id': 'Survey_1',
                'survey_ordinal': 1,
            },
            {
                'key': 'link',
                'value': '',
                'survey_id': 'Survey_2',
                'survey_ordinal': 2,
            },
            {
                'key': 'progress',
                'value': '33',
                'survey_id': 'Survey_2',
                'survey_ordinal': 2,
            },
            {
                'key': 'consent',
                'value': 'true',
                'survey_id': None,
            },
            {
                'key': 'condition',
                'value': 'treatment',
                'survey_id': None,
            },
        ]
        portal_pd = [ParticipantData.create(**dict(pd, **context_params))
                     for pd in portal_pd]
        ParticipantData.put_multi(portal_pd)

        # Save one more in a different project cohort, since participants
        # have an identity at the organization level.
        other_pc_params = dict(
            context_params,
            project_cohort_id='ProjectCohort_other',
            code='other octopus',
            key='saw_validation',  # N.B. this is whitelisted
            value='bar',
            survey_id='Survey_other',
        )
        ParticipantData.create(**other_pc_params).put()

        return context_params['participant_id']

    def test_get_by_project_cohort(self):
        """Retrieve pd for a participant, for a given pc."""
        # A new participant should have no pd.
        new_pid = 'Participant_new'
        results = ParticipantData.get_by_participant(
            new_pid, 'ProjectCohort_12345678')
        self.assertEqual(len(results), 0)

        # An existing participant should have some pd.
        pid = self.test_create_portal_pd()
        results = ParticipantData.get_by_participant(
            pid, 'ProjectCohort_12345678')
        self.assertGreater(len(results), 0)

        # All returned pd should match the project cohort id.
        self.assertTrue(all(
            pd.project_cohort_id == 'ProjectCohort_12345678' for pd in results
        ))

    def test_get_portal_pd(self):
        """The same query made by the portal client, not scoped to pc."""
        # A new participant should have no pd.
        new_pid = 'Participant_new'
        results = ParticipantData.get_by_participant(new_pid)
        self.assertEqual(len(results), 0)

        # An existing participant should have some pd.
        pid = self.test_create_portal_pd()
        results = ParticipantData.get_by_participant(pid)
        self.assertGreater(len(results), 0)

        # Some returned pd should be from other pcs.
        self.assertFalse(all(
            pd.project_cohort_id == 'ProjectCohort_12345678' for pd in results
        ))

    def test_portal_pd_includes_testing(self):
        """A testing user should still have a normal portal experience."""
        # A testing participant should have some pd.
        pid = self.test_create_portal_pd(testing=True)
        results = ParticipantData.get_by_participant(
            pid, 'ProjectCohort_12345678')
        self.assertGreater(len(results), 0)

    def test_pd_whitelist(self):
        """Any pd keys other than those whitelisted should not be returned."""
        pid = 'Participant_0123456789ABCDEF'
        context_params = {
            'participant_id': pid,
            'program_label': 'demo-program',
            'project_id': 'Project_12345678',
            'code': 'trout viper',
            'cohort_label': '2017_spring',
            'project_cohort_id': 'ProjectCohort_12345678',
            'survey_id': 'Survey_12345678',
        }
        portal_pd = [
            {
                'key': 'link',  # whitelisted
                'value': '',
            },
            {
                'key': 'not_whitelisted',
                'value': 'secret',
            },
        ]
        portal_pd = [ParticipantData.create(**dict(pd, **context_params))
                     for pd in portal_pd]
        ParticipantData.put_multi(portal_pd)

        results = ParticipantData.get_by_participant(
            pid, 'ProjectCohort_12345678')
        self.assertEqual(len(results), 1)
        self.assertNotEqual(results[0].value, 'secret')

    def test_survey_participation(self):
        pid = self.test_create_portal_pd()
        results = ParticipantData.participation(survey_id='Survey_1')
        expected = {'survey_ordinal': 1, 'value': '100', 'n': 1}
        self.assertEqual(results[0], expected)

    def test_project_cohort_participation(self):
        pid = self.test_create_portal_pd()
        results = ParticipantData.participation(
            project_cohort_id='ProjectCohort_12345678')
        expected = [
            {'survey_ordinal': 1, 'value': '100', 'n': 1},
            {'survey_ordinal': 2, 'value': '33', 'n': 1},
        ]
        self.assertEqual(results, expected)

    def test_counts_exclude_testing(self):
        """Aggregated counts should ignore testing pd."""
        pid = self.test_create_portal_pd(testing=True)
        results = ParticipantData.participation(survey_id='Survey_1')
        self.assertEqual(results, [])

    def test_completion_ids(self):
        pid = self.test_create_portal_pd()
        participant = Participant.create(
            id=SqlModel.convert_uid(pid),
            name='Pascal',
            organization_id='Organization_PERTS',
        )
        participant.put()
        results = ParticipantData.completion_ids(
            project_cohort_id='ProjectCohort_12345678')
        expected = [
            {'module': 1, 'percent_progress': '100', 'token': 'Pascal'},
            {'module': 2, 'percent_progress': '33', 'token': 'Pascal'},
        ]
        self.assertEqual(results, expected)

    def test_completion_ids_exclude_testing(self):
        """Don't count testing pd as that participant being done."""
        pid = self.test_create_portal_pd(testing=True)
        participant = Participant.create(
            id=SqlModel.convert_uid(pid),
            name='Pascal',
            organization_id='Organization_PERTS',
        )
        participant.put()
        results = ParticipantData.completion_ids(
            project_cohort_id='ProjectCohort_12345678')
        self.assertEqual(results, [])

    def test_put_clears_cache(self):
        pc_id = 'ProjectCohort_foo'
        survey_id = 'Survey_foo'
        code = 'foo bar'

        start1 = datetime.datetime.today()
        end1   = start1 + datetime.timedelta(days=1)
        start2 = start1 + datetime.timedelta(days=2)
        end2   = start1 + datetime.timedelta(days=3)

        cache_data = {
            ParticipantData.participation_cache_key(pc_id): {
                ParticipantData.date_key(start1, end1): ['result1'],
                ParticipantData.date_key(start2, end2): ['result2'],
            },
            ParticipantData.participation_cache_key(survey_id): {
                ParticipantData.date_key(start1, end1): ['result1'],
                ParticipantData.date_key(start2, end2): ['result2'],
            },
            ParticipantData.participation_by_pc_cache_key(pc_id): {
                ParticipantData.date_key(start1, end1): ['result1'],
                ParticipantData.date_key(start2, end2): ['result2'],
            },
            ParticipantData.participation_by_pc_cache_key(code): {
                ParticipantData.date_key(start1, end1): ['result1'],
                ParticipantData.date_key(start2, end2): ['result2'],
            },
        }
        memcache.set_multi(cache_data)

        # Write a pd that relates to the pc and survey, falling in the first
        # date range. That date range should clear, the other should remain.
        pd = ParticipantData.create(
            key='progress',
            value=1,
            participant_id='Participant_foo',
            program_label='demo-program',
            project_id='Project_foo',
            cohort_label='2019',
            project_cohort_id=pc_id,
            code=code,
            survey_id=survey_id,
            survey_ordinal=1,
        )
        ParticipantData.put_for_index(pd, 'participant-survey-key')

        for cache_key in cache_data.keys():
            self.assertEqual(len(memcache.get(cache_key)), 1)

    def test_cache_truncation(self):
        big_cache_value = {
          '2019-01-01T00:00:00{}'.format(x): 'foo'
          for x in range(1001)
        }
        truncated = ParticipantData.truncate_cached(big_cache_value)
        self.assertEqual(len(truncated), 100)

