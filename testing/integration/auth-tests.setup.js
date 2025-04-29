/**
 * Auth Tests Setup
 *
 * This file contains global setup code that runs before all auth-related tests.
 * It ensures the test environment is properly configured.
 */

const axios = require("axios");
const MockAdapter = require("axios-mock-adapter");

// Set a longer default timeout for all tests
jest.setTimeout(60000);

// Mock axios globally for all tests
const globalMock = new MockAdapter(axios);

// Setup time mocking
const originalDateNow = Date.now;

// Add custom matchers
expect.extend({
  // Custom matcher to check if element has specific test ID
  toHaveTestID(received, testID) {
    const pass = received && received.getAttribute("testID") === testID;
    if (pass) {
      return {
        message: () => `Expected element not to have testID "${testID}"`,
        pass: true,
      };
    } else {
      return {
        message: () => `Expected element to have testID "${testID}"`,
        pass: false,
      };
    }
  },
});

// Global before all tests
beforeAll(async () => {
  console.log("Setting up auth tests environment...");

  // Allow real network requests for specific endpoints if needed
  globalMock.onAny().passThrough();
});

// Global before each test
beforeEach(async () => {
  // Reset all mocks
  globalMock.reset();

  // Reset Date.now mock
  Date.now = originalDateNow;
});

// Global after all tests
afterAll(async () => {
  console.log("Tearing down auth tests environment...");

  // Restore axios
  globalMock.restore();

  // Restore Date
  Date.now = originalDateNow;
});
