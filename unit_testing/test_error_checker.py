from model import ErrorChecker
from unit_test_helper import PertsTestCase
import logging


class TestErrorChecker(PertsTestCase):
    def set_up(self):
        self.ErrorChecker = ErrorChecker()

    def test_redact_noop(self):
        """When no rule applies, or when not a string, input matches output."""
        cases = (
            '/api/foo',
            u'abc',
            '{]{[ %s \\n',
            None,
            False,
            object(),
            5,
        )

        for r in cases:
            self.assertEqual(
                self.ErrorChecker.redact_error_text(r),
                r,
            )

    def test_redact_participant_query(self):
        cases = (
            u'/api/participants?name=secret',
            u'/api/participants?name=secret&name=secret',
            u'/api/participants?foo=bar&name=secret',
            u'/api/participants?foo=bar&name=secret&baz=qux',
            u'example.com/api/participants?foo=bar&name=secret&baz=qux',
        )

        for r in cases:
            redacted = self.ErrorChecker.redact_error_text(r)
            logging.info(redacted)
            self.assertNotIn('secret', redacted)

    def test_redact_roster_query(self):
        cases = (
            u'/api/codes/deer-salt/participants/secret',
            u'/api/codes/deer-salt/participants/secret?foo=bar',
            u'example.com/api/codes/deer-salt/participants/secret?foo=bar',
        )

        for r in cases:
            redacted = self.ErrorChecker.redact_error_text(r)
            logging.info(redacted)
            self.assertNotIn('secret', redacted)

    def test_redact_names_in_body(self):
        """Names also redacted in a multi-line email body, both patterns."""
        body = '''
            ERROR: https://copilot/api/participants?name=secret&name=secret
            ERROR: https://neptune/api/codes/qux/participants/secret?foo=bar
        '''

        redacted = self.ErrorChecker.redact_error_text(body)
        logging.info(redacted)
        self.assertNotIn('secret', redacted)
