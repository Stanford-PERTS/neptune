"""
Model
===========

Contains all Neptune data models
"""

import inspect
import sys

from gae_models import DatastoreModel
from gae_models import Email, SecretValue, SqlModel, StorageObject

from .accountmanager import AccountManager
from .authtoken import AuthToken
from .checkpoint import Checkpoint
from .datarequest import DataRequest
from .dataset import Dataset
from .datatable import DataTable
from .errorchecker import ErrorChecker
from .liaisonship import Liaisonship
from .notification import Notification
from .organization import Organization
from .participant import Participant
from .participantdata import ParticipantData
from .program import Program
from .project import Project
from .projectcohort import ProjectCohort
from .survey import Survey
from .surveylink import SurveyLink
from .task import Task
from .tasklist import Tasklist
from .taskreminder import TaskReminder
from .user import User, BadPassword, DuplicateUser

__version__ = '1.0.0'


def get_classes():
    """All the class definitions imported here.

    http://stackoverflow.com/questions/1796180/how-can-i-get-a-list-of-all-classes-within-current-module-in-python
    """
    member_tuples = inspect.getmembers(
        sys.modules[__name__], inspect.isclass)
    return [getattr(sys.modules[__name__], t[0]) for t in member_tuples]


def get_datastore_models():
    """Model classes backed by the datastore."""
    # All those classes which are datastore entities (subclass Model) and
    # have entities recorded.
    # Note this excludes classes which use the datastore but don't subclass
    # Model, e.g. SecretValue, which subclasses ndb.Model directly. But this
    # is the behavior we want anyway.
    return [c for c in get_classes()
            if issubclass(c, DatastoreModel) and c != DatastoreModel]


def get_sql_models():
    """Classes backed by Cloud SQL."""
    return [c for c in get_classes()
            if issubclass(c, SqlModel) and c != SqlModel]
