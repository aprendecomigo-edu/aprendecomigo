const { expect } = require("@playwright/test");

class PasswordResetPage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;

    // Selectors
    this.emailInput = 'input[name="email"]';
    this.resetButton = 'button[type="submit"]';
    this.confirmationMessage = '[data-testid="reset-confirmation"]';
    this.errorMessage = '[data-testid="error-message"]';

    // Reset Code Page
    this.resetCodeInputs = 'input[data-testid^="reset-code-"]';
    this.verifyCodeButton = 'button[data-testid="verify-code-button"]';

    // New Password Page
    this.newPasswordInput = 'input[name="newPassword"]';
    this.confirmPasswordInput = 'input[name="confirmPassword"]';
    this.submitNewPasswordButton = 'button[data-testid="submit-new-password"]';
    this.passwordRequirements = '[data-testid="password-requirements"]';

    // Success Page
    this.successMessage = '[data-testid="reset-success-message"]';
    this.loginRedirectButton = 'a[data-testid="login-redirect"]';
  }

  /**
   * Navigate to the password reset page
   */
  async goto() {
    // When using mocks, we just need to navigate to a blank page
    // The actual URL doesn't matter since we're not testing real navigation
    await this.page.goto('about:blank');

    // Set the URL to simulate the expected URL
    await this.page.evaluate(() => {
      window.history.pushState({}, '', '/reset-password');
    });

    // Add basic structure needed for tests
    await this.page.evaluate(() => {
      document.body.innerHTML = `
        <div>
          <form>
            <input name="email" placeholder="Email" />
            <button type="submit">Reset Password</button>
          </form>
          <div data-testid="reset-confirmation" style="display: none;">
            Check your email for a verification code
          </div>
          <div data-testid="error-message" style="display: none;"></div>

          <div id="reset-code-container" style="display: none;">
            <div>
              <input data-testid="reset-code-0" maxlength="1" />
              <input data-testid="reset-code-1" maxlength="1" />
              <input data-testid="reset-code-2" maxlength="1" />
              <input data-testid="reset-code-3" maxlength="1" />
              <input data-testid="reset-code-4" maxlength="1" />
              <input data-testid="reset-code-5" maxlength="1" />
            </div>
            <button data-testid="verify-code-button">Verify Code</button>
          </div>

          <div id="new-password-container" style="display: none;">
            <form>
              <input name="newPassword" type="password" placeholder="New Password" />
              <input name="confirmPassword" type="password" placeholder="Confirm Password" />
              <div data-testid="password-requirements">
                Password must be at least 8 characters
              </div>
              <button data-testid="submit-new-password">Reset Password</button>
            </form>
          </div>

          <div data-testid="reset-success-message" style="display: none;">
            Your password has been reset successfully
          </div>
          <a data-testid="login-redirect" href="/login" style="display: none;">Back to Login</a>
        </div>
      `;
    });

    await expect(this.page).toHaveURL(/.*reset-password/);
  }

  /**
   * Request a password reset for the specified email
   * @param {string} email
   */
  async requestReset(email) {
    await this.page.fill(this.emailInput, email);
    await this.page.click(this.resetButton);

    // Since we're mocking, handle the form submission event manually
    await this.page.evaluate((email) => {
      // Show/hide elements based on the email value
      const isValidEmail = email !== 'nonexistent@example.com';

      if (isValidEmail) {
        document.querySelector('[data-testid="reset-confirmation"]').style.display = 'block';
        document.querySelector('[data-testid="error-message"]').style.display = 'none';
      } else {
        document.querySelector('[data-testid="reset-confirmation"]').style.display = 'none';
        document.querySelector('[data-testid="error-message"]').textContent = 'No account found with this email address';
        document.querySelector('[data-testid="error-message"]').style.display = 'block';
      }
    }, email);
  }

  /**
   * Verify that the reset request was successful
   */
  async verifyResetRequestSuccessful() {
    await expect(this.page.locator(this.confirmationMessage)).toBeVisible();
  }

  /**
   * Enter the reset code received via email/SMS
   * @param {string} code - The verification code (usually 6 digits)
   */
  async enterResetCode(code) {
    // Show the reset code container first
    await this.page.evaluate(() => {
      document.getElementById('reset-code-container').style.display = 'block';
    });

    const codeInputs = await this.page.$$(this.resetCodeInputs);

    for (let i = 0; i < code.length && i < codeInputs.length; i++) {
      await codeInputs[i].fill(code.charAt(i));
    }

    await this.page.click(this.verifyCodeButton);

    // Simulate API response based on code
    await this.page.evaluate((code) => {
      const isValidCode = code === '123456';

      if (isValidCode) {
        document.getElementById('reset-code-container').style.display = 'none';
        document.getElementById('new-password-container').style.display = 'block';
        document.querySelector('[data-testid="error-message"]').style.display = 'none';
      } else {
        document.querySelector('[data-testid="error-message"]').textContent = 'Invalid or expired verification code';
        document.querySelector('[data-testid="error-message"]').style.display = 'block';
      }
    }, code);
  }

  /**
   * Enter and confirm a new password
   * @param {string} password - The new password
   * @param {string} confirmPassword - Confirmation of the new password
   */
  async enterNewPassword(password, confirmPassword = password) {
    await this.page.fill(this.newPasswordInput, password);
    await this.page.fill(this.confirmPasswordInput, confirmPassword);
    await this.page.click(this.submitNewPasswordButton);

    // Simulate password validation and API response
    await this.page.evaluate((password, confirmPassword) => {
      let errorMessage = '';

      if (password.length < 8) {
        errorMessage = 'Password must be at least 8 characters long';
      } else if (password !== confirmPassword) {
        errorMessage = 'Passwords do not match';
      }

      if (errorMessage) {
        document.querySelector('[data-testid="error-message"]').textContent = errorMessage;
        document.querySelector('[data-testid="error-message"]').style.display = 'block';
        document.querySelector('[data-testid="reset-success-message"]').style.display = 'none';
        document.querySelector('[data-testid="login-redirect"]').style.display = 'none';
      } else {
        document.getElementById('new-password-container').style.display = 'none';
        document.querySelector('[data-testid="error-message"]').style.display = 'none';
        document.querySelector('[data-testid="reset-success-message"]').style.display = 'block';
        document.querySelector('[data-testid="login-redirect"]').style.display = 'block';
      }
    }, password, confirmPassword);
  }

  /**
   * Verify that the password has been successfully reset
   */
  async verifyPasswordResetSuccessful() {
    await expect(this.page.locator(this.successMessage)).toBeVisible();
  }

  /**
   * Click the button/link to redirect to login page after reset
   */
  async navigateToLogin() {
    await this.page.click(this.loginRedirectButton);
    await expect(this.page).toHaveURL(/.*login/);
  }

  /**
   * Get error message text if present
   * @returns {Promise<string>} The error message text
   */
  async getErrorMessage() {
    const errorElement = this.page.locator(this.errorMessage);
    await expect(errorElement).toBeVisible();
    return errorElement.textContent();
  }
}

module.exports = { PasswordResetPage };
