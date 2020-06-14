# -*- coding: utf-8 -*-
import logging
import unittest
import urlparse
import webapp2
import webtest

from api_handlers import api_routes
from gae_models import Email
from model import AuthToken, Program, User
from unit_test_helper import ConsistencyTestCase, jwt_headers
from webapp2_extras.appengine.auth.models import Unique
import config
import json


class TestApiAuthentication(ConsistencyTestCase):

    # We're not interested in how accurately we can retrieve users immediately
    # after saving, so simulate a fully consistent datastore.
    consistency_probability = 1

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    program_name = 'Demo Program'
    program_label = 'demo-program'
    cohort_label = '2018'

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiAuthentication, self).set_up()

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

        # Should be able to register with a legit cohort. Make sure it exists.
        Program.mock_program_config(
            self.program_label,
            {
                'name': self.program_name,
                'cohorts': {self.cohort_label: {'name': self.cohort_label}}
            },
        )

    def tear_down(self):
        Program.reset_mocks()

    def test_register_as_public(self):
        email = 'test@example.com'
        password = 'föô4567890'
        user = User.create(email=email)
        user.put()
        token = AuthToken.create_or_renew(user.uid)
        token.put()

        response = self.testapp.post_json(
            '/api/set_password',
            {'auth_token': token.token, 'password': password, 'name': 'Ôlaf',
             'phone_number': '123-123-1234'}
        )
        response_user = json.loads(response.body)
        self.assertRegexpMatches(response_user['uid'], r'^User_')

    def test_register_bad_password(self):
        email = 'test@example.com'
        password = 'short'
        user = User.create(email=email)
        user.put()
        token = AuthToken.create_or_renew(user.uid)
        token.put()

        response = self.testapp.post_json(
            '/api/set_password',
            {'auth_token': token.token, 'password': password, 'name': 'Ôlaf',
             'phone_number': '123-123-1234'},
            status=400
        )
        response_dict = json.loads(response.body)
        self.assertEqual(response_dict, 'bad_password')

    def test_register_no_cohort(self):
        email = 'test@example.com'

        response = self.testapp.post_json(
            '/api/register',
            {
                'email': email,
                'password': 'battery staple',
                'role': 'principal',
                'platform': 'neptune',
                'domain': 'http://localhost:8888',
                'program_label': self.program_label,
                # no cohort
            },
            status=204,
        )

        # User now exists
        user = User.get_by_auth('email', email)
        self.assertIsNotNone(user)

        # Email was created
        emails = Email.get(to_address=email)
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0].mandrill_template, 'neptune-register-new')

    def test_register_exists(self):
        email_addr = 'test@example.com'
        role = 'principal'
        utm_source = 'foo source'

        user = User.create(email=email_addr, hashed_password='foo')
        user.put()

        response = self.testapp.post_json(
            '/api/register',
            {
                'email': email_addr,
                'role': role,
                'program_label': self.program_label,
                'cohort': self.cohort_label,
                'utm_source': utm_source,
            },
            status=204,
        )

        # Email was created
        emails = Email.get(to_address=email_addr)
        self.assertEqual(len(emails), 1)

        # Email has correct data.
        email = emails[0]
        self.assertEqual(email.mandrill_template, 'neptune-register-exists')
        self.assertEqual(
            email.mandrill_template_content['program_label'],
            self.program_label,
        )
        self.assertEqual(
            email.mandrill_template_content['program_name'],
            self.program_name,
        )

        # Link in email is correct.
        parts = urlparse.urlsplit(email.mandrill_template_content['link'])
        scheme, netloc, path, query_string, fragment = parts
        self.assertEqual(path, '/login')
        query_params = dict(urlparse.parse_qsl(query_string))
        self.assertEqual(
            query_params,
            {
                'email': email_addr,
                'program': self.program_label,
                'cohort': self.cohort_label,
                'utm_source': utm_source,
            }
        )

    def test_register_new(self):
        email_addr = 'test@example.com'
        role = 'principal'
        utm_source = 'foo source'

        response = self.testapp.post_json(
            '/api/register',
            {
                'email': email_addr,
                'role': role,
                'program_label': self.program_label,
                'cohort': self.cohort_label,
                'utm_source': utm_source,
            },
            status=204,
        )

        # User now exists
        user = User.get_by_auth('email', email_addr)
        self.assertIsNotNone(user)
        self.assertEqual(user.role, role)

        # Email was created
        emails = Email.get(to_address=email_addr)
        self.assertEqual(len(emails), 1)

        # Email has correct data.
        email = emails[0]
        self.assertEqual(email.mandrill_template, 'neptune-register-new')
        self.assertEqual(
            email.mandrill_template_content['program_label'],
            self.program_label,
        )
        self.assertEqual(
            email.mandrill_template_content['program_name'],
            self.program_name,
        )
        exp_str = email.mandrill_template_content['expiration_datetime']
        self.assertEqual(type(exp_str), unicode)
        self.assertGreater(len(exp_str), 0)

        # Link in email has correct query string.
        parts = urlparse.urlsplit(email.mandrill_template_content['link'])
        scheme, netloc, path, query_string, fragment = parts
        query_params = dict(urlparse.parse_qsl(query_string))

        self.assertTrue('/set_password' in path)
        self.assertEqual(
            query_params,
            {
                'program': self.program_label,
                'cohort': self.cohort_label,
                'utm_source': utm_source,
            }
        )

    def test_register_pending(self):
        email_addr = 'test@example.com'
        role = 'principal'
        utm_source = 'foo source'

        user = User.create(email=email_addr)
        user.put()

        response = self.testapp.post_json(
            '/api/register',
            {
                'email': email_addr,
                'role': role,
                'program_label': self.program_label,
                'cohort': self.cohort_label,
                'utm_source': utm_source,
            },
            status=204,
        )

        # Email was created
        emails = Email.get(to_address=email_addr)
        self.assertEqual(len(emails), 1)

        # Email has correct data.
        email = emails[0]
        self.assertEqual(email.mandrill_template, 'neptune-register-pending')
        self.assertEqual(
            email.mandrill_template_content['program_label'],
            self.program_label,
        )
        self.assertEqual(
            email.mandrill_template_content['program_name'],
            self.program_name,
        )
        exp_str = email.mandrill_template_content['expiration_datetime']
        self.assertEqual(type(exp_str), unicode)
        self.assertGreater(len(exp_str), 0)

        # Link in email is correct.
        parts = urlparse.urlsplit(email.mandrill_template_content['link'])
        scheme, netloc, path, query_string, fragment = parts
        self.assertTrue('/set_password' in path)
        query_params = dict(urlparse.parse_qsl(query_string))
        self.assertEqual(
            query_params,
            {
                'program': self.program_label,
                'cohort': self.cohort_label,
                'utm_source': utm_source,
            }
        )

    def test_invite_triton_new(self):
        inviter = User.create(email='inviter@user.com')
        inviter.put()
        invitee_email = 'invitee@user.com',

        response = self.testapp.post_json(
            '/api/invitations',
            {
                'email': invitee_email,
                'platform': 'triton',
                'template_content': {'foo': 'bar'},
                'domain': 'https://copilot.perts.net',
                'from_address': 'copilot@perts.net',
                'from_name': 'Copilot',
                'reply_to': 'copilot@perts.net',
            },
            headers=jwt_headers(inviter),
        )
        response_user = json.loads(response.body)
        self.assertRegexpMatches(response_user['uid'], r'^User_')

        # One email queued.
        emails = Email.get()
        self.assertEqual(len(emails), 1)
        email = emails[0]

        # To the right person.
        email.to = invitee_email

        # With the right template.
        self.assertEqual(email.mandrill_template, 'triton-invite-new')

        # And right template params.
        for k in ('expiration_datetime', 'link', 'foo'):
            self.assertEqual(type(email.mandrill_template_content[k]), unicode)
            self.assertGreater(len(email.mandrill_template_content[k]), 0)

    def test_invite_triton_exists(self):
        inviter = User.create(email='inviter@user.com')
        inviter.put()
        invitee = User.create(email='invitee@user.com', hashed_password='foo')
        invitee.put()

        response = self.testapp.post_json(
            '/api/invitations',
            {
                'email': invitee.email,
                'platform': 'triton',
                'template_content': {'foo': 'bar'},
                'domain': 'https://copilot.perts.net',
                'from_address': 'copilot@perts.net',
                'from_name': 'Copilot',
                'reply_to': 'copilot@perts.net',
            },
            headers=jwt_headers(inviter),
        )
        response_user = json.loads(response.body)
        self.assertRegexpMatches(response_user['uid'], r'^User_')

        # One email queued.
        emails = Email.get()
        self.assertEqual(len(emails), 1)
        email = emails[0]

        # To the right person.
        email.to = invitee.email

        # With the right template.
        self.assertEqual(email.mandrill_template, 'triton-invite-exists')

        # And right template params.
        self.assertEqual(type(email.mandrill_template_content['foo']), unicode)
        self.assertGreater(len(email.mandrill_template_content['foo']), 0)

        self.assertIn('/login', email.mandrill_template_content['link'])

    def test_register_triton_exists(self):
        email_addr = 'test@example.com'
        utm_source = 'foo source'

        user = User.create(email=email_addr, hashed_password='foo')
        user.put()

        response = self.testapp.post_json(
            '/api/register',
            {
                'domain': 'https://copilot.perts.net',
                'platform': 'triton',
                'email': email_addr,
                'program_label': self.program_label,
                'utm_source': utm_source,
            },
            status=204,
        )

        # Email was created
        emails = Email.get(to_address=email_addr)
        self.assertEqual(len(emails), 1)

        # Email has correct data.
        email = emails[0]
        self.assertEqual(email.mandrill_template, 'triton-register-exists')
        self.assertEqual(
            email.mandrill_template_content['program_label'],
            self.program_label,
        )
        self.assertEqual(
            email.mandrill_template_content['program_name'],
            self.program_name,
        )

        # Link in email is correct.
        parts = urlparse.urlsplit(email.mandrill_template_content['link'])
        scheme, netloc, path, query_string, fragment = parts
        self.assertEqual(netloc, 'copilot.perts.net')
        self.assertEqual(path, '/login')
        query_params = dict(urlparse.parse_qsl(query_string))
        self.assertEqual(
            query_params,
            {
                'email': email_addr,
                'program': self.program_label,
                'utm_source': utm_source,
            }
        )

    def test_register_triton_new(self):
        email_addr = 'test@example.com'
        utm_source = 'foo source'

        response = self.testapp.post_json(
            '/api/register',
            {
                'domain': 'https://copilot.perts.net',
                'platform': 'triton',
                'email': email_addr,
                'program_label': self.program_label,
                'utm_source': utm_source,
            },
            status=204,
        )

        # User now exists
        user = User.get_by_auth('email', email_addr)
        self.assertIsNotNone(user)

        # Email was created
        emails = Email.get(to_address=email_addr)
        self.assertEqual(len(emails), 1)

        # Email has correct data.
        email = emails[0]
        self.assertEqual(email.mandrill_template, 'triton-register-new')
        self.assertEqual(
            email.mandrill_template_content['program_label'],
            self.program_label,
        )
        self.assertEqual(
            email.mandrill_template_content['program_name'],
            self.program_name,
        )
        exp_str = email.mandrill_template_content['expiration_datetime']
        self.assertEqual(type(exp_str), unicode)
        self.assertGreater(len(exp_str), 0)


        # Link in email has correct query string.
        parts = urlparse.urlsplit(email.mandrill_template_content['link'])
        scheme, netloc, path, query_string, fragment = parts
        query_params = dict(urlparse.parse_qsl(query_string))

        self.assertEqual(netloc, 'copilot.perts.net')
        self.assertTrue('/set_password' in path)
        self.assertEqual(
            query_params,
            {
                'program': self.program_label,
                'utm_source': utm_source,
            }
        )

    def test_register_triton_pending(self):
        email_addr = 'test@example.com'
        utm_source = 'foo source'

        user = User.create(email=email_addr)
        user.put()

        response = self.testapp.post_json(
            '/api/register',
            {
                'platform': 'triton',
                'domain': 'https://copilot.perts.net',
                'email': email_addr,
                'program_label': self.program_label,
                'utm_source': utm_source,
            },
            status=204,
        )

        # Email was created
        emails = Email.get(to_address=email_addr)
        self.assertEqual(len(emails), 1)

        # Email has correct data.
        email = emails[0]
        self.assertEqual(email.mandrill_template, 'triton-register-pending')
        self.assertEqual(
            email.mandrill_template_content['program_label'],
            self.program_label,
        )
        self.assertEqual(
            email.mandrill_template_content['program_name'],
            self.program_name,
        )
        exp_str = email.mandrill_template_content['expiration_datetime']
        self.assertEqual(type(exp_str), unicode)
        self.assertGreater(len(exp_str), 0)

        # Link in email is correct.
        parts = urlparse.urlsplit(email.mandrill_template_content['link'])
        scheme, netloc, path, query_string, fragment = parts
        self.assertEqual(netloc, 'copilot.perts.net')
        self.assertTrue('/set_password' in path)
        query_params = dict(urlparse.parse_qsl(query_string))
        self.assertEqual(
            query_params,
            {
                'program': self.program_label,
                'utm_source': utm_source,
            }
        )

    def test_default_sender(self):
        email_addr = 'test@example.com'
        sender = config.from_server_email_address

        response = self.testapp.post_json(
            '/api/register',
            {
                'domain': 'https://neptune.perts.net',
                # no platform, defaults to Neptune
                'email': email_addr,
                'program_label': self.program_label,
            },
            status=204,
        )

        # Email was created with from/reply properties.
        emails = Email.get(to_address=email_addr)
        email = emails[0]
        self.assertEqual(
            email.mandrill_template_content['contact_email_address'],
            sender,
        )
        self.assertEqual(email.from_address, sender)
        self.assertEqual(email.reply_to, sender)
        # Should be hard-coded in api_helper
        self.assertEqual(email.from_name, 'PERTS')

    def test_custom_sender(self):
        # Mock a program that defines a special contact email address.
        program_label = 'ep'
        sender = 'copilot@perts.net'
        Program.mock_program_config(
            program_label,
            {
                'name': 'Engagement Project',
                'contact_email_address': sender,
            },
        )

        email_addr = 'test@example.com'

        response = self.testapp.post_json(
            '/api/register',
            {
                'domain': 'https://copilot.perts.net',
                'platform': 'triton',
                'email': email_addr,
                'program_label': program_label,
            },
            status=204,
        )

        # Email was created with from/reply properties.
        emails = Email.get(to_address=email_addr)
        email = emails[0]
        self.assertEqual(
            email.mandrill_template_content['contact_email_address'],
            sender,
        )
        self.assertEqual(email.from_address, sender)
        self.assertEqual(email.reply_to, sender)
        # Should be hard-coded in api_helper
        self.assertEqual(email.from_name, 'Copilot')

    def test_login_as_public(self):
        email = 'test@example.com'
        password = 'föô4567890'

        # Create an extra user to prove the query can differentiate.
        # N.B. since this is created first, User.get_by_auth() will prefer it
        # if it somehow matches on both.
        extra = User.create(email='extra@example.com')
        extra.hashed_password = User.hash_password(password)
        extra.put()

        # Create the user we'll login as.
        user = User.create(email=email)
        user.hashed_password = User.hash_password(password)
        user.put()

        response = self.testapp.post_json(
            '/api/login',
            {'auth_type': 'email', 'email': email, 'password': password}
        )
        response_user = json.loads(response.body)
        self.assertEqual(response_user['uid'], user.uid)

    def test_login_multiple_matches(self):
        """Earliest created is preferred."""
        email = 'test@example.com'
        password = 'föô4567890'

        user1 = User.create(email=email)
        user1.hashed_password = User.hash_password(password)
        user1.put()

        # We'll have to hack around our protections against this sort of thing
        # so we can test what will happen if the protections fail.
        Unique.query().get().key.delete()

        # Create the user we'll login as.
        user2 = User.create(email=email)
        user2.hashed_password = User.hash_password(password)
        user2.put()

        response = self.testapp.post_json(
            '/api/login',
            {'auth_type': 'email', 'email': email, 'password': password}
        )
        response_user = json.loads(response.body)
        self.assertEqual(response_user['uid'], user1.uid)

    def test_login_bad_password(self):
        email = 'test@example.com'
        password = 'föô4567890'
        user = User.create(email=email)
        user.hashed_password = User.hash_password(password)
        user.put()

        response = self.testapp.post_json(
            '/api/login',
            {'auth_type': 'email', 'email': email, 'password': 'wrong'},
            status=401,
        )
        response_dict = json.loads(response.body)
        self.assertEqual(
            response_dict, 'credentials_invalid')

    def test_login_unknown_email(self):
        response = self.testapp.post_json(
            '/api/login',
            {'auth_type': 'email', 'email': 'dne', 'password': 'foo'},
            status=401,
        )
        response_dict = json.loads(response.body)
        self.assertEqual(
            response_dict, 'credentials_invalid')

    @unittest.skip("Pending webpackification")
    def test_login_missing_data(self):
        response = self.testapp.post_json(
            '/api/login',
            {'auth_type': 'email'},
            status=401,
        )
        response_dict = json.loads(response.body)
        self.assertEqual(
            response_dict, 'credentials_missing')
