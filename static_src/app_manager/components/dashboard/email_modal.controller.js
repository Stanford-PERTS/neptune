import deepRetrieveObjectProperty from 'utils/deepRetrieveObjectProperty';

(function () {
  'use strict';

  window.ngModule.controller(
    'EmailModalController',
    function EmailModalController(
      $scope,
      $sce,
      $q,
      Email,
      projectDataRows,
      close,
    ) {
      // These are the values you can use in writing interpolations in
      // templates; they need to go to mandrill so the email can be built.
      // Conveniently we also have a function for the using the same syntax to
      // find properties of a data row.
      const templateContentMap = {
        'liaison.email': 'liaison_email',
        'liaison.name': 'liaison_name',
        'liaison.phone_number': 'liaison_phone_number',
        'organization.country': 'organization_country',
        'organization.mailing_address': 'organization_mailing_address',
        'organization.name': 'organization_name',
        'organization.phone_number': 'organization_phone_number',
        'organization.poid': 'organization_poid',
        'organization.postal_code': 'organization_postal_code',
        'organization.state': 'organization_state',
        'organization.status': 'organization_status',
        'organization.website_url': 'organization_website_url',
        'program_cohort.program_label': 'program_label',
        'program_cohort.program_name': 'program_name',
        'program_cohort.program_description': 'program_description',
        'program_cohort.name': 'cohort_name',
        'program_cohort.open_date': 'cohort_participation_open_date',
        'program_cohort.close_date': 'cohort_participation_close_date',
        'program_cohort.registration_open_date': 'cohort_registration_open_date',
        'program_cohort.registration_close_date': 'cohort_registration_close_date',
      };

      /**
       * Sets the `email` string to either tsv or csv.
       */
      $scope.formatEmails = function () {
        if ($scope.emailDisplayFormat === 'mandrill') {
          $scope.emails = '';

          Email.getMandrillTemplates().then(templates => {
            $scope.emailTemplates = templates;
          });
        } else if ($scope.emailDisplayFormat === 'tsv') {
          $scope.emails = '';
          projectDataRows.forEach(p => {
            $scope.emails += `${p.liaison.name}\t${p.liaison.email}\t${
              p.organization.name
            }\n`;
          });
        } else if ($scope.emailDisplayFormat === 'csv') {
          $scope.emails = '';
          projectDataRows.forEach(p => {
            $scope.emails += `${p.liaison.email},`;
          });
        }
      };

      /**
       * Loads the selected email template into $scope, replacing the template
       * expressions with the selected liaison data.
       * @param  {[type]} slug             The Mandrill template slug
       * @param  {Number} [liaisonIndex=0] The projectDataRow index associated
       *                                   with the selected liaison
       * @return {undefined}
       * @affects $scope.template
       * @affects $scope.numberOfEmails
       */
      $scope.selectedEmailTemplateChanged = function (slug, liaisonIndex = 0) {
        if (projectDataRows[liaisonIndex]) {
          $scope.template = Email.previewMandrillTemplate(
            slug,
            projectDataRows[liaisonIndex],
            templateContentMap,
          );
          $scope.template.templateHtml = $sce.trustAsHtml(
            $scope.template.templateHtml,
          );
        }
      };

      /**
       * Switches the currently selected liaison (projectDataRow) index. Then
       * invokes selectedEmailTemplateChanged to update the email preview.
       * @param  {Number} direction Index change direction [1, -1]
       * @return {undefined}
       * @affects $scope.liaisonPreviewIndex
       */
      $scope.selectLiaisonPreview = function (direction) {
        $scope.liaisonPreviewIndex += direction;

        if ($scope.liaisonPreviewIndex < 0) {
          $scope.liaisonPreviewIndex = projectDataRows.length - 1;
        }

        if ($scope.liaisonPreviewIndex > projectDataRows.length - 1) {
          $scope.liaisonPreviewIndex = 0;
        }

        $scope.selectedEmailTemplateChanged(
          $scope.selectedEmailTemplate,
          $scope.liaisonPreviewIndex,
        );
      };

      /**
       * Send emails to selected liaisons using selected template.
       */
      $scope.sendEmails = function () {
        $scope.uiSendEmails = true;
        $scope.busy = true;
        $scope.numEmailsSent = 0;

        const emailPromises = projectDataRows.map(row => {
          // Build the template content from the data row.
          const templateContent = {};
          angular.forEach(templateContentMap, (key, data_path) => {
            templateContent[key] = deepRetrieveObjectProperty(row, data_path);
          });

          // Make a new email resource.
          const email = new Email({
            to_address: row.liaison.email,
            mandrill_template: $scope.template.slug,
            mandrill_template_content: templateContent,
          });

          // POST it to send.
          return email
            .$save()
            .then(() => ($scope.numEmailsSent += 1))
            .catch(console.error);
        });

        $q.all(emailPromises).then(() => {
          $scope.busy = false;
        });
      };

      /**
       * Closes the modal window.
       */
      $scope.close = function () {
        close();

        // We also need to clean up $scope
        $scope.$destroy();
      };

      /**
       * The number of emails that would be sent (liaison selected).
       * @type {Number}
       */
      $scope.numberOfEmails = projectDataRows.length;

      /**
       * Which liaison will we use to place into the email template preview.
       * @type {Number}
       */
      $scope.liaisonPreviewIndex = 0;

      /**
       * Default to tsv format.
       * @type {String}
       */
      $scope.emailDisplayFormat = 'mandrill';

      /**
       * Call on load so that we format the emails field by the default.
       */
      $scope.formatEmails();
    },
  );
})();
