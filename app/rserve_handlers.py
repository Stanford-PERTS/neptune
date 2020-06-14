import cloudstorage as gcs
import logging

from gae_handlers import (ApiHandler, RestHandler, Route)
from model import Dataset
from permission import owns
import jwt_helper


def authenticate_rserve(handler):
    """Specialized authentication and log-in for requests from RServe.

    RServe is designed to echo an rsa-signed jwt back to Neptune. A dedicated
    super admin user account should be in the jwt. We log in that user so
    downstream handler code will execute with full permissions.

    Note that anyone who intercepts this jwt will be able to authenticate in
    the same way. Https should be the first line of defense against this, but
    also this form of authentication should only be used where necessary, and
    also the jwts should expire relatively quickly.

    Returns (rserve_user, error_msg).
    """
    payload, error = jwt_helper.decode_rsa(handler.get_jwt())

    if not payload or error:
        return (None, error)

    # Make sure the payload meets expectations.
    if not all(key in payload for key in ('user_id', 'email', 'user_type')):
        raise Exception("Authorization JWT must include user_id, email, and "
                        "user_type.")

    # Retrieve or create the user, who should be the rserve user, a super
    # admin.
    rserve_user = handler.sync_user_with_token(payload)

    # Replace the rsa-based token with the normal symmetric one which the rest
    # of our code will recognize as this user being logged in.
    handler.log_in(rserve_user)

    return (rserve_user, None)


class Datasets(RestHandler):
    model = Dataset

    def post(self):
        rserve_user, error = authenticate_rserve(self)
        if error == jwt_helper.NOT_FOUND:
            return self.http_unauthorized(error)
        elif error:
            return self.http_forbidden(error)

        if not rserve_user.super_admin:
            return self.http_forbidden("Must be super admin.")

        params = self.get_params({
            'content_type': str,
            'data': 'json',
            'filename': str,
            'parent_id': str,
        })
        # Parent id may be in the query string.
        parent_id = (self.request.get('parent_id', None) or
                     params.pop('parent_id', None))

        ds = Dataset.create(parent_id=parent_id, **params)
        ds.put()

        self.write(ds)

    def get(self, id=None):
        """Download the file linked to this dataset."""
        if id is None:
            return self.query()

        token = self.get_param('token', str, None)

        # The pattern of setting response error codes is strange here because
        # it's designed to be reused by another handler in
        # view_handlers.RenderedDataset.
        ds, error_method, error_msg = self.get_permissions(id, token)

        # Call whatever error method the permission function specified so all
        # the correct settings are made on this response. Then return without
        # any data.
        if error_method:
            args = tuple() if error_msg is None else (error_msg,)
            return getattr(self, error_method)(*args)

        self.response.headers.update({'Content-Type': str(ds.content_type)})
        self.response.write(ds.read())

    def get_permissions(self, id, token):
        """Returns tuple like (dataset, http_error_method_name, error_msg)."""
        if token:
            # This URL has jwt authentication embedded in the query string so
            # that it is shareable. Ignore other permission rules as long as
            # the jwt is valid.
            payload, error = jwt_helper.decode(token)
            if not payload or error:
                return (None, 'http_unauthorized', error)

            allowed_endpoints = payload.get('allowed_endpoints', [])
            if self.get_endpoint_str() not in allowed_endpoints:
                return (None, 'http_forbidden', "Endpoint not allowed.")

            ds = Dataset.get_by_id(id)
            if not ds:
                return (None, 'http_not_found', None)

        else:
            # Without a token, do normal user-based authentication.
            user = self.get_current_user()
            if user.user_type == 'public':
                return (None, 'http_unauthorized', '')

            ds = Dataset.get_by_id(id)
            if not ds:
                return (None, 'http_not_found', None)

            if not ds.parent_id:
                if not user.super_admin:
                    return (None, 'http_forbidden',
                            "Only supers can get parentless datasets.")
            elif not owns(self.get_current_user(), ds.parent_id):
                return (None, 'http_forbidden', "Must own parent.")

        return (ds, None, None)

    def put(self, id=None):
        if id:
            return self.http_method_not_implemented('GET, HEAD')
        else:
            return self.http_method_not_implemented('GET, HEAD, POST')

routes = [
    Route('/api/datasets', Datasets),
    Route('/api/datasets/<id>', Datasets),
]
