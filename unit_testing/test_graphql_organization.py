import json
import logging
import unittest
import webapp2
import webtest

from api_handlers import api_routes
from model import User, Organization
from unit_test_helper import ConsistencyTestCase, login_headers
import config


class TestGraphQLOrganization(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestGraphQLOrganization, self).set_up()

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

    def test_get_single_org(self):
        user = User.create(email="super@example.com", user_type='super_admin')
        user.put()

        org = Organization.create(
            country='USA',
            google_maps_place_id='123',
            liaison_id='User_123',
            mailing_address='555 Quebec Ave',
            name="Org Foo",
            notes="Nice place.",
            phone_number="+1 (555) 555-5555",
            postal_code="12345",
            state="WA",
            status="approved",
            website_url="https://www.example.com",
        )
        org.put()

        query = '''
        query GetSingleOrg($uid: String!) {
            organization(uid: $uid) {
                country
                created
                deleted
                google_maps_place_id
                ipeds_id
                liaison_id
                mailing_address
                modified
                name
                nces_district_id
                nces_school_id
                notes
                ope_id
                phone_number
                poid
                postal_code
                short_uid
                state
                status
                uid
                website_url
            }
        }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            # See http://graphql.org/learn/serving-over-http/#post-request
            {
                'query': query,
                'variables': {'uid': org.uid},
            },
            headers=login_headers(user.uid),
        )

        self.assertEqual(
            response.body,
            json.dumps({'organization': org.to_client_dict()}),
        )

    def test_get_all_orgs(self):
        user = User.create(email="super@example.com", user_type='super_admin')
        user.put()

        org1 = Organization.create(name="Org Foo")
        org2 = Organization.create(name="Org Bar")
        org1.put()
        org2.put()

        query = '''
        query GetAllOrganizations {
            organizations {
                uid
            }
        }
        '''

        expected = {
            'organizations': [
                # Should be ordered by name.
                {'uid': org2.uid},
                {'uid': org1.uid},
            ]
        }

        response = self.testapp.post_json(
            '/api/graphql',
            {'query': query},
            headers=login_headers(user.uid),
        )

        self.assertEqual(json.loads(response.body), expected)
