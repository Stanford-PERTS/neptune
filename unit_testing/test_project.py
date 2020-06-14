"""Test Project entities."""

from google.appengine.api import memcache
import unittest

from unit_test_helper import ConsistencyTestCase
from model import (Checkpoint, Organization, Program, Project, ProjectCohort,
                   Task)
import mysql_connection
import util


class TestProject(ConsistencyTestCase):
    """Test features of project entities."""

    consistency_probability = 0

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestProject, self).set_up()
        with mysql_connection.connect() as sql:
            sql.reset({'checkpoint': Checkpoint.get_table_definition()})

    def test_program_access(self):
        """Should be able to look up program config through project."""
        organization = Organization.create(name='Foo College')
        organization.put()
        project = Project.create(program_label='demo-program',
                                 organization_id=organization.uid)
        project.put()
        p_dict = project.to_client_dict()

        self.assertEqual(p_dict['program_name'], 'Demo Program')
        self.assertIsInstance(p_dict['program_description'], basestring)

    def test_program_label_validation(self):
        """Should be impossible to create projects for invalid programs."""
        with self.assertRaises(Exception):
            Project.create(program_label='does-not-exist',
                           organization_id='Organization_Foo')

    def test_checkpoint_creation(self):
        project = Project.create(program_label='demo-program',
                                 organization_id='Organization_Foo')
        project.put()
        checkpoints = Checkpoint.get(parent_id=project.uid)
        program_config = Program.get_config(project.program_label)
        template = program_config['project_tasklist_template']
        self.assertEqual(len(checkpoints), len(template))

    def test_task_creation(self):
        project = Project.create(program_label='demo-program',
                                 organization_id='Organization_Foo')
        project.put()
        tasks = Task.get(ancestor=project)
        program_config = Program.get_config(project.program_label)
        template = program_config['project_tasklist_template']
        num_tasks = sum([len(checkpoint['tasks']) for checkpoint in template])
        self.assertEqual(len(tasks), num_tasks)

    def test_organization_name(self):
        """Updating a project should update organization name"""
        organization = Organization.create(name='Foo College')
        organization.put()
        project = Project.create(program_label='demo-program',
                                 organization_id=organization.uid)
        project.put()
        self.assertEqual(project.to_client_dict()['organization_name'],
                         organization.name)

    def create_with_pc(self):
        project = Project.create(
            program_label='demo-program',
            organization_id='Organization_Foo',
        )
        project.put()
        pc = ProjectCohort.create(
            program_label=project.program_label,
            organization_id=project.organization_id,
            project_id=project.uid,
            cohort_label='2018',
        )
        pc.put()

        return project.key.get(), pc.key.get()

    def test_put_clears_project_cohort_cache(self):
        project, pc = self.create_with_pc()

        key = util.cached_properties_key(pc.uid)
        memcache.set(key, {'foo': 1})

        # Re-fetch the org so it doesn't have an associated tasklist, which
        # saves checkpoints. This should clear memcache without relying on those
        # checkpoints.
        project = project.key.get()
        project.priority = True
        project.put()

        self.assertIsNone(memcache.get(key))

    def test_put_clears_dashboard_queries(self):
        project, pc = self.create_with_pc()

        org_key = util.cached_query_key(
            'SuperDashboard',
            organization_id=project.organization_id,
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
        project = project.key.get()
        project.priority = True
        project.put()

        self.assertIsNone(memcache.get(org_key))
        self.assertIsNone(memcache.get(program_cohort_key))
