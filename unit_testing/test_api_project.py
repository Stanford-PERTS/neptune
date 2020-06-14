import json
import webapp2
import webtest

from api_handlers import api_routes
from model import User, Organization, Program, Project
from unit_test_helper import ConsistencyTestCase, login_headers
import config


class TestApiProject(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    program_label = 'demo-program'
    org_id = None

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiProject, self).set_up()

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

        org = Organization.create(name='Org Foo')
        org.put()
        self.org_id = org.uid

    def tear_down(self):
        Program.reset_mocks()
        super(TestApiProject, self).tearDown()

    def test_user_create(self):
        user = User.create(email="org@example.com",
                           owned_organizations=[self.org_id])
        user.put()

        response = self.testapp.post_json(
            '/api/projects',
            {'organization_id': self.org_id,
             'program_label': self.program_label},
            headers=login_headers(user.uid),
        )
        response_dict = json.loads(response.body)

        # Project should exist.
        self.assertIsNotNone(Project.get_by_id(response_dict['uid']))

        # User should own it.
        self.assertIn(response_dict['uid'], user.key.get().owned_projects)

        return (response_dict, user)

    def test_program_admin_create(self):
        program_admin = User.create(email="org@example.com",
                                    owned_programs=[self.program_label])
        program_admin.put()

        response = self.testapp.post_json(
            '/api/projects',
            {'organization_id': self.org_id,
             'program_label': self.program_label},
            headers=login_headers(program_admin.uid),
        )
        response_dict = json.loads(response.body)

        self.assertIsNotNone(Project.get_by_id(response_dict['uid']))

    def test_join_existing_project(self):
        project_dict, user = self.test_user_create()

        # Try to make another one, which should _succeed_, now that we support
        # multiple projects at an org.
        self.testapp.post_json(
            '/api/projects',
            {'organization_id': self.org_id,
             'program_label': self.program_label},
            headers=login_headers(user.uid),
        )

    def test_create_requires_auth(self):
        self.testapp.post_json(
            '/api/projects',
            {'organization_id': self.org_id,
             'program_label': self.program_label},
            status=401,
        )
