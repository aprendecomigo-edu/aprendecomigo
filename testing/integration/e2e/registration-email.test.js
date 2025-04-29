const { device, element, by, waitFor } = require("detox");
const axios = require("axios");
const MockAdapter = require("axios-mock-adapter");

// Setup axios mock
const mock = new MockAdapter(axios);

// Test data
const TEST_EMAIL = "test.user@example.com";
const TEST_PASSWORD = "StrongP@ssw0rd!";
const VERIFICATION_CODE = "123456";

describe("User Registration with Email as Primary", () => {
  // Setup before tests
  beforeAll(async () => {
    await device.launchApp();

    // Mock email verification API endpoint
    mock.onPost("/api/auth/send-verification-code/").reply(200, {
      success: true,
      message: "Verification code sent successfully",
    });

    // Mock verification code validation endpoint
    mock.onPost("/api/auth/verify-code/").reply(200, {
      success: true,
      message: "Email verified successfully",
      token: "test-jwt-token-12345",
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

  test("Should select email as primary contact method", async () => {
    // Assumes we start on registration screen
    await element(by.id("email-option")).tap();
    await expect(element(by.id("email-option"))).toBeSelected();
  });

  test("Should validate form fields correctly", async () => {
    // Test validation with empty fields
    await element(by.id("submit-button")).tap();
    await expect(element(by.id("email-error"))).toBeVisible();
    await expect(element(by.id("password-error"))).toBeVisible();

    // Test email format validation
    await element(by.id("email-input")).typeText("invalid-email");
    await element(by.id("submit-button")).tap();
    await expect(element(by.id("email-error"))).toBeVisible();

    // Test password strength validation
    await element(by.id("email-input")).clearText();
    await element(by.id("email-input")).typeText(TEST_EMAIL);
    await element(by.id("password-input")).typeText("weak");
    await element(by.id("submit-button")).tap();
    await expect(element(by.id("password-error"))).toBeVisible();
  });

  test("Should submit valid registration form and request verification code", async () => {
    // Fill in valid form data
    await element(by.id("email-input")).clearText();
    await element(by.id("password-input")).clearText();
    await element(by.id("email-input")).typeText(TEST_EMAIL);
    await element(by.id("password-input")).typeText(TEST_PASSWORD);
    await element(by.id("password-confirm-input")).typeText(TEST_PASSWORD);
    await element(by.id("terms-checkbox")).tap();

    // Spy on the email verification API call
    let emailSent = false;
    mock.onPost("/api/auth/send-verification-code/").reply((config) => {
      const data = JSON.parse(config.data);
      emailSent = data.email === TEST_EMAIL;
      return [200, { success: true }];
    });

    // Submit the form
    await element(by.id("submit-button")).tap();

    // Should navigate to verification screen
    await waitFor(element(by.id("verification-screen")))
      .toBeVisible()
      .withTimeout(3000);

    // Verify the email was sent to the correct address
    expect(emailSent).toBe(true);
  });

  test("Should verify email with correct verification code", async () => {
    // Enter verification code
    await element(by.id("verification-code-input")).typeText(VERIFICATION_CODE);

    // Spy on verification API call
    let codeVerified = false;
    mock.onPost("/api/auth/verify-code/").reply((config) => {
      const data = JSON.parse(config.data);
      codeVerified =
        data.code === VERIFICATION_CODE && data.email === TEST_EMAIL;
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

    // Verify token is stored in secure storage
    // This would require a mock or spy on the secure storage mechanism
    // For this example, we're assuming the app stores it correctly when it receives a valid response
  });

  test("Should handle verification code expiration", async () => {
    // Mock expired verification code
    mock.onPost("/api/auth/verify-code/").reply(400, {
      success: false,
      message: "Verification code has expired",
      error: "CODE_EXPIRED",
    });

    // Navigate back to verification screen (may need additional setup here)
    // ...

    // Enter expired verification code
    await element(by.id("verification-code-input")).typeText("654321");
    await element(by.id("verify-button")).tap();

    // Verify expiration error is shown
    await waitFor(element(by.id("verification-error")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("verification-error"))).toHaveText(
      "Verification code has expired",
    );

    // Verify resend button is available
    await expect(element(by.id("resend-code-button"))).toBeVisible();
  });

  test("Should resend verification code when requested", async () => {
    // Mock resend verification code endpoint
    let resendCalled = false;
    mock.onPost("/api/auth/resend-verification-code/").reply((config) => {
      const data = JSON.parse(config.data);
      resendCalled = data.email === TEST_EMAIL;
      return [200, { success: true }];
    });

    // Tap resend button
    await element(by.id("resend-code-button")).tap();

    // Verify resend confirmation is shown
    await waitFor(element(by.id("resend-confirmation")))
      .toBeVisible()
      .withTimeout(2000);

    // Verify the resend API was called with correct email
    expect(resendCalled).toBe(true);
  });
});
