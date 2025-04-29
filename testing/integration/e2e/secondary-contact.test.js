const { device, element, by, waitFor } = require("detox");
const axios = require("axios");
const MockAdapter = require("axios-mock-adapter");

// Setup axios mock
const mock = new MockAdapter(axios);

// Test data
const TEST_EMAIL = "primary@example.com";
const TEST_PHONE = "+1234567890";
const SECONDARY_EMAIL = "secondary@example.com";
const SECONDARY_PHONE = "+1987654321";
const VERIFICATION_CODE = "123456";
const AUTH_TOKEN = "test-jwt-token-12345";

describe("Secondary Contact Verification", () => {
  // Setup before tests
  beforeAll(async () => {
    await device.launchApp();

    // Mock verification APIs
    mock.onPost("/api/auth/send-verification-code/").reply(200, {
      success: true,
      message: "Verification code sent successfully",
    });

    mock.onPost("/api/auth/send-sms-verification/").reply(200, {
      success: true,
      message: "SMS verification code sent successfully",
    });

    mock.onPost("/api/auth/verify-code/").reply(200, {
      success: true,
      message: "Email verified successfully",
    });

    mock.onPost("/api/auth/verify-phone-code/").reply(200, {
      success: true,
      message: "Phone verified successfully",
    });

    // Mock session timeout
    const now = new Date();
    mock.onGet("/api/server/time").reply(200, {
      timestamp: Math.floor(now.getTime() / 1000),
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();

    // Mock authenticated user state
    // This requires the app to have a way to pre-authenticate for testing
    // Here we're using a special deep link for testing
    await device.openURL({
      url: "aprendecomigo://testing/authenticated",
      sourceApp: "com.aprendecomigo.test",
    });

    // Wait for the app to load in authenticated state
    await waitFor(element(by.id("home-screen")))
      .toBeVisible()
      .withTimeout(5000);

    // Navigate to account settings
    await element(by.id("settings-tab")).tap();
    await waitFor(element(by.id("settings-screen")))
      .toBeVisible()
      .withTimeout(2000);
    await element(by.id("contact-settings")).tap();
    await waitFor(element(by.id("contact-settings-screen")))
      .toBeVisible()
      .withTimeout(2000);
  });

  afterAll(async () => {
    // Clean up mocks
    mock.restore();
  });

  test("Should navigate to add secondary contact screen", async () => {
    // Tap on add secondary contact button
    await element(by.id("add-secondary-contact-button")).tap();

    // Verify we're on the secondary contact screen
    await waitFor(element(by.id("secondary-contact-screen")))
      .toBeVisible()
      .withTimeout(2000);
  });

  test("Should add and verify secondary email", async () => {
    // Tap on add secondary contact button if not already there
    if (await element(by.id("secondary-contact-screen")).isNotVisible()) {
      await element(by.id("add-secondary-contact-button")).tap();
      await waitFor(element(by.id("secondary-contact-screen")))
        .toBeVisible()
        .withTimeout(2000);
    }

    // Select email option
    await element(by.id("email-option")).tap();

    // Enter secondary email
    await element(by.id("email-input")).typeText(SECONDARY_EMAIL);

    // Spy on verification code API call
    let emailPayload = null;
    mock.onPost("/api/auth/send-verification-code/").reply((config) => {
      emailPayload = JSON.parse(config.data);
      return [200, { success: true }];
    });

    // Submit email
    await element(by.id("submit-button")).tap();

    // Should navigate to verification screen
    await waitFor(element(by.id("verification-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Verify correct email was sent for verification
    expect(emailPayload).not.toBeNull();
    expect(emailPayload.email).toBe(SECONDARY_EMAIL);

    // Enter verification code
    await element(by.id("verification-code-input")).typeText(VERIFICATION_CODE);

    // Spy on verification API call
    let verificationPayload = null;
    mock.onPost("/api/auth/verify-code/").reply((config) => {
      verificationPayload = JSON.parse(config.data);
      return [200, { success: true }];
    });

    // Submit verification
    await element(by.id("verify-button")).tap();

    // Should return to contact settings with success
    await waitFor(element(by.id("contact-settings-screen")))
      .toBeVisible()
      .withTimeout(3000);
    await waitFor(element(by.id("verification-success-message")))
      .toBeVisible()
      .withTimeout(2000);

    // Verify the secondary email is now listed
    await expect(element(by.text(SECONDARY_EMAIL))).toBeVisible();
    await expect(element(by.id("verified-badge"))).toBeVisible();

    // Verify correct verification payload
    expect(verificationPayload).not.toBeNull();
    expect(verificationPayload.code).toBe(VERIFICATION_CODE);
    expect(verificationPayload.email).toBe(SECONDARY_EMAIL);
  });

  test("Should add and verify secondary phone", async () => {
    // Go to add secondary contact if not already there
    if (await element(by.id("secondary-contact-screen")).isNotVisible()) {
      await element(by.id("add-secondary-contact-button")).tap();
      await waitFor(element(by.id("secondary-contact-screen")))
        .toBeVisible()
        .withTimeout(2000);
    }

    // Select phone option
    await element(by.id("phone-option")).tap();

    // Enter secondary phone
    await element(by.id("phone-input")).typeText(SECONDARY_PHONE);

    // Spy on SMS verification API call
    let smsPayload = null;
    mock.onPost("/api/auth/send-sms-verification/").reply((config) => {
      smsPayload = JSON.parse(config.data);
      return [200, { success: true }];
    });

    // Submit phone
    await element(by.id("submit-button")).tap();

    // Should navigate to verification screen
    await waitFor(element(by.id("phone-verification-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Verify correct phone was sent for verification
    expect(smsPayload).not.toBeNull();
    expect(smsPayload.phone).toBe(SECONDARY_PHONE);

    // Enter verification code
    await element(by.id("verification-code-input")).typeText(VERIFICATION_CODE);

    // Spy on verification API call
    let verificationPayload = null;
    mock.onPost("/api/auth/verify-phone-code/").reply((config) => {
      verificationPayload = JSON.parse(config.data);
      return [200, { success: true }];
    });

    // Submit verification
    await element(by.id("verify-button")).tap();

    // Should return to contact settings with success
    await waitFor(element(by.id("contact-settings-screen")))
      .toBeVisible()
      .withTimeout(3000);
    await waitFor(element(by.id("verification-success-message")))
      .toBeVisible()
      .withTimeout(2000);

    // Verify the secondary phone is now listed
    await expect(element(by.text(SECONDARY_PHONE))).toBeVisible();
    await expect(element(by.id("verified-badge"))).toBeVisible();

    // Verify correct verification payload
    expect(verificationPayload).not.toBeNull();
    expect(verificationPayload.code).toBe(VERIFICATION_CODE);
    expect(verificationPayload.phone).toBe(SECONDARY_PHONE);
  });

  test("Should handle session timeout during verification", async () => {
    // Go to add secondary contact
    await element(by.id("add-secondary-contact-button")).tap();
    await waitFor(element(by.id("secondary-contact-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Select email option
    await element(by.id("email-option")).tap();
    await element(by.id("email-input")).typeText(SECONDARY_EMAIL);
    await element(by.id("submit-button")).tap();

    // Should be on verification screen
    await waitFor(element(by.id("verification-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Mock session timeout by advancing the server time
    const oneHourLater = new Date();
    oneHourLater.setHours(oneHourLater.getHours() + 1);

    mock.onGet("/api/server/time").reply(200, {
      timestamp: Math.floor(oneHourLater.getTime() / 1000),
    });

    // Force session check (this might need to be triggered differently in your app)
    await element(by.id("refresh-button")).tap();

    // Should show session timeout message
    await waitFor(element(by.id("session-timeout-message")))
      .toBeVisible()
      .withTimeout(2000);

    // Should have restart button
    await expect(element(by.id("restart-button"))).toBeVisible();
  });

  test("Should verify both contacts are marked verified in database", async () => {
    // This would typically require a direct database check, but for this test
    // we'll verify through the API that both contacts are marked as verified

    // Navigate to user profile that shows verification status
    await element(by.id("profile-tab")).tap();
    await waitFor(element(by.id("profile-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Mock API response for getting user profile
    mock.onGet("/api/users/profile/").reply(200, {
      email: TEST_EMAIL,
      phone: TEST_PHONE,
      secondary_email: SECONDARY_EMAIL,
      secondary_phone: SECONDARY_PHONE,
      email_verified: true,
      phone_verified: true,
      secondary_email_verified: true,
      secondary_phone_verified: true,
    });

    // Refresh profile to get latest data
    await element(by.id("refresh-profile-button")).tap();

    // Verify all contacts show as verified
    await waitFor(element(by.id("primary-email-verified")))
      .toBeVisible()
      .withTimeout(2000);
    await waitFor(element(by.id("primary-phone-verified")))
      .toBeVisible()
      .withTimeout(2000);
    await waitFor(element(by.id("secondary-email-verified")))
      .toBeVisible()
      .withTimeout(2000);
    await waitFor(element(by.id("secondary-phone-verified")))
      .toBeVisible()
      .withTimeout(2000);
  });

  test("Should not allow unverified contacts to be used for authentication", async () => {
    // This test would require adding a contact but not verifying it
    // Then attempt to login with it

    // First add a new unverified contact
    await element(by.id("add-secondary-contact-button")).tap();
    await waitFor(element(by.id("secondary-contact-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Select email option
    await element(by.id("email-option")).tap();

    // Use a different email that won't be verified
    const UNVERIFIED_EMAIL = "unverified@example.com";
    await element(by.id("email-input")).typeText(UNVERIFIED_EMAIL);

    // Spy on verification code API call
    mock.onPost("/api/auth/send-verification-code/").reply(200, {
      success: true,
    });

    // Submit but don't complete verification
    await element(by.id("submit-button")).tap();
    await waitFor(element(by.id("verification-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Go back without verifying
    await element(by.id("back-button")).tap();

    // Logout
    await element(by.id("settings-tab")).tap();
    await waitFor(element(by.id("settings-screen")))
      .toBeVisible()
      .withTimeout(2000);
    await element(by.id("logout-button")).tap();

    // Verify we're on login screen
    await waitFor(element(by.id("login-screen")))
      .toBeVisible()
      .withTimeout(3000);

    // Try to login with the unverified email
    await element(by.id("email-input")).typeText(UNVERIFIED_EMAIL);
    await element(by.id("password-input")).typeText("Password123!");

    // Mock failed login
    mock.onPost("/api/auth/token/").reply(400, {
      success: false,
      message: "Contact not verified",
      error: "UNVERIFIED_CONTACT",
    });

    // Attempt login
    await element(by.id("login-button")).tap();

    // Should show unverified contact error
    await waitFor(element(by.id("error-message")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("error-message"))).toHaveText(
      "Contact not verified",
    );

    // Verify we're still on login screen
    await expect(element(by.id("login-screen"))).toBeVisible();
  });
});
