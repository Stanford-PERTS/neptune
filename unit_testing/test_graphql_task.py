"""Test reading tasks with GraphQL."""

import datetime
import json
import logging
import unittest
import webapp2
import webtest

from api_handlers import api_routes
from model import Checkpoint, Organization, Program, Project, Task, User
from unit_test_helper import ConsistencyTestCase, login_headers
import config
import mysql_connection
import organization_tasks


class TestGraphQLTask(ConsistencyTestCase):
    """Test features of project cohort entities."""

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    program_label = 'demo-program'

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestGraphQLTask, self).set_up()

        with mysql_connection.connect() as sql:
            sql.reset({
                'checkpoint': Checkpoint.get_table_definition(),
            })

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
        super(TestGraphQLTask, self).tearDown()

    def create_org_tasks(self, user, cohort_date=datetime.datetime.today()):
        org = Organization.create(name='Org Foo')
        org.put()

        org.tasklist.open(user)

        return (org, Task.get(ancestor=org, order='ordinal'))

    def create_project_task(self, cohort_date=datetime.datetime.today()):
        program_label = 'demo-program'
        task_label = 'task_project_foo'
        project = Project.create(program_label=program_label,
                                 organization_id='Organization_Foo')

        task_template = {
            'label': task_label,
            'data_type': 'radio',
            'select_options': [
                {'value': 'normal', 'label': 'true names'},
                {'value': 'alias', 'label': 'aliases'}
            ],
        }
        Program.mock_program_config(program_label, {
            'project_tasklist_template': [
                {
                    'tasks': [task_template]
                }
            ]
        })

        t = Task.create(task_label, 1, 'checkpoint_foo', parent=project,
                        program_label=program_label)
        t.put()
        return t

    def test_super_single(self):
        t = self.create_project_task()
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()

        query = '''
            query GetSingleTask($uid: String) {
                task(uid: $uid) {
                    action_statement
                    attachment
                    body
                    checkpoint_id
                    completed_by_id
                    completed_by_name
                    completed_date
                    counts_as_program_complete
                    created
                    data_admin_only_visible
                    data_type
                    deleted
                    disabled
                    due_date
                    label
                    modified
                    name
                    non_admin_may_edit
                    ordinal
                    parent_id
                    program_label
                    select_options
                    short_parent_id
                    status
                    uid
                }
            }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            {
                'query': query,
                'variables': {'uid': t.uid},
            },
            headers=login_headers(user.uid),
        )


        self.assertEqual(
            response.body,
            json.dumps({'task': t.to_client_dict()}),
        )

    def test_get_all_tasks(self):
        super_user = User.create(email='super@perts.net',
                                 user_type='super_admin')
        super_user.put()
        org, tasks = self.create_org_tasks(super_user)

        query = '''
        query GetAllTasks {
            tasks {
                label
            }
        }
        '''

        expected = {
            # Should be ordered by ordinal
            'tasks': [{'label': t.label} for t in tasks],
        }

        response = self.testapp.post_json(
            '/api/graphql',
            {'query': query},
            headers=login_headers(super_user.uid),
        )

        self.assertEqual(json.loads(response.body), expected)

    def test_get_many_tasks(self):
        """Queries aren't limited to an arbitrarily small number."""
        super_user = User.create(email='super@perts.net',
                                 user_type='super_admin')
        super_user.put()

        num_orgs = 10
        # Assumes only one org checkpoint.
        num_org_tasks = len(organization_tasks.tasklist_template[0]['tasks'])

        for x in range(num_orgs):
            self.create_org_tasks(super_user)

        query = '''
        query GetAllTasks {
            tasks {
                label
            }
        }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            {'query': query},
            headers=login_headers(super_user.uid),
        )
        response_dict = json.loads(response.body)

        self.assertEqual(len(response_dict['tasks']), num_org_tasks * num_orgs)
