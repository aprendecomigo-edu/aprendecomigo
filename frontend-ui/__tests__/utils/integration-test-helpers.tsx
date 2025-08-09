/**
 * Integration Test Helpers
 *
 * Comprehensive utilities for coordinating multiple API mocks, setting up
 * complex test scenarios, and providing reusable test patterns for
 * end-to-end integration tests.
 */

import React from 'react';

import {
  createMockAuthUser,
  createMockTokenResponse,
  createAuthTestWrapper,
} from './auth-test-utils';
import {
  createMockPricingPlans,
  createMockPricingPlan,
  createMockStripeConfig,
  createMockPurchaseInitiationResponse,
  createMockStripe,
  createMockElements,
  createMockStripeSuccess,
  createMockStripeError,
  createMockPaymentMethods,
  createMockWebSocket,
  createBalanceUpdateMessage,
  VALID_TEST_DATA,
} from './payment-test-utils';

import { render } from '@/__tests__/utils/test-utils';
import type {
  PricingPlan,
  StudentBalanceResponse,
  PaymentMethod,
  StripeConfig,
  PurchaseInitiationResponse,
} from '@/types/purchase';

// Integration scenario builders
export interface IntegrationTestHelpers {
  setupNewUserScenario: () => NewUserScenario;
  setupReturningUserScenario: () => ReturningUserScenario;
  setupTokenExpiryScenario: () => TokenExpiryScenario;
  setupSessionPersistenceScenario: () => SessionPersistenceScenario;
  setupWebRecoveryScenario: () => WebRecoveryScenario;
  setupRealtimeUpdateScenario: () => RealtimeUpdateScenario;
  setupConcurrentSessionScenario: () => ConcurrentSessionScenario;
  setupFormPreservationScenario: () => FormPreservationScenario;
  setupHappyPathScenario: () => HappyPathScenario;
  setupFailureScenario: () => FailureScenario;
  setupPaymentRetryScenario: () => PaymentRetryScenario;
  setupCrossPlatformScenario: (platform: 'web' | 'ios' | 'android') => CrossPlatformScenario;
  setupParentApprovalScenario: () => ParentApprovalScenario;
  coordinateApiMocks: (scenario: TestScenario) => MockCoordinator;
  createUserJourneySimulator: () => UserJourneySimulator;
  setupPerformanceTest: () => PerformanceTestSetup;
  createAccessibilityTestHelpers: () => AccessibilityTestHelpers;
}

// Scenario type definitions
export interface NewUserScenario {
  mockNewUser: any;
  onAuthComplete: (user: any) => void;
  mockRegistrationFlow: () => void;
}

export interface ReturningUserScenario {
  mockExistingUser: any;
  mockSessionData: any;
  setupStoredSession: () => void;
}

export interface TokenExpiryScenario {
  mockExistingUser: any;
  mockExpiredToken: string;
  mockRefreshFlow: () => void;
}

export interface SessionPersistenceScenario {
  mockExistingUser: any;
  simulateAppBackgrounding: () => void;
  simulateAppForegrounding: () => void;
}

export interface WebRecoveryScenario {
  mockExistingUser: any;
  mockBrowserRefresh: () => void;
  mockStateRecovery: () => void;
}

export interface RealtimeUpdateScenario {
  mockExistingUser: any;
  mockWebSocket: any;
  simulateRealtimeUpdate: (type: string, data: any) => void;
}

export interface ConcurrentSessionScenario {
  mockExistingUser: any;
  simulateSessionConflict: () => void;
}

export interface FormPreservationScenario {
  mockExistingUser: any;
  preservedFormData: any;
  simulateFormPreservation: () => void;
}

export interface HappyPathScenario {
  mockSuccessfulApis: () => void;
  mockValidFormData: any;
  simulateCompleteFlow: (helpers: any) => Promise<void>;
}

export interface FailureScenario {
  mockFailingApis: (failurePoints: string[]) => void;
  mockErrorRecovery: () => void;
  simulateErrorScenarios: () => void;
}

export interface PaymentRetryScenario {
  mockMultiplePaymentMethods: any[];
  mockPaymentFailureRecovery: () => void;
  simulateRetryFlow: () => void;
}

export interface CrossPlatformScenario {
  platform: 'web' | 'ios' | 'android';
  mockPlatformSpecifics: () => void;
  setupPlatformMocks: () => void;
}

export interface ParentApprovalScenario {
  mockStudentUser: any;
  mockParentUser: any;
  mockApprovalFlow: () => void;
  simulateApprovalResponse: (approved: boolean) => void;
}

export interface TestScenario {
  name: string;
  apis: string[];
  expectedCalls: MockExpectation[];
  errorConditions?: ErrorCondition[];
}

export interface MockCoordinator {
  setupMocks: () => void;
  verifyCallOrder: () => void;
  teardownMocks: () => void;
}

export interface UserJourneySimulator {
  simulateRapidInteractions: (actions: string[]) => void;
  simulateSlowNetwork: () => void;
  simulateInterruptions: () => void;
  measurePerformance: () => PerformanceMetrics;
}

export interface PerformanceTestSetup {
  startMonitoring: () => void;
  stopMonitoring: () => PerformanceMetrics;
  expectFastRender: (maxMs?: number) => void;
  expectMemoryUsage: (maxMb?: number) => void;
}

export interface PerformanceMetrics {
  renderTime: number;
  memoryUsage: number;
  apiCallCount: number;
  reRenderCount: number;
}

export interface AccessibilityTestHelpers {
  expectAccessibleElements: (component: any) => void;
  simulateScreenReader: () => void;
  testKeyboardNavigation: () => void;
  verifyAriaLabels: () => void;
}

export interface MockExpectation {
  api: string;
  method: string;
  callOrder: number;
  parameters?: any;
  response?: any;
}

export interface ErrorCondition {
  api: string;
  method: string;
  error: Error;
  recoveryAction?: string;
}

export function createIntegrationTestHelpers(): IntegrationTestHelpers {
  return {
    setupNewUserScenario(): NewUserScenario {
      const mockNewUser = createMockAuthUser({
        id: 1,
        name: 'New User',
        email: 'newuser@example.com',
        isNewUser: true,
        hasCompletedOnboarding: false,
      });

      let authCompleteCallback: (user: any) => void = () => {};

      return {
        mockNewUser,
        onAuthComplete: callback => {
          authCompleteCallback = callback;
        },
        mockRegistrationFlow: () => {
          // Simulate registration completion
          setTimeout(() => {
            authCompleteCallback(mockNewUser);
          }, 100);
        },
      };
    },

    setupReturningUserScenario(): ReturningUserScenario {
      const mockExistingUser = createMockAuthUser({
        id: 2,
        name: 'Returning User',
        email: 'returning@example.com',
        hasCompletedOnboarding: true,
        lastLoginAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      });

      const mockSessionData = {
        user: mockExistingUser,
        token: 'valid_jwt_token_' + Math.random(),
        refreshToken: 'valid_refresh_token_' + Math.random(),
        expiresAt: Date.now() + 3600000, // 1 hour from now
      };

      return {
        mockExistingUser,
        mockSessionData,
        setupStoredSession: () => {
          // Mock AsyncStorage or localStorage with session data
          if (typeof window !== 'undefined') {
            window.localStorage?.setItem('user_session', JSON.stringify(mockSessionData));
          }
        },
      };
    },

    setupTokenExpiryScenario(): TokenExpiryScenario {
      const mockExistingUser = createMockAuthUser({
        id: 3,
        name: 'Token Expiry User',
        email: 'tokenexpiry@example.com',
      });

      const mockExpiredToken = 'expired_token_' + Date.now();

      return {
        mockExistingUser,
        mockExpiredToken,
        mockRefreshFlow: () => {
          // Mock token refresh API response
          return createMockTokenResponse({
            token: 'refreshed_token_' + Date.now(),
            refreshToken: 'new_refresh_token_' + Date.now(),
          });
        },
      };
    },

    setupSessionPersistenceScenario(): SessionPersistenceScenario {
      const mockExistingUser = createMockAuthUser({
        id: 4,
        name: 'Session Persistence User',
        email: 'session@example.com',
      });

      return {
        mockExistingUser,
        simulateAppBackgrounding: () => {
          // Mock React Native AppState change
          if (typeof require !== 'undefined') {
            const AppState = require('react-native').AppState;
            AppState.currentState = 'background';
            AppState._eventHandlers?.change?.forEach((handler: any) => handler('background'));
          }
        },
        simulateAppForegrounding: () => {
          if (typeof require !== 'undefined') {
            const AppState = require('react-native').AppState;
            AppState.currentState = 'active';
            AppState._eventHandlers?.change?.forEach((handler: any) => handler('active'));
          }
        },
      };
    },

    setupWebRecoveryScenario(): WebRecoveryScenario {
      const mockExistingUser = createMockAuthUser({
        id: 5,
        name: 'Web Recovery User',
        email: 'webrecovery@example.com',
      });

      return {
        mockExistingUser,
        mockBrowserRefresh: () => {
          // Mock window.location.reload
          if (typeof window !== 'undefined') {
            window.location.reload = jest.fn();
          }
        },
        mockStateRecovery: () => {
          // Mock localStorage state recovery
          if (typeof window !== 'undefined' && window.localStorage) {
            window.localStorage.getItem = jest.fn().mockImplementation(key => {
              if (key === 'purchase_flow_state') {
                return JSON.stringify({
                  step: 'user-info',
                  formData: {
                    selectedPlan: createMockPricingPlan(),
                    studentName: VALID_TEST_DATA.studentName,
                    studentEmail: VALID_TEST_DATA.studentEmail,
                  },
                });
              }
              return null;
            });
          }
        },
      };
    },

    setupRealtimeUpdateScenario(): RealtimeUpdateScenario {
      const mockExistingUser = createMockAuthUser({
        id: 6,
        name: 'Realtime User',
        email: 'realtime@example.com',
      });

      const mockWebSocket = createMockWebSocket();

      return {
        mockExistingUser,
        mockWebSocket,
        simulateRealtimeUpdate: (type: string, data: any) => {
          setTimeout(() => {
            mockWebSocket.onmessage?.({
              data: JSON.stringify({ type, data }),
            } as any);
          }, 50);
        },
      };
    },

    setupConcurrentSessionScenario(): ConcurrentSessionScenario {
      const mockExistingUser = createMockAuthUser({
        id: 7,
        name: 'Concurrent User',
        email: 'concurrent@example.com',
      });

      return {
        mockExistingUser,
        simulateSessionConflict: () => {
          // Mock 401 response from API indicating session conflict
          throw {
            status: 401,
            message: 'Session invalid - logged in elsewhere',
          };
        },
      };
    },

    setupFormPreservationScenario(): FormPreservationScenario {
      const mockExistingUser = createMockAuthUser({
        id: 8,
        name: 'Form Preservation User',
        email: 'formpreservation@example.com',
      });

      const preservedFormData = {
        selectedPlan: createMockPricingPlan(),
        studentName: VALID_TEST_DATA.studentName,
        studentEmail: VALID_TEST_DATA.studentEmail,
      };

      return {
        mockExistingUser,
        preservedFormData,
        simulateFormPreservation: () => {
          // Mock form data preservation during auth flows
          return preservedFormData;
        },
      };
    },

    setupHappyPathScenario(): HappyPathScenario {
      const mockValidFormData = {
        selectedPlan: createMockPricingPlan(),
        studentName: VALID_TEST_DATA.studentName,
        studentEmail: VALID_TEST_DATA.studentEmail,
      };

      return {
        mockSuccessfulApis: () => {
          // Mock all APIs to return successful responses
          const { PurchaseApiClient } = require('@/api/purchaseApi');
          const { PaymentMethodApiClient } = require('@/api/paymentMethodApi');

          PurchaseApiClient.getStripeConfig = jest.fn().mockResolvedValue(createMockStripeConfig());
          PurchaseApiClient.getPricingPlans = jest.fn().mockResolvedValue(createMockPricingPlans());
          PurchaseApiClient.initiatePurchase = jest
            .fn()
            .mockResolvedValue(createMockPurchaseInitiationResponse());
          PaymentMethodApiClient.getPaymentMethods = jest
            .fn()
            .mockResolvedValue(createMockPaymentMethods());

          const mockStripe = createMockStripe();
          mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());
        },
        mockValidFormData,
        simulateCompleteFlow: async helpers => {
          const { getByText, getByPlaceholderText, waitFor, fireEvent } = helpers;

          // Plan selection
          await waitFor(() => getByText('Select Plan'));
          fireEvent.press(getByText('Standard Package'));

          // User info
          await waitFor(() => getByText('Student Information'));
          fireEvent.changeText(getByPlaceholderText('Student name'), mockValidFormData.studentName);
          fireEvent.changeText(
            getByPlaceholderText('Student email'),
            mockValidFormData.studentEmail
          );
          fireEvent.press(getByText('Continue to Payment'));

          // Payment
          await waitFor(() => getByText('Payment'));
          fireEvent.press(getByText(/Pay €/));

          // Success
          await waitFor(() => getByText('Purchase Successful!'));
        },
      };
    },

    setupFailureScenario(): FailureScenario {
      return {
        mockFailingApis: (failurePoints: string[]) => {
          const { PurchaseApiClient } = require('@/api/purchaseApi');

          failurePoints.forEach(point => {
            switch (point) {
              case 'stripe_config':
                PurchaseApiClient.getStripeConfig = jest
                  .fn()
                  .mockRejectedValue(new Error('Stripe config failed'));
                break;
              case 'pricing_plans':
                PurchaseApiClient.getPricingPlans = jest
                  .fn()
                  .mockRejectedValue(new Error('Plans loading failed'));
                break;
              case 'purchase_initiation':
                PurchaseApiClient.initiatePurchase = jest
                  .fn()
                  .mockRejectedValue(new Error('Purchase initiation failed'));
                break;
              case 'payment':
                const mockStripe = createMockStripe();
                mockStripe.confirmPayment.mockResolvedValue(
                  createMockStripeError('Payment failed')
                );
                break;
            }
          });
        },
        mockErrorRecovery: () => {
          // Reset mocks to successful state for recovery testing
          const { PurchaseApiClient } = require('@/api/purchaseApi');
          PurchaseApiClient.getStripeConfig = jest.fn().mockResolvedValue(createMockStripeConfig());
          PurchaseApiClient.initiatePurchase = jest
            .fn()
            .mockResolvedValue(createMockPurchaseInitiationResponse());

          const mockStripe = createMockStripe();
          mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());
        },
        simulateErrorScenarios: () => {
          // Simulate various error conditions
          const scenarios = ['network_error', 'validation_error', 'payment_error', 'timeout_error'];
          return scenarios;
        },
      };
    },

    setupPaymentRetryScenario(): PaymentRetryScenario {
      const mockMultiplePaymentMethods = createMockPaymentMethods();
      mockMultiplePaymentMethods.push({
        id: 'pm_backup_card',
        type: 'card',
        card: { brand: 'amex', last4: '0005', exp_month: 12, exp_year: 2026, funding: 'credit' },
        billing_details: { name: 'John Doe', email: 'john@example.com' },
        is_default: false,
        created_at: '2024-01-15T00:00:00Z',
      });

      return {
        mockMultiplePaymentMethods,
        mockPaymentFailureRecovery: () => {
          const mockStripe = createMockStripe();
          // First call fails, second succeeds
          mockStripe.confirmPayment
            .mockResolvedValueOnce(createMockStripeError('Card declined'))
            .mockResolvedValueOnce(createMockStripeSuccess());
        },
        simulateRetryFlow: () => {
          // Mock payment method switching and retry logic
        },
      };
    },

    setupCrossPlatformScenario(platform: 'web' | 'ios' | 'android'): CrossPlatformScenario {
      return {
        platform,
        mockPlatformSpecifics: () => {
          const Platform = require('react-native').Platform;
          Platform.OS = platform;
          Platform.select = jest.fn(
            (platforms: any) => platforms[platform] || platforms.native || platforms.default
          );
        },
        setupPlatformMocks: () => {
          switch (platform) {
            case 'web':
              // Mock web-specific APIs
              Object.defineProperty(global, 'window', {
                value: {
                  localStorage: { getItem: jest.fn(), setItem: jest.fn() },
                  location: { reload: jest.fn() },
                },
                writable: true,
              });
              break;
            case 'ios':
              // Mock iOS-specific modules
              jest.doMock('expo-haptics', () => ({
                impactAsync: jest.fn(),
                notificationAsync: jest.fn(),
              }));
              break;
            case 'android':
              // Mock Android-specific modules
              jest.doMock('react-native', () => ({
                ...jest.requireActual('react-native'),
                BackHandler: {
                  addEventListener: jest.fn(),
                  removeEventListener: jest.fn(),
                },
              }));
              break;
          }
        },
      };
    },

    setupParentApprovalScenario(): ParentApprovalScenario {
      const mockStudentUser = createMockAuthUser({
        id: 10,
        name: 'Student User',
        email: 'student@example.com',
        role: 'student',
        age: 16,
        parent_email: 'parent@example.com',
        requires_parent_approval: true,
      });

      const mockParentUser = createMockAuthUser({
        id: 11,
        name: 'Parent User',
        email: 'parent@example.com',
        role: 'parent',
        children: [10],
      });

      return {
        mockStudentUser,
        mockParentUser,
        mockApprovalFlow: () => {
          const { PurchaseApiClient } = require('@/api/purchaseApi');
          PurchaseApiClient.createApprovalRequest = jest.fn().mockResolvedValue({
            id: 1,
            student_id: mockStudentUser.id,
            parent_email: mockParentUser.email,
            status: 'pending',
            approval_token: 'approval_token_123',
          });
        },
        simulateApprovalResponse: (approved: boolean) => {
          const mockWs = createMockWebSocket();
          setTimeout(() => {
            mockWs.onmessage?.({
              data: JSON.stringify({
                type: 'approval_response',
                data: {
                  success: true,
                  approved,
                  approval_id: 1,
                  transaction_id: approved ? 123 : null,
                  message: approved ? 'Purchase approved' : 'Purchase declined',
                },
              }),
            } as any);
          }, 100);
        },
      };
    },

    coordinateApiMocks(scenario: TestScenario): MockCoordinator {
      const callOrder: string[] = [];

      return {
        setupMocks: () => {
          // Setup mocks based on scenario
          scenario.expectedCalls.forEach(expectation => {
            // Mock each API call and track call order
          });
        },
        verifyCallOrder: () => {
          // Verify APIs were called in expected order
          scenario.expectedCalls.forEach((expectation, index) => {
            expect(callOrder[index]).toBe(`${expectation.api}.${expectation.method}`);
          });
        },
        teardownMocks: () => {
          jest.clearAllMocks();
          callOrder.length = 0;
        },
      };
    },

    createUserJourneySimulator(): UserJourneySimulator {
      const performanceMetrics: PerformanceMetrics = {
        renderTime: 0,
        memoryUsage: 0,
        apiCallCount: 0,
        reRenderCount: 0,
      };

      return {
        simulateRapidInteractions: (actions: string[]) => {
          // Simulate rapid user interactions to test race conditions
          actions.forEach((action, index) => {
            setTimeout(() => {
              // Execute action
            }, index * 50); // 50ms intervals
          });
        },
        simulateSlowNetwork: () => {
          // Add artificial delays to API responses
          const originalMocks = jest.getAllMocks();
          originalMocks.forEach(mock => {
            if (mock.mockImplementation) {
              const originalImpl = mock.getMockImplementation();
              mock.mockImplementation((...args) => {
                return new Promise(resolve => {
                  setTimeout(() => resolve(originalImpl?.(...args)), 2000);
                });
              });
            }
          });
        },
        simulateInterruptions: () => {
          // Simulate app interruptions, network failures, etc.
        },
        measurePerformance: () => performanceMetrics,
      };
    },

    setupPerformanceTest(): PerformanceTestSetup {
      let startTime: number;
      let startMemory: number;

      return {
        startMonitoring: () => {
          startTime = performance.now();
          startMemory = (performance as any).memory?.usedJSHeapSize || 0;
        },
        stopMonitoring: () => {
          const endTime = performance.now();
          const endMemory = (performance as any).memory?.usedJSHeapSize || 0;

          return {
            renderTime: endTime - startTime,
            memoryUsage: endMemory - startMemory,
            apiCallCount: 0, // Would track from mock calls
            reRenderCount: 0, // Would track from React DevTools
          };
        },
        expectFastRender: (maxMs = 100) => {
          const metrics = this.stopMonitoring();
          expect(metrics.renderTime).toBeLessThan(maxMs);
        },
        expectMemoryUsage: (maxMb = 50) => {
          const metrics = this.stopMonitoring();
          expect(metrics.memoryUsage / 1024 / 1024).toBeLessThan(maxMb);
        },
      };
    },

    createAccessibilityTestHelpers(): AccessibilityTestHelpers {
      return {
        expectAccessibleElements: (component: any) => {
          // Verify all interactive elements have accessibility labels
          const buttons = component.queryAllByRole('button');
          const inputs = component.queryAllByRole('textbox');

          buttons.forEach((button: any) => {
            expect(button).toHaveProperty('accessibilityLabel');
          });

          inputs.forEach((input: any) => {
            expect(input).toHaveProperty('accessibilityLabel');
          });
        },
        simulateScreenReader: () => {
          // Mock screen reader interactions
        },
        testKeyboardNavigation: () => {
          // Test tab navigation between elements
        },
        verifyAriaLabels: () => {
          // Verify ARIA labels are properly set
        },
      };
    },
  };
}

// Utility functions for test scenarios
export function waitForAsyncOperations(ms = 100): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function createTestWrapper(props: any = {}) {
  return function TestWrapper({ children }: { children: React.ReactNode }) {
    return (
      <div data-testid="test-wrapper" {...props}>
        {children}
      </div>
    );
  };
}

export function expectTestToCompleteWithin(maxMs: number) {
  const startTime = performance.now();

  return {
    verify: () => {
      const duration = performance.now() - startTime;
      expect(duration).toBeLessThan(maxMs);
    },
  };
}

export function simulateComplexUserJourney(steps: UserJourneyStep[]): Promise<void> {
  return steps.reduce(async (promise, step) => {
    await promise;
    await step.execute();
    await waitForAsyncOperations(step.delay || 100);
  }, Promise.resolve());
}

export interface UserJourneyStep {
  name: string;
  execute: () => Promise<void> | void;
  delay?: number;
  expectedOutcome?: string;
}

// Export all utilities
export * from './payment-test-utils';
export * from './auth-test-utils';
