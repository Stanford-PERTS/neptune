import datetime
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
from unit_test_helper import ConsistencyTestCase, login_headers, jwt_headers
import config
import mysql_connection
import util


class TestApiParticipantData(ConsistencyTestCase):

    # We're not interested in how accurately we can retrieve data immediately
    # after saving, so simulate a fully consistent datastore.
    consistency_probability = 1

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key
    program_label = 'demo-program'
    cohort_label = '2018'

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiParticipantData, self).set_up()

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

        # Successful download of completion ids triggers a notification, which
        # requires a cohort name.
        Program.mock_program_config(
            self.program_label,
            {'cohorts': {self.cohort_label: {'name': self.cohort_label}}},
        )

    def tear_down(self):
        Program.reset_mocks()

    def test_whitelist(self):
        """Certain pd values should readable, other's shouldn't."""
        project_cohort, survey, participant = self.create_pd_context()

        keys = (
            'progress',
            'link',
            'condition',
            'ep_assent',
            'last_login',
            'saw_baseline',
            'saw_demographics',
            'saw_validation',
            'secret',  # NOT on whitelist; should remain secret
        )
        pds = [
            ParticipantData.create(
                key=k,
                value='foo',
                participant_id=participant.uid,
                program_label=self.program_label,
                cohort_label=self.cohort_label,
                project_cohort_id=project_cohort.uid,
                code=project_cohort.code,
                survey_id=survey.uid,
                survey_ordinal=survey.ordinal,
            )
            for k in keys
        ]
        ParticipantData.put_multi(pds)

        url = '/api/participants/{}/data?project_cohort_id={}'.format(
            participant.uid, project_cohort.uid)
        result = self.testapp.get(url)
        result_dict = json.loads(result.body)

        self.assertEqual(len(result_dict), len(keys) - 1)

        secret_pd = [pd for pd in result_dict if pd['key'] == 'secret']

        self.assertEqual(len(secret_pd), 0)

    def test_completion_csv_requires_auth(self):
        self.testapp.get(
            '/api/project_cohorts/ProjectCohort_foo/completion/ids.csv',
            status=401,
        )

    def test_completion_csv_invalid_token(self):
        user = User.create(email='user@perts.net')
        user.put()

        self.testapp.get(
            '/api/project_cohorts/ProjectCohort_foo/completion/ids.csv',
            headers=login_headers(user.uid),
            # no auth token, request invalid
            status=400,
        )

    def test_completion_csv_forbidden(self):
        pc = ProjectCohort.create(
            program_label=self.program_label,
            cohort_label=self.cohort_label,
        )
        pc.put()

        user = User.create(email='user@perts.net')
        user.put()

        t = AuthToken.create(user.uid)
        t.put()

        self.testapp.get(
            '/api/project_cohorts/{}/completion/ids.csv'.format(pc.uid),
            params={'token': t.token},
            headers=login_headers(user.uid),
            # user doesn't own ProjectCohort_foo, forbidden
            status=403,
        )

    def test_completion_csv_allowed(self):
        org_id = 'Organization_foo'
        pc = ProjectCohort.create(
            organization_id=org_id,
            program_label=self.program_label,
            cohort_label=self.cohort_label,
        )
        pc.put()

        user = User.create(
            email='user@perts.net',
            owned_organizations=[org_id],
        )
        user.put()

        t = AuthToken.create(user.uid)
        t.put()

        self.testapp.get(
            '/api/project_cohorts/{}/completion/ids.csv'.format(pc.uid),
            params={'token': t.token},
            headers=login_headers(user.uid),
            # Authenticated, one-time token valid, has permission: 200.
            status=200,
        )

    def test_completion_anonymous_requires_auth(self):
        self.testapp.get(
            '/api/project_cohorts/ProjectCohort_foo/completion',
            status=401,
        )

    def test_completion_anonymous_forbidden(self):
        pc = ProjectCohort.create(
            program_label=self.program_label,
            cohort_label=self.cohort_label,
        )
        pc.put()

        user = User.create(email='user@perts.net')
        user.put()

        self.testapp.get(
            '/api/project_cohorts/{}/completion'.format(pc.uid),
            headers=login_headers(user.uid),
            # user doesn't own ProjectCohort_foo, forbidden
            status=403,
        )

    def test_completion_anonymous_allowed(self):
        org_id = 'Organization_foo'
        pc = ProjectCohort.create(
            organization_id=org_id,
            program_label=self.program_label,
            cohort_label=self.cohort_label,
        )
        pc.put()

        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)

        pd_params =  {
            'key': 'progress',
            'value': '100',
            'program_label': self.program_label,
            'cohort_label': self.cohort_label,
            'project_cohort_id': pc.uid,
            'code': pc.code,
            'survey_id': 'Survey_foo',
            'survey_ordinal': 1,
        }

        old_pd = ParticipantData.create(
            created=yesterday.strftime(config.sql_datetime_format),
            modified=yesterday.strftime(config.sql_datetime_format),
            participant_id='Participant_foo',
            **pd_params
        )
        # Use a lower-level interface so we can set the modified time.
        row = ParticipantData.coerce_row_dict(old_pd.to_dict())
        with mysql_connection.connect() as sql:
            sql.insert_or_update(ParticipantData.table, row)

        current_pd = ParticipantData.create(
            participant_id='Participant_bar',
            **pd_params
        )
        current_pd.put()

        user = User.create(
            email='user@perts.net',
            owned_organizations=[org_id],
        )
        user.put()

        result = self.testapp.get(
            '/api/project_cohorts/{}/completion'.format(pc.uid),
            params={
                'start': util.datelike_to_iso_string(today),
                'end': util.datelike_to_iso_string(tomorrow),
            },
            headers=login_headers(user.uid),
            # Authenticated, has permission: 200.
            status=200,
        )

        expected = [{
            'value': '100',
            'survey_ordinal': 1,
            'participant_id': current_pd.participant_id,
        }]
        self.assertEqual(json.loads(result.body), expected)


    def create_pd_context(self):
        program_label = 'demo-program'
        program_config = Program.get_config(program_label)
        template = program_config['surveys'][0]['survey_tasklist_template']

        project_cohort = ProjectCohort.create(
            program_label=program_label,
            organization_id='Organization_foo',
            project_id='Project_foo',
            cohort_label='2018',
        )
        project_cohort.put()

        survey = Survey.create(
            template,
            program_label=program_label,
            organization_id='Organization_foo',
            project_cohort_id=project_cohort.uid,
            ordinal=1,
        )
        survey.put()

        participant = Participant.create(name='Pascal', organization_id='PERTS')
        participant.put()

        return (project_cohort, survey, participant)

    def test_write_cross_site_pd(self, testing=False):
        pc, survey, participant = self.create_pd_context()

        url = (
            '/api/participants/{participant_id}/data/cross_site.gif?'
            'survey_id={survey_id}&key=progress&value=1{testing_param}'
        ).format(
            participant_id=participant.uid,
            survey_id=survey.uid,
            testing_param='&testing=true' if testing else '',
        )
        self.testapp.get(url)

        # The response is not designed to be useful (it's a gif), so check the
        # db to ensure the pd was written.

        result = ParticipantData.get_by_participant(
            participant.uid, survey.project_cohort_id)
        pd = result[0]
        self.assertEqual(pd.participant_id, participant.uid)
        self.assertEqual(pd.project_cohort_id, pc.uid)
        self.assertEqual(pd.code, pc.code)
        self.assertEqual(pd.survey_id, survey.uid)
        self.assertEqual(pd.key, 'progress')
        self.assertEqual(pd.value, '1')
        self.assertEqual(pd.testing, testing)

    def test_update_cross_site_pd(self):
        pc, survey, participant = self.create_pd_context()

        user = User.create(
            email='org_admin@school.edu',
            owned_organizations=[pc.organization_id],
        )
        user.put()

        def write_value(value):
            url = (
                '/api/participants/{participant_id}/data/cross_site.gif?'
                'survey_id={survey_id}&key=progress&value={value}'
            ).format(
                participant_id=participant.uid,
                survey_id=survey.uid,
                value=value,
            )
            self.testapp.get(url)

        # Query for participation between each write to make sure there are
        # no errors while clearing and re-populating the participation cache.
        self.query_pc_participation(user, pc)
        write_value('1')
        self.query_pc_participation(user, pc)
        write_value('100')

        pd = ParticipantData.get_by_participant(
            participant.uid, survey.project_cohort_id)[0]
        self.assertEqual(pd.value, '100')

    def test_downgrade_progress_fails_cross_site(self):
        pc, survey, participant = self.create_pd_context()

        def write_value(value):
            url = (
                '/api/participants/{participant_id}/data/cross_site.gif?'
                'survey_id={survey_id}&key=progress&value={value}'
            ).format(
                participant_id=participant.uid,
                survey_id=survey.uid,
                value=value,
            )
            self.testapp.get(url)

        write_value('100')
        write_value('1')  # should silently fail

        # Recorded pd is still 100.
        pd = ParticipantData.get_by_participant(
            participant.uid, survey.project_cohort_id)[0]
        self.assertEqual(pd.value, '100')

    def query_pc_participation(self, user, project_cohort):
        """Populates memcache w/ participation (even if blank) for this pc."""

        start = datetime.datetime.now() - datetime.timedelta(days=1)
        end = datetime.datetime.now() + datetime.timedelta(days=1)
        url = '/api/project_cohorts/{}/participation?start={}&end={}'.format(
            project_cohort.uid,
            start.strftime(config.iso_datetime_format),
            end.strftime(config.iso_datetime_format),
        )

        self.testapp.get(url, headers=jwt_headers(user))

    def test_update_cross_site_pd_with_descriptor(self):
        """Tests two ways: as a param, and as a compound survey id."""
        pc, survey, participant = self.create_pd_context()
        survey_descriptor = 'cycle-1'
        compound_id = '{}:{}'.format(survey.uid, survey_descriptor)

        # As a param.
        url = (
            '/api/participants/{participant_id}/data/cross_site.gif?'
            'survey_id={survey_id}&survey_descriptor={survey_descriptor}&'
            'key=progress&value={value}'
        ).format(
            participant_id=participant.uid,
            survey_id=survey.uid,
            survey_descriptor=survey_descriptor,
            value='1',
        )
        self.testapp.get(url)

        # As a compound id.
        url = (
            '/api/participants/{participant_id}/data/cross_site.gif?'
            'survey_id={survey_id}&key=progress&value={value}'
        ).format(
            participant_id=participant.uid,
            survey_id=compound_id,
            value='100',
        )
        self.testapp.get(url)

        pds = ParticipantData.get_by_participant(
            participant.uid, survey.project_cohort_id)
        self.assertEqual(len(pds), 1)
        self.assertEqual(pds[0].survey_id, compound_id)
        self.assertEqual(pds[0].value, '100')

    def test_update_local_pd(self):
        pc, survey, participant = self.create_pd_context()

        def write_value(value):
            return self.testapp.post_json(
                '/api/participants/{participant_id}/data/{key}'.format(
                    participant_id=participant.uid,
                    key='progress',
                ),
                {'value': value, 'survey_id': survey.uid},
            )

        original_id = json.loads(write_value('1').body)['uid']

        updated_id = json.loads(write_value('100').body)['uid']
        self.assertEqual(original_id, updated_id)

        pd = ParticipantData.get_by_id(original_id)
        self.assertEqual(pd.value, '100')

    def test_update_local_pd_with_descriptor(self):
        """Uses a descriptor two ways: in a param, and in the survey id."""
        pc, survey, participant = self.create_pd_context()
        survey_descriptor = 'cycle-1'

        # Using the param.
        response = self.testapp.post_json(
            '/api/participants/{participant_id}/data/{key}'.format(
                participant_id=participant.uid,
                key='progress',
            ),
            {'value': '1', 'survey_id': survey.uid,
             'survey_descriptor': survey_descriptor},
        )
        original_id = json.loads(response.body)['uid']

        # With the descriptor combined in the id.
        response = self.testapp.post_json(
            '/api/participants/{participant_id}/data/{key}'.format(
                participant_id=participant.uid,
                key='progress',
            ),
            {
                'value': '100',
                'survey_id': '{}:{}'.format(survey.uid, survey_descriptor)
            },
        )
        updated_id = json.loads(response.body)['uid']

        self.assertEqual(original_id, updated_id)

        pd = ParticipantData.get_by_id(original_id)
        self.assertEqual(pd.value, '100')
        self.assertEqual(pd.survey_id, '{}:{}'.format(
            survey.uid, survey_descriptor))

    def test_downgrade_progress_fails_local(self):
        pc, survey, participant = self.create_pd_context()

        def write_value(value, status):
            return self.testapp.post_json(
                '/api/participants/{participant_id}/data/{key}'.format(
                    participant_id=participant.uid,
                    key='progress',
                ),
                {'value': value, 'survey_id': survey.uid},
                status=status,
            )

        write_value('100', 200)
        write_value('1', 400)  # should explicitly fail

        # Recorded pd is still 100.
        pd = ParticipantData.get_by_participant(
            participant.uid, survey.project_cohort_id)[0]
        self.assertEqual(pd.value, '100')
