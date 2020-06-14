"""Miscellaneous functions to allow better code reuse in api_handlers.py."""

import datetime
import pytz
import re

from model import AuthToken
import config
import jwt_helper
import util


class SetPasswordDomainForbidden(Exception):
    """When we attempt to send a set password link to an unsafe domain."""
    pass


def check_domain_allowed(domain):
    # Make sure it's legit so Eve can't send a legit user a link to her
    # evil site.
    is_allowed = any(re.match(p, domain) for p in config.allow_origins)
    if not is_allowed:
        raise SetPasswordDomainForbidden(
            "Got a request to send an invite link for an "
            "unallowed domain: {}".format(domain)
        )
    return True


TOKEN_DURATION_HOURS = 7 * 24


def platform_token(platform, user):
    """Returns AuthToken strings for 'neptune', otherwise jwts."""
    # Unfortunately we're caught between two authentication schemes,
    # one home-grown (Neptune's AuthToken) and JWT Authorization
    # headers (used in Triton and future systems).
    if platform == 'neptune':
        duration_hours = TOKEN_DURATION_HOURS
        token_entity = AuthToken.create_or_renew(
            user.uid, duration = duration_hours)
        token_entity.put()
        return token_entity.token
    else:
        return jwt_helper.encode_user(
            user, expiration_minutes=TOKEN_DURATION_HOURS * 60)


def apply_auth_defaults(params):
    params = params.copy()

    if 'platform' not in params:
        # Default to neptune
        params['platform'] = config.platform_name

    if 'from_name' not in params:
        if params['platform'] == 'neptune':
            params['from_name'] = 'PERTS'
        if params['platform'] == 'triton':
            params['from_name'] = 'Copilot'


    if 'template_content' not in params:
        params['template_content'] = {}

    if 'contact_email_address' not in params['template_content']:
        params['template_content']['contact_email_address'] = \
            params.get('from_address', config.from_server_email_address)

    if 'domain' in params:
        check_domain_allowed(params['domain'])
    else:
        # Default the domain to neptune.
        params['domain'] = util.get_domain()
    # Either way, also make it available to email templates
    params['template_content']['domain'] = params['domain']

    return params

def get_token_expiration_str():
    exp_datetime = (
        datetime.datetime.now(pytz.timezone("America/Los_Angeles")) +
        datetime.timedelta(hours=TOKEN_DURATION_HOURS)
    )
    # e.g. "7:30 PM on Wednesday, Dec 4, 2019 PST"
    return exp_datetime.strftime('%-I:%M %p on %A, %b %-d, %Y %Z')
