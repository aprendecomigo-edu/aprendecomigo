/**
 * Password Reset E2E Tests
 *
 * Tests the password reset functionality in the Aprende Conmigo application
 */

describe("Password Reset Flow", () => {
  beforeAll(async () => {
    await device.launchApp({
      delete: true, // Start with a fresh app state
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();

    // Navigate to login screen if not already there
    if (await element(by.text("Welcome Back")).isNotVisible()) {
      // If on signup screen, go back to login
      if (await element(by.text("Create Account")).isVisible()) {
        await element(by.text("Already have an account? Log In")).tap();
      } else {
        // Return to initial screen and tap login
        await device.reloadReactNative();
        await element(by.text("Log In")).tap();
      }
    }

    // Navigate to forgot password screen
    await element(by.text("Forgot Password?")).tap();
  });

  it("should display forgot password screen with email input", async () => {
    // Verify forgot password screen elements
    await expect(element(by.text("Reset Your Password"))).toBeVisible();
    await expect(element(by.id("email-input"))).toBeVisible();
    await expect(element(by.text("Send Reset Link"))).toBeVisible();
    await expect(element(by.text("Back to Login"))).toBeVisible();
  });

  it("should validate required email field", async () => {
    // Submit without filling email
    await element(by.text("Send Reset Link")).tap();

    // Check error message
    await expect(element(by.text("Email is required"))).toBeVisible();
  });

  it("should validate email format", async () => {
    // Enter invalid email
    await element(by.id("email-input")).typeText("invalid-email");

    // Submit form
    await element(by.text("Send Reset Link")).tap();

    // Check error message
    await expect(element(by.text("Please enter a valid email"))).toBeVisible();
  });

  it("should handle non-existent email error", async () => {
    // Enter email that doesn't exist in the system
    await element(by.id("email-input")).typeText("nonexistent@example.com");

    // Submit form
    await element(by.text("Send Reset Link")).tap();

    // Check error message
    await waitFor(element(by.text("No account found with this email")))
      .toBeVisible()
      .withTimeout(5000);
  });

  it("should send reset email successfully", async () => {
    // Enter valid email that exists in the system
    await element(by.id("email-input")).typeText("existing@example.com");

    // Submit form
    await element(by.text("Send Reset Link")).tap();

    // Check success message
    await waitFor(element(by.text("Password reset email sent")))
      .toBeVisible()
      .withTimeout(5000);

    // Verify instruction message is displayed
    await expect(
      element(by.text("Check your email for instructions")),
    ).toBeVisible();
  });

  it("should navigate back to login from forgot password screen", async () => {
    // Tap on back to login link
    await element(by.text("Back to Login")).tap();

    // Verify we're on the login screen
    await expect(element(by.text("Welcome Back"))).toBeVisible();
  });

  // This test simulates the user following the reset link and setting a new password
  // Note: This is a more complex E2E test that may require mocking the email link behavior
  it("should reset password when following email link", async () => {
    // Mock: Simulate user following reset link from email
    // In a real scenario, you might need to intercept the email or use a deep link

    // For testing purposes, we'll use a mock function to simulate the deep link behavior
    await device.openURL({
      url: "aprendeconmigo://reset-password?token=mock-valid-token",
    });

    // Verify reset password form is shown
    await expect(element(by.text("Set New Password"))).toBeVisible();
    await expect(element(by.id("new-password-input"))).toBeVisible();
    await expect(element(by.id("confirm-password-input"))).toBeVisible();
    await expect(element(by.text("Reset Password"))).toBeVisible();

    // Enter new password
    await element(by.id("new-password-input")).typeText("NewPassword123!");
    await element(by.id("confirm-password-input")).typeText("NewPassword123!");

    // Submit form
    await element(by.text("Reset Password")).tap();

    // Check success message
    await waitFor(element(by.text("Password reset successful")))
      .toBeVisible()
      .withTimeout(5000);

    // Verify redirection to login
    await expect(element(by.text("Welcome Back"))).toBeVisible();

    // Verify we can login with the new password
    await element(by.id("email-input")).typeText("existing@example.com");
    await element(by.id("password-input")).typeText("NewPassword123!");
    await element(by.text("Log In")).tap();

    // Verify successful login
    await waitFor(element(by.id("dashboard-screen")))
      .toBeVisible()
      .withTimeout(5000);
  });

  it("should validate password strength on reset form", async () => {
    // Mock: Simulate user following reset link from email
    await device.openURL({
      url: "aprendeconmigo://reset-password?token=mock-valid-token",
    });

    // Verify reset password form is shown
    await expect(element(by.text("Set New Password"))).toBeVisible();

    // Enter weak password
    await element(by.id("new-password-input")).typeText("weak");
    await element(by.id("confirm-password-input")).typeText("weak");

    // Submit form
    await element(by.text("Reset Password")).tap();

    // Check error message
    await expect(
      element(
        by.text(
          "Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one number, and one special character",
        ),
      ),
    ).toBeVisible();
  });

  it("should validate password matching on reset form", async () => {
    // Mock: Simulate user following reset link from email
    await device.openURL({
      url: "aprendeconmigo://reset-password?token=mock-valid-token",
    });

    // Verify reset password form is shown
    await expect(element(by.text("Set New Password"))).toBeVisible();

    // Enter mismatched passwords
    await element(by.id("new-password-input")).typeText("Password123!");
    await element(by.id("confirm-password-input")).typeText(
      "DifferentPassword123!",
    );

    // Submit form
    await element(by.text("Reset Password")).tap();

    // Check error message
    await expect(element(by.text("Passwords do not match"))).toBeVisible();
  });

  it("should handle invalid or expired token", async () => {
    // Mock: Simulate user following reset link with invalid token
    await device.openURL({
      url: "aprendeconmigo://reset-password?token=invalid-or-expired-token",
    });

    // Check error message
    await waitFor(element(by.text("Invalid or expired reset link")))
      .toBeVisible()
      .withTimeout(5000);

    // Verify option to request a new link
    await expect(element(by.text("Request a new reset link"))).toBeVisible();

    // Tap on request new link
    await element(by.text("Request a new reset link")).tap();

    // Verify return to forgot password screen
    await expect(element(by.text("Reset Your Password"))).toBeVisible();
  });
});
