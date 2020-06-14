"""Test reading checkpoints via GraphQL."""

import json
import logging
import unittest
import webapp2
import webtest

from api_handlers import api_routes
from unit_test_helper import ConsistencyTestCase, login_headers
from model import Checkpoint, Program, User
import config
import mysql_connection


class TestGraphQLCheckpoint(ConsistencyTestCase):
    """Test features of project cohort entities."""

    consistency_probability = 0

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestGraphQLCheckpoint, self).set_up()

        with mysql_connection.connect() as sql:
            sql.reset({
                'checkpoint': Checkpoint.get_table_definition(),
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

    def tearDown(self):
        Program.reset_mocks()
        super(TestGraphQLCheckpoint, self).tearDown()

    def create_checkpoints(self):
        """Checkpoints should gain additional properties as client dicts."""
        config = {
           'project_tasklist_template': [
                {
                    'name': "Project Foo",
                    'label': 'demo_project__foo',
                    'body': "foo",
                    'tasks': [],
                },
                {
                    'name': "Project Bar",
                    'label': 'demo_project__bar',
                    'body': "bar",
                    'tasks': [],
                },
            ],
        }
        Program.mock_program_config('demo-program', config)
        checkpoints = (
            Checkpoint.create(
                parent_id='Project_foo', ordinal=1,
                program_label='demo-program',
                **config['project_tasklist_template'][0]
            ),
            Checkpoint.create(
                parent_id='Project_bar', ordinal=2,
                program_label='demo-program',
                **config['project_tasklist_template'][1]
            ),
        )
        Checkpoint.put_multi(checkpoints)
        return checkpoints

    def test_super_single(self):
        checkpoint1, checkpoint2 = self.create_checkpoints()
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()

        query = '''
            query GetSingleCheckpoint($uid: String) {
                checkpoint(uid: $uid) {
                    body
                    cohort_label
                    label
                    name
                    ordinal
                    organization_id
                    parent_id
                    parent_kind
                    program_label
                    project_cohort_id
                    project_id
                    short_uid
                    status
                    survey_id
                    task_ids
                    uid
                }
            }
        '''

        response = self.testapp.post_json(
            '/api/graphql',
            {
                'query': query,
                'variables': {'uid': checkpoint1.uid},
            },
            headers=login_headers(user.uid),
        )

        self.assertEqual(
            response.body,
            json.dumps({'checkpoint': checkpoint1.to_client_dict()}),
        )

    def test_get_all_checkpoints(self):
        checkpoints = self.create_checkpoints()
        user = User.create(email='super@perts.net', user_type='super_admin')
        user.put()

        query = '''
        query GetAllCheckpoints {
            checkpoints {
                label
            }
        }
        '''

        expected = {
            # Should be ordered by ordinal
            'checkpoints': [{'label': c.label} for c in checkpoints],
        }

        response = self.testapp.post_json(
            '/api/graphql',
            {'query': query},
            headers=login_headers(user.uid),
        )

        self.assertEqual(json.loads(response.body), expected)
