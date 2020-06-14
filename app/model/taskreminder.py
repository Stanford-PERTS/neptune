"""TaskReminder: A convenience object for describing a user's current tasks in
the UI. Children of a user.

Created in TaskList.create()

Created for org admins only. Progs and supers will have nice admin interfaces
and training and won't need this kind of reminder.

Which org admins get them?

* Organization tasklists: organization owners
* All other kinds of tasklists: project liaisons.

When tasklists are finished, corresponding task reminders are deleted; this
happens in Tasklist.close()

When the liaison of a project changes, task reminders are transferred to the
new liaision; this happens in TaskReminder.transfer_liaisons()
"""

from google.appengine.ext import ndb
import logging

from gae_models import DatastoreModel


class TaskReminder(DatastoreModel):
    context_id = ndb.StringProperty()  # organization, project, or survey id
    description = ndb.TextProperty()  # e.g. "Chicago Academy Application"
    url = ndb.StringProperty()  # e.g. "/dashboard/projects/ABC"

    @classmethod
    def create(klass, entity, recipient):
        return super(klass, klass).create(
            parent=recipient,
            context_id=entity.uid,
            description=entity.tasklist_name(),
            url='/{}/{}'.format(DatastoreModel.get_url_kind(entity),
                                entity.uid),
        )

    @classmethod
    def delete_task_reminders(klass, parent_id):
        """Delete all TaskReminders related to a tasklist.

        Doesn't attempt to be strongly consistent because tasklists won't be
        opened and closed again in a short amount of time.
        """
        # Most tasklists will have only one TaskReminder-the one with its
        # project liaison. If this is an org tasklist, there may be many
        # owners.
        tr_keys = klass.get(context_id=parent_id, n=100, keys_only=True)
        if len(tr_keys) == 100:
            logging.error(
                "Found 100 TaskReminders for {}. This shouldn't happen."
                .format(parent_id))
        else:
            logging.info("TaskReminder.delete_task_reminders({}): {}"
                         .format(parent_id, tr_keys))
        ndb.delete_multi(tr_keys)

    @classmethod
    def transfer_reminder(klass, tasklist_parent, new_recipient):
        klass.delete_task_reminders(tasklist_parent.uid)
        return klass.create(
            parent=new_recipient,
            context_id=tasklist_parent.uid,
            description=tasklist_parent.tasklist_name(),
        )

    @classmethod
    def get_long_uid(klass, short_uid):
        return super(klass, klass).get_long_uid(
            short_uid, kinds=(klass.__name__, 'User'))
