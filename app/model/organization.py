"""Organization: a University, College, School, or other institution."""

from collections import OrderedDict
from google.appengine.api import memcache, taskqueue
from google.appengine.ext import ndb
import json
import logging
import random
import string

import organization_tasks

from gae_models import DatastoreModel
import config
import model
import util


class Organization(DatastoreModel):
    name = ndb.StringProperty()
    # Org admin and owner, principal contact, gets the task reminder for this
    # org. By default, is the creator of the org.
    liaison_id = ndb.StringProperty()
    website_url = ndb.StringProperty()
    mailing_address = ndb.StringProperty()
    state = ndb.StringProperty()  # abbreviation, e.g. 'WA'
    country = ndb.StringProperty()
    postal_code = ndb.StringProperty()
    phone_number = ndb.StringProperty()
    #   PERTS Organization ID. For now just a serialization of all the ids we
    # record.
    #   We plan on establishing specific rules about what existing identifier to
    # use depending on the class of organization. For instance, for post-
    # secondary insitutions, we may decide that the poid should be the UNITID,
    # which is the primary identifier for the D of Ed's college scorecard.
    # https://collegescorecard.ed.gov/assets/FullDataDocumentation.pdf
    poid_json = ndb.ComputedProperty(lambda self: json.dumps(OrderedDict([
        ('nces_district_id', self.nces_district_id),
        ('nces_school_id', self.nces_school_id),
        ('ipeds_id', self.ipeds_id),
        ('ope_id', self.ope_id),
    ])))
    nces_district_id = ndb.StringProperty()
    nces_school_id = ndb.StringProperty()
    ipeds_id = ndb.StringProperty()
    ope_id = ndb.StringProperty()

    # |    value     |                    description                     |
    # |--------------|----------------------------------------------------|
    # | 'unapproved' | org was created, super admins have taken no action |
    # | 'approved'   | org found in public database (e.g. NCES), given a  |
    # |              | POID, accepted as legitimate by a super admin      |
    # | 'rejected'   | super admin decided org is not legitimate or is a  |
    # |              | duplicate.                                         |
    status = ndb.StringProperty(default='unapproved')
    google_maps_place_id = ndb.StringProperty()
    # Admin notes regarding the organization. Useful for recording reason for
    # rejection.
    notes = ndb.TextProperty()

    # These may be queried or gotten by id as resources by anyone, i.e. any
    # user may GET /api/organizations/names or GET /api/organizations/:id/name
    public_properties = ['name', 'google_maps_place_id', 'poid',
                         'nces_district_id', 'ipeds_id', 'ope_id']

    json_props = ['poid_json']

    # After creation, this will have a tasklist object, which in turn will
    # have checkpoints and tasks that need saving to their respective
    # databases.
    tasklist = None

    @property
    def poid(self):
        return json.loads(self.poid_json) if self.poid_json else None

    # N.B. there is no setter for poid b/c it's a computed property.

    @classmethod
    def create(klass, tasklist_template=None, **kwargs):
        org = super(klass, klass).create(**kwargs)

        tt = tasklist_template or organization_tasks.tasklist_template
        org.tasklist = model.Tasklist.create(tt, org)

        return org

    @classmethod
    def example_params(klass):
        name = ''.join(random.choice(string.ascii_uppercase)
                       for c in range(3))
        return {
            'name': name + " College",
            'website_url': 'www.{}.edu'.format(name),
            'mailing_address': '555 {} Ave.\nSeattle, WA 98120'.format(name),
            'state': 'WA',
            'country': 'USA',
            'phone_number': '+1 (555) 555-5555',
        }

    @classmethod
    def all_of_property_key(klass, prop):
        return 'all_organization.' + prop

    @classmethod
    def get_all_of_property(klass, prop):
        mem_key = klass.all_of_property_key(prop)
        results = memcache.get(mem_key)

        # In the case of json properties, the name of the property in the db
        # is different from the name we want to show in the API.
        db_prop = prop
        json_prop = prop + '_json'
        if json_prop in klass.json_props:
            db_prop = json_prop

        if results is None:
            # Db name in the projection, external name in the results.
            orgs = Organization.get(n=float('inf'), projection=[db_prop])
            results = [{'uid': o.uid, prop: getattr(o, prop)} for o in orgs]
            memcache.set(mem_key, results)

        return results

    def after_put(self, *args, **kwargs):
        # On changes to any org, clear the cached list of names.
        for p in self.public_properties:
            memcache.delete(self.all_of_property_key(p))


        # Reset memcache for cached properties of related objects and queries.
        # This relationship is "down" so there may be many keys to clear so
        # don't try to actually refresh the cached values, just set up a cache
        # miss for their next read and they'll recover.
        to_delete = []

        # Projects
        p_keys = model.Project.get(n=float('inf'), organization_id=self.uid,
                                   keys_only=True)
        # These keys are for individual project entities
        to_delete += [util.cached_properties_key(k.id()) for k in p_keys]

        # ProjectCohorts
        pcs = list(
            model.ProjectCohort.get(n=float('inf'), organization_id=self.uid)
        )  # force generator to store whole list in memory for re-use
        # These keys are for individual project cohort entities
        to_delete += [util.cached_properties_key(pc.uid) for pc in pcs]
        # These are for caches of whole query results.
        to_delete += [
            util.cached_query_key('SuperDashboard', organization_id=self.uid)
        ]
        for pc in pcs:
            kwargs = {'program_label': pc.program_label,
                      'cohort_label': pc.cohort_label}
            to_delete.append(util.cached_query_key('SuperDashboard', **kwargs))
            taskqueue.add(
                url='/task/cache_dashboard',
                headers={'Content-Type': 'application/json; charset=utf-8'},
                payload=json.dumps(kwargs),
                countdown=config.task_consistency_countdown,
            )

        memcache.delete_multi(to_delete)

        # Save tasklist.
        if self.tasklist:
            # Tasklist might not always be present; it is if created via
            # create(), but not if fetched from the datastore.
            self.tasklist.put()

    def tasks(self):
        """Get all the tasks for this organization.
        Returns tasks in order of creation to mimic templates.
        Requires a user_type for permissions
        """
        return model.Task.get(ancestor=self, n=100, order="ordinal")

    def tasklist_name(self):
        return 'Application for {org} to join PERTS'.format(org=self.name)
