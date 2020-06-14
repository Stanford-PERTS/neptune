"""Test mapreduce mappers."""

from google.appengine.ext import ndb
import json
import unittest

from unit_test_helper import ConsistencyTestCase
from map_handlers import fix_open_responses
from model import ProjectCohort


class MapreduceTest(ConsistencyTestCase):
    # I don't know exactly how mapreduce queries for all entities of a kind. May
    # need to set this to 1 to avoid annoyance.
    consistency_probability = 0

    def test_fix_open_responses(self):
        """Non-triton pcs shouldn't have the open response param."""
        non_triton_empty = ProjectCohort.create(
            program_label='demo-program',
        )
        non_triton_only = ProjectCohort.create(
            program_label='demo-program',
            survey_params_json=json.dumps({
                'show_open_response_questions': 'true',
            })
        )
        non_triton_extra = ProjectCohort.create(
            program_label='demo-program',
            survey_params_json=json.dumps({
                'foo': 'bar',
                'show_open_response_questions': 'true',
            }),
        )
        triton = ProjectCohort.create(
            program_label='triton',
            survey_params_json=json.dumps({
                'learning_conditions': "feedback-for-growth",
                'show_open_response_questions': 'true',
            }),
        )

        def get_mapped(pc):
            operation = next(fix_open_responses(pc), None)
            if operation:
                return operation.entity

        # Empty value unchanged
        mapped_non_triton_empty = get_mapped(non_triton_empty)
        self.assertEqual(mapped_non_triton_empty.survey_params, {})

        # Key removed.
        mapped_non_triton_only = get_mapped(non_triton_only)
        self.assertNotIn('show_open_response_questions',
                         mapped_non_triton_only.survey_params)

        # Key removed, other data preserved.
        mapped_non_triton_extra = get_mapped(non_triton_extra)
        self.assertNotIn('show_open_response_questions',
                         mapped_non_triton_extra.survey_params)
        self.assertIn('foo', mapped_non_triton_extra.survey_params)

        # Triton pc untouched.
        mapped_triton = get_mapped(triton)
        self.assertIsNone(mapped_triton)
