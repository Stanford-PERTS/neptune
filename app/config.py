"""Hard-coded python settings.

Note: settings related to environment (production, etc.) should go in the
branch_environments.json file or app.template.yaml file.
"""

# When this is False, the server will accept valid jwts as holy scripture and
# change its own records to make sure that user emails and ids match the token.
# Currently Neptune is our auth server and Triton is not.
is_auth_server = True
platform_name = 'neptune'

auth_types = ['email', 'google_id']

session_cookie_name = 'neptune_login'
# Only used when a SecretValue for this isn't yet set.
default_session_cookie_secret_key = ''

# Only used when a SecretValue for this isn't set.
default_mandrill_api_key = ''

default_jwt_secret = ''

default_jwt_secret_rsa = ''

default_jwt_public_rsa = ''


def generate_rsa_key_pair():
    from Crypto.PublicKey import RSA

    key = RSA.generate(2048)

    return {
        'private': key.exportKey('PEM'),
        'public': key.publickey().exportKey('PEM'),
    }


# Clients from these origins are allowed to make requests from the Neptune API.
allow_origins = [
    r'^http://localhost(:\d+)?/?$',
    r'^https://neptune.perts.net/?$',
    r'^https://copilot.perts.net/?$',
    r'^https://(\S+-dot-)?neptuneplatform.appspot.com/?$',
    r'^https://(\S+-dot-)?neptune-dev.appspot.com/?$',
    r'^https://(\S+-dot-)?tritonplatform.appspot.com/?$',
    r'^https://(\S+-dot-)?triton-dev.appspot.com/?$',
    r'^https://www.perts.net/?$',
    r'^https://(\S+-dot-)?yellowstoneplatform.appspot.com/?$',
    r'^https://(\S+-dot-)?yellowstone-dev.appspot.com/?$',
]

# At least 8 characters.
password_pattern = r'^.{8,}$'

# ISO 8601 in UTC for strptime() and strftime()
iso_datetime_format = '%Y-%m-%dT%H:%M:%SZ'
iso_date_format = '%Y-%m-%d'
sql_datetime_format = '%Y-%m-%d %H:%M:%S'

# Email settings
#
to_dev_team_email_addresses = []
# Default FROM address and name
from_server_email_address = ''
from_server_name = ''
# * spam prevention *
# time between emails
# if we exceed this for a given to address, an error will be logged
suggested_delay_between_emails = 10      # 10 minutes
# whitelist
# some addessess we spam
addresses_we_can_spam = []
# Determines if Mandrill sends emails on local or dev environments
should_deliver_smtp_dev = True

# Time, in seconds, queued tasks should wait before executing, to encourage the
# datastore to reach consistency first.
# https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.api.taskqueue#google.appengine.api.taskqueue.add
task_consistency_countdown = 30


