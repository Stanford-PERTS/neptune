"""Test general GraphQL operations."""

import datetime
import json
import unittest
import webapp2
import webtest

from api_handlers import api_routes
from unit_test_helper import ConsistencyTestCase, login_headers
from model import Program, Project, ProjectCohort, User
import config


class TestGraphQL(ConsistencyTestCase):
    """Test features of project cohort entities."""

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    program_label = 'demo-program'

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestGraphQL, self).set_up()

        Program.mock_program_config(
            self.program_label,
            {
                'default_portal_type': 'name_or_id',
            }
        )

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

    def tearDown(self):
        Program.reset_mocks()
        super(TestGraphQL, self).tearDown()

    def create_project_cohort(self, cohort_date=datetime.datetime.today()):
        program_label = 'demo-program'
        cohort_label = 'demo-cohort'
        program = Program.get_config(program_label)
        org_id = 'Org_Foo'
        liaison_id = 'User_liaison'
        project = Project.create(organization_id=org_id,
                                 program_label=program_label)
        project.put()

        one_day = datetime.timedelta(days=1)
        cohort_config = {
            'label': cohort_label,
            'name': 'Demo Cohort',
            'open_date': str(cohort_date - one_day),  # yesterday
            'close_date': str(cohort_date + one_day),  # tomorrow
        }
        program['cohorts'][cohort_label] = cohort_config
        Program.mock_program_config(
            program_label,
            {'cohorts': {cohort_label: cohort_config}},
        )

        pc = ProjectCohort.create(
            project_id=project.uid,
            organization_id=org_id,
            program_label=program_label,
            cohort_label=cohort_label,
            liaison_id=liaison_id,
        )
        pc.put()

        return pc

    def test_single_project_cohort_super(self):
        pc = self.create_project_cohort()
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()

        query = '''
            query Tasklist($uid: String) {
                project_cohort(uid: $uid) {
                    code
                    cohort_label
                    completed_report_task_ids
                    created
                    custom_portal_url
                    data_export_survey
                    deleted
                    expected_participants
                    liaison_id
                    modified
                    organization_id
                    portal_message
                    portal_type
                    program_label
                    project_id
                    short_uid
                    status
                    survey_ids
                    survey_params
                    uid
                }
            }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            {
                'query': query,
                'variables': {'uid': pc.uid},
            },
            headers=login_headers(user.uid),
        )

        self.assertEqual(
            response.body,
            json.dumps({"project_cohort": pc.to_client_dict()}),
        )
