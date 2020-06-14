from google.appengine.ext import ndb
from mapreduce import operation as op, context
from webapp2_extras.appengine.auth.models import Unique
import json
import logging
import traceback

from gae_handlers import BaseHandler, Route
from model import DatastoreModel, ProjectCohort, Survey, Task


class MapHandler(BaseHandler):
    """Superclass for all mapreduce-related urls.

    Very similar to ApiHandler, but with fewer security concerns (app.yaml
    enforces that only app admins can reach these endpoints).
    """

    def dispatch(self, *args, **kwargs):
        """Wrap all cron calls in a try/catch so we can log a trace."""

        # app.yaml specifies that only project admins can hit these URLs, so
        # don't worry further about permissions.

        self.response.headers['Content-Type'] = (
            'application/json; charset=utf-8')

        try:
            # Call the descendant handler's method matching the appropriate
            # verb, GET, POST, etc.
            BaseHandler.dispatch(self)

        except Exception as error:
            self.error(500)
            trace = traceback.format_exc()
            logging.error("{}\n{}".format(error, trace))
            response = "{}: {}\n\n{}".format(
                error.__class__.__name__, error, trace)
            self.response.write(json.dumps(response))

        else:
            # If everything about the request worked out, but no data was
            # returned, put out a standard empty response.
            if not self.response.body:
                self.write(None)

    def write(self, obj):
        # In the extremely common cases where we want to return an entity or
        # a list of entities, translate them to JSON-serializable dictionaries.
        if isinstance(obj, DatastoreModel):
            obj = obj.to_client_dict()
        elif type(obj) is list and all([isinstance(x, DatastoreModel) for x in obj]):
            obj = [x.to_client_dict() for x in obj]
        self.response.write(json.dumps(obj))


def add_survey_ids_to_project_cohorts(project_cohort):
    """To make batch querying of dashboard views easier, we want to be able to
    get surveys by id, given project cohorts. This is a change to how pcs are
    created, so legacy data needs updating.

    Configure this job in map_reduce.yaml and initiate it from /mapreduce. You
    must be signed in as a project admin.

    See: https://sookocheff.com/post/appengine/mapreduce/mapreduce-yaml/
    """
    if len(project_cohort.survey_ids) > 0:
        return

    keys = Survey.get(project_cohort_id=project_cohort.uid, keys_only=True)
    project_cohort.survey_ids = [k.id() for k in keys]
    yield op.db.Put(project_cohort)


def fix_open_responses(project_cohort):
    if project_cohort.program_label == 'triton':
        # This correctly has the open response flag. Leave it alone.
        return

    survey_params = project_cohort.survey_params
    survey_params.pop('show_open_response_questions', None)
    project_cohort.survey_params = survey_params

    yield op.db.Put(project_cohort)


def change_default_user_type(user):
    # See #985
    if user.user_type == 'org_admin':
        user.user_type = 'user'
        yield op.db.Put(user)


def add_completed_report_task_ids_to_project_cohort(task):
    """See Issue #1020 & PR #1062. In order to facilitate creating the
    Returning Organizations report, we need to know which Project Cohorts
    are returning. Returning is defined as an Organization that has
    participated in a previous cohort and has enrolled again. We are counting
    Project Cohorts as having participated if they have a completed report
    uploaded. This job adds the UID of report tasks that have a file attached
    to the associated Project Cohort's completed_report_task_ids property."""

    report_task_labels = [
        'cg17_survey__report_1',
        'cb17_survey__report_1',
        'hg17_survey__report_2',
        'sse_survey__report_1'
    ]

    if task.label in report_task_labels and task.attachment:
        parent_key = task.key.parent()
        survey = parent_key.get()
        project_cohort = ProjectCohort.get_by_id(survey.project_cohort_id)

        if (project_cohort and
            task.uid not in project_cohort.completed_report_task_ids):
                project_cohort.completed_report_task_ids.append(task.uid)
                yield op.db.Put(project_cohort)


def parse_poid(org):
    import re

    nces_district_pattern = re.compile(r'NCES *District[a-z :]*(\d+)',re.I)
    nces_school_pattern = re.compile(r'NCES *School[a-z :]*(\d+)', re.I)
    ipeds_pattern = re.compile(r'IPEDS[a-z :]*(\d+)', re.I)
    ope_pattern = re.compile(r'OPE[a-z :]*(\d+)', re.I)

    def first_group(pattern, subject=''):
        m = re.search(pattern, subject)
        if m and len(m.groups()):
            return m.group(1)
        return None

    org.nces_district_id = first_group(nces_district_pattern, org.poid)
    org.nces_school_id = first_group(nces_school_pattern, org.poid)
    org.ipeds_id = first_group(ipeds_pattern, org.poid)
    org.ope_id = first_group(ope_pattern, org.poid)

    yield op.db.Put(org)


def delete_all_survey_links(sl):
    yield op.db.Delete(sl)


def delete_for_program(entity):
    """Permanently delete anything in the datastore from a program.

    Works with Projects, ProjectCohorts, and Surveys. Also requires a param set
    in mapreduce.yaml: `program_label`.
    """
    params = context.get().mapreduce_spec.mapper.params
    if getattr(entity, 'program_label', None) != params['program_label']:
        return

    # If this is a project cohort, delete the Unique entity that serves as an
    # index of participation codes.
    key_name = ProjectCohort.uniqueness_key(getattr(entity, 'code', ''))
    unique_entity = ndb.Key('Unique', key_name).get()
    if unique_entity:
        yield op.db.Delete(unique_entity)

    # Some entities have tasks in their entity group. There's no convenient
    # way to query tasks directly, so delete them while we're handling their
    # parent.
    # Bypass DatastoreModel to make sure we get soft-deleted entities.
    for task in Task.query(ancestor=entity.key).iter():
        yield op.db.Delete(task)

    yield op.db.Delete(entity)

map_routes = [
    # Route('/map/do_some_job', DoSomeJobHandler),
]
