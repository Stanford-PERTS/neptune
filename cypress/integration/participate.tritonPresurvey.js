import { createCcpProgram, createEpProgram } from 'mocks/program';

const ccpProgram = createCcpProgram();
const epProgram = createEpProgram();

const toUrlCode = code => code.replace(/ /g, '-');

const org = {
  uid: 'Organization_001',
  name: 'Chris Test U',
};

const epCode1 = {
  uid: 'ProjectCohort_cool-cat',
  code: 'cool cat',
  organization_id: 'Team_ep',
  portal_type: 'name_or_id',
  portal_message: 'Please enter your student ID:',
  program_label: 'ep19',
  cohort_label: '2018',
  survey_params: {
    learning_conditions: '[]',
    open_response_lcs: '[]',
  },
};

const epCode2 = {
  uid: 'ProjectCohort_eager-eagle',
  code: 'eager eagle',
  organization_id: 'Team_ep',
  portal_type: 'name_or_id',
  portal_message: 'Please enter your student ID:',
  program_label: 'ep19',
  cohort_label: '2018',
  survey_params: {
    learning_conditions: '[]',
    open_response_lcs: '[]',
  },
};

const ccpCode = {
  uid: 'ProjectCohort_dapper-duck',
  code: 'dapper duck',
  organization_id: 'Team_ccp',
  portal_type: 'name_or_id',
  portal_message: 'Please enter your student ID:',
  program_label: 'ccp19',
  cohort_label: '2018',
  survey_params: {
    learning_conditions: '[]',
    open_response_lcs: '[]',
  },
};

const surveyEp1 = { uid: 'Survey_ep1' };
const surveyEp2 = { uid: 'Survey_ep2' };
const surveyCcp = { uid: 'Survey_ccp1' };

const invalidUser = {
  uid: 'Participant_invalid',
  name: 'invalid-user',
};

const newUser = {
  uid: 'Participant_new',
  name: 'new-user',
};

const newRosteredUser = {
  uid: 'Participant_new-rostered',
  name: 'new-rostered',
};

const existingUser = {
  uid: 'Particpant_existing',
  name: 'existing-user',
};

const mismatchUser = {
  uid: 'Particpant_mismatch',
  name: 'mismatch-user',
};

const getLinkPd = pcId => ({
  uid: 'ParticipantData_link',
  key: 'link',
  value: 'https://www.example.com/',
  project_cohort_id: pcId,
});

// The existing user has seen the validation, demographics, and baseline blocks
// once before for a single classroom.
const sawValidationPd = {
  uid: 'ParticipantData_sawValidation',
  key: 'saw_validation',
  value: new Date().toISOString().substr(0, 10), // recent, so should be off
  project_cohort_id: epCode1.uid,
};

const sawDemoPd = {
  uid: 'ParticipantData_sawDemo',
  key: 'saw_demographics',
  value: 'true',
  project_cohort_id: epCode1.uid,
};

const sawBasePd = {
  uid: 'ParticipantData_sawBase',
  key: 'saw_baseline',
  value: 'true',
  project_cohort_id: epCode1.uid,
};

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
    url: '/api/programs/ep19',
    response: epProgram,
  }).as('loadEPProgram');
  cy.route({
    method: 'GET',
    url: '/api/programs/ccp19',
    response: ccpProgram,
  }).as('loadCCPProgram');

  // ProjectCohorts a.k.a. codes
  cy.route({
    method: 'GET',
    url: '/api/codes/cool-cat',
    response: epCode1,
  }).as('loadEPCode');
  cy.route({
    method: 'GET',
    url: '/api/codes/eager-eagle',
    response: epCode2,
  }).as('loadEPCode2');
  cy.route({
    method: 'GET',
    url: '/api/codes/dapper-duck',
    response: ccpCode,
  }).as('loadCCPCode');

  // Surveys are needed if we're going to write new pd for the user.
  cy.route({
    method: 'GET',
    url: `/api/surveys?*project_cohort_id=${epCode1.uid}*`,
    response: [surveyEp1],
  });
  cy.route({
    method: 'GET',
    url: `/api/surveys?*project_cohort_id=${epCode2.uid}*`,
    response: [surveyEp2],
  });
  cy.route({
    method: 'GET',
    url: `/api/surveys?*project_cohort_id=${ccpCode.uid}*`,
    response: [surveyCcp],
  });

  // Checking for the new user should always return empty set.
  cy.route({
    method: 'GET',
    url: `/api/participants?*name=${newUser.name}*`,
    response: [],
  });

  // User is new-to-neptune.
  cy.route({
    method: 'GET',
    url: `/api/participants?*name=${newRosteredUser.name}*`,
    response: [],
  });

  // Existing user.
  cy.route({
    method: 'GET',
    url: `/api/participants?*name=${existingUser.name}*`,
    response: [existingUser],
  });

  // Invalid user.
  cy.route({
    method: 'GET',
    url: `/api/participants?*name=${invalidUser.name}*`,
    response: [invalidUser],
  });

  // Mismatch user. Notice the uid is intentionally wrong.
  cy.route({
    method: 'GET',
    url: `/api/participants?*name=${mismatchUser.name}*`,
    response: [{ ...mismatchUser, uid: 'Participant_neptune-mismatch' }],
  });

  // N.B. We do need to also mock a POST for new participants, but that's done
  // per-test, since it changes a lot.

  // "Unique link"
  cy.route({
    method: 'POST',
    url: '/api/survey_links/**/get_unique',
    response: getLinkPd().value,
  });

  // "New" and "Invalid" users have no pd.
  cy.route({
    method: 'GET',
    url: '/api/participants/*/data',
    response: [],
  });

  cy.route({
    method: 'GET',
    url: `/api/participants/${existingUser.uid}/data`,
    response: [sawValidationPd, sawDemoPd, sawBasePd, getLinkPd(epCode1)],
  }).as('getPdForExisting');

  // An existing user's pd must always contain, at minimum, a link pd.
  // cy.route({
  //   method: 'GET',
  //   url: `/api/participants/${newUser.uid}/data`,
  //   response: [linkPd],
  // });

  // Mock the response of creating the link pd.
  cy.route({
    method: 'POST',
    url: '/api/participants/*/data/link',
    response: getLinkPd(),
  });
}

const copilotDomainPrefix = '^https?://(copilot.perts.net|localhost:10080)';
const copilotExistingPath1 = `/api/codes/${toUrlCode(
  epCode1.code,
)}/participants/${existingUser.name}`;
const copilotExistingPath2 = `/api/codes/${toUrlCode(
  epCode2.code,
)}/participants/${existingUser.name}`;
const copilotNewPath = `/api/codes/${toUrlCode(epCode1.code)}/participants/${
  newUser.name
}`;
const copilotNewRosteredPath = `/api/codes/${toUrlCode(
  epCode1.code,
)}/participants/${newRosteredUser.name}`;
const copilotInvalidPath = `/api/codes/${toUrlCode(
  epCode1.code,
)}/participants/${invalidUser.name}`;
const copilotMismatchPath = `/api/codes/${toUrlCode(
  epCode1.code,
)}/participants/${mismatchUser.name}`;
const copilotParticipantResponse = (team, participant) => ({
  uid: participant.uid,
  team_id: team.uid,
  cycle: {
    uid: 'Cycle_001',
    team_id: 'Team_001',
    ordinal: 1,
    start_date: '2019-01-01',
    end_date: '2019-11-01',
  },
});

function mockCopilot() {
  // existing user is in two classes
  cy.route({
    method: 'GET',
    url: new RegExp(`${copilotDomainPrefix}${copilotExistingPath1}`),
    status: 200,
    response: copilotParticipantResponse(epCode1.organization_id, existingUser),
  });
  cy.route({
    method: 'GET',
    url: new RegExp(`${copilotDomainPrefix}${copilotExistingPath2}`),
    status: 200,
    response: copilotParticipantResponse(epCode2.organization_id, existingUser),
  });

  cy.route({
    method: 'GET',
    url: new RegExp(`${copilotDomainPrefix}${copilotNewPath}`),
    status: 200,
    response: copilotParticipantResponse(epCode1.organization_id, newUser),
  });
  cy.route({
    method: 'GET',
    url: new RegExp(`${copilotDomainPrefix}${copilotNewRosteredPath}`),
    status: 200,
    response: copilotParticipantResponse(
      epCode1.organization_id,
      newRosteredUser,
    ),
  });
  cy.route({
    method: 'GET',
    url: new RegExp(`${copilotDomainPrefix}${copilotMismatchPath}`),
    status: 200,
    response: copilotParticipantResponse(
      epCode1.organization_id,
      // intentionally wrong
      { ...mismatchUser, uid: 'Participant_triton-mismatch' },
    ),
  });

  cy.route({
    method: 'GET',
    url: new RegExp(`${copilotDomainPrefix}${copilotInvalidPath}`),
    status: 404,
    response: '',
  });
}

describe('EP modules', () => {
  beforeEach(() => {
    cy.on('window:before:load', win => {
      // Don't actually redirect, switch on the debugging behavior so we can
      // check where we _would_ have gone.
      win.debugRedirect = true;
    });
    cy.server();
    mockCopilot();
    mockCodes();

    // All these tests only post the newUser.
    cy.route({
      method: 'POST',
      url: `/api/participants`,
      response: newUser,
    }).as('postUser');
  });

  it('accepts name found on Copilot roster', () => {
    cy.visit(
      `/participate/portal/${toUrlCode(epCode1.code)}/1/${existingUser.name}`,
    );
    cy.get('#redirect-to').contains(getLinkPd().value);
  });

  it('rejects name NOT found on Copilot roster', () => {
    cy.visit(
      `/participate/portal/${toUrlCode(epCode1.code)}/1/${invalidUser.name}`,
    );
    cy.get('#submit-token-button').should('be.visible');
    cy.get('.error-message').should('be.visible');
  });

  it('communicates unexpected errors', () => {
    cy.route({
      method: 'GET',
      url: new RegExp(`${copilotDomainPrefix}${copilotExistingPath1}`),
      status: 500,
      response: 'Unexpected server error',
    });
    cy.visit(
      `/participate/portal/${toUrlCode(epCode1.code)}/1/${existingUser.name}`,
    );
    cy.get('[data-test="unexpected error"]').should('be.visible');
  });

  it('redirects with the right parameters, new user', () => {
    cy.visit(
      `/participate/portal/${toUrlCode(epCode1.code)}/1/${newUser.name}`,
    );

    // in lieu of testing participant id in redirect
    cy.wait('@postUser').then(xhr => {
      expect(xhr.request.body.name).to.equal(newUser.name);
      expect(xhr.request.body.organization_id).to.equal(
        epCode1.organization_id,
      );
    });

    cy.get('#redirect-to')
      // Can't dynamically mock POST responses, so don't do this:
      // .contains(`participant_id=${newUser.uid}`)
      // Instead just check that there's SOME value
      .contains(/participant_id=Participant_\S+/)
      .contains(`survey_id=${surveyEp1.uid}%3Acycle-1`)
      .contains('first_login=true')
      .contains(
        `learning_conditions=${encodeURIComponent(
          epCode1.survey_params.learning_conditions,
        )}`,
      )
      .contains(
        `open_response_lcs=${encodeURIComponent(
          epCode1.survey_params.open_response_lcs,
        )}`,
      )
      .contains('token=')
      .contains('code=cool+cat')
      .contains('show_validation=true')
      .should('not.contain', 'saw_demographics')
      .should('not.contain', 'saw_baseline');
  });

  it('redirects with the right parameters, existing user', () => {
    cy.visit(
      `/participate/portal/${toUrlCode(epCode1.code)}/1/${existingUser.name}`,
    );

    // The exisiting user has seen these blocks in this classroom previously.
    // The URL should tell Qualtrics not to display them.
    cy.get('#redirect-to')
      .contains('saw_demographics=true')
      .contains('saw_baseline=true')
      .should('not.contain', 'show_validation=true'); // seen it recently
  });

  it('displays validation after 50 days', () => {
    // Change the pd route stub so it gives an older date for `saw_validation`.
    const fiftyDays = 50 * 24 * 60 * 60 * 1000;
    const oldSawDate = new Date(Number(new Date()) - fiftyDays);
    const oldValidationPd = {
      ...sawValidationPd,
      value: oldSawDate.toISOString().substr(0, 10),
    };
    cy.route({
      method: 'GET',
      url: `/api/participants/${existingUser.uid}/data`,
      response: [oldValidationPd, sawDemoPd, sawBasePd, getLinkPd(epCode1)],
    }).as('getPdForExisting');

    cy.visit(
      `/participate/portal/${toUrlCode(epCode1.code)}/1/${existingUser.name}`,
    );

    cy.get('#redirect-to').contains('show_validation=true');
  });

  it('respects one-time survey blocks across classrooms', () => {
    cy.visit(
      `/participate/portal/${toUrlCode(epCode2.code)}/1/${existingUser.name}`,
    );

    // No project cohort id filtering the pd; get all pd for user.
    cy.wait('@getPdForExisting')
      .its('url')
      .should('be', `/api/participants/${existingUser.uid}/data`);

    // The existing user has seen these blocks in a _different_ classroom
    // previously. The presurvey should still detect this and tell Qualtrics
    // not to display them.
    cy.get('#redirect-to')
      .contains('saw_demographics=true')
      .contains('saw_baseline=true');
  });
});

describe('Neptune/Triton sync', () => {
  beforeEach(() => {
    cy.on('window:before:load', win => {
      // Don't actually redirect, switch on the debugging behavior so we can
      // check where we _would_ have gone.
      win.debugRedirect = true;
    });
    cy.server();
    mockCopilot();
    mockCodes();
  });

  it('creates new neptune participants with triton uids', () => {
    cy.route({
      method: 'POST',
      url: `/api/participants`,
      response: newRosteredUser,
    }).as('postUser');

    cy.visit(
      `/participate/portal/${toUrlCode(epCode1.code)}/1/${
        newRosteredUser.name
      }`,
    );

    // The new neptune participant should be created with the id from triton.
    cy.wait('@postUser').then(xhr => {
      expect(xhr.request.body.id).to.equal('new-rostered');
    });

    cy.get('#redirect-to').contains(`participant_id=${newRosteredUser.uid}`);
  });

  it("logs an error when neptune and triton uids don't match", () => {
    cy.route({
      method: 'POST',
      url: `/api/participants`,
      response: mismatchUser,
    });

    cy.visit(
      `/participate/portal/${toUrlCode(epCode1.code)}/1/${mismatchUser.name}`,
    );

    cy.get('[data-test="unexpected error"]').should('be.visible');
  });
});
