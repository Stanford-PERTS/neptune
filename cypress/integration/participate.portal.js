import {
  createCgProgram,
  createHgProgram,
  createMsetProgram,
} from 'mocks/program';

const toUrlCode = (code) => code.replace(/ /g, '-');

const org = {
  uid: 'Organization_001',
  name: 'Chris Test U',
};

const CGProgram = createCgProgram();
const HGProgram = createHgProgram();
const MSETProgram = createMsetProgram();

const CGCode = {
  uid: 'ProjectCohort_cool-cat',
  code: 'cool cat',
  program_label: 'cg17',
  cohort_label: '2018',
};

const CGClosedCode = {
  uid: 'ProjectCohort_old-cobra',
  code: 'old cobra',
  program_label: 'cg17',
  cohort_label: '2017_spring',
};

const CGCodeCustom = {
  uid: 'ProjectCohort_custom-cow',
  code: 'custom cow',
  portal_type: 'custom',
  program_label: 'cg17',
  cohort_label: '2018',
  custom_portal_url: 'http://www.example.com',
};

const HGCode = {
  uid: 'ProjectCohort_trout-viper',
  code: 'trout viper',
  program_label: 'hg17',
  cohort_label: '2018',
};

const MSETCode = {
  uid: 'ProjectCohort_feral-feline',
  code: 'feral feline',
  program_label: MSETProgram.label,
  cohort_label: '2019',
  portal_type: MSETProgram.default_portal_type,
};

const survey = {
  uid: 'Survey_1',
};

const newUser = {
  uid: 'Participant_new',
  name: 'new-user',
};

const existingUser = {
  uid: 'Participant_existing',
  name: 'existing-user',
};

const linkPd = {
  uid: 'ParticipantData_link',
  key: 'link',
  value: 'https://www.example.com/',
};

const sawDemographicsPd = {
  uid: 'ParticipantData_sawDemographics',
  key: 'saw_demographics',
  value: '2019-1-1',
};

const sawBaselinePd = {
  uid: 'ParticipantData_sawDemographics',
  key: 'saw_demographics',
  value: '2019-1-1',
};

function mockCodes() {
  cy.server();

  // Portal queries the org to send its name to Q.
  cy.route({
    method: 'GET',
    url: '/api/organizations/**',
    response: org,
  });

  // Program configs.
  cy.route({
    method: 'GET',
    url: '/api/programs/cg17',
    response: CGProgram,
  }).as('loadCGProgram');
  cy.route({
    method: 'GET',
    url: '/api/programs/hg17',
    response: HGProgram,
  }).as('loadHGProgram');
  cy.route({
    method: 'GET',
    url: '/api/programs/mset19',
    response: MSETProgram,
  }).as('loadMSETProgram');

  // ProjectCohorts a.k.a. codes
  cy.route({
    method: 'GET',
    url: '/api/codes/cool-cat',
    response: CGCode,
  }).as('loadCGCode');

  cy.route({
    method: 'GET',
    url: `/api/codes/${CGClosedCode.code.replace(' ', '-')}`,
    response: CGClosedCode,
  });

  cy.route({
    method: 'GET',
    url: '/api/codes/custom-cow',
    response: CGCodeCustom,
  }).as('loadCGCodeCustom');
  cy.route({
    method: 'GET',
    url: '/api/codes/bad-bear',
    status: 404,
    response: '',
  }).as('badCode');

  cy.route({
    method: 'GET',
    url: '/api/codes/trout-viper',
    response: HGCode,
  }).as('loadHGCode');

  cy.route({
    method: 'GET',
    url: '/api/codes/feral-feline',
    response: MSETCode,
  }).as('loadMSETCode');

  // Surveys are needed if we're going to write new pd for the user.
  cy.route({
    method: 'GET',
    url: '/api/surveys**',
    response: [survey],
  });

  // Checking for the new user should always return empty set.
  cy.route({
    method: 'GET',
    url: `/api/participants?name=${newUser.name}`,
    response: [],
  });

  // Existing user.
  cy.route({
    method: 'GET',
    url: `/api/participants?name=${existingUser.name}`,
    response: [existingUser],
  });

  // Mock the result of posting the new user.
  cy.route({
    method: 'POST',
    url: '/api/participants',
    response: newUser,
  });

  // "Unique link"
  cy.route({
    method: 'POST',
    url: '/api/survey_links/*/1/get_unique',
    response: {
      url: linkPd.value,
      survey_ordinal: 1,
      program_label: 'demo-program',
    },
  });

  // An existing user's pd must always contain, at minimum, a link pd.
  cy.route({
    method: 'GET',
    url: '/api/participants/*/data**',
    response: [linkPd],
  });

  cy.route({
    method: 'GET',
    url: `/api/participants/${existingUser.uid}/data**`,
    response: [linkPd, sawBaselinePd, sawDemographicsPd],
  });

  // Mock the response of creating the link pd.
  cy.route({
    method: 'POST',
    url: '/api/participants/*/data/link',
    response: linkPd,
  });

  // Pulled by the ies check presurvey module.
  cy.route({
    method: 'GET',
    url: '/static/known_ies_student_ids.json',
    response: [],
  });
}

beforeEach(mockCodes);

describe('generic portal first state', () => {
  beforeEach(() => {
    // Cypress makes debugging a javascript redirect really hard.
    // https://docs.cypress.io/guides/guides/web-security.html#JavaScript-Redirects
    // Note that disabling web security per these docs doesn't work for the GUI
    // runner as of 2018-06-25 (although it does work on the command line).
    //
    // Combine this with the observation that we already often comment out the
    // location.href = x lines when developing, and the conclusion is to provide
    // a debugging flag on window. When this is set to true, the redirect()
    // factory function acts as a stub, and records the destination URL in a
    // hidden div.
    //
    // The approach here is to set the debugging flag as the page loads, then
    // check the value of the div.
    cy.on('window:before:load', (win) => (win.debugRedirect = true));
    cy.visit('/participate');
  });

  it('prompts for token on sessionless code for CG', () => {
    cy.get('#participation-code').should('be.visible');
    cy.get('#submit-code-button').should('be.disabled');
    cy.get('#participation-code').type(CGCode.code);
    cy.get('#submit-code-button').click();

    // CG has a single survey, so we skip the #session-ordinal view

    cy.get('form[name="tokenForm"]').should('be.visible');
  });

  it('prompts for session on sessionless code for HG', () => {
    cy.get('#participation-code').type(HGCode.code);
    cy.get('#submit-code-button').click();

    cy.get('#session-ordinal').should('be.visible');
    cy.get('#session-ordinal').type(1);

    cy.get('#submit-session-button').click();

    cy.get('form[name="tokenForm"]').should('be.visible');
  });

  it('applies overrides for "testing only" code', () => {
    cy.get('#participation-code').type(`testing only ${CGCode.code}`);
    cy.get('#submit-code-button').click();

    cy.document()
      .its('location.search')
      .should('include', 'date_override=true')
      .should('include', 'ready_override=true');
  });

  it('rejects nonexistent code', () => {
    cy.get('#participation-code').type('bad bear');
    cy.get('#submit-code-button').click();

    // Result is the form can't be submitted and there's an error message.
    cy.get('#submit-code-button').should('be.disabled');
    cy.get('.error-message').should('not.be.empty');
  });

  it('skips token state, creates random token for "skipped" type', () => {
    cy.get('#participation-code').type(MSETCode.code);
    cy.get('#submit-code-button').click();

    // 1. No form is shown, user not prompted to enter token.
    cy.get('form[name="tokenForm"]').should('not.be.visible');

    // 2. Generates a random token, passed to presurvey

    // The app will hang for the rest of this test since we're not mocking
    // presurvey stuff. But we can check just the portal's behavior by looking
    // at the cookies it stores, which is how it communicates with the
    // presurvey. Note this will eventually use local storage instead.
    cy.location('pathname').should('include', '/participate/presurvey');
    cy.getCookies().should((cookies) => {
      const codeC = cookies.find((c) => c.name === 'appParticipate.code');
      const sessionC = cookies.find((c) => c.name === 'appParticipate.session');
      const tokenC = cookies.find((c) => c.name === 'appParticipate.token');

      expect(codeC.value).to.equal(encodeURIComponent(MSETCode.code));
      expect(sessionC.value).to.equal('1');
      expect(tokenC.value).to.match(/^\S+$/);
    });
  });
});

describe('custom portal first state', () => {
  beforeEach(() => {
    cy.on('window:before:load', (win) => (win.debugRedirect = true));
    cy.visit('/participate');
  });

  it('redirects to the custom portal url', () => {
    cy.get('#participation-code').type(CGCodeCustom.code);
    cy.get('#submit-code-button').click();

    const urlCode = toUrlCode(CGCodeCustom.code);
    cy.get('#redirect-to').contains(`?code=${urlCode}&session=1`);
  });

  it('redirects to the custom portal with testing only', () => {
    cy.get('#participation-code').type(`testing only ${CGCodeCustom.code}`);
    cy.get('#submit-code-button').click();

    const urlCode = toUrlCode(`testing only ${CGCodeCustom.code}`);
    cy.get('#redirect-to').contains(`?code=${urlCode}&session=1`);
  });
});

describe('portal code state', () => {
  // Once the code is known.
  beforeEach(() => {
    cy.on('window:before:load', (win) => (win.debugRedirect = true));
  });

  it('accepts entry of a session number', () => {
    cy.visit(`/participate/portal/${toUrlCode(HGCode.code)}`);

    // parses the code the the URL
    cy.get('#participation-code').should('have.value', HGCode.code);
    cy.get('#session-ordinal').should('be.visible');

    cy.get('#session-ordinal').type('1');
    cy.get('#submit-session-button').click();

    // This appears via ngIf (not ngShow), so existence is an appropriate check.
    cy.get('nep-first-mi-last').should('exist');
  });

  it("rejects session if it doesn't exist for that program.", () => {
    cy.visit(`/participate/portal/${toUrlCode(HGCode.code)}`);

    cy.get('#session-ordinal').type('9');
    cy.get('#submit-session-button').click();

    cy.get('#session-ordinal').should('be.visible');
    cy.get('.error-message').should('not.be.empty');
  });

  it('skips both session and token forms, generates random token for "skipped" type', () => {
    cy.visit(`/participate/portal/${toUrlCode(MSETCode.code)}`);

    // An extra agreement screen is required since all the normal portal forms
    // are skipped (all the data they collect is in the URL).
    cy.get('#submit-agreement-button').click();

    // The app will hang for the rest of this test since we're not mocking
    // presurvey stuff. But we can check just the portal's behavior by looking
    // at the cookies it stores, which is how it communicates with the
    // presurvey. Note this will eventually use local storage instead.
    cy.location('pathname').should('include', '/participate/presurvey');
    cy.getCookies().should((cookies) => {
      const codeC = cookies.find((c) => c.name === 'appParticipate.code');
      const sessionC = cookies.find((c) => c.name === 'appParticipate.session');
      const tokenC = cookies.find((c) => c.name === 'appParticipate.token');

      expect(codeC.value).to.equal(encodeURIComponent(MSETCode.code));
      expect(sessionC.value).to.equal('1');
      expect(tokenC.value).to.match(/^\S+$/);
    });
  });
});

describe('portal testing state', () => {
  it('applies overrides for "testing only" code', () => {
    const testingCode = `testing only ${CGCode.code}`;
    cy.visit(`/participate/portal/${toUrlCode(testingCode)}`);
    cy.get('#participation-code').should('have.value', CGCode.code);
    cy.document()
      .its('location.search')
      .should('include', 'date_override=true')
      .should('include', 'ready_override=true');
  });
});

describe('portal code state with invalid code', () => {
  it('rejects code in URL', () => {
    cy.visit('/participate/portal/nonexistent-narwhal');
    cy.get('#participation-code').should('be.visible');
    cy.get('.error-message').should('not.be.empty');
  });
});

describe('portal session state', () => {
  // Both the code and session are known and in the URL.
  beforeEach(() => {
    cy.on('window:before:load', (win) => (win.debugRedirect = true));
  });

  it('displays the name form for "name_or_id" type', () => {
    cy.visit(`/participate/portal/${toUrlCode(HGCode.code)}/1`);
    cy.get('form[name="tokenForm"]').should('be.visible');
  });

  it('skips token form and generates random token for "skipped" type', () => {
    cy.visit(`/participate/portal/${toUrlCode(MSETCode.code)}/1`);

    // An extra agreement screen is required since all the normal portal forms
    // are skipped (all the data they collect is in the URL).
    cy.get('#submit-agreement-button').click();

    // The app will hang for the rest of this test since we're not mocking
    // presurvey stuff. But we can check just the portal's behavior by looking
    // at the cookies it stores, which is how it communicates with the
    // presurvey. Note this will eventually use local storage instead.
    cy.location('pathname').should('include', '/participate/presurvey');
    cy.getCookies().should((cookies) => {
      const codeC = cookies.find((c) => c.name === 'appParticipate.code');
      const sessionC = cookies.find((c) => c.name === 'appParticipate.session');
      const tokenC = cookies.find((c) => c.name === 'appParticipate.token');

      expect(codeC.value).to.equal(encodeURIComponent(MSETCode.code));
      expect(sessionC.value).to.equal('1');
      expect(tokenC.value).to.match(/^\S+$/);
    });
  });
});

describe('code url with spaces', () => {
  it('should parse a code with a space', () => {
    cy.visit('/participate/portal/cool cat');

    cy.wait('@loadCGCode').then(() => {
      cy.get('.error-message').should('not.be.visible');
    });
  });

  it('should parse a code with an encoded space', () => {
    cy.visit('/participate/portal/cool%20cat');

    cy.wait('@loadCGCode').then(() => {
      cy.get('.error-message').should('not.be.visible');
    });
  });

  it('should parse a code with a plus', () => {
    cy.visit('/participate/portal/cool+cat');

    cy.wait('@loadCGCode').then(() => {
      cy.get('.error-message').should('not.be.visible');
    });
  });
});

describe('portal session state with invalid session', () => {
  it('rejects session in URL if it is invalid', () => {
    cy.visit(`/participate/portal/${toUrlCode(HGCode.code)}/9`);
    cy.wait('@loadHGCode').then(() => {
      cy.get('.error-message').should('be.visible');
    });
  });
});

describe('portal token state with new participant', () => {
  beforeEach(() => {
    cy.on('window:before:load', (win) => (win.debugRedirect = true));
  });

  it('redirects with the right parameters, first session', () => {
    cy.visit(`/participate/portal/${toUrlCode(HGCode.code)}/1/${newUser.name}`);

    // An extra agreement screen is required since all the normal portal forms
    // are skipped (all the data they collect is in the URL).
    cy.get('#submit-agreement-button').click();

    cy.get('#redirect-to').contains(`survey_id=${survey.uid}`);
    cy.get('#redirect-to').contains(`organization_id=${org.uid}`);
    cy.get('#redirect-to').contains(
      `organization_name=${org.name.replace(/ /g, '+')}`,
    );
    cy.get('#redirect-to').contains('first_login=true');
  });

  it('redirects with the right parameters, after first session', () => {
    cy.visit(
      `/participate/portal/${toUrlCode(HGCode.code)}/1/${existingUser.name}`,
    );

    // An extra agreement screen is required since all the normal portal forms
    // are skipped (all the data they collect is in the URL).
    cy.get('#submit-agreement-button').click();

    cy.get('#redirect-to').contains(`survey_id=${survey.uid}`);
    cy.get('#redirect-to').contains(`organization_id=${org.uid}`);
    cy.get('#redirect-to').contains(
      `organization_name=${org.name.replace(/ /g, '+')}`,
    );
    cy.get('#redirect-to').contains('first_login=false');
  });
});

describe('portal code from closed cohort', () => {
  it('lets the user know the cohort is closed', () => {
    cy.visit(
      `/participate/portal/${toUrlCode(CGClosedCode.code)}/1/${
        existingUser.name
      }`,
    );

    // An extra agreement screen is required since all the normal portal forms
    // are skipped (all the data they collect is in the URL).
    cy.get('#submit-agreement-button').click();

    cy.get('#error-message').should('be.visible');
    cy.get('#error-message').should((msg) => {
      expect(msg).to.exist;
      expect(msg).to.contain('This program is only available between');
    });
  });
});

// @todo(chris): testing-only variants, and anything that's triggered a bug.
