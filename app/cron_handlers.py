from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
import json
import logging
import os
import traceback

import cloudstorage as gcs

from big_query_api import BigQueryApi
from gae_handlers import (BackupSqlToGcsHandler, BackupToGcsHandler,
                          BaseHandler, CronHandler, CleanGcsBucket, Route,
                          rserve_jwt)
from model import (Checkpoint, DatastoreModel, Email, ErrorChecker, Program,
                   Project, ProjectCohort, SecretValue, Task)
import auto_prompt
import mandrill
import mysql_connection
import slow_query
import util


class SendPendingEmail(CronHandler):
    """See model.Email for details."""
    def get(self):
        emails = Email.send_pending_email()
        self.write(emails)


class CheckForErrors(CronHandler):
    """Send emails to devs about errors in production."""
    def get(self):
        """Check for new errors - email on error.
        Must be called with internal_api for full permissions.
        See named_model@Index for full description.
        """

        checker = ErrorChecker.get_or_insert('the error checker')
        result = checker.check()
        checker.put()
        self.write(result)


class CacheDashboards(CronHandler):
    """Periodically refresh dashboard cache to fight stale data.

    See #1029.
    """
    def get(self):
        # Refresh the newest two cohorts of each program.
        tasks = []
        for program_config in Program.get_all_configs():
            cohorts = sorted(program_config['cohorts'].keys())
            for cohort_label in cohorts[-2:]:
                task = taskqueue.add(
                    url='/task/cache_dashboard',
                    headers={'Content-Type': 'application/json'},
                    payload=json.dumps({
                        'program_label': program_config['label'],
                        'cohort_label': cohort_label,
                    }),
                )
                tasks.append(task)
        self.write({
            'tasks': [
                {'name': t.name, 'payload': json.loads(t.payload)}
                for t in tasks
            ]
        })


class RServeCGReports(CronHandler):
    def get(self):
        program_label = 'cg17'
        cohort = Program.get_current_cohort(program_label)

        url = '{protocol}://{domain}/api/scripts/cg'.format(
            protocol='http' if util.is_localhost() else 'https',
            domain=('localhost:9080' if util.is_localhost()
                    else os.environ['RSERVE_DOMAIN']),
        )

        # Look up all the valid project cohorts
        pc_ids = [pc_key.id() for pc_key in ProjectCohort.get(
            program_label=program_label,
            cohort_label=cohort['label'],
            status='open',
            keys_only=True,
            n=float('inf'),
        )]

        # To match up the right report tasks, we'll need tasks and checkpoints.
        checkpoints = [c for c in Checkpoint.get(
            label='cg17_survey__monitor_1',
            cohort_label=cohort['label'],
            n=float('inf'),
        ) if c.project_cohort_id in pc_ids]
        checkpoint_ids = [c.uid for c in checkpoints]
        tasks = [t for t in Task.get(
            label='cg17_survey__report_1',
            n=float('inf'),
        ) if t.checkpoint_id in checkpoint_ids]

        # Alternate way to get tasks, via surveys, which may or may not be
        # more efficient. My current assumption is, for large result sets,
        # SQL-back checkpoints are faster.
        #
        # survey_keys = [s.key for s in Survey.get(
        #     program_label=program_label,
        #     cohort_label=cohort['label'],
        #     n=float('inf'),
        # ) if s.project_cohort_id in pc_ids]
        # tasks = [t for t in Task.get(
        #     label='cg17_survey__report_1',
        #     n=float('inf'),
        # ) if t.key.parent() in survey_keys]

        payload = {
            'reporting_units': [
                self.build_reporting_unit(uid, checkpoints, tasks)
                for uid in pc_ids
            ],
        }

        secrets = ('neptune_sql_credentials', 'big_pipe_credentials',
                   'qualtrics_credentials')
        for s in secrets:
            payload[s] = SecretValue.get(s, None)

        result = urlfetch.fetch(
            url=url,
            payload=json.dumps(payload),
            method=urlfetch.POST,
            headers={
                'Authorization': 'Bearer ' + rserve_jwt(),
                'Content-Type': 'application/json',
            }
        )

        if not result or result.status_code >= 300:
            logging.error("Non-successful response from RServe: {} {}"
                          .format(result.status_code, result.content))
        else:
            logging.info("response status: {}".format(result.status_code))
            try:
                json.loads(result.content)
                # ok, it's valid
                # logging.info(util.truncate_json(result.content))
                logging.info(result.content)
            except:
                # just log as text
                logging.info(result.content)

    def build_reporting_unit(self, pc_id, checkpoints, tasks):
        url_base = '{protocol}://{domain}'.format(
            protocol='http' if util.is_localhost() else 'https',
            domain=('localhost:8888' if util.is_localhost()
                    else os.environ['HOSTING_DOMAIN']),
        )

        # Find the right task for this project cohort
        c = next(c for c in checkpoints if c.project_cohort_id == pc_id)
        t = next(t for t in tasks if t.checkpoint_id == c.uid)

        # Assemble the URLs that RServe will need to post back to.
        dataset_url = '{base}/api/datasets?parent_id={parent_id}'.format(
            base=url_base,
            parent_id=pc_id,
        )
        task_attachment_url = '{base}/api/tasks/{task_id}/attachment'.format(
            base=url_base,
            task_id=t.uid,
        )
        return {
            'project_cohort_id': pc_id,
            'post_url': dataset_url,
            'post_task_attachment_url': task_attachment_url,
        }


class RServeDaily(CronHandler):
    def get(self):
        pass


class ExportSlowQueryLog(CronHandler):
    def get(self):
        log_bucket = 'neptuneplatform-logs'
        log_dataset = 'neptune_logs'
        log_table = 'slow_log'

        with BigQueryApi() as bq:
            bq.ensure_dataset(log_dataset)
            bq.ensure_table(log_dataset, log_table, schema=slow_query.schema)

            num_fragments = 0
            num_entries = 0
            failed_insertions = 0
            for lines, file_name in slow_query.json_batch_gen(log_bucket):
                entries = slow_query.json_lines_to_entries(lines)
                slow_query_rows = [
                    slow_query.to_slow_schema(e) for e in entries.values()
                ]

                status, response_body = bq.insert_data(
                    log_dataset,
                    log_table,
                    slow_query_rows,
                    insert_id_field='timestamp',
                )

                if status == 200:
                    gcs.delete(file_name)
                    num_fragments += 1
                    num_entries += len(entries)
                else:
                    failed_insertions += 1
                    logging.warning("Failed to insert: {}".format(file_name))

        self.write({
            "message": "log fragments exported",
            "num_fragments": num_fragments,
            "num_entries": num_entries,
            "failed_insertions": failed_insertions,
        })


class AutoPromptEmailsHandler(CronHandler):
    def get(self):
        neptune_templates = mandrill.call(
            'templates/list.json',
            {'label': 'neptune'}
        )
        tasks = []
        tasks += auto_prompt.queue_org_welcome(neptune_templates)
        tasks += auto_prompt.queue_org_welcome_back(neptune_templates)
        tasks += auto_prompt.queue_checklist_nudge(neptune_templates)

        self.write({
            'tasks': [t.url for t in tasks]
        })


cron_routes = [
    Route('/cron/backup', BackupToGcsHandler),
    Route('/cron/cache_dashboards', CacheDashboards),
    Route('/cron/check_for_errors', CheckForErrors),
    Route('/cron/clean_gcs_bucket/<bucket>', CleanGcsBucket),
    Route('/cron/export_slow_query_log', ExportSlowQueryLog),
    Route('/cron/rserve/cg_reports', RServeCGReports),
    Route('/cron/rserve/daily', RServeDaily),
    Route('/cron/send_pending_email', SendPendingEmail),
    Route('/cron/sql_backup/<instance>/<db>/<bucket>', BackupSqlToGcsHandler),
    Route('/cron/auto_prompt_emails', AutoPromptEmailsHandler),
]
