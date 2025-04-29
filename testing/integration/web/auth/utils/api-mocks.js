/**
 * API mocking utilities for password reset tests
 */

/**
 * Configure request interception and mock API responses for password reset flow
 * @param {import('@playwright/test').Page} page
 * @param {Object} options - Configuration options for the mocks
 */
async function setupPasswordResetMocks(page, options = {}) {
  const {
    validEmail = "test@example.com",
    validCode = "123456",
    validUserToken = "valid-reset-token",
    invalidEmail = "nonexistent@example.com",
    invalidCode = "000000",
    emailDelay = 500,
    verificationDelay = 500,
    passwordResetDelay = 500,
    shouldFailEmailRequest = false,
    shouldFailCodeVerification = false,
    shouldFailPasswordReset = false,
  } = options;

  // Intercept reset password email request
  await page.route("**/api/auth/reset-password", async (route) => {
    const body = await route.request().postDataJSON();
    const email = body.email;

    await new Promise((resolve) => setTimeout(resolve, emailDelay));

    if (shouldFailEmailRequest) {
      return route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          message: "Server error while processing reset request",
        }),
      });
    }

    if (email === invalidEmail) {
      return route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          message: "No account found with this email address",
        }),
      });
    }

    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        message: "Reset password link sent successfully",
      }),
    });
  });

  // Intercept code verification request
  await page.route("**/api/auth/verify-reset-code", async (route) => {
    const body = await route.request().postDataJSON();
    const code = body.code;

    await new Promise((resolve) => setTimeout(resolve, verificationDelay));

    if (shouldFailCodeVerification) {
      return route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          message: "Server error during code verification",
        }),
      });
    }

    if (code !== validCode) {
      return route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          message: "Invalid or expired verification code",
        }),
      });
    }

    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        message: "Code verified successfully",
        token: validUserToken,
      }),
    });
  });

  // Intercept password reset confirmation
  await page.route("**/api/auth/reset-password-confirm", async (route) => {
    const body = await route.request().postDataJSON();
    const { token, newPassword } = body;

    await new Promise((resolve) => setTimeout(resolve, passwordResetDelay));

    if (shouldFailPasswordReset) {
      return route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          message: "Server error during password reset",
        }),
      });
    }

    if (token !== validUserToken) {
      return route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          message: "Invalid or expired reset token",
        }),
      });
    }

    // Password validation logic can be added here
    if (newPassword.length < 8) {
      return route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          message: "Password must be at least 8 characters long",
        }),
      });
    }

    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        message: "Password reset successfully",
      }),
    });
  });
}

module.exports = {
  setupPasswordResetMocks,
};
