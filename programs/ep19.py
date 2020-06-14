# -*- coding: utf-8 -*-

# A Copilot program: The Engagement Project.
#
# Certain kinds of objects correspond across platforms:
#
# |    Neptune    |   Triton  |
# |---------------|-----------|
# | Organization  | Team      |
# | ProjectCohort | Classroom |
# | Program       | Program   |
#
# Also, a Neptune survey id, plus a "survey descriptor", like
# `Survey_123:cycle-1`, maps to a Triton Cycle.

config = {
    'label': 'ep19',
    'name': "The Engagement Project",
    'listed': False,
    'description': (
        "Build a classroom climate that fosters equitable academic "
        "engagement."
    ),
    'contact_email_address': 'copilot@perts.net',
    'default_portal_type': 'name_or_id',
    'override_portal_message': (
        "Please enter your roster ID. Usually that’s your school email "
        "address. Ask your instructor if you don’t know your roster ID."
    ),
    'platform': 'triton',
    'presurvey_states': [
        # These are state names for ui-router, relative to `presurvey`.
        # See static_src/routes/participate.js
        'previewAgreement',
        # 'epAssent',  # https://github.com/PERTS/triton/issues/1316
        'epBlockSwitcher',
    ],
    'cohorts': {},
    'default_cohort': "",
    'project_tasklist_template': [],
    'surveys': [
        # survey
        {
            'name': "Main Survey",
            # "Copilot OFFICIAL 2019-2020"
            'anonymous_link': '',
            'survey_tasklist_template': [],
        },
    ],
}
