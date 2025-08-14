module.exports = {
  useBreakpointValue: jest.fn(values => {
    // Return the default or base value for testing
    if (typeof values === 'object') {
      return (
        values.base || values.sm || values.md || values.lg || values.xl || Object.values(values)[0]
      );
    }
    return values;
  }),
  getBreakPointValue: jest.fn((values, breakpoint = 'base') => {
    if (typeof values === 'object') {
      return values[breakpoint] || values.base || Object.values(values)[0];
    }
    return values;
  }),
};
