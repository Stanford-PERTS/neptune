"""URL Handlers are designed to be simple wrappers over our python API layer.
They generally convert a URL directly to an API function call.
"""

from google.appengine.api import users as app_engine_users
from google.appengine.ext import ndb
from io import BytesIO
from MySQLdb import IntegrityError
import datetime
import hashlib
import itertools
import json
import logging
import os
import random
import string
import unicodecsv

from gae_handlers import (ApiHandler, RestHandler, Route)
from graphql_handlers import (DashboardByOwner, GraphQLBase, SuperDashboard,
                              TasklistHandler)
from model import (AccountManager, AuthToken, BadPassword, Checkpoint,
                   Email, Liaisonship, DatastoreModel, Notification, Organization,
                   Participant, Program, ParticipantData, Project,
                   ProjectCohort, SecretValue, Survey, SurveyLink, Task,
                   Tasklist, TaskReminder, User)
from permission import owns, owns_program
from util import PermissionDenied
import api_helper
import cloudstorage as gcs
import jwt_helper
import mandrill
import notifier
import util

from rserve_handlers import authenticate_rserve, routes as rserve_routes


# Make sure this is off in production, it exposes exception messages.
debug = util.is_development()


class Register(ApiHandler):
    def post(self):
        # A user wants to create an account, so the first step is to confirm
        # they own the email address in question. We send them an invitation
        # with a link that will allow them to log in.

        # This handler is used from other PERTS systems as well so it needs
        # to handle generic and neptune-specific cases.
        params = self.get_params({
            # Generic
            'email': unicode,
            'role': str,
            'platform': str,
            'template_content': 'json',
            'domain': str,
            'program_label': str,
            'from_address': str,  # e.g. support@perts.net
            'from_name': str,  # e.g. "PERTS" or "Copilot"
            'reply_to': str,
            # Neptune-specific
            'cohort': str,
        })

        params = api_helper.apply_auth_defaults(params)

        # these will be available as params in emails
        template_content = params['template_content']
        # these will be added to the link shown in the email
        qs_params = {}

        # Customize links by program if one is given.
        program_label = params.get('program_label', None)
        if program_label:
            try:
                program = Program.get_config(program_label)
            except ImportError:
                return self.http_bad_request("Program does not exist.")

            # Customize email link for program.
            qs_params.update(program=program_label)
            if params.get('cohort', None):
                qs_params.update(cohort=params['cohort'])

            # Customize sender for program, if not already set.
            sender = program.get('contact_email_address', None)
            if sender:
                template_content['contact_email_address'] = sender
                params['from_address'] = params.get('from_address', sender)
                params['reply_to'] = params.get('reply_to', sender)

            # Customize branding for program.
            template_content.update(
                program_label=program_label,
                program_name=program['name'],
            )
        else:
            if params['platform'] == 'triton':
                logging.error("triton registrants should have a program")
                logging.info('{}'.format(params))
            template_content.update(program_name='PERTS')

        # Use our strongly-consistent Unique type to make sure we don't miss
        # an existing account.
        if User.email_exists(params['email']):
            user = User.get_by_auth('email', params['email'])
            if user.hashed_password:
                if params['platform'] == 'neptune' and not program_label:
                    # Special case where neptune registrants don't have a
                    # program selected (they usually do).
                    template_suffix = '-register-exists-no-program'
                else:
                    # Normal neptune registrants, or those for other platforms,
                    # don't need a special template.
                    template_suffix = '-register-exists'
            else:
                # This is the unusual case where a user has been invited and
                # sent a link to set their password, but they don't use it.
                # Instead, they attempt to register with the email address that
                # has already been set up for them. Send them a /set_password
                # link rather than unhelpfully telling them their account
                # already exists.
                template_suffix = '-register-pending'
        else:
            # Create a new user!
            # @todo: eventually we may want to support google type logins, but
            # definitely not for MVP. Right now assume all users authenticate
            # via their email (i.e. don't have a google id)
            user = User.create(
                email=params['email'],
                role=params.get('role', None),
            )
            user.put()
            template_suffix = '-register-new'

        # Determine what kind of link we want in the email.
        if template_suffix in ('-register-pending', '-register-new'):
            token = api_helper.platform_token(params['platform'], user)
            link = user.create_reset_link(
                params['domain'],
                token,
            )
            template_content['expiration_datetime'] = \
                api_helper.get_token_expiration_str()
        elif '-register-exists' in template_suffix:  # handles both "exists"
            link = util.set_query_parameters(
                params['domain'] + '/login',
                email=params['email'],
                program=program_label,  # possibly None
            )

        # If there are any google analytics campaign params then add them so
        # Neptune can continue to track.
        google_analytics_params = self.get_params({
            'utm_source': unicode,
            'utm_medium': unicode,
            'utm_campaign': unicode,
            'utm_term': unicode,
            'utm_content': unicode,
        })
        qs_params.update(**google_analytics_params)

        # Apply all the query string parameters set so far.
        link = util.set_query_parameters(link, **qs_params)
        template_content.update(link=link)

        optional_email_keys = ('from_address', 'from_name', 'reply_to')
        optional_email_kwargs = {k: params[k] for k in optional_email_keys
                                 if k in params}
        email = Email.create(
            to_address=params['email'],
            mandrill_template=params['platform'] + template_suffix,
            mandrill_template_content=template_content,
            **optional_email_kwargs
        )
        email.put()
        # We want to send this immediately, not in batches.
        email.deliver()

        self.http_no_content()


class Login(ApiHandler):
    # POSTs will contain plaintext passwords. Don't log them.
    should_log_request = False

    def get(self, email):
        # Allow super_admin users to imitate (login as) other users
        user = self.get_current_user()
        if not user.super_admin:
            logging.info('Login: {} failed to imitate {}'
                         .format(user.email, email))
            self.http_forbidden()
            return

        imitate_user = User.get_by_auth('email', email)
        if not imitate_user:
            logging.info('Login: {} failed to imitate {}'
                         .format(user.email, email))
            self.http_not_found()
            return

        logging.info('Login: {} is imitating {}'
                     .format(user.email, email))
        self.log_out()
        self.log_in(imitate_user)
        new_user = self.get_current_user()
        self.write(new_user)

    def post(self):
        # Make sure these useful accounts exist so devs don't have to register
        # themselves all the time.
        self.create_admin_account()
        self.create_demo_account()

        params = self.get_params({
            'auth_type': str, 'email': unicode, 'password': unicode})
        if len(params) != 3:
            return self.http_bad_request()

        response = self.authenticate(**params)
        if not isinstance(response, User):
            self.error(401)  # Unauthorized
        self.write(response)

    def create_demo_account(self):
        demo_exists = User.get_by_id('User_demo') is not None
        if demo_exists or not util.is_development() or util.is_testing():
            return

        # Create the demo user with a known passwod
        demo_user = User.create(id='demo', email='demo@perts.net',
                                user_type='org_admin', name="Debbie Demo")
        demo_user.hashed_password = User.hash_password('1231231231')

        demo_user.put()
        demo_user.key.get()

    def create_admin_account(self):
        admin_exists = User.get_by_id('User_admin') is not None
        if admin_exists or not util.is_development() or util.is_testing():
            return

        # Create the admin user with a known passwod
        admin_user = User.create(
            id='admin',
            email='admin@perts.net',
            user_type='super_admin',
            name="Aaron Admin",
        )
        admin_user.hashed_password = User.hash_password('1231231231')
        admin_user.put()
        admin_user.key.get()

        program_admin = User.create(
            id='prog-demo',
            email='prog-demo@perts.net',
            user_type='program_admin',
            name="Patrick Fiore",
            owned_programs=['demo-program'],
        )
        program_admin.hashed_password = User.hash_password('1231231231')
        program_admin.put()
        program_admin.key.get()


class ResetPassword(ApiHandler):
    """For requesting a link via email to reset a password."""
    def post(self):
        # @todo: probably want a limit on how often any given ip can hit this

        # This handler is used from other PERTS systems as well so it needs
        # to handle generic and neptune-specific cases.
        params = self.get_params({
            # Generic
            'email': unicode,
            'platform': str,
            'template_content': 'json',
            'domain': str,
        })

        params = api_helper.apply_auth_defaults(params)

        # Use our strongly-consistent Unique type to make sure we don't miss
        # an existing account.
        if User.email_exists(params['email']):
            user = User.get_by_auth('email', params['email'])
            template_suffix = '-reset-exists'
        else:
            template_suffix = '-reset-not-found'

        if template_suffix == '-reset-exists':
            token = api_helper.platform_token(params['platform'], user)
            link = user.create_reset_link(
                params['domain'],
                token,
                case='reset',
            )

            params['template_content']['expiration_datetime'] = \
                api_helper.get_token_expiration_str()
        elif template_suffix == '-reset-not-found':
            link = util.set_query_parameters(
                params['domain'] + '/register',
                email=params['email'],
            )
        params['template_content'].update(link=link)

        email = Email.create(
            to_address=params['email'],
            mandrill_template=params['platform'] + template_suffix,
            mandrill_template_content=params['template_content'],
        )
        email.put()
        # We want to send this immediately, not in batches.
        email.deliver()

        self.http_no_content()


class SetPassword(ApiHandler):
    """To actually change or set a user's password, given a valid token.

    Handles neptune-style AuthTokens and triton-based jwts.

    Note: by strict REST standards, the way to update a user's password is a
    PATCH (but more commonly a PUT) to the user resource. However, that assumes
    authentication is not a problem. This is a custom POST because it combines
    authentication and user modification in one call.

    When a signed-in user wants to change their password from their account
    page, we can do a more standard REST operation.
    """
    # POSTs will contain plaintext passwords. Don't log them.
    should_log_request = False

    def post(self):
        # Look up the user from the token.
        params = self.get_params({'auth_token': str, 'password': unicode,
                                  'name': unicode, 'phone_number': str})

        error = None

        if 'auth_token' in params:
            user, error = AuthToken.check_token_string(params['auth_token'])
        else:
            # Check if there's a JWT authenticating a user. Notably, consume
            # the token by caching it. Any future encounters with this token
            # will be invalid.
            user, error = self.get_jwt_user(
                jwt_kwargs={'validate_jti': True, 'cache_jti': True})

        if not user or error:
            self.error(401)  # Unauthorized
            # This is appropriate for JWT, which we're in the process of
            # changing to.
            # https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.2
            self.response.headers['WWW-Authenticate'] = 'Bearer'
            self.write(error or '')
            return

        # Hash and save the new password (util checks the password against our
        # regex).
        try:
            user.hashed_password = User.hash_password(params['password'])
        except BadPassword:
            self.error(400)  # Bad Request
            self.write('bad_password')
            return

        # New accounts are also asked to provide some profile info. Save it.
        if 'name' in params:
            user.name = params['name']
        if 'phone_number' in params:
            user.phone_number = params['phone_number']

        user.put()

        # Clear the token.
        AuthToken.clear_all_tokens_for_user(user.uid)

        self.write(user)


class AuthTokens(ApiHandler):
    def post(self):
        user = self.get_current_user()

        if not user:
            return self.http_unauthorized()

        t = AuthToken.create(user.uid, 1)  # 1 hour duration
        t.put()

        self.write(t)


class UserFromAuthToken(ApiHandler):
    """Allow client to validate auth token and see related user."""

    def get(self, token):
        user, error = AuthToken.check_token_string(token)

        if error == 'not found':
            # Maybe it's a jwt rather than an AuthToken.
            user, error = self.user_from_jwt(token)

        if not error:
            self.write(user)

        elif error == 'not found':
            self.error(404)  # Not Found
            self.write(error)

        elif error == 'expired' or error.startswith('used'):
            self.error(410)  # Gone
            self.write(error)

        else:
            raise Exception("Unexpected token error: {}".format(error))

    def user_from_jwt(self, token):
        # Check validity, including jti nonce uniqueness, as a way to
        # pre-check the validity of a future call to /api/set_password.
        payload, error = jwt_helper.decode(
            token, validate_jti=True, cache_jti=False)

        # Make sure the payload meets expectations.
        if payload:
            if 'user_id' not in payload or 'email' not in payload:
                raise Exception("Authorization JWT must include user_id and "
                                "email.")

            return (User.get_by_id(payload['user_id']), error)
        else:
            return (None, error)


class Invitations(ApiHandler):
    requires_auth = True

    def post(self, override_permissions=False):
        """To invite people to create accounts on Neptune.

        Also supports adding relationships to invitee, if the inviter has
        the right permission. Only works for orgs thus far.
        """
        user = self.get_current_user()

        # This handler is used from other PERTS systems as well so it needs
        # to handle generic and neptune-specific cases.
        params = self.get_params({
            # Generic
            'email': unicode,
            'platform': str,
            'template_content': 'json',
            'domain': str,
            'continue_url': str,
            'from_address': str,  # e.g. support@perts.net
            'from_name': str,  # e.g. "PERTS" or "Copilot"
            'reply_to': str,
            # Neptune-specific
            'organization_id': str,
        })

        params = api_helper.apply_auth_defaults(params)

        # If this invitation also creates relationships to an org, the user
        # needs to own that org (or be a super admin).
        org_id = params.get('organization_id', None)
        if org_id:
            if not owns(user, org_id):
                logging.error("{} tried to invite {} to an org they don't "
                              "own: {}".format(user, params['email'], org_id))
                self.error(403)
                return
            org = Organization.get_by_id(org_id)
            params['template_content'].update(organization_name=org.name)

        # If the recipient doesn't already exist, they'll need an invitation,
        # otherwise advise them to log in with a helpful redirect to their new
        # org/team.
        if User.email_exists(params['email']):
            recipient = User.get_by_auth('email', params['email'])
            if recipient.hashed_password:
                # Already have an account and password; they need to log in.
                template_suffix = '-invite-exists'
            else:
                # They've been invited before (their user object exists), but
                # they haven't set their password yet. A link to log in won't be
                # helpful. Send them a set_password link instead.
                template_suffix = '-invite-new'
        else:
            recipient = User.create(email=params['email'])
            recipient.put()
            template_suffix = '-invite-new'

        # Determine what kind of link we want in the email.
        if template_suffix == '-invite-new':
            token = api_helper.platform_token(params['platform'], recipient)
            link = recipient.create_reset_link(
                params['domain'],
                token,
                continue_url=params.get('continue_url', None),
                case='invitation',
            )
            params['template_content']['expiration_datetime'] = \
                api_helper.get_token_expiration_str()
        elif template_suffix == '-invite-exists':
            link = util.set_query_parameters(
                params['domain'] + '/login',
                continue_url=params.get('continue_url', None),
            )
        params['template_content'].update(link=link)

        optional_email_keys = ('from_address', 'from_name', 'reply_to')
        optional_email_kwargs = {k: params[k] for k in optional_email_keys
                                 if k in params}

        email = Email.create(
            to_address=params['email'],
            mandrill_template=params['platform'] + template_suffix,
            mandrill_template_content=params['template_content'],
            **optional_email_kwargs
        )
        email.put()
        # We want to send this immediately, not in batches.
        email.deliver()

        # Give them access if requested.
        if org_id and org_id not in recipient.owned_organizations:
            recipient.owned_organizations.append(org_id)
            recipient.put()

        # Output a limited amount of information about the invited user, just
        # enough to let the UI confirm to the inviter what's succeeded. Note
        # that hashed password is just a boolean in this case.
        self.write({k: v for k, v in recipient.to_client_dict().items()
                    if k in ('uid', 'email', 'hashed_password')})


class Accounts(ApiHandler):
    def get(self, email):
        """Does an account with this email address exist?

        Yes? Is the account verified? Return dictionary containing email and
        verified boolean.

        No? Return dictionary containing empty email property and False verified
        boolean.

        Used in Triton registration to figure out if a user should be newly
        created or copied from their account on Neptune.

        Also, used in Triton to figure out if a user has been verified.

        Open to the public. Responds with an object with email and verified
        properties.
        """
        verifiedUser = { 'email': email.lower(), 'verified': False }
        if User.email_exists(email):
            user = User.get_by_auth('email', email)
            if user.hashed_password:
                verifiedUser['verified'] = True
            self.write(verifiedUser)
        else:
            self.error(404)


def RelatedQuery(model, relationship_property):
    """Generates handlers for relationship-based queries."""

    class RelatedQueryHandler(RestHandler):
        """Dynamically generated handler for listing a resource by their
        relationship to another."""

        requires_auth = True

        def get(self, parent_type, rel_id):
            # You must be a super admin or own the related object.
            user = self.get_current_user()
            rel_id = self.get_long_uid(parent_type, rel_id)

            if not rel_id:
                self.error(404)

            if parent_type == 'programs':
                if not owns_program(user, rel_id):
                    self.error(403)
            elif not owns(user, rel_id):
                self.error(403)

            if self.response.has_error():
                return

            # Simulate a query string parameter so existing handler code
            # can run the query.
            self.request.GET[relationship_property] = rel_id
            # There is no id-based GET for these RelatedQuery endpoints,
            # e.g. we don't support /api/projects/X/users/Y.
            # Skip right to the inherited query() method.
            super(RelatedQueryHandler, self).query(
                  override_permissions=True)

        # Override other inherited methods we don't support here.
        # HTTP 405: Method not allowed

        def post(self):
            self.not_allowed()

        def put(self):
            self.not_allowed()

        def delete(self):
            self.not_allowed()

        def not_allowed(self):
            self.error(405)
            self.response.headers['Allow'] = 'GET, HEAD'

    RelatedQueryHandler.model = model
    RelatedQueryHandler.__name__ = '{}s by {}'.format(
        model.__name__, relationship_property)

    return RelatedQueryHandler


def UserRelationship(relationship_property):
    """Generates handlers for managing user relationships.

    e.g. /api/organizations/<rel_id>/users/<id>
    """

    class UserRelationshipHandler(RestHandler):
        """Dynamically generated handler for managing user relationships.

        Allows PUT for associating, and DELETE for disassociating."""

        requires_auth = True

        model = User

        def put(self, parent_type, rel_id, id):
            """Make the specified user an owner of the specified entity."""
            # The typical pattern is that the request user owns the related
            # entity and is requesting a change to the relationship of the
            # url user to that entity.
            req_user = self.get_current_user()  # user making the request
            url_user = User.get_by_id(id)  # user id'ed in the URL

            rel_id = self.get_long_uid(parent_type, rel_id)
            rel_list = getattr(url_user, relationship_property)

            if not rel_id:
                self.error(404)
            elif not owns(req_user, rel_id):
                # You must be a super admin or own the related object.
                self.error(403)
            else:
                # Make the requested association, avoiding duplication.
                if rel_id not in rel_list:
                    rel_list.append(rel_id)
                    url_user.put()
                self.write(url_user)

        def delete(self, parent_type, rel_id, id):
            """Revoke ownership of the entity from the specified user."""
            # Similar pattern as PUT, but you can remove ownership from
            # yourself.
            req_user = self.get_current_user()  # user making the request
            url_user = User.get_by_id(id)  # user id'ed in the URL

            rel_id = self.get_long_uid(parent_type, rel_id)
            rel_list = getattr(url_user, relationship_property)

            # You must be a super admin, own the related object, or be
            # modifying yourself.
            if (not owns(req_user, rel_id) and req_user != url_user):
                self.error(403)
            else:
                if rel_id in rel_list:
                    rel_list.remove(rel_id)
                    url_user.put()
                self.write(url_user)

        # Override other inherited methods we don't support here.
        # HTTP 405: Method not allowed

        def get(self):
            self.error(405)

        def post(self):
            self.error(405)

    UserRelationshipHandler.__name__ = 'User relationships via {}'.format(
        relationship_property)

    return UserRelationshipHandler


class AccountManagers(RestHandler):
    model = AccountManager


class Liaisonships(RestHandler):
    model = Liaisonship


class Notifications(RestHandler):
    """Handles both the main task endpoint, /api/notifications, as well as
    hierarchical query endpoints, e.g. /api/projects/X/notifications.

    Hierarchical endpoints define a user id, which is added to the request
    parameters as an ancestor.
    """
    requires_auth = True

    model = Notification

    def query(self, override_permissions=None):
        user = self.get_current_user()
        parent_id = self.request.get('ancestor', None)

        order = self.get_param('order', str, None)
        if order is None:
            self.request.GET['order'] = '-created'

        if parent_id and owns(user, parent_id):
            # Since parent_id is set, this is a hierarchical endpoint, e.g.
            # /api/users/X/notifications. You must own the parent or be a super
            # admin.
            super(Notifications, self).query(override_permissions=True)
        else:
            # The parent id is not set, so this is the main endpoint,
            # /api/notifications. We can use the default REST handler rules.
            super(Notifications, self).query(override_permissions=False)

    def get(self, id=None, parent_id=None):
        if parent_id:
            user = self.get_current_user()
            if owns(user, parent_id):
                self.request.GET['ancestor'] = parent_id
                super(Notifications, self).get(
                    id=id, override_permissions=True)
            else:
                self.error(403)
        else:
            # Don't override usual permissions if no parent.
            super(Notifications, self).get(id=id)


class Organizations(RestHandler):
    requires_auth = True

    model = Organization

    def get(self, id=None):
        if id:
            # Add a loophole: associated users are allowed to get the org
            # object by id.
            o = id in self.get_current_user().assc_organizations
            return super(Organizations, self).get(id, override_permissions=o)
        else:
            return super(Organizations, self).query()

    def post(self):
        # Allow any user to create the organization.
        org = super(Organizations, self).post(override_permissions=True)

        # Pass in the requesting user explicitly, because a general query of
        # org owners will be inconsistent at this point.
        org.tasklist.open(self.get_current_user())
        notifier.created_organization(self.get_current_user(), org)

    def put(self, id):
        org = self.model.get_by_id(id)  # unmodified verison of org
        user = self.get_current_user()

        if not user.super_admin:
            safe_props = ['liaison_id']
            params = self.get_params(self.model.property_types())
            safe_params = {k: v for k, v in params.items() if k in safe_props}
            self.override_json_body(safe_params)

        super(Organizations, self).put(id)

        # Did the contact change? Reassign taskslists to them.
        params = self.get_params({'liaison_id': str}, required=True)
        new_liaison_id = params['liaison_id']
        if new_liaison_id and new_liaison_id != org.liaison_id:
            TaskReminder.transfer_reminder(org, User.get_by_id(new_liaison_id))


class OrganizationProperty(ApiHandler):
    """Some properties of organizations should be public."""
    def query(self, prop):
        """Returns a list, eventually consistent."""
        self.write(Organization.get_all_of_property(prop))

    def get(self, prop, id=None):
        if prop.endswith('s'):
            prop = prop[:-1]  # make non-plural

        if prop not in Organization.public_properties:
            logging.error("Can only get whitelisted properties.")
            self.error(404)
        elif id:
            org = Organization.get_by_id(id)
            if org:
                self.write({'uid': org.uid, prop: getattr(org, prop)})
            else:
                self.error(404)
        else:
            self.query(prop)


class Programs(ApiHandler):
    def query(self):
        """Provide an abbreviated config dictionary for every program."""
        keys = ['label', 'name', 'description', 'listed', 'cohorts']
        listings = [{k: c[k] for k in keys} for c in Program.get_all_configs()]
        self.write(listings)

    def get(self, label=None):
        # Allow any user to view a given program.
        if label:
            try:
                self.write(Program.get_config(label))
            except ImportError:
                return self.http_not_found()
        else:
            self.query()


class Projects(RestHandler):
    requires_auth = True

    model = Project
    requires_auth = True

    def post(self):
        user = self.get_current_user()
        params = self.get_params(self.model.property_types())

        # Since we support multiple projects (run by independent teams) at an
        # organization, there are no restrictions on creating one. Invalid or
        # unacceptable projects will be rejected after manual review.

        project = super(Projects, self).post(override_permissions=True)
        project.tasklist.open(user)
        notifier.created_project(user, project)

    def put(self, id):
        project = self.model.get_by_id(id)  # unmodified version of project

        user = self.get_current_user()
        if owns_program(user, project.program_label):
            super(Projects, self).put(id, override_permissions=True)

            # Did the liaison change? Reassign taskslists to them.
            params = self.get_params({'liaison_id': str}, required=True)
            new_liaison_id = params['liaison_id']
            if new_liaison_id and new_liaison_id != project.liaison_id:
                self.transfer_liaisons(project, new_liaison_id)
        else:
            self.error(403)

    def delete(self, id):
        project = self.model.get_by_id(id)
        user = self.get_current_user()
        if owns_program(user, project.program_label):
            super(Projects, self).delete(id, override_permissions=True)
        else:
            self.error(403)

    def transfer_liaisons(project, new_liaison_id):
        """Go through all the entities a liaison is expected to manage within
        a project and transfer the task reminder from the old liaison to the
        new one."""
        user = User.get_by_id(new_liaison_id)

        reminders = [TaskReminder.transfer_reminder(project, user)]

        pcs = ProjectCohort.get(project_id=project.uid, n=float('inf'))
        reminders += [TaskReminder.transfer_reminder(pc, user) for pc in pcs]

        ss = Survey.get(project_id=project.uid, n=float('inf'))
        reminders += [TaskReminder.transfer_reminder(s, user) for s in ss]

        ndb.put_multi(reminders)


class ProjectCohorts(RestHandler):
    requires_auth = True

    model = ProjectCohort

    # No special rules for GETting PCs. Unauthenticated participants can query
    # PCs via participation code through /api/codes/<code>.

    def post(self):
        """All the predictable work of joining a cohort happens here.

        ProjectCohort, contained Surveys, contained tasklists with Checkpoints
        and Tasks.
        """
        # Any owners of the project can create project cohorts.
        user = self.get_current_user()
        params = self.get_params(self.model.property_types())
        program = Program.get_config(params['program_label'])

        # Validate the cohort. Can't join after they're closed.
        date_str = program['cohorts'][params['cohort_label']]['close_date']
        close_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if datetime.date.today() > close_date:
            msg = ("Can't join {}, close date has passed ({})."
                   .format(params['cohort_label'], close_date))
            logging.error(msg)
            return self.http_bad_request(msg)

        # Validate the uniqueness of the project cohort. Only one allowed per
        # org-program-cohort combination.
        existing = ProjectCohort.get(
            organization_id=params['organization_id'],
            program_label=params['program_label'],
            cohort_label=params['cohort_label'],
        )
        if len(existing) > 0:
            if len(existing) > 1:
                logging.error("Duplicate project cohorts: {}".format(existing))
            return self.http_bad_request("Project cohort already exists.")

        # Checks complete, delegate creation to super.
        pc = super(ProjectCohorts, self).post(
            override_permissions=owns(user, params['project_id']))

        if pc is None:
            # may be None if operation is forbidden
            return

        # Not forbidden, so save our work and notify.

        surveys = Survey.create_for_project_cohort(program['surveys'], pc)
        pc.survey_ids = [s.uid for s in surveys]
        ndb.put_multi(surveys + [pc])
        notifier.joined_cohort(user, pc)

        # Tasks are children of surveys, so they have to be put after
        # surveys are put.
        for s in surveys:
            s.tasklist.open(user)

    ## @todo(chris): may want to enforce that org admins may only change the
    ## liaison_id and the expected_participants, not other props.
    # def patch(self, id):
    #     pass


class Surveys(RestHandler):
    model = Survey

    def get(self, id=None):
        override = False
        expected = {'project_cohort_id': str, 'ordinal': int}
        params = self.get_params(expected)
        all_params = all([params.get(k, None) for k in expected.keys()])

        if id is None and all_params:
            # This special version of a survey query is open to call comers so
            # participants can query surveys from the portal.
            override = True

        return super(Surveys, self).get(id, override_permissions=override)

    def post(self):
        # Surveys are only created server-side when the project cohort is
        # created.
        self.error(405)

    def delete(self, id):
        # Surveys are only deleted server-side when the project cohort is
        # deleted.
        self.error(405)


class TaskReminders(RestHandler):
    requires_auth = True

    model = TaskReminder

    def get(self, user_id=None, id=None):
        req_user = self.get_current_user()
        if user_id:
            # This is a query for a user's task reminders. Allowed if you
            # are requesting this for yourself.
            if owns(req_user, user_id):
                self.write(TaskReminder.get(ancestor=DatastoreModel.id_to_key(user_id)))
            else:
                self.error(403)
        else:
            # Standard REST behavior.
            super(TaskReminders, self).get(id)


class Tasks(RestHandler):
    """Handles both the main task endpoint, /api/tasks, as well as
    hierarchical query endpoints, e.g. /api/projects/X/tasks.

    Hierarchical endpoints define a parent id, which is added to the request
    parameters.
    """
    requires_auth = True

    model = Task

    def query(self, override_permissions=None):
        # @todo: how this works for hierarchical or not needs cleanup.
        user = self.get_current_user()
        parent_id = self.request.get('ancestor', None)

        if parent_id and owns(user, parent_id):
            # Since parent_id is set, this is a hierarchical endpoint, e.g.
            # /api/projects/X/tasks. You must own the parent or be a super
            # admin.
            self.request.GET['order'] = 'ordinal'
            super(Tasks, self).query(override_permissions=True)
        else:
            # The parent id is not set, so this is the main endpoint,
            # /api/tasks. We want one exception to the default REST handler
            # rules: if you own a checkpoint's parent, you can query by that
            # checkpoint.
            override = False
            params = self.get_params({'checkpoint_id': str})
            if 'checkpoint_id' in params:
                checkpoint = Checkpoint.get_by_id(params['checkpoint_id'])
                override = owns(user, checkpoint.parent_id)
            super(Tasks, self).query(override_permissions=override)

    def get(self, id=None, parent_type=None, parent_id=None):
        if parent_id:
            parent_id = self.get_long_uid(parent_type, parent_id)
            user = self.get_current_user()

            if not parent_id:
                self.error(404)
            elif owns(user, parent_id):
                self.request.GET['ancestor'] = parent_id
                super(Tasks, self).get(id=id, override_permissions=True)
            else:
                self.error(403)
        else:
            # Don't override usual permissions if no parent.
            super(Tasks, self).get(id=id)

    def put(self, id):
        # Tasks have an extra permission check: org admins aren't allowed to
        # modify some tasks.
        task = self.model.get_by_id(id)
        t_dict = task.to_client_dict()
        user = self.get_current_user()

        if user.non_admin and not t_dict['non_admin_may_edit']:
            self.error(403)
            return

        super(Tasks, self).put(id)

        # Bubble task status changes up to checkpoints.
        checkpoint = Checkpoint.get_by_id(task.checkpoint_id)
        checkpoint.status = Checkpoint.get_status_from_tasks(checkpoint)
        checkpoint.put()

        # Notify various parties.

        parent = task.key.parent().get()
        parent_kind = DatastoreModel.get_kind(parent)
        project = None  # used to update project.last_active
        if parent_kind == 'Organization':
            notify_fn = notifier.changed_organization_task
        elif parent_kind == 'Project':
            notify_fn = notifier.changed_project_task
            project = parent
        elif parent_kind == 'Survey':
            notify_fn = notifier.changed_survey_task
            project = Project.get_by_id(parent.project_id)
        else:
            logging.error('Notification rules for {} tasks not written'
                          .format(parent_kind))
            return

        # The client adds a project cohort id to all Task updates, even though
        # they're not part of the datastore model, because we need them in
        # notifications to construct useful links for recipients.
        params = self.get_params({'project_cohort_id': str})
        project_cohort_id = params.get('project_cohort_id', None)
        notify_fn(user, parent, task, project_cohort_id)

        # Update last active.
        if project and user.non_admin:
            project.last_active = datetime.datetime.now()
            project.put()


class TasksAttachment(ApiHandler):
    """Task file attachment reading and writing to Google Cloud Storage."""
    requires_auth = False  # Custom implentation; accepts rsa-based jwts also

    def post(self, id):
        """Sets attachment for task type "file", either in-app links or actual
        files which are saved in gcs."""

        # Allow RServe to call this endpoint, then fall back on regular auth.
        user, error = authenticate_rserve(self)
        if not user:
            user = self.get_current_user()
            error = ''

        # Replaces function of `requires_auth = True`.
        if user.user_type == 'public':
            return self.http_unauthorized()

        if not user.super_admin and not owns(user, id):
            return self.http_forbidden(error)

        is_form = 'multipart/form-data' in self.request.headers['Content-Type']
        is_json = 'application/json' in self.request.headers['Content-Type']

        if is_form:
            attachment = self.save_file(self.request.POST['file'], id)
        elif is_json:
            params = self.get_params({'filename': unicode, 'link': unicode})
            attachment = {
                'filename': params['filename'],
                # The link/url should already be escaped if it contains special
                # characters, but do it again just in case.
                'link': util.encode_uri_non_ascii(params['link']),
            }

        task = Task.get_by_id(id)
        task.attachment = json.dumps(attachment)

        # In the case of RServe setting the attachment, we also want to mark
        # the task complete.
        if user.email == 'rserve@perts.net':
            task.status = 'complete'

        task.put()

        # Add task UID to ProjectCohort's completed_report_task_ids property
        if task.get_task_config().get('counts_as_program_complete', False):
            parent_key = task.key.parent()
            if DatastoreModel.get_kind(parent_key) == 'Survey':
                survey = parent_key.get()
                pc = ProjectCohort.get_by_id(survey.project_cohort_id)
                if (pc and task.uid not in pc.completed_report_task_ids):
                    pc.completed_report_task_ids.append(task.uid)
                    pc.put()

        self.write(attachment)

    def save_file(self, field_storage, task_id):
        """Saves to GCS by their md5 hash, so uploading the same file many
        times has no effect (other than io). Uploading a different file changes
        the reference on the task, but doesn't delete previous uploads. A
        history of uploads for a given task can be found by searching the
        upload bucket for files with the header
        'x-goog-meta-task-id:[task uid]'

        Filenames as uploaded are preserved:

        * in the content-disposition header of the GCS file
        * in the task attachment, which is JSON of the form:
          {"gcs_path": "...", "filename": "...", "content_type": "..."}

        To avoid file names getting out of sync, only the one in the task
        attachment is actually used.
        """

        # FieldStorageClass object has potentially useful properties:
        # file: cStringIO.StringO object
        # headers: rfc822.Message instance
        # type: str, MIME type, e.g. 'application/pdf'
        # filename: str, file name as uploaded

        file_contents = field_storage.file.read()
        file_hash = hashlib.md5(file_contents).hexdigest()

        attachment = {
            'gcs_path': '/{}{}/{}'.format(
                util.get_upload_bucket(), os.environ['GCS_UPLOAD_PREFIX'],
                file_hash),
            'filename': field_storage.filename,
            # Avoid unicode input here, since possible values are limited.
            'content_type': str(field_storage.type),
        }

        open_kwargs = {
            'content_type': attachment['content_type'],
            # These will be headers on the stored file.
            'options': {
                # Not actually used, but seems smart to keep track of.
                'Content-Disposition': 'attachment; filename={}'.format(
                    attachment['filename']),
                # Theoretically allows figuring out an attachment history for
                # a given task.
                'x-goog-meta-task-id': task_id,
            },
            'retry_params': gcs.RetryParams(backoff_factor=1.1),
        }

        with gcs.open(attachment['gcs_path'], 'w', **open_kwargs) as gcs_file:
            gcs_file.write(file_contents)

        return attachment

    def get(self, id):
        """Download the file attached to this task.

        If this isn't an upload type task, just get the value of the attachment
        property.
        """
        user = self.get_current_user()

        # Replaces function of `requires_auth = True`.
        if user.user_type == 'public':
            return self.http_unauthorized()

        if not user.super_admin and not owns(user, id):
            self.error(403)
            return

        task = Task.get_by_id(id)

        if task.to_client_dict()['data_type'] == 'file' and task.attachment:
            attachment = json.loads(task.attachment)
            headers = {
                'Content-Disposition': 'inline; filename={}'.format(
                    attachment['filename']),
                'Content-Type': str(attachment['content_type']),
            }
            self.response.headers.update(headers)
            with gcs.open(attachment['gcs_path'], 'r') as gcs_file:
                self.response.write(gcs_file.read())
        else:
            # Respond with whatever data we've got.
            self.write(task.attachment)


class Checkpoints(ApiHandler):
    """Handles both the main task endpoint, /api/checkpoints, as well as
    hierarchical query endpoints, e.g. /api/projects/X/checkpoints.

    Hierarchical endpoints define a parent id, which is added to the request
    parameters.

    The non-hierarchical version has an extra optional param:
        include_conf: bool, default True, whether to mix in properties from the
            matching org or program config. Setting to false simplifies queries
            when not rendering the tasklist view b/c you don't need the body
            html.

    Checkpoints are a little different in that they have to explicitly
    converted to a client dict, rather than auto-converted in
    ApiHandlers.write().

    There's one special endpoint where the query string params aren't
    simply passed to SQL, because the query requires a JOIN:
    /api/checkpoints?parent_kind=Organization&program_label=foo
    Which invokes Checkpoint.for_organizations_from_program()
    """
    requires_auth = True

    def get(self, id=None, parent_type=None, parent_id=None):
        user = self.get_current_user()
        if parent_id:
            parent_id = self.get_long_uid(parent_type, parent_id)

            if not parent_id:
                self.error(404)
            elif owns(user, parent_id):
                cps = Checkpoint.get(parent_id=parent_id, order='ordinal')
                self.write(cps)
            else:
                self.error(403)  # you don't own the parent; forbidden
        elif id:
            checkpoint = Checkpoint.get_by_id(id)
            if not checkpoint:
                self.error(404)  # no such id; not found
            elif not owns(user, checkpoint.parent_id):
                self.error(403)  # you don't own the parent; forbidden
            else:
                self.write(checkpoint)
        else:
            self.query()

    def query(self):
        # This is a query for all checkpoints matching some filter.
        params = self.get_params({
            'organization_id': str,
            'program_label': str,
            'project_id': str,
            'cohort_label': str,
            'survey_id': str,
            'label': str,
            'parent_kind': str,
            'n': int,
            'offset': int,
            'include_conf': bool,
        })

        # All params but these are for WHERE clauses.
        include_conf = params.pop('include_conf', True)
        n = params.pop('n', 1000)
        offset = params.pop('offset', None)

        user = self.get_current_user()
        if user.super_admin:
            # Include access to a special checkpoint query.
            if (params.get('parent_kind', None) == 'Organization' and
                params.get('program_label', None)):
                cps = Checkpoint.for_organizations_in_program(
                    params['program_label'], n)
                self.write([cp.to_client_dict(include_conf) for cp in cps])
                return
            # Else they can do what they like; fall through to the write() at
            # the bottom.
        else:
            # Make sure the user owns the filtering id. Consider only id- or
            # label-based filters.
            filters = {k: v for k, v in params.items()
                       if k.endswith('id') or k.endswith('label')}

            # It's too hard to calculate overlapping permissions. Limit to
            # one type of permission-restricted filter.
            if len(filters.keys()) != 1:
                logging.error("Must use exactly 1 id or label filter.")
                self.error(403)
                return

            filter_id = filters.values()[0]
            if not owns(user, filter_id):
                self.error(403)
                return

        cps = Checkpoint.get(n=n, offset=offset, **params)
        self.write([cp.to_client_dict(include_conf) for cp in cps])

    def put(self, id):
        user = self.get_current_user()

        if not user:
            self.error(403)
            return

        ckpt = Checkpoint.get_by_id(id)
        if owns(user, ckpt.parent_id):
            params = self.get_params(Checkpoint.property_types())

            # Make sure status is legit (some users aren't allowed to change
            # tasks, so don't let them change checkpoint status either).
            if ('status' in params
                and params['status'] != Checkpoint.get_status_from_tasks(ckpt)):
                raise Exception("Checkpoint PUT: status doesn't match tasks.")

            for k, v in params.items():
                setattr(ckpt, k, v)
            ckpt.put()

            # Is the whole tasklist finished? If so, close it.
            parent = DatastoreModel.get_by_id(ckpt.parent_id)
            tasklist = Tasklist(parent)
            if tasklist.status() == 'complete':
                notifier.completed_task_list(user, parent)
                tasklist.close()
            else:
                tasklist.open()

            # Write the modified dict as our respose.
            self.write(ckpt)
        else:
            self.error(403)


class Users(RestHandler):
    requires_auth = True

    model = User

    def put(self, id):
        # Allowing user updates is generally a security risk. We don't want to
        # allow:
        # * Users to change their user type and escalate their privileges.
        # * Users to change their relationships and gain access to data they
        #   shouldn't see.
        # Therefore whitelist properties that are safe.
        safe_props = ('name', 'notification_option')

        id = self.model.get_long_uid(id)
        req_user = self.get_current_user()
        if owns(req_user, id):
            params = self.get_params(self.model.property_types())
            # Here's where we enforce only changing certain properties.
            safe_params = {k: v for k, v in params.items() if k in safe_props}
            entity = self.model.get_by_id(id)
            for k, v in safe_params.items():
                setattr(entity, k, v)
            entity.put()
            self.write(entity)
            return entity
        else:
            self.error(403)


class ProjectAccountManager(ApiHandler):
    requires_auth = True

    def get(self, project_id):
        """Org admins can get their account manager. Program owners can get
        any account manager on their program."""
        allowed = False
        user = self.get_current_user()
        project = Project.get_by_id(project_id)

        if user.super_admin:
            allowed = True
        elif user.user_type == 'program_admin':
            if project.program_label in user.owned_programs:
                allowed = True
        elif user.non_admin:
            if project.organization_id in user.owned_organizations:
                allowed = True

        if allowed:
            self.write(User.get_by_id(project.account_manager_id))
        else:
            self.error(403)


class Liaison(ApiHandler):
    requires_auth = True

    def get(self, id):
        """Anyone associated to the parent can get the liaison."""
        user = self.get_current_user()

        if id in user.assc_organizations or owns(user, id):
            parent = DatastoreModel.get_by_id(id)
            self.write(User.get_by_id(parent.liaison_id))
        else:
            self.error(403)


class UsersOrganizations(ApiHandler):
    """Organizations related to the specified user.

    Doesn't use the generic RelatedQuery handler for GET because, unlike every
    other case, there's no relationship information on the target type:
    organizations.

    The POST case is unusual also because its used to create the special
    association for organization applicants (rather than the typical ownership
    relationship).
    """
    requires_auth = True

    def get(self, user_id, relationship, org_id=None):
        if org_id:
            self.error(405)  # Method not allowed
            return

        req_user = self.get_current_user()  # user making the request
        url_user = User.get_by_id(user_id)  # user id'ed in the URL

        # You must be a super admin or the user mentioned in the URL.
        if req_user.super_admin or req_user == url_user:
            self.write(url_user.get_organizations())
        else:
            self.error(403)

    def post(self, user_id, relationship, org_id=None):
        if org_id:
            self.error(405)  # Method not allowed
            return

        org_id = self.get_params({'uid': unicode})['uid']

        if relationship == 'organizations':
            self.add_ownership(user_id, org_id)
        elif relationship == 'associated_organizations':
            self.add_association(user_id, org_id)

    def delete(self, user_id, relationship, org_id=None):
        if not org_id:
            self.error(405)  # Method not allowed
            return

        if relationship == 'organizations':
            self.remove_ownership(user_id, org_id)
        elif relationship == 'associated_organizations':
            self.remove_association(user_id, org_id)

    def add_association(self, user_id, org_id):
        """Anyone can request this for themselves."""
        req_user = self.get_current_user()  # user making the request
        if owns(req_user, user_id):
            url_user = User.get_by_id(user_id)  # user id'ed in the URL
            if org_id not in url_user.assc_organizations:
                url_user.assc_organizations.append(org_id)
                url_user.put()
                # Send notification to organization owner
                notifier.requested_to_join_organization(
                    url_user, Organization.get_by_id(org_id))
            # else do nothing; joiners shouldn't be able to spam owners.
            self.write(url_user)
        else:
            self.error(403)

    def add_ownership(self, user_id, org_id):
        """You must be a super admin or own the org."""
        req_user = self.get_current_user()  # user making the request

        if owns(req_user, org_id):

            url_user = User.get_by_id(user_id)  # user id'ed in the URL
            org = Organization.get_by_id(org_id)

            # Adjust relationships.
            if org_id not in url_user.owned_organizations:
                url_user.owned_organizations.append(org_id)
            if org_id in url_user.assc_organizations:
                url_user.assc_organizations.remove(org_id)
            url_user.put()

            # Send notification to organization owner
            notifier.joined_organization(req_user, url_user, org)

            # Generate task reminders for all their new responsibilities.
            projects = Project.get(organization_id=org_id, n=float('inf'))
            surveys = Survey.get(organization_id=org_id, n=float('inf'))
            parents = itertools.chain([org], projects, surveys)
            trs = []
            for tasklist_parent in parents:
                tr = TaskReminder.create(tasklist_parent, url_user)
                trs.append(tr)
            ndb.put_multi(trs)

            self.write(url_user)

        else:
            self.error(403)

    def remove_association(self, user_id, org_id):
        """Only org owners."""
        req_user = self.get_current_user()  # user making the request

        if owns(req_user, org_id):
            url_user = User.get_by_id(user_id)  # user id'ed in the URL
            if org_id in url_user.assc_organizations:
                url_user.assc_organizations.remove(org_id)
                url_user.put()
            # Send notification to the subject of the removal.
            notifier.rejected_from_organization(
                req_user, url_user, Organization.get_by_id(org_id))
            self.write(url_user)
        else:
            self.error(403)

    def remove_ownership(self, user_id, org_id):
        raise Exception("Not yet implemented.")


class SecretValues(ApiHandler):
    """For securely storing secret values."""
    # POSTs will contain secret values. Don't log them.
    should_log_request = False

    def get(self, id):
        if not app_engine_users.is_current_user_admin():
            raise PermissionDenied()
        exists = SecretValue.get_by_id(id) is not None
        self.write({'key exists': exists,
                    'message': "SecretValues can't be read via api urls."})

    def post(self, id):
        if not app_engine_users.is_current_user_admin():
            raise PermissionDenied()
        value = self.get_params({'value': unicode}).get('value', None)
        if value is None:
            raise Exception("Must POST with a value.")
        sv = SecretValue.get_or_insert(id)
        sv.value = value
        sv.put()
        self.write(id)

    def delete(self, id):
        if not app_engine_users.is_current_user_admin():
            raise PermissionDenied()
        sv = SecretValue.get_by_id(id)
        if sv is not None:
            sv.key.delete()
        self.write(id)


class Everything(ApiHandler):
    def delete(self):
        """Clear the datastore, DROP and re-CREATE all SQL tables."""
        admin_in_dev = (app_engine_users.is_current_user_admin() and
                        util.is_development())
        if not admin_in_dev:
            self.error(403)
            return

        # These imports are only required by this handler, not any of the
        # others. Don't spend computation importing them for general
        # operation.
        from webapp2_extras.appengine.auth.models import Unique
        import model
        import mysql_connection

        # Get all the datastore entity kinds we define. This ignores any
        # entities that might be around via map reduce or app engine internals.
        ds_models = model.get_datastore_models()
        # Include the webapp2-provided Unique entities, which aren't in model.
        ds_models.append(Unique)
        # Delete all entities for each model.
        keys = [k for m in ds_models for k in m.query().iter(keys_only=True)]
        ndb.delete_multi(keys)

        # Get all our sql table definitions.
        sql_models = model.get_sql_models()
        # Pass them all to reset, which will call DROP TABLE and CREATE TABLE
        # for each.
        with mysql_connection.connect() as sql:
            sql.reset({m.table: m.get_table_definition() for m in sql_models})


class Seed(ApiHandler):
    def post(self, program='demo-program', cohort='all', n=10):
        """Seed database with fake orgs, users, etc. for local development.

        Args:
            program - str, default 'demo-program', in which program to seed
            cohort - str, default '2018', in which cohort to seed. Use 'all' to
                have data distributed among all available cohorts.
            n - int, default 10, how many project cohorts to create
        """
        admin_in_dev = (app_engine_users.is_current_user_admin() and
                        util.is_development())

        if not admin_in_dev:
            self.error(403)
            return

        program = Program.get_config(program)

        def random_string(char_set, length=5):
            return ''.join(random.choice(char_set) for _ in range(length))

        for n in range(int(n)):
            logging.info('[{}] Seeding Organization.'.format(n))

            name = random_string(string.ascii_lowercase)

            # Create an organization and org liaison
            organization = Organization.create(
                name='{} College'.format(name.capitalize()),
                mailing_address='555 {} Street\nSan Francisco, CA 94105'
                                .format(name.capitalize()),
                phone_number='+1 (555) 555-5555',
                state='CA',
                website_url='www.{}.edu'.format(name),
                nces_district_id=random_string(string.digits),
                nces_school_id=random_string(string.digits),
                ipeds_id=random_string(string.digits),
                ope_id=random_string(string.digits),
            )

            user = self.create_seed_user(name, organization.uid)

            organization.liaison_id = user.uid
            organization.put()

            # Create project
            project = Project.create(
                organization_id=organization.uid,
                program_label=program['label']
            )

            project.put()
            project.tasklist.open()

            # Create project cohorts
            if cohort == 'all':
                self.create_seed_project_cohorts(
                    organization, program, project, cohort)
            else:
                self.create_seed_project_cohort(
                    organization, program, project, cohort)

        self.write('Success')

    def create_seed_project_cohorts(self, organization, program, project,
                                    cohort='all'):
        # The organization will join from 1 to all of the available cohorts in
        # the provided program.
        joined_cohorts = []
        random_cohort_label = random.choice(program['cohorts'].keys())

        while random_cohort_label not in joined_cohorts:
            joined_cohorts.append(random_cohort_label)

            self.create_seed_project_cohort(
                organization,
                program,
                project,
                random_cohort_label
            )

            random_cohort_label = random.choice(program['cohorts'].keys())

        logging.info('COHORTS {}'.format(joined_cohorts))

    def create_seed_project_cohort(self, organization, program,
                                   project, random_cohort_label):
        # Create Project Cohort
        project_cohort = ProjectCohort.create(
            organization_id=organization.uid,
            program_label=program['label'],
            project_id=project.uid,
            cohort_label=random_cohort_label
        )


        # Create Surveys
        surveys = []

        for i, survey_definition in enumerate(program['surveys']):
            survey = Survey.create(
                survey_definition['survey_tasklist_template'],
                project_id=project.uid,
                organization_id=organization.uid,
                program_label=program['label'],
                cohort_label=random_cohort_label,
                project_cohort_id=project_cohort.uid,
                ordinal=i + 1,
            )

            surveys.append(survey)

        project_cohort.survey_ids = [s.uid for s in surveys]
        project_cohort.put()
        ndb.put_multi(surveys)

        # Tasks are children of surveys, so they have to be put after
        # surveys are put.
        for s in surveys:
            s.tasklist.open()

    def create_seed_user(self, name, organization_id):
        user_name = '{} {}'.format(name.capitalize(), name.capitalize()[:3])
        user_email = '{}@{}.edu'.format(name.capitalize(), name.capitalize())
        owned_organizations = [organization_id]

        user = User.create(
            name=user_name,
            email=user_email,
            owned_organizations=owned_organizations
        )

        user.hashed_password = User.hash_password('1231231231')

        user.put()

        return user


class Participation(ApiHandler):
    requires_auth = True

    def get(self, parent_type, id=None, cohort_label=None):
        """Get counts of participants at each distinct value of progress."""
        user = self.get_current_user()

        type_to_field = {
            'surveys': 'survey_id',
            'project_cohorts': 'project_cohort_id',
            'programs': 'program_label',
        }
        if parent_type not in type_to_field.keys():
            return self.http_bad_request("Invalid parent for participation.")
        parent_field = type_to_field[parent_type]

        if id:
            id = self.get_long_uid(parent_type, id)
            result = self.get_for_single_parent(
                parent_type, parent_field, id, cohort_label, user)
        else:
            ids = self.get_params({'uid': list}).get('uid', [])

            if not ids:
                return self.http_bad_request("Need uid(s) in query string.")

            if parent_type == 'project_cohorts' and not cohort_label:
                # This is a common request from triton/Copilot; use a more
                # efficient bulk query.
                result = self.get_for_project_cohorts(ids, user)
            else:
                result = {
                    uid: self.get_for_single_parent(
                        parent_type, parent_field, id, cohort_label, user)
                    for id in ids
                }

        if not self.response.has_error():
            # Don't write if some called function has set an error code.
            self.write(result)

    def parent_allowed(self, parent_type, parent_id, user):
        # Apply permissions. Triton may endorse a user to call this.
        try:
            allowed = owns(user, parent_id)
        except NotImplementedError:
            allowed = False  # it's likely a code
        if not allowed:
            jwt_user, jwt_error = self.get_jwt_user()
            jwt_user_ok = jwt_user and not jwt_error
            endpoint = self.get_endpoint_str(
                # Change the path; we use /api/project_cohorts/participation
                # for batch stuff, while the jwt permissions are always in
                # terms of /api/project_cohorts/<id>
                path='/api/{}/{}/participation'.format(parent_type, parent_id))
            endpoint_ok = self.jwt_allows_endpoint(endpoint_str=endpoint)
            allowed = jwt_user_ok and endpoint_ok

        return allowed

    def get_for_single_parent(self, parent_type, parent_field, id_or_code,
                              cohort_label, user):
        parent_id = self.get_parent_id(parent_type, id_or_code)
        if not parent_id:
            return self.http_not_found()
        if not self.parent_allowed(parent_type, id_or_code, user):
            return self.http_forbidden()
        kwargs = dict(
            # Program label, or pc id, or survey id
            {parent_field: parent_id},
            cohort_label=cohort_label,
            **self.get_params({'start': 'datetime', 'end': 'datetime'})
        )

        return ParticipantData.participation(**kwargs)

    def get_for_project_cohorts(self, ids_or_codes, user):
        # # !-- Testing use only --!
        # # Use this to fake participation while testing Copilot.
        # return {
        #     code.replace(' ', '-'): [{
        #         'project_cohort_id': 'ProjectCohort_foo',
        #         'code': code,
        #         'survey_ordinal': 1,
        #         'value': '100',
        #         'n': 5,
        #     }]
        #     for code in ids_or_codes
        # }
        # !-- Testing use only --!

        # These should either be all uids (possibly short) or codes. Let's
        # not create brittle code by relying on any regexes or conventions.
        # Instead try to load them as-is, which will work if they're uids.
        # Then attempt to use them as codes. See self.get_parent_id.
        using_codes = False
        pc_ids = [ProjectCohort.get_long_uid(id) for id in ids_or_codes]

        # N.B. When checking for 404s, don't put more than 30 terms into a
        # property filter, otherwise the Datastore will raise. It's enough to
        # know that none of the first 30 "ids" provided are found or not. If
        # this criteria isn't valid then someone is providing a very broken
        # query and will get garbage out (empty lists, in this case).

        if ProjectCohort.count(uid=pc_ids[:30]) == 0:
            # Couldn't find any. Either they're all 404s or they're codes.
            # Attempt to convert the codes to ids_or_codes.
            codes = [ioc.replace('-', ' ') for ioc in ids_or_codes]
            if ProjectCohort.count(code=codes[:30]) == 0:
                # Still couldn't find any. Abort.
                return self.http_not_found()
            using_codes = True

        # User should have all necessary permissions.
        allowed = [
            self.parent_allowed('project_cohorts', ioc, user)
            for ioc in ids_or_codes
        ]
        if not all(allowed):
            return self.http_forbidden()

        by_value_result = ParticipantData.participation_by_project_cohort(
            codes if using_codes else pc_ids,
            using_codes=using_codes,
            **self.get_params({'start': 'datetime', 'end': 'datetime'})
        )

        # Wrangle to be keyed by the incoming id.
        keyed_result = util.list_by(
            by_value_result,
            'code' if using_codes else 'project_cohort_id',
        )
        for db_key in (codes if using_codes else pc_ids):
            key = db_key.replace(' ', '-')
            # If the project cohort has no participation, the db will not
            # return any rows, and the key won't be set, so default to
            # an empty list.
            keyed_result[key] = keyed_result.pop(db_key, [])

        return keyed_result

    def get_parent_id(self, parent_type, id):
        if parent_type == 'programs':
            uid = id  # really the program label
        else:
            klass = DatastoreModel.url_kind_to_class(parent_type)
            uid = klass.get_long_uid(id)
            parent = DatastoreModel.get_by_id(uid)
            if parent is None:
                # We might not have been able to find this id because it was a
                # participation code. Treat it is a such and see if we do any
                # better.
                pcs = ProjectCohort.get(code=id.replace('-', ' '))
                if len(pcs) > 0:
                    uid = pcs[0].uid
                else:
                    uid = None

        return uid


class CompletionIdsCsv(Participation):
    requires_auth = True

    def get(self, parent_type, id):
        # Requiring a one-time token discourages users from revisiting this
        # URL repeatedly to download this data. However it does NOT add any
        # meaningful security because it's easy for users to request new tokens
        # for themselves.
        token = self.get_params({'token': str}).get('token', '')
        user, error = AuthToken.check_token_string(token)
        if error:
            logging.info("AuthToken error: {}".format(error))
            return self.http_bad_request("Invalid token.")

        # Don't clear all tokens b/c that would affect password resets and
        # similar. Just this one.
        AuthToken.mark_as_used(token)

        type_to_field = {'project_cohorts': 'project_cohort_id'}
        if parent_type not in type_to_field.keys():
            return self.http_bad_request("Invalid parent for completion ids.")
        project_cohort_id = self.get_parent_id(parent_type, id)
        if not project_cohort_id:
            return self.http_not_found()

        # This is the meaningful security precaution. User must be authenticated
        # and associated with the data.
        user = self.get_current_user()
        if not owns(user, project_cohort_id):
            return self.http_forbidden("Insufficent permission.")

        kwargs = dict(
            project_cohort_id=project_cohort_id,
            **self.get_params({'start': 'datetime', 'end': 'datetime'})
        )

        results = ParticipantData.completion_ids(**kwargs)

        self.response.write(self.to_csv_str(results))
        self.response.headers['Content-Type'] = 'application/csv'

        # Notify super admins a download has occurred. These are also recorded
        # by the client to ProjectCohort.data_export_survey.
        if not user.super_admin:
            notifier.downloaded_identifiers(user, project_cohort_id)

    def to_csv_str(self, results):
        # https://github.com/jdunck/python-unicodecsv
        with BytesIO() as fh:
            w = unicodecsv.DictWriter(
                fh,
                fieldnames=('token', 'percent_progress', 'module'),
                encoding='utf-8'
            )
            w.writeheader()
            for row in results:
                w.writerow(row)
            fh.seek(0)
            csv_str = fh.read()
        return csv_str


class CompletionIdsAnonymous(Participation):
    requires_auth = True

    def get(self, parent_type, id_or_code):
        """Get anonymous participant ids and their progress through surveys
        related to this project cohort.

        Args:
            parent_type: str, always 'project_cohorts'
            id_or_code: str, either a uid or a participation code, identifies a unique
                project cohort.
        """
        type_to_field = {'project_cohorts': 'project_cohort_id'}
        if parent_type not in type_to_field.keys():
            return self.http_bad_request("Invalid parent for completion ids.")
        project_cohort_id = self.get_parent_id(parent_type, id_or_code)

        user = self.get_current_user()

        if not project_cohort_id:
            return self.http_not_found()
        if not self.parent_allowed(parent_type, id_or_code, user):
            return self.http_forbidden()

        params = self.get_params({'start': 'datetime', 'end': 'datetime'})
        if 'start' not in params or 'end' not in params:
            return self.http_bad_request("Missing 'start' and 'end' times.")

        results = ParticipantData.completion_ids_anonymous(
            project_cohort_id,
            params['start'],
            params['end'],
        )

        self.write(results)

    def parent_allowed(self, parent_type, parent_id, user):
        # Apply permissions. Triton may endorse a user to call this.
        try:
            allowed = owns(user, parent_id)
        except NotImplementedError:
            allowed = False  # it's likely a code
        if not allowed:
            jwt_user, jwt_error = self.get_jwt_user()
            jwt_user_ok = jwt_user and not jwt_error
            endpoint_ok = self.jwt_allows_endpoint(self.get_endpoint_str())
            allowed = jwt_user_ok and endpoint_ok

        return allowed


class CohortCompletion(ApiHandler):
    requires_auth = True

    def get(self, program_label):
        if not self.get_current_user().super_admin:
            return self.http_forbidden()

        self.write(ParticipantData.completion_by_cohort(program_label))


class Participants(ApiHandler):
    def get(self, participant_id=None):
        if not participant_id:
            return self.query()

        participant = Participant.get_by_id(participant_id)
        if participant:
            self.write(participant)
        else:
            self.error(404)

    def query(self):
        params = self.get_params({'name': unicode, 'organization_id': str},
                                 required=True)
        if not params['name'] or not params['organization_id']:
            self.error(400)  # Bad Request
            return
        self.write(Participant.get(**params))

    def post(self):
        params = self.get_params({
            'id': str,
            'name': unicode,
            'organization_id': str,
        })
        if 'name' not in params or 'organization_id' not in params:
            return self.http_bad_request()

        participant = Participant.create(**params)
        try:
            participant.put()
        except IntegrityError as error:
            if error.args[1].startswith('Duplicate entry'):
                # Slow networks using the participant portal often post
                # multiple times to this endpoint, but every one after the
                # first causes an error because of the unique name-org index on
                # the participant table. Silence the error and give the browser
                # a redirect to the existing entity instead. The portal will
                # call the redirect and use that object as the participant.
                logging.info("MySQL error downgraded to warning, see "
                             "api_handlers.Participants for comments.")

                participant = Participant.get(
                    name=params['name'],
                    organization_id=params['organization_id'],
                )[0]
                return self.http_see_other(participant.uid)
            else:
                raise error

        self.write(participant)

    def put(self, *args, **kwargs):
        return self.http_method_not_allowed('HEAD, GET, POST')

    def delete(self, *args, **kwargs):
        return self.http_method_not_allowed('HEAD, GET, POST')

    def http_see_other(self, id):
        # https://stackoverflow.com/questions/9414374/whats-a-proper-response-status-code-to-rest-post-request-when-duplicate-is-foun
        # https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.3.4
        self.response.status = 303
        link = '{protocol}://{domain}/api/participants/{id}'.format(
            protocol='http' if util.is_localhost() else 'https',
            domain=('localhost:8080' if util.is_localhost()
                    else os.environ['HOSTING_DOMAIN']),
            id=id,
        )
        self.response.headers['Location'] = link


class ParticipantDataHandler(ApiHandler):
    # POSTs will contain responses from participants; don't log them.
    should_log_request = False

    def get(self, participant_id, key=None):
        params = self.get_params({'project_cohort_id': str})
        pc_id = params.get('project_cohort_id', None)

        if key:
            # The key is only for POST.
            return self.http_bad_request("Invalid parameter: `key`.")

        self.write(ParticipantData.get_by_participant(participant_id, pc_id))

    def post(self, participant_id, key):
        expected = {
            'value': unicode,
            'survey_id': str,
        }
        params = self.get_params(expected)
        survey_id, survey_descriptor = (
            ParticipantData.separate_survey_descriptor(params['survey_id']))

        # Get remaining params from the survey.
        survey = Survey.get_by_id(survey_id)
        project_cohort = ProjectCohort.get_by_id(survey.project_cohort_id)

        # Add optional survey descriptor.
        if not survey_descriptor:
            survey_descriptor = self.get_param('survey_descriptor', str, None)
        if survey_descriptor:
            params['survey_id'] = ParticipantData.combine_survey_descriptor(
                survey.uid,
                survey_descriptor,
            )

        params['survey_ordinal'] = survey.ordinal
        params['program_label'] = survey.program_label
        params['project_id'] = survey.project_id
        params['cohort_label'] = survey.cohort_label
        params['project_cohort_id'] = survey.project_cohort_id
        params['code'] = project_cohort.code

        # All params should be present and truthy.
        if not all([k in params and params[k] for k in expected.keys()]):
            return self.http_bad_request('Missing parameters.')

        if (
            key == 'progress' and
            not ParticipantData.is_valid_progress_value(params['value'])
        ):
            return self.http_bad_request('Invalid progress value.')

        params['participant_id'] = participant_id
        params['key'] = key

        pd = ParticipantData.create(**params)

        if ParticipantData.is_progress_downgrade(pd):
            message = 'Progress value may not decrease.'
            logging.warning(message)
            return self.http_bad_request(message)

        pd = ParticipantData.put_for_index(pd, 'participant-survey-key')

        self.write(pd)

    def put(self, *args, **kwargs):
        return self.http_method_not_allowed('HEAD, GET, POST')

    def delete(self, *args, **kwargs):
        return self.http_method_not_allowed('HEAD, GET, POST')


class ParticipantDataCorsHandler(ApiHandler):
    """Similar to ParticipantDataHandler, but with the following additions:
    * This provides a CORS accessible means for Qualtrics integration.
    * Checks that all the fields for writing a row to `participant_data` are
      present in the query string.
    * Checks that the `participant_id` exists in `participant` table.
    * Checks that `key` is set to `progress`.
    * Checks that `value` is an integer between `0` and `100` inclusive.
    * Responds with `200` regardless of data validity, with tiny gif.
    """
    # POSTs will contain responses from participants; don't log them.
    should_log_request = False

    def get(self, participant_id):
        pd = self.update_participant_data(participant_id)
        if pd:
            logging.info(
                u"Inserted or updated pd for: {} {}"
                .format(pd.participant_id, pd.survey_id)
            )
        else:
            logging.info("Invalid params, did not insert.")
        self.cors_gif_response()

    def update_participant_data(self, participant_id):
        expected = {
            'key': str,
            'value': unicode,
            'survey_id': str,
        }
        params = self.get_params(expected)
        survey_id, survey_descriptor = (
            ParticipantData.separate_survey_descriptor(params['survey_id']))

        # All params should be present and truthy.
        if not all([k in params and params[k] for k in expected.keys()]):
            logging.info("One or more params is missing or falsy.")
            return None

        # Participant should exist
        if not Participant.get_by_id(participant_id):
            logging.info("Participant does not exist.")
            return None

        if (
            params['key'] == 'progress' and
            not ParticipantData.is_valid_progress_value(params['value'])
        ):
            return None

        # If we've passed all the above validation, add participant data
        params['participant_id'] = participant_id

        # Get remaining params from the survey.
        survey = Survey.get_by_id(survey_id)
        if not survey:
            logging.info("Survey doesn't exist.")
            return None

        project_cohort = ProjectCohort.get_by_id(survey.project_cohort_id)

        if not survey_descriptor:
            survey_descriptor = self.get_param('survey_descriptor', str, None)
        if survey_descriptor:
            params['survey_id'] = ParticipantData.combine_survey_descriptor(
                survey.uid,
                survey_descriptor,
            )

        params['survey_ordinal'] = survey.ordinal
        params['program_label'] = survey.program_label
        params['project_id'] = survey.project_id
        params['cohort_label'] = survey.cohort_label
        params['project_cohort_id'] = survey.project_cohort_id
        params['code'] = project_cohort.code
        params.update(self.get_params({'testing': bool}, required=True))

        pd = ParticipantData.create(**params)

        if ParticipantData.is_progress_downgrade(pd):
            message = 'Progress value may not decrease.'
            logging.warning(message)
            return None

        pd = ParticipantData.put_for_index(pd, 'participant-survey-key')
        return pd

    def cors_gif_response(self):
        # Enabling CORS in Python
        # https://enable-cors.org/server_appengine.html
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        # A 1x1 transparent pixel in a base64 encoded string. See
        # http://stackoverflow.com/questions/2933251/code-golf-1x1-black-pixel
        self.response.headers['Content-Type'] = 'image/gif'
        gif_data = 'R0lGODlhAQABAAAAACwAAAAAAQABAAACAkwBADs='.decode('base64')
        self.response.out.write(gif_data)


class SurveyLinks(ApiHandler):
    def post(self, program_label, survey_ordinal):
        survey_link = SurveyLink.get_unique(program_label, int(survey_ordinal))
        if survey_link:
            self.write(survey_link)
        else:
            # No survey links found!
            self.error(404)


class ParticipationCodes(RestHandler):
    def get(self, code=None):
        # Public endpoint for getting details from a participation code.

        if code is None:
            return self.http_method_not_allowed('POST')

        # Codes have spaces replaced with dashes when they're in the URL.
        code = code.replace('-', ' ')
        pc_result = ProjectCohort.get(code=code)

        if len(pc_result) > 1:
            logging.error("Participation code duplication!")
            logging.info(pc_result)
            # gracefully fall through

        if len(pc_result) > 0:
            self.write(pc_result[0])
        else:
            # This error is too noisy.
            # logging.error("Someone asked for a code and got 404'ed: {}"
            #               .format(self.request.path_qs))
            return self.http_not_found()

    def post(self, code=None):
        """Starting with Triton, this is a multi-system service, with POST
        meaning "issue me a unique code please."""
        if code:
            return self.http_method_not_allowed('GET, HEAD, PUT, DELETE')

        user = self.get_current_user()
        if user.user_type == 'public':
            return self.http_unauthorized()

        prop_types = {
            'organization_id': str,
            'program_label': str,
            'portal_type': str,  # see nepApi.ProjectCohort.PORTAL_TYPES
            'portal_message': unicode,
            'survey_params': 'json',
        }
        params = self.get_params(prop_types)

        required = ('organization_id', 'program_label')
        for k in required:
            if k not in params:
                return self.http_bad_request("Parameter '{}' required."
                                             .format(k))

        pc = ProjectCohort.create(
            organization_id=params['organization_id'],
            program_label=params['program_label'],
            portal_type=params.get('portal_type', None),
            portal_message=params.get('portal_message', None),
            survey_params=params.get('survey_params', None),
        )
        pc.put()

        # Create surveys according to the program definition.
        program = Program.get_config(params['program_label'])
        surveys = []
        for i, survey_definition in enumerate(program['surveys']):
            # Most things we need for surveys are available as pc params.
            survey = Survey.create(
                survey_definition['survey_tasklist_template'],
                project_id=params.get('project_id', None),
                organization_id=params['organization_id'],
                program_label=params['program_label'],
                cohort_label=params.get('cohort_label', None),
                project_cohort_id=pc.uid,
                ordinal=i + 1,
            )
            surveys.append(survey)
        ndb.put_multi(surveys)

        self.write({k: v for k, v in pc.to_client_dict().items()
                    if k in prop_types or k == 'code'})

    def put(self, code=None):
        """Modify the data attached to a participation code."""
        if code is None:
            return self.http_method_not_allowed('POST')

        user, error = self.get_jwt_user()
        if not user or error:
            return self.http_unauthorized("Must use JWT.")

        if not self.jwt_allows_endpoint():
            return self.http_forbidden(
                "Did not find correct 'allowed_endpoints' value in jwt.")

        params = self.get_params({
            'name': unicode,
            'organization_id': str,
            'portal_message': unicode,
            'survey_params': 'json',
        })

        pc_result = ProjectCohort.get(code=code.replace('-', ' '))
        if len(pc_result) == 0:
            return self.http_not_found()

        project_cohort = pc_result[0]
        for k, v in params.items():
            setattr(project_cohort, k, v)
        project_cohort.put()

        self.write(project_cohort)

    def delete(self, code=None):
        if code is None:
            return self.http_method_not_allowed('POST')

        user, error = self.get_jwt_user()
        if not user or error:
            return self.http_unauthorized("Must use JWT.")

        if not self.jwt_allows_endpoint():
            return self.http_forbidden(
                "Did not find correct 'allowed_endpoints' value in jwt.")

        pc_result = ProjectCohort.get(code=code.replace('-', ' '))
        if len(pc_result) == 0:
            return self.http_not_found()

        project_cohort = pc_result[0]
        key_name = ProjectCohort.uniqueness_key(project_cohort.code)
        unique_key = ndb.Key('Unique', key_name)
        # n = 10 should be fine here, we never have that many surveys per pc.
        survey_keys = Survey.get(project_cohort_id=project_cohort.uid,
                                 keys_only=True)

        ndb.delete_multi([project_cohort.key, unique_key] + survey_keys)

        return self.http_no_content()


class Emails(RestHandler):
    requires_auth = True

    model = Email

    def query(self, **kwargs):
        """Only allow queries by recipient address."""
        params = self.get_params({'to_address': unicode})
        if 'to_address' not in params:
            self.error(400)
        else:
            return super(Emails, self).query(**kwargs)

    def put(self):
        self.not_allowed()

    def delete(self):
        self.not_allowed()

    def not_allowed(self):
        self.error(405)
        self.response.headers['Allow'] = 'GET, HEAD, POST'


class MandrillTemplates(ApiHandler):
    requires_auth = True

    def get(self, slug=None):
        """Get a template or list available."""
        if slug:
            results = mandrill.call(
                'templates/info.json',
                {'name': slug}
            )
        else:
            results = mandrill.call(
                'templates/list.json',
                {'label': 'neptune'}
            )

        self.write(results)


api_routes = rserve_routes + [

    # Super-admin-only, all-access GraphQL.

    Route('/api/graphql', GraphQLBase),

    # Database administration

    Route('/api/everything', Everything),
    Route('/api/seed', Seed),
    Route('/api/seed/<program>', Seed),
    Route('/api/seed/<program>/<cohort>', Seed),
    Route('/api/seed/<program>/<cohort>/<n>', Seed),

    # Authentication.

    Route('/api/login', Login),
    Route('/api/login/<email>', Login),
    Route('/api/register', Register),
    Route('/api/reset_password', ResetPassword),
    Route('/api/set_password', SetPassword),
    Route('/api/invitations', Invitations),
    Route('/api/auth_tokens', AuthTokens),
    Route('/api/auth_tokens/<token>/user', UserFromAuthToken),
    Route('/api/accounts/<email>', Accounts),

    # Getting users via special roles: liaisons and account managers.

    Route('/api/projects/<project_id>/account_manager', ProjectAccountManager),
    Route('/api/organizations/<id>/liaison', Liaison),
    Route('/api/projects/<id>/liaison', Liaison),
    Route('/api/project_cohorts/<id>/liaison', Liaison),
    Route('/api/surveys/<id>/liaison', Liaison),

    # Getting users directly and by relationship.

    Route('/api/users', Users),
    Route('/api/users/<id>', Users),
    Route('/api/<parent_type:organizations>/<rel_id>/users',
          RelatedQuery(User, 'owned_organizations')),
    Route('/api/<parent_type:organizations>/<rel_id>/users/<id>',
          UserRelationship('owned_organizations')),
    Route('/api/<parent_type:organizations>/<rel_id>/associated_users',
          RelatedQuery(User, 'assc_organizations')),
    Route('/api/<parent_type:programs>/<rel_id>/users',
          RelatedQuery(User, 'owned_programs')),
    Route('/api/<parent_type:programs>/<rel_id>/users/<id>',
          UserRelationship('owned_programs')),
    Route('/api/<parent_type:projects>/<rel_id>/users',
          RelatedQuery(User, 'owned_projects')),
    Route('/api/<parent_type:projects>/<rel_id>/users/<id>',
          UserRelationship('owned_projects')),

    # Participation

    Route('/api/<parent_type>/participation', Participation),
    Route('/api/<parent_type>/<id>/participation', Participation),
    Route('/api/<parent_type:programs>/<id>/cohorts/<cohort_label>/'
          'participation', Participation),
    Route('/api/programs/<program_label>/cohort_completion', CohortCompletion),
    Route('/api/<parent_type:project_cohorts>/<id_or_code>/completion',
          CompletionIdsAnonymous),
    Route('/api/<parent_type:project_cohorts>/<id>/completion/ids.csv',
          CompletionIdsCsv),

    # Getting public properties of organizations.

    Route(
        '/api/organizations/<prop:{}>'.format(
            '|'.join(p + 's' for p in Organization.public_properties)
        ),
        OrganizationProperty
    ),
    Route(
        '/api/organizations/<id>/<prop:{}>'.format(
            '|'.join(Organization.public_properties)
        ),
        OrganizationProperty
    ),
    Route('/api/organizations', Organizations),
    Route('/api/organizations/<id>', Organizations),

    Route('/api/users/<user_id>/'
          '<relationship:organizations|associated_organizations>',
          UsersOrganizations),
    Route('/api/users/<user_id>/'
          '<relationship:organizations|associated_organizations>/<org_id>',
          UsersOrganizations),

    Route('/api/programs', Programs),
    Route('/api/programs/<label>', Programs),

    Route('/api/projects', Projects),
    Route('/api/projects/<id>', Projects),
    Route('/api/<parent_type:organizations>/<rel_id>/projects',
          RelatedQuery(Project, 'organization_id')),
    Route('/api/<parent_type:programs>/<rel_id>/projects',
          RelatedQuery(Project, 'program_label')),

    # Not using RelatedQuery b/c Tasks are in entity groups.
    Route('/api/tasks', Tasks),
    Route('/api/tasks/<id>', Tasks),
    Route('/api/<parent_type>/<parent_id>/tasks', Tasks),
    Route('/api/tasks/<id>/attachment', TasksAttachment),

    # Not using RelatedQuery b/c Checkpoints are in SQL.
    Route('/api/checkpoints', Checkpoints),
    Route('/api/checkpoints/<id>', Checkpoints),
    Route('/api/<parent_type>/<parent_id>/checkpoints', Checkpoints),

    Route('/api/project_cohorts', ProjectCohorts),
    Route('/api/project_cohorts/<id>', ProjectCohorts),
    Route('/api/<parent_type:organizations>/<rel_id>/project_cohorts',
          RelatedQuery(ProjectCohort, 'organization_id')),
    Route('/api/<parent_type:projects>/<rel_id>/project_cohorts',
          RelatedQuery(ProjectCohort, 'project_id')),

    Route('/api/tasklists/<project_cohort_id>', TasklistHandler),
    Route('/api/users/<user_id>/dashboard', DashboardByOwner),
    Route('/api/organizations/<organization_id>/dashboard', DashboardByOwner),
    Route('/api/dashboard', SuperDashboard),

    Route('/api/secret_values', SecretValues),
    Route('/api/secret_values/<id>', SecretValues),

    Route('/api/surveys', Surveys),
    Route('/api/surveys/<id>', Surveys),
    Route('/api/<parent_type:organizations>/<rel_id>/surveys',
          RelatedQuery(Survey, 'organization_id')),
    Route('/api/<parent_type:projects>/<rel_id>/surveys',
          RelatedQuery(Survey, 'project_id')),
    Route('/api/<parent_type:project_cohorts>/<rel_id>/surveys',
          RelatedQuery(Survey, 'project_cohort_id')),

    Route('/api/task_reminders', TaskReminders),
    Route('/api/task_reminders/<id>', TaskReminders),
    # Not using RelatedQuery b/c Tasks are in entity groups.
    Route('/api/users/<user_id>/task_reminders', TaskReminders),

    Route('/api/account_managers', AccountManagers),
    Route('/api/account_managers/<id>', AccountManagers),
    Route('/api/liaisonships', Liaisonships),
    Route('/api/liaisonships/<id>', Liaisonships),

    Route('/api/notifications', Notifications),
    Route('/api/notifications/<id>', Notifications),
    Route('/api/users/<parent_id>/notifications', Notifications),

    # Participants and participant data
    Route('/api/participants', Participants),
    Route('/api/participants/<participant_id>', Participants),
    Route('/api/participants/<participant_id>/data', ParticipantDataHandler),
    Route('/api/participants/<participant_id>/data/cross_site.gif',
          ParticipantDataCorsHandler),
    Route('/api/participants/<participant_id>/data/<key>',
          ParticipantDataHandler),
    Route('/api/survey_links/<program_label>/<survey_ordinal>/get_unique',
          SurveyLinks),

    Route('/api/codes', ParticipationCodes),
    Route('/api/codes/<code>', ParticipationCodes),

    Route('/api/emails', Emails),
    Route('/api/emails/<id>', Emails),

    Route('/api/mandrill_templates', MandrillTemplates),
    Route('/api/mandrill_templates/<slug>', MandrillTemplates),
]
