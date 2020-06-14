describe('Array.prototype.last', () => {
  it('should be a function', () => {
    expect(typeof Array.prototype.last).toEqual('function');
  });

  it('should return the last element of an array', () => {
    expect([1, 2, 3].last()).toEqual(3);
    expect([1, 2, [1, 2, 3]].last()).toEqual([1, 2, 3]);
    expect([1, 2, , null].last()).toEqual(null);
    expect([1, 2, undefined].last()).toEqual(undefined);
  });

  it('should return value if not an array', () => {
    expect({ foo: 'bar' }).toEqual({ foo: 'bar' });
    expect(27).toEqual(27);
  });

  it('should handle zero length arrays', () => {
    expect([]).toEqual([]);
  });
});
