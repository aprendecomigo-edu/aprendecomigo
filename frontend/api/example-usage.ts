/**
 * Example usage of the new API client architecture
 * This file demonstrates how to use the refactored API system
 *
 * This file is for documentation purposes and should not be committed to production
 */

import { createApiGateway, createApiClient } from './factory';

import { storage } from '@/utils/storage';

// Example 1: Using the factory to create a configured API gateway
const handleAuthError = (error: any) => {
  if (__DEV__) {
    console.log('Authentication error occurred:', error);
  }
  // Handle auth error (e.g., redirect to login)
};

const apiGateway = createApiGateway(storage, handleAuthError);

// Now you can use all services through the gateway
async function exampleUsage() {
  try {
    // Authentication
    await apiGateway.auth.requestEmailCode({ email: 'user@example.com' });
    const authResult = await apiGateway.auth.verifyEmailCode({
      email: 'user@example.com',
      code: '123456',
    });

    // User management
    const profile = await apiGateway.user.getUserProfile();
    await apiGateway.user.updateUserProfile({ name: 'Updated Name' });

    // Tasks
    const tasks = await apiGateway.tasks.getTasks();
    const newTask = await apiGateway.tasks.createTask({
      title: 'New Task',
      description: 'Task description',
    });

    // Payments
    const paymentMethods = await apiGateway.payment.getPaymentMethods();

    // Balance
    const balance = await apiGateway.balance.getBalance();

    // Notifications
    const notifications = await apiGateway.notification.getNotifications();
  } catch (error) {
    console.error('API operation failed:', error);
  }
}

// Example 2: Creating a custom API client with specific configuration
const customApiClient = createApiClient(storage, handleAuthError, {
  baseURL: 'https://custom-api.example.com',
  timeout: 10000,
  headers: {
    'Custom-Header': 'value',
  },
});

// Example 3: Multiple isolated instances (useful for testing or multi-tenant scenarios)
const storage1 = storage; // First user's storage
const storage2 = storage; // Second user's storage (would be different in real scenario)

const apiGateway1 = createApiGateway(storage1, handleAuthError);
const apiGateway2 = createApiGateway(storage2, handleAuthError);

// These instances are completely isolated - no shared state
async function isolatedUsage() {
  // Each gateway maintains its own auth state and configuration
  await apiGateway1.auth.requestEmailCode({ email: 'user1@example.com' });
  await apiGateway2.auth.requestEmailCode({ email: 'user2@example.com' });
}

export { exampleUsage, isolatedUsage };
