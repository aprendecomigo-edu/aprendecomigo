/**
 * Auth Tests Configuration
 *
 * This configuration file is used to group all authentication-related
 * tests for easier execution as a test suite.
 */
module.exports = {
  testMatch: [
    "integration/e2e/registration-email.test.js",
    "integration/e2e/registration-phone.test.js",
    "integration/e2e/verification-code.test.js",
    "integration/e2e/secondary-contact.test.js",
    "integration/e2e/primary-contact-change.test.js",
    "integration/e2e/role-permissions.test.js",
  ],
  testTimeout: 120000, // 2 minutes per test
  maxWorkers: 1, // Run tests serially for more predictable results
  setupFilesAfterEnv: ["./integration/auth-tests.setup.js"],
  reporters: ["detox/runners/jest/streamlineReporter"],
  verbose: true,
};
