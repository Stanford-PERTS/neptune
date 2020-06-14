"""Provide example code for writing unit tests."""

from google.appengine.api import memcache

from unit_test_helper import ConsistencyTestCase
from model import Organization


class MemcacheTest(ConsistencyTestCase):
    """Test uses of memcache to speed up queries."""

    consistency_probability = 0

    def test_all_organization_names_caches(self):
        """After the first query, all names should be cached."""
        name_key = Organization.all_of_property_key('name')
        self.assertIsNone(memcache.get(name_key))
        orgNames = Organization.get_all_of_property('name')
        self.assertEqual(orgNames, memcache.get(name_key))

    def test_all_organization_names_recache(self):
        """After writing an org, the cache should clear."""
        name_key = Organization.all_of_property_key('name')
        self.test_all_organization_names_caches()
        Organization.create().put()
        self.assertIsNone(memcache.get(name_key))
