"""Notification: An alert to a user about some event, with sufficient context
to quickly navigate and take action."""

from collections import defaultdict
from google.appengine.ext import ndb
import json
import logging

from gae_models import Email, DatastoreModel


class Notification(DatastoreModel):
    task_id = ndb.StringProperty()
    # The related organization, project, or survey.
    context_id = ndb.StringProperty()
    subject = ndb.StringProperty()
    body = ndb.TextProperty()
    link = ndb.StringProperty()
    dismissed = ndb.BooleanProperty(default=False)
    autodismiss = ndb.BooleanProperty()
    # Some notifications have nothing to view so they should have no view
    # button, e.g. being rejected from an organization.
    viewable = ndb.BooleanProperty(default=True)

    # There may be an email created to go along with the notification if this
    # entity was just instantiated via Notification.create(). If so, calling
    # notification.put() will also put() the email (and thus put it in the
    # queue for sending).
    email = None

    @classmethod
    def create(klass, **kwargs):
        if 'parent' not in kwargs:
            raise Exception("Notifications must have a parent user.")

        note = super(klass, klass).create(**kwargs)
        note.email = note.create_email()
        return note

    @classmethod
    def filter_redundant(klass, notifications):
        """Remove redundant notifications from a list.

        Example redundant notifications:
        * Joey updated task X to read "bla"
        * Joey updated task X to read "blah"

        ...when both tasks haven't been dismissed.
        """
        # Index notifications by their recipient so we can minimize entity
        # group reads.

        notes_by_parent = defaultdict(list)
        for n in notifications:
            notes_by_parent[DatastoreModel.get_parent_uid(n.uid)].append(n)

        # Filter out redundant notifications from each user.
        for parent_id, new_notes in notes_by_parent.items():

            existing_notes = Notification.get(
                ancestor=DatastoreModel.id_to_key(parent_id))

            def not_redundant(new_note):
                """Does the new note match any existing, undismissed one?"""
                return all([ex.task_id != new_note.task_id or ex.dismissed
                            for ex in existing_notes])

            notes_by_parent[parent_id] = filter(not_redundant, new_notes)

        # Collapse the lists for return.
        return reduce(lambda x, y: x + y, notes_by_parent.values(), [])

    @classmethod
    def get_long_uid(klass, short_uid):
        return super(klass, klass).get_long_uid(
            short_uid, kinds=(klass.__name__, 'User'))

    def create_email(self):
        """Create an email to match the content of the notification if user
        has not set their notification preferences to disable emails.
        """
        recipient = self.key.parent().get()

        # The default is to send an email, unless the user has disabled
        if recipient.notification_option.get('email', None) == 'no':
            return None

        return Email.create(
            to_address=recipient.email,
            subject=self.subject,
            template='notification.html',
            template_data={'subject': self.subject, 'body': self.body,
                           'link': self.link},
        )

    def after_put(self, *args, **kwargs):
        """If fresh from create(), saving a notification to the datastore
        triggers sending the associated email."""
        if self.email:
            self.email.put()
