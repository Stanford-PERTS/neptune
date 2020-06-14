import webapp2
import webtest
import json

from api_handlers import api_routes
from model import Checkpoint, ProjectCohort, Survey, Task, User
from unit_test_helper import ConsistencyTestCase, login_headers
import config
import jwt_helper
import mysql_connection


class TestApiTaskAttachment(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiTaskAttachment, self).set_up()
        with mysql_connection.connect() as sql:
            sql.reset({'checkpoint': Checkpoint.get_table_definition()})

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

    def test_task_attachment_post(self):
        """Test that ProjectCohort's completed_report_task_ids are updated"""

        user = User.create(
            email='super@perts.net',
            user_type='super_admin'
        )
        user.put()

        pc = ProjectCohort.create(
            organization_id='Org_123',
        )
        pc.put()

        tasklist_template = []

        s = Survey.create(
            tasklist_template,
            project_cohort_id=pc.uid
        )
        s.put()

        t = Task.create(
            'cg17_survey__report_1',
            1,
            'Checkpoint_123',
            parent=s,
            program_label='cg17'
        )
        t.put()

        self.testapp.post(
            '/api/tasks/{}/attachment'.format(t.uid),
            upload_files=[('file', 'static_src/assets/privacy_policy.pdf')],
            headers=login_headers(user.uid)
        )

        self.assertEqual(pc.key.get().completed_report_task_ids, [t.uid])

    def create_task(self):
        pc = ProjectCohort.create(organization_id='Org_123')
        pc.put()

        tasklist_template = []

        s = Survey.create(tasklist_template, project_cohort_id=pc.uid)
        s.put()

        t = Task.create(
            'cg17_survey__report_1',
            1,
            'Checkpoint_123',
            parent=s,
            program_label='cg17'
        )
        t.put()

        return pc, s, t

    def test_link_attachment(self):
        """Link-style attachments for reports save correctly."""
        user = User.create(
            email='super@perts.net',
            user_type='super_admin'
        )
        user.put()

        pc, survey, task = self.create_task()

        attachment = {
            "link": "https://www.example.com/Je\u017cu.html?Je\u017cu=/Je\u017cu&foo=bar#Je\u017cu/stuffis",
            "filename": "Je\u017cu.html",
        }
        response = self.testapp.post_json(
            '/api/tasks/{}/attachment'.format(task.uid),
            attachment,
            headers=login_headers(user.uid)
        )
        json_attachment = response.body

        self.assertEqual(json.loads(json_attachment), attachment)
        self.assertEqual(Task.get_by_id(task.uid).attachment, json_attachment)

    def test_rserve_post_task_attachment(self):
        valid_payload = {
            'user_id': 'User_rserve',
            'email': 'rserve@perts.net',
            'user_type': 'super_admin',
        }
        valid_jwt = jwt_helper.encode_rsa(valid_payload)
        invalid_payload = {
            'user_id': 'User_foo',
            'email': 'foo@perts.net',
            'user_type': 'user',  # neither owner nor super; should fail
        }
        invalid_jwt = jwt_helper.encode_rsa(invalid_payload)

        pc, survey, task = self.create_task()

        attachment = {"link": "www.example.com", "filename": "foo.html"}

        self.testapp.post_json(
            '/api/tasks/{}/attachment'.format(task.uid),
            attachment,
            headers={'Authorization': 'Bearer ' + invalid_jwt},
            status=403,
        )

        response = self.testapp.post_json(
            '/api/tasks/{}/attachment'.format(task.uid),
            attachment,
            headers={'Authorization': 'Bearer ' + valid_jwt},
        )
        json_attachment = response.body

        self.assertEqual(json.loads(json_attachment), attachment)
        self.assertEqual(Task.get_by_id(task.uid).attachment, json_attachment)
