"""Test reading surveys with GraphQL."""

import json
import logging
import unittest
import webapp2
import webtest

from api_handlers import api_routes
from unit_test_helper import ConsistencyTestCase, login_headers
from model import User, Survey
import config


class TestGraphQLSurvey(ConsistencyTestCase):
    """Test features of project cohort entities."""

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    program_label = 'demo-program'

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestGraphQLSurvey, self).set_up()

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

    def create_surveys(self):
        tasklist_template = []

        survey1 = Survey.create(
            tasklist_template,
            program_label=self.program_label,
            organization_id='Organization_Foo',
            project_cohort_id='ProjectCohort_Foo',
            ordinal=1,
        )
        survey2 = Survey.create(
            tasklist_template,
            program_label=self.program_label,
            organization_id='Organization_Foo',
            project_cohort_id='ProjectCohort_Foo',
            ordinal=2,
        )
        survey1.put()
        survey2.put()

        # Simulate consistency.
        survey1.key.get()
        survey2.key.get()

        return survey1, survey2

    def test_super_single(self):
        surveys = self.create_surveys()
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()

        query = '''
            query GetSingleSurvey($uid: String) {
                survey(uid: $uid) {
                    cohort_label
                    created
                    deleted
                    liaison_id
                    modified
                    name
                    ordinal
                    organization_id
                    program_label
                    project_cohort_id
                    project_id
                    short_uid
                    status
                    uid
                }
            }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            {
                'query': query,
                'variables': {'uid': surveys[0].uid},
            },
            headers=login_headers(user.uid),
        )

        self.assertEqual(
            response.body,
            json.dumps({'survey': surveys[0].to_client_dict()}),
        )

    def test_get_all_surveys(self):
        surveys = self.create_surveys()
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()

        query = '''
        query GetAllSurveys {
            surveys {
                uid
            }
        }
        '''

        expected = {
            # Should be ordered by ordinal
            'surveys': [{"uid": s.uid} for s in surveys],
        }

        response = self.testapp.post_json(
            '/api/graphql',
            {'query': query},
            headers=login_headers(user.uid),
        )

        self.assertEqual(response.body, json.dumps(expected))
