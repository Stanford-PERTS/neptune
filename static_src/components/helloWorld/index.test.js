xdescribe('helloWorld', () => {
  it('should display Hello', () => {
    inject(($rootScope, $compile) => {
      const scope = $rootScope.$new();
      const element = $compile('<hello-world></hello-world>')(scope);
      scope.$digest();

      expect(element.html()).toContain('Hello');
    });
  });
});
