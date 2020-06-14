"""URL Handlers designed to be simple wrappers over our tasks. See map.py."""

from google.appengine.api import namespace_manager
from google.appengine.api import taskqueue
import json
import logging
import os

from gae_handlers import ApiHandler, Route
from graphql_handlers import SuperDashboard
from model import Email, Organization, Program, Project, SurveyLink, User
import auto_prompt
import config
import util


class TaskWorker(ApiHandler):
    """Abstract handler for a push queue task.

    The POST method is for the server to use after the code calls
    taskqueue.add(). If you POST, you'll run the same code, but you won't get
    any queueing benefits like the 10 minute run time or rate-limiting.

    If you're a human and you want to manually queue a task, use the following
    GET method.
    """
    def dispatch(self):
        # Set the namespace, which varies by branch.
        namespace = os.environ['NAMESPACE']
        if namespace:
            logging.info("Setting namespace: {}".format(namespace))
            namespace_manager.set_namespace(namespace)

        # Call the overridden dispatch(), which has the effect of running
        # the get() or post() etc. of the inheriting class.
        ApiHandler.dispatch(self)

    def get(self, *args, **kwargs):
        """Add a task to a queue."""
        # To translate from a GET-style query string to the POST required for
        # processing tasks, move the qs to the body and set the content type.
        # ApiHandler.get_params() takes care of the rest.
        task = taskqueue.add(
            url=self.request.path,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            payload=self.request.query_string,
            queue_name=self.queue_name(),
        )
        self.response.write(json.dumps({
            'params': task.extract_params(),
            'url': task.url,
            'was_deleted': task.was_deleted,
            'was_enqueued': task.was_enqueued,
        }))

    def queue_name(self):
        return self.request.get('queue_name', 'default')


class ImportLinks(TaskWorker):
    def get(self, program_label, survey_ordinal, file_name=None):
        """Launch separate tasks for each csv found to import."""
        paths = SurveyLink.list_gcs_files(program_label, survey_ordinal,
                                          file_name)
        tasks = []
        for gcs_path in paths:
            # Convert each gcs path into a POST url for a task worker.
            url = self.request.path
            if not file_name:
                # Add a file name to the url if there isn't one. This supports
                # calling, e.g. GET /task/import_links/hg17/1 with no file name
                # and thus launching a task for each csv found in that dir.
                if not url.endswith('/'):
                    url += '/'
                url += gcs_path.split('/')[-1]
            task = taskqueue.add(url=url, queue_name=self.queue_name())
            tasks.append(task)

        self.response.write(json.dumps([{
            'url': task.url,
            'was_deleted': task.was_deleted,
            'was_enqueued': task.was_enqueued,
        } for task in tasks]))

    def post(self, program_label, survey_ordinal, file_name=None):
        if not file_name:
            return
        num_imported = SurveyLink.import_links(
            program_label, int(survey_ordinal), file_name)
        self.response.write(json.dumps({'num_imported': num_imported}))


class CacheDashboard(TaskWorker):
    def post(self):
        # allowed = ('organization_id', 'program_label', 'cohort_label')
        # params = {
        #     k: self.request.get(k) for k in allowed
        #     if self.request.get(k, None) is not None
        # }

        # Make sure not to recurse this task.
        SuperDashboard.__dict__['get'](self, queue_cache_task=False)

    def get_current_user(self):
        class FakeSuper(object):
            super_admin = True

        return FakeSuper()


class EmailProject(TaskWorker):
    def post(self, project_id, slug):
        """A project has been identified as new. Send them a welcome."""
        project = Project.get_by_id(project_id)
        program = Program.get_config(project.program_label)
        org = Organization.get_by_id(project.organization_id)

        # The Org liaison is preferred, but is not guaranteed to be set (users
        # choose their org liaison explicitly as one of the org tasks). Default
        # to the Project liaison, which is set on creation in
        # add_program.controller.js@joinProgram
        org_liaison = User.get_by_id(org.liaison_id)
        project_liaison = User.get_by_id(project.liaison_id)
        liaison = org_liaison or project_liaison

        email = Email.create(
            to_address=liaison.email,
            mandrill_template=slug,
            mandrill_template_content={
                'program_name': program['name'],
                'organization_name': org.name,
                'liaison_name': liaison.name,
                'join_date': util.datelike_to_iso_string(project.created),
            },
        )
        email.put()

task_routes = [
    Route('/task/cache_dashboard', CacheDashboard),
    Route('/task/import_links/<program_label>/<survey_ordinal>', ImportLinks),
    Route('/task/import_links/<program_label>/<survey_ordinal>/<file_name>',
          ImportLinks),
    Route('/task/email_project/<project_id>/<slug>', EmailProject),
]
