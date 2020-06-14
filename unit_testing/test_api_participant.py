import json
import logging
import webapp2
import webtest

from api_handlers import api_routes
from model import (
    AuthToken,
    Participant,
    ParticipantData,
    Program,
    ProjectCohort,
    Survey,
    User,
)
from unit_test_helper import ConsistencyTestCase, login_headers
import config
import mysql_connection


class TestApiParticipant(ConsistencyTestCase):
    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key
    program_label = 'demo-program'
    cohort_label = '2018'

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiParticipant, self).set_up()

        with mysql_connection.connect() as sql:
            sql.reset({
                'participant': Participant.get_table_definition(),
                'participant_data': ParticipantData.get_table_definition(),
            })

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

    def create_participant(self):
        p = Participant.create(name='Rene', organization_id='Org_Eruditorum')
        p.put()
        return p

    def test_get(self):
        p = self.create_participant()

        response = self.testapp.get(
            '/api/participants?name={}&organization_id={}'
            .format(p.name, p.organization_id)
        )
        self.assertIn('uid', json.loads(response.body)[0])

    def test_post_new(self):
        response = self.testapp.post_json(
            '/api/participants',
            {'name': 'Rene', 'organization_id': 'Org_Eruditorum'},
        )
        participant_id = json.loads(response.body)['uid']

        self.assertIsNotNone(Participant.get_by_id(participant_id))

    def test_post_duplicate(self):
        p = self.create_participant()

        response = self.testapp.post_json(
            '/api/participants',
            {'name': p.name, 'organization_id': p.organization_id},
            status=303,
        )

        self.assertIn(
            '/api/participants/{}'.format(p.uid),
            response.headers['Location'],
        )
