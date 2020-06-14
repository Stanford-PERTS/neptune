import json
import logging
import unittest
import webapp2
import webtest

from api_handlers import api_routes
from model import User
from unit_test_helper import ConsistencyTestCase, login_headers
import config


class TestGraphQLUser(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestGraphQLUser, self).set_up()

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

    def test_get_single_user(self):
        user = User.create(email="super@example.com",
                           user_type='super_admin',
                           owned_organizations=['Organization_001'])
        user.hashed_password = User.hash_password('abcdefgh')
        user.put()

        query = '''
        query GetSingleUser($uid: String!) {
            user(uid: $uid) {
                assc_organizations
                assc_projects
                created
                deleted
                email
                google_id
                hashed_password
                last_login
                modified
                name
                notification_option
                owned_data_requests
                owned_data_tables
                owned_organizations
                owned_programs
                owned_projects
                phone_number
                role
                short_uid
                uid
                user_type
            }
        }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            # See http://graphql.org/learn/serving-over-http/#post-request
            {
                'query': query,
                'variables': {'uid': user.uid},
            },
            headers=login_headers(user.uid),
        )

        # Using the api gives the user a value for last_login. Refetch them to
        # get an accurate reference.
        user = user.key.get()

        self.assertEqual(
            response.body,
            json.dumps({'user': user.to_client_dict()}),
        )

    def test_get_all_users(self):
        super_user = User.create(
            name='super',
            email="super@example.com",
            user_type='super_admin',
            owned_organizations=['Organization_001'],
        )
        super_user.put()
        user1 = User.create(name='foo', email="foo@bar.com")
        user1.put()

        # Assume enough time to achieve consistency. Typical for a get-whole
        # collection query that isn't scoped in any way.
        User.get_by_id([super_user.uid, user1.uid])

        query = '''
        query GetAllUsers {
            users {
                email
            }
        }
        '''

        expected = {
            'users': [
                # Should be ordered by name.
                {'email': user1.email},
                {'email': super_user.email},
            ]
        }

        response = self.testapp.post_json(
            '/api/graphql',
            {'query': query},
            headers=login_headers(super_user.uid),
        )

        self.assertEqual(json.loads(response.body), expected)
