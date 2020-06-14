
program_name = "Growth Mindset for 9th Graders"

config = {
    'label': 'hg17',
    'name': program_name,
    'listed': True,
    'description': ("A free, evidence-based program to increase students' "
                    "engagement, motivation, and success by promoting a "
                    "growth mindset."),
    'default_account_manager': 'support@perts.net',
    'default_portal_type': 'first_mi_last',
    'presurvey_states': [
        # These are state names for ui-router, relative to `presurvey`.
        # See static_src/routes/participate.js
        'skipCheck',
        'previewAgreement',
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
            'open_date': '2017-03-06',
            'close_date': '2018-05-16',
            'registration_open_date': '2017-01-01',
            'registration_close_date': '2018-05-02',
        },
        '2018': {
            'label': '2018',
            'name': u"{apos}18-{apos}19".format(apos=u"\u02BC"),
            'open_date': '2018-06-01',
            'close_date': '2019-05-16',
            'registration_open_date': '2018-03-30',
            'registration_close_date': '2019-04-02',
        },
        '2019': {
            'label': '2019',
            'name': u"{apos}19-{apos}20".format(apos=u"\u02BC"),
            'open_date': '2019-05-20',
            'close_date': '2020-05-16',
            'registration_open_date': '2019-03-28',
            'registration_close_date': '2020-05-02',
        },
        '2020': {
            'label': '2020',
            'name': u"{apos}20-{apos}21".format(apos=u"\u02BC"),
            'open_date': '2020-06-01',
            'close_date': '2021-05-03',
            'registration_open_date': '2020-03-01',
            'registration_close_date': '2021-04-28',
        }
    },
    'default_cohort': "2017_spring",
    'project_tasklist_template': [
        # project checkpoint
        {
            'name': "Making the Commitment",
            'label': 'hg17_project__commitment',
            'tasks': [
                # project task
                {
                    'label': "hg17_project__letter_of_agreement",
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
                    'label': "hg17_project__loa_approval",
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
            'name': "Module 1",
            # HG20 Session 1 OFFICIAL
            'anonymous_link': '',
            'survey_tasklist_template': [
                # survey checkpoint
                {
                    'name': "Prepare to Participate",
                    'label': 'hg17_survey__prepare_session_1',
                    'body': """
<p>
  Decision time! Use this page to make important decisions about how your
  organization will implement {program_name}. The
  elections and agreements you make here will help us
  <strong>customize the program</strong> for your school and
  <strong>grant us official permission</strong> to provide you with services.
</p>
<p>
  If you haven&rsquo;t already, this is the time to study the
  <a target="_blank"
     href="/static/programs/hg17/information_packet.pdf">
    Program Information Packet</a>.
</p>
""".format(program_name=program_name),
                    'tasks': [
                        # survey task
                        {
                            'label': 'hg17_survey__reserve_resources',
                            'name': "Reserve Resources",
                            'body': """
<p>
  Reserve resources for <strong>both modules</strong> as needed. Consider:
</p>
<ul>
  <li>Computer labs or laptop carts</li>
  <li>Headphones for each student</li>
</ul>
<p>
  Schedule a time and day for each classroom to access the module. Each module
  takes up to 40 minutes to complete. <strong>Recall that the two modules must
  be scheduled 1-4 weeks apart.</strong>
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
                            'label': 'hg17_survey__faciliator_quiz',
                            'name': "Orient Faciliators",
                            'body': """
<p>
  Facilitators are the individuals who will be involved in administering the
  program to students. They may include instructors, computer lab staff, or
  others. The program will only succeed if facilitators understand what they
  are supposed to do and why it is important.
</p>
<p>
  Prepare facilitators for their duties by reviewing the
  <a target="_blank"
     ng-href="/facilitator_instructions/{[$ctrl.parentProjectCohort.short_uid]}">
    Facilitator Instructions
  </a> with them and by providing opportunities for them to ask questions and
  take part in planning for a smooth implementation.
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
                            'label': 'hg17_survey__expected_participants',
                            'name': "Expected Participation",
                            'body': """
<p>
  Approximately how many students will be invited to participate? This will
  help you gauge how successful you were at reaching your participation goals.
</p>
""",
                            'action_statement': "Submit",
                            'data_type': 'input:number',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'hg17_survey__other_gms',
                            'name': "Other Growth Mindset Efforts at your School",
                            'body': """
<p>
  One of our goals is to learn what schools are doing to promote growth
  mindset and how we can support those efforts. For example, some schools use
  textbooks that discuss growth mindset. Others conduct faculty professional
  development around growth mindset.
</p>
<p>
  To the best of your knowledge, what other things is your school currently
  doing or planning to do to promote growth mindset? If {program_name}
  is your school&rsquo;s first and only such effort, write
  &ldquo;none.&rdquo;
</p>
""".format(program_name=program_name),
                            'action_statement': None,
                            'data_type': 'textarea',
                            'non_admin_may_edit': True,
                        },
                         # survey task
                        {
                            'label': 'hg17_survey__recruitment_source',
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
                    'label': 'hg17_survey__quiz',
                    'body': """
<p>
  {program_name} is a research-based program, and it
  should be administered following a specific protocol. Failing to follow the
  protocol could cause the program to become ineffective. Take this quiz to
  test your knowledge of the appropriate administration protocol so that you
  can be sure you are following this protocol appropriately.
</p>
<p>
  You may also learn more about the research behind Growth Mindset interventions
  by reading this
  <a target="_blank"
   href="http://gregorywalton-stanford.weebly.com/uploads/4/9/4/4/49448111/yeagerwalton2011.pdf">
  review article by David Yeager and Greg Walton</a>.
</p>
""".format(program_name=program_name),
                    'tasks': [
                        # survey task
                        {
                            'label': 'hg17_survey__instruction_framing',
                            'name': "How to Describe the Student Modules",
                            'body': """
<p>
  When students are invited to participate in %s
  the program modules will always be described using the wording in the
  <a target="_blank"
     ng-href="/facilitator_instructions/{[$ctrl.parentProjectCohort.short_uid]}">
    Facilitator Instructions</a>.
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
                            'label': 'hg17_survey__code_expiration',
                            'name': "Participation Code Duration",
                            'body': """
<p>
  Your participation code will expire on
  {[$ctrl.cohort.close_date | date:'longDate']}. On or after this date, you
  will need to register for the next cohort in order for your students to
  participate.
</p>""",
                            'action_statement': "I Understand",
                            'data_type': 'button',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'hg17_survey__quiz_instruction_framing',
                            'name': "Quiz: Describing the Module",
                            'body': """
<p>
  {program_name} should be described as:
</p>
""".format(program_name=program_name),
                            'action_statement': None,
                            'data_type': 'radio:quiz',
                            'select_options': [
                                {"value": "incorrect", "label": (
                                    "An intervention that will help them do "
                                    " better in school."
                                )},
                                {"value": "correct", "label": (
                                    "A welcome activity that the school "
                                    "thinks is important for all students."
                                )}
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'hg17_survey__quiz_expiration',
                            'name': "Quiz: Participation Code Duration",
                            'body': """
<p>
  Your participation code will remain the same every year.
</p>
""",
                            'action_statement': None,
                            'data_type': 'radio:quiz',
                            'select_options': [
                                {"value": "incorrect_true", "label": "True"},
                                {"value": "correct", "label": "False"},
                            ],
                            'non_admin_may_edit': True,
                        },
                    ],
                },
                # survey checkpoint
                {
                    'name': "Launch Module 1",
                    'label': 'hg17_survey__monitor_1',
                    'body': """
<p>
  Hooray! This page will let you launch {program_name} and
  track students&rsquo; participation for the first of the two modules.
</p>
""".format(program_name=program_name),
                    'tasks': [
                        # survey task
                        {
                            'label': 'hg17_survey__monitor_1',
                            'name': "Monitor Module 1",
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
      Launched! You&rsquo;re ready to go. Just follow the
      <a
        target="_blank"
        ng-href="/facilitator_instructions/{[$ctrl.parentProjectCohort.short_uid]}"
      >
        Facilitator Instructions
      </a>
      to invite them.
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
      &ldquo;We&rsquo;ve Finished Module 1&rdquo; below.
    </p>
  </div>
  <p ng-show="$ctrl.task.attachment === 'complete'">
    You marked this module as complete. Students can still participate if they
    need to make up a missed session.
  </p>
</nep-monitor-survey-task>
""",
                            'action_statement': "We've Finished Module 1",
                            'data_type': 'monitor',
                            'non_admin_may_edit': True,
                        },
                    ],
                },
            ]
        },
        # survey
        {
            'name': "Module 2",
            # HG20 Session 2 OFFICIAL
            'anonymous_link': '',
            'survey_tasklist_template': [
                # survey checkpoint
                {
                    'name': "Launch Module 2",
                    'label': 'hg17_survey__monitor_2',
                    'body': """
<p>
  Great job! This page will let you launch the second part of {program_name}
  as well as track students&rsquo; participation.
</p>
""".format(program_name=program_name),
                    'tasks': [
                        # survey task
                        {
                            'label': 'hg17_survey__adjustments_2',
                            'name': "Administration Adjustments",
                            'body': """
<p>
  Before beginning Module 2, review how Module 1 went by asking yourself these
  two questions.
</p>
<ol>
  <li>
    Do you have any students for whom you want to schedule makeups for Module
    1?
  </li>
  <li>
    Are there any adjustments you want to make to increase participation for
    Module 2?
  </li>
</ol>
""",
                            'action_statement': "I've Done This",
                            'data_type': 'button',
                            'non_admin_may_edit': True,
                        },
                        # Confirm Reserved Resources for Module 2 with min separation
                        # survey task
                        {
                            'label': 'hg17_survey__confirm_resources_2',
                            'name': "Confirm Reserved Resources",
                            'body': """
<p>
  Confirm all resources needed for Module 2 are reserved.
</p>
""",
                            'action_statement': "I've Done This",
                            'data_type': 'button',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'hg17_survey__remind_2',
                            'name': "Remind Facilitators",
                            'body': """
<p>
  Remind your facilitators about Module 2. We recommend a reminder one week ahead
  of time, and another reminder one day ahead of time.
</p>
""",
                            'action_statement': "I've Done This",
                            'data_type': 'button',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'hg17_survey__monitor_2',
                            'name': "Module 2",
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
    because your PERTS account manager still needs to check on some of your work.
    We&rsquo;ll do this as soon as we can. Thanks so much for your patience.
  </p>
  <p ng-show="$ctrl.task.attachment === 'ready' && !$parent.$ctrl.openByDate">
    On Your Marks: You&rsquo;re ready to go as soon as the program opens for
    participation on
    {[$parent.$ctrl.cohort.participationOpenDate | date:'longDate']}.
  </p>
  <div ng-show="$ctrl.task.attachment === 'ready' && $parent.$ctrl.openByDate">
    <p>
      Launched! You&rsquo;re ready to go. Just follow the
      <a
        target="_blank"
        ng-href="/facilitator_instructions/{[$ctrl.parentProjectCohort.short_uid]}"
      >
        Facilitator Instructions
      </a>
      to invite them.
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
      &ldquo;We&rsquo;ve Finished Module 2&rdquo; below.
    </p>
  </div>
  <p ng-show="$ctrl.task.attachment === 'complete'">
    You marked this module as complete. Students can still participate if they
    need to make up a missed session.
  </p>
</nep-monitor-survey-task>
""",
                            'action_statement': "We've Finished Module 2",
                            'data_type': 'monitor',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'hg17_survey__report_2',
                            'name': "Final Report",
                            'body': """
<p>
  We will make reports available here according to the schedule in your
  Information Packet. The report will include information about the impact of
  the program on survey outcomes at your school. Return here to download the
  report once your students have completed the program.
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
