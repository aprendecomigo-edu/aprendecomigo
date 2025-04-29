describe("Login Flow", () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it("should show login screen", async () => {
    await expect(element(by.id("login-screen"))).toBeVisible();
  });

  it("should show error on invalid login", async () => {
    await element(by.id("email-input")).typeText("invalid@example.com");
    await element(by.id("password-input")).typeText("wrongpassword");
    await element(by.id("login-button")).tap();

    // Wait for the error message to appear
    await waitFor(element(by.id("error-message")))
      .toBeVisible()
      .withTimeout(5000);
  });

  it("should login successfully with valid credentials", async () => {
    // Clear previous inputs
    await element(by.id("email-input")).clearText();
    await element(by.id("password-input")).clearText();

    // Enter valid credentials (use test accounts in your environment)
    await element(by.id("email-input")).typeText("test@example.com");
    await element(by.id("password-input")).typeText("password123");
    await element(by.id("login-button")).tap();

    // Check if we navigate to the home screen
    await waitFor(element(by.id("home-screen")))
      .toBeVisible()
      .withTimeout(5000);
  });
});
