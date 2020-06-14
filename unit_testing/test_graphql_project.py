import datetime
import json
import logging
import unittest
import webapp2
import webtest

from api_handlers import api_routes
from model import User, Organization, Project
from unit_test_helper import ConsistencyTestCase, login_headers
import config


class TestGraphQLProject(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestGraphQLProject, self).set_up()

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

    def test_get_single_project(self):
        user = User.create(email="super@example.com", user_type='super_admin')
        user.put()

        org = Organization.create(name="Org Foo")
        org.put()

        project = Project.create(
            organization_id=org.uid,
            program_label='demo-program',
            account_manager_id='User_001',
            liaison_id='User_002',
            priority=True,
            deidentification_method='total',
            loa_notes="Some stuff happened.",
            last_active=datetime.datetime.now(),
        )
        project.put()

        query = '''
        query GetSingleProject($uid: String!) {
            project(uid: $uid) {
                account_manager_id
                created
                deidentification_method
                deleted
                last_active
                liaison_id
                loa_notes
                modified
                organization_id
                organization_name
                organization_status
                priority
                program_description
                program_label
                program_name
                short_uid
                uid
            }
        }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            # See http://graphql.org/learn/serving-over-http/#post-request
            {
                'query': query,
                'variables': {'uid': project.uid},
            },
            headers=login_headers(user.uid),
        )

        self.assertEqual(
            response.body,
            json.dumps({'project': project.to_client_dict()}),
        )

    def test_get_all_projects(self):
        user = User.create(email="super@example.com", user_type='super_admin')
        user.put()

        org = Organization.create(name="Org Foo")
        org.put()

        project1 = Project.create(organization_id=org.uid,
                                  program_label='demo-program')
        project2 = Project.create(organization_id=org.uid,
                                  program_label='demo-program')
        project1.put()
        project2.put()

        query = '''
        query GetAllProjects {
            projects {
                uid
            }
        }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            {'query': query},
            headers=login_headers(user.uid),
        )
        received = json.loads(response.body)

        # No particular order.
        self.assertIn({'uid': project1.uid}, received['projects'])
        self.assertIn({'uid': project2.uid}, received['projects'])
