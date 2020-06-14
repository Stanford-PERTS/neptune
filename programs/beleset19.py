# -*- coding: utf-8 -*-

# A Copilot program: BELE-SET
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
    'label': 'beleset19',
    'name': "Copilot-Elevate",
    'listed': False,
    'description': (
        "Description not yet written"
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
            'anonymous_link': 'https://saturn.perts.net/surveys/beleset19',
            'survey_tasklist_template': [],
        },
    ],
}
