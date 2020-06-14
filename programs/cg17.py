
program_name = "Growth Mindset for College Students"

config = {
    'label': 'cg17',
    'name': program_name,
    'listed': True,
    'description': "An evidence-based program to increase retention and equity.",
    'default_account_manager': 'support@perts.net',
    'default_portal_type': 'name_or_id',
    'presurvey_states': [
        # These are state names for ui-router, relative to `presurvey`.
        # See static_src/routes/participate.js
        'skipCheck',
        'previewAgreement',
        'iesCheck',
    ],
    'cohorts': {
        # N.B. Close dates are exclusive as opposed to inclusive, i.e. they go
        # into effect instantly, i.e. if the close date is 2018-01-01, the
        # computer will consider the thing to be closed at 2018-01-01 00:00:00.
        # So the last day of the thing is the day _before_ the close date. Keep
        # this in mind when translating from advertised deadlines, which will
        # typically be one day earlier.
        '2017_spring': {
            'label': '2017_spring',
            'name': u"{apos}17-{apos}18".format(apos=u"\u02BC"),
            'open_date': '2017-08-01',
            'close_date': '2018-05-16',
            'registration_open_date': '2017-01-01',
            'registration_close_date': '2018-04-06',
        },
        '2018': {
            'label': '2018',
            'name': u"{apos}18-{apos}19".format(apos=u"\u02BC"),
            'open_date': '2018-06-01',
            'close_date': '2019-05-16',
            'registration_open_date': '2018-02-28',
            'registration_close_date': '2019-05-02',
        },
        '2019': {
            'label': '2019',
            'name': u"{apos}19-{apos}20".format(apos=u"\u02BC"),
            'open_date': '2019-05-20',
            'close_date': '2020-05-16',
            'registration_open_date': '2019-01-07',
            'registration_close_date': '2020-05-02',
        },
        '2020': {
            'label': '2020',
            'name': u"{apos}20-{apos}21".format(apos=u"\u02BC"),
            'open_date': '2020-06-01',
            'close_date': '2021-05-03',
            'registration_open_date': '2020-03-01',
            'registration_close_date': '2021-03-29',
        }
    },
    'default_cohort': "2017_spring",
    'project_tasklist_template': [
        # project checkpoint
        {
            'name': "Making the Commitment",
            'label': 'cg17_project__commitment',
            'tasks': [
                # project task
                {
                    'label': "cg17_project__letter_of_agreement",
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
                    'label': "cg17_project__loa_approval",
                    'name': "Participation Approval",
                    'body': """
<p>
  Your PERTS Account Manager will reach out if there any problems with
  participating in this program within 7 days of you agreeing to the terms of
  use and privacy policy.
</p>
""",
                    'action_statement': None,
                    'data_type': 'button',
                    'non_admin_may_edit': False,
                    'initial_values': {
                      'status': 'complete',
                    },
                },
            ]
        },
    ],
    'surveys': [
        # survey
        {
            'name': "Student Module",
            # CG20 OFFICIAL
            'anonymous_link': '',
            'survey_tasklist_template': [
                # survey checkpoint
                {
                    'name': "Prepare to Participate",
                    'label': 'cg17_survey__prepare_session_1',
                    'body': """
<p>
  Decision time! Use this page to make important decisions about how your
  organization will implement {program_name}. The
  elections and agreements you make here will help us
  <strong>customize the program</strong> for your college and
  <strong>grant us official permission</strong> to provide you with services.
</p>
<p>
  If you haven&rsquo;t already, this is the time to study the
  <a
    target="_blank"
    href="/static/programs/cg17/information_packet.pdf"
  >Program Information Packet</a>.
</p>
""".format(program_name=program_name),
                    'tasks': [
                        # survey task
                        {
                            'label': "cg17_survey__pip",
                            'name': "Review the Information Packet",
                            'body': """
<p>
  Carefully read the
  <a target="_blank"
     href="/static/programs/cg17/information_packet.pdf">Information
  Packet</a> for <em>{program_name}</em>. Share it with any colleagues who will
  need to be familiar with the survey.
</p>
<p>
  The packet includes answers to <strong>most questions</strong> colleges
  have about the survey.
</p>
""".format(program_name=program_name),
                            'action_statement': "I've done this",
                            'data_type': 'button',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__administration_method',
                            'name': "Administration Method: Independent or Supervised?",
                            'body': """
<p>
  Choose an <strong>Administration Method</strong> to run the program. Here is
  an overview of the options; for more information, please refer to &ldquo;Which
  administration method will you use to administer the program&rdquo; in the
  Program Information Packet.
</p>
""",
                            'action_statement': None,  # use default
                            'data_type': 'radio',
                            'select_options': [
                                {'value': 'independent', 'label': """
Independent completion: choose this option if students will complete their
program in an unsupervised setting, e.g., students will complete the program on
a computer at home.
"""},
                                {'value': 'supervised', 'label': """
Supervised completion: choose this option if students will complete the program
in a supervised setting, like in a computer lab session for orientation or in a
first-year course. Students may use either their own computer or university-
provided computers. Please account for the 30 minutes this will take.
"""},
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__administration_context',
                            'name': "Administration Context",
                            'body': """
<p>
In what context will you administer the program? For example, you may implement
it during orientation, a first-year course, a developmental course, or you may
choose to administer the program in another context.
</p>
<p>
If you choose to administer the program in a course, it is important that the
course rosters don&rsquo;t overlap; students shouldn&rsquo;t be asked to
complete the program more than once.
</p>
""",
                            'action_statement': None,
                            'data_type': 'textarea',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__portal_quiz',
                            'name': "Sign In Portal",
                            'body': """
<p>
  Students can sign in through a custom portal created by your own
  college&rsquo;s IT department or through a generic portal at
  <a href="http://www.perts.me" target="_blank">perts.me</a>. For this option,
  please be sure to speak with your IT team about how feasible this will be on
  your campus.
</p>
""",
                            'action_statement': None,  # use default
                            'data_type': 'radio',
                            'select_options': [
                                {'value': 'custom', 'label': """
<strong>Custom Portal</strong>. Choose this option if you intend to create a
custom portal with the help of your organization&rsquo;s internal network
authorization. You&rsquo;ll need to
<strong>
  <a
    target="_blank" ng-
    href="/custom_portal_technical_guide/{[$ctrl.parentProjectCohort.short_uid]}"
  >
    share these instructions
  </a>
</strong> with your IT team in order to create a custom portal. We recommend
sharing the instructions as early as possible to determine how feasible this
will be at your school.
<ul>
  <li>Pros: This is the best option because your college&rsquo;s network will
  be in control of students&rsquo; IDs and because everything can be automated,
  eliminating common errors.</li>
  <li>Cons: Requires your IT staff to construct a special web page, for which
  we provide
  <a
    target="_blank"
    ng-href="/custom_portal_technical_guide/{[$ctrl.parentProjectCohort.short_uid]}"
  >detailed instructions</a>.
</ul>
"""},
                                {'value': 'name_or_id', 'label': """
<strong>Generic Portal</strong>. Choose this option if your IT team will not
set up a custom portal for your college.
<ul>
  <li>Pros: Less work for your IT department, as your IT staff will not need to
  set up a special web page.</li>
  <li>Cons: Increases the chances of identification errors as students enter
  the program, if they&rsquo;re unsure of or mistype their student IDs.</li>
</ul>
"""},
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__custom_portal_url',
                            'name': "Custom Portal URL",
                            'body': """
<nep-custom-portal-task portal-type="$ctrl.parentProjectCohort.portal_type"
                        task="$ctrl.task" task-complete="$ctrl.taskComplete()">
  <p ng-show="$parent.$ctrl.portalType === 'custom'">
    Great! You&rsquo;ve chosen to set up a custom portal for your organization.
    PERTS will direct students to it as part of the sign in process. Enter the
    URL of the portal that you and your IT staff create.
  </p>
  <p ng-show="$parent.$ctrl.portalType !== 'custom'">
    You&rsquo;re not using a custom portal for your organization. That
    means you&rsquo;re all done here!
  </p>
</nep-custom-portal-task>
""",
                            'action_statement': "Submit",
                            'data_type': 'input:url',
                            'non_admin_may_edit': True,
                            'initial_values': {
                                # This task should only come into play if the
                                # user actively choosed the custom portal
                                # option on a previous task.
                                'disabled': True,
                                'status': 'complete',
                            }
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__reserve_resources',
                            'name': "Reserve Resources",
                            'body': """
<p>
  Reserve resources as needed. This may include computer labs or laptop carts,
  or a scheduled time and day for each classroom to access the program (this
  may not be necessary if the program is assigned for individual completion,
  e.g., as homework or part of an online orientation).
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
                            'label': 'cg17_survey__faciliator_quiz',
                            'name': "Orient Faciliators",
                            'body': """
<p>
  Facilitators are the individuals who will be involved in administering the
  program to students. They may include instructors, computer lab staff, new
  student orientation staff, or others. The program will only succeed if
  facilitators understand what they are supposed to do and why it is important.
</p>
<p>
  Prepare facilitators for their duties by reviewing the
  <a
    target="_blank"
    ng-href="/facilitator_instructions/{[$ctrl.parentProjectCohort.short_uid]}"
  >
    Facilitator Instructions
  </a> with them and by providing opportunities for them to ask questions and
  take part in planning for a smooth implementation. You may also want to show
  them the Program Video and/or Program Brochure.
</p>
""",
                            'action_statement': None,  # use default
                            'data_type': 'radio:conditional',
                            'select_options': [
                                {'value': 'incorrect_none', 'label': """
We have not yet oriented facilitators.
"""},
                                {'value': 'incorrect_some', 'label': """
We have oriented some, but not all, facilitators and discussed the ins and outs
of participation.
"""},
                                {'value': 'correct', 'label': """
We have met with all facilitators and discussed the ins and outs of
participation.
"""},
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__expected_participants',
                            'name': "Expected Participation",
                            'body': """
<p>
  Approximately how many students do you expect will take part in the program?
  This will help you gauge how successful you were at reaching your
  participation goals.
</p>
""",
                            'action_statement': "Submit",
                            'data_type': 'input:number',
                            'non_admin_may_edit': True,
                        },

                        # survey task
                        {
                            'label': 'cg17_survey__expected_launch_date',
                            'name': "Expected Launch Date",
                            'body': """
<p>
  When will you be inviting students to participate in the program?
</p>
""",
                            'action_statement': "Submit",
                            'data_type': 'input:date',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__other_gms',
                            'name': "Other Growth Mindset Efforts at your College",
                            'body': """
<p>
  One of our goals is to learn what colleges are doing to promote growth
  mindset and how we can support those efforts. For example, some colleges use
  textbooks that discuss growth mindset. Others conduct faculty professional
  development around growth mindset.
</p>
<p>
  To the best of your knowledge, what other things is your school currently
  doing or planning to do to promote growth mindset? If {program_name}
  is your college&rsquo;s first and only such effort, write
  &ldquo;none.&rdquo;
</p>
""".format(program_name=program_name),
                            'action_statement': None,
                            'data_type': 'textarea',
                            'non_admin_may_edit': True,
                        },

                          # survey task
                        {
                            'label': 'cg17_survey__recruitment_source',
                            'name': "How Did You Learn About This Program?",
                            'body': """
<p>
  How did you learn about this program? What influenced your decision to
  register for this program?
</p>
""",
                            'action_statement': None,
                            'data_type': 'textarea',
                            'non_admin_may_edit': True,
                        },
                    ]
                },
                # survey checkpoint
                {
                    'name': "Quiz",
                    'label': 'cg17_survey__quiz',
                    'body': """
<p>
  {program_name} is a research-based program, and it
  should be administered following a specific protocol. Failing to follow the
  protocol could cause the program to become ineffective. Take this quiz to
  test your knowledge of the appropriate administration protocol so that you can
  be sure you are following this protocol appropriately. You may also want to go
  over these questions with the program facilitators.
</p>
<p>
  You may also learn more about the research behind Growth Mindset interventions
  by reading this
  <a
   target="_blank"
   href="http://gregorywalton-stanford.weebly.com/uploads/4/9/4/4/49448111/yeagerwalton2011.pdf"
  >
    review article by David Yeager and Greg Walton</a>.
</p>
""".format(program_name=program_name),
                    'tasks': [
                        # survey task
                        {
                            'label': 'cg17_survey__instruction_framing',
                            'name': "How to Describe the Program",
                            'body': """
<p>
  When students are invited to participate in %s
  the program will always be described using the wording in the
  <a
    target="_blank"
    ng-href="/facilitator_instructions/{[$ctrl.parentProjectCohort.short_uid]}"
  >Facilitator Instructions</a>.
</p>
""" % program_name,  # not using format b/c it doesn't play nice w/ {[ foo ]}
                            'action_statement': (
                                "I Understand"
                            ),
                            'data_type': 'button',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__code_expiration',
                            'name': "Participation Code Duration",
                            'body': """
<p>
  Your participation code will expire on
   {[$ctrl.cohort.displayCloseDate | date:'longDate']}. After this date, you
   will need to register for the next cohort in order for your students to
   participate.
</p>""",
                            'action_statement': (
                                "I Understand"
                            ),
                            'data_type': 'button',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__quiz_instruction_framing',
                            'name': "Quiz: Program Description",
                            'body': """

<p>
 How will you describe <em>{program_name}</em> when speaking to students?
</p>
""".format(program_name=program_name),
                            'action_statement': None,
                            'data_type': 'radio:quiz',
                            'select_options': [
                                {"value": "incorrect_program_name", "label": (
                                    "This activity is called {program_name}."
                                    .format(program_name=program_name)
                                )},
                                {"value": "incorrect_perts", "label": (
                                    "This is an activity from PERTS."
                                )},
                                {"value": "correct", "label": (
                                    "This is a welcome activity."
                                )},
                                {"value": "incorrect_help", "label": (
                                    """This is an activity to help students
                                    develop a growth mindset."""
                                )},
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__quiz_find_code',
                            'name': "Quiz: Participation Code",
                            'body': """
<p>
  Where can you find your college&rsquo;s participation code?
</p>
""",
                            'action_statement': None,
                            'data_type': 'radio:quiz',
                            'select_options': [
                                {"value": "incorrect_pip", "label": (
                                    "Program Information Packet"
                                )},
                                {"value": "correct", "label": (
                                    "Facilitator Instructions"
                                 )},
                                {"value": "incorrect_link", "label": (
                                    "perts.net/college-mindset"
                                )}
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__quiz_expiration',
                            'name': "Quiz: Participation Code Duration",
                            'body': """
<p>
  Your participation code will remain the same every year.
</p>
""",
                            'action_statement': None,
                            'data_type': 'radio:quiz',
                            'select_options': [
                                {"value": "incorrect_true", "label": (
                                    "True"
                                )},
                                {"value": "correct", "label": (
                                    "False"
                                 )},
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__quiz_frequency',
                            'name': "Quiz: Participation Frequency",
                            'body': """

<p>
  How often should a student complete the program?
</p>
""",
                            'action_statement': None,
                            'data_type': 'radio:quiz',
                            'select_options': [
                                {"value": "correct", "label": (
                                    "1 time"
                                )},
                                {"value": "incorrect_2", "label": (
                                    "2 times"
                                 )},
                                {"value": "incorrect_3", "label": (
                                    "3 times"
                                 )},
                                {"value": "incorrect_3+", "label": (
                                    "More than 3 times"
                                )}
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cg17_survey__quiz_colleague_framing',
                            'name': "Quiz: Orientation Resources",
                            'body': """
<p>
  We provide all of the following resources for introducing the program to your
  colleagues, except for:
</p>
""",
                            'action_statement': None,
                            'data_type': 'radio:quiz',
                            'select_options': [
                                {"value": "incorrect_video", "label": (
                                    "A brief video"
                                )},
                                {"value": "incorrect_facinstr", "label": (
                                    "Facilitator instructions"
                                 )},
                                {"value": "correct", "label": (
                                    "An explanation for why they&rsquo;re "
                                    "being invited to join the Dashboard"
                                 )},
                                {"value": "incorrect_pip", "label": (
                                    "Program Information Packet"
                                  )},
                                {"value": "incorrect_website", "label": (
                                    "An orientation website"
                                )},
                            ],
                            'non_admin_may_edit': True,
                        },
                    ],
                },
                # survey checkpoint
                {
                    'name': "Launch and Monitor",
                    'label': 'cg17_survey__monitor_1',
                    'body': """
<p>
  Hooray! This page will let you launch {program_name},
  track students&rsquo; participation, and view the program&rsquo;s results.
</p>
""".format(program_name=program_name),
                    'tasks': [
                        # survey task
                        {
                            'label': 'cg17_survey__monitor_1',
                            'name': "Monitor Program",
                            'body': """
<nep-monitor-survey-task
 set-completable="$ctrl.setValidity(surveyCompletable, error)"
 task-complete="$ctrl.taskComplete()"
 task="$ctrl.task"
 cohort="$ctrl.program.cohorts[$ctrl.parentProjectCohort.cohort_label]"
>
  <p ng-show="!$ctrl.task.attachment && !$ctrl.task.isCurrent">
    <!-- The previous checkpoints aren't all complete. Also, this task isn't
    the current one, which means the org admin has more work to do. -->
    Not ready yet! We need more information to customize your students&rsquo;
    experience. Make sure you&rsquo;ve done all previous tasks.
  </p>
  <p ng-show="!$ctrl.task.attachment && $ctrl.task.isCurrent">
    <!-- The previous checkpoints aren't all complete, but this task IS
    the current one, which means the only thing holding them up are program
    admin approval tasks. -->
    So sorry, we&rsquo;re holding you up! Your program isn&rsquo;t ready yet
    because your PERTS account manager still needs to check on some of your
    work. We&rsquo;ll do this as soon as we can. Thanks so much for your
    patience.
  </p>
  <p ng-show="$ctrl.task.attachment === 'ready' && !$parent.$ctrl.openByDate">
    On Your Marks: You&rsquo;re ready to go as soon as the program opens for
    participation on
    {[$parent.$ctrl.cohort.participationOpenDate | date:'longDate']}.
  </p>
  <div ng-show="$ctrl.task.attachment === 'ready' && $parent.$ctrl.openByDate">
    <p>
      Launched! You&rsquo;re ready to go. Your students can participate any
      time between
      {[$parent.$ctrl.cohort.participationOpenDate | date:'longDate']} and
      {[$parent.$ctrl.cohort.displayCloseDate | date:'longDate']}.
      Just follow the
      <a
        target="_blank"
        ng-href="/facilitator_instructions/{[$ctrl.parentProjectCohort.short_uid]}"
      >
        Facilitator Instructions
      </a>
      to invite them. If students are participating on their own, you can
      provide them with the
      <a
        target="_blank"
        ng-href="/student_handout/{[$ctrl.parentProjectCohort.short_uid]}"
      >
        Student Handout
      </a>
      so that they can turn in their completion codes to improve participation
      rates.
    </p>
    <p>
      Monitor how things are going in the Participation section. Here&rsquo;s a
      shortcut:
      <ui-action-button
        ui-sref="dashboard.participation({
          projectCohortId: $ctrl.parentProjectCohort.short_uid
        })"
       >
        <i class="fa fa-child" />
        Participation
      </ui-action-button>
    </p>
    <p>
      When all students have completed the program, come back here and click
      &ldquo;We&rsquo;ve Finished The Program&rdquo; below.
    </p>
  </div>
  <p ng-show="$ctrl.task.attachment === 'complete'">
    You marked this program as complete. Students can still participate if they
    need to make up a missed session.
  </p>
</nep-monitor-survey-task>
""",
                            'action_statement': "We've Finished The Program",
                            'data_type': 'monitor',
                            'non_admin_may_edit': True,
                        },
                        {
                            'label': 'cg17_survey__report_1',
                            'name': "Final Report",
                            'body': """
<p>
  We will make reports available here according to the schedule in your
  Information Packet. The report will include information about the impact of
  the program on survey outcomes at your college and across other participating
  colleges. Return here to download the report once your students have completed
  the program.
</p>
""",
                            'action_statement': None,
                            'data_type': 'file',
                            'non_admin_may_edit': False,
                            'counts_as_program_complete': True,
                        },
                    ]
                },
            ]
        },
    ]
}
