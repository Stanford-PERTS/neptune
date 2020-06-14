from google.appengine.ext import testbed
import datetime
import logging

from model import (Program, Project, ProjectCohort)
from unit_test_helper import ConsistencyTestCase
import auto_prompt
import util


class TestAutoPrompt(ConsistencyTestCase):
    consistency_probability = 1

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestAutoPrompt, self).set_up()

        self.taskqueue_stub = self.testbed.get_stub(
            testbed.TASKQUEUE_SERVICE_NAME)

    def create_mandrill_template(self, slug):
        return {
            "labels": ["neptune"],
            "publish_code": "<p>Welcome to {{ program_name }}!</p>",
            "publish_name": "test: email preview",
            "publish_subject": "Welcome to Foo Program!",
            "published_at": "2018-06-18 18:56:50",
            "slug": slug,
        }

    def test_queue_org_welcome(self):
        Program.mock_program_config('p1', {'project_tasklist_template': []})
        Program.mock_program_config('p2', {'project_tasklist_template': []})
        old_project = Project.create(
            program_label='p1',
            organization_id='Organization_foo',
            created=datetime.datetime.now() - datetime.timedelta(hours=48),
        )
        old_project.put()
        new_project = Project.create(
            program_label='p1',
            organization_id='Organization_foo',
        )
        new_project.put()
        other_project = Project.create(
            program_label='p2', # no matching template
            organization_id='Organization_foo',
        )
        other_project.put()

        templates = [
            self.create_mandrill_template(
              'p1-{}'.format(auto_prompt.ORG_WELCOME_SUFFIX)
            ),
            self.create_mandrill_template('foo-template'),
        ]

        auto_prompt.queue_org_welcome(templates)

        tasks = self.taskqueue_stub.get_filtered_tasks()

        # Only the recently created project, which also has a org welcome
        # template, should be queued. The old project, and the project on the
        # other program, should not be welcomed.
        self.assertEqual(len(tasks), 1)

        expected_url = '/task/email_project/{}/p1-org-welcome'.format(
            new_project.uid)
        self.assertIn(expected_url, [t.url for t in tasks])

        Program.reset_mocks()

    def test_queue_org_welcome_back(self):
        Program.mock_program_config('p1', {'project_tasklist_template': []})

        # Case 1: New PC, returning.
        returning_pc1 = ProjectCohort.create(
            program_label='p1',
            organization_id='Organization_returning',
            project_id='Project_returning',
            cohort_label='2020',
        )
        returning_pc1.put()
        returning_pc2 = ProjectCohort.create(
            program_label='p1',
            organization_id='Organization_returning',
            project_id='Project_returning',
            cohort_label='2019',
            created=datetime.datetime.now() - datetime.timedelta(days=365)
        )
        returning_pc2.put()

        # Case 2: New PC, but not returning.
        new_pc = ProjectCohort.create(
            program_label='p1',
            organization_id='Organization_new',
            project_id='Project_new',
        )
        new_pc.put()

        # Case 3: Old PC (not created in the day).
        old_pc = ProjectCohort.create(
            program_label='p1',
            organization_id='Organization_old',
            project_id='Project_old',
            created=datetime.datetime.now() - datetime.timedelta(hours=48),
        )
        old_pc.put()

        # Some tasks are created on put. We're not interested in these.
        creation_tasks = self.taskqueue_stub.get_filtered_tasks()

        templates = [
            self.create_mandrill_template(
              'p1-{}'.format(auto_prompt.ORG_WELCOME_BACK_SUFFIX)
            ),
        ]

        auto_prompt.queue_org_welcome_back(templates)

        tasks = self.taskqueue_stub.get_filtered_tasks()
        num_new_tasks = len(tasks) - len(creation_tasks)

        # Only the returning pc should have a task queued.
        self.assertEqual(num_new_tasks, 1)

        expected_url = '/task/email_project/Project_returning/p1-org-welcome-back'
        self.assertIn(expected_url, [t.url for t in tasks])

        Program.reset_mocks()

    def test_checklist_nudge(self):
        month_from_now = util.datelike_to_iso_string(
            datetime.date.today() + datetime.timedelta(days=30))

        Program.mock_program_config(
            'p1',
            {
                'cohorts': {
                    '2019': {'label': '2019', 'open_date': '2019-06-01'},
                    '2020': {'label': '2020', 'open_date': month_from_now},
                },
                'project_tasklist_template': []
            },
        )
        Program.mock_program_config(
            'p2',
            {
                'cohorts': {},
                'project_tasklist_template': []
            },
        )

        templates = [
            self.create_mandrill_template(
              'p1-{}'.format(auto_prompt.CHECKLIST_NUDGE_SUFFIX)
            ),
        ]

        # Case 1: 2020 PCs gets prompt
        current_pc1 = ProjectCohort.create(
            program_label='p1',
            organization_id='Organization_foo',
            project_id='Project_current1',
            cohort_label='2020',
        )
        current_pc1.put()
        current_pc2 = ProjectCohort.create(
            program_label='p1',
            organization_id='Organization_bar',
            project_id='Project_current2',
            cohort_label='2020',
        )
        current_pc2.put()

        # Case 2: 2019 PC does not
        old_pc = ProjectCohort.create(
            program_label='p1',
            cohort_label='2019',
            project_id='Project_old',
        )
        old_pc.put()

        # Case 3: PC in other program does not
        other_pc = ProjectCohort.create(
            program_label='p2',
            cohort_label='2020',
            project_id='Project_other',
        )
        other_pc.put()

        # Some tasks are created on put. We're not interested in these.
        creation_tasks = self.taskqueue_stub.get_filtered_tasks()

        auto_prompt.queue_checklist_nudge(templates)

        tasks = self.taskqueue_stub.get_filtered_tasks()
        num_new_tasks = len(tasks) - len(creation_tasks)

        # Only the 2 2020 pcs in the right program should have a task queued.
        self.assertEqual(num_new_tasks, 2)

        expected_url1 = '/task/email_project/Project_current1/p1-checklist-nudge'
        self.assertIn(expected_url1, [t.url for t in tasks])
        expected_url2 = '/task/email_project/Project_current2/p1-checklist-nudge'
        self.assertIn(expected_url2, [t.url for t in tasks])

        Program.reset_mocks()
