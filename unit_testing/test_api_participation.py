from google.appengine.api import memcache
from google.appengine.ext import ndb
import datetime
import json
import logging
import webapp2
import webtest

from api_handlers import api_routes
from gae_handlers import BaseHandler
from model import (
    Participant,
    ParticipantData,
    Program,
    ProjectCohort,
    User,
)
from test_participation import mock_one_finished_one_unfinished
from unit_test_helper import ConsistencyTestCase, jwt_headers
import config
import jwt_helper
import mysql_connection


def get_endpoint_str(method, platform, path):
    return BaseHandler.__dict__['get_endpoint_str'](
        None, method, platform, path)


class TestApiParticipation(ConsistencyTestCase):

    # We're not interested in how accurately we can retrieve data immediately
    # after saving, so simulate a fully consistent datastore.
    consistency_probability = 1

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key
    program_label = 'demo-program'
    cohort_label = '2018'

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiParticipation, self).set_up()

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

        # Successful download of completion ids triggers a notification, which
        # requires a cohort name.
        Program.mock_program_config(
            self.program_label,
            {'cohorts': {self.cohort_label: {'name': self.cohort_label}}},
        )

        with mysql_connection.connect() as sql:
            sql.reset({
                'participant': Participant.get_table_definition(),
                'participant_data': ParticipantData.get_table_definition(),
            })

    def tear_down(self):
        Program.reset_mocks()

    def test_survey_participation(self):
        org_id = 'Org_foo'
        user = User.create(email='org_admin@school.edu',
                           owned_organizations=[org_id])
        user.put()

        pds = mock_one_finished_one_unfinished(
            1,
            'Participant_unfinished',
            'Participant_finished',
            program_label=self.program_label,
            cohort_label=self.cohort_label,
            organization_id=org_id,
        )

        result = self.testapp.get(
            '/api/surveys/{}/participation'.format(pds[0].survey_id),
            headers=jwt_headers(user),
        )
        expected = [
            {"survey_ordinal": 1, "value": "1", "n": 1},
            {"survey_ordinal": 1, "value": "100", "n": 1},
        ]
        self.assertEqual(json.loads(result.body), expected)

    def test_batch_participation_subqueries(self):
        """Shouldn't fail if requested >30 pcs.

        See https://cloud.google.com/appengine/docs/standard/python/datastore/queries#Python_Property_filters
        """
        user = User.create(email='triton@perts.net')
        user.put()

        url = '/api/project_cohorts/participation?{}'.format(
            '&'.join(r'uid=cool%20cat{}'.format(x) for x in range(31))
        )

        self.testapp.get(
            url,
            headers=jwt_headers(user),
            status=404,  # breaking subqueries would respond with a 500
        )

    def test_batch_participation(self):
        user = User.create(email='triton@perts.net')
        user.put()

        pc_kwargs = {
            'program_label': self.program_label,
            'cohort_label': self.cohort_label,
        }
        pcs = [
            ProjectCohort.create(**pc_kwargs),
            ProjectCohort.create(**pc_kwargs),
        ]
        ndb.put_multi(pcs)

        all_pds = []
        for pc in pcs:
            pds = mock_one_finished_one_unfinished(
                1,
                'Participant_unfinished',
                'Participant_finished',
                pc_id=pc.uid,
                code=pc.code,
                program_label=self.program_label,
                cohort_label=self.cohort_label,
            )
            all_pds += pds

        # Forbidden without allowed endpoints.
        pc_ids = [pc.uid for pc in pcs]
        self.testapp.get(
            '/api/project_cohorts/participation?uid={}&uid={}'.format(*pc_ids),
            headers=jwt_headers(user),
            status=403
        )

        # Running various queries works as expected.
        self.batch_participation(user, pcs)

        # Simulate a new pd being written to the first pc by clearing that
        # memcache key. The server should fall back to sql and still give the
        # same results.
        id_key = ParticipantData.participation_by_pc_cache_key(pcs[0].uid)
        code_key = ParticipantData.participation_by_pc_cache_key(pcs[0].code)
        self.assertIsNotNone(memcache.get(id_key))
        self.assertIsNotNone(memcache.get(code_key))
        memcache.delete(id_key)
        memcache.delete(code_key)
        self.batch_participation(user, pcs)

        # Now with everything cached, clearing the db and running the same
        # queries again should have the same result.
        ParticipantData.delete_multi(all_pds)
        self.batch_participation(user, pcs)

    def batch_participation(self, user, pcs):
        # Successful with allowed endpoints for individual project cohorts
        # (even if the paths are different). Can use either uid or code.
        start = datetime.date.today()
        end = start + datetime.timedelta(days=1)
        for attr in ('uid', 'code'):
            ids = [getattr(pc, attr).replace(' ', '-') for pc in pcs]
            paths = ['/api/project_cohorts/{}/participation'
                     .format(id) for id in ids]

            payload = {
                'user_id': user.uid,
                'email': user.email,
                'allowed_endpoints': [get_endpoint_str('GET', 'neptune', p)
                                      for p in paths],
            }

            url = (
                '/api/project_cohorts/participation?'
                'uid={}&uid={}&start={start}&end={end}'
                .format(
                    *ids,
                    start=start.strftime(config.iso_datetime_format),
                    end=end.strftime(config.iso_datetime_format)
                )
            )

            result = self.testapp.get(
                url,
                headers={
                    'Authorization': 'Bearer ' + jwt_helper.encode(payload),
                },
            )
            expected = {
                getattr(pc, attr).replace(' ', '-'): [
                    {'project_cohort_id': pc.uid, 'survey_ordinal': 1, 'n': 1,
                     'value': '1', 'code': pc.code},
                    {'project_cohort_id': pc.uid, 'survey_ordinal': 1, 'n': 1,
                     'value': '100', 'code': pc.code},
                ]
                for pc in pcs
            }

            self.assertEqual(json.loads(result.body), expected)
