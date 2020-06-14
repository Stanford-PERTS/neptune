"""ProjectCohort: A project's participation in a cohort.

I.e. One organization participating in one program for a specific period of
time.
"""

from google.appengine.api import memcache, taskqueue
from google.appengine.ext import ndb
from webapp2_extras.appengine.auth.models import Unique
import json
import logging

import model

from gae_models import DatastoreModel, CachedPropertiesModel
import code_phrase
import config
import util


# To save a little IO time, limit the data we query to what we know
# we'll need.
c_fields = ('parent_kind', 'status', 'survey_id', 'uid')

# Although `program_label` isn't listed in the query, survey.py needs it
# for looking up its name from the program.
s_fields = ('ordinal', 'program_label', 'status', 'uid')


class ProjectCohort(DatastoreModel, CachedPropertiesModel):
    project_id = ndb.StringProperty()
    organization_id = ndb.StringProperty()
    program_label = ndb.StringProperty()
    # A machine-readable immutable id for the entire cohort (not project-
    # cohort) matching a program configuration, e.g. spring_2016.
    cohort_label = ndb.StringProperty()
    survey_ids = ndb.StringProperty(repeated=True)

    code = ndb.StringProperty()  # e.g. "silver snake"
    liaison_id = ndb.StringProperty()
    expected_participants = ndb.IntegerProperty()

    # These are ultimately enforced on the client. See valid values and
    # descriptions in nepApi.ProjectCohort.PORTAL_TYPES, and see rules for
    # validating in nepPortal.validatePortalType.
    portal_type = ndb.StringProperty()

    # Defaults to 'default_portal_message' if present in program config.
    # Ignored if 'override_portal_message' is present in program config.
    # Only displays in the 'name_or_id' portal type.
    portal_message = ndb.TextProperty()
    custom_portal_url = ndb.StringProperty()
    survey_params_json = ndb.TextProperty(default=r'{}')

    # Task UIDs of uploaded reports
    completed_report_task_ids = ndb.StringProperty(repeated=True)

    # Whenever someone downloads identifiers from the participation screen,
    # they need to complete a survey, and this records their responses.
    # Structure: {
    #   "yyyy-mm-ddThh:mm:ssZ": {
    #     "submitter_id": "User_X",
    #     "submitter_email": "user@school.edu",
    #     "data": { ... survey form values ... },
    #   },
    #   ...
    # }
    data_export_survey_json = ndb.TextProperty(default=r'{}')

    json_props = ['survey_params_json', 'data_export_survey_json']

    @property
    def survey_params(self):
        return (json.loads(self.survey_params_json)
                if self.survey_params_json else None)

    @survey_params.setter
    def survey_params(self, obj):
        self.survey_params_json = json.dumps(obj)
        return obj

    @property
    def data_export_survey(self):
        return (json.loads(self.data_export_survey_json)
                if self.data_export_survey_json else None)

    @data_export_survey.setter
    def data_export_survey(self, obj):
        self.data_export_survey_json = json.dumps(obj)
        return obj

    # |     value     |                     description                   |
    # |---------------|---------------------------------------------------|
    # | open          | Normal behavior. Org admins can work on setting   |
    # |               | up their program.                                 |
    # | closed        | Contained survey tasks cannot be completed. For   |
    # |               | when the cohort close date has passed or when     |
    # |               | program slots are full.                           |

    status = ndb.StringProperty(default='open')

    @classmethod
    def create(klass, **kwargs):
        # Create Unique code, allowing strongly consistent prevention of
        # duplicates, with retries if necessary.

        code = kwargs.pop('code', None)
        if code is None:
            # No code specified. Generate a unique one.
            # Rather than a while, raise an exception after too many tries.
            for num_tries in range(10):
                code = code_phrase.generate()  # default n=2
                is_unique_code = Unique.create(klass.uniqueness_key(code))
                if is_unique_code:
                    break
            if num_tries >= 3:
                logging.error("Running critically low on codes.")
            if code is None:
                raise Exception("Failed to generate unique code.")
        elif not Unique.create(klass.uniqueness_key(code)):
            # Code specified in creation params. Ensure it's unique.
            raise Exception("Could not create with specified code: {}"
                            .format(code))

        # Use default from the program config.
        if 'program_label' in kwargs:
            conf = model.Program.get_config(kwargs['program_label'])
            if not kwargs.get('portal_type', None):
                kwargs['portal_type'] = conf.get('default_portal_type', None)
            if not kwargs.get('portal_message', None):
                kwargs['portal_message'] = conf.get('default_portal_message',
                                                    None)

        return super(klass, klass).create(code=code, **kwargs)

    @classmethod
    def uniqueness_key(klass, code):
        return u'ProjectCohort.code:{}'.format(code)

    @classmethod
    def batch_cached_properties_from_db(
        klass,
        ids=[],
        project_cohorts=[],
        checkpoints=[],
        organizations=[],
        projects=[],
        surveys=[],
    ):
        if not ids and not project_cohorts:
            return {}

        if not project_cohorts:
            project_cohorts = klass.get_by_id(ids)

        to_get = []

        if not checkpoints:
            # This seems hard right now.
            pass

        if not organizations:
            util.profiler.add_event("getting orgs by id")
            to_get += [pc.organization_id for pc in project_cohorts]

        if not projects:
            util.profiler.add_event("getting projects by id")
            to_get += [pc.project_id for pc in project_cohorts]

        if not surveys:
            util.profiler.add_event("querying surveys")
            to_get += [uid for pc in project_cohorts for uid in pc.survey_ids]

        if to_get:
            entities = DatastoreModel.get_by_id(to_get)
            checkpoints = []
            organizations = []
            projects = []
            surveys = []
            for e in entities:
                if DatastoreModel.get_kind(e) == 'Checkpoint':
                    checkpoints.append(e)
                elif DatastoreModel.get_kind(e) == 'Organization':
                    organizations.append(e)
                elif DatastoreModel.get_kind(e) == 'Project':
                    projects.append(e)
                elif DatastoreModel.get_kind(e) == 'Survey':
                    surveys.append(e)

        orgs_by_id = {o.uid: o for o in organizations}
        projects_by_id = {p.uid: p for p in projects}

        props_by_id = {}
        for pc in project_cohorts:
            pc_surveys = [s for s in surveys if s.project_cohort_id == pc.uid]
            props_by_id[pc.uid] = pc.get_cached_properties_from_db(
                checkpoints=checkpoints,
                organization=orgs_by_id[pc.organization_id],
                project=projects_by_id[pc.project_id],
                surveys=sorted(pc_surveys, key=lambda s: s.ordinal)
            )

        return props_by_id

    def get_cached_properties_from_db(self, checkpoints=[], organization=None,
                                      project=None, surveys=[]):
        """Doesn't use memcache; see get_ and update_cached_properties."""
        # Either use the data passed in (if part of a batch) or query for it.
        return {
            'checkpoints': (checkpoints if checkpoints else
                            model.Checkpoint.for_tasklist(self, fields=c_fields)),
            'organization': (organization if organization else
                             model.Organization.get_by_id(self.organization_id)),
            'project': (project if project else
                        model.Project.get_by_id(self.project_id)),
            'surveys': (surveys if surveys else
                        model.Survey.get(project_cohort_id=self.uid,
                                         order='ordinal', projection=s_fields)),
        }

    def after_put(self, *args, **kwargs):
        """Clear any cached queries related to this."""
        kwargs = {'program_label': self.program_label,
                  'cohort_label': self.cohort_label}
        to_delete = [
            util.cached_query_key('SuperDashboard',
                                  organization_id=self.organization_id),
            util.cached_query_key('SuperDashboard', **kwargs),
        ]
        taskqueue.add(
            url='/task/cache_dashboard',
            headers={'Content-Type': 'application/json; charset=utf-8'},
            payload=json.dumps(kwargs),
            countdown=config.task_consistency_countdown,
        )

        memcache.delete_multi(to_delete)

    def tasklist_name(self):
        program_config = model.Program.get_config(self.program_label)
        return 'Application to join {cohort} in {program}'.format(
            cohort=program_config['cohorts'][self.cohort_label]['name'],
            program=program_config['name'])

    def to_client_dict(self):
        d = super(ProjectCohort, self).to_client_dict()

        # Portal messages were originally built to be customizable for each
        # project cohort. We've since found that it's more convenient to set
        # them in config for the whole program so they can be easily changed.
        program_config = model.Program.get_config(self.program_label)
        override = program_config.get('override_portal_message', None)
        if override:
            d['portal_message'] = override

        return d
