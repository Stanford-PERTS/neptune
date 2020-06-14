"""Project: A team from some organization participating in a program."""

from collections import OrderedDict
from google.appengine.api import memcache, taskqueue
from google.appengine.ext import ndb
import json
import logging

from gae_models import DatastoreModel, CachedPropertiesModel
import config
import model
import util


class Project(DatastoreModel, CachedPropertiesModel):
    organization_id = ndb.StringProperty()

    # These two additional properties are available to the client, added in
    # to_client_dict().
    # organization_name
    # organization_status

    program_label = ndb.StringProperty()
    # The program_admin assigned to handle communication for this project.
    account_manager_id = ndb.StringProperty()
    # The non-admin user assigned to handle communication for this project.
    liaison_id = ndb.StringProperty()
    # PERTS has schools that we have a special connection with, so they are
    # given priority in certain programs. This allows us to highlight these
    # schools in admin interfaces.
    priority = ndb.BooleanProperty(default=False)
    deidentification_method = ndb.StringProperty()
    # Admin notes regarding the Letter of Agreement.
    loa_notes = ndb.TextProperty()
    # The last time a project or survey task was updated by an org admin.
    last_active = ndb.DateTimeProperty()

    # After creation, this will have a tasklist object, which in turn will
    # have checkpoints and tasks that need saving to their respective
    # databases.
    tasklist = None

    @classmethod
    def create(klass, **kwargs):
        """Validate program relationship, create task lists."""

        project = super(klass, klass).create(**kwargs)

        program_config = model.Program.get_config(project.program_label)

        # Build the task list.
        template = program_config['project_tasklist_template']
        project.tasklist = model.Tasklist.create(
            template, project, program_label=project.program_label,
            organization_id=project.organization_id)

        # Assign a default account manager, if available.
        am_email = program_config.get('default_account_manager', '')
        if model.User.email_exists(am_email):
            am = model.User.get_by_auth('email', am_email)
            project.account_manager_id = am.uid

        return project

    def after_put(self, *args, **kwargs):
        if self.tasklist:
            # Tasklist might not always be present; it is if created via
            # create(), but not if fetched from the datastore.
            self.tasklist.put()

        # Reset memcache for cached properties of related objects.
        # This relationship is "down" so there may be many keys to clear so
        # don't try to actually refresh the cached values, just set up a cache
        # miss for their next read and they'll recover.
        to_delete = []

        for pc in model.ProjectCohort.get(n=float('inf'), project_id=self.uid):
            # These keys are for individual project cohort entities.
            to_delete.append(util.cached_properties_key(pc.uid))
            # These are for caches of whole query results.
            kwargs = {'program_label': pc.program_label,
                      'cohort_label': pc.cohort_label}
            to_delete.append(util.cached_query_key('SuperDashboard', **kwargs))
            taskqueue.add(
                url='/task/cache_dashboard',
                headers={'Content-Type': 'application/json; charset=utf-8'},
                payload=json.dumps(kwargs),
                countdown=config.task_consistency_countdown,
            )
        # Also clear the dashboard's organization query.
        to_delete.append(
            util.cached_query_key('SuperDashboard',
                                  organization_id=self.organization_id)
        )

        memcache.delete_multi(to_delete)

    def tasklist_name(self):
        program_config = model.Program.get_config(self.program_label)
        org = DatastoreModel.get_by_id(self.organization_id)
        return 'Application for {org} to join {program}'.format(
            org=org.name, program=program_config['name'])

    def liaison(self):
        return DatastoreModel.get_by_id(self.liaison_id)

    @classmethod
    def batch_cached_properties_from_db(
        klass,
        ids=[],
        projects=[],
        organizations=[],
        programs=[],
    ):
        if not ids and not projects:
            return {}

        if not projects:
            projects = klass.get_by_id(ids)

        if not organizations:
            organizations = model.Organization.get_by_id(
                [p.organization_id for p in projects]
            )

        if not programs:
            labels = set(p.program_label for p in projects)
            programs = [model.Program.get_config(l) for l in labels]

        orgs_by_id = {o.uid: o for o in organizations}
        programs_by_label = {p['label']: p for p in programs}

        props_by_id = {}
        for p in projects:
            props_by_id[p.uid] = p.get_cached_properties_from_db(
                organization=orgs_by_id[p.organization_id],
                program=programs_by_label[p.program_label],
            )

        return props_by_id

    def get_cached_properties_from_db(self, organization=None, program=None):
        """Add program- and organization-derived properties for convenience."""
        if not organization:
            organization = model.Organization.get_by_id(self.organization_id)

        if not program:
            program = model.Program.get_config(self.program_label)

        return {
            'program_name': program['name'],
            'program_description': program['description'],
            'organization_name': organization.name if organization else None,
            'organization_status': organization.status if organization else None,
        }

    def to_client_dict(self):
        """Decorate with counts of related objects; cached."""
        d = super(Project, self).to_client_dict()

        d.update(self.get_cached_properties())

        # Keep client dict ordered
        return OrderedDict((k, d[k]) for k in sorted(d.keys()))
