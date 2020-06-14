from string import Template


class PctTemplate(Template):
    delimiter = '%'


fragments = {
    'user_fields': '''
        fragment user_fields on User {
            assc_organizations
            assc_projects
            created
            deleted
            email
            google_id
            hashed_password
            last_login
            modified
            name
            notification_option
            owned_data_requests
            owned_data_tables
            owned_organizations
            owned_programs
            owned_projects
            phone_number
            role
            short_uid
            uid
            user_type
        }
    ''',
    'project_cohort_fields': '''
        fragment project_cohort_fields on ProjectCohort {
            code
            cohort_label
            completed_report_task_ids
            created
            custom_portal_url
            data_export_survey
            deleted
            expected_participants
            liaison_id
            modified
            organization_id
            portal_message
            portal_type
            program_label
            project_id
            short_uid
            status
            survey_params
            uid
        }
    ''',
    'checkpoint_fields': '''
        fragment checkpoint_fields on Checkpoint {
            body
            cohort_label
            label
            name
            ordinal
            organization_id
            parent_id
            parent_kind
            program_label
            project_cohort_id
            project_id
            short_uid
            status
            survey_id
            task_ids
            uid
        }
    ''',
    'task_fields': '''
        fragment task_fields on Task {
            action_statement
            attachment
            body
            checkpoint_id
            completed_by_id
            completed_by_name
            completed_date
            counts_as_program_complete
            created
            data_admin_only_visible
            data_type
            deleted
            disabled
            due_date
            label
            modified
            name
            non_admin_may_edit
            ordinal
            parent_id
            program_label
            select_options
            short_parent_id
            status
            uid
        }
    ''',
    'organization_fields': '''
        fragment organization_fields on Organization {
            country
            created
            deleted
            google_maps_place_id
            ipeds_id
            liaison_id
            mailing_address
            modified
            name
            nces_district_id
            nces_school_id
            notes
            ope_id
            phone_number
            poid
            postal_code
            short_uid
            state
            status
            uid
            website_url
        }
    ''',
    'program_cohort_fields': '''
        fragment program_cohort_fields on ProgramCohort {
            close_date
            label
            name
            open_date
            program_description
            program_label
            program_name
            registration_close_date
            registration_open_date
        }
    ''',
    'project_fields': '''
        fragment project_fields on Project {
            account_manager_id
            created
            deidentification_method
            deleted
            last_active
            liaison_id
            loa_notes
            modified
            organization_id
            organization_name
            organization_status
            priority
            program_description
            program_label
            program_name
            short_uid
            uid
        }
    ''',
    'survey_fields': '''
        fragment survey_fields on Survey {
            cohort_label
            created
            deleted
            liaison_id
            modified
            name
            ordinal
            organization_id
            program_label
            project_cohort_id
            project_id
            short_uid
            status
            uid
        }
    ''',
}


single_tasklist = PctTemplate('''
    query Tasklist($uid: String) {
        project_cohort(uid: $uid) {
            ...project_cohort_fields
            surveys {
                ...survey_fields
            }
            checkpoints {
                ...checkpoint_fields
                tasks {
                    ...task_fields
                }
            }
            liaison {
                ...user_fields
            }
            organization {
                ...organization_fields
                liaison {
                    ...user_fields
                }
                users {
                    ...user_fields
                }
            }
            program_cohort {
                ...program_cohort_fields
            }
            project {
                ...project_fields
            }
        }
    }
    %{project_cohort_fields}
    %{survey_fields}
    %{checkpoint_fields}
    %{task_fields}
    %{user_fields}
    %{organization_fields}
    %{program_cohort_fields}
    %{project_fields}
''').substitute(fragments)


dashboard = PctTemplate('''
    query Dashboard(
        $organization_id: String,
        $program_label: String,
        $user_id: String,
    ) {
        project_cohorts(
            organization_id: $organization_id,
            program_label: $program_label,
            user_id: $user_id,
        ) {
            ...project_cohort_fields
            checkpoints {
                ...checkpoint_fields
            }
            organization {
                ...organization_fields
            }
            program_cohort {
                ...program_cohort_fields
            }
            project {
                ...project_fields
            }
            surveys {
                ...survey_fields
            }
        }
    }
    %{project_cohort_fields}
    %{checkpoint_fields}
    %{organization_fields}
    %{program_cohort_fields}
    %{project_fields}
    %{survey_fields}
''').substitute(fragments)


program_cohort_dashboard = '''
    query ProgramCohortDashboard(
        $program_label: String!,
        $cohort_label: String!,
    ) {
        program_cohort(
            program_label: $program_label,
            cohort_label: $cohort_label,
        ) {
            close_date
            label
            name
            open_date
            program_description
            program_label
            program_name
            registration_close_date
            registration_open_date
        }

        project_cohorts(
            program_label: $program_label,
            cohort_label: $cohort_label,
        ) {
            organization_id
            short_uid
            status
            uid
            checkpoints {
                parent_kind
                status
                survey_id
                uid
            }
            organization {
                status
            }
            project {
                organization_name
                priority
                last_active
                loa_notes
                uid
            }
            surveys {
                name
                ordinal
                status
                uid
            }
        }
    }
'''
