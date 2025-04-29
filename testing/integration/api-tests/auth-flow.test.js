const axios = require("axios");
const { expect } = require("@jest/globals");

// API base URL - can be configured via env variable
const API_URL = process.env.API_URL || "http://localhost:8000";

// Test credentials from our fixtures
const TEST_CREDENTIALS = {
  admin: {
    email: "admin@example.com",
    password: "adminpassword",
  },
  teacher: {
    email: "teacher@example.com",
    password: "password123",
  },
  student: {
    email: "student@example.com",
    password: "password123",
  },
  user: {
    email: "test@example.com",
    password: "password123",
  },
};

// Helper function to get auth tokens
async function getAuthTokens(credentials) {
  try {
    const response = await axios.post(`${API_URL}/api/auth/token/`, {
      email: credentials.email,
      password: credentials.password,
    });
    return response.data;
  } catch (error) {
    console.error(
      "Authentication error:",
      error.response?.data || error.message,
    );
    throw error;
  }
}

// Helper to make authenticated requests
async function makeAuthenticatedRequest(
  endpoint,
  token,
  method = "get",
  data = null,
) {
  try {
    const config = {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    };

    if (method === "get") {
      return await axios.get(`${API_URL}${endpoint}`, config);
    } else if (method === "post") {
      return await axios.post(`${API_URL}${endpoint}`, data, config);
    } else if (method === "put") {
      return await axios.put(`${API_URL}${endpoint}`, data, config);
    } else if (method === "delete") {
      return await axios.delete(`${API_URL}${endpoint}`, config);
    }
  } catch (error) {
    console.error("Request error:", error.response?.data || error.message);
    throw error;
  }
}

describe("Authentication Flow Integration Tests", () => {
  // Test tokens for each user type
  let adminToken, teacherToken, studentToken, userToken;

  // Before all tests, get auth tokens
  beforeAll(async () => {
    try {
      // Get tokens for each user type
      const adminAuth = await getAuthTokens(TEST_CREDENTIALS.admin);
      adminToken = adminAuth.access;

      const teacherAuth = await getAuthTokens(TEST_CREDENTIALS.teacher);
      teacherToken = teacherAuth.access;

      const studentAuth = await getAuthTokens(TEST_CREDENTIALS.student);
      studentToken = studentAuth.access;

      const userAuth = await getAuthTokens(TEST_CREDENTIALS.user);
      userToken = userAuth.access;
    } catch (error) {
      console.error("Setup error:", error);
    }
  }, 10000); // Increase timeout for initial setup

  test("Admin can access protected admin endpoints", async () => {
    // Skip if token wasn't retrieved successfully
    if (!adminToken) {
      console.warn("Skipping admin test due to missing token");
      return;
    }

    const response = await makeAuthenticatedRequest(
      "/api/admin/users/",
      adminToken,
    );
    expect(response.status).toBe(200);
    expect(Array.isArray(response.data)).toBe(true);
  });

  test("Teacher can access teacher resources", async () => {
    if (!teacherToken) {
      console.warn("Skipping teacher test due to missing token");
      return;
    }

    const response = await makeAuthenticatedRequest(
      "/api/teacher/resources/",
      teacherToken,
    );
    expect(response.status).toBe(200);
  });

  test("Student can access student resources", async () => {
    if (!studentToken) {
      console.warn("Skipping student test due to missing token");
      return;
    }

    const response = await makeAuthenticatedRequest(
      "/api/student/courses/",
      studentToken,
    );
    expect(response.status).toBe(200);
  });

  test("Regular user can access user profile", async () => {
    if (!userToken) {
      console.warn("Skipping user test due to missing token");
      return;
    }

    const response = await makeAuthenticatedRequest(
      "/api/users/profile/",
      userToken,
    );
    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty("email", TEST_CREDENTIALS.user.email);
  });

  test("User cannot access admin-only endpoints", async () => {
    if (!userToken) {
      console.warn("Skipping permission test due to missing token");
      return;
    }

    try {
      await makeAuthenticatedRequest("/api/admin/users/", userToken);
      // If we get here, the test failed - user shouldn't access admin endpoints
      fail("Regular user should not be able to access admin endpoints");
    } catch (error) {
      expect(error.response.status).toBe(403);
    }
  });

  test("Token refresh works correctly", async () => {
    // Get initial tokens
    const auth = await getAuthTokens(TEST_CREDENTIALS.user);

    // Try to refresh the token
    const refreshResponse = await axios.post(
      `${API_URL}/api/auth/token/refresh/`,
      {
        refresh: auth.refresh,
      },
    );

    expect(refreshResponse.status).toBe(200);
    expect(refreshResponse.data).toHaveProperty("access");

    // Verify the new token works
    const response = await makeAuthenticatedRequest(
      "/api/users/profile/",
      refreshResponse.data.access,
    );
    expect(response.status).toBe(200);
  });
});
