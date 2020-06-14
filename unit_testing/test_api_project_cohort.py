import json
import webapp2
import webtest

from api_handlers import api_routes
from google.appengine.datastore import datastore_stub_util
from model import User, Program, Project, ProjectCohort, Survey
from unit_test_helper import ConsistencyTestCase, login_headers
import config
import datetime


class TestApiProjectCohort(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiProjectCohort, self).set_up()

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
        super(TestApiProjectCohort, self).tearDown()

    def test_join_cohort(self, cohort_date=datetime.date.today()):
        """Allowed for org admin owner of project."""

        # Existing things to relate to.
        program_label = 'demo-program'
        cohort_label = 'demo-cohort'
        program = Program.get_config(program_label)
        org_id = 'Org_Foo'
        user = User.create(email="test@example.com",
                           owned_organizations=[org_id])
        project = Project.create(organization_id=org_id,
                                 program_label=program_label)
        user.put()
        project.put()

        # Guarantee the dates will work by mocking the cohort config.
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

        # Create the project cohort through the api. Any response other than
        # 200 will fail the test.
        response = self.testapp.post_json(
            '/api/project_cohorts',
            {
                'project_id': project.uid,
                'organization_id': org_id,
                'program_label': program_label,
                'cohort_label': cohort_label,
                'liaison_id': user.uid,
            },
            headers=login_headers(user.uid)
        )
        response_dict = json.loads(response.body)

        return (ProjectCohort.get_by_id(response_dict['uid']), user)

    def test_join_closed_cohort(self):
        """Can't join closed cohorts."""
        old_date = datetime.date.today() - datetime.timedelta(days=10)
        with self.assertRaises(webtest.AppError):
            self.test_join_cohort(cohort_date=old_date)

    def test_join_existing_project_cohort(self):
        pc, user = self.test_join_cohort()

        # Try to make another one, which should fail.
        self.testapp.post_json(
            '/api/project_cohorts',
            {
                'project_id': pc.project_id,
                'organization_id': pc.organization_id,
                'program_label': pc.program_label,
                'cohort_label': pc.cohort_label,
                'liaison_id': user.uid,
            },
            headers=login_headers(user.uid),
            status=400,
        )

    def test_survey_creation(self):
        """Creating a project cohort should create surveys."""

        # Hack eventual consistency for just this test because we don't
        # expect surveys to be available instantly upon creation, unlike the
        # project cohort itself.
        self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
            probability=1)
        self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)

        pc, user = self.test_join_cohort()

        program_label = 'demo-program'
        program = Program.get_config(program_label)

        surveys = Survey.get(project_cohort_id=pc.uid)
        self.assertEqual(len(surveys), len(program['surveys']))
