"""Maps view and api URLs to handlers defined elsewhere.

Takes the routes and handlers defined in other files and makes a wsgi
application. See app.yaml for which wsgi applications are used where.
"""

import webapp2

from api_handlers import api_routes
from cron_handlers import cron_routes
from map_handlers import map_routes
from model import SecretValue
from task_handlers import task_routes
from view_handlers import view_routes
import config
import logging
import util


# Attempt to look up the encryption key used to protect our session cookies.
# In normal operation there should be one stored in a SecretValue entity. If
# we can't find it, fill in a default value, but log an error to bother the
# devs.
sv_entity = SecretValue.get_by_id('session_cookie_secret_key')
if sv_entity is None:
    secret_key = config.default_session_cookie_secret_key
    if not util.is_localhost():
        logging.error("No SecretValue set for 'session_cookie_secret_key'.")
else:
    # Why the string coercion? If the value here is a unicode, app
    # engine complains, "TypeError: character mapping must return
    # integer, None or unicode"
    secret_key = str(sv_entity.value)

webapp2_config = {
    'webapp2_extras.sessions': {
        # Related to cookie security, see:
        # http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
        'secret_key': secret_key
    },
}

# Monkey-patch to allow PATCH, otherwise webapp2 will 501 any calls.
allowed = webapp2.WSGIApplication.allowed_methods
webapp2.WSGIApplication.allowed_methods = allowed.union(('PATCH',))

application = webapp2.WSGIApplication(
    # Keep view_routes last, because it has a catch-all route.
    task_routes + cron_routes + map_routes + api_routes + view_routes,
    config=webapp2_config,
    debug=util.is_development()
)
