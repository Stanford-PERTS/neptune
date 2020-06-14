"""Test auth tokens."""

import datetime
import logging
import time
import unittest

from unit_test_helper import ConsistencyTestCase
from model import (AuthToken, User)


class TestAuthToken(ConsistencyTestCase):
    """Test basic functions of our data model, i.e. the DatastoreModel class."""

    consistency_probability = 0

    def create_parent_user(self):
        user = User.create(email='test@example.com')
        user.put()
        # Force consistency so we can isolate the test of auth tokens.
        user.key.get()
        return user

    def test_auth_token_validation(self):
        """Correct tokens should pass, wrong ones should fail."""
        user = self.create_parent_user()

        auth_token = AuthToken.create_or_renew(user.uid)
        auth_token.put()

        matched_user, error = AuthToken.check_token_string(auth_token.token)
        self.assertEqual(user, matched_user)

        dne_user, error = AuthToken.check_token_string('bad token')
        self.assertIsNone(dne_user)
        self.assertEqual(error, 'not found')

    def test_auth_token_expiration(self):
        """Old tokens should fail."""
        user = self.create_parent_user()

        auth_token = AuthToken.create_or_renew(user.uid)
        auth_token.put()

        # Simulate over 48 hours passing.
        auth_token.created = auth_token.created - datetime.timedelta(hours=50)
        auth_token.put()

        matched_user, error = AuthToken.check_token_string(auth_token.token)
        self.assertIsNone(matched_user)  # b/c expired
        self.assertEqual(error, 'expired')

    def test_auth_token_custom_expiration(self):
        """Old tokens should fail."""
        user = self.create_parent_user()

        auth_token = AuthToken.create_or_renew(user.uid, duration=3)
        auth_token.put()

        # Simulate over an hour passing.
        auth_token.created = auth_token.created - datetime.timedelta(hours=2)
        auth_token.put()

        matched_user, error = AuthToken.check_token_string(auth_token.token)
        self.assertEqual(user, matched_user)  # b/c extended duration

        # Simulate over three hours passing.
        auth_token.created = auth_token.created - datetime.timedelta(hours=4)
        auth_token.put()

        matched_user, error = AuthToken.check_token_string(auth_token.token)
        self.assertIsNone(matched_user)  # b/c expired
        self.assertEqual(error, 'expired')

    def test_overwriting_expired_auth_tokens(self):
        """Creating should make a new token when there are expired ones."""
        user = self.create_parent_user()

        token_one = AuthToken.create_or_renew(user.uid)
        token_one.put()

        # Simulate over 48 hours passing.
        token_one.created = token_one.created - datetime.timedelta(hours=50)
        token_one.put()

        # This should be a new token, not a re-used one.
        token_two = AuthToken.create_or_renew(user.uid)
        self.assertNotEqual(token_one.token, token_two.token)

    def test_overwriting_deleted_auth_tokens(self):
        """Creating should make a new token when there are deleted ones."""
        user = self.create_parent_user()

        token_one = AuthToken.create_or_renew(user.uid)
        token_one.deleted = True
        token_one.put()

        # This should be a new token, not a re-used one.
        token_two = AuthToken.create_or_renew(user.uid)
        self.assertNotEqual(token_one.token, token_two.token)

    def test_resusing_valid_auth_token(self):
        """Creating when a valid one exists should reuse it."""
        user = self.create_parent_user()

        token_one = AuthToken.create_or_renew(user.uid)
        old_created = token_one.created
        token_one.put()

        time.sleep(.01)

        # This should be the same token, but with a newer creation time.
        token_two = AuthToken.create_or_renew(user.uid)
        self.assertEqual(token_one.token, token_two.token)
        self.assertLess(token_one.created, token_two.created)

    def test_malformed_auth_token(self):
        """Should handle any string, e.g. jwts, or garbage."""
        # Although this has underscores, it shouldn't be interpreted as a uid.
        jwt = (
            'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTgwMjc1MDksImp0'
            'aSI6ImY0MWE3N2UyLTMxOTctNGNhNC05OGYwLWFkMWI0MGQ1ZjhhYSIsInVzZXJfa'
            'WQiOiJVc2VyX0xLTzNDb00zIiwiZW1haWwiOiJiYmFycmV0dEBsYW5pZXJocy5vcm'
            'ciLCJleHAiOjE1MTgyMDAzMDl9._nGqLn4dRJjcWMMnorTvgCewXX2wN5_S-QiUwf'
            '6n_lmiN3A0pD46fisIFSEhMihRD7PKqoQUHbYP4Hc30hd48w'
        )
        # O hedgehog of curses, generate for the Finns a part of the game of
        # ignominies!
        # http://clagnut.com/blog/2380/
        garbage = u'Je\u017cu kl\u0105tw, sp\u0142\xf3d\u017a Finom cz\u0119\u015b\u0107 gry ha\u0144b!'
        empty = ''

        for t in (jwt, garbage, empty):
            user, error = AuthToken.check_token_string(t)
            self.assertEqual(error, 'not found')
