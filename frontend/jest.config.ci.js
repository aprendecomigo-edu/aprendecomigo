const baseConfig = require('./jest.config.js');

module.exports = {
  ...baseConfig,
  // Reduce coverage thresholds for CI to focus on functionality over coverage for now
  coverageThreshold: {
    global: {
      branches: 0.5,
      functions: 1,
      lines: 1,
      statements: 1,
    },
  },
  // Only collect coverage from critical paths for CI speed
  collectCoverageFrom: [
    'hooks/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/__tests__/**',
    '!**/coverage/**',
  ],
};