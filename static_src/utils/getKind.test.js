import getKind from './getKind';

describe('getKind', () => {
  const uid = 'User_123456789';

  describe('when a valid UID is provided', () => {
    it('should return a String', () => {
      expect(typeof getKind(uid)).toEqual('string');
    });

    it('should provide the entity type', () => {
      expect(getKind(uid)).toEqual('User');
    });
  });
});
