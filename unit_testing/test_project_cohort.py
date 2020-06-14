"""Test Project Cohort entities."""

from google.appengine.api import memcache
import unittest

from unit_test_helper import ConsistencyTestCase
from model import Program, ProjectCohort
import util


class TestProjectCohort(ConsistencyTestCase):
    """Test features of project cohort entities."""

    consistency_probability = 0

    program_label = 'demo-program'

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestProjectCohort, self).set_up()

        Program.mock_program_config(
            self.program_label,
            {
                'default_portal_type': 'name_or_id',
            }
        )

    def tearDown(self):
        Program.reset_mocks()
        super(TestProjectCohort, self).tearDown()

    def test_override_portal_message(self):
        label = 'override-program'
        config = {
            'override_portal_message': 'Override message.'
        }
        Program.mock_program_config(label, config)

        pc = ProjectCohort.create(program_label=label)
        self.assertEqual(
            pc.to_client_dict()['portal_message'],
            config['override_portal_message'],
        )

    def test_default_portal_type(self):
        """Portal type should be based on program config"""
        program = Program.get_config(self.program_label)
        pc = ProjectCohort.create(
            program_label=self.program_label,
        )
        self.assertEqual(pc.portal_type, program['default_portal_type'])

    def test_put_clears_dashboard_queries(self):
        pc = ProjectCohort.create(
            program_label='demo-program',
            organization_id='Organization_Foo',
            project_id='Project_Foo',
            cohort_label='2018',
        )

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
        pc.put()

        self.assertIsNone(memcache.get(org_key))
        self.assertIsNone(memcache.get(program_cohort_key))
