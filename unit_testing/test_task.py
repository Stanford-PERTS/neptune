from model import Checkpoint, Organization, Program, Project, Survey, Task
from unit_test_helper import ConsistencyTestCase
import logging
import mysql_connection

import organization_tasks


class TestTask(ConsistencyTestCase):

    consistency_probability = 0

    def set_up(self):
        """Clear relevant tables from testing SQL database."""
        super(TestTask, self).set_up()
        with mysql_connection.connect() as sql:
            sql.reset({'checkpoint': Checkpoint.get_table_definition()})

    def tearDown(self):
        Program.reset_mocks()
        super(TestTask, self).tearDown()

    def test_create_select(self):
        program_label = 'demo-program'
        task_label = 'task_foo'
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
        t_dict = t.to_client_dict()
        self.assertEqual(t_dict['select_options'],
                         task_template['select_options'])

    def test_org_task_body(self):
        """Tasks should get dynamic properties from their definition."""
        org = Organization.create(name='org')
        org.put()

        orig_config = organization_tasks.tasklist_template
        organization_tasks.tasklist_template = [
            {
                'tasks': [
                    {
                        'label': 'task_foo',
                        'body': "<p>Demo body.</p>",
                    }
                ]
            }
        ]

        t = Task.create('task_foo', 1, 'checkpoint_foo',parent=org)
        t_dict = t.to_client_dict()

        self.assertIsInstance(t_dict['body'], basestring)
        self.assertGreater(len(t_dict['body']), 0)

        organization_tasks.tasklist_template = orig_config

    def test_project_task_body(self):
        """Tasks should get dynamic properties from their definition."""
        program_label = 'demo-program'
        task_label = 'task_foo'
        project = Project.create(program_label=program_label,
                                 organization_id='Organization_Foo')

        task_template = {
            'label': task_label,
            'body': "<p>Demo body.</p>",
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
        t_dict = t.to_client_dict()

        self.assertIsInstance(t_dict['body'], basestring)
        self.assertGreater(len(t_dict['body']), 0)

    def test_survey_task_body(self):
        """Tasks should get dynamic properties from their definition."""
        program_label = 'demo-program'
        task_label = 'task_foo'
        survey = Survey.create(
            [],
            program_label='demo-program',
            organization_id='Organization_Foo',
            ordinal=1,
        )

        task_template = {
            'label': task_label,
            'body': "<p>Demo body.</p>",
        }
        Program.mock_program_config(program_label, {
            'surveys': [
                {
                    'survey_tasklist_template': [
                        {
                            'tasks': [task_template]
                        }
                    ]
                }
            ]
        })

        t = Task.create(task_label, 1, 'checkpoint_foo', parent=survey,
                        program_label=program_label)
        t_dict = t.to_client_dict()

        self.assertIsInstance(t_dict['body'], basestring)
        self.assertGreater(len(t_dict['body']), 0)

    def test_initial_values(self):
        """Adopt initial values if specified, overriding defaults."""
        # Background
        program_label = 'demo-program'
        task_label_default = 'task_default'
        task_label_init = 'task_init'

        # One task with default values, one with a non-default initial value.
        task_template_default = {
            'label': task_label_default,
            # default value of disabled is False
        }
        task_template_initial_values = {
            'label': task_label_init,
            'initial_values': {'disabled': True},  # override default
        }
        Program.mock_program_config(program_label, {
            'project_tasklist_template': [
                {
                    'tasks': [
                        task_template_default,
                        task_template_initial_values,
                    ]
                }
            ]
        })

        # Creating the project will generate a tasklist with the above tasks.
        project = Project.create(program_label=program_label,
                                 organization_id='Organization_Foo')

        self.assertFalse(project.tasklist.tasks[0].disabled)
        self.assertTrue(project.tasklist.tasks[1].disabled)
