import unittest
import webtest
import webapp2

from model import User
from unit_test_helper import ConsistencyTestCase, login_headers
from view_handlers import view_routes
import config


class TestViews(ConsistencyTestCase):

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestViews, self).set_up()

        application = webapp2.WSGIApplication(
            view_routes,
            config={
                'webapp2_extras.sessions': {
                    'secret_key': config.default_session_cookie_secret_key
                }
            },
            debug=True
        )
        self.testapp = webtest.TestApp(application)

    @unittest.skip("Pending webpackification")
    def test_landing_page(self):
        response = self.testapp.get('/')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.normal_body[:15], '<!DOCTYPE html>')
        self.assertEqual(response.content_type, 'text/html')

    @unittest.skip("Pending webpackification")
    def test_register_page_as_public(self):
        response = self.testapp.get('/register')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.normal_body[:15], '<!DOCTYPE html>')
        self.assertEqual(response.content_type, 'text/html')

    @unittest.skip("Pending issue #19")
    def test_register_page_as_user(self):
        user = User.create(email='test@example.com')
        user.put()
        headers = login_headers(user.uid)

        response = self.testapp.get('/register', headers=headers)
        # Should redirect to the dashboard.
        self.assertEqual(response.status_int, 302)
        self.assertRegexpMatches(
            response.headers.get('Location'), r'/dashboard$')

    def test_user_dashboard_as_public(self):
        pass

    def test_user_dashboard_as_user(self):
        # log in user...
        pass

    def test_org_page_wo_access(self):
        # create an org to view...
        pass

    def test_org_page_w_access(self):
        # create an org to view...
        # log in user...
        pass
