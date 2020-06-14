import json
import webapp2
import webtest

from api_handlers import api_routes
from model import DatastoreModel, Checkpoint, Organization, User
from unit_test_helper import ConsistencyTestCase, login_headers
import config
import mysql_connection


class TestApiOrganization(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiOrganization, self).set_up()

        # Clear relevant tables from testing SQL database.
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

    def test_get_tasks(self):
        org = Organization.create()
        org.put()

        user = User.create(email='org@example.com', user_type='user',
                           owned_organizations=[org.uid])
        user.put()

        response = self.testapp.get(
            '/api/organizations/{}/tasks'.format(org.uid),
            headers=login_headers(user.uid),
        )
        tasks = json.loads(response.body)
        for t in tasks:
            self.assertEqual(DatastoreModel.get_kind(t['uid']), 'Task')
            self.assertEqual(DatastoreModel.get_parent_uid(t['uid']), org.uid)

    def test_get_checkpoints(self):
        org = Organization.create()
        org.put()

        user = User.create(email='org@example.com', user_type='user',
                           owned_organizations=[org.uid])
        user.put()

        response = self.testapp.get(
            '/api/organizations/{}/checkpoints'.format(org.uid),
            headers=login_headers(user.uid),
        )
        checkpoints = json.loads(response.body)
        for c in checkpoints:
            self.assertEqual(DatastoreModel.get_kind(c['uid']), 'Checkpoint')
            self.assertEqual(c['parent_id'], org.uid)

    def test_get_owners(self):
        org = Organization.create()
        org.put()

        user = User.create(email='org@example.com', user_type='user',
                           owned_organizations=[org.uid])
        user.put()

        response = self.testapp.get(
            '/api/organizations/{}/users'.format(org.uid),
            headers=login_headers(user.uid),
        )
        owners = json.loads(response.body)
        for o in owners:
            self.assertEqual(DatastoreModel.get_kind(o['uid']), 'User')
