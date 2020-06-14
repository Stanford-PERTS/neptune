import datetime
import json
import logging
import unittest
import webapp2
import webtest


from api_handlers import api_routes
from model import (Checkpoint, Organization, Program, Project, Survey,
                   Tasklist, TaskReminder, User)
from unit_test_helper import ConsistencyTestCase, login_headers
import config
import mysql_connection


class TestTaskReminder(ConsistencyTestCase):

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        super(TestTaskReminder, self).set_up()
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

    def tearDown(self):
        Program.reset_mocks()
        super(TestTaskReminder, self).tearDown()

    def test_create_org(self):
        """Creating an org through the api makes a TR for the creator."""
        user = User.create(email='user@perts.net',
                                user_type='user')
        user.put()

        response = self.testapp.post_json(
            '/api/organizations',
            {'name': "Foo Org", 'liaison_id': user.uid},
            headers=login_headers(user.uid),
        )
        org_dict = json.loads(response.body)

        trs = TaskReminder.get(ancestor=user)
        self.assertEqual(len(trs), 1)
        self.assertEqual(trs[0].context_id, org_dict['uid'])

    def test_create_project(self):
        """Creating a project through the api makes a TR for all org owners."""
        user1 = User.create(email='org1@perts.net', user_type='user')
        user2 = User.create(email='org2@perts.net', user_type='user')
        org = Organization.create(name="Foo Org", liaison_id=user1.uid)
        user1.owned_organizations = [org.uid]
        user2.owned_organizations = [org.uid]
        user1.put()
        user2.put()
        org.put()

        # Bring org 2 into consistency, assuming they've been part of the org
        # for some time. Don't bring org 1 into consistency, to simulate
        # joining an org and creating a project within a short timespan, which
        # we expect.
        user2.key.get()

        response = self.testapp.post_json(
            '/api/projects',
            {'organization_id': org.uid, 'program_label': 'demo-program',
             'liaison_id': user1.uid},
            headers=login_headers(user1.uid),
        )
        project_dict = json.loads(response.body)

        trs1 = TaskReminder.get(ancestor=user1)
        trs2 = TaskReminder.get(ancestor=user2)
        self.assertEqual(len(trs1), 1)
        self.assertEqual(len(trs2), 1)
        self.assertEqual(trs1[0].context_id, project_dict['uid'])

    def test_close_tasklist(self):
        """Should delete all associated task reminders."""
        user1 = User.create(email='org1@perts.net', user_type='user')
        user2 = User.create(email='org2@perts.net', user_type='user')
        org = Organization.create(name="Foo Org", liaison_id=user1.uid)
        user1.owned_organizations = [org.uid]
        user2.owned_organizations = [org.uid]
        user1.put()
        user2.put()
        org.put()

        response = self.testapp.post_json(
            '/api/projects',
            {'organization_id': org.uid, 'program_label': 'demo-program',
             'liaison_id': user1.uid},
            headers=login_headers(user1.uid),
        )
        project_dict = json.loads(response.body)
        project = Project.get_by_id(project_dict['uid'])

        # Simulate time passing and the datastore reaching consistency.
        trs1 = TaskReminder.get(ancestor=user1)
        trs2 = TaskReminder.get(ancestor=user2)

        Tasklist(project).close()

        self.assertEqual(len(TaskReminder.get(ancestor=user1)), 0)
        self.assertEqual(len(TaskReminder.get(ancestor=user2)), 0)

    def test_join_org(self):
        """Joining an org makes task reminders for all contained tasklists."""
        program_label = 'demo-program'
        cohort_label = 'demo-cohort'

        # Guarantee the dates will work by mocking the cohort config.
        cohort_config = {
            'label': cohort_label,
            'name': 'Demo Cohort',
            'open_date': str(datetime.date.today()),
            'close_date': str(datetime.date.today()),
        }
        Program.mock_program_config(
            program_label,
            {'cohorts': {cohort_label: cohort_config}},
        )

        program = Program.get_config(program_label)
        tasklist_template = program['surveys'][0]['survey_tasklist_template']

        owner = User.create(email='owner@perts.net', user_type='user')
        org = Organization.create(name="Foo Org", liaison_id=owner.uid)
        owner.owned_organizations = [org.uid]
        project = Project.create(program_label=program_label,
                                 organization_id=org.uid)
        survey = Survey.create(tasklist_template, project_id=project.uid,
                               organization_id=org.uid,
                               program_label=program_label, ordinal=1,
                               cohort_label=cohort_label)
        owner.put()
        org.put()
        project.put()
        survey.put()

        # The assumption here is the org and its contents are long-standing,
        # so force consistency with all.
        org.key.get()
        project.key.get()
        survey.key.get()

        joiner = User.create(email='joiner@perts.net', user_type='user')
        joiner.put()

        self.testapp.post_json(
            '/api/users/{}/organizations'.format(joiner.uid),
            org.to_client_dict(),
            headers=login_headers(owner.uid),
        )

        # One TaskReminder for each of: org tasklist, project tasklist, survey
        # tasklist.
        self.assertEqual(len(TaskReminder.get(ancestor=joiner)), 3)

        return (org, project, survey, owner, joiner)

    @unittest.skip("Skipping until removing ownership is implemented.")
    def test_leave_org(self):
        """Leaving an org deletes task reminders for all related task lists."""

        org, project, survey, owner, joiner = self.test_join_org()

        self.testapp.delete(
            '/api/users/{}/organizations/{}'.format(joiner.uid, org.uid),
            headers=login_headers(owner.uid),
        )

        self.assertEqual(len(TaskReminder.get(ancestor=joiner)), 0)
