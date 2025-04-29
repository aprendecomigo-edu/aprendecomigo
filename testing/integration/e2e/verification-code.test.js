const { device, element, by, waitFor } = require("detox");
const axios = require("axios");
const MockAdapter = require("axios-mock-adapter");

// Setup axios mock
const mock = new MockAdapter(axios);

// Test data
const TEST_EMAIL = "test.user@example.com";
const TEST_PHONE = "+1234567890";
const VALID_CODE = "123456";
const INVALID_CODE = "654321";
const EXPIRED_CODE = "111111";

describe("Verification Code Validation", () => {
  // Setup before tests
  beforeAll(async () => {
    await device.launchApp();

    // Mock successful verification for valid code
    mock.onPost("/api/auth/verify-code/").reply((config) => {
      const data = JSON.parse(config.data);
      if (data.code === VALID_CODE) {
        return [
          200,
          {
            success: true,
            message: "Code verified successfully",
            token: "test-jwt-token-12345",
          },
        ];
      } else if (data.code === EXPIRED_CODE) {
        return [
          400,
          {
            success: false,
            message: "Verification code has expired",
            error: "CODE_EXPIRED",
          },
        ];
      } else {
        return [
          400,
          {
            success: false,
            message: "Invalid verification code",
            error: "INVALID_CODE",
          },
        ];
      }
    });

    // Mock rate limiting
    let attempts = 0;
    mock.onPost("/api/auth/check-attempts/").reply(() => {
      attempts += 1;
      if (attempts > 3) {
        return [
          429,
          {
            success: false,
            message: "Too many attempts. Please try again in 15 minutes.",
            error: "RATE_LIMITED",
            retryAfter: 900, // seconds
          },
        ];
      }
      return [200, { success: true, attempts: attempts }];
    });

    // Mock time-based expiration
    const now = new Date();
    mock.onGet("/api/server/time").reply(200, {
      timestamp: Math.floor(now.getTime() / 1000),
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();

    // Navigate to verification screen
    // This would need to be adjusted based on your app flow
    await waitFor(element(by.id("login-screen")))
      .toBeVisible()
      .withTimeout(2000);
    await element(by.id("register-link")).tap();
    await element(by.id("email-option")).tap();
    await element(by.id("email-input")).typeText(TEST_EMAIL);
    await element(by.id("password-input")).typeText("Password123!");
    await element(by.id("password-confirm-input")).typeText("Password123!");
    await element(by.id("terms-checkbox")).tap();
    await element(by.id("submit-button")).tap();

    // Should be on verification screen now
    await waitFor(element(by.id("verification-screen")))
      .toBeVisible()
      .withTimeout(3000);
  });

  afterAll(async () => {
    // Clean up mocks
    mock.restore();
  });

  test("Should validate correct verification code format", async () => {
    // Test with too short code
    await element(by.id("verification-code-input")).typeText("123");
    await element(by.id("verify-button")).tap();

    // Should show format error
    await waitFor(element(by.id("verification-error")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("verification-error"))).toHaveText(
      "Please enter a 6-digit code",
    );

    // Clear and test with invalid characters
    await element(by.id("verification-code-input")).clearText();
    await element(by.id("verification-code-input")).typeText("12A34B");
    await element(by.id("verify-button")).tap();

    // Should show format error
    await waitFor(element(by.id("verification-error")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("verification-error"))).toHaveText(
      "Code must contain only numbers",
    );
  });

  test("Should verify valid code successfully", async () => {
    // Enter valid code
    await element(by.id("verification-code-input")).clearText();
    await element(by.id("verification-code-input")).typeText(VALID_CODE);

    // Track API call
    let validationPayload = null;
    mock.onPost("/api/auth/verify-code/").reply((config) => {
      validationPayload = JSON.parse(config.data);
      if (validationPayload.code === VALID_CODE) {
        return [
          200,
          {
            success: true,
            token: "test-jwt-token-12345",
          },
        ];
      }
      return [400, { success: false }];
    });

    // Submit verification
    await element(by.id("verify-button")).tap();

    // Should navigate to success/next screen
    await waitFor(element(by.id("onboarding-screen")))
      .toBeVisible()
      .withTimeout(3000);

    // Verify correct payload was sent
    expect(validationPayload).not.toBeNull();
    expect(validationPayload.code).toBe(VALID_CODE);
    expect(validationPayload.email).toBe(TEST_EMAIL);
  });

  test("Should handle invalid verification code", async () => {
    // Enter invalid code
    await element(by.id("verification-code-input")).clearText();
    await element(by.id("verification-code-input")).typeText(INVALID_CODE);

    // Submit verification
    await element(by.id("verify-button")).tap();

    // Should show error message
    await waitFor(element(by.id("verification-error")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("verification-error"))).toHaveText(
      "Invalid verification code",
    );

    // Verify we stay on verification screen
    await expect(element(by.id("verification-screen"))).toBeVisible();
  });

  test("Should handle expired verification code", async () => {
    // Enter expired code
    await element(by.id("verification-code-input")).clearText();
    await element(by.id("verification-code-input")).typeText(EXPIRED_CODE);

    // Submit verification
    await element(by.id("verify-button")).tap();

    // Should show expiration error
    await waitFor(element(by.id("verification-error")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("verification-error"))).toHaveText(
      "Verification code has expired",
    );

    // Verify resend button is enabled
    await expect(element(by.id("resend-code-button"))).toBeVisible();
    await expect(element(by.id("resend-code-button"))).toBeEnabled();
  });

  test("Should handle rate limiting for verification attempts", async () => {
    // Reset attempts count in our mock
    let attempts = 0;
    mock.onPost("/api/auth/verify-code/").reply((config) => {
      attempts += 1;
      if (attempts > 3) {
        return [
          429,
          {
            success: false,
            message: "Too many attempts. Please try again in 15 minutes.",
            error: "RATE_LIMITED",
            retryAfter: 900,
          },
        ];
      }
      return [400, { success: false, message: "Invalid verification code" }];
    });

    // Make multiple attempts with invalid code
    for (let i = 0; i < 4; i++) {
      await element(by.id("verification-code-input")).clearText();
      await element(by.id("verification-code-input")).typeText(INVALID_CODE);
      await element(by.id("verify-button")).tap();

      // Small delay between attempts
      await new Promise((resolve) => setTimeout(resolve, 500));
    }

    // After 4th attempt, should see rate limit error
    await waitFor(element(by.id("rate-limit-error")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("rate-limit-error"))).toHaveText(
      "Too many attempts. Please try again in 15 minutes.",
    );

    // Verify retry countdown is shown
    await expect(element(by.id("retry-countdown"))).toBeVisible();

    // Verify submit button is disabled
    await expect(element(by.id("verify-button"))).toBeDisabled();
  });

  test("Should handle controlled time-based expiration", async () => {
    // Mock an expired timestamp (30 minutes in the future)
    const thirtyMinutesLater = new Date();
    thirtyMinutesLater.setMinutes(thirtyMinutesLater.getMinutes() + 30);

    mock.onGet("/api/server/time").reply(200, {
      timestamp: Math.floor(thirtyMinutesLater.getTime() / 1000),
    });

    // Enter valid code but with expired timestamp
    await element(by.id("verification-code-input")).clearText();
    await element(by.id("verification-code-input")).typeText(VALID_CODE);

    // Force code expiration check (might need a refresh button or similar in your app)
    await element(by.id("refresh-button")).tap();

    // Should show expiration message
    await waitFor(element(by.id("expiration-message")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("expiration-message"))).toHaveText(
      "Your verification session has expired",
    );

    // Verify resend/restart button is available
    await expect(element(by.id("restart-verification-button"))).toBeVisible();
  });
});
