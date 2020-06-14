"""Checkpoint: A grouping of tasks designed for high-level reporting of task
status. SQL-backed."""

from collections import OrderedDict
from google.appengine.api import memcache
from google.appengine.api import taskqueue
import json
import logging

from gae_models import DatastoreModel
from gae_models import SqlModel, SqlField as Field
import config
import model
import mysql_connection
import organization_tasks
import util


class Checkpoint(SqlModel):
    """A grouping of tasks designed for high-level reporting of task status.

    Parameters for defining checkpoint content are in program definitions.
    Checkpoints are created when their parent organization, project, or
    survey are created.

    There are no instances of this class, strictly speaking. The select()
    method returns a list of dictionaries, which is good enough.
    """
    table = 'checkpoint'

    py_table_definition = {
        'table_name': table,
        'fields': [
            #     name,            type,      length, unsigned, null,  default, on_update
            Field('uid',           'varchar',  50,    None,     False, None,    None),
            Field('short_uid',     'varchar',  50,    None,     False, None,    None),
            Field('label',         'varchar',  50,    None,     False, None,    None),
            Field('parent_id',     'varchar',  50,    None,     False, None,    None),
            Field('parent_kind',   'varchar',  50,    None,     False, None,    None),
            Field('name',          'text',     None,  None,     False, None,    None),
            Field('ordinal',       'tinyint',  3,     True,     False, None,    None),
            Field('status',        'varchar',  50,    None,     False, 'incomplete', None),
            Field('survey_id',     'varchar',  50,    None,     True,  SqlModel.sql_null, None),
            Field('project_cohort_id','varchar',50,   None,     True,  SqlModel.sql_null, None),
            Field('cohort_label',  'varchar',  100,   None,     True,  SqlModel.sql_null, None),
            Field('project_id',    'varchar',  50,    None,     True,  SqlModel.sql_null, None),
            Field('program_label', 'varchar',  50,    None,     True,  SqlModel.sql_null, None),
            Field('organization_id','varchar', 50,    None,     True,  SqlModel.sql_null, None),
            Field('task_ids',      'text',     None,  None,     True,  SqlModel.sql_null, None),
        ],
        'primary_key': ['uid'],
        'indices': [
            {
                'name': 'ordinal',
                'fields': ['ordinal'],
            },
        ],
        'engine': 'InnoDB',
        'charset': 'utf8',
    }

    @classmethod
    def create(klass, **kwargs):
        # Drop certain properties that may show up due do our JSON
        # defintions of checkpoints, like nested lists of tasks.
        # Need to pop all non-primitive values and any that aren't stored in
        # SQL.
        kwargs.pop('tasks', None)  # 2nd arg silences missing key
        kwargs.pop('body', None)
        kwargs['parent_kind'] = DatastoreModel.get_kind(kwargs['parent_id'])

        return super(klass, klass).create(**kwargs)

    @classmethod
    def property_types(klass):
        # Normally no properties are directly queryable or updateable. But
        # checkpoints need their status changed in normal operation.
        return {'status': str}

    @classmethod
    def get_status_from_tasks(klass, checkpoint):
        tasks = model.Task.get_by_id(json.loads(checkpoint.task_ids))

        all_complete = True
        all_assigned_complete = True
        for t in tasks:
            if t.status != 'complete':
                all_complete = False
                if t.to_client_dict()['non_admin_may_edit'] is True:
                    all_assigned_complete = False

        if all_complete:
            status = 'complete'
        elif all_assigned_complete:
            status = 'waiting'
        else:
            status = 'incomplete'

        return status

    @classmethod
    def get_checkpoint_config(klass, checkpoint):
        if checkpoint.parent_kind == 'Organization':
            tasklist = organization_tasks.tasklist_template
            return tasklist[checkpoint.ordinal - 1]
        elif checkpoint.parent_kind == 'Project':
            program = model.Program.get_config(checkpoint.program_label)
            tasklist = program['project_tasklist_template']
            return tasklist[checkpoint.ordinal - 1]
        elif checkpoint.parent_kind == 'Survey':
            program = model.Program.get_config(checkpoint.program_label)
            for survey in program['surveys']:
                for cp_template in survey['survey_tasklist_template']:
                    if cp_template['label'] == checkpoint.label:
                        return cp_template

    @classmethod
    def for_organizations_in_program(klass, program_label, limit=1000):
        query = """
            SELECT `org_ch`.*

            FROM `checkpoint` `prj_ch`

            JOIN `checkpoint` `org_ch`
              ON `prj_ch`.`organization_id` = `org_ch`.`parent_id`

            WHERE `prj_ch`.`parent_kind` = 'Project'
              AND `prj_ch`.`program_label` = %s

            GROUP BY `org_ch`.`uid`

            LIMIT {limit};
        """.format(limit=limit)
        with mysql_connection.connect() as sql:
            row_dicts = sql.select_query(query, (program_label,))
        return [klass.row_dict_to_obj(d) for d in row_dicts]

    @classmethod
    def for_tasklist(klass, project_cohort, fields=None):
        fields = '`{}`'.format('`, `'.join(fields)) if fields else '*'
        query = """
            SELECT {fields}
            FROM `checkpoint`
            WHERE (
                (`parent_kind` = 'Organization' AND `organization_id` = %s)
                OR
                (`parent_kind` = 'Project' AND `project_id` = %s)
                OR
                (`parent_kind` = 'Survey' AND `project_cohort_id` = %s)
            )
            ORDER BY FIELD(`parent_kind`,'Organization','Project','Survey'),
                     `ordinal`
        """.format(fields=fields)
        params = (
            project_cohort.organization_id,
            project_cohort.project_id,
            project_cohort.uid,
        )
        with mysql_connection.connect() as sql:
            row_dicts = sql.select_query(query, params)
        return [klass.row_dict_to_obj(d) for d in row_dicts]

    def clear_cached_properties(self, prop):
        """Related project cohorts need their cached properties cleared."""
        # This relationship is "down" so there may be many keys to clear so
        # don't try to actually refresh the cached values, just set up a
        # cache miss for their next read and they'll recover.
        pcs = list(model.ProjectCohort.get(
            n=float('inf'),
            **{prop: self.parent_id}
        ))  # force generator to store whole list in memory for re-use
        mem_keys = [util.cached_properties_key(pc.uid) for pc in pcs]
        memcache.delete_multi(mem_keys)
        return pcs

    def after_put(self, init_kwargs):
        """Reset memcache for cached properties of related objects

        This is a bit tricky, because org or project checkpoints may be cached
        on many different project cohorts, while survey checkpoints will only
        ever be cached on one.
        """

        # First clear cached properties on whatever project cohorts are related.
        # Collect them for later.
        pcs = []
        if self.parent_kind == 'Organization':
            pcs += self.clear_cached_properties('organization_id')
        elif self.parent_kind == 'Project':
            pcs += self.clear_cached_properties('project_id')
        elif self.parent_kind == 'Survey':
            # This relationship is "up" so there's only one thing to update.
            # Take the time to refresh the cache value instead of just clearing.
            pc = model.ProjectCohort.get_by_id(self.project_cohort_id)
            if pc:
                pc.update_cached_properties()
                pcs.append(pc)

        # Then clear cached queries related to these project cohorts and queue
        # a task to re-cached them.
        to_delete = []
        if self.organization_id:
            to_delete.append(util.cached_query_key(
                'SuperDashboard', organization_id=self.organization_id
            ))
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

    def to_client_dict(self, include_conf=True):
        """Add properties from checkpoint definitions that aren't stored."""
        d = super(Checkpoint, self).to_client_dict()
        if include_conf:
            config = self.get_checkpoint_config(self)
            props = ('body',)
            d.update({p: config.get(p, None) for p in props})

        # Keep the dictionary sorted
        return OrderedDict((k, d[k]) for k in sorted(d.keys()))
