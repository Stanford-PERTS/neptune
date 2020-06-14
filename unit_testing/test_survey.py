"""Test Survey entities."""

from google.appengine.api import memcache
from unit_test_helper import ConsistencyTestCase
from model import Checkpoint, Program, ProjectCohort, Survey, Task
import logging
import mysql_connection
import util


class TestSurvey(ConsistencyTestCase):
    """Test features of survey entities."""

    consistency_probability = 0

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestSurvey, self).set_up()
        with mysql_connection.connect() as sql:
            sql.reset({'checkpoint': Checkpoint.get_table_definition()})

    def test_program_access(self):
        """Should be able to look up program config through project."""
        tasklist_template = []
        survey = Survey.create(
            tasklist_template,
            program_label='demo-program',
            organization_id='Organization_Foo',
            ordinal=1,
        )
        s_dict = survey.to_client_dict()

        self.assertEqual(s_dict['name'], 'Intervention')

    def test_checkpoint_creation(self):
        program_label = 'demo-program'
        program_config = Program.get_config(program_label)
        template = program_config['surveys'][0]['survey_tasklist_template']
        survey = Survey.create(
            template,
            program_label=program_label,
            organization_id='Organization_Foo',
            ordinal=1,
        )
        survey.put()
        checkpoints = Checkpoint.get(parent_id=survey.uid)
        self.assertEqual(len(checkpoints), len(template))

    def test_task_creation(self):
        program_label = 'demo-program'
        program_config = Program.get_config(program_label)
        template = program_config['surveys'][0]['survey_tasklist_template']
        survey = Survey.create(
            template,
            program_label=program_label,
            organization_id='Organization_Foo',
            ordinal=1,
        )
        survey.put()
        tasks = Task.get(ancestor=survey)
        num_tasks = sum([len(checkpoint['tasks']) for checkpoint in template])
        self.assertEqual(len(tasks), num_tasks)

    def test_put_clears_dashboard_queries(self):
        org_id = 'Organization_Foo'
        program_label = 'demo-program'
        pc = ProjectCohort.create(
            program_label='demo-program',
            organization_id=org_id,
            project_id='Project_Foo',
            cohort_label='2018',
        )
        pc.put()
        program_config = Program.get_config(program_label)
        template = program_config['surveys'][0]['survey_tasklist_template']
        survey = Survey.create(
            template,
            program_label=program_label,
            organization_id=org_id,
            project_cohort_id=pc.uid,
            ordinal=1,
        )
        survey.put()

        org_key = util.cached_query_key(
            'SuperDashboard',
            organization_id=pc.organization_id,
        )
        program_cohort_key = util.cached_query_key(
            'SuperDashboard',
            program_label=pc.program_label,
            cohort_label=pc.cohort_label,
        )

        memcache.set(org_key, {'foo': 1})
        memcache.set(program_cohort_key, {'foo': 1})

        # Re-fetch the org so it doesn't have an associated tasklist, which
        # saves checkpoints. This should clear memcache without relying on those
        # checkpoints.
        survey = survey.key.get()
        survey.status = 'ready'
        survey.put()

        self.assertIsNone(memcache.get(org_key))
        self.assertIsNone(memcache.get(program_cohort_key))
