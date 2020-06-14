# A Copilot program. The Classroom Connections Program.
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
    'label': 'ccp19',
    'name': "The Classroom Connections Program",
    'listed': False,
    'description': (
        "Helping teachers build strong relationships that foster equitable "
        "student engagement and success."
    ),
    'contact_email_address': 'copilot@perts.net',
    'default_portal_type': 'name_or_id',
    'override_portal_message': (
        "Please enter your unique code. This might be your email or a special "
        "number."
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
