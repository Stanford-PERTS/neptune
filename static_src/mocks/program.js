/* global cy */
import moment from 'moment';

const thisYear = moment().year();
// open/close dates for a cohort in the past
const closedOpenDate = moment()
  .year(thisYear - 2)
  .toDate();
const closedCloseDate = moment()
  .year(thisYear - 1)
  .toDate();

const now = new Date();
const todayStr = now.toISOString().substr(0, 10);
const tomorrow = new Date(now + 24 * 60 * 60 * 1000);
const tomorrowStr = tomorrow.toISOString().substr(0, 10);

export const createCgProgram = () => ({
  name: 'Growth Mindset for College Students',
  label: 'cg17',
  surveys: ['survey1'],
  cohorts: {
    '2018': {
      open_date: todayStr,
      close_date: tomorrowStr,
    },
    '2017_spring': {
      open_date: closedOpenDate,
      close_date: closedCloseDate,
    },
  },
});

export const createCgCode = () => ({
  uid: 'ProjectCohort_cool-cat',
  code: 'cool cat',
  program_label: 'cg17',
  cohort_label: '2018',
});

export const createHgProgram = () => ({
  name: 'Growth Mindset for 9th Graders',
  label: 'hg17',
  surveys: ['survey1', 'survey2'],
  cohorts: {
    '2018': {
      open_date: todayStr,
      close_date: tomorrowStr,
    },
  },
  presurvey_states: ['skipCheck'],
});

export const createHgCode = () => ({
  uid: 'ProjectCohort_high-horse',
  code: 'high horse',
  program_label: 'hg17',
  cohort_label: '2018',
});

export const createMsetProgram = () => ({
  name: 'Message Student Experience Tracker',
  label: 'mset19',
  surveys: [{ anonymous_link: 'https://saturn.perts.net/surveys/mset19' }],
  cohorts: {},
  default_portal_type: 'skipped',
});

export const createEpProgram = () => ({
  name: 'Engagement Project',
  label: 'ep19',
  platform: 'triton',
  presurvey_states: ['previewAgreement', 'epBlockSwitcher'],
  surveys: [
    {
      anonymous_link: 'https://www.example.com?ep-anon-link',
    },
  ],
  cohorts: {
    '2018': {
      open_date: todayStr,
      close_date: tomorrowStr,
    },
  },
});

export const createCcpProgram = () => ({
  name: 'Classroom Connections Program',
  label: 'ccp19',
  platform: 'triton',
  presurvey_states: ['previewAgreement', 'epBlockSwitcher'],
  surveys: [
    {
      anonymous_link: 'https://www.example.com?ccp-anon-link',
    },
  ],
  cohorts: {
    '2018': {
      open_date: todayStr,
      close_date: tomorrowStr,
    },
  },
});
