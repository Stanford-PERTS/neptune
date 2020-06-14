import logging
import unittest

from model import Organization, Project, User
from unit_test_helper import ConsistencyTestCase
import notifier


class TestNotifier(ConsistencyTestCase):

    # Don't test eventual consistency. Notifications don't have to appear
    # instantly in queries, and if a notification misses a recently related
    # user, it's not a big deal.
    consistency_probability = 1

    def test_requested_to_join_organization(self):
        """Applying to join an org notifies org owners."""
        org = Organization.create(name="Foo Org")
        joiner = User.create(email="joiner@example.com", name="Johnny Joiner")
        owner1 = User.create(email="owner1@example.com",
                             owned_organizations=[org.uid])
        owner2 = User.create(email="owner2@example.com",
                             owned_organizations=[org.uid])
        owner1.put()
        owner2.put()

        notifier.requested_to_join_organization(joiner, org)
        # One notification should be generated for each owner
        self.assertEqual(len(owner1.notifications()), 1)
        self.assertEqual(len(owner2.notifications()), 1)

    def test_joined_organization(self):
        """Join approval an org notifies joiner."""
        org = Organization.create(name="Foo Org")
        joiner = User.create(email="joiner@example.com", name="Johnny Joiner")
        approver = User.create(email="approver@example.com",
                               owned_organizations=[org.uid])
        joiner.put()
        approver.put()

        notifier.joined_organization(approver, joiner, org)
        # One notification should be generated for the joiner.
        self.assertEqual(len(joiner.notifications()), 1)

    def test_create_organization(self):
        """Super admins notified about new orgs."""
        sup1 = User.create(email='sup1@perts.net', user_type='super_admin')
        sup2 = User.create(email='sup2@perts.net', user_type='super_admin')
        sup1.put()
        sup2.put()

        admin = User.create(email='admin@perts.net', user_type='user',
                            name='Addi Admin')
        org = Organization.create(name='Foo Org')

        notifier.created_organization(admin, org)

        # # Each super admin should get a notification.
        # self.assertEqual(len(sup1.notifications()), 1)
        # self.assertEqual(len(sup2.notifications()), 1)

        # We turned these off b/c supers are too busy.
        self.assertEqual(len(sup1.notifications()), 0)
        self.assertEqual(len(sup2.notifications()), 0)

    @unittest.skip("We turned these off b/c supers are too busy.")
    def test_user_changes_organization_task(self):
        """Super admins get notifications about activity on org tasks."""
        sup1 = User.create(email='sup1@perts.net', user_type='super_admin')
        sup2 = User.create(email='sup2@perts.net', user_type='super_admin')
        sup1.put()
        sup2.put()

        admin = User.create(email='admin@perts.net', user_type='user',
                            name='Addi Admin')
        org = Organization.create(name='Foo Org')
        task = org.tasklist.tasks[0]

        notifier.changed_organization_task(admin, org, task)

        # # Each super admin should get a notification.
        # self.assertEqual(len(sup1.notifications()), 1)
        # self.assertEqual(len(sup2.notifications()), 1)

        # We turned these off b/c supers are too busy.
        self.assertEqual(len(sup1.notifications()), 0)
        self.assertEqual(len(sup2.notifications()), 0)

    def test_super_admin_changes_organization_task(self):
        """Org admins get notifications about activity on their org tasks."""
        org = Organization.create(name='Foo Org')
        admin1 = User.create(email='admin1@perts.net', user_type='user',
                             owned_organizations=[org.uid])
        admin2 = User.create(email='admin2@perts.net', user_type='user',
                             owned_organizations=[org.uid])
        admin3 = User.create(email='admin3@perts.net', user_type='user')
        admin1.put()
        admin2.put()
        admin3.put()

        task = org.tasklist.tasks[0]
        sup = User.create(email='super@perts.net', user_type='super_admin',
                          name="Susan Super")

        notifier.changed_organization_task(sup, org, task)

        # Each related org admin should get a notification.
        self.assertEqual(len(admin1.notifications()), 1)
        self.assertEqual(len(admin2.notifications()), 1)
        self.assertEqual(len(admin3.notifications()), 0)

    @unittest.skip("No project notifications pending future cohort designs.")
    def test_create_project(self):
        """All program owners notified about new projects."""
        prog1 = User.create(email='prog1@perts.net', user_type='program_admin',
                            owned_programs=['demo-program'])
        prog2 = User.create(email='prog2@perts.net', user_type='super_admin',
                            owned_programs=['demo-program'])
        prog3 = User.create(email='prog3@perts.net', user_type='program_admin',
                            owned_programs=[])
        prog1.put()
        prog2.put()
        prog3.put()

        org = Organization.create(name='Foo Org')
        org.put()

        admin = User.create(email='admin@perts.net', user_type='user',
                            name='Addi Admin')
        project = Project.create(program_label='demo-program',
                                 organization_id=org.uid)

        notifier.created_project(admin, project)

        # Each super admin should get a notification.
        self.assertEqual(len(prog1.notifications()), 1)
        self.assertEqual(len(prog2.notifications()), 1)
        self.assertEqual(len(prog3.notifications()), 0)

    def test_user_changes_project_task(self):
        """All program admins are notified."""
        prog1 = User.create(email='prog1@perts.net', user_type='program_admin',
                            owned_programs=['demo-program'])
        prog2 = User.create(email='prog2@perts.net', user_type='super_admin',
                            owned_programs=['demo-program'])
        prog3 = User.create(email='prog3@perts.net', user_type='program_admin',
                            owned_programs=[])
        prog1.put()
        prog2.put()
        prog3.put()

        org = Organization.create(name='Foo Org')
        org.put()

        admin = User.create(email='admin@perts.net', user_type='user',
                            name='Addi Admin')
        project = Project.create(program_label='demo-program',
                                 organization_id=org.uid)
        task = project.tasklist.tasks[0]

        notifier.changed_project_task(admin, project, task)

        # Each related program admin should get a notification.
        self.assertEqual(len(prog1.notifications()), 1)
        self.assertEqual(len(prog2.notifications()), 1)
        self.assertEqual(len(prog3.notifications()), 0)

    def test_user_changes_project_task_with_account_manager(self):
        """Account manager notified."""
        acct_mgr = User.create(email='acct_mgr@perts.net',
                               user_type='program_admin',
                               owned_programs=['demo-program'])
        other_prog = User.create(email='other_prog@perts.net',
                                 user_type='program_admin',
                                 owned_programs=['demo-program'])
        acct_mgr.put()
        other_prog.put()

        org = Organization.create(name='Foo Org')
        org.put()

        admin = User.create(email='admin@perts.net', user_type='user',
                            name='Addi Admin')
        project = Project.create(program_label='demo-program',
                                 organization_id=org.uid,
                                 account_manager_id=acct_mgr.uid)
        task = project.tasklist.tasks[0]

        notifier.changed_project_task(admin, project, task)

        # Each account manager gets a notification, other related program
        # admins don't.
        self.assertEqual(len(acct_mgr.notifications()), 1)
        self.assertEqual(len(other_prog.notifications()), 0)

    def test_program_admin_changes_project_task(self):
        """All related org admins are notified."""
        org = Organization.create(name='Foo Org')
        admin1 = User.create(email='admin1@perts.net', user_type='user',
                             owned_organizations=[org.uid])
        admin2 = User.create(email='admin2@perts.net', user_type='user',
                             owned_organizations=[org.uid])
        admin3 = User.create(email='admin3@perts.net', user_type='user')
        admin1.put()
        admin2.put()
        admin3.put()

        task = org.tasklist.tasks[0]
        prog = User.create(email='prog@perts.net', user_type='program_admin',
                           name='Petrarch Prog')
        project = Project.create(program_label='demo-program',
                                 organization_id=org.uid)

        notifier.changed_project_task(prog, project, task)

        # Each related org admin should get a notification.
        self.assertEqual(len(admin1.notifications()), 1)
        self.assertEqual(len(admin2.notifications()), 1)
        self.assertEqual(len(admin3.notifications()), 0)

    def test_program_admin_changes_project_task_with_liaison(self):
        """Liaison notified."""
        org = Organization.create(name='Foo Org')
        admin1 = User.create(email='admin1@perts.net', user_type='user',
                             owned_organizations=[org.uid])
        admin2 = User.create(email='admin2@perts.net', user_type='user',
                             owned_organizations=[org.uid])
        admin1.put()
        admin2.put()

        task = org.tasklist.tasks[0]
        prog = User.create(email='prog@perts.net', user_type='program_admin',
                           name='Petrarch Prog')
        project = Project.create(program_label='demo-program',
                                 organization_id=org.uid,
                                 liaison_id=admin1.uid)

        notifier.changed_project_task(prog, project, task)

        # Each related org admin should get a notification.
        self.assertEqual(len(admin1.notifications()), 1)
        self.assertEqual(len(admin2.notifications()), 0)

    def test_redundant(self):
        """Multiple undismissed updates about the same task are ignored."""
        org = Organization.create(name='Foo Org')
        admin1 = User.create(email='admin1@perts.net', user_type='user',
                             owned_organizations=[org.uid])
        admin1.put()

        task = org.tasklist.tasks[0]
        sup = User.create(email='super@perts.net', user_type='super_admin',
                          name="Susan Super")

        # Second notification should not be saved.
        notifier.changed_organization_task(sup, org, task)
        notifier.changed_organization_task(sup, org, task)

        notes = admin1.notifications()
        self.assertEqual(len(notes), 1)

        # Two will arrive if one is dismissed.
        notes[0].dismissed = True
        notes[0].put()
        notifier.changed_organization_task(sup, org, task)
        self.assertEqual(len(admin1.notifications()), 2)

    @unittest.skip("No tasklist notifications pending future cohort designs.")
    def test_complete_organization_tasklist(self):
        """Super and org admins get notifications about complete tasklist."""
        org = Organization.create(name='Foo Org')
        sup1 = User.create(email='sup1@perts.net', user_type='super_admin')
        sup2 = User.create(email='sup2@perts.net', user_type='super_admin')
        org1 = User.create(email='org1@perts.net', user_type='user',
                           owned_organizations=[org.uid])
        org2 = User.create(email='org2@perts.net', user_type='user',
                           owned_organizations=[org.uid])
        sup1.put()
        sup2.put()
        org1.put()
        org2.put()

        notifier.completed_task_list(sup1, org)

        # Each super and or admin should get a notification.
        self.assertEqual(len(sup1.notifications()), 1)
        logging.info([n.body for n in sup1.notifications()])
        self.assertEqual(len(sup2.notifications()), 1)
        self.assertEqual(len(org1.notifications()), 1)
        self.assertEqual(len(org2.notifications()), 1)

    @unittest.skip("No tasklist notifications pending future cohort designs.")
    def test_complete_project_tasklist(self):
        """Liaisons and account managers notified re complete tasklist."""
        org = Organization.create(name='Foo Org')
        project = Project.create(program_label='demo-program',
                                 organization_id=org.uid)

        prog = User.create(email='prog@perts.net', user_type='prog_admin')
        admin = User.create(email='admin@perts.net', user_type='user',
                            owned_organizations=[org.uid])
        prog.put()
        admin.put()

        org.liaison_id = admin.uid
        project.account_manager_id = prog.uid

        notifier.completed_task_list(prog, project)

        self.assertEqual(len(prog.notifications()), 1)
        self.assertEqual(len(admin.notifications()), 1)
