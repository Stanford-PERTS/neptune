import datetime
import json
import logging
import unittest
import webapp2
import webtest

from api_handlers import api_routes
from collections import OrderedDict
from model import Program, User
from unit_test_helper import ConsistencyTestCase, login_headers
import config


class TestGraphQLProgramCohort(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    cohorts = {
        '2017': {
            'close_date': '2018-05-16',
            'label': '2017',
            'name': u"{apos}17-{apos}18".format(apos=u"\u02BC"),
            'open_date': '2017-03-06',
            'registration_close_date': '2018-05-02',
            'registration_open_date': '2017-01-01',
        },
        '2018': {
            'close_date': '2019-05-16',
            'label': '2018',
            'name': u"{apos}18-{apos}19".format(apos=u"\u02BC"),
            'open_date': '2018-06-01',
            'registration_close_date': '2019-05-02',
            'registration_open_date': '2018-03-30',
        },
    }

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestGraphQLProgramCohort, self).set_up()

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

        Program.mock_program_config('demo-program', {'cohorts': self.cohorts})

    def tearDown(self):
        Program.reset_mocks()
        super(TestGraphQLProgramCohort, self).tearDown()

    def test_get_single_cohort(self):
        user = User.create(email="super@example.com", user_type='super_admin')
        user.put()

        query = '''
        query GetSingleProgramCohort(
            $program_label: String!,
            $cohort_label: String!,
        ) {
            program_cohort(
                program_label: $program_label,
                cohort_label: $cohort_label,
            ) {
                close_date
                label
                name
                open_date
                program_description
                program_label
                program_name
                registration_close_date
                registration_open_date
            }
        }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            # See http://graphql.org/learn/serving-over-http/#post-request
            {
                'query': query,
                'variables': {
                    'program_label': 'demo-program',
                    'cohort_label': '2018',
                },
            },
            headers=login_headers(user.uid),
        )

        conf = Program.get_config('demo-program')
        cohort = conf['cohorts']['2018']
        cohort['program_label'] = conf['label']
        cohort['program_name'] = conf['name']
        cohort = OrderedDict((k, cohort[k]) for k in sorted(cohort.keys()))

        self.assertEqual(
            response.body,
            json.dumps({'program_cohort': cohort}),
        )

    def test_get_all_for_program(self):
        user = User.create(email="super@example.com", user_type='super_admin')
        user.put()

        query = '''
        query GetProgramCohorts($program_label: String!) {
            program_cohorts(program_label: $program_label) {
                label
            }
        }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            {'query': query, 'variables': {'program_label': 'demo-program'}},
            headers=login_headers(user.uid),
        )
        received = json.loads(response.body)

        for l in Program.get_config('demo-program')['cohorts'].keys():
            self.assertIn({'label': l}, received['program_cohorts'])
