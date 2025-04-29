const { test, expect } = require("@playwright/test");
const { PasswordResetPage } = require("./pages/password-reset.page");
const { setupPasswordResetMocks } = require("./utils/api-mocks");

test.describe("Password Reset Flow", () => {
  test.beforeEach(async ({ page }) => {
    // Setup API mocks for all tests
    await setupPasswordResetMocks(page);
  });

  test("should successfully reset password with valid email and code", async ({
    page,
  }) => {
    // Create page object
    const resetPage = new PasswordResetPage(page);

    // Step 1: Navigate to password reset page
    await resetPage.goto();

    // Step 2: Request password reset with valid email
    await resetPage.requestReset("test@example.com");

    // Step 3: Verify reset request confirmation is shown
    await resetPage.verifyResetRequestSuccessful();

    // Step 4: Enter valid verification code
    await resetPage.enterResetCode("123456");

    // Step 5: Enter new password
    await resetPage.enterNewPassword("NewPassword123!");

    // Step 6: Verify success message is displayed
    await resetPage.verifyPasswordResetSuccessful();

    // Step 7: Navigate to login page
    await resetPage.navigateToLogin();
  });

  test("should show error for non-existent email", async ({ page }) => {
    const resetPage = new PasswordResetPage(page);

    await resetPage.goto();
    await resetPage.requestReset("nonexistent@example.com");

    const errorMessage = await resetPage.getErrorMessage();
    expect(errorMessage).toContain("No account found");
  });

  test("should show error for invalid verification code", async ({ page }) => {
    const resetPage = new PasswordResetPage(page);

    await resetPage.goto();
    await resetPage.requestReset("test@example.com");
    await resetPage.verifyResetRequestSuccessful();

    // Enter invalid code
    await resetPage.enterResetCode("000000");

    const errorMessage = await resetPage.getErrorMessage();
    expect(errorMessage).toContain("Invalid or expired verification code");
  });

  test("should validate password requirements", async ({ page }) => {
    const resetPage = new PasswordResetPage(page);

    await resetPage.goto();
    await resetPage.requestReset("test@example.com");
    await resetPage.verifyResetRequestSuccessful();
    await resetPage.enterResetCode("123456");

    // Try with a password that's too short
    await resetPage.enterNewPassword("Short1!");

    const errorMessage = await resetPage.getErrorMessage();
    expect(errorMessage).toContain("at least 8 characters");
  });

  test("should show error when passwords do not match", async ({ page }) => {
    const resetPage = new PasswordResetPage(page);

    await resetPage.goto();
    await resetPage.requestReset("test@example.com");
    await resetPage.verifyResetRequestSuccessful();
    await resetPage.enterResetCode("123456");

    // Enter mismatched passwords
    await resetPage.enterNewPassword(
      "GoodPassword123!",
      "DifferentPassword123!",
    );

    const errorMessage = await resetPage.getErrorMessage();
    expect(errorMessage).toContain("Passwords do not match");
  });

  test("should handle server errors gracefully", async ({ page }) => {
    // Setup new mocks with server failure
    await setupPasswordResetMocks(page, {
      shouldFailPasswordReset: true,
    });

    const resetPage = new PasswordResetPage(page);

    await resetPage.goto();
    await resetPage.requestReset("test@example.com");
    await resetPage.verifyResetRequestSuccessful();
    await resetPage.enterResetCode("123456");
    await resetPage.enterNewPassword("GoodPassword123!");

    const errorMessage = await resetPage.getErrorMessage();
    expect(errorMessage).toContain("Server error");
  });
});
