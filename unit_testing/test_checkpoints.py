"""Test Checkpoint methods."""

from google.appengine.api import memcache
import json
import logging
import unittest

from unit_test_helper import ConsistencyTestCase
from model import (DatastoreModel, Checkpoint, Organization, Program, Project,
                   ProjectCohort)
import organization_tasks
import util


class TestCheckpoints(ConsistencyTestCase):
    """Test features of checkpoint objects, backed by MySQL."""

    consistency_probability = 0

    program_label = 'demo-program'

    # No set up is required b/c these tests are all in-memory.

    def tearDown(self):
        Program.reset_mocks()
        super(TestCheckpoints, self).tearDown()

    def test_checkpoint_task_ids(self):
        """Checkpoints should track task ids created within them."""
        org = Organization.create(name='Foo Org')

        for i, c in enumerate(org.tasklist.checkpoints):
            num_tasks = len(organization_tasks.tasklist_template[i]['tasks'])
            task_ids = json.loads(c.task_ids)
            self.assertEqual(len(task_ids), num_tasks)
            self.assertEqual(DatastoreModel.get_kind(task_ids[0]), 'Task')

    def test_checkpoint_client_dict(self):
        """Checkpoints should gain additional properties as client dicts."""
        checkpoint_template = {
            'name': "Project Foo",
            'label': 'demo_project__foo',
            'body': "foo",
            'tasks': [],
        }
        config = {'project_tasklist_template': [checkpoint_template]}
        Program.mock_program_config('demo-program', config)
        checkpoint = Checkpoint.create(
            parent_id='Project_foo', ordinal=1, program_label='demo-program',
            **checkpoint_template
        )
        self.assertIsNone(getattr(checkpoint, 'body', None))
        self.assertIsNotNone(checkpoint.to_client_dict()['body'])

    def create_with_project_cohort(self):
        checkpoint_template = {
            'name': "Survey Foo",
            'label': 'demo_survey__foo',
            'body': "foo",
            'tasks': [],
        }
        config = {
            'surveys': [
                {
                    'name': "Student Module",
                    'survey_tasklist_template': [checkpoint_template],
                },
            ],
        }
        Program.mock_program_config(self.program_label, config)

        org = Organization.create(name='Foo Org')
        org.put()

        project = Project.create(
            program_label=self.program_label,
            organization_id=org.uid,
        )
        project.put()

        pc = ProjectCohort.create(
            program_label=self.program_label,
            organization_id=org.uid,
            project_id=project.uid,
        )
        pc.put()

        checkpoint = Checkpoint.create(
            parent_id='Survey_foo', ordinal=1, program_label=self.program_label,
            organization_id=org.uid, project_id=project.uid,
            project_cohort_id=pc.uid, status='incomplete',
            **checkpoint_template
        )
        checkpoint.put()

        pc.update_cached_properties()

        return org, project, pc, checkpoint

    def test_update_project_cohort(self):
        org, project, pc, checkpoint = self.create_with_project_cohort()

        # Now changing the status should update the cached properties of the
        # project cohort.
        checkpoint.status = 'waiting'
        checkpoint.put()

        fetched = ProjectCohort.get_by_id(pc.uid)
        # There should be one survey checkpoint that was changed
        fetched_checkpoint = [
            c for c in fetched.get_cached_properties()['checkpoints']
            if c.parent_kind == 'Survey'
        ][0]

        self.assertEqual(
            fetched_checkpoint.status,
            'waiting',
        )

    def test_put_clears_dashboard_queries(self):
        org, project, pc, checkpoint = self.create_with_project_cohort()

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

        # This should clear memcache.
        checkpoint.status = 'complete'
        checkpoint.put()

        self.assertIsNone(memcache.get(org_key))
        self.assertIsNone(memcache.get(program_cohort_key))
