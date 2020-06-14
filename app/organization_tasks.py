"""Defines tasks all orgs must do to legitimize themselves with PERTS.

Only organizations have task lists that aren't within a program, and they're
uniform across all organizations.
"""

tasklist_template = [
    # Organization checkpoint
    {
        'name': 'Organization',
        'label': 'organization__main',
        'body': """
<p>
  Tell us about your team! The tasks below will help you invite other staff at
  your college who will oversee the program. It will also let you name the main
  point of contact for your organization.
</p>
""",
        'tasks': [
            {
                'label': 'organization__invite',
                'name': "Invite Colleagues",
                # Always wrap text in a block level element, e.g. <p>
                'body': """
<p>
  Send invitations to any colleagues who will be running
  <em>{[ $ctrl.program.name ]}</em>. This will give them access to this
  dashboard so they can help administer the program. You can return here
  anytime to invite more colleagues or
  <a ui-sref="dashboard.organizationUsers(
       {projectCohortId: $ctrl.parentProjectCohort.short_uid})
  ">manage your team</a>.
</p>
<p>
  You only need to invite colleagues who will be managing the tasks and
  settings of your program. Later tasks will walk you through how to involve
  other collaborators, if necessary.
</p>
<p nep-organization-invitation organization="$ctrl.parentOrganization"></p>
""",
                # Do NOT wrap in a block level element.
                'action_statement': (
                    "I'm Done Sending Invitations"
                ),
                'data_type': 'button',
                'non_admin_may_edit': True,
            },
            {
                'label': 'organization__liaison',
                'name': "Organization Liaison",
                # Always wrap text in a block level element, e.g. <p>
                'body': """
<p>
  The liaison, named below, will be the main point of contact for your
  organization. They will be publicly listed at neptune.perts.net so that
  others can contact them with questions. We recommend you choose the liaison
  based on who will manage the implementation of
  <em>{[ $ctrl.program.name ]}</em>. You can return here and change the liaison
  at any time.
</p>
<nep-liaison-task-setter task-attachment="$ctrl.task.attachment"
                         liaison-id="$ctrl.parentOrganization.liaison_id"
                         set-liaison="$ctrl.setAttachment(liaisonId)">
</nep-liaison-task-setter>
""",
                # Do NOT wrap in a block level element.
                'action_statement': (
                    "Save Selection"
                ),
                'data_type': 'radio',
                # When this is a string, it's evaluated as an angular
                # expression. The Liaison service should be injected in the
                # Task directive.
                'select_options': '$ctrl.Liaison.options($ctrl.parentOrganization.uid)',
                'non_admin_may_edit': True,
            },
            {
                'label': 'organization__approval',
                'name': "Organization Validation",
                'body': """
<p ng-if="$ctrl.parentOrganization.status === 'rejected'">
  Your PERTS Account Manager has determined your organization doesn&rsquo;t
  meet requirements and will reach out to explain this decision within 7 days.
</p>
<p ng-if="$ctrl.parentOrganization.status !== 'rejected'">
  Your PERTS Account Manager will reach out if there are any problems with
  your organization within 7 days. Otherwise, you're good to go!
</p>
<p>
  Account Manager: you may enter the PERTS Organization ID here.
</p>
""",
                # Do NOT wrap in a block level element.
                'action_statement': (
                    "Approve Organization"
                ),
                'data_type': 'input:text',
                'non_admin_may_edit': False,
                'data_admin_only_visible': True,
                'initial_values': {
                  'status': 'complete',
                },
            },
        ],
    },
]
