import React from "react";
import TestRenderer from "react-test-renderer";
import { act } from "react-test-renderer";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";

/**
 * Renders a component with Test Renderer and waits for all async operations to complete
 * @param {React.ReactElement} element - The React element to render
 * @returns {Promise<TestRenderer.ReactTestRenderer>} - A promise that resolves to the test renderer
 */
export async function renderWithTestRenderer(element) {
  let renderer;
  await act(async () => {
    renderer = TestRenderer.create(element);
    // Allow any pending promises to resolve
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  return renderer;
}

/**
 * Finds all instances of a component with the given test ID
 * @param {TestRenderer.ReactTestRenderer} renderer - The test renderer
 * @param {string} testID - The testID to search for
 * @returns {TestRenderer.ReactTestInstance[]} - Array of instances matching the testID
 */
export function findAllByTestId(renderer, testID) {
  return renderer.root.findAll((instance) => instance.props.testID === testID);
}

/**
 * Finds a component with the given test ID
 * @param {TestRenderer.ReactTestRenderer} renderer - The test renderer
 * @param {string} testID - The testID to search for
 * @returns {TestRenderer.ReactTestInstance} - The first instance matching the testID
 */
export function findByTestId(renderer, testID) {
  return renderer.root.find((instance) => instance.props.testID === testID);
}

/**
 * Mocks successful user authentication
 * @param {Object} userData - The user data to mock
 */
export function mockAuthentication(
  userData = { id: "1", username: "testuser" },
) {
  // Mock JWT token in secure store
  SecureStore.getItemAsync.mockResolvedValue(
    JSON.stringify({
      access: "mock-jwt-token",
      refresh: "mock-refresh-token",
    }),
  );

  // Mock user data in AsyncStorage
  AsyncStorage.getItem.mockResolvedValue(JSON.stringify(userData));
}

/**
 * Mocks API responses for testing
 * @param {Object} axios - The axios instance to mock
 * @param {Object} mockResponses - An object mapping URL paths to response data
 */
export function mockAPIResponses(axios, mockResponses) {
  // Save original implementation
  const originalGet = axios.get;
  const originalPost = axios.post;
  const originalPut = axios.put;
  const originalDelete = axios.delete;

  // Mock implementation that returns data based on URL
  axios.get = jest.fn((url) => {
    const matchingUrl = Object.keys(mockResponses).find((path) =>
      url.includes(path),
    );
    if (matchingUrl) {
      return Promise.resolve({ data: mockResponses[matchingUrl] });
    }
    return originalGet(url);
  });

  axios.post = jest.fn((url, data) => {
    const matchingUrl = Object.keys(mockResponses).find((path) =>
      url.includes(path),
    );
    if (matchingUrl) {
      return Promise.resolve({ data: mockResponses[matchingUrl] });
    }
    return originalPost(url, data);
  });

  axios.put = jest.fn((url, data) => {
    const matchingUrl = Object.keys(mockResponses).find((path) =>
      url.includes(path),
    );
    if (matchingUrl) {
      return Promise.resolve({ data: mockResponses[matchingUrl] });
    }
    return originalPut(url, data);
  });

  axios.delete = jest.fn((url) => {
    const matchingUrl = Object.keys(mockResponses).find((path) =>
      url.includes(path),
    );
    if (matchingUrl) {
      return Promise.resolve({ data: mockResponses[matchingUrl] });
    }
    return originalDelete(url);
  });

  // Return cleanup function
  return () => {
    axios.get = originalGet;
    axios.post = originalPost;
    axios.put = originalPut;
    axios.delete = originalDelete;
  };
}

/**
 * Wait for a condition to be true
 * @param {Function} condition - Function that returns a boolean
 * @param {number} timeout - Maximum time to wait in milliseconds
 * @param {number} interval - Interval between checks in milliseconds
 * @returns {Promise<void>} - Resolves when condition is true, rejects on timeout
 */
export async function waitFor(condition, timeout = 5000, interval = 100) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    if (condition()) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  throw new Error(`Timeout (${timeout}ms) reached while waiting for condition`);
}
