/**
 * Complete Purchase Flow Integration Tests
 *
 * Comprehensive end-to-end tests covering authentication integration,
 * session management, token expiry, and complete user journeys.
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@/__tests__/utils/test-utils';

import { PurchaseFlow } from '@/components/purchase/PurchaseFlow';
import { PurchaseApiClient } from '@/api/purchaseApi';
import { PaymentMethodApiClient } from '@/api/paymentMethodApi';
import { AuthApiClient } from '@/api/authApi';
import {
  createMockPricingPlans,
  createMockStripeConfig,
  createMockPurchaseInitiationResponse,
  createMockStripe,
  createMockElements,
  createMockStripeSuccess,
  createMockStripeError,
  createMockPaymentMethods,
  createMockWebSocket,
  VALID_TEST_DATA,
  cleanupMocks,
} from '@/__tests__/utils/payment-test-utils';
import {
  createMockAuthUser,
  createMockTokenResponse,
  createAuthTestWrapper,
  mockAuthenticatedUser,
  mockUnauthenticatedUser,
  simulateTokenExpiry,
  simulateSessionRecovery,
} from '@/__tests__/utils/auth-test-utils';
import { createIntegrationTestHelpers } from '@/__tests__/utils/integration-test-helpers';

// Mock APIs
jest.mock('@/api/purchaseApi');
jest.mock('@/api/paymentMethodApi');
jest.mock('@/api/authApi', () => ({
  AuthApiClient: {
    requestEmailVerification: jest.fn(),
    verifyEmailCode: jest.fn(),
    refreshToken: jest.fn(),
    logout: jest.fn(),
  },
}));
const mockPurchaseApiClient = PurchaseApiClient as jest.Mocked<typeof PurchaseApiClient>;
const mockPaymentMethodApiClient = PaymentMethodApiClient as jest.Mocked<typeof PaymentMethodApiClient>;
const mockAuthApiClient = (AuthApiClient as any) as {
  requestEmailVerification: jest.Mock;
  verifyEmailCode: jest.Mock;
  refreshToken: jest.Mock;
  logout: jest.Mock;
};

// Mock Stripe
jest.mock('@stripe/react-stripe-js', () => ({
  Elements: ({ children }: any) => children,
  PaymentElement: () => <div testID="stripe-payment-element">Payment Element</div>,
  useStripe: () => mockStripe,
  useElements: () => mockElements,
}));

jest.mock('@stripe/stripe-js', () => ({
  loadStripe: jest.fn(),
}));

// Mock router
const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: () => ({ push: mockPush, replace: mockReplace }),
}));

// Mock AsyncStorage for session persistence
const mockAsyncStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
jest.mock('@react-native-async-storage/async-storage', () => mockAsyncStorage);

// Global test data
const mockPlans = createMockPricingPlans();
const mockStripe = createMockStripe();
const mockElements = createMockElements();
const testHelpers = createIntegrationTestHelpers();

describe('Complete Purchase Flow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    cleanupMocks();
    
    // Reset AsyncStorage mocks
    mockAsyncStorage.getItem.mockReset();
    mockAsyncStorage.setItem.mockReset();
    mockAsyncStorage.removeItem.mockReset();
    
    // Setup successful API responses
    mockPurchaseApiClient.getStripeConfig.mockResolvedValue(createMockStripeConfig());
    mockPurchaseApiClient.getPricingPlans.mockResolvedValue(mockPlans);
    mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue(createMockPaymentMethods());
  });

  describe('Authentication Integration Scenarios', () => {
    it('handles new user registration → purchase flow integration', async () => {
      const { mockNewUser, onAuthComplete } = testHelpers.setupNewUserScenario();
      
      // Mock registration flow
      mockAuthApiClient.requestEmailVerification.mockResolvedValue({
        success: true,
        message: 'Verification email sent',
      });
      mockAuthApiClient.verifyEmailCode.mockResolvedValue(createMockTokenResponse());
      
      const onPurchaseComplete = jest.fn();
      const onCancel = jest.fn();

      const { getByText, getByPlaceholderText, queryByText } = render(
        createAuthTestWrapper(
          <PurchaseFlow onPurchaseComplete={onPurchaseComplete} onCancel={onCancel} />
        )
      );

      // Initial state - user not authenticated, should see auth prompts
      await waitFor(() => {
        expect(queryByText('Sign in to continue')).toBeTruthy();
      });

      // Simulate user completing registration
      act(() => {
        onAuthComplete(mockNewUser);
      });

      // Now purchase flow should be accessible
      await waitFor(() => {
        expect(getByText('Select Plan')).toBeTruthy();
        expect(getByText('Step 1 of 4')).toBeTruthy();
      });

      // Complete purchase flow with authenticated user
      const purchaseResponse = createMockPurchaseInitiationResponse();
      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(purchaseResponse);
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());

      // Step 1: Plan Selection
      fireEvent.press(getByText('Standard Package'));
      
      // Step 2: User Information (should be pre-filled from auth)
      await waitFor(() => {
        expect(getByText('Student Information')).toBeTruthy();
        expect(getByPlaceholderText('Student name')).toHaveProperty('value', mockNewUser.name);
        expect(getByPlaceholderText('Student email')).toHaveProperty('value', mockNewUser.email);
      });

      fireEvent.press(getByText('Continue to Payment'));

      // Verify API call includes authenticated user context
      await waitFor(() => {
        expect(mockPurchaseApiClient.initiatePurchase).toHaveBeenCalledWith({
          plan_id: expect.any(Number),
          student_info: {
            name: mockNewUser.name,
            email: mockNewUser.email,
          },
        });
      });

      // Step 3: Payment
      await waitFor(() => {
        expect(getByText('Payment')).toBeTruthy();
      });

      fireEvent.press(getByText(/Pay €/));

      // Step 4: Success with authenticated user benefits
      await waitFor(() => {
        expect(getByText('Purchase Successful!')).toBeTruthy();
        expect(onPurchaseComplete).toHaveBeenCalledWith(purchaseResponse.transaction_id);
      });

      // Verify session persistence
      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'user_session',
        JSON.stringify(expect.objectContaining({
          user: mockNewUser,
          token: expect.any(String),
        }))
      );
    });

    it('handles returning user authentication → purchase flow', async () => {
      const { mockExistingUser } = testHelpers.setupReturningUserScenario();
      
      // Mock existing session in storage
      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify({
        user: mockExistingUser,
        token: 'valid_jwt_token',
        refreshToken: 'valid_refresh_token',
        expiresAt: Date.now() + 3600000, // 1 hour from now
      }));

      const onPurchaseComplete = jest.fn();

      const { getByText, getByPlaceholderText, queryByText } = render(
        createAuthTestWrapper(
          <PurchaseFlow onPurchaseComplete={onPurchaseComplete} />
        )
      );

      // Should immediately show purchase flow without auth prompt
      await waitFor(() => {
        expect(getByText('Select Plan')).toBeTruthy();
        expect(queryByText('Sign in to continue')).toBeNull();
      });

      // User info should be pre-populated from session
      fireEvent.press(getByText('Standard Package'));
      
      await waitFor(() => {
        expect(getByText('Student Information')).toBeTruthy();
        expect(getByPlaceholderText('Student name')).toHaveProperty('value', mockExistingUser.name);
        expect(getByPlaceholderText('Student email')).toHaveProperty('value', mockExistingUser.email);
      });

      // Verify session was restored
      expect(mockAsyncStorage.getItem).toHaveBeenCalledWith('user_session');
    });

    it('handles authentication token expiry during checkout', async () => {
      const { mockExistingUser } = testHelpers.setupTokenExpiryScenario();
      
      // Mock session with expired token
      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify({
        user: mockExistingUser,
        token: 'expired_jwt_token',
        refreshToken: 'valid_refresh_token',
        expiresAt: Date.now() - 1000, // Expired
      }));

      // Mock successful token refresh
      mockAuthApiClient.refreshToken.mockResolvedValue(createMockTokenResponse());

      const { getByText, getByPlaceholderText } = render(
        createAuthTestWrapper(<PurchaseFlow />)
      );

      // Start purchase flow
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));
      
      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);

      // Mock purchase initiation failure due to expired token
      mockPurchaseApiClient.initiatePurchase
        .mockRejectedValueOnce(new Error('Token expired'))
        .mockResolvedValueOnce(createMockPurchaseInitiationResponse());

      fireEvent.press(getByText('Continue to Payment'));

      // Should automatically refresh token and retry
      await waitFor(() => {
        expect(mockAuthApiClient.refreshToken).toHaveBeenCalled();
        expect(getByText('Payment')).toBeTruthy();
      });

      // Verify new token was stored
      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'user_session',
        JSON.stringify(expect.objectContaining({
          token: expect.not.stringMatching('expired_jwt_token'),
        }))
      );
    });

    it('handles session persistence across app backgrounding/foregrounding', async () => {
      const { mockExistingUser } = testHelpers.setupSessionPersistenceScenario();
      
      // Mock active session
      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify({
        user: mockExistingUser,
        token: 'valid_token',
        expiresAt: Date.now() + 3600000,
      }));

      const { getByText, getByPlaceholderText } = render(
        createAuthTestWrapper(<PurchaseFlow />)
      );

      // Start purchase flow
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));
      
      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);

      // Simulate app backgrounding (common mobile scenario)
      act(() => {
        // Trigger AppState change event
        require('react-native').AppState.currentState = 'background';
        require('react-native').AppState._eventHandlers.change.forEach((handler: any) => 
          handler('background')
        );
      });

      // Simulate app foregrounding
      act(() => {
        require('react-native').AppState.currentState = 'active';
        require('react-native').AppState._eventHandlers.change.forEach((handler: any) => 
          handler('active')
        );
      });

      // Should maintain form state and user session
      await waitFor(() => {
        expect(getByText('Student Information')).toBeTruthy();
        expect(getByPlaceholderText('Student name')).toHaveProperty('value', VALID_TEST_DATA.studentName);
        expect(getByPlaceholderText('Student email')).toHaveProperty('value', VALID_TEST_DATA.studentEmail);
      });

      // Should still be able to complete purchase
      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(createMockPurchaseInitiationResponse());
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Payment')).toBeTruthy();
      });
    });

    it('handles browser refresh → flow state recovery (web platform)', async () => {
      // Mock web environment
      Object.defineProperty(window, 'location', {
        value: { reload: jest.fn() },
        writable: true,
      });

      const { mockExistingUser } = testHelpers.setupWebRecoveryScenario();
      
      // Mock session persistence in localStorage (web)
      const mockLocalStorage = {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      };
      Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'user_session') {
          return JSON.stringify({
            user: mockExistingUser,
            token: 'valid_token',
            expiresAt: Date.now() + 3600000,
          });
        }
        if (key === 'purchase_flow_state') {
          return JSON.stringify({
            step: 'user-info',
            formData: {
              selectedPlan: mockPlans[1],
              studentName: VALID_TEST_DATA.studentName,
              studentEmail: VALID_TEST_DATA.studentEmail,
            },
          });
        }
        return null;
      });

      const { getByText, getByPlaceholderText } = render(
        createAuthTestWrapper(<PurchaseFlow />)
      );

      // Should recover to the saved state
      await waitFor(() => {
        expect(getByText('Student Information')).toBeTruthy();
        expect(getByPlaceholderText('Student name')).toHaveProperty('value', VALID_TEST_DATA.studentName);
        expect(getByPlaceholderText('Student email')).toHaveProperty('value', VALID_TEST_DATA.studentEmail);
      });

      // Verify state recovery from localStorage
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('user_session');
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('purchase_flow_state');
    });

    it('handles authentication failure scenarios gracefully', async () => {
      // Mock authentication failure
      mockAuthApiClient.requestEmailVerification.mockRejectedValue(
        new Error('Email service unavailable')
      );
      
      const { getByText, queryByText } = render(
        createAuthTestWrapper(<PurchaseFlow />)
      );

      // Should show authentication error
      await waitFor(() => {
        expect(queryByText('Sign in to continue')).toBeTruthy();
      });

      // Try to access purchase flow without auth
      expect(queryByText('Select Plan')).toBeNull();
    });

    it('completes full authenticated purchase with real-time updates', async () => {
      const { mockExistingUser } = testHelpers.setupRealtimeUpdateScenario();
      const mockWs = createMockWebSocket();
      
      // Mock authenticated user
      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify({
        user: mockExistingUser,
        token: 'valid_token',
        expiresAt: Date.now() + 3600000,
      }));

      const onPurchaseComplete = jest.fn();
      const { getByText, getByPlaceholderText } = render(
        createAuthTestWrapper(
          <PurchaseFlow onPurchaseComplete={onPurchaseComplete} />
        )
      );

      // Complete full flow
      const purchaseResponse = createMockPurchaseInitiationResponse();
      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(purchaseResponse);
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());

      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));
      
      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));
      
      await waitFor(() => getByText('Payment'));
      fireEvent.press(getByText(/Pay €/));

      // Simulate real-time payment confirmation via WebSocket
      act(() => {
        mockWs.onmessage?.({ 
          data: JSON.stringify({
            type: 'payment_confirmed',
            data: {
              transaction_id: purchaseResponse.transaction_id,
              status: 'success',
              user_id: mockExistingUser.id,
            },
          })
        } as any);
      });

      await waitFor(() => {
        expect(getByText('Purchase Successful!')).toBeTruthy();
        expect(onPurchaseComplete).toHaveBeenCalledWith(purchaseResponse.transaction_id);
      });
    });
  });

  describe('Session Management Edge Cases', () => {
    it('handles concurrent session invalidation', async () => {
      const { mockExistingUser } = testHelpers.setupConcurrentSessionScenario();
      
      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify({
        user: mockExistingUser,
        token: 'valid_token',
        expiresAt: Date.now() + 3600000,
      }));

      // Mock API returning 401 (session invalidated elsewhere)
      mockPurchaseApiClient.initiatePurchase.mockRejectedValue({
        status: 401,
        message: 'Session invalid',
      });

      const { getByText, getByPlaceholderText, queryByText } = render(
        createAuthTestWrapper(<PurchaseFlow />)
      );

      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));
      
      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      // Should redirect to authentication
      await waitFor(() => {
        expect(queryByText('Sign in to continue')).toBeTruthy();
        expect(queryByText('Payment')).toBeNull();
      });

      // Verify session was cleared
      expect(mockAsyncStorage.removeItem).toHaveBeenCalledWith('user_session');
    });

    it('preserves form data during auth flows', async () => {
      const { getByText, getByPlaceholderText } = render(
        createAuthTestWrapper(<PurchaseFlow />)
      );

      // Fill form while unauthenticated
      await waitFor(() => {
        if (getByText('Select Plan')) {
          fireEvent.press(getByText('Standard Package'));
        }
      });

      await waitFor(() => {
        if (getByText('Student Information')) {
          fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
          fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
        }
      });

      // Simulate successful auth
      const { mockExistingUser } = testHelpers.setupFormPreservationScenario();
      act(() => {
        mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify({
          user: mockExistingUser,
          token: 'new_token',
          expiresAt: Date.now() + 3600000,
        }));
      });

      // Form data should be preserved
      await waitFor(() => {
        expect(getByPlaceholderText('Student name')).toHaveProperty('value', VALID_TEST_DATA.studentName);
        expect(getByPlaceholderText('Student email')).toHaveProperty('value', VALID_TEST_DATA.studentEmail);
      });
    });
  });

  afterEach(() => {
    cleanupMocks();
    // Clean up web environment mocks
    if (typeof window !== 'undefined') {
      delete (window as any).localStorage;
      delete (window as any).location;
    }
  });
});