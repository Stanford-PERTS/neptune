# -*- coding: utf-8 -*-
import inspect
import json
import logging
import webapp2
import webtest

from api_handlers import api_routes
from model import Checkpoint, Organization, Task, User
from unit_test_helper import ConsistencyTestCase, login_headers
import config
import organization_tasks
import model
import mysql_connection
import util


class TestApiPermissions(ConsistencyTestCase):
    """Test what humans can and can't do over HTTP."""

    # We're not interested in how accurately we can retrieve fresh data, but
    # rather whether permission filters are in effect.
    consistency_probability = 1

    cookie_name = config.session_cookie_name
    cookie_key = config.default_session_cookie_secret_key

    def set_up(self):
        # Let ConsistencyTestCase set up the datastore testing stub.
        super(TestApiPermissions, self).set_up()

        with mysql_connection.connect() as sql:
            sql.reset({'checkpoint': Checkpoint.get_table_definition()})

        application = webapp2.WSGIApplication(
            api_routes,
            config={
                'webapp2_extras.sessions': {
                    'secret_key': self.cookie_key
                }
            },
            debug=True
        )
        self.testapp = webtest.TestApp(application)

        # Tone down the intense number of hashing rounds for passwords so our
        # unit tests are fast.
        User.password_hashing_context.update(
            sha512_crypt__default_rounds=1000,
            sha256_crypt__default_rounds=1000,
        )

    def get_all_models(self):
        # Scan the model for all class definitions / kinds.
        all_models = []
        for class_name in dir(model):
            c = getattr(model, class_name)
            if inspect.isclass(c) and issubclass(c, model.DatastoreModel):
                all_models.append(c)
        return all_models

    def create_entities_to_get(self):
        """To test GETting, populate with some stuff."""
        org1 = Organization.create(name='org1')
        org2 = Organization.create(name='org2')
        org3 = Organization.create(name='org3')
        org1.put()
        org2.put()
        org3.put()

        super_admin = User.create(email='super@example.com',
                                  user_type='super_admin',
                                  owned_organizations=[org1.uid])
        program_admin = User.create(email='program@example.com',
                                    user_type='program_admin')
        user = User.create(email='org@example.com',
                                user_type='user',
                                owned_organizations=[org2.uid],
                                assc_organizations=[org3.uid])
        super_admin.put()
        program_admin.put()
        user.put()

        return (super_admin, program_admin, user)

    def test_get_nonexistent_resource(self):
        user = User.create(email='test@example.com')
        user.put()
        for klass in self.get_all_models():
            resource_name = util.camel_to_separated(klass.__name__)
            response = self.testapp.get('/api/{}/foo'.format(resource_name),
                                        headers=login_headers(user.uid),
                                        status=404)

    ### Organization ###

    def test_get_all_orgs(self):
        # Also creates 3 orgs, where user owns one and is assc with one.
        super_admin, program_admin, user = self.create_entities_to_get()

        # Super sees all
        response = self.testapp.get('/api/organizations',
                                    headers=login_headers(super_admin.uid))
        self.assertEqual(len(json.loads(response.body)), 3)

        # Org and Program admins are forbidden.
        response = self.testapp.get('/api/organizations',
                                    headers=login_headers(user.uid),
                                    status=403)
        response = self.testapp.get('/api/organizations',
                                    headers=login_headers(program_admin.uid),
                                    status=403)

    def test_get_related_orgs(self):
        # Also creates 3 orgs, where user owns one and is assc with one.
        super_admin, program_admin, user = self.create_entities_to_get()

        owned_id = user.owned_organizations[0]
        assc_id = user.assc_organizations[0]
        response = self.testapp.get(
            '/api/users/{}/organizations'.format(user.uid),
            headers=login_headers(user.uid)
        )
        orgs = json.loads(response.body)
        self.assertIs(type(orgs), list)
        org_ids = {o['uid'] for o in orgs}
        self.assertEquals({owned_id, assc_id}, org_ids)

    def test_related_org_permissions(self):
        """Who besides the specified user can get related orgs?"""
        # Also creates 3 orgs, where user owns one and is assc with one.
        super_admin, program_admin, user = self.create_entities_to_get()

        # Besides the user specified in the URL, super admins can reach the
        # resource, but others can't.
        response = self.testapp.get(
            '/api/users/{}/organizations'.format(user.uid),
            headers=login_headers(super_admin.uid),
            status=200
        )
        response = self.testapp.get(
            '/api/users/{}/organizations'.format(user.uid),
            headers=login_headers(program_admin.uid),
            status=403
        )

    def test_get_owned_org(self):
        """You can get an org you own."""
        # Also creates 3 orgs, where user owns one and is assc with one.
        super_admin, program_admin, user = self.create_entities_to_get()

        owned_id = user.owned_organizations[0]
        response = self.testapp.get('/api/organizations/' + owned_id,
                                    headers=login_headers(user.uid))
        org = json.loads(response.body)
        self.assertIs(type(org), dict)
        self.assertEquals(org['uid'], owned_id)

    def test_get_assc_org(self):
        """You CAN get an org you're merely associated with."""
        # Also creates 3 orgs, where user owns one and is assc with one.
        super_admin, program_admin, user = self.create_entities_to_get()

        assc_id = user.assc_organizations[0]
        response = self.testapp.get('/api/organizations/' + assc_id,
                                    headers=login_headers(user.uid))

    def test_get_assc_org_children(self):
        """You can't use org-based endpoints.

        Includes: data tables, users, projects, checkpoints, tasks.
        """
        # Also creates 3 orgs, where user owns one and is assc with one.
        super_admin, program_admin, user = self.create_entities_to_get()

        urls = [
            '/api/organizations/{}/users',
            '/api/organizations/{}/projects',
            '/api/organizations/{}/checkpoints',
            '/api/organizations/{}/tasks',
        ]
        assc_id = user.assc_organizations[0]

        for url in urls:
            response = self.testapp.get(url.format(assc_id),
                                        headers=login_headers(user.uid),
                                        status=403)

    def test_get_unrelated_org(self):
        """You can't get an org you're enitrely unrelated to."""
        # Also creates 3 orgs, where user owns one and is assc with one.
        super_admin, program_admin, user = self.create_entities_to_get()

        unrelated_id = super_admin.owned_organizations[0]
        response = self.testapp.get('/api/organizations/' + unrelated_id,
                                    headers=login_headers(user.uid),
                                    status=403)

    def test_post_with_ownership(self):
        """POSTing an ownable entity should make you the owner."""
        user = User.create(email='org@example.com', user_type='user')
        user.put()

        response = self.testapp.post_json(
            '/api/organizations',
            {'name': "Foo Org", 'liaison_id': user.uid},
            headers=login_headers(user.uid),
        )

        new_org = json.loads(response.body)
        refreshed_user = user.key.get()
        self.assertEqual(refreshed_user.owned_organizations, [new_org['uid']])

    def test_update_task(self):
        """Org admins can't change some tasks."""
        org = Organization.create(name='org')
        org.put()
        user = User.create(email='org@example.com', user_type='user',
                                owned_organizations=[org.uid])
        user.put()

        orig_config = organization_tasks.tasklist_template
        organization_tasks.tasklist_template = [
            {
                'tasks': [
                    {
                        'label': 'task_foo',
                        'non_admin_may_edit': False,
                    }
                ]
            }
        ]

        task = Task.create('task_foo', 1, 'checkpoint_foo', parent=org)
        task.put()

        # Org admin shouldn't be able to mark the task as complete, even though
        # they own the task.
        task.status = 'complete'
        response = self.testapp.put_json('/api/tasks/{}'.format(task.uid),
                                         task.to_client_dict(),
                                         headers=login_headers(user.uid),
                                         status=403)

        organization_tasks.tasklist_template = orig_config

    def test_update_checkpoint(self):
        """Can't change a checkpoint to an invalid status, based on tasks."""
        # One checkpoint with one tasks.
        orig_config = organization_tasks.tasklist_template
        tasklist_tmpl = [
            {
                'name': "Checkpoint Foo",
                'label': 'checkpoint label foo',
                'tasks': [
                    {'label': 'foo', 'non_admin_may_edit': True},
                    {'label': 'bar', 'non_admin_may_edit': True}
                ]
            },
        ]
        organization_tasks.tasklist_template = tasklist_tmpl

        user = User.create(email='org@example.com', user_type='user')
        org = Organization.create(name='org', tasklist_template=tasklist_tmpl,
                                  liaison_id=user.uid)
        user.owned_organizations = [org.uid]
        org.put()
        user.put()

        # Make one task complete, the other stays incomplete by default.
        org.tasklist.tasks[0].status = 'complete'
        org.tasklist.tasks[0].put()

        # This is an unsaved, in-memory dict, and thus doesn't contain defaults
        # set in the table definition.
        ckpt = org.tasklist.checkpoints[0]
        # Fetch the checkpoint by id to pick up those defaults.
        ckpt = Checkpoint.get_by_id(ckpt.uid)

        # The derived checkpoint status is 'incomplete'. Setting it this way
        # should work.
        response = self.testapp.put_json(
            '/api/checkpoints/{}'.format(ckpt.uid),
            ckpt.to_client_dict(),
            headers=login_headers(user.uid),
        )

        # Shouldn't be able to set the checkpoint to any other value.
        ckpt.status = 'foo'
        response = self.testapp.put_json(
            '/api/checkpoints/{}'.format(ckpt.uid),
            ckpt.to_client_dict(),
            headers=login_headers(user.uid),
            status=500,
        )

        organization_tasks.tasklist_template = orig_config
