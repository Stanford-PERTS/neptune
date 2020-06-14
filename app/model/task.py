"""Task: One action to be taken in the context of an organization, project, or
survey.

Tasks have a complex initialization.

**Datastore-backed properties**

Some properties are part of the Task entity in the datastore, which are listed
below. These are mutable and persistent.

**Hard-coded configuration properties**

These are defined by the program configuration with the matching task label,
e.g. in demo-program.py. These are immutable (except in the case where one
changes the source code) and are combined with the entity after it is retrieved
from the datastore in to_client_dict() below.

**On-initialization configuration properties**

The program configuration can also specify `initial_values` for datastore
properties that may be different than the defaults specified here. These only
take effect within create(). Thereafter datastore-backed properties reflect
datastore values.
"""

from collections import OrderedDict
from google.appengine.ext import ndb
import jinja2
import logging

from gae_models import DatastoreModel
from .program import Program
import organization_tasks


class Task(DatastoreModel):
    label = ndb.StringProperty()
    program_label = ndb.StringProperty()
    checkpoint_id = ndb.StringProperty()
    # Always 'complete' or 'incomplete'
    status = ndb.StringProperty(default='incomplete')
    # Can be set to true in the manager app if this task is determined to be
    # inapplicable for some reason.
    # Example: User chooses a 'generic' portal type, in which case setting
    # the custom portal url isn't applicable, and the corresponding task is
    # disabled.
    disabled = ndb.BooleanProperty(default=False)
    ordinal = ndb.IntegerProperty()
    due_date = ndb.DateProperty()
    completed_date = ndb.DateProperty()
    completed_by_id = ndb.StringProperty()
    completed_by_name = ndb.StringProperty()  # "Doofus McAdmin"
    attachment = ndb.TextProperty()  # e.g. S3 URL, JSON, user input

    ### Dynamic properties pulled from program/tasklist definitions. ###

    # name
    # body
    # action_statement
    # # Designed to be HTML-friendly to make rendering easy. Current convention
    # # is <tag>[:<type>], e.g. "input:date", "select", or "textarea".
    # data_type
    # # Only used if data type is 'radio' or 'select'.
    # select_options
    # # Some tasks will not be editable by the org admin, e.g. approvals. A
    # # program admin who owns the parent program may always edit, and naturally
    # # a super admin may always edit.
    # non_admin_may_edit  # boolean
    # # True if this is a task that is used to determine that a program has
    # # been completed for participated status
    # counts_as_program_complete # boolean

    default_config = {
        'name': "PERTS Internal Use",
        'body': "<p>For internal use.</p>",
        'action_statement': None,
        'data_type': 'button',
        'non_admin_may_edit': False,
        'counts_as_program_complete': False,
    }

    jinja_environment = jinja2.Environment(
        autoescape=True,
        extensions=['jinja2.ext.autoescape'],
    )

    @property
    def short_uid(self):
        raise Exception("The parent kind for a Task is ambiguous; can't use "
                        "short ids.")

    @classmethod
    def create(klass, label, ordinal, checkpoint_id, **kwargs):
        kwargs['label'] = label
        kwargs['ordinal'] = ordinal
        kwargs['checkpoint_id'] = checkpoint_id

        if 'parent' not in kwargs:
            raise Exception("Tasks must have a parent.")

        if label == 'organization__registration':
            # This task is always complete, because it's just a placeholder
            # for the registration step that comes before real tasks.
            kwargs['status'] = 'complete'
            kwargs['attachment'] = 'true'

        return super(klass, klass).create(**kwargs)

    def get_task_config(self):
        parent_kind = DatastoreModel.get_kind(DatastoreModel.get_parent_uid(self.uid))

        if parent_kind == 'Organization':
            tasklist = organization_tasks.tasklist_template
            for checkpoint in tasklist:
                for task in checkpoint['tasks']:
                    if task['label'] == self.label:
                        return task
        elif parent_kind == 'Project':
            program = Program.get_config(self.program_label)
            for checkpoint in program['project_tasklist_template']:
                for task in checkpoint['tasks']:
                    if task['label'] == self.label:
                        return task
        elif parent_kind == 'Survey':
            program = Program.get_config(self.program_label)
            for survey in program['surveys']:
                for checkpoint in survey['survey_tasklist_template']:
                    for task in checkpoint['tasks']:
                        if task['label'] == self.label:
                            return task

        return self.default_config.copy()

    def to_client_dict(self):
        """Add properties from the template."""
        d = super(Task, self).to_client_dict()

        d['parent_id'] = DatastoreModel.get_parent_uid(self.uid)
        d['short_parent_id'] = DatastoreModel.convert_uid(d['parent_id'])

        # Copy in all the properties that are defined in the program config.
        # This means that changes to the config will immediately reflect on
        # the site, rather than persisting in legacy datastore entities.
        config = self.get_task_config()
        props = ['name', 'body', 'action_statement', 'data_type',
                 'select_options', 'non_admin_may_edit',
                 'counts_as_program_complete']
        d.update({p: config.get(p, None) for p in props})

        # Added Nov 2019, with default value.
        d['data_admin_only_visible'] = config.get('data_admin_only_visible', False)

        return OrderedDict((k, d[k]) for k in sorted(d.keys()))
