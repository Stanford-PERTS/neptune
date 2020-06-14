# -*- coding: utf-8 -*-

from unit_test_helper import PertsTestCase
from gae_handlers import ApiHandler, InvalidParamType
import datetime
import webapp2


class TestRequestParams(PertsTestCase):
    """Tests for parsing query string parameters in the request."""

    def create_handler(self, query_string):
        environ = {}
        request = webapp2.Request(environ)
        request.query_string = query_string
        return ApiHandler(request=request)

    def test_expected_native_types(self):
        """String, integer, boolean, and list handled as expected."""
        # Note that falsy-seeming things like '0' are seen by the handler as
        # strings, and any non-empty string is True according to python
        # (except the value we've customized: 'false').
        handler = self.create_handler(
            'string=foo&'
            'empty_string=&'
            'unicode=föô&'
            'integer=5&'
            'boolean1=true&boolean2=false&boolean3=1&boolean4=0&boolean5=&'
            'list=a&list=b'
        )
        param_types = {
            'string': str,
            'empty_string': str,
            'unicode': unicode,
            'integer': int,
            'boolean1': bool,
            'boolean2': bool,
            'boolean3': bool,
            'boolean4': bool,
            'boolean5': bool,
            'list': list,
        }
        expected_params = {
            u'string': 'foo',
            u'empty_string': '',
            u'unicode': u'föô',
            u'integer': 5,
            u'boolean1': True,
            u'boolean2': False,
            u'boolean3': True,
            u'boolean4': True,
            u'boolean5': False,
            u'list': [u'a', u'b'],
        }
        self.assertEqual(handler.get_params(param_types), expected_params)

    def test_expected_custom_types(self):
        """JSON, datetime, and date values handled as expected."""
        handler = self.create_handler(
            r'json_list=["a", "b"]&'
            r'json_dict={"a": 1}&'
            r'datetime=2007-03-04T21:08:12Z&'
            r'date=2007-03-04')
        param_types = {
            'json_list': 'json',
            'json_dict': 'json',
            'datetime': 'datetime',
            'date': 'date',
        }
        expected_params = {
            u'json_list': [u'a', u'b'],
            u'json_dict': {u'a': 1},
            u'datetime': datetime.datetime(2007, 3, 4, 21, 8, 12),
            u'date': datetime.date(2007, 3, 4),
        }
        self.assertEqual(handler.get_params(param_types), expected_params)

    def test_unspecified_excluded(self):
        """When not specifying types, values are ignored."""
        handler = self.create_handler(r'unspecified1=foo&unspecified2=5')
        self.assertEqual(handler.get_params(), {})

    def test_missing_required(self):
        """Missing expected params should get default values for their type."""
        param_types = {
            'string': str,
            'unicode': unicode,
            'integer': int,
            'boolean': bool,
            'list': list,
            'json': 'json',
            'datetime': 'datetime',
            'date': 'date',
        }
        expected_types = {
            'string': '',
            'unicode': u'',
            'integer': 0,
            'boolean': False,
            'list': [],
            'json': u'',
            'datetime': None,
            'date': None,
        }
        handler = self.create_handler(r'')
        self.assertEqual(handler.get_params(param_types, required=True),
                         expected_types)

    def test_missing_optional(self):
        """Missing expected params should be absent."""
        param_types = {
            'string': str,
            'unicode': unicode,
            'integer': int,
            'boolean': bool,
            'list': list,
            'json': 'json',
            'datetime': 'datetime',
            'date': 'date',
        }
        expected_types = {}
        handler = self.create_handler(r'')
        self.assertEqual(handler.get_params(param_types), expected_types)

    def test_bad_datetime(self):
        # No 'Z', so not UTC or not ISO 8601.
        handler = self.create_handler(r'datetime=2007-03-04T21:08:12')
        param_types = {'datetime': 'datetime'}
        with self.assertRaises(InvalidParamType):
            handler.get_params(param_types)

    def test_bad_date(self):
        handler = self.create_handler(r'date=3/4/07')
        param_types = {'date': 'date'}
        with self.assertRaises(InvalidParamType):
            handler.get_params(param_types)

    def test_bad_json(self):
        handler = self.create_handler(r'json_list=3,4')
        param_types = {'json_list': 'json'}
        with self.assertRaises(InvalidParamType):
            handler.get_params(param_types)
