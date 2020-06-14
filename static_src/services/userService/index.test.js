xdescribe('user service', () => {
  const mockData = {
    User_0001: {
      uid: 'User_0001',
      name: 'Aaron Admin',
      email: 'aaron@example.com',
      user_type: 'super_admin',
    },
    User_0002: {
      uid: 'User_0002',
      name: 'Viper Script',
      email: 'viper@example.com',
      user_type: 'user',
    },
    User_0003: {
      uid: 'User_0003',
      name: 'Cass Burch',
      email: 'cass@example.com',
      user_type: 'user',
    },
    User_0004: {
      uid: 'User_0004',
      name: 'Deckard Burch',
      email: 'deckard@example.com',
      user_type: 'user',
    },
  };

  it('should initialize data object', () => {
    inject(User => {
      expect(User.data).toBeDefined();
      expect(typeof User.data).toEqual('object');
    });
  });

  describe('get', () => {
    it('should return the single user requested', () => {
      inject(User => {
        User.data = mockData;

        const userUid = 'User_0001';
        const user = User.get(userUid);

        expect(user).toBeDefined();
        expect(user).toEqual(User.data[userUid]);
      });
    });

    it('should return undefined for non-existent user', () => {
      inject(User => {
        User.data = mockData;

        const userUid = 'User_DOESNT_EXIST';
        const user = User.get(userUid);

        expect(user).toBeUndefined();
        expect(user).toEqual(User.data[userUid]);
      });
    });
  });
});
