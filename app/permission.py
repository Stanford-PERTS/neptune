"""What relationships (ownership, association...) do users have to things?"""

import logging

from model import DatastoreModel


def owns(user, id_or_entity):
    """Does this user own the object in question?"""

    # Supers own everything.
    if user.super_admin:
        return True

    if owns_program(user, id_or_entity):
        return True

    # Convert to id.
    uid = (str(id_or_entity) if isinstance(id_or_entity, basestring)
           else id_or_entity.uid)

    kind = DatastoreModel.get_kind(uid)

    # Everyone owns public data.
    owned_orgs = user.owned_organizations + ['Organization_public']

    if kind == 'Organization':
        result = uid in owned_orgs
    elif kind == 'Project':
        project = DatastoreModel.get_by_id(uid)
        user_owns_program = project.program_label in user.owned_programs
        user_owns_org = project.organization_id in owned_orgs
        user_owns_project = project.uid in user.owned_projects
        result = user_owns_program or user_owns_org or user_owns_project
    elif kind == 'ProjectCohort':
        # Same logic as project
        pc = DatastoreModel.get_by_id(uid)
        user_owns_program = pc.program_label in user.owned_programs
        user_owns_org = pc.organization_id in owned_orgs
        result = user_owns_program or user_owns_org
    elif kind == 'Survey':
        # Same logic as project
        survey = DatastoreModel.get_by_id(uid)
        user_owns_program = survey.program_label in user.owned_programs
        user_owns_org = survey.organization_id in owned_orgs
        result = user_owns_program or user_owns_org
    elif kind == 'Task' or kind == 'TaskReminder':
        # same ownership as parent
        result = owns(user, DatastoreModel.get_parent_uid(uid))
    elif kind == 'User':
        result = uid == user.uid  # no slavery!
    elif kind == 'DataTable':
        result = uid in user.owned_data_tables
    elif kind == 'DataRequest':
        result = uid in user.owned_data_requests
    elif kind == 'Notification':
        # same ownership as parent
        result = owns(user, DatastoreModel.get_parent_uid(uid))
    else:
        raise NotImplementedError("Ownership does not apply to " + uid)

    return result


def owns_program(user, program_label):
    return user.super_admin or program_label in user.owned_programs
