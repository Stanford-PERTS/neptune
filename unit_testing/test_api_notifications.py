from google.appengine.ext import ndb
import datetime
import json
import logging
import webapp2
import webtest

from api_handlers import api_routes
from model import User, Notification
from unit_test_helper import ConsistencyTestCase, login_headers
import config


class TestApiOrganization(ConsistencyTestCase):

    # Not interested in how quickly the notifications come in.
    consistency_probability = 1

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiOrganization, self).set_up()

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

    def test_get_notifications(self):
        user = User.create(email='user@perts.net')
        user.put()
        admin = User.create(email='admin@pets.net', user_type='super_admin')
        admin.put()

        notes = [
            Notification.create(
                # intentionally created in reverse time order, to demonstrate
                # that we can query them in correct time order.
                created=datetime.datetime(2018, 8, 10 + x),
                parent=user,
                context_id='Org_foo',
                subject='Thing one.',
                body='The thing is thingish.',
                link='/organizations/foo',
            )
            for x in range(3)
        ]
        ndb.put_multi(notes)

        user_response = self.testapp.get(
            '/api/users/{}/notifications?dismissed=false'.format(user.uid),
            headers=login_headers(user.uid),
        )
        admin_response = self.testapp.get(
            '/api/notifications?dismissed=false',
            headers=login_headers(admin.uid),
        )

        # All responses should be ordered with newest first by default.
        for response in (user_response, admin_response):
            response_notes = json.loads(response.body)
            previous_time = response_notes[0]['created']
            for note_dict in response_notes[1:]:
                self.assertLess(note_dict['created'], previous_time)
                previous_time = note_dict['created']
