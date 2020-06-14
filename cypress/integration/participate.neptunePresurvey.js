import { createHgProgram, createHgCode } from 'mocks/program';
import { createPd } from 'mocks/participantData';

const toUrlCode = code => code.replace(/ /g, '-');

const hgProgram = createHgProgram();
const hgCode = createHgCode();

const org = {
  uid: 'Organization_001',
  name: 'Chris Test U',
};

const surveyHg1 = { uid: 'Survey_hg1', ordinal: 1 };
const surveyHg2 = { uid: 'Survey_hg2', ordinal: 2 };

const newUser = {
  uid: 'Participant_new',
  name: 'new-user',
};

const existingUser = {
  uid: 'Particpant_existing',
  name: 'existing-user',
};

const getLinkPd = options =>
  createPd({
    key: 'link',
    value: `https://www.example.com/${options.survey_id}`,
    ...options,
  });

function mockCodes() {
  // Portal queries the org to send its name to Q.
  cy.route({
    method: 'GET',
    url: '/api/organizations/**',
    response: org,
  });

  // Program configs.
  cy.route({
    method: 'GET',
    url: '/api/programs/hg17',
    response: hgProgram,
  }).as('loadHgProgram');

  // ProjectCohorts a.k.a. codes
  cy.route({
    method: 'GET',
    url: `/api/codes/${toUrlCode(hgCode.code)}`,
    response: hgCode,
  }).as('loadHgCode');

  // Surveys are needed if we're going to write new pd for the user.
  cy.route({
    method: 'GET',
    url: `/api/surveys?project_cohort_id=${hgCode.uid}`,
    response: [surveyHg1, surveyHg2],
  });
  cy.route({
    method: 'GET',
    url: `/api/surveys?ordinal=1&project_cohort_id=${hgCode.uid}`,
    response: [surveyHg1],
  });
  cy.route({
    method: 'GET',
    url: `/api/surveys?ordinal=2&project_cohort_id=${hgCode.uid}`,
    response: [surveyHg2],
  });

  // Checking for the new user should always return empty set.
  cy.route({
    method: 'GET',
    url: `/api/participants?*name=${newUser.name}*`,
    response: [],
  });

  // Existing user.
  cy.route({
    method: 'GET',
    url: `/api/participants?*name=${existingUser.name}*`,
    response: [existingUser],
  });

  // N.B. We do need to also mock a POST for new participants, but that's done
  // per-test, since it changes a lot.

  // "Unique link"
  cy.route({
    method: 'POST',
    url: `/api/survey_links/${hgProgram.label}/1/get_unique`,
    response: {
      program_label: hgProgram.label,
      survey_ordinal: 1,
      url: getLinkPd({ survey_id: surveyHg1.uid }).value,
    },
  });
  cy.route({
    method: 'POST',
    url: `/api/survey_links/${hgProgram.label}/2/get_unique`,
    response: {
      program_label: hgProgram.label,
      survey_ordinal: 2,
      url: getLinkPd({ survey_id: surveyHg2.uid }).value,
    },
  });

  // "New" and "Invalid" users have no pd.
  cy.route({
    method: 'GET',
    url: '/api/participants/*/data',
    response: [],
  });

  // "Exisiting" user has link pd and progress for survey 1.
  cy.route({
    method: 'GET',
    url: `/api/participants/${existingUser.uid}/data`,
    response: [
      getLinkPd({ survey_id: surveyHg1.uid, project_cohort_id: hgCode.uid }),
      createPd({
        participant_id: existingUser.uid,
        project_cohort_id: hgCode.uid,
        survey_id: surveyHg1.uid,
        survey_ordinal: 1,
        key: 'progress',
        value: '100',
      }),
    ],
  }).as('getPdForExisting');
}

describe('skipCheck module', () => {
  beforeEach(() => {
    cy.on('window:before:load', win => {
      // Don't actually redirect, switch on the debugging behavior so we can
      // check where we _would_ have gone.
      win.debugRedirect = true;
    });
    cy.server();
    mockCodes();

    // All these tests only post the newUser.
    cy.route({
      method: 'POST',
      url: `/api/participants`,
      response: newUser,
    }).as('postUser');
  });

  it("does nothing if you ask for session 1 and haven't done it yet", () => {
    cy.route({
      method: 'POST',
      url: '/api/participants/*/data/link',
      response: getLinkPd({ survey_id: surveyHg1.uid }),
    }).as('postLink');

    cy.visit(`/participate/portal/${toUrlCode(hgCode.code)}/1/${newUser.name}`);

    cy.get('#redirect-to')
      // The survey id should be in the URL path, just like in Qualtrics.
      .contains(getLinkPd({ survey_id: surveyHg1.uid }).value)
      // Our survey id should also be in the query string.
      .contains(`survey_id=${surveyHg1.uid}`);
  });

  it('does nothing if ask for 2 and have already done 1', () => {
    cy.route({
      method: 'POST',
      url: '/api/participants/*/data/link',
      response: getLinkPd({ survey_id: surveyHg2.uid }),
    }).as('postLink');

    cy.visit(
      `/participate/portal/${toUrlCode(hgCode.code)}/2/${existingUser.name}`,
    );

    cy.get('#redirect-to')
      // The survey id should be in the URL path, just like in Qualtrics.
      .contains(getLinkPd({ survey_id: surveyHg2.uid }).value)
      // Our survey id should also be in the query string.
      .contains(`survey_id=${surveyHg2.uid}`);
  });

  it('redirects if you choose to switch to session 1', () => {
    // The participant requests session 2, which will cause the presurvey to
    // set up a unique link for survey 2.
    cy.route({
      method: 'POST',
      url: '/api/participants/*/data/link',
      response: getLinkPd({ survey_id: surveyHg2.uid }),
    }).as('postLink');

    cy.visit(`/participate/portal/${toUrlCode(hgCode.code)}/2/${newUser.name}`);
    cy.wait('@postLink').then(xhr => {
      expect(xhr.request.body.survey_id).to.equal(surveyHg2.uid);
    });

    // The next link we respond with should be for survey 1.
    cy.route({
      method: 'POST',
      url: '/api/participants/*/data/link',
      response: getLinkPd({ survey_id: surveyHg1.uid }),
    }).as('postLink');

    // But they skipped session 1, so it will display the skipCheck.
    cy.get('form[name="skipForm"]').should('be.visible');

    // Have the participant admit they skipped, which means they'll switch to
    // doing session 1.
    cy.get('input[data-test="theyDid1-false"]').click();
    cy.get('form[name="skipForm"] button[type="submit"]').click();

    cy.wait('@postLink').then(xhr => {
      expect(xhr.request.body.survey_id).to.equal(surveyHg1.uid);
    });

    cy.get('#redirect-to')
      // The survey id should be in the URL path, just like in Qualtrics.
      .contains(getLinkPd({ survey_id: surveyHg1.uid }).value)
      // Our survey id should also be in the query string.
      .contains(`survey_id=${surveyHg1.uid}`);
  });

  it('redirects if you choose to stay with session 2', () => {
    // We'll have the participant request session 2 first. This should cause
    // the presurvey to set up a unique link for survey 2.
    cy.route({
      method: 'POST',
      url: '/api/participants/*/data/link',
      response: getLinkPd({ survey_id: surveyHg2.uid }),
    }).as('postLink');

    cy.visit(`/participate/portal/${toUrlCode(hgCode.code)}/2/${newUser.name}`);
    cy.wait('@postLink').then(xhr => {
      expect(xhr.request.body.survey_id).to.equal(surveyHg2.uid);
    });

    // But they skipped session 1, so it will display the skipCheck.
    cy.get('form[name="skipForm"]').should('be.visible');

    // Have the participant deny they skipped, which means they'll continue
    // with session 2.
    cy.get('input[data-test="theyDid1-true"]').click();
    cy.get('form[name="skipForm"] button[type="submit"]').click();

    cy.get('#redirect-to')
      // The survey id should be in the URL path, just like in Qualtrics.
      .contains(getLinkPd({ survey_id: surveyHg2.uid }).value)
      // Our survey id should also be in the query string.
      .contains(`survey_id=${surveyHg2.uid}`);
  });
});
