import json
import logging
import webapp2
import webtest

from api_handlers import api_routes
from google.appengine.api import memcache
from model import User
from unit_test_helper import ConsistencyTestCase
import config
import jwt_helper
import model
import organization_tasks
import util


class TestApiSetPassword(ConsistencyTestCase):
    """Test responses of /api/set_password."""

    # Everything here should be getting users by id and thus strongly
    # consistent.
    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiSetPassword, self).set_up()

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

        # Tone down the intense number of hashing rounds for passwords so our
        # unit tests are fast.
        User.password_hashing_context.update(
            sha512_crypt__default_rounds=1000,
            sha256_crypt__default_rounds=1000,
        )

    def login_headers(self, user):
        payload = {'user_id': user.uid, 'email': user.email}
        return {'Authorization': 'Bearer ' + jwt_helper.encode(payload)}

    def test_request_register_bad_domain(self):
        response = self.testapp.post_json(
            '/api/register',
            {
                "email": "perts01@mailinator.com",
                "domain": "http://www.evil.com",
                "template_prefix": "neptune",
            },
            status=500,
        )
        self.assertTrue('SetPasswordDomainForbidden' in response.body)

    def test_request_reset_bad_domain(self):
        response = self.testapp.post_json(
            '/api/reset_password',
            {
                "email": "perts01@mailinator.com",
                "domain": "http://www.evil.com",
                "template_prefix": "neptune",
            },
            status=500,
        )
        self.assertTrue('SetPasswordDomainForbidden' in response.body)

    def test_exists_success(self):
        """Valid token and password, user exists."""
        user = User.create(email='foo@perts.net')
        user.put()
        user.key.get()  # force consistency, e.g. user waits for email
        response = self.testapp.post_json(
            '/api/set_password',
            {'password': '1231231231'},
            headers=self.login_headers(user),
        )
        user_dict = json.loads(response.body)
        self.assertEqual(type(user_dict), dict)
        self.assertEqual(user_dict['uid'], user.uid)

    def test_new_success(self):
        """Valid token and password, user is new."""
        # User.create() actually hits the db with a Unique entity, so we can't
        # use that to make a user.
        payload = {'user_id': 'User_foo', 'email': 'foo@perts.net'}
        token = jwt_helper.encode(payload)

        response = self.testapp.post_json(
            '/api/set_password',
            {'password': '1231231231'},
            headers={'Authorization': 'Bearer ' + token}
        )
        user_dict = json.loads(response.body)
        self.assertEqual(type(user_dict), dict)
        self.assertEqual(user_dict['uid'], payload['user_id'])

        # should now be in the db
        self.assertIsNotNone(User.get_by_id(payload['user_id']))

        return token

    def test_set_properties(self):
        """Some user props in the call should be set on the user."""
        user = User.create(email='foo@perts.net')
        user.put()
        user.key.get()  # force consistency, e.g. user waits for email
        params = {'password': '1231231231', 'name': 'foo',
                  'phone_number': '123'}
        response = self.testapp.post_json(
            '/api/set_password',
            params,
            headers=self.login_headers(user),
        )
        user_dict = json.loads(response.body)
        self.assertEqual(user_dict['name'], params['name'])
        self.assertEqual(user_dict['phone_number'], params['phone_number'])

    def test_bad_password(self):
        """Password doesn't match regex."""
        user = User.create(email='foo@perts.net')
        user.put()
        user.key.get()  # force consistency, e.g. user waits for email
        response = self.testapp.post_json(
            '/api/set_password',
            {'password': '123'},
            headers=self.login_headers(user),
            status=400,
        )

    def test_used_token(self):
        """Invalid token: has already been used."""
        user = User.create(email='foo@perts.net')
        user.put()
        user.key.get()  # force consistency, e.g. user waits for email
        header = self.login_headers(user)
        self.testapp.post_json(
            '/api/set_password',
            {'password': '1231231231'},
            headers=header,
        )

        # Grab the timestamp from when the server saw the token; it should have
        # only one entry.
        expiration = memcache.get('jwt_jtis').values()[0]

        # now do it again
        response = self.testapp.post_json(
            '/api/set_password',
            {'password': '1231231231'},
            headers=header,  # use the same token in the auth header
            status=401,
        )
        self.assertEqual(
            json.loads(response.body),
            'used ' + util.datelike_to_iso_string(expiration)
        )

    def test_expired_token(self):
        """Invalid token: expired."""
        payload = {'user_id': 'User_foo', 'email': 'foo@perts.net'}
        token = jwt_helper.encode(payload, expiration_minutes=-1)
        response = self.testapp.post_json(
            '/api/set_password',
            {'password': '1231231231'},
            headers={'Authorization': 'Bearer ' + token},
            status=401,
        )
        self.assertEqual(json.loads(response.body), 'expired')

    def test_bad_token(self):
        """Invalid token: decoding error b/c typo or bad secret."""
        payload = {'user_id': 'User_foo', 'email': 'foo@perts.net'}
        token = jwt_helper.encode(payload, expiration_minutes=-1)
        response = self.testapp.post_json(
            '/api/set_password',
            {'password': '1231231231'},
            headers={'Authorization': 'Bearer ' + token[:-1]},
            status=401,
        )
        self.assertEqual(json.loads(response.body), 'not found')

    # @todo(chris): fill these out when we merge master and neptune-dev.
    def test_precheck_auth_token_valid(self):
        pass

    def test_precheck_auth_token_not_found(self):
        pass

    def test_precheck_auth_token_expired(self):
        pass

    def test_precheck_auth_token_used(self):
        pass

    def test_precheck_jwt_valid(self):
        user = User.create(email='foo@perts.net')
        user.put()

        response = self.testapp.get(
            '/api/auth_tokens/{}/user'.format(jwt_helper.encode_user(user)),
        )
        user_dict = json.loads(response.body)
        self.assertEqual(type(user_dict), dict)
        self.assertEqual(user_dict['uid'], user.uid)

        # jti not cached
        self.assertIsNone(memcache.get('jwt_jtis'))

    def test_precheck_jwt_not_found(self):
        response = self.testapp.get(
            '/api/auth_tokens/{}/user'.format('dne'),
            status=404,
        )
        self.assertEqual(json.loads(response.body), 'not found')

    def test_precheck_jwt_expired(self):
        payload = {'user_id': 'User_foo', 'email': 'foo@perts.net'}
        token = jwt_helper.encode(payload, expiration_minutes=-1)
        response = self.testapp.get(
            '/api/auth_tokens/{}/user'.format(token),
            status=410,
        )
        self.assertEqual(json.loads(response.body), 'expired')

    def test_precheck_jwt_used(self):
        token = self.test_new_success()  # should use the token
        response = self.testapp.get(
            '/api/auth_tokens/{}/user'.format(token),
            status=410,
        )

        # Grab the timestamp from when the server saw the token; it should have
        # only one entry.
        expiration = memcache.get('jwt_jtis').values()[0]
        self.assertEqual(
            json.loads(response.body),
            'used ' + util.datelike_to_iso_string(expiration)
        )
