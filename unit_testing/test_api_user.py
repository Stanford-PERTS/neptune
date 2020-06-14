import json
import webapp2
import webtest

from api_handlers import api_routes
from model import User, Organization
from unit_test_helper import ConsistencyTestCase, login_headers
import config


class TestApiUser(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiUser, self).set_up()

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

    def test_join_organization_new(self):
        """User applies to org, uses the assc_organizations property."""
        org = Organization.create()
        user = User.create(email="test@example.com")
        org.put()
        user.put()

        response = self.testapp.post_json(
            '/api/users/{}/associated_organizations'.format(user.uid),
            org.to_client_dict(),
            headers=login_headers(user.uid)
        )
        response_dict = json.loads(response.body)
        self.assertEqual(response_dict['uid'], user.uid)
        self.assertIn(org.uid, response_dict['assc_organizations'])

    def test_join_organization_related(self):
        """Applying to an org is idempotent."""
        org = Organization.create()
        user = User.create(email="test@example.com",
                           assc_organizations=[org.uid])
        org.put()
        user.put()

        response = self.testapp.post_json(
            '/api/users/{}/associated_organizations'.format(user.uid),
            org.to_client_dict(),
            headers=login_headers(user.uid)
        )
        response_dict = json.loads(response.body)
        self.assertEqual(response_dict['uid'], user.uid)
        self.assertIn(org.uid, response_dict['assc_organizations'])
        self.assertEqual(len(response_dict['assc_organizations']), 1)

    def test_query_by_organization(self):
        """Get a list of users who own an org."""
        org = Organization.create()
        user = User.create(email="test@example.com",
                           owned_organizations=[org.uid])
        org.put()
        user.put()

        response = self.testapp.get(
            '/api/organizations/{}/users'.format(org.uid),
            headers=login_headers(user.uid)
        )
        response_list = json.loads(response.body)
        self.assertEqual(len(response_list), 1)
        self.assertEqual(response_list[0]['uid'], user.uid)

    def test_related_query_forbidden(self):
        """Can't query for owners of an org you don't own."""
        org = Organization.create()
        user = User.create(email="test@example.com")
        org.put()
        user.put()

        response = self.testapp.get(
            '/api/organizations/{}/users'.format(org.uid),
            headers=login_headers(user.uid),
            status=403
        )

    # @todo(chris): These next three operations should be happening through
    # /api/users/{id}/owned_organizations, which is the UsersOrganizations
    # handler.

    def test_add_owner_to_organization(self):
        """Existing org owner adds another user to org as owner."""
        org = Organization.create()
        owner = User.create(email="owner@example.com",
                            owned_organizations=[org.uid])
        joiner = User.create(email="joiner@example.com")
        org.put()
        owner.put()
        joiner.put()

        response = self.testapp.put(
            '/api/organizations/{}/users/{}'.format(org.uid, joiner.uid),
            headers=login_headers(owner.uid)
        )
        response_dict = json.loads(response.body)
        self.assertEqual(response_dict['uid'], joiner.uid)
        self.assertIn(org.uid, response_dict['owned_organizations'])

    def test_add_self_to_organization(self):
        """Can't give org ownership if you're not an owner."""
        org = Organization.create()
        joiner = User.create(email="joiner@example.com")
        org.put()
        joiner.put()

        response = self.testapp.put(
            '/api/organizations/{}/users/{}'.format(org.uid, joiner.uid),
            headers=login_headers(joiner.uid),
            status=403
        )

    def test_remove_self_from_organization(self):
        """User leaves an organization."""
        org = Organization.create()
        owner = User.create(email="owner@example.com",
                            owned_organizations=[org.uid])
        org.put()
        owner.put()

        response = self.testapp.delete(
            '/api/organizations/{}/users/{}'.format(org.uid, owner.uid),
            headers=login_headers(owner.uid)
        )
        response_dict = json.loads(response.body)
        self.assertEqual(response_dict['uid'], owner.uid)
        self.assertNotIn(org.uid, response_dict['owned_organizations'])

    def test_remove_other_from_organization(self):
        """One org admin removes another from an organization."""
        org = Organization.create()
        remover = User.create(email="remover@example.com",
                              owned_organizations=[org.uid])
        removee = User.create(email="removee@example.com",
                              owned_organizations=[org.uid])
        org.put()
        remover.put()
        removee.put()

        response = self.testapp.delete(
            '/api/organizations/{}/users/{}'.format(org.uid, removee.uid),
            headers=login_headers(remover.uid)
        )
        response_dict = json.loads(response.body)
        self.assertEqual(response_dict['uid'], removee.uid)
        self.assertNotIn(org.uid, response_dict['owned_organizations'])
