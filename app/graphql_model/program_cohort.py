"""GraphQL cohort schema."""

import graphene
import model


class ProgramCohort(graphene.ObjectType):
    class Meta:
        def default_resolver(p, default, root, info):
            return root.get(p, None)
    label = graphene.String()
    name = graphene.String()
    program_description = graphene.String()
    program_label = graphene.String()
    program_name = graphene.String()
    # These are always date strings, but we control the inputs, so don't bother
    # with validation.
    open_date = graphene.String()
    close_date = graphene.String()
    registration_open_date = graphene.String()
    registration_close_date = graphene.String()


def program_cohort_resource_resolver(program_label, cohort_label):
    program_conf = model.Program.get_config(program_label)
    cohort_conf = program_conf['cohorts'][cohort_label]
    cohort_conf.update(
        program_description=program_conf['description'],
        program_label=program_conf['label'],
        program_name=program_conf['name'],
    )
    return cohort_conf


def program_cohort_collection_resolver(root, info, **kwargs):
    program_conf = model.Program.get_config(kwargs['program_label'])
    cohorts = sorted(
        program_conf['cohorts'].values(),
        key=lambda c: c['label'],
    )
    for c in cohorts:
        c.update(program_label=program_conf['label'],
                 program_name=program_conf['name'])
    return cohorts

ProgramCohortResource = graphene.Field(
    ProgramCohort,
    args={
        'cohort_label': graphene.Argument(graphene.String),
        'program_label': graphene.Argument(graphene.String),
    },
    resolver=lambda root, info, **kwargs: program_cohort_resource_resolver(
        kwargs['program_label'],
        kwargs['cohort_label'],
    )
)


ProgramCohortCollection = graphene.Field(
    graphene.List(ProgramCohort),
    args={'program_label': graphene.Argument(graphene.String)},
    resolver=program_cohort_collection_resolver,
)
