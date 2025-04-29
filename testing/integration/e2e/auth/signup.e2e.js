/**
 * Signup E2E Tests
 *
 * Tests the signup (registration) functionality in the Aprende Conmigo application
 */

describe("Signup Flow", () => {
  beforeAll(async () => {
    await device.launchApp({
      delete: true, // Start with a fresh app state
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it("should display signup screen with required fields", async () => {
    // Navigate to signup screen
    await element(by.text("Sign Up")).tap();

    // Verify signup screen elements
    await expect(element(by.text("Create Account"))).toBeVisible();
    await expect(element(by.id("name-input"))).toBeVisible();
    await expect(element(by.id("email-input"))).toBeVisible();
    await expect(element(by.id("password-input"))).toBeVisible();
    await expect(element(by.id("confirm-password-input"))).toBeVisible();
    await expect(element(by.text("Sign Up"))).toBeVisible();
    await expect(
      element(by.text("Already have an account? Log In")),
    ).toBeVisible();
  });

  it("should validate required fields", async () => {
    // Navigate to signup screen
    await element(by.text("Sign Up")).tap();

    // Submit without filling any fields
    await element(by.text("Sign Up")).tap();

    // Check error messages
    await expect(element(by.text("Name is required"))).toBeVisible();
    await expect(element(by.text("Email is required"))).toBeVisible();
    await expect(element(by.text("Password is required"))).toBeVisible();
    await expect(
      element(by.text("Confirm password is required")),
    ).toBeVisible();
  });

  it("should validate email format", async () => {
    // Navigate to signup screen
    await element(by.text("Sign Up")).tap();

    // Fill form with invalid email
    await element(by.id("name-input")).typeText("Test User");
    await element(by.id("email-input")).typeText("invalid-email");
    await element(by.id("password-input")).typeText("Password123!");
    await element(by.id("confirm-password-input")).typeText("Password123!");

    // Submit form
    await element(by.text("Sign Up")).tap();

    // Check error message
    await expect(element(by.text("Please enter a valid email"))).toBeVisible();
  });

  it("should validate password strength", async () => {
    // Navigate to signup screen
    await element(by.text("Sign Up")).tap();

    // Fill form with weak password
    await element(by.id("name-input")).typeText("Test User");
    await element(by.id("email-input")).typeText("test@example.com");
    await element(by.id("password-input")).typeText("123");
    await element(by.id("confirm-password-input")).typeText("123");

    // Submit form
    await element(by.text("Sign Up")).tap();

    // Check error message
    await expect(
      element(
        by.text(
          "Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one number, and one special character",
        ),
      ),
    ).toBeVisible();
  });

  it("should validate password matching", async () => {
    // Navigate to signup screen
    await element(by.text("Sign Up")).tap();

    // Fill form with mismatched passwords
    await element(by.id("name-input")).typeText("Test User");
    await element(by.id("email-input")).typeText("test@example.com");
    await element(by.id("password-input")).typeText("Password123!");
    await element(by.id("confirm-password-input")).typeText(
      "DifferentPassword123!",
    );

    // Submit form
    await element(by.text("Sign Up")).tap();

    // Check error message
    await expect(element(by.text("Passwords do not match"))).toBeVisible();
  });

  it("should handle already existing email", async () => {
    // Navigate to signup screen
    await element(by.text("Sign Up")).tap();

    // Fill form with existing email
    await element(by.id("name-input")).typeText("Test User");
    await element(by.id("email-input")).typeText("existing@example.com");
    await element(by.id("password-input")).typeText("Password123!");
    await element(by.id("confirm-password-input")).typeText("Password123!");

    // Submit form
    await element(by.text("Sign Up")).tap();

    // Check error message
    await waitFor(element(by.text("Email is already registered")))
      .toBeVisible()
      .withTimeout(5000);
  });

  it("should register successfully with valid data", async () => {
    // Generate unique email to avoid conflicts
    const uniqueEmail = `test${Date.now()}@example.com`;

    // Navigate to signup screen
    await element(by.text("Sign Up")).tap();

    // Fill form with valid data
    await element(by.id("name-input")).typeText("Test User");
    await element(by.id("email-input")).typeText(uniqueEmail);
    await element(by.id("password-input")).typeText("Password123!");
    await element(by.id("confirm-password-input")).typeText("Password123!");

    // Accept terms if present
    if (await element(by.id("terms-checkbox")).isVisible()) {
      await element(by.id("terms-checkbox")).tap();
    }

    // Submit form
    await element(by.text("Sign Up")).tap();

    // Verify registration successful (either email verification screen or dashboard)
    await waitFor(
      element(by.id("email-verification-screen")).or(by.id("dashboard-screen")),
    )
      .toBeVisible()
      .withTimeout(5000);
  });

  it("should navigate to login screen from signup", async () => {
    // Navigate to signup screen
    await element(by.text("Sign Up")).tap();

    // Click on login link
    await element(by.text("Already have an account? Log In")).tap();

    // Verify we're on the login screen
    await expect(element(by.text("Welcome Back"))).toBeVisible();
  });

  it("should toggle password visibility", async () => {
    // Navigate to signup screen
    await element(by.text("Sign Up")).tap();

    // Enter password
    await element(by.id("password-input")).typeText("Password123!");

    // Verify password is hidden by default
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

    // Tap hide password icon again
    await element(by.id("toggle-password-visibility")).tap();

    // Verify password is hidden again
    await expect(element(by.id("password-input"))).toHaveToggleAttribute(
      "secureTextEntry",
      true,
    );
  });

  it("should verify valid email format as user types", async () => {
    // Navigate to signup screen
    await element(by.text("Sign Up")).tap();

    // Enter incomplete email
    await element(by.id("email-input")).typeText("test@");

    // Move focus to next field
    await element(by.id("password-input")).tap();

    // Check for validation message
    await expect(element(by.text("Please enter a valid email"))).toBeVisible();

    // Complete email with valid format
    await element(by.id("email-input")).tap();
    await element(by.id("email-input")).typeText("example.com");

    // Check that validation message disappears
    await expect(
      element(by.text("Please enter a valid email")),
    ).not.toBeVisible();
  });
});
