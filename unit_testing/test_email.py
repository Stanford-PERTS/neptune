"""Unit tests related to the Email model"""

import unittest

from model import Email
from unit_test_helper import ConsistencyTestCase


class TestEmail(ConsistencyTestCase):
    """Test emailing functionality for Email model (email.py)"""

    consistency_probability = 1

    def test_spam_with_single_email(self):
        # Create a single email
        to_address = 'unit_testing@example.com'
        email = Email.create(to_address=to_address)
        email.put()
        Email.send_pending_email()

        fetched_email = Email.query(Email.to_address == to_address).get()
        self.assertIsInstance(fetched_email, Email)
        # Test if email was attempted to send
        self.assertEqual(fetched_email.was_attempted, True)
        # ...and has been sent
        self.assertEqual(fetched_email.was_sent, True)

    @unittest.skip("Spam protection is off pending digest development.")
    def test_spam_with_two_emails_to_same_address(self):
        # Create a single email
        to_address = 'unit_testing@example.com'
        email = Email.create(to_address=to_address)
        email.put()
        second_email = Email.create(to_address=to_address)
        second_email.put()
        Email.send_pending_email()

        fetched_email = Email.query().fetch()
        self.assertEqual(len(fetched_email), 2)
        self.assertIsInstance(fetched_email[0], Email)
        self.assertIsInstance(fetched_email[1], Email)
        # Test if email was attempted to send
        self.assertEqual(fetched_email[0].was_attempted, True)
        self.assertEqual(fetched_email[1].was_attempted, True)
        # ...and has been sent
        self.assertEqual(fetched_email[0].was_sent, True)
        self.assertEqual(fetched_email[1].was_sent, False)

    def test_spam_with_two_emails_to_different_addresses(self):
        # Create a single email
        to_address = 'unit_testing@example.com'
        second_address = 'unit_testing2@example.com'
        email = Email.create(to_address=to_address)
        email.put()
        second_email = Email.create(to_address=second_address)
        second_email.put()
        Email.send_pending_email()

        fetched_email = Email.query().fetch()
        self.assertEqual(len(fetched_email), 2)
        self.assertIsInstance(fetched_email[0], Email)
        self.assertIsInstance(fetched_email[1], Email)
        # Test if email was attempted to send
        self.assertEqual(fetched_email[0].was_attempted, True)
        self.assertEqual(fetched_email[1].was_attempted, True)
        # ...and has been sent
        self.assertEqual(fetched_email[0].was_sent, True)
        self.assertEqual(fetched_email[1].was_sent, True)

    @unittest.skip("Spam protection is off pending digest development.")
    def test_spam_with_recent_email_to_same_addresses(self):
        # Create a sent and not sent email to same address
        # Note: Cannot be to a '@mindsetkit.org' address
        to_address = 'unit_testing@example.com'
        email_subject = 'Email subject'
        sent_email = Email.create(
            to_address=to_address,
            was_attempted=True,
            was_sent=True)
        sent_email.put()
        email = Email.create(
            to_address=to_address,
            subject=email_subject)
        email.put()
        Email.send_pending_email()

        fetched_email = Email.query(Email.subject == email_subject).get()
        self.assertIsInstance(fetched_email, Email)
        # Test if email was attempted to send
        self.assertEqual(fetched_email.was_attempted, True)
        # ...and has been sent
        self.assertEqual(fetched_email.was_sent, False)

    def test_spam_with_recent_email_to_different_addresses(self):
        # Create a sent and not sent email to different addresses
        # Note: Cannot be to a '@mindsetkit.org' address
        to_address = 'first@example.com'
        second_address = 'second@example.com'
        email_subject = 'Email subject'
        sent_email = Email.create(
            to_address=to_address,
            was_attempted=True,
            was_sent=True,)
        sent_email.put()
        email = Email.create(
            to_address=second_address,
            subject=email_subject)
        email.put()
        Email.send_pending_email()

        fetched_email = Email.query(Email.subject == email_subject).get()
        self.assertIsInstance(fetched_email, Email)
        # Test if email was attempted to send
        self.assertEqual(fetched_email.was_attempted, True)
        # ...and has been sent
        self.assertEqual(fetched_email.was_sent, True)
