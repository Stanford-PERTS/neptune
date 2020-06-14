"""Provide example code for writing unit tests."""

import inspect
import unittest

from unit_test_helper import ConsistencyTestCase
from model import User
import model


class DatastoreModelTest(ConsistencyTestCase):
    """Test basic functions of our data model, i.e. the DatastoreModel class."""

    # This test case focuses on the functionality of our query helpers,
    # including inconsistent queries, and don't want to bother with populating
    # the datastore and then artificially enforcing consistency. Tests that
    # integrate inconsistency will go elsewhere.
    consistency_probability = 1

    def get_all_models(self):
        # Scan the model for all class definitions / kinds.
        all_models = []
        for class_name in dir(model):
            c = getattr(model, class_name)
            if inspect.isclass(c) and issubclass(c, model.DatastoreModel):
                all_models.append(c)
        return all_models

    def test_create_simple(self):
        """Create a DatastoreModel entity in the datastore."""
        m = model.DatastoreModel.create()
        m.put()
        return m

    def test_get_by_id(self):
        m = self.test_create_simple()

        fetched_m = model.DatastoreModel.get_by_id(m.uid)
        # Special __eq__ method on DatastoreModel should make this work, even
        # though normal python behavior is to compare objects by memory
        # location.
        self.assertEqual(m, fetched_m)

    def test_get_by_short_id(self):
        m = self.test_create_simple()

        fetched_m = model.DatastoreModel.get_by_id(m.short_uid)
        # Special __eq__ method on DatastoreModel should make this work, even
        # though normal python behavior is to compare objects by memory
        # location.
        self.assertEqual(m, fetched_m)

    @unittest.skip("Need to reconsider where to put this code.")
    def test_create_all(self):
        # Some entities are created as parents of others. These parents need
        # to exist for them to be created.
        parent_user = User.create(email='parent@example.com')

        # Specify when a kind requires arguments to be created.
        required_kwargs = {
            'User': {
                'email': 'test@example.com',
            },
            'Email': {
                'to_address': 'test@example.com',
            },
            'AuthToken': {
                'user_id': parent_user.uid,
            },
        }

        # Instantiate each kind, providing required arguments.
        entities = []
        for klass in self.get_all_models():
            kwargs = required_kwargs.get(klass.__name__, {})
            e = klass.create(**kwargs)
            entities.append(e)

        # So we can reuse this code in later tests.
        return entities

    @unittest.skip("Need to reconsider where to put this code.")
    def test_get_all(self):
        """Vanilla fetch of a kind."""
        for e in self.test_create_all():
            e.put()

        for klass in self.get_all_models():
            results = klass.get()
            self.assertEqual(len(results), 1)
            self.assertIsInstance(results[0], klass)

    def test_negative_filter(self):
        """Can postpend property with ! to create "not-equals" filter."""
        u1 = User.create(email='foo@bar')
        u1.put()
        u2 = User.create(email='baz@qux')
        u2.put()
        kwargs = {'email!': u1.email}
        results = list(User.get(n=float('inf'), **kwargs))
        self.assertEqual(len(results), 1)
        self.assertEqual(u2.uid, results[0].uid)
