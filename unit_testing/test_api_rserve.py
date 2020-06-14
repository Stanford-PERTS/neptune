from google.appengine.ext import ndb
import logging
import unittest
import webapp2
import webtest

from api_handlers import api_routes
from gae_handlers import BaseHandler
from model import Dataset, ProjectCohort, SecretValue, User
from unit_test_helper import ConsistencyTestCase, jwt_headers
from view_handlers import view_routes
import config
import json
import jwt_helper
import util

invalid_public_rsa_key = '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAytzAqmZmvF5g8jSlfp4E
8Cb1Nvhgm566+t2i8o4SuSwVQzYHvox15ZO33BOZavQ2IPmD5LtePSPg38QlCNr4
SlRTNSBvhJOr98UcP6gLA5TW9m8JYe+i9FEbrHnwzKMM6ZtKNXz49wbYHSxuT59b
y9C0TeqoNGK4rcSUSHVURXDh6nmfQTFYDbu6X6kZ0rPUxWlTyvbT1GSBg68zqj0n
Y0qmtYab3Kskul0mnodeav9A+OOcv0ods1/Xf+btc1JT8QUqc15WpClPNDKSDzT9
cI5AK3rSd+b+VuQuHaD0Um77I6LK6vwKeubItgWL2N3FsS730ocdLPnkqQfxkfQa
TQIDAQAB
-----END PUBLIC KEY-----'''


class TestApiRServe(ConsistencyTestCase):

    # We're not interested in how accurately we can retrieve users immediately
    # after saving, so simulate a fully consistent datastore.
    consistency_probability = 1

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    valid_jwt = None

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiRServe, self).set_up()

        application = webapp2.WSGIApplication(
            api_routes + view_routes,
            config={
                'webapp2_extras.sessions': {
                    'secret_key': self.cookie_key
                }
            },
        )
        self.testapp = webtest.TestApp(application)

        if self.valid_jwt is None:
            self.valid_jwt = jwt_helper.encode_rsa({
                'user_id': 'User_rserve',
                'email': 'rserve@perts.net',
                'user_type': 'super_admin',
            })

    def test_save_dataset_forbidden(self):
        data = {
            'school_name': 'Example School',
            'pct_winning': 100,
        }

        # Fails if missing.
        self.testapp.post_json('/api/datasets', {}, status=401)

        # Fails if malformed.
        self.testapp.post_json(
            '/api/datasets',
            {},
            headers={'Authorization': 'Bearer foo'},
            status=401,
        )

        # Fails if signature invalid (force invalid by saving a bad secret).
        sv = SecretValue(
            id='jwt_public_rsa',
            value=invalid_public_rsa_key,
        )
        sv.put()
        self.testapp.post_json(
            '/api/datasets',
            {},
            headers={'Authorization': 'Bearer ' + self.valid_jwt},
            status=401,
        )

    def test_save_dataset(self):
        data = {
            'school_name': 'Example School',
            'pct_winning': 100,
        }
        parent_id = 'ProjectCohort_001'
        response = self.testapp.post_json(
            '/api/datasets?parent_id={}'.format(parent_id),
            {
                'content_type': 'application/json',
                'filename': 'script.date.unit_id',
                'data': data,
            },
            headers={'Authorization': 'Bearer ' + self.valid_jwt},
        )

        # get dataset from database to make sure it was saved
        ds = Dataset.get_by_id(json.loads(response.body)['uid'])
        self.assertIsNotNone(ds)
        self.assertEqual(ds.parent_id, parent_id)

        return ds, data

    def test_get_parentless_dataset(self):
        """Only super admins can get parentless datasets."""
        user = User.create(email='demo@perts.net', user_type='user')
        user.put()
        sup = User.create(email='super@perts.net', user_type='super_admin')
        sup.put()
        data = {'foo': 'bar'}
        ds = Dataset.create(
            content_type='application/json',
            filename='script.date.unit_id',
            parent_id=None,
            data=data,
        )
        ds.put()

        # Non supers forbidden.
        self.testapp.get(
            '/api/datasets/{}'.format(ds.uid),
            headers=jwt_headers(user),
            status=403,
        )

        # Supers succeed
        response = self.testapp.get(
            '/api/datasets/{}'.format(ds.uid),
            headers=jwt_headers(sup),
        )
        self.assertEqual(json.loads(response.body), data)

    def test_get_dataset_requires_auth(self):
        """Getting data w/o token requires Authorization header."""
        self.testapp.get(
            '/api/datasets/Dataset_foo',
            status=401,
        )

    def test_get_dataset_with_token(self):
        """Jwt with allowed_endpoints gives permission on dataset."""
        data = {'foo': 'bar'}
        ds = Dataset.create(
            content_type='application/json',
            filename='script.date.unit_id',
            parent_id=None,
            data=data,
        )
        ds.put()

        path = '/api/datasets/{}'.format(ds.uid)

        # An otherwise valid token, but without the right endpoint, forbidden.
        empty_token = jwt_helper.encode({})
        response = self.testapp.get(
            '{}?token={}'.format(path, empty_token),
            status=403,
        )

        endpoint = BaseHandler.__dict__['get_endpoint_str'](
            None,  # dummy for "self" in instance method
            method='GET',
            path=path,
        )
        token = jwt_helper.encode({'allowed_endpoints': [endpoint]})

        # Explicit permission on this endpoint succeeds.
        response = self.testapp.get('{}?token={}'.format(path, token))
        self.assertEqual(json.loads(response.body), data)

    def test_get_dataset_with_parent(self):
        """Can get dataset if you own the parent."""
        org_id = 'Organization_foo'
        pc = ProjectCohort.create(
            organization_id=org_id,
            program_label='demo-program',
            cohort_label='2018',
            project_id='Project_foo',
        )
        pc.put()
        user = User.create(email='demo@perts.net', user_type='user')
        user.put()
        owner = User.create(email='owner@perts.net', user_type='user',
                            owned_organizations=[org_id])
        owner.put()
        data = {'foo': 'bar'}

        ds = Dataset.create(
            content_type='application/json',
            filename='script.date.unit_id',
            parent_id=pc.uid,  # only one user owns this
            data=data,
        )
        ds.put()

        # Non owners forbidden
        self.testapp.get(
            '/api/datasets/{}'.format(ds.uid),
            headers=jwt_headers(user),
            status=403,
        )

        # Owner succeeds
        response = self.testapp.get(
            '/api/datasets/{}'.format(ds.uid),
            headers=jwt_headers(owner),
        )
        self.assertEqual(json.loads(response.body), data)

    def test_view_dataset(self):
        """Load a ViewHandler with a specified dataset and template."""
        user = User.create(email='demo@perts.net', user_type='user')
        user.put()
        sup = User.create(email='super@perts.net', user_type='super_admin')
        sup.put()
        data = {'foo': 'bar'}
        ds = Dataset.create(
            content_type='application/json',
            filename='script.date.unit_id',
            parent_id=None,  # should be restricted to supers
            data=data,
        )
        ds.put()

        # passthrough.html is a template that just echos the data
        path = '/datasets/{}/{}/{}'.format(ds.uid, 'passthrough', ds.filename)

        # Viewing datasets with a template should have exactly the same
        # permissions as getting through the api.
        self.testapp.get(path, headers=jwt_headers(user), status=403)

        response = self.testapp.get(path, headers=jwt_headers(sup))
        self.assertIn(json.dumps(data), response.body)

    def test_query_parentless_datasets(self):
        """Should be possible to list datasets with no parent."""
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()
        data = {'foo': 'bar'}
        ds1 = Dataset.create(
            content_type='application/json',
            filename='script.date.unit_id',
            parent_id=None,
            data=data,
        )
        ds2 = Dataset.create(
            content_type='application/json',
            filename='script.date.unit_id',
            parent_id=None,
            data=data,
        )
        ds3 = Dataset.create(
            content_type='application/json',
            filename='script.date.unit_id',
            parent_id='ProjectCohort_foo',
            data=data,
        )
        ndb.put_multi((ds1, ds2, ds3))

        response = self.testapp.get(
            '/api/datasets?has_parent=false',
            headers=jwt_headers(user),
        )
        self.assertEqual(len(json.loads(response.body)), 2)
