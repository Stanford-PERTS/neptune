"""Test Project entities."""

import datetime
import logging
import unittest

from unit_test_helper import ConsistencyTestCase
from model import (Participant, ParticipantData, ProjectCohort, Survey)
import mysql_connection


def mock_one_finished_one_unfinished(
    survey_ordinal, unfinished_id, finished_id, pc_id='ProjectCohort_foo',
    code='cool cat', program_label=None, cohort_label=None,
    organization_id=None):
    """Simulating one who finished and one who didn't."""
    survey = Survey.create(
        [],
        ordinal=survey_ordinal,
        program_label=program_label,
        organization_id=organization_id or 'Org_foo',
    )
    survey.put()
    kwargs = {
        'key': 'progress',
        'program_label': program_label,
        'project_id': 'Project_12345678',
        'cohort_label': cohort_label or cohort_label,
        'project_cohort_id': pc_id,
        'code': code,
        'survey_id': survey.uid,
        'survey_ordinal': survey.ordinal,
    }

    pd1 = ParticipantData.create(participant_id=unfinished_id,
                                 value=1, **kwargs)
    pd2 = ParticipantData.create(participant_id=finished_id,
                                 value=1, **kwargs)
    pd3 = ParticipantData.create(participant_id=finished_id,
                                 value=100, **kwargs)

    return [
        ParticipantData.put_for_index(pd1, 'participant-survey-key'),
        ParticipantData.put_for_index(pd2, 'participant-survey-key'),
        # Writing this third one should should update the second, so the third
        # uid will never get to the db.
        ParticipantData.put_for_index(pd3, 'participant-survey-key'),
    ]


class TestParticipation(ConsistencyTestCase):
    """Test features of participation queries, backed by MySQL."""

    consistency_probability = 0

    program_label = 'demo-program'
    cohort_label = '2017_spring'

    unfinished_id = 'Participant_unfinished'
    finished_id = 'Participant_finished'

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestParticipation, self).set_up()
        with mysql_connection.connect() as sql:
            sql.reset({
                'participant': Participant.get_table_definition(),
                'participant_data': ParticipantData.get_table_definition(),
            })

    def mock_participants(self):
        unfinished_id = Participant.convert_uid(self.unfinished_id)
        finished_id = Participant.convert_uid(self.finished_id)
        participants = [
            Participant.create(id=unfinished_id, name='unfinished',
                               organization_id='Org_foo'),
            Participant.create(id=finished_id, name='finished',
                               organization_id='Org_foo'),
        ]
        Participant.put_multi(participants)
        return participants

    def mock_one_finished_one_unfinished(
        self, survey_ordinal, pc_id='ProjectCohort_foo', cohort_label=None):
        """Simulating one who finished and one who didn't."""
        return mock_one_finished_one_unfinished(
            survey_ordinal,
            self.unfinished_id,
            self.finished_id,
            pc_id=pc_id,
            program_label=self.program_label,
            cohort_label=cohort_label or self.cohort_label,
        )

    def test_get_participant_by_id(self):
        p = Participant.create(
            name='f7fbba6e0636f890e56fbbf3283e524c6fa3204ae298382d624741d0dc6638326e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7',
            organization_id='Organization_12345678',
        )
        p.put()
        fetched_p = Participant.get_by_id(p.uid)
        # Test that hashes up to 128 characters will fit.
        self.assertEqual(fetched_p.name, p.name)

    def test_get_survey_participation(self):
        """Get count of particpants at each marker."""
        pds = self.mock_one_finished_one_unfinished(1)
        survey_id = pds[0].survey_id
        start = datetime.date.today()
        end = start + datetime.timedelta(days=1)
        result = ParticipantData.participation(
            survey_id=survey_id, start=start, end=end)
        expected = [
            {'value': '1', 'n': 1, 'survey_ordinal': 1},
            {'value': '100', 'n': 1, 'survey_ordinal': 1},
        ]
        self.assertEqual(result, expected)

        # The same result should also now be available in memcache, so if we
        # clear the db the result should be the same.
        ParticipantData.delete_multi(pds)
        result = ParticipantData.participation(
            survey_id=survey_id, start=start, end=end)
        self.assertEqual(result, expected)

    def test_nobody_done(self):
        """If no one finished the survey, counts are zero."""
        survey = Survey.create([], ordinal=1, program_label=self.program_label)
        survey.put()
        kwargs = {
            'key': 'progress',
            'program_label': self.program_label,
            'project_id': 'Project_12345678',
            'cohort_label': '2017_spring',
            'project_cohort_id': 'ProjectCohort_12345678',
            'code': 'trout viper',
            'survey_id': survey.uid,
            'survey_ordinal': survey.ordinal,
        }

        pd = [
            ParticipantData.create(participant_id='Participant_unfinished1',
                                   value=1, **kwargs),
            ParticipantData.create(participant_id='Participant_unfinished2',
                                   value=1, **kwargs),
        ]
        ParticipantData.put_multi(pd)

        result = ParticipantData.participation(survey_id=pd[0].survey_id)
        expected = [
            {'value': '1', 'n': 2, 'survey_ordinal': 1},
        ]

        self.assertEqual(result, expected)

    def test_get_project_cohort_participation(self):
        """Get stats for all surveys in the project cohort."""
        pds1 = self.mock_one_finished_one_unfinished(1)
        pds2 = self.mock_one_finished_one_unfinished(2)
        project_cohort_id = pds1[0].project_cohort_id
        ProjectCohort(
            id=project_cohort_id,
            program_label=self.program_label,
        ).put()
        start = datetime.date.today()
        end = start + datetime.timedelta(days=1)

        expected = [
            {'value': '1', 'n': 1, 'survey_ordinal': 1},
            {'value': '100', 'n': 1, 'survey_ordinal': 1},
            {'value': '1', 'n': 1, 'survey_ordinal': 2},
            {'value': '100', 'n': 1, 'survey_ordinal': 2},
        ]

        result = ParticipantData.participation(
            project_cohort_id=project_cohort_id, start=start, end=end)
        self.assertEqual(result, expected)

        # The same result should also now be available in memcache, so if we
        # clear the db the result should be the same.
        ParticipantData.delete_multi(pds1 + pds2)
        result = ParticipantData.participation(
            project_cohort_id=project_cohort_id, start=start, end=end)
        self.assertEqual(result, expected)

        # It should also work if some other kwargs are set with value None.
        result = ParticipantData.participation(
            project_cohort_id=project_cohort_id, start=start, end=end,
            cohort_label=None)
        self.assertEqual(result, expected)

    def test_get_cohort_participation(self):
        """Get stats for all surveys in a cohort."""
        pc_id1 = 'ProjectCohort_one'
        pc_id2 = 'ProjectCohort_two'
        pds11 = self.mock_one_finished_one_unfinished(1, pc_id=pc_id1)
        pds12 = self.mock_one_finished_one_unfinished(2, pc_id=pc_id1)
        pds21 = self.mock_one_finished_one_unfinished(1, pc_id=pc_id2)
        pds22 = self.mock_one_finished_one_unfinished(2, pc_id=pc_id2)

        expected = [
            {'value': '1', 'n': 2, 'survey_ordinal': 1},
            {'value': '100', 'n': 2, 'survey_ordinal': 1},
            {'value': '1', 'n': 2, 'survey_ordinal': 2},
            {'value': '100', 'n': 2, 'survey_ordinal': 2},
        ]

        stats = ParticipantData.participation(program_label=self.program_label,
                                              cohort_label=self.cohort_label)
        self.assertEqual(stats, expected)

    def test_get_program_participation(self):
        """Get stats for all surveys in a cohort."""
        cohort1 = 'fall'
        cohort2 = 'spring'
        pds1 = self.mock_one_finished_one_unfinished(1, cohort_label=cohort1)
        pds2 = self.mock_one_finished_one_unfinished(1, cohort_label=cohort2)

        expected = [
            {'complete': 1, 'survey_ordinal': 1, 'cohort_label': cohort1},
            {'complete': 1, 'survey_ordinal': 1, 'cohort_label': cohort2},
        ]

        stats = ParticipantData.completion_by_cohort(self.program_label)

        self.assertEqual(stats, expected)

    def test_get_survey_completion_ids(self):
        participants = {p.uid: p for p in self.mock_participants()}
        pds = self.mock_one_finished_one_unfinished(1)
        result = ParticipantData.completion_ids(survey_id=pds[0].survey_id)

        expected = [
            {'token': 'unfinished', 'percent_progress': '1', 'module': 1},
            {'token': 'finished', 'percent_progress': '100', 'module': 1},
        ]

        self.assertEqual(result, expected)

    def test_get_project_cohort_completion_ids(self):
        participants = {p.uid: p for p in self.mock_participants()}
        pds1 = self.mock_one_finished_one_unfinished(1)
        pds2 = self.mock_one_finished_one_unfinished(2)
        ProjectCohort(
            id=pds1[0].project_cohort_id,
            program_label=self.program_label,
        ).put()

        result = ParticipantData.completion_ids(
            project_cohort_id=pds1[0].project_cohort_id)

        expected = [
            {'token': 'unfinished', 'percent_progress': '1', 'module': 1},
            {'token': 'finished', 'percent_progress': '100', 'module': 1},
            {'token': 'unfinished', 'percent_progress': '1', 'module': 2},
            {'token': 'finished', 'percent_progress': '100', 'module': 2},
        ]

        self.assertEqual(result, expected)
