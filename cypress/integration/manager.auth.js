/* global cy */

const now = new Date();
const todayStr = now.toISOString().substr(0, 10);
const tomorrow = new Date(Number(now) + 24 * 60 * 60 * 1000);
const tomorrowStr = tomorrow.toISOString().substr(0, 10);

const CGProgram = {
  name: 'Growth Mindset for College Students',
  surveys: ['survey1'],
  cohorts: {
    '2018': {
      open_date: todayStr,
      close_date: tomorrowStr,
    },
  },
};

function mockServer() {
  cy.server();
  
  cy.route({
    method: 'GET',
    url: '/api/programs/cg17',
    response: CGProgram,
  }).as('loadCGProgram');

  cy.route({
    method: 'GET',
    url: '/api/auth_tokens/missing.demo/user',
    status: 404,
    response: 'not found',
  });

  cy.route({
    method: 'GET',
    url: '/api/auth_tokens/used.demo/user',
    status: 410,
    response: 'used',
  });
}

beforeEach(mockServer);

describe('Neptune appManager auth', () => {
  it('loads home page', () => {
    cy.visit('/');
    cy.window().should('have.property', 'PERTS');
    cy.get('nep-navbar').should('be.visible');
    cy.get('nep-navbar a[href="/login"]').should('be.visible');
  });

  it('loads login page', () => {
    cy.visit('/login');
    cy.get('#email').should('be.visible');
    cy.get('#password').should('be.visible');
    cy.get('button[type="submit"]').should('be.visible');
  });

  it('shows error on missing auth token', () => {
    cy.visit('/set_password/missing.demo?case=invitation');
    cy.get('div[data-test="not-found"]').should('be.visible');
  });

  it('shows error on used auth token', () => {
    cy.visit('/set_password/used.demo?case=invitation');
    cy.get('div[data-test="used"]').should('be.visible');
  });
});
