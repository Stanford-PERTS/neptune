"""Tasklist: collection of tools for managing task lists.

Tasklists are tasks nested within checkpoints, but have no database
representation of their own.
"""

from google.appengine.ext import ndb
import json

from gae_models import DatastoreModel
from .checkpoint import Checkpoint
from .task import Task
from .taskreminder import TaskReminder
from .user import User


class Tasklist():
    parent = None
    checkpoints = []
    tasks = []

    @classmethod
    def create(klass, tasklist_template, parent, **checkpoint_kwargs):
        """Instantiate checkpoints and tasks based on a tasklist template."""

        allowed_kwargs = [
            'organization_id',
            'program_label',
            'project_id',
            'cohort_label',
            'project_cohort_id',
            'survey_id',
        ]
        if [k for k in checkpoint_kwargs.keys() if k not in allowed_kwargs]:
            raise Exception("Invalids kwargs: {}".format(checkpoint_kwargs))

        # Parent entity is used for both tasks and checkpoints. Add it to
        # checkpoint kwargs here.
        checkpoint_kwargs['parent_id'] = parent.uid

        # Tasks uses the program label to quickly look up their definitions,
        # but only when it applies (e.g. not org tasks).
        task_kwargs = {}

        # Parent id stored redundantly for convenience. Deduce which extra
        # properties be filled in automatically.
        parent_kind = DatastoreModel.get_kind(parent)
        if parent_kind == 'Organization':
            checkpoint_kwargs['organization_id'] = parent.uid
        elif parent_kind == 'Project':
            checkpoint_kwargs['project_id'] = parent.uid
            task_kwargs['program_label'] = parent.program_label
        elif parent_kind == 'Survey':
            checkpoint_kwargs['survey_id'] = parent.uid
            checkpoint_kwargs['project_cohort_id'] = parent.project_cohort_id
            task_kwargs['program_label'] = parent.program_label

        # Dynamically assign ordinals; easier to maintain than hardcoding them.
        for i, checkpoint_tmpl in enumerate(tasklist_template):
            checkpoint_tmpl['ordinal'] = i + 1

        # Convert templates to checkpoint dictionaries that have ids, merging
        # in all the relationship information that is the same for each.
        checkpoints = []
        for checkpoint_tmpl in tasklist_template:
            merged_params = dict(checkpoint_tmpl.copy(), **checkpoint_kwargs)
            checkpoints.append(Checkpoint.create(**merged_params))

        # Dynamically assign ordinals; easier to maintain than hardcoding them.
        # Note that task ordinals count _across_ checkpoints; i.e. task
        # ordinals ignore checkpoints.
        tasks = []
        task_ord = 1
        for i, checkpoint_tmpl in enumerate(tasklist_template):
            checkpoint = checkpoints[i]
            checkpoint_task_ids = []
            for task_tmpl in checkpoint_tmpl['tasks']:
                # Mix in any initial values specified for _this_ task to the
                # kwargs that are the same for every task.
                kwargs = task_kwargs.copy()
                kwargs.update(task_tmpl.get('initial_values', {}))
                task = Task.create(
                    task_tmpl['label'], task_ord, checkpoint.uid,
                    parent=parent, **kwargs
                )
                tasks.append(task)
                checkpoint_task_ids.append(task.uid)
                task_ord += 1
            checkpoint.task_ids = json.dumps(checkpoint_task_ids)

        return Tasklist(parent, checkpoints, tasks)

    def __init__(self, parent, checkpoints=None, tasks=None):
        """Checkpoints and tasks provided when called via create(); otherwise
        provides access to parent-related instance methods."""
        self.parent = parent
        self.checkpoints = checkpoints
        self.tasks = tasks

    def put(self):
        # Save the checkpoints and tasks that make up the tasklist.
        Checkpoint.put_multi(self.checkpoints)
        ndb.put_multi(self.tasks)  # we'll want to render the tasks right away

    def status(self):
        """Check checkpoint status, returns 'complete' or 'incomplete'."""
        checkpoints = Checkpoint.get(parent_id=self.parent.uid)
        if all([c.status == 'complete' for c in checkpoints]):
            return 'complete'
        else:
            return 'incomplete'

    def open(self, new_owner=None):
        """Called on any checkpoint update that doesn't close the tasklist.

        So far manages creation of TaskReminder entities.
        """
        if DatastoreModel.get_kind(self.parent) == 'Organization':
            org_id = self.parent.uid
        else:
            org_id = self.parent.organization_id

        # Include any user who was just recently (in this request) added to
        # the org, because a general query of org owners will be inconsistent.
        # If there are more than 100 owners, oh well, they don't get task
        # reminders.
        owners = User.get(owned_organizations=org_id, n=100)
        if (new_owner and new_owner.non_admin and new_owner not in owners):
            owners.append(new_owner)

        trs = []
        for owner in owners:
            # Only save a task reminder if one doesn't already exist for this
            # user and tasklist.
            num_existing = TaskReminder.count(ancestor=owner,
                                              context_id=self.parent.uid)
            if num_existing == 0:
                tr = TaskReminder.create(self.parent, owner)
                trs.append(tr)

        ndb.put_multi(trs)

    def close(self):
        """Cleaning house when a tasklist is done."""
        TaskReminder.delete_task_reminders(self.parent.uid)
