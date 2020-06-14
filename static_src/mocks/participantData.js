import { createUid } from 'mocks';

export const createPd = options => ({
  uid: createUid('ParticipantData'),
  ...options,
});
