# program
config = {
    'label': 'demo-program',
    'name': "Demo Program",
    'listed': False,
    'description': "An evidence-based program to raise retention and equity.",
    'default_portal_type': 'first_mi_last',
    'presurvey_states': [
        'skipCheck',
    ],
    'cohorts': {
        '2017_spring': {
            'label': "2017_spring",
            'name': "Spring 2017",
            'open_date': "2017-01-01",
            'close_date': "2017-05-31"
        }
    },
    'default_cohort': "2017_spring",
    'project_tasklist_template': [
        # project checkpoint
        {
            'name': "Making the Commitment",
            'label': 'demo_project__commitment',
            'tasks': [
                # project task
                {
                    'label': 'demo_project__research_compliance_doc',
                    'name': "Upload a signed letter",
                    'body': """
<p>
  Download <a href="#">the commitment letter</a>, read it carefully, and have
  it signed by your college Dean or President. Upload the signed letter here.
</p>
""",
                    'action_statement': None,  # uses default for file upload
                    'data_type': 'file',
                    'non_admin_may_edit': True,
                },
            ]
        },
        # project checkpoint
        {
            'name': "Study Fidelity Training",
            'label': 'demo_project__fidelity_training',
            'tasks': [
                # project task
                {
                    'label': 'demo_project__fidelity_quiz_student_names',
                    'name': "Quiz Question 1",
                    'body': """
<p>
  Participants have to provide their names to participate.
</p>
""",
                    'action_statement': (
                        "Select one of the options below to complete this "
                        "task."
                    ),
                    'data_type': 'radio',
                    'select_options': [
                        {"value": "correct", "label": "True"},
                        {"value": "incorrect", "label": "False"}
                    ],
                    'non_admin_may_edit': True,
                },
                # project task
                {
                    'label': 'demo_project__fidelity_quiz_name_storage',
                    'name': "Quiz Question 2",
                    'body': """
<p>
  Participants names are stored by PERTS.
</p>
""",
                    'action_statement': (
                        "Select one of the options below to complete this "
                        "task."
                    ),
                    'data_type': 'radio',
                    'select_options': [
                        {"value": "incorrect", "label": "True"},
                        {"value": "correct", "label": "False"}
                    ],
                    'non_admin_may_edit': True,
                },
                # project task
                {
                    'label': 'demo_project__fidelity_quiz_participation',
                    'name': "Quiz Question 3",
                    'body': """
<p>
  Student participation consists of one 30-minute online module.
</p>
""",
                    'action_statement': (
                        "Select one of the options below to complete this "
                        "task."
                    ),
                    'data_type': 'radio',
                    'select_options': [
                        {"value": "correct", "label": "True"},
                        {"value": "incorrect", "label": "False"}
                    ],
                    'non_admin_may_edit': True,
                },
            ]
        },
        # project checkpoint
        {
            'name': "Making the Commitment",
            'label': 'demo_project__approval',
            'tasks': [
                # project task
                {
                    'label': "demo_project__letter_of_agreement",
                    'name': "Agree to Terms of Use and Privacy Policy",
                    'body': """
<p>
  Review the <a target="_blank" ng-href="//www.perts.net/terms-of-use">
  Terms of Use</a> and <a target="_blank" ng-href="//www.perts.net/privacy">
  Privacy Policy</a> and click the &ldquo;I Agree&rdquo; button below.
</p>
    """,
                    'action_statement': "I Agree",
                    'data_type': 'button',
                    'non_admin_may_edit': True,
                },
                # project task
                {
                    'label': 'project__loa_approval',
                    'name': "Participation Approval",
                    'body': """
<p>
  Your PERTS Account Manager will approve your participation within 7 days of
  you agreeing to the terms of use and privacy policy or email you if there
  is a problem.
</p>
""",
                    # Do NOT wrap in a block level element.
                    'action_statement': (
                        "Your PERTS Account Manager will complete this task " +
                        "within 7 days."
                    ),
                    'data_type': 'button',
                    'non_admin_may_edit': False,
                },
            ]
        },
    ],
    'surveys': [
        # survey
        {
            'name': "Intervention",
            'anonymous_link': '',
            'survey_tasklist_template': [
                # survey checkpoint
                {
                    'name': "Participant Data",
                    'label': 'demo_survey__participant_data',
                    'tasks': [
                        # survey task
                        {
                            'label': 'demo_survey__expected_participants',
                            'body': """
<p>
  How many participants do you expect will complete the module?
</p>
""",
                            'action_statement': (
                                "Enter a number to complete this task."
                            ),
                            'data_type': 'input:number',
                            'non_admin_may_edit': True,
                        },
                    ]
                },
                # survey checkpoint
                {
                    'name': "Session Planning",
                    'label': 'demo_survey__session_planning',
                    'tasks': [
                        # survey task
                        {
                            'label': 'demo_survey__session_instructions',
                            'body': """
<p>
  Carefully read the
  <a href="/programs/cg17/session_instructions/{{short_parent_id}}">
  session instructions</a>.
</p>
""",
                            'action_statement': (
                                "I've Done This"
                            ),
                            'data_type': 'button',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'demo_survey__participation_method',
                            'name': "Participation Method",
                            'body': """
<p>
  Choose a method to run the student module.
</p>
""",
                            'action_statement': (
                                "Select one of the options below to complete "
                                "this task."
                            ),
                            'data_type': 'radio',
                            'select_options': [
                                {'value': 'orientation', 'label': (
                                    "Place a link in a required digital "
                                    "orientation process. Please account for "
                                    "the 30 minutes this will take."
                                )},
                                {'value': 'course', 'label': (
                                    "In-classroom sessions where students in "
                                    "a required first year course use "
                                    "provided computers to access the module "
                                    "(note that instructors in these classes "
                                    "do NOT need a PERTS account but WILL "
                                    "need a copy of the session instructions)."
                                )},
                                {'value': 'email', 'label': (
                                    "Send a link sent to their institutional "
                                    "email accounts (not recommended, likely "
                                    "to lead to low participation rates)."
                                )},
                            ],
                            'non_admin_may_edit': True,
                        },
                    ]
                },
            ]
        },
        # survey
        {
            'name': "Follow Up 1",
            'anonymous_link': '',
            'survey_tasklist_template': [
                # survey checkpoint
                {
                    'name': "Follow Up 1",
                    'label': 'demo_survey__follow_up_1',
                    'tasks': [],
                },
            ],
        },
        # survey
        {
            'name': "Follow Up 2",
            'anonymous_link': '',
            'survey_tasklist_template': [
                # survey checkpoint
                {
                    'name': "Follow Up 2",
                    'label': 'demo_survey__follow_up_2',
                    'tasks': [],
                },
            ],
        },
    ]
}
