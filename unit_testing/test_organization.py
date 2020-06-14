from google.appengine.api import memcache
from model import (DatastoreModel, Checkpoint, Organization, Project,
                   ProjectCohort, Task, User)
from unit_test_helper import ConsistencyTestCase
import mysql_connection
import logging
import util


class TestOrganization(ConsistencyTestCase):

    consistency_probability = 1

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestOrganization, self).set_up()
        with mysql_connection.connect() as sql:
            sql.reset({'checkpoint': Checkpoint.get_table_definition()})

    def test_create(self):
        o = Organization.create()

        self.assertNotEqual(len(o.tasklist.tasks), 0)
        self.assertNotEqual(len(o.tasklist.checkpoints), 0)
        for t in o.tasklist.tasks:
            self.assertIsInstance(t, Task)
        for c in o.tasklist.checkpoints:
            self.assertIsInstance(c, Checkpoint)
            self.assertEqual(DatastoreModel.get_kind(c.uid), 'Checkpoint')

    def test_fetch_owners(self):
        """Tests method to pull owners of a given organization"""
        org = Organization.create()
        # Add organizations id's to users
        # include extra org id's in case that confuses the code.
        user1 = User.create(email="test1@example.com",
                            owned_organizations=[org.uid, 'foo'])
        user2 = User.create(email="test2@example.com",
                            owned_organizations=[org.uid])
        user1.put()
        user2.put()
        owners = User.get(owned_organizations=org.uid, n=10)
        self.assertEqual({user1, user2}, set(owners))

    def test_fetch_checkpoints(self):
        """Tests method to pull checkpoints for an organization tasklist."""
        org = Organization.create()
        org.put()

        # Tasks are automatically created from template on org.put()
        checkpoints = Checkpoint.get(parent_id=org.uid, order='ordinal')
        self.assertNotEqual(len(checkpoints), 0)
        self.assertEqual(DatastoreModel.get_kind(checkpoints[0].uid), 'Checkpoint')
        # Check that the checkpoints are being ordered properly.
        for i, c in enumerate(checkpoints):
            self.assertEqual(c.ordinal, i + 1)

    def test_fetch_tasks(self):
        """Tests method to pull tasks for an organization tasklist."""
        org = Organization.create()
        org.put()

        # Tasks are automatically created from template on org.put()
        tasks = org.tasks()
        self.assertIsNotNone(tasks)
        self.assertNotEqual(len(tasks), 0)
        self.assertIsInstance(tasks[0], Task)
        # Check that the tasks are being ordered properly.
        for i, t in enumerate(tasks):
            self.assertEqual(t.ordinal, i + 1)

    def test_organization_name_update(self):
        """Updating an organization name should update associated project"""
        org_name_1 = 'Foo College'
        org_name_2 = 'Bar College'
        organization = Organization.create(name=org_name_1)
        organization.put()
        project = Project.create(program_label='demo-program',
                                 organization_id=organization.uid)
        project.put()
        organization = Organization.get_by_id(organization.uid)
        organization.name = org_name_2
        organization.put()
        project_dict = project.get_by_id(project.uid).to_client_dict()
        self.assertEqual(project_dict['organization_name'], organization.name)

    def create_org_with_pc(self):
        org = Organization.create(name="Foo College")
        org.put()
        project = Project.create(
            program_label='demo-program',
            organization_id=org.uid,
        )
        project.put()
        pc = ProjectCohort.create(
            program_label=project.program_label,
            organization_id=org.uid,
            project_id=project.uid,
            cohort_label='2018',
        )
        pc.put()

        # Simulate consistency
        return org, project.key.get(), pc.key.get()

    def test_put_clears_entity_caches(self):
        org, project, pc = self.create_org_with_pc()

        p_key = util.cached_properties_key(project.uid)
        pc_key = util.cached_properties_key(pc.uid)
        memcache.set(p_key, {'foo': 1})
        memcache.set(pc_key, {'foo': 1})

        # Re-fetch the org so it doesn't have an associated tasklist, which
        # saves checkpoints. This should clear memcache without relying on those
        # checkpoints.
        org = org.key.get()
        org.name = "Bar University"
        org.put()

        self.assertIsNone(memcache.get(p_key))
        self.assertIsNone(memcache.get(pc_key))

    def test_put_clears_dashboard_queries(self):
        org, project, pc = self.create_org_with_pc()

        org_key = util.cached_query_key(
            'SuperDashboard',
            organization_id=org.uid,
        )
        program_cohort_key = util.cached_query_key(
            'SuperDashboard',
            program_label=pc.program_label,
            cohort_label=pc.cohort_label,
        )
        memcache.set(org_key, {'foo': 1})
        memcache.set(program_cohort_key, {'foo': 1})
        self.assertEqual(memcache.get(program_cohort_key), {'foo': 1})

        # Re-fetch the org so it doesn't have an associated tasklist, which
        # saves checkpoints. This should clear memcache without relying on those
        # checkpoints.
        org = org.key.get()
        org.name = "Bar University"
        org.put()

        self.assertIsNone(memcache.get(org_key))
        self.assertIsNone(memcache.get(program_cohort_key))
