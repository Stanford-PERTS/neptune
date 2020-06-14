import deepRetrieveObjectProperty from 'utils/deepRetrieveObjectProperty';

const emailService = ngModule => {
  ngModule.service('Email', Email);

  function Email($q, $http, $resource, hostingDomain) {
    const EmailResource = $resource(`//${hostingDomain}/api/emails/:id`, {
      id: '@uid',
    });

    /**
     * Stored template data
     */
    const templateCache = [];

    /**
     * GET the available Mandrill templates from API.
     * @return {Array} Mandrill templates array
     */
    EmailResource.getMandrillTemplates = function () {
      return $http({
        method: 'GET',
        url: `//${hostingDomain}/api/mandrill_templates`,
      })
        .then(response => response.data)
        .then(EmailResource.storeMandrillTemplates);
    };

    /**
     * Store Mandrill templates in `data`.
     * @param  {Array} templates Mandrill templates data as returned by API
     * @return {Array}           Mandrill templates array
     */
    EmailResource.storeMandrillTemplates = function (templates) {
      // note: we set length to 0 and push onto the array instead of using a
      // map to create a new array since views may already be referencing
      // the `data` array, and templateCache = templates.map would break the
      // references

      // make sure initial fetch starts clean
      templateCache.length = 0;

      // push data onto `data` array
      templates.forEach(t => {
        templateCache.push(t);
      });

      return templates;
    };

    /**
     * Creates a template object for use in rendering a preview of the selected
     * Mandrill template with liaison (projectDataRow) data. This function
     * assumes that `getMandrillTemplates` has already run.
     * @param  {String} slug    Mandrill template slug
     * @param  {Object} replace projectDataRow source of data
     * @param  {Object} templateContentMap mapping of replacement tokens into
     *                                     the projectDataRow object
     * @return {Object}
     */
    EmailResource.previewMandrillTemplate = function (
      slug,
      replace,
      templateContentMap,
    ) {
      const template = templateCache.find(t => t.slug === slug);
      let templateHtml = template.code;

      angular.forEach(templateContentMap, (key, data_path) => {
        const replaceProp = deepRetrieveObjectProperty(replace, data_path);
        if (replaceProp) {
          // We need to create a RegExp so that we can both dynamically generate
          // the regular expression using a variable (`key`) and also make the
          // regular expression search globally (`g`).
          const keyRegex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
          templateHtml = templateHtml.replace(keyRegex, replaceProp);
        }
      });

      return {
        emailTo: replace.liaison.email,
        nameTo: replace.liaison.name,
        emailFrom: template.from_email,
        nameFrom: template.from_name,
        emailSubject: template.publish_subject,
        slug: template.slug,
        templateHtml,
      };
    };

    return EmailResource;
  }
};

export default emailService;
