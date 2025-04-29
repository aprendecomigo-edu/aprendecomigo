const { device, element, by, waitFor } = require("detox");
const axios = require("axios");
const MockAdapter = require("axios-mock-adapter");

// Setup axios mock
const mock = new MockAdapter(axios);

// Test data
const PRIMARY_EMAIL = "primary@example.com";
const PRIMARY_PHONE = "+1234567890";
const SECONDARY_EMAIL = "secondary@example.com";
const SECONDARY_PHONE = "+1987654321";
const PASSWORD = "Password123!";
const VERIFICATION_CODE = "123456";
const AUTH_TOKEN = "test-jwt-token-12345";

describe("Changing Primary Contact", () => {
  // Setup before tests
  beforeAll(async () => {
    await device.launchApp();

    // Mock verification APIs
    mock.onPost("/api/auth/send-verification-code/").reply(200, {
      success: true,
      message: "Verification code sent successfully",
    });

    mock.onPost("/api/auth/verify-code/").reply(200, {
      success: true,
      message: "Code verified successfully",
    });

    // Mock contact change endpoint
    mock.onPut("/api/users/contact/primary/").reply(200, {
      success: true,
      message: "Primary contact changed successfully",
      new_token: "new-jwt-token-67890", // New token with updated claims
    });

    // Mock re-authentication endpoint
    mock.onPost("/api/auth/reauthenticate/").reply((config) => {
      const data = JSON.parse(config.data);
      if (data.password === PASSWORD) {
        return [200, { success: true }];
      }
      return [400, { success: false, message: "Invalid password" }];
    });

    // Mock notification service
    mock.onPost("/api/notifications/send/").reply(200, {
      success: true,
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();

    // Mock authenticated user state
    await device.openURL({
      url: "aprendecomigo://testing/authenticated",
      sourceApp: "com.aprendecomigo.test",
    });

    // Wait for the app to load in authenticated state
    await waitFor(element(by.id("home-screen")))
      .toBeVisible()
      .withTimeout(5000);

    // Mock API response for getting user profile with both primary and secondary contacts
    mock.onGet("/api/users/profile/").reply(200, {
      email: PRIMARY_EMAIL,
      phone: PRIMARY_PHONE,
      secondary_email: SECONDARY_EMAIL,
      secondary_phone: SECONDARY_PHONE,
      email_verified: true,
      phone_verified: true,
      secondary_email_verified: true,
      secondary_phone_verified: true,
    });

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

  test("Should display current primary and secondary contacts", async () => {
    // Force refresh profile data
    await element(by.id("refresh-button")).tap();

    // Verify current contacts are displayed correctly
    await waitFor(element(by.id("primary-email")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("primary-email"))).toHaveText(PRIMARY_EMAIL);

    await waitFor(element(by.id("primary-phone")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("primary-phone"))).toHaveText(PRIMARY_PHONE);

    await waitFor(element(by.id("secondary-email")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("secondary-email"))).toHaveText(SECONDARY_EMAIL);

    await waitFor(element(by.id("secondary-phone")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("secondary-phone"))).toHaveText(SECONDARY_PHONE);
  });

  test("Should require password for changing primary contact", async () => {
    // Tap on the secondary email to make it primary
    await element(by.id("make-primary-button-email")).tap();

    // Should show password confirmation modal
    await waitFor(element(by.id("password-confirmation-modal")))
      .toBeVisible()
      .withTimeout(2000);

    // Try with empty password
    await element(by.id("password-input")).clearText();
    await element(by.id("confirm-button")).tap();

    // Should show validation error
    await waitFor(element(by.id("password-error")))
      .toBeVisible()
      .withTimeout(2000);

    // Try with wrong password
    await element(by.id("password-input")).clearText();
    await element(by.id("password-input")).typeText("WrongPassword!");

    // Mock failed authentication
    mock.onPost("/api/auth/reauthenticate/").reply(400, {
      success: false,
      message: "Invalid password",
      error: "INVALID_CREDENTIALS",
    });

    await element(by.id("confirm-button")).tap();

    // Should show invalid password error
    await waitFor(element(by.id("password-error")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("password-error"))).toHaveText(
      "Invalid password",
    );
  });

  test("Should change primary contact from email to secondary email", async () => {
    // Tap on the secondary email to make it primary
    await element(by.id("make-primary-button-email")).tap();

    // Should show password confirmation modal
    await waitFor(element(by.id("password-confirmation-modal")))
      .toBeVisible()
      .withTimeout(2000);

    // Enter correct password
    await element(by.id("password-input")).clearText();
    await element(by.id("password-input")).typeText(PASSWORD);

    // Mock successful authentication
    mock.onPost("/api/auth/reauthenticate/").reply(200, {
      success: true,
    });

    // Track API call payload
    let changePayload = null;
    mock.onPut("/api/users/contact/primary/").reply((config) => {
      changePayload = JSON.parse(config.data);
      return [
        200,
        {
          success: true,
          message: "Primary contact changed successfully",
          new_token: "new-jwt-token-67890",
        },
      ];
    });

    // Track notification payload
    let notificationPayload = null;
    mock.onPost("/api/notifications/send/").reply((config) => {
      notificationPayload = JSON.parse(config.data);
      return [200, { success: true }];
    });

    // Confirm change
    await element(by.id("confirm-button")).tap();

    // Should show success message
    await waitFor(element(by.id("success-message")))
      .toBeVisible()
      .withTimeout(3000);

    // Mock updated profile API response
    mock.onGet("/api/users/profile/").reply(200, {
      email: SECONDARY_EMAIL, // Now this is primary
      phone: PRIMARY_PHONE,
      secondary_email: PRIMARY_EMAIL, // Previous primary is now secondary
      secondary_phone: SECONDARY_PHONE,
      email_verified: true,
      phone_verified: true,
      secondary_email_verified: true,
      secondary_phone_verified: true,
    });

    // Refresh profile to see changes
    await element(by.id("refresh-button")).tap();

    // Verify the contacts have been swapped
    await waitFor(element(by.id("primary-email")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("primary-email"))).toHaveText(SECONDARY_EMAIL);

    await waitFor(element(by.id("secondary-email")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("secondary-email"))).toHaveText(PRIMARY_EMAIL);

    // Verify correct API payload
    expect(changePayload).not.toBeNull();
    expect(changePayload.new_primary_type).toBe("email");
    expect(changePayload.new_primary_value).toBe(SECONDARY_EMAIL);

    // Verify notifications were sent to both emails
    expect(notificationPayload).not.toBeNull();
    expect(notificationPayload.recipients).toContain(PRIMARY_EMAIL);
    expect(notificationPayload.recipients).toContain(SECONDARY_EMAIL);
    expect(notificationPayload.notification_type).toBe(
      "PRIMARY_CONTACT_CHANGED",
    );
  });

  test("Should change primary contact from email to phone", async () => {
    // Tap on the primary phone to make it primary
    await element(by.id("make-primary-button-phone")).tap();

    // Should show password confirmation modal
    await waitFor(element(by.id("password-confirmation-modal")))
      .toBeVisible()
      .withTimeout(2000);

    // Enter correct password
    await element(by.id("password-input")).clearText();
    await element(by.id("password-input")).typeText(PASSWORD);

    // Track API call payload
    let changePayload = null;
    mock.onPut("/api/users/contact/primary/").reply((config) => {
      changePayload = JSON.parse(config.data);
      return [
        200,
        {
          success: true,
          message: "Primary contact changed successfully",
          new_token: "new-jwt-token-67890",
        },
      ];
    });

    // Confirm change
    await element(by.id("confirm-button")).tap();

    // Should show success message
    await waitFor(element(by.id("success-message")))
      .toBeVisible()
      .withTimeout(3000);

    // Mock updated profile API response
    mock.onGet("/api/users/profile/").reply(200, {
      email: PRIMARY_EMAIL,
      phone: PRIMARY_PHONE, // Now phone is primary
      secondary_email: SECONDARY_EMAIL,
      secondary_phone: SECONDARY_PHONE,
      email_verified: true,
      phone_verified: true,
      secondary_email_verified: true,
      secondary_phone_verified: true,
      primary_contact_type: "phone", // Important field indicating primary type
    });

    // Refresh profile to see changes
    await element(by.id("refresh-button")).tap();

    // Verify the primary indicator has moved to phone
    await waitFor(element(by.id("primary-indicator-phone")))
      .toBeVisible()
      .withTimeout(2000);

    // Verify correct API payload
    expect(changePayload).not.toBeNull();
    expect(changePayload.new_primary_type).toBe("phone");
    expect(changePayload.new_primary_value).toBe(PRIMARY_PHONE);
  });

  test("Should verify login with new primary contact works after app restart", async () => {
    // First change the primary contact
    await element(by.id("make-primary-button-email")).tap();
    await waitFor(element(by.id("password-confirmation-modal")))
      .toBeVisible()
      .withTimeout(2000);
    await element(by.id("password-input")).typeText(PASSWORD);
    await element(by.id("confirm-button")).tap();
    await waitFor(element(by.id("success-message")))
      .toBeVisible()
      .withTimeout(3000);

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

    // Restart app (this simulates app restart)
    await device.reloadReactNative();

    // Mock successful login with new primary email
    mock.onPost("/api/auth/token/").reply((config) => {
      const data = JSON.parse(config.data);
      if (data.email === SECONDARY_EMAIL && data.password === PASSWORD) {
        return [
          200,
          {
            access: "new-access-token",
            refresh: "new-refresh-token",
          },
        ];
      }
      return [400, { success: false, message: "Invalid credentials" }];
    });

    // Login with new primary email
    await element(by.id("email-input")).typeText(SECONDARY_EMAIL);
    await element(by.id("password-input")).typeText(PASSWORD);
    await element(by.id("login-button")).tap();

    // Should navigate to home screen
    await waitFor(element(by.id("home-screen")))
      .toBeVisible()
      .withTimeout(5000);

    // Verify login was successful
    await expect(element(by.id("home-screen"))).toBeVisible();
  });

  test("Should verify old primary contact no longer works for login", async () => {
    // Logout if not already logged out
    if (await element(by.id("home-screen")).isVisible()) {
      await element(by.id("settings-tab")).tap();
      await waitFor(element(by.id("settings-screen")))
        .toBeVisible()
        .withTimeout(2000);
      await element(by.id("logout-button")).tap();
      await waitFor(element(by.id("login-screen")))
        .toBeVisible()
        .withTimeout(3000);
    }

    // Mock unsuccessful login with old primary email
    mock.onPost("/api/auth/token/").reply((config) => {
      const data = JSON.parse(config.data);
      if (data.email === PRIMARY_EMAIL) {
        return [
          400,
          {
            success: false,
            message:
              "This email is registered as a secondary contact. Please use your primary contact to login.",
            error: "SECONDARY_CONTACT",
          },
        ];
      }
      return [400, { success: false, message: "Invalid credentials" }];
    });

    // Try to login with old primary email
    await element(by.id("email-input")).typeText(PRIMARY_EMAIL);
    await element(by.id("password-input")).typeText(PASSWORD);
    await element(by.id("login-button")).tap();

    // Should show specific error
    await waitFor(element(by.id("error-message")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.id("error-message"))).toHaveText(
      "This email is registered as a secondary contact. Please use your primary contact to login.",
    );

    // Verify still on login screen
    await expect(element(by.id("login-screen"))).toBeVisible();
  });

  test("Should handle simultaneous settings changes gracefully", async () => {
    // This test simulates a potential race condition when changing multiple settings

    // Mock a delayed response for the first change
    let firstChangeComplete = false;
    mock.onPut("/api/users/contact/primary/").reply((config) => {
      const data = JSON.parse(config.data);

      // If this is the first request, delay the response
      if (data.new_primary_value === SECONDARY_EMAIL && !firstChangeComplete) {
        return new Promise((resolve) => {
          setTimeout(() => {
            firstChangeComplete = true;
            resolve([
              200,
              {
                success: true,
                message: "Primary contact changed successfully",
                new_token: "new-jwt-token-67890",
              },
            ]);
          }, 2000);
        });
      }

      // For other requests, respond immediately
      return [
        200,
        {
          success: true,
          message: "Primary contact changed successfully",
          new_token: "new-jwt-token-67890",
        },
      ];
    });

    // Start the first change
    await element(by.id("make-primary-button-email")).tap();
    await waitFor(element(by.id("password-confirmation-modal")))
      .toBeVisible()
      .withTimeout(2000);
    await element(by.id("password-input")).typeText(PASSWORD);
    await element(by.id("confirm-button")).tap();

    // Should show loading indicator
    await waitFor(element(by.id("loading-indicator")))
      .toBeVisible()
      .withTimeout(1000);

    // Attempt to make another change while the first one is processing
    await element(by.id("make-primary-button-phone")).tap();

    // Should show an error or warning that another change is in progress
    await waitFor(element(by.id("operation-in-progress-warning")))
      .toBeVisible()
      .withTimeout(2000);

    // Wait for the first change to complete
    await waitFor(element(by.id("success-message")))
      .toBeVisible()
      .withTimeout(3000);

    // Now try the second change
    await element(by.id("make-primary-button-phone")).tap();
    await waitFor(element(by.id("password-confirmation-modal")))
      .toBeVisible()
      .withTimeout(2000);
    await element(by.id("password-input")).typeText(PASSWORD);
    await element(by.id("confirm-button")).tap();

    // Should complete successfully
    await waitFor(element(by.id("success-message")))
      .toBeVisible()
      .withTimeout(3000);
  });
});
