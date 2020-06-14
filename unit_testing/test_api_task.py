import unittest
import webapp2
import webtest

from api_handlers import api_routes
from model import Organization, User, Checkpoint
from unit_test_helper import ConsistencyTestCase, login_headers
import config
import mysql_connection


class TestApiTask(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiTask, self).set_up()

        with mysql_connection.connect() as sql:
            sql.reset({'checkpoint': Checkpoint.get_table_definition()})

        application = webapp2.WSGIApplication(
            api_routes,
            config={
                'webapp2_extras.sessions': {
                    'secret_key': self.cookie_key
                }
            },
            debug=True
        )
        self.testapp = webtest.TestApp(application)

    def test_update_checkpoint_incomplete(self):
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()
        org = Organization.create(name='Foo Org')
        org.put()

        # Work with the first checkpoint (generally there's only one anyway).
        c = org.tasklist.checkpoints[0]

        # Our org tasklist doesn't change much; break down its structure.
        tasks = [t for t in org.tasklist.tasks if t.checkpoint_id == c.uid]
        invite_task, liaison_task, approve_task = tasks

        # Marking just the first task complete shouldn't change the checkpoint
        # status.
        invite_task.status = 'complete'
        self.testapp.put_json(
            '/api/tasks/{}'.format(invite_task.uid),
            invite_task.to_client_dict(),
            headers=login_headers(user.uid),
        )

        fetched_c = Checkpoint.get_by_id(c.uid)
        self.assertEqual(fetched_c.status, 'incomplete')

    @unittest.skip("the approve task no longer makes people wait")
    def test_update_checkpoint_waiting(self):
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()
        org = Organization.create(name='Foo Org')
        org.put()

        # Work with the first checkpoint (generally there's only one anyway).
        c = org.tasklist.checkpoints[0]

        # Our org tasklist doesn't change much; break down its structure.
        tasks = [t for t in org.tasklist.tasks if t.checkpoint_id == c.uid]
        invite_task, liaison_task, approve_task = tasks

        # Marking the first two complete should change the checkpoint to
        # waiting, since the last is for super admins only.
        for task in (invite_task, liaison_task):
            task.status = 'complete'
            self.testapp.put_json(
                '/api/tasks/{}'.format(task.uid),
                task.to_client_dict(),
                headers=login_headers(user.uid),
            )

        fetched_c = Checkpoint.get_by_id(c.uid)
        self.assertEqual(fetched_c.status, 'waiting')

    def test_update_checkpoint_complete(self):
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()
        org = Organization.create(name='Foo Org')
        org.put()

        # Work with the first checkpoint (generally there's only one anyway).
        c = org.tasklist.checkpoints[0]

        # Our org tasklist doesn't change much; break down its structure.
        tasks = [t for t in org.tasklist.tasks if t.checkpoint_id == c.uid]
        invite_task, liaison_task, approve_task = tasks

        # Marking all tasks as complete should complete the checkpoint.
        for task in tasks:
            task.status = 'complete'
            self.testapp.put_json(
                '/api/tasks/{}'.format(task.uid),
                task.to_client_dict(),
                headers=login_headers(user.uid),
            )

        fetched_c = Checkpoint.get_by_id(c.uid)
        self.assertEqual(fetched_c.status, 'complete')
