from google.appengine.ext import ndb

from model import (DatastoreModel, Notification, Organization, Program, Project,
                   ProjectCohort, User)


def get_project_program_recipients(project):
    """What super/program admins get notifications about this project?"""
    if project.account_manager_id:
        return [User.get_by_id(project.account_manager_id)]
    else:
        return User.get(owned_programs=project.program_label)


def get_project_organization_recipients(project):
    """What org admins get notifications about this project?"""
    if project.liaison_id:
        return [User.get_by_id(project.liaison_id)]
    else:
        return User.get(user_type='user',
                        owned_organizations=project.organization_id)


def received_data_request(user, data_request):
    """Notify just recipient."""
    note = Notification.create(
        parent=user,
        context_id=data_request.uid,
        subject=data_request.title,
        body=data_request.description,  # obv. needs to be extended later
        link=data_request.link,
    )
    note.put()


def received_invitation(user, inviter, context_id=None):
    note = Notification.create(
        parent=user,
        context_id=context_id,
        subject="You've been invited to PERTS.",
        body=u"{} invited you to create an account.".format(inviter.name),
        link='/dashboard',
        autodismiss=True,
    )
    note.put()


def requested_to_join_organization(user, organization):
    """Notify existing org admins."""
    # Joining user won't appear here b/c they have assc_organizations.
    owners = User.get(owned_organizations=organization.uid, n=float('inf'))
    notes = []
    for owner in owners:
        note = Notification.create(
            parent=owner,
            context_id=organization.uid,
            subject="New user in your organization",
            body=u"{} would like to join {}.".format(
                user.name, organization.name),
            link='/organizations/{}/users'.format(organization.short_uid),
            autodismiss=True,
        )
        notes.append(note)
    ndb.put_multi(notes)


def joined_organization(approver, joiner, organization):
    """Notify joiner that existing owners approved the join."""
    note = Notification.create(
        parent=joiner,
        context_id=organization.uid,
        subject="You have been approved",
        body=u"{} approved you to join {}.".format(
            approver.name, organization.name),
        link='/organizations/{}'.format(organization.uid),
        autodismiss=True,
    )
    note.put()


def rejected_from_organization(rejecter, rejectee, organization):
    """Notify rejectee that existing owners rejected them."""
    note = Notification.create(
        parent=rejectee,
        context_id=organization.uid,
        subject="You were not admitted",
        body=u"{} rejected your request to join {}.".format(
            rejecter.name, organization.name),
        # Doesn't make sense to send them to an org page which they're not
        # permitted to access. Provide no link at all.
        autodismiss=True,
        viewable=False,
    )
    note.put()


def created_organization(user, organization):
    """When an org is created. Agnostic of program.

    Not currently going out to anyone.
    """
    return
    # # To re-enable these notifications, use the code below.
    # supers = User.get(user_type='super_admin')
    # notes = []
    # for sup in supers:
    #     note = Notification.create(
    #         parent=sup,
    #         context_id=organization.uid,
    #         subject="New organization",
    #         body=u"{} ({}) created {}.".format(
    #             user.name, user.email, organization.name),
    #         link='/organizations/{}'.format(organization.uid),
    #         autodismiss=True,
    #     )
    #     notes.append(note)
    # ndb.put_multi(notes)


def changed_organization_task(user, organization, task,
                              project_cohort_id=None):
    """Notify the other type of user, not one's own type: org or super."""
    t_dict = task.to_client_dict()
    if project_cohort_id:
        link = '/dashboard/{pc}/tasks/{ckpt}/{task}'.format(
            pc=DatastoreModel.convert_uid(project_cohort_id),
            ckpt=DatastoreModel.convert_uid(task.checkpoint_id),
            task=task.uid
        )
    else:
        link = '/dashboard'
    params = {
        'task_id': task.uid,
        'context_id': organization.uid,
        'subject': "Task updated",
        'body': u"{} updated \"{}\" in {}.".format(
            user.name, t_dict['name'], organization.name),
        'link': link,
        'autodismiss': True,
    }
    notes = []
    if user.super_admin:
        # Notify anyone who owns the organization.
        admins = User.get(
            user_type='user', owned_organizations=organization.uid)
        notes += [Notification.create(parent=a, **params) for a in admins]
    if user.non_admin:
        # Super admins are too busy to care.
        pass
        # # Old code for sending to supers.
        # supers = User.get(user_type='super_admin')
        # notes += [Notification.create(parent=s, **params) for s in supers]
    # else program admin? Program admins are largely not implemented, and likely
    # won't have rights to modify/approve organizations anyway.

    filtered_notes = Notification.filter_redundant(notes)
    ndb.put_multi(filtered_notes)


def created_project(user, project):
    """Notify any program owners, regardless of type."""
    # This isn't very useful since it always happens along with a project
    # cohort (for now).
    # @todo(chris): resurrect or delete this once it becomes more clear how
    # we're going to handle additional cohorts in the future.
    pass
    # admins = User.get(owned_programs=project.program_label)
    # organization = Organization.get_by_id(project.organization_id)
    # program_config = Program.get_config(project.program_label)
    # notes = []
    # for admin in admins:
    #     note = Notification.create(
    #         parent=admin,
    #         context_id=project.uid,
    #         subject=u"{} joined {}".format(
    #             organization.name, program_config['name']),
    #         body=u"{} applied for {} to join {}.".format(
    #             user.name, organization.name, program_config['name']),
    #         link='/projects/{}'.format(project.uid),
    #         autodismiss=True,
    #     )
    #     notes.append(note)
    # ndb.put_multi(notes)


def changed_project_task(user, project, task, project_cohort_id=None):
    """If change made by an org admin, notify related account manager, or all
    the program owners. Otherwise, notify project liaison, or all the org
    admins.
    """
    t_dict = task.to_client_dict()
    program_config = Program.get_config(project.program_label)
    if project_cohort_id:
        link = '/dashboard/{pc}/tasks/{ckpt}/{task}'.format(
            pc=DatastoreModel.convert_uid(project_cohort_id),
            ckpt=DatastoreModel.convert_uid(task.checkpoint_id),
            task=task.uid
        )
    else:
        link = '/dashboard'
    params = {
        'task_id': task.uid,
        'context_id': project.uid,
        'subject': "Task updated",
        'body': u"{} updated \"{}\" in {}.".format(
            user.name, t_dict['name'], program_config['name']),
        'link': link,
        'autodismiss': True,
    }
    if user.non_admin:
        # Send to account managers (usu. set via program config ->
        # default_account_manager).
        parents = get_project_program_recipients(project)
    else:
        parents = get_project_organization_recipients(project)
    notes = [Notification.create(parent=p, **params) for p in parents]

    filtered_notes = Notification.filter_redundant(notes)
    ndb.put_multi(filtered_notes)


def changed_survey_task(user, survey, task, project_cohort_id=None):
    """Behave just the same as project tasks IF notifing org admins."""
    if user.user_type != 'super_admin':
        # The user who took action is an org admin. Suppress these
        # notifications b/c super admins are too busy.
        return
    else:
        # The user who took action is a staff memeber, _do_ notify org admins
        # that we changed something, following rules for project tasks.
        project = Project.get_by_id(survey.project_id)
        changed_project_task(user, project, task, project_cohort_id)


def completed_task_list(completer, tasklist_parent):
    """A whole tasklist is done. Let owners know, and also:

    * super admins, if an org
    * org admins, if an org
    * owners of the program, otherwise
    """
    # Tasklists aren't a UI concept any longer.
    # @todo(chris): resurrect or delete this once it becomes more clear how
    # we're going to handle additional cohorts in the future.
    pass
    # recipients = set()

    # parent_kind = DatastoreModel.get_kind(tasklist_parent)
    # if parent_kind == 'Organization':
    #     org = tasklist_parent
    #     recipients.update(User.get(user_type='super_admin'))
    #     recipients.update(User.get(user_type='user',
    #                                owned_organizations=org.uid))
    #     parent_name = org.name
    # elif parent_kind == 'Project':
    #     project = tasklist_parent
    #     recipients.update(get_project_program_recipients(project))
    #     recipients.update(get_project_organization_recipients(project))
    #     parent_name = Program.get_config(project.program_label)['name']

    # notes = []
    # for r in recipients:
    #     note = Notification.create(
    #         parent=r,
    #         context_id=tasklist_parent.uid,
    #         subject="Tasklist complete",
    #         body=u"{} finished all tasks for {}.".format(
    #             completer.name, parent_name),
    #         link='/{}/{}'.format(
    #             DatastoreModel.get_url_kind(tasklist_parent), tasklist_parent.uid),
    #         autodismiss=True,
    #     )
    #     notes.append(note)
    # ndb.put_multi(notes)


def joined_cohort(user, project_cohort):
    """Notify program and super admins."""
    # This always happens along with creating a program.
    pc = project_cohort
    program_admins = User.get(owned_programs=pc.program_label)
    super_admins = User.get(user_type='super_admin')
    organization = Organization.get_by_id(pc.organization_id)
    program_config = Program.get_config(pc.program_label)
    cohort_name = program_config['cohorts'][pc.cohort_label]['name']

    notes = []
    for admin in program_admins + super_admins:
        note = Notification.create(
            parent=admin,
            context_id=pc.uid,
            subject=u"{org} joined a cohort".format(org=organization.name),
            body=(
                u"{org} joined {cohort} in {program}. The organization is "
                "currently {status}."
            ).format(
                org=organization.name, cohort=cohort_name,
                program=program_config['name'], status=organization.status,
            ),
            link='/organizations/{}'.format(organization.short_uid),
            autodismiss=True,
        )
        notes.append(note)
    ndb.put_multi(notes)

def downloaded_identifiers(user, project_cohort_id):
    supers = User.get(user_type='super_admin')
    notes = []

    project_cohort = ProjectCohort.get_by_id(project_cohort_id)
    organization = Organization.get_by_id(project_cohort.organization_id)
    program = Program.get_config(project_cohort.program_label)
    cohort_name = program['cohorts'][project_cohort.cohort_label]['name']

    for sup in supers:
        note = Notification.create(
            parent=sup,
            context_id=project_cohort_id,
            subject="IDs Downloaded",
            body=u"{} ({}) downloaded IDs for {}: {} {}.".format(
                user.name, user.email, organization.name, program['name'],
                cohort_name),
            link='/dashboard/{}'.format(project_cohort.short_uid),
            autodismiss=True,
        )
        notes.append(note)
    ndb.put_multi(notes)
