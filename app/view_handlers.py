from google.appengine.api import users as app_engine_users
import datetime
import json

import logging

from gae_handlers import ViewHandler, Route
from model import (Organization, Program, Survey, ProjectCohort, User)
from rserve_handlers import Datasets as DatasetsApiHandler
import gae_mini_profiler.templatetags
import copilot_report_config
import config
import util
import os


# Make sure this is off in production, it exposes exception messages.
debug = util.is_development()


class AdminLogin(ViewHandler):
    """Where App Engine Admins can log in with their google accounts."""
    def get(self):
        self.redirect(app_engine_users.create_login_url())


class Logout(ViewHandler):
    """Clears the user's session, closes connections to google."""
    def get(self):
        self.log_out()

        redirect = self.request.get('redirect') or '/'

        if util.is_localhost():
            # In the SDK, it makes sense to log the current user out of Google
            # entirely (otherwise admins have to click logout twice, b/c
            # existing code will attempt to sign them right in again).
            self.redirect(app_engine_users.create_logout_url(redirect))
        else:
            # In production, we don't want to sign users out of their Google
            # account entirely, because that would break their gmail, youtube,
            # etc. etc. Instead, just clear the cookies on *this* domain that
            # Google creates. That's what self.log_out() does above. So we're
            # done, except for a simple redirect.
            self.redirect(redirect)


class DynamicDocument(ViewHandler):
    def get(self, template, context_id):
        # Attempt to treat id as as project cohort (it might be a program, or
        # invalid).
        project_cohort = ProjectCohort.get_by_id(context_id)

        def todt(s):
            return datetime.datetime.strptime(s, config.iso_date_format)

        if project_cohort:
            # This is a "real" set of instructions with data filled in.
            organization = Organization.get_by_id(
                project_cohort.organization_id)
            liaison = User.get_by_id(organization.liaison_id)
            program = Program.get_config(project_cohort.program_label)
            cohort = program['cohorts'][project_cohort.cohort_label]
            participation_open_date = todt(cohort['open_date'])
            # See notes in program config for why we take a day off for display.
            participation_close_date = (
                todt(cohort['close_date']) - datetime.timedelta(1))
        else:
            # This is a generic example version of the document.
            try:
                program = Program.get_config(context_id)
            except ImportError:
                return self.http_not_found()
            organization = None
            liaison = None
            project_cohort = None
            cohort = None
            participation_open_date = None
            participation_close_date = None

        if template == 'custom_portal_technical_guide':
            # This template doesn't vary by program.
            template_filename = '{}.html'.format(template)
        else:
            template_filename = '{}_{}.html'.format(program['label'], template)

        self.write(
            template_filename,
            organization=organization,
            liaison=liaison,
            program_name=program['name'],
            cohort_name=cohort['name'] if cohort else '',
            program_description=program['description'],
            project_cohort=project_cohort,
            participation_open_date=participation_open_date,
            participation_close_date=participation_close_date,
        )


class RenderedDataset(ViewHandler):
    """Use a dataset to populate and display a report template."""
    def get(self, dataset_id, template, filename):

        # Reuse the permissions from the api endpoint. The function will
        # name error methods without calling them so we can apply them to
        # this response.
        get_permissions = DatasetsApiHandler.__dict__['get_permissions']
        dataset, error_method, error_msg = get_permissions(
            self, dataset_id, self.request.get('token', None))

        # Call whatever error method the permission function specified so all
        # the correct settings are made on this response. Then return without
        # any data.
        if error_method:
            args = tuple() if error_msg is None else (error_msg,)
            return getattr(self, error_method)(*args)

        # The filename isn't actually used, it's just informative for the user
        # and sets the download name. In principle it should match the dataset.
        if filename != dataset.filename:
            logging.warning("Dataset filename doesn't match URL: {}"
                            .format(dataset.filename))

        data = dataset.read()

        self.write(
            template + '.html',
            config=copilot_report_config.config,
            data=data,
            desc='sample report',
            title='sample report',
            **json.loads(data)
        )


class ParticipateApp(ViewHandler):
    """Participant portal, managed by angular."""
    def get(self, *args):
        self.write(
            'dist/participate.html',
            sentry_url=os.environ.get('SENTRY_URL', None),
            triton_domain=os.environ.get('TRITON_DOMAIN', None),
        )


class IndexPage(ViewHandler):
    """All dashboards, from super admin views to specific survey details,
    managed by angular."""
    def get(self, *args, **kwargs):

        self.write(
            'dist/neptune.html',
            is_localhost=util.is_localhost(),
            sentry_url=os.environ.get('SENTRY_URL', None),
            triton_domain=os.environ.get('TRITON_DOMAIN', None),
            include_profiler=os.environ.get('INCLUDE_PROFILER', None) == 'true',
            profiler_includes=gae_mini_profiler.templatetags.profiler_includes()
        )


view_routes = [
    Route('/logout', Logout),
    Route('/admin_login', AdminLogin),
    Route('/<template:facilitator_instructions>/<context_id>', DynamicDocument),
    Route('/<template:student_handout>/<context_id>', DynamicDocument),
    Route('/<template:custom_portal_technical_guide>/<context_id>', DynamicDocument),
    Route('/datasets/<dataset_id>/<template>/<filename>', RenderedDataset),
    Route(r'/participate<:.*>', ParticipateApp),
    # Must go last; sends all paths not described above to angular routing.
    Route(r'/<:.*>', IndexPage),
]
