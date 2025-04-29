const { device, element, by, waitFor } = require("detox");
const axios = require("axios");
const MockAdapter = require("axios-mock-adapter");

// Setup axios mock
const mock = new MockAdapter(axios);

// Test data
const TEST_PHONE = "+1234567890";
const TEST_PASSWORD = "StrongP@ssw0rd!";
const VERIFICATION_CODE = "123456";

describe("User Registration with Phone as Primary", () => {
  // Setup before tests
  beforeAll(async () => {
    await device.launchApp();

    // Mock SMS verification API endpoint
    mock.onPost("/api/auth/send-sms-verification/").reply(200, {
      success: true,
      message: "SMS verification code sent successfully",
    });

    // Mock verification code validation endpoint
    mock.onPost("/api/auth/verify-phone-code/").reply(200, {
      success: true,
      message: "Phone verified successfully",
      token: "test-jwt-token-12345",
    });

    // Mock phone validation service if any
    mock.onGet("/api/auth/validate-phone-format/").reply((config) => {
      const phone = config.params.phone;
      const isValid = /^\+[1-9]\d{1,14}$/.test(phone); // Simple E.164 format check
      return [
        200,
        {
          valid: isValid,
          formatted: isValid ? phone : null,
          error: isValid ? null : "Invalid phone number format",
        },
      ];
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  afterAll(async () => {
    // Clean up mocks
    mock.restore();
  });

  test("Should navigate to registration screen", async () => {
    // Get to registration from login screen
    await waitFor(element(by.id("login-screen")))
      .toBeVisible()
      .withTimeout(2000);
    await element(by.id("register-link")).tap();

    // Verify we're on the registration screen
    await waitFor(element(by.id("registration-screen")))
      .toBeVisible()
      .withTimeout(2000);
  });

  test("Should select phone as primary contact method", async () => {
    // Assumes we start on registration screen
    await element(by.id("phone-option")).tap();
    await expect(element(by.id("phone-option"))).toBeSelected();

    // Verify phone input is visible
    await expect(element(by.id("phone-input"))).toBeVisible();
  });

  test("Should validate phone number format", async () => {
    // Test with invalid phone format
    await element(by.id("phone-input")).typeText("123456");

    // Tap outside to trigger validation
    await element(by.id("registration-screen")).tap({ x: 10, y: 10 });

    // Check error message
    await waitFor(element(by.id("phone-error")))
      .toBeVisible()
      .withTimeout(2000);

    // Clear and enter valid phone
    await element(by.id("phone-input")).clearText();
    await element(by.id("phone-input")).typeText(TEST_PHONE);

    // Tap outside again
    await element(by.id("registration-screen")).tap({ x: 10, y: 10 });

    // Error should be gone
    await waitFor(element(by.id("phone-error")))
      .not.toBeVisible()
      .withTimeout(2000);
  });

  test("Should submit valid registration form with phone and request verification code", async () => {
    // Fill in valid form data
    await element(by.id("phone-input")).clearText();
    await element(by.id("password-input")).clearText();
    await element(by.id("phone-input")).typeText(TEST_PHONE);
    await element(by.id("password-input")).typeText(TEST_PASSWORD);
    await element(by.id("password-confirm-input")).typeText(TEST_PASSWORD);
    await element(by.id("terms-checkbox")).tap();

    // Spy on the SMS verification API call
    let smsSent = false;
    mock.onPost("/api/auth/send-sms-verification/").reply((config) => {
      const data = JSON.parse(config.data);
      smsSent = data.phone === TEST_PHONE;
      return [200, { success: true }];
    });

    // Submit the form
    await element(by.id("submit-button")).tap();

    // Should navigate to verification screen
    await waitFor(element(by.id("phone-verification-screen")))
      .toBeVisible()
      .withTimeout(3000);

    // Verify the SMS was sent to the correct phone number
    expect(smsSent).toBe(true);
  });

  test("Should verify phone with correct verification code", async () => {
    // Enter verification code
    await element(by.id("verification-code-input")).typeText(VERIFICATION_CODE);

    // Spy on verification API call
    let codeVerified = false;
    mock.onPost("/api/auth/verify-phone-code/").reply((config) => {
      const data = JSON.parse(config.data);
      codeVerified =
        data.code === VERIFICATION_CODE && data.phone === TEST_PHONE;
      return [
        200,
        {
          success: true,
          token: "test-jwt-token-12345",
        },
      ];
    });

    // Submit verification code
    await element(by.id("verify-button")).tap();

    // Should navigate to onboarding/home after successful verification
    await waitFor(element(by.id("onboarding-screen")))
      .toBeVisible()
      .withTimeout(3000);

    // Verify the code was submitted correctly
    expect(codeVerified).toBe(true);
  });

  test("Should handle invalid phone numbers", async () => {
    // Navigate back to registration (this may require more setup depending on app flow)
    // ...

    // Select phone registration again
    await element(by.id("phone-option")).tap();

    // Enter invalid international format
    await element(by.id("phone-input")).typeText("12345");
    await element(by.id("password-input")).typeText(TEST_PASSWORD);
    await element(by.id("password-confirm-input")).typeText(TEST_PASSWORD);
    await element(by.id("terms-checkbox")).tap();

    // Mock invalid phone response
    mock.onPost("/api/auth/send-sms-verification/").reply(400, {
      success: false,
      message: "Invalid phone number",
      error: "INVALID_PHONE",
    });

    // Submit form
    await element(by.id("submit-button")).tap();

    // Should show error message
    await waitFor(element(by.id("phone-error")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("phone-error"))).toHaveText(
      "Invalid phone number",
    );
  });

  test("Should handle rate limiting for SMS verification", async () => {
    // Clear fields and enter valid data again
    await element(by.id("phone-input")).clearText();
    await element(by.id("phone-input")).typeText(TEST_PHONE);

    // Mock rate limiting response
    mock.onPost("/api/auth/send-sms-verification/").reply(429, {
      success: false,
      message: "Too many attempts. Please try again in 15 minutes.",
      error: "RATE_LIMITED",
      retryAfter: 900, // seconds
    });

    // Submit form
    await element(by.id("submit-button")).tap();

    // Should show rate limit error
    await waitFor(element(by.id("rate-limit-error")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("rate-limit-error"))).toHaveText(
      "Too many attempts. Please try again in 15 minutes.",
    );

    // Should show countdown timer
    await expect(element(by.id("retry-countdown"))).toBeVisible();
  });

  test("Should handle international phone numbers correctly", async () => {
    // Different international test number
    const INTL_PHONE = "+447911123456"; // UK format

    // Clear fields and enter international number
    await element(by.id("phone-input")).clearText();
    await element(by.id("phone-input")).typeText(INTL_PHONE);

    // Mock successful international validation and SMS sending
    mock.onGet("/api/auth/validate-phone-format/").reply(200, {
      valid: true,
      formatted: INTL_PHONE,
    });

    let smsPayload = null;
    mock.onPost("/api/auth/send-sms-verification/").reply((config) => {
      smsPayload = JSON.parse(config.data);
      return [200, { success: true }];
    });

    // Submit form
    await element(by.id("submit-button")).tap();

    // Should navigate to verification
    await waitFor(element(by.id("phone-verification-screen")))
      .toBeVisible()
      .withTimeout(3000);

    // Verify correct international format was used
    expect(smsPayload.phone).toBe(INTL_PHONE);
  });
});
