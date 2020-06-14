"""Survey: One data collection point for one ProjectCohort.

Many-to-one with a Qualtrics survey.
"""

from collections import OrderedDict
from google.appengine.ext import ndb

from gae_models import DatastoreModel
import model


class Survey(DatastoreModel):
    project_id = ndb.StringProperty()
    organization_id = ndb.StringProperty()
    program_label = ndb.StringProperty()
    cohort_label = ndb.StringProperty()
    project_cohort_id = ndb.StringProperty()
    liaison_id = ndb.StringProperty()
    ordinal = ndb.IntegerProperty()
    # May be 'not ready', 'ready', or 'complete'
    status = ndb.StringProperty(default='not ready')

    # After creation, this will have a tasklist object, which in turn will
    # have checkpoints and tasks that need saving to their respective
    # databases.
    tasklist = None

    @classmethod
    def create(klass, tasklist_template, **kwargs):
        """Create task list as well."""
        survey = super(klass, klass).create(**kwargs)

        survey.tasklist = model.Tasklist.create(
            tasklist_template,
            survey,
            # Fields for the checkpoint table.
            program_label=survey.program_label,
            organization_id=survey.organization_id,
            project_id=survey.project_id,
            cohort_label=survey.cohort_label,
        )

        return survey

    @classmethod
    def create_for_project_cohort(klass, surveys_config, project_cohort):
        # Create surveys according to the program definition.
        surveys = []
        for i, survey_definition in enumerate(surveys_config):
            # Most things we need for surveys are available as pc params.
            survey = klass.create(
                survey_definition['survey_tasklist_template'],
                project_id=project_cohort.project_id,
                organization_id=project_cohort.organization_id,
                program_label=project_cohort.program_label,
                cohort_label=project_cohort.cohort_label,
                project_cohort_id=project_cohort.uid,
                liaison_id=project_cohort.liaison_id,
                ordinal=i + 1,
            )
            surveys.append(survey)
        return surveys

    @property
    def name(self):
        return self.config()['name']

    def after_put(self, *args, **kwargs):
        if self.tasklist:
            # Tasklist might not always be present; it is if created via
            # create(), but not if fetched from the datastore.
            self.tasklist.put()

        pc = model.ProjectCohort.get_by_id(self.project_cohort_id)
        if pc:
            # Reset memcache for cached properties of related objects.
            # This relationship is "up" so there's only one thing to update.
            # Take the time to refresh the cache value instead of just clearing.
            pc.update_cached_properties()
            # Also clear any related cached query results.
            pc.after_put()

    def config(self):
        program_config = model.Program.get_config(self.program_label)
        return program_config['surveys'][self.ordinal - 1]

    def to_client_dict(self):
        """Add program-derived properties for convenience."""
        d = super(Survey, self).to_client_dict()

        d.update(name=self.name)

        return OrderedDict((k, d[k]) for k in sorted(d.keys()))

    def tasklist_name(self):
        program_config = model.Program.get_config(self.program_label)
        return u'Preparation for {survey} in {cohort}'.format(
            survey=program_config['surveys'][self.ordinal - 1]['name'],
            cohort=program_config['cohorts'][self.cohort_label]['name'])
