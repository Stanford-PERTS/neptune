from six import BytesIO
import datetime
import logging
import unittest
import webapp2
import webtest

from gae_handlers.api import ApiHandler
from unit_test_helper import PertsTestCase
import json


class TestApiParams(PertsTestCase):
    def test_coerces_json(self):
        handler = ApiHandler()
        self.assertEqual(
            handler.coerce_param('x', '["a"]', 'json'),
            ['a']
        )
        with self.assertRaises(ValueError):
            handler.coerce_param('x', 'bar', 'json')

    def test_coerces_datetime(self):
        handler = ApiHandler()
        self.assertEqual(
            handler.coerce_param('x', '2000-01-01T00:00:00Z', 'datetime'),
            datetime.datetime(2000, 1, 1, 0, 0, 0)
        )
        with self.assertRaises(ValueError):
            handler.coerce_param('x', '2000-01-01 00:00:00', 'datetime'),

    def test_coerces_date(self):
        handler = ApiHandler()
        self.assertEqual(
            handler.coerce_param('x', '2000-01-01', 'date'),
            datetime.date(2000, 1, 1)
        )
        with self.assertRaises(ValueError):
            handler.coerce_param('x', '2000-01-01 00:00:00', 'date'),

    def test_coerces_bool(self):
        handler = ApiHandler()
        self.assertEqual(
            handler.coerce_param('x', 'true', bool),
            True
        )
        self.assertEqual(
            handler.coerce_param('x', 'false', bool),
            False
        )

    def test_coerces_str(self):
        handler = ApiHandler()
        # O hedgehog of curses, generate for the Finns a part of the game of
        # ignominies!
        # http://clagnut.com/blog/2380/
        hedgehog = u'Je\u017cu'
        self.assertEqual(
            handler.coerce_param('x', hedgehog, str),
            'Jeu'  # Drop non-ascii chars
        )

    def test_coerces_unicode(self):
        handler = ApiHandler()
        hedgehog = u'Je\u017cu'
        self.assertEqual(
            handler.coerce_param('x', hedgehog, unicode),
            hedgehog
        )

    def test_coerces_unicode(self):
        handler = ApiHandler()
        self.assertEqual(handler.coerce_param('x', '0', int), 0)
        self.assertEqual(handler.coerce_param('x', '01', int), 1)
        with self.assertRaises(ValueError):
            handler.coerce_param('x', '01x', int),

    def post_json(self, params):
        handler = ApiHandler()
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'application/json',
            'wsgi.input': BytesIO(json.dumps(params)),
        }
        handler.request = webapp2.Request.blank('/', environ)
        return handler

    def test_get_params_excludes_unmentioned(self):
        """Params not described are not returned."""
        handler = self.post_json({
            'foo': 'bar',
            'baz': 'qux',
        })

        self.assertEqual(
            handler.get_params({'foo': str}),  # lacks baz
            {'foo': 'bar'}  # also lacks baz
        )

    def test_get_params_does_not_insert(self):
        """Described params that are not present are not retruned."""
        handler = self.post_json({
            'foo': 'bar',
        })

        self.assertEqual(
            handler.get_params({'foo': str, 'baz': str}),
            {'foo': 'bar'}  # lacks baz
        )

    def test_get_params_requires_defaults(self):
        handler = self.post_json({
            'foo': 'bar',
        })

        self.assertEqual(
            handler.get_params({'foo': str, 'baz': str}, required=True),
            {'foo': 'bar', 'baz': ''}  # baz has default value
        )
