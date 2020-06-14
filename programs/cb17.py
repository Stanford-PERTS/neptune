
program_name = "Social-Belonging for College Students"

config = {
    'label': 'cb17',
    'name': program_name,
    'listed': True,
    'description': ("A free, evidence-based program designed to support a "
                    "sense of belonging on campus."),
    'default_account_manager': 'support@perts.net',
    'default_portal_type': 'name_or_id',
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
        '2017_fall': {
            'label': '2017_fall',
            'name': "Fall 2017",
            'open_date': '2017-07-01',
            'close_date': '2018-01-01',
            'registration_open_date': '2017-01-01',
            'registration_close_date': '2017-10-16',
        },
        '2018': {
            'label': '2018',
            'name': "Fall 2018",
            'open_date': '2018-06-01',
            'close_date': '2019-01-02',
            'registration_open_date': '2018-02-01',
            'registration_close_date': '2018-10-16',
        },
        '2019': {
            'label': '2019',
            'name': "Fall 2019",
            'open_date': '2019-05-20',
            'close_date': '2020-01-01',
            'registration_open_date': '2019-01-31',
            'registration_close_date': '2019-10-17',
        },
        '2020': {
            'label': '2020',
            'name': "Summer/Fall 2020",
            'open_date': '2020-06-01',
            'close_date': '2021-01-01',
            'registration_open_date': '2020-03-01',
            'registration_close_date': '2020-10-13',
        },
    },
    'default_cohort': "2017_fall",
    'project_tasklist_template': [
        # project checkpoint
        {
            'name': "Making the Commitment",
            'label': 'cb17_project__commitment',
            'tasks': [
                # project task
                {
                    'label': "cb17_project__letter_of_agreement",
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
                    'label': "cb17_project__loa_approval",
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
            # "CB20 OFFICIAL"
            'anonymous_link': '',
            'survey_tasklist_template': [
                # survey checkpoint
                {
                    'name': "Prepare to Participate",
                    'label': 'cb17_survey__prepare_session_1',
                    'body': """
<p>
  Decision time! Use this page to make important decisions about how your
  organization will implement <em>{program_name}</em>. The
  elections and agreements you make here will help us
  <strong>customize the program</strong> for your college and
  <strong>grant us official permission</strong> to provide you with services.
</p>
""".format(program_name=program_name),
                    'tasks': [
                        # survey task
                        {
                            'label': "cb17_survey__pip",
                            'name': "Review the Program Information Packet",
                            'body': """
<p>
  Download and carefully review the
  <a target="_blank"
     href="/static/programs/cb17/information_packet.pdf">Program Information
  Packet</a> for <em>{program_name}</em>. Distribute it to any colleagues who
  will need to be familiar with the program.
</p>
<p>
  The packet includes <strong>answers to most questions</strong> colleges
  have about the program.
</p>
""".format(program_name=program_name),
                            'action_statement': "I've read the packet",
                            'data_type': 'button',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__administration_method',
                            'name': "Administration Method: Independent or Supervised",
                            'body': """
<p>
  At this step, you will select how you would like the 30-minute module to be
  administered to students. Here is an overview of the options; for more
  information, please refer to &ldquo;In what context will you administer
  {program_name}?&rdquo; in the
  <a target="_blank" href="/static/programs/cb17/information_packet.pdf">
  Program Information Packet</a>.
</p>
""".format(program_name=program_name),
                            'action_statement': None,  # use default
                            'data_type': 'radio',
                            'select_options': [
                                {'value': 'prematriculation', 'label': """
Independent Completion: Students are provided a link to independently
participate in the program over the summer. Students will complete the program
on their own computers prior to arriving on campus.
"""},
                                {'value': 'orientation', 'label': """
Supervised Completion: Students participate in the program during a supervised,
in-person session as part of your new student orientation process. Students can
either use their own computers or university-provided computers.
"""},
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__portal_quiz',
                            'name': "Sign In Portal",
                            'body': """
<p>
  Here you will decide how you would like students to sign in to the program.
  Students can sign in through a custom portal created by your own
  college&rsquo;s IT department or through a generic portal at
  <a target="_blank" href="//www.comingtocollege.org">comingtocollege.org</a>.
  There are pros and cons to each approach listed below, and we encourage you
  to consult with your IT department to determine the best solution for your
  school. Your decision here will help us customize your students&rsquo;
  experience.
</p>
""",
                            'action_statement': None,  # use default
                            'data_type': 'radio',
                            'select_options': [

                                {'value': 'custom', 'label': """
<strong>Custom Portal</strong>. Choose this option if you intend to create a
custom portal with the help of your organization&rsquo;s internal network
authorization. You&rsquo;ll need to
<strong><a target="_blank" ng-href="/custom_portal_technical_guide/{[$ctrl.parentProjectCohort.short_uid]}">
Custom Portal Technical Guide</a></strong> with your IT team in order to create a
custom portal. We recommend sharing the instructions as early as possible to
determine how feasible this will be at your school.
<ul>
  <li>Pros: This is the best option because your college&rsquo;s network will
  be in control of students&rsquo; IDs and because everything can be automated,
  eliminating common errors.</li>
  <li>Cons: Requires your IT staff to construct a special web page, for which
  we provide
  <a target="_blank" ng-href="/custom_portal_technical_guide/{[$ctrl.parentProjectCohort.short_uid]}">detailed
  instructions</a>.
</ul>
"""},
                                {'value': 'name_or_id', 'label': """
<strong>Generic Portal</strong>. Choose this option if your IT team will not
set up a custom portal for your college.
<ul>
  <li>Pros: Less work for your IT department, as your IT staff will not need to
  set up a special web page.</li>
  <li>Cons: Increases the chances of identification errors as students enter
  the module, if they&rsquo;re unsure of or mistype their student IDs.</li>
</ul>
"""},
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__custom_portal_url',
                            'name': "Custom Portal URL",
                            'body': """
<nep-custom-portal-task portal-type="$ctrl.parentProjectCohort.portal_type"
                        task="$ctrl.task" task-complete="$ctrl.taskComplete()">
  <p ng-show="$parent.$ctrl.portalType === 'custom'">
    Great! You&rsquo;ve chosen to set up a custom portal for your organization.
    PERTS will direct students to it as part of the sign in process.
  </p>
  <p ng-show="$parent.$ctrl.portalType === 'custom'">
    Contact your IT team as early as possible, explain that your college is
    doing this program, and share the
    <a target="_blank" ng-href="/custom_portal_technical_guide/{[$ctrl.parentProjectCohort.short_uid]}">
    custom portal instructions</a> with them. They'll give you the
    URL of the portal that they create. Enter it below.
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
                            'label': 'cb17_survey__reserve_resources',
                            'name': "Reserve Resources",
                            'body': """
<p>
  You will need to reserve resources to complete the program as needed,
  particularly if you decide to implement in-person when students are on
  campus. This may include computer labs or laptop carts, or scheduled times
  and days for students to access the module. If you are implementing the
  program as an independent exercise over the summer, you should not need to
  reserve any resources for this step.
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
                            'label': 'cb17_survey__facilitator_quiz',
                            'name': "Orient Your Team",
                            'body': """
<p>
  This step reminds you to orient all colleagues and offices who will be
  involved in administering the program to students. Depending on how you
  choose to administer the program, this may include individuals responsible
  for sending out email invitations to students and promoting the program in
  orientation materials, or individuals who will administer the program to
  students in-person (e.g. instructors, computer lab staff, new student
  orientation staff). Obtaining buy-in from colleagues who will directly
  administer the program is critical to the program&rsquo;s success. They must
  all understand what they are supposed to do and why it is important.
</p>
<p>
  Prepare
  these individuals for their duties by reviewing the appropriate
  <a target="_blank"
     ng-href="/facilitator_instructions/{[$ctrl.parentProjectCohort.short_uid]}">
  Facilitator Instructions</a> (see the sections regarding
  &ldquo;independent&rdquo; or &ldquo;supervised&rdquo;) with them and by
  providing
  opportunities for them to ask questions and take part in planning. We also
  encourage you to provide all colleagues involved with the activity a copy of
  the <a target="_blank" href="/static/programs/cb17/communications_guidelines.pdf">
  Communications Guidelines</a>. You may also want to
  show them the
  <a href="//www.youtube.com/watch?v=YYJLMmWZiMQ" target="_blank">Program Video</a>
  and
  <a href="/static/programs/cb17/brochure.pdf" target="_blank">Brochure</a>.
</p>
""",
                            'action_statement': None,  # use default
                            # Although the task labels says "quiz", we want
                            # to communicate that "incorrect" options aren't
                            # _wrong_, they just aren't complete.
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
                            'label': 'cb17_survey__recruitment_source',
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
                    'name': "About Your College",
                    'label': 'cb17_survey__survey_params',
                    'body': """
<p>
  At this step you&rsquo;ll be asked to fill out a few questions to help us
  customize portions of the module to your school context.
</p>
""",
                    'tasks': [
                        # survey task
                        {
                            'label': 'cb17_survey__customize_full_name',
                            'name': "Customize Activity: Full School Name",
                            'body': """
<nep-survey-params-task
  task="$ctrl.task"
  survey-params-change="$ctrl.setAttachment(paramsJson);
                        $ctrl.validateInputForm(form);"
>
  <form name="$parent.$ctrl.surveyParamsForm" novalidate>

    <p>
      How would you like your school name to appear at the beginning of the
      program when students are first introduced to the activity? Typically we
      use the full, formal school name in these instances (e.g. &ldquo;University
      of Belonging&rdquo; instead of &ldquo;UoB&rdquo;).
    </p>
    <div class="input-field">
      <input id="schoolNameFull" type="text" name="school_name_full"
             ng-model="$parent.$ctrl.params.school_name_full"
             required>
      <label for="schoolNameFull"
             ng-class="{active: $parent.$ctrl.params.school_name_full}">
        Full School Name
      </label>
    </div>

  </form>
</nep-survey-params-task>
""",
                            'action_statement': "Save Responses",
                            'data_type': 'survey_params',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__customize_short_name',
                            'name': "Customize Activity: Short School Name",
                            'body': """
<nep-survey-params-task
  task="$ctrl.task"
  survey-params-change="$ctrl.setAttachment(paramsJson);
                        $ctrl.validateInputForm(form);"
>
  <form name="$parent.$ctrl.surveyParamsForm" novalidate>
    <p>
      Is there a less formal school name or nickname (e.g. &ldquo;UoB&rdquo;
      instead of &ldquo;University of Belonging&rdquo;) you would like to use
      more frequently throughout the activity?
    </p>
    <div class="input-field">
      <input id="schoolName" type="text" name="school_name"
             ng-model="$parent.$ctrl.params.school_name"
             required>
      <label for="schoolName"
             ng-class="{active: $parent.$ctrl.params.school_name}">
        Short School Name
      </label>
    </div>

  </form>
</nep-survey-params-task>
""",
                            'action_statement': "Save Responses",
                            'data_type': 'survey_params',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__customize_office',
                            'name': "Customize Activity: Sponsoring Office",
                            'body': """
<nep-survey-params-task
  task="$ctrl.task"
  survey-params-change="$ctrl.setAttachment(paramsJson);
                        $ctrl.validateInputForm(form);"
>
  <form name="$parent.$ctrl.surveyParamsForm" novalidate>
    <p>
      In our introductory materials, we like to share with students which
      office is putting on the activity. Examples from other schools include
      &ldquo;the Office of Undergraduate Studies&rdquo;, &ldquo;the Department
      of Academic Affairs&rdquo;, and &ldquo;Institutional Research.&rdquo;
      What office should we say is sponsoring the activity? Please enter it as
      you would like it to appear in the blank below:
    </p>
    <div class="input-field">
      <input id="sponsoringOffice" type="text" name="sponsoring_office"
             ng-model="$parent.$ctrl.params.sponsoring_office"
             required>
      <label for="sponsoringOffice"
             ng-class="{active: $parent.$ctrl.params.sponsoring_office}">
        Sponsoring Office
      </label>
      <blockquote class="quote">
        Example: A team from <strong>{[ $parent.$ctrl.params.sponsoring_office
        || '(name of office)' ]}</strong> is interested in students&rsquo;
        experiences in the transition to college.
      </blockquote>
    </div>
  </form>
</nep-survey-params-task>
""",
                            'action_statement': "Save Responses",
                            'data_type': 'survey_params',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__customize_email',
                            'name': "Customize Activity: Contact Email",
                            'body': """
<nep-survey-params-task
  task="$ctrl.task"
  survey-params-change="$ctrl.setAttachment(paramsJson);
                        $ctrl.validateInputForm(form);"
>
  <form name="$parent.$ctrl.surveyParamsForm" novalidate>

    <p>
      In case students have any questions or concerns, we would like to provide
      them with a contact email. Who can we tell students to contact if they
      have any questions or concerns related to the activity?
    </p>
    <div class="input-field">
      <input id="contactEmail" type="email" name="contact_email"
             ng-model="$parent.$ctrl.params.contact_email"
             required>
      <label for="contactEmail"
             ng-class="{active: $parent.$ctrl.params.contact_email}">
        Contact Email
      </label>
    </div>
  </form>
</nep-survey-params-task>
""",
                            'action_statement': "Save Responses",
                            'data_type': 'survey_params',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        # |    meaning     |      code      |
                        # |----------------|----------------|
                        # | pct_white      | p1             |
                        # | pct_asian      | p2             |
                        # | pct_black      | p3             |
                        # | pct_latinx     | p4             |
                        # | pct_native     | p5             |
                        # | pct_multi      | p6             |
                        # | pct_other      | p7             |
                        # | black_label    | preferredterm1 |
                        # | hispanic_label | preferredterm2 |
                        {
                            'label': 'cb17_survey__customize_demographics',
                            'name': "Customize Activity: School Demographics",
                            'body': """
<nep-survey-params-task
  task="$ctrl.task"
  survey-params-change="$ctrl.setAttachment(paramsJson);
                        $ctrl.validateInputForm(form);"
>
  <form name="$parent.$ctrl.surveyParamsForm" novalidate>
    <p>
      Please fill in the percentage of students <strong style="color: red">at
      your school</strong> who primarily identify with each racial/ethnic
      group. The following categories are meant to be mutually exclusive, i.e.
      all values should sum up to 100% and each student should be counted in
      only one category.
    </p>
    <table class="radio-table">
      <tbody>
        <tr>
          <td>African American/African/Black</td>
          <td>
            <div class="input-field inline">
              <input type="number" max="100" min="0" name="p3"
                     ng-model="$parent.$ctrl.params.p3"
              >
            </div>
            %
          </td>
        </tr>
        <tr>
          <td>American Indian/Alaskan Native</td>
          <td>
            <div class="input-field inline">
              <input type="number" max="100" min="0" name="p5"
                     ng-model="$parent.$ctrl.params.p5"
              >
            </div>
            %
          </td>
        </tr>
        <tr>
          <td>Asian/Asian American</td>
          <td>
            <div class="input-field inline">
              <input type="number" max="100" min="0" name="p2"
                     ng-model="$parent.$ctrl.params.p2"
              >
            </div>
            %
          </td>
        </tr>
        <tr>
          <td>Caucasian/White</td>
          <td>
            <div class="input-field inline">
              <input type="number" max="100" min="0" name="p1"
                     ng-model="$parent.$ctrl.params.p1"
              >
            </div>
            %
          </td>
        </tr>
        <tr>
          <td>Hispanic/Latino</td>
          <td>
            <div class="input-field inline">
              <input type="number" max="100" min="0" name="p4"
                     ng-model="$parent.$ctrl.params.p4"
              >
            </div>
            %
          </td>
        </tr>
        <tr>
          <td>Multiracial</td>
          <td>
            <div class="input-field inline">
              <input type="number" max="100" min="0" name="p6"
                     ng-model="$parent.$ctrl.params.p6"
              >
            </div>
            %
          </td>
        </tr>
        <tr>
          <td>Other groups</td>
          <td>
            <div class="input-field inline">
              <input type="number" max="100" min="0" name="p7"
                     ng-model="$parent.$ctrl.params.p7"
              >
            </div>
            %
          </td>
        </tr>
      </tbody>
    </table>
    <p>
      Sum of percents is: {[
        $parent.$ctrl.roundedSum(
          $parent.$ctrl.params.p3,
          $parent.$ctrl.params.p5,
          $parent.$ctrl.params.p2,
          $parent.$ctrl.params.p1,
          $parent.$ctrl.params.p4,
          $parent.$ctrl.params.p6,
          $parent.$ctrl.params.p7
        )
      ]}%.
      <span
        class="btn-instructions error"
        ng-show="$parent.$ctrl.roundedSum(
          $parent.$ctrl.params.p3,
          $parent.$ctrl.params.p5,
          $parent.$ctrl.params.p2,
          $parent.$ctrl.params.p1,
          $parent.$ctrl.params.p4,
          $parent.$ctrl.params.p6,
          $parent.$ctrl.params.p7
        ) != 100"
      >
        Does not sum to 100.
      </span>
    </p>
  </form>
</nep-survey-params-task>
""",
                            'action_statement': "Save Responses",
                            'data_type': 'survey_params',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__customize_group_terms',
                            'name': "Customize Activity: Preferred Terms",
                            'body': """
<nep-survey-params-task
  task="$ctrl.task"
  survey-params-change="$ctrl.setAttachment(paramsJson);
                        $ctrl.validateInputForm(form);"
>
  <form name="$parent.$ctrl.surveyParamsForm" novalidate>

    <p>
      Part of <em>{program_name}</em> involves students reading stories
      from sophomores, juniors, and seniors about their experience in the
      transition to college. These stories include race and gender attributions
      (e.g., Junior, African American male). Please select the preferred term
      for each of the following racial/ethnic groups on your campus.
    </p>
    <p>
      African American/Black
    </p>
    <p>
      <input id="blackLabelAA" type="radio" name="blackLabel"
             ng-model="$parent.$ctrl.params.preferredterm1"
             ng-value="'African American'"
             required>
      <label for="blackLabelAA">African American</label>
    </p>
    <p>
      <input id="blackLabelB" type="radio" name="blackLabel"
             ng-model="$parent.$ctrl.params.preferredterm1"
             ng-value="'Black'"
             required>
      <label for="blackLabelB">Black</label>
    </p>
    <p>
      Hispanic/Latino
    </p>
    <p>
      <input id="hispanicLabelH" type="radio" name="hispanicLabel"
             ng-model="$parent.$ctrl.params.preferredterm2"
             ng-value="'Hispanic'"
             required>
      <label for="hispanicLabelH">Hispanic</label>
    </p>
    <p>
      <input id="hispanicLabelLL" type="radio" name="hispanicLabel"
             ng-model="$parent.$ctrl.params.preferredterm2"
             ng-value="'Latino/Latina'"
             required>
      <label for="hispanicLabelLL">Latino/Latina</label>
    </p>
    <p>
      <input id="hispanicLabelX" type="radio" name="hispanicLabel"
             ng-model="$parent.$ctrl.params.preferredterm2"
             ng-value="'Latinx'"
             required>
      <label for="hispanicLabelX">Latinx</label>
    </p>
  </form>
</nep-survey-params-task>
""".format(program_name=program_name),
                            'action_statement': "Save Responses",
                            'data_type': 'survey_params',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__expected_invitations',
                            'name': "Expected Invitations",
                            'body': """
<p>
  Now you&rsquo;ll be asked to answer a few questions to help us understand how
  you plan to implement this program and how it fits in with other efforts at
  your school.
</p>
<p>
  How many students do you plan to invite?
</p>
""",
                            'action_statement': "Submit",
                            'data_type': 'input:number',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__expected_participants',
                            'name': "Expected Participation",
                            'body': """
<p>
  How many students do you expect to participate?
</p>
""",
                            'action_statement': "Submit",
                            'data_type': 'input:number',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__expected_launch_date',
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
                            'label': 'cb17_survey__invitation_plan',
                            'name': "Method of Invitation",
                            'body': """
<p>
  How do you plan to invite students to participate in the program? This could
  include emails, including on new student orientation checklists, promoting on
  websites and online dashboards, or other methods.
</p>
""",
                            'action_statement': None,
                            'data_type': 'textarea',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__other_assessments',
                            'name': "Other Surveys and Assessments",
                            'body': """
<p>
  What other major assessments and surveys around students&rsquo; experiences
  of college or first year students&rsquo; transition to college does your
  school send out?
</p>
""".format(program_name=program_name),
                            'action_statement': None,
                            'data_type': 'textarea',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__other_assessments_timing',
                            'name': "Other Surveys and Assessments: Timing",
                            'body': """
<p>
  When do you typically send out these assessments/surveys?
</p>
""".format(program_name=program_name),
                            'action_statement': None,
                            'data_type': 'textarea',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__other_belonging',
                            'name': "Other Belonging Efforts",
                            'body': """
<p>
  What efforts does your school employ to promote a sense of belonging on
  campus, improve student achievement and completion, and/or foster diversity
  and inclusion? We are particularly interested in learning about other
  programs administered at your school related to student mindsets and
  psychological wellbeing, as well as efforts to reduce the achievement gap
  between students from advantaged backgrounds (e.g. continuing-generation college-goers, not members of
  ethnic/racial minorities) and students from disadvantaged backgrounds (e.g. first-generation
  college-goers, members of ethnic/racial minorities) at your institution.
</p>
""".format(program_name=program_name),
                            'action_statement': None,
                            'data_type': 'textarea',
                            'non_admin_may_edit': True,
                        },
                    ],
                },
                # survey checkpoint
                {
                    'name': "Quiz",
                    'label': 'cb17_survey__quiz',
                    'body': """
<p>
  <em>{program_name}</em> is a research-based program, and it should be
  administered following a specific protocol. Failing to follow the protocol
  could cause the program to become ineffective. Take this quiz to test your
  knowledge of the appropriate administration protocol so that you can be sure
  you are following this protocol appropriately. You might also want to go over
  these questions with the program facilitators.
</p>
<p>
  You may also learn more about the research behind social-belonging
  interventions by reading this
  <a target="_blank"
     href="http://gregorywalton-stanford.weebly.com/uploads/4/9/4/4/49448111/yeagerwalton2011.pdf">
  review article by David Yeager and Greg Walton</a>.
</p>
""".format(program_name=program_name),
                    'tasks': [
                        # survey task
                        {
                            'label': 'cb17_survey__instruction_framing',
                            'name': "Describing the Program in Invitations",
                            'body': """
<p>
  When students are invited to participate in %s
  the program will always be described using the wording in the
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
                            'label': 'cb17_survey__code_expiration',
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
                            'label': 'cb17_survey__quiz_instruction_framing',
                            'name': "Quiz: Describing the Student Module",
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
                                    "This is a welcome activity that is part "
                                    "of your college orientation."
                                )},
                                {"value": "incorrect_help", "label": (
                                    "This is an activity to help students "
                                    "develop a sense of belonging."
                                )},
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__quiz_find_code',
                            'name': "Quiz: Participation Code",
                            'body': """
<p>
Where can you find your college&rsquo;s participation code?
</p>
""".format(program_name=program_name),
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
                                    "perts.net/social-belonging"
                                )}
                            ],
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__quiz_expiration',
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
                            'label': 'cb17_survey__quiz_frequency',
                            'name': "Quiz: Participation Frequency",
                            'body': """
<p>
How often should a student complete the program?
</p>
""".format(program_name=program_name),
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
                            'label': 'cb17_survey__quiz_colleague_framing',
                            'name': "Quiz: Orientation Resources",
                            'body': """
<p>
We provide all of the following resources for introducing the program to your
colleagues, except for:
</p>
""".format(program_name=program_name),
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
                                {"value": "incorrect_comm", "label": (
                                    "Communications guidelines"
                                )}
                            ],
                            'non_admin_may_edit': True,
                        },
                    ],
                },

                # survey checkpoint
                {
                    'name': "Launch and Monitor",
                    'label': 'cb17_survey__monitor_1',
                    'body': """
<p>
  Hooray! This page will let you launch <em>{program_name}</em>,
  track students&rsquo; participation, and view the program&rsquo;s results.
</p>
""".format(program_name=program_name),
                    'tasks': [
                        # survey task
                        {
                            'label': 'cb17_survey__monitor_1',
                            'name': "Monitor Module",
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
      Launched! You&rsquo;re ready to go. Your students can participate any time
      between
      {[$parent.$ctrl.cohort.participationOpenDate | date:'longDate']} and
      {[$parent.$ctrl.cohort.displayCloseDate | date:'longDate']}.
      Just follow the
      <a
        target="_blank"
        ng-href="/facilitator_instructions/{[$ctrl.parentProjectCohort.short_uid]}"
      >
        Facilitator Instructions
      </a>
      to invite them. If students are participating on their own, you can provide
      them with the
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
      &ldquo;We&rsquo;ve Finished The Module&rdquo; below.
    </p>
  </div>
  <p ng-show="$ctrl.task.attachment === 'complete'">
    You marked this module as complete. Students can still participate if they
    need to make up a missed session.
  </p>
</nep-monitor-survey-task>
""",
                            'action_statement': "We've Finished The Module",
                            'data_type': 'monitor',
                            'non_admin_may_edit': True,
                        },
                        # survey task
                        {
                            'label': 'cb17_survey__report_1',
                            'name': "Final Report",
                            'body': """
<p>
  In November, we will make available a report showing the impact of
  the program on survey outcomes at your college and across other participating
  colleges. Return here to download the report once your students have
  completed the program.
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
