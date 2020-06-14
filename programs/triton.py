# A Copilot program. The old (2018-19) Engagement Project.
config = {
    'label': 'triton',
    'name': "Triton Program",
    'listed': False,
    'description': "Not for display.",
    'default_portal_type': 'name_or_id',
    'default_portal_message': "Please enter your student ID:",
    'platform': 'triton',
    'presurvey_states': [
        # These are state names for ui-router, relative to `presurvey`.
        # See static_src/routes/participate.js
        'previewAgreement',
        'epRoster',
        'epAssent',
        'epBlockSwitcher',
    ],
    'cohorts': {},
    'default_cohort': "",
    'project_tasklist_template': [],
    'surveys': [
        # survey
        {
            'name': "Main Survey",
            # Updated 2018-08-07
            # Don't forget to change any references to this link in triton!
            'anonymous_link': '',
            'survey_tasklist_template': [],
        },
    ],
}
