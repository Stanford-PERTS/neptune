from api_handlers import api_routes
from google.appengine.ext import ndb
from google.appengine.ext import testbed
import json
import logging
import unittest
import webapp2
import webtest

from model import ProjectCohort, User
from unit_test_helper import ConsistencyTestCase
from webapp2_extras.appengine.auth.models import Unique
import config
import jwt_helper


path = lambda code: '/api/codes/{}'.format(code.replace(' ', '-'))


class TestApiParticipationCodes(ConsistencyTestCase):

    # We expect project cohorts to be created well before participation happens
    # so they will have plenty of time to reach consistency.
    consistency_probability = 1

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiParticipationCodes, self).set_up()

        self.testbed.init_taskqueue_stub()
        self.taskqueue = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

        application = self.patch_webapp(webapp2.WSGIApplication)(
            api_routes,
            config={
                'webapp2_extras.sessions': {
                    'secret_key': self.cookie_key
                }
            },
            debug=True
        )
        self.testapp = webtest.TestApp(application)

    def patch_webapp(self, WSGIApplication):
        """Webapp doesn't allow PATCH by default. See wsgi.py."""
        allowed = WSGIApplication.allowed_methods
        WSGIApplication.allowed_methods = allowed.union(('PATCH',))
        return WSGIApplication

    def login_headers(self, user):
        return {'Authorization': 'Bearer ' + jwt_helper.encode_user(user)}

    def create_demo_data(self):
        # Existing things to relate to.
        program_label = 'demo-program'
        cohort_label = 'demo-cohort'
        org_id = 'Org_Foo'
        user_id = 'User_Liaison'
        pc = ProjectCohort.create(
            project_id='Project_foo',
            organization_id=org_id,
            program_label=program_label,
            cohort_label=cohort_label,
            liaison_id=user_id,
            portal_type='custom',
            custom_portal_url='http://www.example.com',
        )
        pc.put()

        return pc

    def test_get_neptune_code(self):
        pc = self.create_demo_data()
        url_code = pc.code.replace(' ', '-')
        # No login headers; testing as an unauthenticated user. Any return
        # status other than 200 will break the test.
        response = self.testapp.get('/api/codes/{}'.format(url_code))
        expected = pc.to_client_dict()

        self.assertEqual(json.loads(response.body), expected)

    def test_get_non_existent_code(self):
        pc = self.create_demo_data()
        url_code = 'does-not-exist'
        # No login headers; testing as an unauthenticated user. Any return
        # status other than 200 will break the test.
        response = self.testapp.get(
            '/api/codes/{}'.format(url_code),
            status=404,
        )

    def test_create_code_requires_auth(self):
        response = self.testapp.post_json('/api/codes', {}, status=401)

    def test_create_code_creates_unique(self):
        """Should be an entry in Unique to ensure unique code."""
        user = User.create(email='user@perts.net')
        user.put()
        response = self.testapp.post_json(
            '/api/codes',
            {'organization_id': 'triton', 'program_label': 'triton'},
            headers=self.login_headers(user)
        )
        pc = ProjectCohort.query().fetch(1)
        unique = Unique.query().fetch(1)
        self.assertIsNotNone(pc)
        self.assertIsNotNone(unique)

    def test_create_code_defaults(self):
        user = User.create(email='user@perts.net')
        user.put()
        response = self.testapp.post_json(
            '/api/codes',
            {'organization_id': 'triton', 'program_label': 'triton'},
            headers=self.login_headers(user)
        )
        expected_props = ('code', 'organization_id', 'program_label',
                          'portal_type', 'portal_message', 'survey_params')
        for p in expected_props:
            self.assertIn(p, json.loads(response.body))

    def test_create_code_specify(self):
        user = User.create(email='user@perts.net')
        user.put()
        params = {
            'organization_id': 'Team_foo',
            'program_label': 'triton',
            'portal_type': 'first_mi_last',
            'portal_message': "Please do the thing.",
            'survey_params': {'teacher_caring': True},
        }
        response = self.testapp.post_json(
            '/api/codes',
            params,
            headers=self.login_headers(user)
        )
        code_dict = json.loads(response.body)
        code_dict.pop('code')
        self.assertEqual(code_dict, params)

    def test_update_code_requires_auth(self):
        self.testapp.put_json(
            '/api/codes/trout-viper',
            {'name': 'Team Foo'},
            status=401,
        )

    def test_update_code_forbidden(self):
        """Requires 'allowed_endpoints' in jwt."""
        token = jwt_helper.encode({'user_id': 'User_foo',
                                   'email': 'user@foo.com'})
        self.testapp.put_json(
            '/api/codes/trout-viper',
            {'name': 'Team Foo'},
            headers={'Authorization': 'Bearer ' + token},
            status=403,
        )

    def test_update_code_allowed(self):
        code = 'trout viper'
        path = '/api/codes/{}'.format(code.replace(' ', '-'))
        pc = ProjectCohort.create(
            code=code,
            organization_id='triton',
            program_label='triton',
        )
        pc.put()
        pc.key.get()  # simulate consistency, code fetches are eventual
        token = jwt_helper.encode({
            'user_id': 'User_foo',
            'email': 'user@foo.com',
            'allowed_endpoints': ['PUT //neptune{}'.format(path)],
        })
        self.testapp.put_json(
            path,
            {'portal_message': 'hi'},
            headers={'Authorization': 'Bearer ' + token}
        )

    def test_patch_update_codes(self):
        codes = ('trout viper', 'solid snake')
        pcs = []
        for c in codes:
            pcs.append(ProjectCohort.create(
                code=c,
                organization_id='triton',
                program_label='triton',
            ))
        ndb.put_multi(pcs)
        for pc in pcs:
            pc.key.get()  # simulate consistency, code fetches are eventual

        token = jwt_helper.encode({
            'user_id': 'User_foo',
            'email': 'user@foo.com',
            'allowed_endpoints': ['PUT //neptune{}'.format(path(c))
                                  for c in codes],
        })

        body = {'portal_message': 'hi'}
        response = self.testapp.patch_json(
            '/api/codes',
            [{'method': 'PUT', 'path': path(c), 'body': body} for c in codes],
            headers={'Authorization': 'Bearer ' + token},
        )
        task_names = [t['task_name'] for t in json.loads(response.body)]

        # PATCHing two codes should result in two tasks.
        for name in task_names:
            tasks = self.taskqueue.get_filtered_tasks(name=name)
            self.assertEqual(len(tasks), 1)
            t = tasks[0]

            # Running the tasks should update the codes.
            self.assertEqual(t.method, 'PUT')
            self.testapp.put_json(
                t.url,
                json.loads(t.payload),
                headers=t.headers,
            )

        for pc in pcs:
            fetched = pc.key.get()
            self.assertEqual(fetched.portal_message, 'hi')

    def test_delete_code_requires_auth(self):
        self.testapp.delete(
            '/api/codes/trout-viper',
            {'name': 'Team Foo'},
            status=401,
        )

    def test_delete_code_forbidden(self):
        """Requires 'allowed_endpoints' in jwt."""
        token = jwt_helper.encode({'user_id': 'User_foo',
                                   'email': 'user@foo.com'})
        self.testapp.delete(
            '/api/codes/trout-viper',
            headers={'Authorization': 'Bearer ' + token},
            status=403,
        )

    def test_delete_code_allowed(self):
        code = 'trout viper'
        path = '/api/codes/{}'.format(code.replace(' ', '-'))
        pc = ProjectCohort.create(
            code=code,
            organization_id='triton',
            program_label='triton',
        )
        pc.put()
        pc.key.get()  # simulate consistency, code fetches are eventual
        token = jwt_helper.encode({
            'user_id': 'User_foo',
            'email': 'user@foo.com',
            'allowed_endpoints': ['DELETE //neptune{}'.format(path)],
        })
        self.testapp.delete(
            path,
            headers={'Authorization': 'Bearer ' + token},
            status=204,
        )

        # Project cohort AND Unique should be gone
        self.assertIsNone(pc.key.get())
        unique_key = ndb.Key('Unique', ProjectCohort.uniqueness_key(code))
        self.assertIsNone(unique_key.get())

    def test_patch_delete_codes(self):
        codes = ('trout viper', 'solid snake')
        pcs = []
        for c in codes:
            pcs.append(ProjectCohort.create(
                code=c,
                organization_id='triton',
                program_label='triton',
            ))
        ndb.put_multi(pcs)
        for pc in pcs:
            pc.key.get()  # simulate consistency, code fetches are eventual

        token = jwt_helper.encode({
            'user_id': 'User_foo',
            'email': 'user@foo.com',
            'allowed_endpoints': ['DELETE //neptune{}'.format(path(c))
                                  for c in codes],
        })

        response = self.testapp.patch_json(
            '/api/codes',
            [{'method': 'DELETE', 'path': path(c)} for c in codes],
            headers={'Authorization': 'Bearer ' + token},
        )
        task_names = [t['task_name'] for t in json.loads(response.body)]

        # PATCHing two codes should result in two tasks.
        for name in task_names:
            tasks = self.taskqueue.get_filtered_tasks(name=name)
            self.assertEqual(len(tasks), 1)
            t = tasks[0]

            # Running the tasks should update the codes.
            self.assertEqual(t.method, 'DELETE')
            self.testapp.delete(t.url, headers=t.headers)

        for pc in pcs:
            self.assertIsNone(pc.key.get())

    def test_patch_requires_auth(self):
        """No jwt in Authorization header results in 401."""
        codes = ('trout viper', 'solid snake')
        self.testapp.patch_json(
            '/api/codes',
            [{'method': 'DELETE', 'path': path(c)} for c in codes],
            status=401,
        )

    def test_patch_super_admin(self):
        """Super admins don't need to specify allowed endpoints in the jwt."""
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()
        codes = ('trout viper', 'solid snake')
        self.testapp.patch_json(
            '/api/codes',
            [{'method': 'DELETE', 'path': path(c)} for c in codes],
            headers=self.login_headers(user),
        )

    def test_patch_missing_allowed_endpoints(self):
        """You must have an allowed endpoint in the jwt for each call."""
        user = User.create(email='user@perts.net')
        user.put()
        codes = ('trout viper', 'solid snake')
        self.testapp.patch_json(
            '/api/codes',
            [{'method': 'DELETE', 'path': path(c)} for c in codes],
            headers=self.login_headers(user),
            status=403,
        )

    def test_patch_bad_scope(self):
        """You can't request calls from some different scope/collection."""
        codes = ('trout viper', 'solid snake')

        # These paths are for the "other" collection, not "codes".
        path = lambda code: '/api/other/{}'.format(code.replace(' ', '-'))

        token = jwt_helper.encode({
            'user_id': 'User_foo',
            'email': 'user@foo.com',
            'allowed_endpoints': ['DELETE //neptune{}'.format(path(c))
                                  for c in codes],
        })

        self.testapp.patch_json(
            '/api/codes',  # doesn't match "/api/other"
            [{'method': 'DELETE', 'path': path(c)} for c in codes],
            headers={'Authorization': 'Bearer ' + token},
            status=400,
        )

    def test_patch_bad_method(self):
        """Can only package PUT and DELETE with a bulk PATCH."""
        codes = ('trout viper', 'solid snake')

        token = jwt_helper.encode({
            'user_id': 'User_foo',
            'email': 'user@foo.com',
            'allowed_endpoints': ['POST //neptune{}'.format(path(c))
                                  for c in codes],
        })

        self.testapp.patch_json(
            '/api/codes',  # doesn't match "/api/other"
            [{'method': 'POST', 'path': path(c)} for c in codes],
            headers={'Authorization': 'Bearer ' + token},
            status=400,
        )
