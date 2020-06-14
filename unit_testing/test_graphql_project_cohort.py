"""Test reading project cohorts with GraphQL."""

from collections import OrderedDict
from google.appengine.ext import ndb
import datetime
import json
import logging
import unittest
import webapp2
import webtest

from api_handlers import api_routes
from gae_models import DatastoreModel
from unit_test_helper import ConsistencyTestCase, login_headers
from model import (Checkpoint, Organization, Program, Project, ProjectCohort,
                   Survey, Task, User)
import config
import graphql_queries
import mysql_connection


class TestGraphQLProjectCohort(ConsistencyTestCase):
    """Test features of project cohort entities."""

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    program_description = "The cooolest."
    program_name = "Demo Program"
    program_label = 'demo-program'
    cohort_label = 'demo-cohort'

    cohort = OrderedDict([
        ('close_date', '2019-06-01'),
        ('label', cohort_label),
        ('name', u"{apos}18-{apos}19".format(apos=u"\u02BC")),
        ('open_date', '2018-06-01'),
        ('program_description', program_description),
        ('program_label', program_label),
        ('program_name', program_name),
        ('registration_close_date', '2019-05-01'),
        ('registration_open_date', '2018-02-28'),
    ])

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestGraphQLProjectCohort, self).set_up()

        with mysql_connection.connect() as sql:
            sql.reset({
                'checkpoint': Checkpoint.get_table_definition(),
            })

        Program.mock_program_config(
            self.program_label,
            {
                'name': self.program_name,
                'default_portal_type': 'name_or_id',
                'description': self.program_description,
                'cohorts': {
                    self.cohort_label: self.cohort
                }
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

    def tear_down(self):
        Program.reset_mocks()

    def create_project_cohort(self, cohort_date=datetime.datetime.today()):
        program = Program.get_config(self.program_label)
        liaison = User.create(email='liaison@perts.net')
        org = Organization.create(name="Org Foo", liaison_id=liaison.uid)
        liaison.owned_organizations.append(org.uid)
        project = Project.create(organization_id=org.uid,
                                 program_label=self.program_label)
        liaison.put()
        org.put()
        project.put()

        pc = ProjectCohort.create(
            project_id=project.uid,
            organization_id=org.uid,
            program_label=self.program_label,
            cohort_label=self.cohort_label,
            liaison_id=liaison.uid,
        )
        pc.put()

        surveys = Survey.create_for_project_cohort(program['surveys'], pc)
        ndb.put_multi(surveys)

        return liaison, org, project, pc, surveys

    def test_super_single(self):
        liaison, org, project, pc, surveys = self.create_project_cohort()
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()

        # The org owners query will be eventually consistent. That's fine. Mock
        # consistency.
        liaison.key.get()

        query = '''
            query GetSingleProjectCohort($uid: String) {
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
            json.dumps({'project_cohort': pc.to_client_dict()}),
        )

    def tasklist_query_expected(self, liaison, org, project, pc, surveys):
        org.tasklist.open()
        project.tasklist.open()
        for s in surveys:
            s.tasklist.open()

        unexpected_props = ('survey_ids',)
        pc_items = [(k, v) for k, v in pc.to_client_dict().items()
                    if k not in unexpected_props]

        # Assemble the result we expect, being careful to put everything in an
        # explicit order, since that's how the client will see it.
        expected = {
            "project_cohort": OrderedDict(
                pc_items +
                [
                    ('surveys', [s.to_client_dict() for s in surveys]),
                    ('checkpoints', [
                        OrderedDict(
                            list(c.to_client_dict().items()) +
                            [
                                ('tasks', [t.to_client_dict() for t in Task.get(
                                    ancestor=DatastoreModel.id_to_key(c.parent_id),
                                    checkpoint_id=c.uid,
                                    order='ordinal',
                                )]),
                            ]
                        )
                        for c in Checkpoint.for_tasklist(pc)
                    ]),
                    ("liaison", liaison.to_client_dict()),
                    ("organization", OrderedDict(
                        list(org.to_client_dict().items()) +
                        [
                            ("liaison", liaison.to_client_dict()),
                            ("users", [
                                liaison.to_client_dict(),
                            ]),
                        ]
                    )),
                    ("program_cohort", self.cohort),
                    ("project", project.to_client_dict()),
                ]
            ),
        }

        return graphql_queries.single_tasklist, expected

    def test_dashboard_unlisted(self):
        """Some programs support other apps and aren't meant to be queried."""
        # See #1015
        Program.mock_program_config('ep19', {'listed': False})

        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()

        pc = ProjectCohort.create(
            program_label='ep19',
            organization_id='Org_foo',
        )
        pc.put()

        response = self.testapp.get(
            '/api/dashboard?program_label=ep19',
            headers=login_headers(user.uid)
        )

        self.assertEqual(response.body, '[]')

    def test_dashboard_by_owner(self):
        query, expected = self.tasklist_query_expected(
            *self.create_project_cohort()
        )

        project_cohort_id = expected['project_cohort']['uid']
        user_id = expected['project_cohort']['liaison']['uid']

        response = self.testapp.get(
            '/api/users/{}/dashboard'.format(user_id),
            headers=login_headers(user_id),
        )

        self.assertEqual(response.body, json.dumps(expected))

    def test_dashboard_by_owner_empty(self):
        user = User.create(email='org@perts.net', user_type='user')
        user.put()

        response = self.testapp.get(
            '/api/users/{}/dashboard'.format(user.uid),
            headers=login_headers(user.uid),
        )
        logging.info(json.dumps(json.loads(response.body), indent=2))

        self.assertEqual(json.loads(response.body), {'project_cohorts': []})

    def test_super_tasklist(self):
        """Get everything you need for a tasklist in one query."""
        query, expected = self.tasklist_query_expected(
            *self.create_project_cohort()
        )
        project_cohort_id = expected['project_cohort']['uid']

        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()

        response = self.testapp.post_json(
            '/api/graphql',
            {
                'query': query,
                'variables': {'uid': project_cohort_id},
            },
            headers=login_headers(user.uid),
        )

        self.assertEqual(response.body, json.dumps(expected))

    def test_super_tasklist_forbidden(self):
        """Forbidden if you're not a super."""
        user = User.create(email='org@perts.net', user_type='user')
        user.put()

        self.testapp.post_json(
            '/api/graphql',
            {},
            headers=login_headers(user.uid),
            status=403,
        )

    def test_user_tasklist(self):
        """Get everything you need for a tasklist in one query."""
        query, expected = self.tasklist_query_expected(
            *self.create_project_cohort()
        )
        project_cohort_id = expected['project_cohort']['uid']
        org_id = expected['project_cohort']['organization']['uid']

        user = User.create(
            email='org@perts.net',
            user_type='user',
            owned_organizations=[org_id],
        )
        user.put()

        # Now that there's an org-level user, expect another in the users list.
        # They'll always come second b/c the org's users are sorted by email.
        expected['project_cohort']['organization']['users'].append(
            user.to_client_dict())

        response = self.testapp.get(
            '/api/tasklists/{}'.format(project_cohort_id),
            headers=login_headers(user.uid),
        )

        self.assertEqual(response.body, json.dumps(expected))

    def test_user_tasklist_forbidden(self):
        """Forbidden if you aren't on the org."""
        liaison, org, project, pc, surveys = self.create_project_cohort()
        user = User.create(email='other@perts.net', user_type='user')
        user.put()
        self.testapp.get(
            '/api/tasklists/{}'.format(pc.uid),
            headers=login_headers(user.uid),
            status=403,
        )

    def test_user_tasklist_not_found(self):
        user = User.create(email='other@perts.net', user_type='user')
        user.put()
        self.testapp.get(
            '/api/tasklists/foo',
            headers=login_headers(user.uid),
            status=404,
        )

    def test_cohort(self):
        user = User.create(email='super@email.com', user_type='super_admin')
        user.put()
        pc = ProjectCohort.create(
            project_id='Project_001',
            organization_id='Organization_001',
            program_label=self.program_label,
            cohort_label=self.cohort_label,
            liaison_id='User_001',
        )
        pc.put()

        query = '''
        query PCWithCohort($uid: String) {
            project_cohort(uid: $uid) {
                program_cohort {
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
        }
        '''

        expected = {
            'project_cohort': {
                'program_cohort': OrderedDict(
                    (k, self.cohort[k])
                    for k in sorted(self.cohort.keys())
                ),
            },
        }

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
            json.dumps(expected),
        )
