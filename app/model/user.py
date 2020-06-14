"""
User
===========

Represents Neptune users.

## Notes on public users:

BaseHandler.get_current_user() returns a public user object when there is no
one signed in. Public users are like regular users except:

* They are never saved to the datastore. Trying to put() one raises an
  exception.
* They have user_type 'public'.
* They are falsey, i.e. `bool(public_user)` is False, accomplished via the
  __nonzero__ magic method.

Public users are useful because you can always expect a user back from
get_current_user() and test for ownership or other properties without raising
any errors. They are also used to give users who aren't signed in access to
certain internal pages we want to intentionally expose, e.g. demo
tasklists.

Public users are related to public data, see BaseHandler.create_public_data().
The owns() method in permission.py has special rules regarding this data such
that all users, even public ones, 'own' public data.
"""

from google.appengine.ext import ndb
from webapp2_extras.appengine.auth.models import Unique
import json
import logging
import random
import re
import string

from gae_models import DatastoreModel
from passlib.context import CryptContext

from .notification import Notification
import config
import util


class BadPassword(Exception):
    """Password doesn't match required pattern."""
    pass


class DuplicateUser(Exception):
    """A user with the provided email already exists."""
    pass


class User(DatastoreModel):
    """Neptune users."""

    # tl;dr: values forced to lower case before storage here AND in
    # uniqueness_key()!
    #
    # Emails are stored in two places and must match across them to make
    # sure we don't get duplicate users: in User.email and the key name of
    # the corresponding Unique entity (see uniqueness_key()). And because
    # email addresses are effectively case insensitive while our databases
    # are case sensistive, force them all to lower case before storage.
    # Because people _do_ vary their capitalization between sessions. See
    # #387.
    email = ndb.StringProperty(required=True,
                               validator=lambda prop, value: value.lower())
    name = ndb.StringProperty()
    role = ndb.StringProperty()
    phone_number = ndb.StringProperty()
    hashed_password = ndb.StringProperty()
    google_id = ndb.StringProperty()
    # user type can be: super_admin, program_admin, user, public
    user_type = ndb.StringProperty(default='user')
    # notification option has two possible keys:
    # {
    #   "email": ("yes"|"no"),
    #   "sms":  ("yes"|"no")
    # }
    notification_option_json = ndb.TextProperty(default=r'{}')
    owned_organizations = ndb.StringProperty(repeated=True)
    assc_organizations = ndb.StringProperty(repeated=True)
    owned_programs = ndb.StringProperty(repeated=True)
    owned_projects = ndb.StringProperty(repeated=True)
    assc_projects = ndb.StringProperty(repeated=True)
    owned_data_tables = ndb.StringProperty(repeated=True)
    owned_data_requests = ndb.StringProperty(repeated=True)
    last_login = ndb.DateTimeProperty()

    # App Engine can only run pure-python external libraries, and so we can't get
    # a native (C-based) implementation of bcrypt. Pure python implementations are
    # so slow that [the feasible number of rounds is insecure][1]. This uses the
    # [algorithm recommended by passlib][2].
    # [1]: http://stackoverflow.com/questions/7027196/how-can-i-use-bcrypt-scrypt-on-appengine-for-python
    # [2]: https://pythonhosted.org/passlib/new_app_quickstart.html#sha512-crypt
    password_hashing_context = CryptContext(
        schemes=['sha512_crypt', 'sha256_crypt'],
        default='sha512_crypt',
        all__vary_rounds=0.1,
        # Can change hashing rounds here. 656,000 is the default.
        # sha512_crypt__default_rounds=656000,
        # sha256_crypt__default_rounds=656000,
    )

    json_props = ['notification_option_json']


    @property
    def super_admin(self):
        return self.user_type == 'super_admin'

    @property
    def non_admin(self):
        # Matches either value while we transition. See #985.
        return self.user_type in ('org_admin', 'user')

    @property
    def notification_option(self):
        return (json.loads(self.notification_option_json)
                if self.notification_option_json else None)

    @notification_option.setter
    def notification_option(self, obj):
        self.notification_option_json = json.dumps(obj)
        return obj

    @classmethod
    def create(klass, **kwargs):
        # Create Unique entity based on email, allowing strongly consistent
        # prevention of duplicates.
        is_unique_email = Unique.create(User.uniqueness_key(kwargs['email']))
        if not is_unique_email:
            raise DuplicateUser("There is already a user with email {}."
                                .format(kwargs['email']))

        return super(klass, klass).create(**kwargs)

    @classmethod
    def create_public(klass):
        return super(klass, klass).create(
            id='public',
            name='public',
            email='public',
            user_type='public',
        )

    @classmethod
    def uniqueness_key(klass, email):
        # See #387.
        return u'User.email:{}'.format(email.lower())

    @classmethod
    def email_exists(klass, email):
        """Test if this email has been registered, idempotent."""
        return Unique.get_by_id(User.uniqueness_key(email)) is not None

    @classmethod
    def get_by_auth(klass, auth_type, auth_id):
        # All stored emails are in lower case. If we hope to find them, need
        # to lower case the search param. See #387.
        if auth_type == 'email':
            auth_id = auth_id.lower()

        matches = User.get(order='created', **{auth_type: auth_id})

        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            logging.error(u"More than one user matches auth info: {}, {}."
                          .format(auth_type, auth_id))

            # We'll let the function pass on and take the first of multiple
            # duplicate users, which will be the earliest-created one.
            return matches[0]

    @classmethod
    def property_types(klass):
        """Overrides DatastoreModel. Prevents hashed_password from being set."""
        props = super(klass, klass).property_types()
        props.pop('hashed_password', None)
        return props

    @classmethod
    def example_params(klass):
        name = ''.join(random.choice(string.ascii_uppercase)
                       for c in range(3))
        return {
            'name': name,
            'email': name + '@example.com',
            'phone_number': '+1 (555) 555-5555',
            'hashed_password': 'foo',
            'user_type': random.choice(
                ['user', 'program_admin', 'super_admin']),
        }

    @classmethod
    def hash_password(klass, password):
        if re.match(config.password_pattern, password) is None:
            raise BadPassword(u'Bad password: {}'.format(password))
        return klass.password_hashing_context.encrypt(password)

    @classmethod
    def verify_password(klass, password, hashed_password):
        return (klass.password_hashing_context.verify(password, hashed_password)
                if hashed_password else False)

    def __nonzero__(self):
        return False if getattr(self, 'user_type', None) == 'public' else True

    def before_put(self, *args, **kwargs):
        if self.user_type == 'public':
            raise Exception("Public user cannot be saved.")

    def to_client_dict(self, **kwargs):
        """Overrides DatastoreModel, modifies behavior of hashed_password.

        Change hashed_password to a boolean so client can detect if a user
        hasn't set their password yet. Also prevent hash from be unsafely
        exposed.
        """
        output = super(User, self).to_client_dict()
        output['hashed_password'] = bool(self.hashed_password)
        return output

    def create_reset_link(self, domain, token, continue_url='', case=''):
        """Create the kind of jwt-based set password link used by Triton.

        Args:
            domain: str, beginning with protocol, designed this way to make it
                easier to switch btwn localhost on http and deployed on https.
            continue_url: str, page should support redirecting user to this url
                after successful submission
            case: str, either 'reset' or 'invitation', aids the UI in
                displaying helpful text based on why the user has arrived.
        """
        return util.set_query_parameters(
            '{}/set_password/{}'.format(domain, token),
            continue_url=continue_url,
            case=case,
        )

    def get_organizations(self):
        """Get the organizations associated with this user."""
        all_ids = self.owned_organizations + self.assc_organizations
        return DatastoreModel.get_by_id(all_ids)

    def notifications(self):
        """Get notifications associated with this user."""
        return Notification.get(ancestor=self, n=20)

    def get_owner_property(self, id_or_entity):
        owner_props = {
            'Organization': 'owned_organizations',
            'Program': 'owned_programs',
            'Project': 'owned_projects',
            'DataTable': 'owned_data_tables',
            'DataRequest': 'owned_data_requests',
        }
        kind = DatastoreModel.get_kind(id_or_entity)
        return getattr(self, owner_props[kind])if kind in owner_props else None

    def __str__(self):
        """A string represenation of the entity. Goal is to be readable.

        Returns, e.g. <User_oha4tp8a:foo@bar.com>.
        Overrides method from DatastoreModel by adding email address.
        """
        return '<{}:{}>'.format(self.key.id(), self.email)
