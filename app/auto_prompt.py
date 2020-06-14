from google.appengine.api import taskqueue
import datetime
import logging

from model import (Program, Project, ProjectCohort)
import util


ORG_WELCOME_SUFFIX = 'org-welcome'
ORG_WELCOME_BACK_SUFFIX = 'org-welcome-back'
CHECKLIST_NUDGE_SUFFIX = 'checklist-nudge'


def get_slug(program_label, suffix):
    return '{}-{}'.format(program_label, suffix)


def programs_with_template(templates, suffix):
    matching_programs = []
    slugs = [t['slug'] for t in templates]
    for program in Program.get_all_configs():
        if get_slug(program['label'], suffix) in slugs:
            matching_programs.append(program)

    return matching_programs


def queue_org_welcome(templates):
    """After joining a program for the first time, welcome them."""
    # Every org-program combination is represented by a Project. Look for
    # recently created ones.
    yesterday = datetime.datetime.now() - datetime.timedelta(hours=24)

    # Which programs have a welcome template?
    to_welcome = programs_with_template(templates, ORG_WELCOME_SUFFIX)
    tasks = []

    for program in to_welcome:
        # Can't use .get() from DatastoreModel because of the >= query
        query = Project.query(
            Project.created >= yesterday,
            Project.deleted == False,
            Project.program_label == program['label'],
        )
        for project_key in query.iter(keys_only=True):
            url = '/task/email_project/{}/{}'.format(
                project_key.id(),
                get_slug(program['label'], ORG_WELCOME_SUFFIX)
            )
            task = taskqueue.add(url=url)
            tasks.append(task)

    return tasks


def queue_org_welcome_back(templates):
    """After joining a program for the first time, welcome them."""
    # Orgs signing up for a program generate a new ProjectCohort every year.
    # Look for recently created ones, then exclude orgs that only have one PC
    # in this program.
    yesterday = datetime.datetime.now() - datetime.timedelta(hours=24)

    # Which programs have a template?
    to_prompt = programs_with_template(templates, ORG_WELCOME_BACK_SUFFIX)
    tasks = []

    for program in to_prompt:
        # Can't use .get() from DatastoreModel because of the >= query
        query = ProjectCohort.query(
            ProjectCohort.created >= yesterday,
            ProjectCohort.deleted == False,
            ProjectCohort.program_label == program['label'],
        )

        # Gather the project ids of all applicable project cohorts. By tracking
        # unique project ids, we only email each org in this program once.
        project_ids = set()
        for pc in query.iter(projection=[ProjectCohort.project_id]):
            if pc.project_id not in project_ids:
                if ProjectCohort.count(project_id=pc.project_id) > 1:
                    project_ids.add(pc.project_id)

        # Now send an email for each org that qualifies.
        for project_id in project_ids:
            # Then this org has done this program before, they're returning
            # so welcome them back.
            url = '/task/email_project/{}/{}'.format(
                project_id,
                get_slug(program['label'], ORG_WELCOME_BACK_SUFFIX)
            )
            task = taskqueue.add(url=url)
            tasks.append(task)

    return tasks


def queue_checklist_nudge(templates):
    # Is it exactly one month before the program opens for student
    # participation for this cohort year? Find all orgs registered and send
    # them reminder email (complete checklist, participation code, etc)

    tasks = []

    month_from_now = util.datelike_to_iso_string(
        datetime.date.today() + datetime.timedelta(days=30))

    to_prompt = programs_with_template(templates, CHECKLIST_NUDGE_SUFFIX)
    for program in to_prompt:
        for cohort in program['cohorts'].values():

            project_ids = set()
            if cohort['open_date'] == month_from_now:
                # This whole cohort needs a nudge. Get all the project cohorts.
                pcs = ProjectCohort.get(
                    program_label=program['label'],
                    cohort_label=cohort['label'],
                    projection=['project_id'],
                    n=float('inf'),
                )
                for pc in pcs:
                    url = '/task/email_project/{}/{}'.format(
                        pc.project_id,
                        get_slug(program['label'], CHECKLIST_NUDGE_SUFFIX)
                    )
                    task = taskqueue.add(url=url)
                    tasks.append(task)

    return tasks
