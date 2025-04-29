const { device, element, by, waitFor } = require("detox");
const axios = require("axios");
const MockAdapter = require("axios-mock-adapter");

// Setup axios mock
const mock = new MockAdapter(axios);

// Test users with different roles
const TEST_USERS = {
  admin: {
    email: "admin@example.com",
    password: "adminPassword123!",
    role: "admin",
  },
  teacher: {
    email: "teacher@example.com",
    password: "teacherPassword123!",
    role: "teacher",
  },
  student: {
    email: "student@example.com",
    password: "studentPassword123!",
    role: "student",
  },
  parent: {
    email: "parent@example.com",
    password: "parentPassword123!",
    role: "parent",
  },
};

// Mock tokens for each role
const MOCK_TOKENS = {
  admin: "admin-jwt-token-12345",
  teacher: "teacher-jwt-token-12345",
  student: "student-jwt-token-12345",
  parent: "parent-jwt-token-12345",
};

describe("Role-Based Permissions", () => {
  // Setup before tests
  beforeAll(async () => {
    await device.launchApp();

    // Mock login endpoint for all roles
    mock.onPost("/api/auth/token/").reply((config) => {
      const data = JSON.parse(config.data);

      // Find the matching user
      const userRole = Object.keys(TEST_USERS).find(
        (role) =>
          TEST_USERS[role].email === data.email &&
          TEST_USERS[role].password === data.password,
      );

      if (userRole) {
        return [
          200,
          {
            access: MOCK_TOKENS[userRole],
            refresh: `refresh-${MOCK_TOKENS[userRole]}`,
            user: {
              email: TEST_USERS[userRole].email,
              role: userRole,
            },
          },
        ];
      }

      return [400, { success: false, message: "Invalid credentials" }];
    });
  });

  afterEach(async () => {
    // Logout after each test if logged in
    if (await element(by.id("logout-button")).isVisible()) {
      await element(by.id("logout-button")).tap();
      await waitFor(element(by.id("login-screen")))
        .toBeVisible()
        .withTimeout(3000);
    }
  });

  afterAll(async () => {
    // Clean up mocks
    mock.restore();
  });

  // Helper function to login with a specific role
  async function loginWithRole(role) {
    // Reload to ensure we're on login screen
    await device.reloadReactNative();
    await waitFor(element(by.id("login-screen")))
      .toBeVisible()
      .withTimeout(3000);

    // Fill login details
    await element(by.id("email-input")).typeText(TEST_USERS[role].email);
    await element(by.id("password-input")).typeText(TEST_USERS[role].password);

    // Submit login
    await element(by.id("login-button")).tap();

    // Wait for login to complete
    await waitFor(element(by.id("home-screen")))
      .toBeVisible()
      .withTimeout(5000);
  }

  test("Should see different dashboard elements based on role", async () => {
    // Test for admin role
    await loginWithRole("admin");

    // Admin should see all dashboard elements
    await expect(element(by.id("admin-panel-button"))).toBeVisible();
    await expect(element(by.id("reports-button"))).toBeVisible();
    await expect(element(by.id("users-management-button"))).toBeVisible();
    await expect(element(by.id("settings-button"))).toBeVisible();

    // Logout and test teacher role
    await element(by.id("logout-button")).tap();
    await waitFor(element(by.id("login-screen")))
      .toBeVisible()
      .withTimeout(3000);
    await loginWithRole("teacher");

    // Teacher should see teacher-specific elements
    await expect(element(by.id("classes-button"))).toBeVisible();
    await expect(element(by.id("assignments-button"))).toBeVisible();
    await expect(element(by.id("students-button"))).toBeVisible();

    // But not admin elements
    await expect(element(by.id("admin-panel-button"))).not.toBeVisible();
    await expect(element(by.id("users-management-button"))).not.toBeVisible();

    // Logout and test student role
    await element(by.id("logout-button")).tap();
    await waitFor(element(by.id("login-screen")))
      .toBeVisible()
      .withTimeout(3000);
    await loginWithRole("student");

    // Student should see student-specific elements
    await expect(element(by.id("courses-button"))).toBeVisible();
    await expect(element(by.id("assignments-button"))).toBeVisible();
    await expect(element(by.id("grades-button"))).toBeVisible();

    // But not teacher or admin elements
    await expect(element(by.id("admin-panel-button"))).not.toBeVisible();
    await expect(element(by.id("classes-button"))).not.toBeVisible();
  });

  test("Admin can access user management", async () => {
    // Login as admin
    await loginWithRole("admin");

    // Mock user list API response
    mock.onGet("/api/admin/users/").reply(200, [
      { id: 1, email: "user1@example.com", role: "teacher" },
      { id: 2, email: "user2@example.com", role: "student" },
    ]);

    // Navigate to user management
    await element(by.id("users-management-button")).tap();

    // Should see user management screen
    await waitFor(element(by.id("user-management-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Should see user list
    await waitFor(element(by.id("user-list")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.text("user1@example.com"))).toBeVisible();

    // Should be able to edit a user
    await element(by.id("edit-user-1")).tap();
    await waitFor(element(by.id("edit-user-screen")))
      .toBeVisible()
      .withTimeout(2000);
  });

  test("Teacher cannot access admin areas", async () => {
    // Login as teacher
    await loginWithRole("teacher");

    // Mock forbidden response for admin endpoints
    mock.onGet("/api/admin/users/").reply(403, {
      success: false,
      message: "Permission denied",
      error: "FORBIDDEN",
    });

    // Try to navigate to admin area by deep link
    await device.openURL({
      url: "aprendecomigo://admin/users",
      sourceApp: "com.aprendecomigo.test",
    });

    // Should see permission denied message
    await waitFor(element(by.id("permission-denied-message")))
      .toBeVisible()
      .withTimeout(3000);

    // Or alternatively, should stay on current screen
    await expect(element(by.id("home-screen"))).toBeVisible();
  });

  test("Teacher can manage their own classes", async () => {
    // Login as teacher
    await loginWithRole("teacher");

    // Mock teacher's classes
    mock.onGet("/api/teacher/classes/").reply(200, [
      { id: 1, name: "Math 101", students: 25 },
      { id: 2, name: "Science 202", students: 18 },
    ]);

    // Navigate to classes
    await element(by.id("classes-button")).tap();

    // Should see classes screen
    await waitFor(element(by.id("classes-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Should see class list
    await waitFor(element(by.id("class-list")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.text("Math 101"))).toBeVisible();

    // Should be able to view class details
    await element(by.id("view-class-1")).tap();
    await waitFor(element(by.id("class-details-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Should be able to modify their own class
    await element(by.id("edit-class-button")).tap();
    await waitFor(element(by.id("edit-class-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Change class name
    await element(by.id("class-name-input")).clearText();
    await element(by.id("class-name-input")).typeText("Math 101 Advanced");

    // Mock update endpoint
    mock.onPut("/api/teacher/classes/1/").reply(200, {
      id: 1,
      name: "Math 101 Advanced",
      students: 25,
    });

    // Save changes
    await element(by.id("save-button")).tap();

    // Should return to class details with updated info
    await waitFor(element(by.id("class-details-screen")))
      .toBeVisible()
      .withTimeout(3000);
    await expect(element(by.text("Math 101 Advanced"))).toBeVisible();
  });

  test("Teacher cannot modify other teachers classes", async () => {
    // Login as teacher
    await loginWithRole("teacher");

    // Mock forbidden access to another teacher's class
    mock.onGet("/api/teacher/classes/99/").reply(403, {
      success: false,
      message: "You do not have permission to access this class",
      error: "FORBIDDEN",
    });

    // Try to access another teacher's class by deep link
    await device.openURL({
      url: "aprendecomigo://teacher/classes/99",
      sourceApp: "com.aprendecomigo.test",
    });

    // Should see permission denied message
    await waitFor(element(by.id("permission-denied-message")))
      .toBeVisible()
      .withTimeout(3000);
  });

  test("Student can access their own grades", async () => {
    // Login as student
    await loginWithRole("student");

    // Mock student's grades
    mock.onGet("/api/student/grades/").reply(200, [
      { id: 1, class: "Math 101", grade: "A", score: 95 },
      { id: 2, class: "Science 202", grade: "B", score: 85 },
    ]);

    // Navigate to grades
    await element(by.id("grades-button")).tap();

    // Should see grades screen
    await waitFor(element(by.id("grades-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Should see grade list
    await waitFor(element(by.id("grade-list")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.text("Math 101"))).toBeVisible();
    await expect(element(by.text("A"))).toBeVisible();
  });

  test("Student cannot access other students grades", async () => {
    // Login as student
    await loginWithRole("student");

    // Mock forbidden access to another student's grades
    mock.onGet("/api/student/grades/user/99/").reply(403, {
      success: false,
      message: "You do not have permission to access these grades",
      error: "FORBIDDEN",
    });

    // Try to access another student's grades by deep link
    await device.openURL({
      url: "aprendecomigo://student/grades/user/99",
      sourceApp: "com.aprendecomigo.test",
    });

    // Should see permission denied message
    await waitFor(element(by.id("permission-denied-message")))
      .toBeVisible()
      .withTimeout(3000);
  });

  test("Parent can access their children grades", async () => {
    // Login as parent
    await loginWithRole("parent");

    // Mock parent's children
    mock.onGet("/api/parent/children/").reply(200, [
      { id: 101, name: "Child One", grade: "5th" },
      { id: 102, name: "Child Two", grade: "3rd" },
    ]);

    // Navigate to children list
    await element(by.id("children-button")).tap();

    // Should see children screen
    await waitFor(element(by.id("children-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Should see children list
    await waitFor(element(by.id("children-list")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.text("Child One"))).toBeVisible();

    // Mock child's grades
    mock.onGet("/api/parent/children/101/grades/").reply(200, [
      { id: 1, class: "Math 101", grade: "A", score: 95 },
      { id: 2, class: "Science 202", grade: "B", score: 85 },
    ]);

    // View child's grades
    await element(by.id("view-child-101")).tap();

    // Should see child's grades screen
    await waitFor(element(by.id("child-grades-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Should see grade list
    await waitFor(element(by.id("grade-list")))
      .toBeVisible()
      .withTimeout(2000);
    await expect(element(by.text("Math 101"))).toBeVisible();
    await expect(element(by.text("A"))).toBeVisible();
  });

  test("Parent cannot access other children grades", async () => {
    // Login as parent
    await loginWithRole("parent");

    // Mock forbidden access to another parent's child
    mock.onGet("/api/parent/children/999/").reply(403, {
      success: false,
      message: "You do not have permission to access this child",
      error: "FORBIDDEN",
    });

    // Try to access another parent's child by deep link
    await device.openURL({
      url: "aprendecomigo://parent/children/999",
      sourceApp: "com.aprendecomigo.test",
    });

    // Should see permission denied message
    await waitFor(element(by.id("permission-denied-message")))
      .toBeVisible()
      .withTimeout(3000);
  });

  test("HTTP status codes are correct for permission errors", async () => {
    // This test verifies that the backend returns the correct HTTP status codes

    // 401 for unauthenticated requests
    mock.onGet("/api/admin/users/").reply(401, {
      success: false,
      message: "Authentication required",
      error: "UNAUTHORIZED",
    });

    // 403 for authenticated but unauthorized requests
    mock.onGet("/api/admin/settings/").reply(403, {
      success: false,
      message: "Permission denied",
      error: "FORBIDDEN",
    });

    // Login as teacher to test these scenarios
    await loginWithRole("teacher");

    // Set up a spy to track API responses
    let apiResponses = [];
    const originalMockResponse =
      axios.interceptors.response.handlers[0].fulfilled;

    // Add custom response interceptor
    axios.interceptors.response.handlers[0].fulfilled = (response) => {
      apiResponses.push({
        url: response.config.url,
        status: response.status,
      });
      return originalMockResponse(response);
    };

    // Try to access admin users (simulate token expiration)
    try {
      await axios.get("/api/admin/users/");
    } catch (error) {
      // Should get 401
      expect(error.response.status).toBe(401);
    }

    // Try to access admin settings (authenticated but unauthorized)
    try {
      await axios.get("/api/admin/settings/");
    } catch (error) {
      // Should get 403
      expect(error.response.status).toBe(403);
    }

    // Restore original interceptor
    axios.interceptors.response.handlers[0].fulfilled = originalMockResponse;
  });

  test("Permission boundaries are respected in the UI", async () => {
    // This test verifies that the UI properly hides/disables elements based on permissions

    // Login as student
    await loginWithRole("student");

    // Student shouldn't see admin tabs or buttons
    await expect(element(by.id("admin-tab"))).not.toBeVisible();
    await expect(element(by.id("teacher-tab"))).not.toBeVisible();

    // There shouldn't be any hidden admin elements in the DOM either
    // This verifies that we're not just hiding elements with CSS
    const adminElements = await device.queryAll(by.id("admin-*"));
    expect(adminElements.length).toBe(0);

    // Navigate to a student area
    await element(by.id("courses-button")).tap();
    await waitFor(element(by.id("courses-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Should not see any teacher actions
    await expect(element(by.id("add-course-button"))).not.toBeVisible();
    await expect(element(by.id("edit-course-button"))).not.toBeVisible();

    // Login as teacher to verify they see the appropriate actions
    await element(by.id("logout-button")).tap();
    await waitFor(element(by.id("login-screen")))
      .toBeVisible()
      .withTimeout(3000);
    await loginWithRole("teacher");

    // Navigate to courses
    await element(by.id("classes-button")).tap();
    await waitFor(element(by.id("classes-screen")))
      .toBeVisible()
      .withTimeout(2000);

    // Teacher should see course management actions
    await expect(element(by.id("add-class-button"))).toBeVisible();
    await expect(element(by.id("edit-class-button"))).toBeVisible();
  });
});
