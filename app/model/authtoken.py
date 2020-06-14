"""AuthToken: Temporary code for a user to authenticate, confirm
email, or change their password from a link.
"""


from google.appengine.ext import ndb
import datetime
import logging

from gae_models import DatastoreModel


class AuthToken(DatastoreModel):
    """Acts as a one-time-pass for a user to take some sensitive action.

    Children of a user. The "token" is just the uid of a AuthToken entity.
    """

    duration = ndb.IntegerProperty(default=48)  # number of hours
    token = ndb.ComputedProperty(lambda self: self.short_uid)

    @classmethod
    def create(klass, user_id, duration=None):
        klass.clear_all_tokens_for_user(user_id)
        user_key = DatastoreModel.id_to_key(user_id)
        if duration is None:
            duration = klass.duration._default
        return super(klass, klass).create(parent=user_key, duration=duration)

    @classmethod
    def create_or_renew(klass, user_id, duration=None):
        """Attempt to find and renew a valid token, else create one."""
        logging.info("AuthToken.create_or_renew()")
        valid_token = None
        for t in klass.get_all_tokens_for_user(user_id):
            if not t.is_expired():
                valid_token = t
                valid_token.created = datetime.datetime.utcnow()
                valid_token.put()
                break

        return valid_token or klass.create(user_id, duration)

    @classmethod
    def check_token_string(klass, token_string):
        """Validate a token in a password reset URL.

        Returns: tuple as (user, error)
            * user is a User entity or None
            * error is a string:
                - 'not found' if the token doesn't exist
                - 'used' if the token does exist but has deleted = True
                - 'expired' if the token exists, is not delete, but has expired
        """
        # Bypass DatastoreModel.get_by_id to make sure we pick up any entites that have
        # deleted = True.
        user = None
        error = None

        # The token string is user input; treat with caution b/c it may not
        # be a valid/interpretable uid.
        key = AuthToken.id_to_key(token_string)
        if not key:
            error = 'not found'
            return (user, error)

        token = key.get()
        if not token:
            error = 'not found'
        elif token.deleted:
            error = 'used'
        elif token.is_expired():
            error = 'expired'
        else:
            user = token.get_user()

        return (user, error)

    @classmethod
    def mark_as_used(klass, token_string):
        t = AuthToken.get_by_id(token_string)
        t.deleted = True
        t.put()

    @classmethod
    def clear_all_tokens_for_user(klass, user_id):
        """Delete all tokens for a given user."""
        tokens_to_put = []
        for t in klass.get_all_tokens_for_user(user_id):
            t.deleted = True
            tokens_to_put.append(t)
        ndb.put_multi(tokens_to_put)

    @classmethod
    def get_all_tokens_for_user(klass, user_id):
        user_key = DatastoreModel.id_to_key(user_id)
        results = AuthToken.get(n=float('inf'), ancestor=user_key)
        return results

    @classmethod
    def get_long_uid(klass, short_uid):
        return super(klass, klass).get_long_uid(
            short_uid, kinds=(klass.__name__, 'User'))

    def is_expired(self):
        duration = datetime.timedelta(hours=self.duration)
        # Use utcnow() b/c our unit tests use local python runtimes, which may
        # vary in timezone setting, while the production App Engine runtime is
        # always in UTC. This forces everything to UTC.
        return datetime.datetime.utcnow() - self.created > duration

    def get_user(self):
        return self.key.parent().get()
