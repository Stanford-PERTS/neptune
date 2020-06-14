"""Defines specific links that should be immediately redirected elsewhere.

N.B. None of these work unless they're also specified in app.yaml.
"""

import webapp2


# Reminder: 302's are temporary, 301's are permanent.
redirection_map = {
    '/neptune-privacy': ('https://www.perts.net/privacy', 301),
}


class RedirectionHandler(webapp2.RequestHandler):
    def get(self):
        url, code = redirection_map[self.request.path]
        if self.request.query_string:
            url = '{}?{}'.format(url, self.request.query_string)
        self.redirect(url, code=code)


application = webapp2.WSGIApplication(
    [(k, RedirectionHandler) for k, v in redirection_map.items()])
