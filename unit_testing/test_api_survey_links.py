"""Test accessing survey link entities."""

import json
import logging
import webapp2
import webtest

from api_handlers import api_routes
from unit_test_helper import ConsistencyTestCase
from model import SurveyLink
import config


class TestApiSurveyLinks(ConsistencyTestCase):
    """Test survey-link-issuing API."""

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        super(TestApiSurveyLinks, self).set_up()

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

    def test_get_unique(self):
        """Unauthed participants can get unique survey links."""
        program_label = 'demo-program'
        url = 'https://sshs.qualtrics.com/SE?Q_DL=foobar_foobar_MLRP_foobar&Q_CHL=gl'
        sl = SurveyLink(id=url, program_label=program_label, survey_ordinal=1)
        sl.put()
        # Survey links have time to become consistent as they are uploaded well
        # ahead of participation.
        sl.key.get()

        response = self.testapp.post_json(
            '/api/survey_links/demo-program/1/get_unique',
            {'program_label': program_label, 'survey_ordinal': 1},
        )
        response_dict = json.loads(response.body)
        expected = {
            'program_label': program_label,
            'survey_ordinal': 1,
            'url': url,
        }
        self.assertEqual(expected, response_dict)
