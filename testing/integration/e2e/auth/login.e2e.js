/**
 * Login E2E Tests
 *
 * Tests the login functionality in the Aprende Conmigo application
 */

describe("Login Flow", () => {
  beforeAll(async () => {
    await device.launchApp({
      delete: true, // Start with a fresh app state
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it("should display login screen with required fields", async () => {
    // Navigate to login screen
    await element(by.text("Log In")).tap();

    // Verify login screen elements
    await expect(element(by.text("Welcome Back"))).toBeVisible();
    await expect(element(by.id("email-input"))).toBeVisible();
    await expect(element(by.id("password-input"))).toBeVisible();
    await expect(element(by.text("Log In"))).toBeVisible();
    await expect(element(by.text("Forgot Password?"))).toBeVisible();
    await expect(
      element(by.text("Don't have an account? Sign Up")),
    ).toBeVisible();
  });

  it("should validate email format", async () => {
    // Navigate to login screen
    await element(by.text("Log In")).tap();

    // Enter invalid email
    await element(by.id("email-input")).typeText("invalid-email");
    await element(by.id("password-input")).typeText("password123");

    // Submit form
    await element(by.text("Log In")).tap();

    // Check error message
    await expect(element(by.text("Please enter a valid email"))).toBeVisible();
  });

  it("should validate required fields", async () => {
    // Navigate to login screen
    await element(by.text("Log In")).tap();

    // Submit without filling any fields
    await element(by.text("Log In")).tap();

    // Check error messages
    await expect(element(by.text("Email is required"))).toBeVisible();
    await expect(element(by.text("Password is required"))).toBeVisible();
  });

  it("should handle invalid login credentials", async () => {
    // Navigate to login screen
    await element(by.text("Log In")).tap();

    // Enter valid email format but wrong credentials
    await element(by.id("email-input")).typeText("wrong@example.com");
    await element(by.id("password-input")).typeText("wrongpassword");

    // Submit form
    await element(by.text("Log In")).tap();

    // Check error message
    await waitFor(element(by.text("Invalid email or password")))
      .toBeVisible()
      .withTimeout(5000);
  });

  it("should login successfully with valid credentials", async () => {
    // Navigate to login screen
    await element(by.text("Log In")).tap();

    // Enter valid credentials
    await element(by.id("email-input")).typeText("test@example.com");
    await element(by.id("password-input")).typeText("Password123!");

    // Submit form
    await element(by.text("Log In")).tap();

    // Verify login successful and navigation to dashboard
    await waitFor(element(by.id("dashboard-screen")))
      .toBeVisible()
      .withTimeout(5000);
  });

  it("should navigate to signup screen from login", async () => {
    // Navigate to login screen
    await element(by.text("Log In")).tap();

    // Click on sign up link
    await element(by.text("Don't have an account? Sign Up")).tap();

    // Verify we're on the signup screen
    await expect(element(by.text("Create Account"))).toBeVisible();
  });

  it("should navigate to forgot password screen", async () => {
    // Navigate to login screen
    await element(by.text("Log In")).tap();

    // Click on forgot password link
    await element(by.text("Forgot Password?")).tap();

    // Verify we're on the forgot password screen
    await expect(element(by.text("Reset Your Password"))).toBeVisible();
  });

  it("should remember user after login", async () => {
    // Navigate to login screen
    await element(by.text("Log In")).tap();

    // Enter valid credentials
    await element(by.id("email-input")).typeText("test@example.com");
    await element(by.id("password-input")).typeText("Password123!");

    // Enable remember me
    await element(by.id("remember-me-checkbox")).tap();

    // Submit form
    await element(by.text("Log In")).tap();

    // Verify login successful
    await waitFor(element(by.id("dashboard-screen")))
      .toBeVisible()
      .withTimeout(5000);

    // Kill and restart app
    await device.terminateApp();
    await device.launchApp();

    // Verify user is still logged in (dashboard is visible without login)
    await waitFor(element(by.id("dashboard-screen")))
      .toBeVisible()
      .withTimeout(5000);
  });

  it("should show and hide password when toggle is pressed", async () => {
    // Navigate to login screen
    await element(by.text("Log In")).tap();

    // Enter password
    await element(by.id("password-input")).typeText("Password123!");

    // Verify password is hidden by default (secure text entry)
    await expect(element(by.id("password-input"))).toHaveToggleAttribute(
      "secureTextEntry",
      true,
    );

    // Tap show password icon
    await element(by.id("toggle-password-visibility")).tap();

    // Verify password is now visible
    await expect(element(by.id("password-input"))).toHaveToggleAttribute(
      "secureTextEntry",
      false,
    );

    // Tap hide password icon
    await element(by.id("toggle-password-visibility")).tap();

    // Verify password is hidden again
    await expect(element(by.id("password-input"))).toHaveToggleAttribute(
      "secureTextEntry",
      true,
    );
  });
});
