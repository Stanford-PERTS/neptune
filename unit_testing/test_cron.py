"""Test Project entities."""

import logging
import unittest

from slow_query import seconds_to_sql_time


class TestCron(unittest.TestCase):
    def test_sql_time(self):
        cases = {
            0: '00:00:00.000000',
            0.00000099: '00:00:00.000001',
            0.1: '00:00:00.100000',
            1.1: '00:00:01.100000',
            61: '00:01:01.000000',
            3661: '01:01:01.000000',
            24 * 60 * 60 - 0.000001: '23:59:59.999999',
        }

        for case, expected in cases.items():
            self.assertEqual(seconds_to_sql_time(case), expected)

        with self.assertRaises(Exception):
            seconds_to_sql_time(24 * 60 * 60)
