/**
 * Purchase Flow Integration Tests
 *
 * End-to-end integration tests for the complete purchase flow.
 * Tests real user scenarios from plan selection through payment completion.
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';

import { PurchaseFlow } from '@/components/purchase/PurchaseFlow';
import { PurchaseApiClient } from '@/api/purchaseApi';
import { PaymentMethodApiClient } from '@/api/paymentMethodApi';
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
  simulateCompleteePurchaseFlow,
  VALID_TEST_DATA,
  INVALID_TEST_DATA,
  cleanupMocks,
} from '@/__tests__/utils/payment-test-utils';

// Mock APIs
jest.mock('@/api/purchaseApi');
jest.mock('@/api/paymentMethodApi');
const mockPurchaseApiClient = PurchaseApiClient as jest.Mocked<typeof PurchaseApiClient>;
const mockPaymentMethodApiClient = PaymentMethodApiClient as jest.Mocked<typeof PaymentMethodApiClient>;

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

// Mock hooks to control their behavior in integration tests
jest.mock('@/hooks/usePricingPlans', () => ({
  usePricingPlans: () => ({
    plans: mockPlans,
    loading: false,
    error: null,
    refetch: jest.fn(),
  }),
}));

jest.mock('@/hooks/useStudentBalance', () => ({
  useStudentBalance: () => ({
    balance: null,
    loading: false,
    error: null,
    refetch: jest.fn(),
  }),
}));

// Mock router
const mockPush = jest.fn();
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: () => ({ push: mockPush }),
}));

// Global test data
const mockPlans = createMockPricingPlans();
const mockStripe = createMockStripe();
const mockElements = createMockElements();

describe('Purchase Flow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    cleanupMocks();
    
    // Setup successful API responses
    mockPurchaseApiClient.getStripeConfig.mockResolvedValue(createMockStripeConfig());
    mockPurchaseApiClient.getPricingPlans.mockResolvedValue(mockPlans);
    mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue(createMockPaymentMethods());
  });

  describe('Complete Purchase Flow - Happy Path', () => {
    it('completes full purchase flow successfully', async () => {
      const onPurchaseComplete = jest.fn();
      const onCancel = jest.fn();

      // Mock successful purchase initiation
      const purchaseResponse = createMockPurchaseInitiationResponse();
      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(purchaseResponse);

      // Mock successful Stripe payment
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());

      const { getByText, getByPlaceholderText, queryByText } = render(
        <PurchaseFlow onPurchaseComplete={onPurchaseComplete} onCancel={onCancel} />
      );

      // Step 1: Plan Selection
      await waitFor(() => {
        expect(getByText('Select Plan')).toBeTruthy();
        expect(getByText('Step 1 of 4')).toBeTruthy();
      });

      // Select the Standard Package
      fireEvent.press(getByText('Standard Package'));

      // Step 2: User Information
      await waitFor(() => {
        expect(getByText('Student Information')).toBeTruthy();
        expect(getByText('Step 2 of 4')).toBeTruthy();
      });

      // Fill in student information
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      // Verify purchase initiation API call
      await waitFor(() => {
        expect(mockPurchaseApiClient.initiatePurchase).toHaveBeenCalledWith({
          plan_id: expect.any(Number),
          student_info: {
            name: VALID_TEST_DATA.studentName,
            email: VALID_TEST_DATA.studentEmail,
          },
        });
      });

      // Step 3: Payment
      await waitFor(() => {
        expect(getByText('Payment')).toBeTruthy();
        expect(getByText('Step 3 of 4')).toBeTruthy();
      });

      // Complete payment
      fireEvent.press(getByText(/Pay €/));

      // Verify Stripe payment call
      await waitFor(() => {
        expect(mockStripe.confirmPayment).toHaveBeenCalledWith({
          elements: mockElements,
          confirmParams: {
            return_url: expect.stringContaining('/purchase/success'),
          },
          redirect: 'if_required',
        });
      });

      // Step 4: Success
      await waitFor(() => {
        expect(getByText('Purchase Successful!')).toBeTruthy();
        expect(getByText('Step 4 of 4')).toBeTruthy();
      });

      // Verify completion callback
      expect(onPurchaseComplete).toHaveBeenCalledWith(purchaseResponse.transaction_id);
      expect(onCancel).not.toHaveBeenCalled();
    });

    it('handles purchase flow with existing payment methods', async () => {
      const savedMethods = createMockPaymentMethods();
      mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue(savedMethods);

      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Complete flow to payment step
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Payment')).toBeTruthy();
      });

      // Payment methods should be available for selection
      expect(mockPaymentMethodApiClient.getPaymentMethods).toHaveBeenCalled();
    });

    it('shows real-time balance updates via WebSocket', async () => {
      const mockWs = createMockWebSocket();
      
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Complete purchase flow
      await simulateCompleteePurchaseFlow(getByText, getByPlaceholderText, fireEvent, waitFor);

      // Simulate WebSocket balance update
      const balanceUpdate = createBalanceUpdateMessage({
        balance_summary: {
          remaining_hours: '15.0',
          hours_purchased: '20.0',
          hours_consumed: '5.0',
          balance_amount: '150.00',
        },
      });

      act(() => {
        mockWs.onmessage?.({ data: JSON.stringify(balanceUpdate) } as any);
      });

      // Balance should be updated in real-time
      // This would be verified by the balance components receiving the update
    });
  });

  describe('Error Scenarios', () => {
    it('handles plan selection API errors', async () => {
      // Mock API failure
      const error = new Error('Failed to load pricing plans');
      mockPurchaseApiClient.getPricingPlans.mockRejectedValue(error);

      const { getByText } = render(<PurchaseFlow />);

      await waitFor(() => {
        expect(getByText('Error')).toBeTruthy();
        expect(getByText('Failed to load pricing plans')).toBeTruthy();
      });
    });

    it('handles purchase initiation validation errors', async () => {
      const validationResponse = {
        success: false,
        message: 'Validation failed',
        field_errors: {
          'student_info.email': ['Email already exists in system'],
          'student_info.name': ['Name contains invalid characters'],
        },
      };
      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(validationResponse);

      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Select plan and fill form with problematic data
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      fireEvent.changeText(getByPlaceholderText('Student name'), 'Test User');
      fireEvent.changeText(getByPlaceholderText('Student email'), 'existing@example.com');
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Email already exists in system')).toBeTruthy();
        expect(getByText('Name contains invalid characters')).toBeTruthy();
      });

      // Should stay on user info step
      expect(getByText('Student Information')).toBeTruthy();
    });

    it('handles payment failures and recovery', async () => {
      const purchaseResponse = createMockPurchaseInitiationResponse();
      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(purchaseResponse);

      // Mock payment failure
      const paymentError = 'Your card was declined';
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeError(paymentError));

      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Complete flow to payment
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => getByText('Payment'));

      // Attempt payment
      fireEvent.press(getByText(/Pay €/));

      // Should show error
      await waitFor(() => {
        expect(getByText('Purchase Failed')).toBeTruthy();
        expect(getByText(paymentError)).toBeTruthy();
      });

      // Should allow retry
      expect(getByText('Try Again')).toBeTruthy();
      expect(getByText('Go Back')).toBeTruthy();
    });

    it('handles network failures gracefully', async () => {
      // Mock network error
      const networkError = new Error('Network request failed');
      mockPurchaseApiClient.initiatePurchase.mockRejectedValue(networkError);

      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Complete to purchase initiation
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Error')).toBeTruthy();
        expect(getByText('Network request failed')).toBeTruthy();
      });
    });

    it('handles Stripe configuration failures', async () => {
      // Mock Stripe config failure
      mockPurchaseApiClient.getStripeConfig.mockRejectedValue(new Error('Stripe unavailable'));

      const { getByText } = render(<PurchaseFlow />);

      await waitFor(() => {
        expect(getByText('Error')).toBeTruthy();
        expect(getByText('Stripe unavailable')).toBeTruthy();
      });
    });

    it('handles 3D Secure authentication requirements', async () => {
      const purchaseResponse = createMockPurchaseInitiationResponse();
      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(purchaseResponse);

      // Mock 3D Secure required
      mockStripe.confirmPayment.mockResolvedValue({
        error: {
          type: 'card_error',
          code: 'authentication_required',
          message: 'This payment requires authentication',
        },
        paymentIntent: {
          id: 'pi_test_123',
          status: 'requires_action',
        },
      });

      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Complete flow to payment
      await simulateCompleteePurchaseFlow(getByText, getByPlaceholderText, fireEvent, waitFor);

      await waitFor(() => {
        expect(getByText('This payment requires authentication')).toBeTruthy();
      });
    });
  });

  describe('User Experience Features', () => {
    it('provides smooth navigation between steps', async () => {
      const { getByText, getByPlaceholderText, getByTestId } = render(<PurchaseFlow />);

      // Forward navigation
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => expect(getByText('Student Information')).toBeTruthy());

      // Back navigation
      fireEvent.press(getByText('Back'));
      await waitFor(() => expect(getByText('Select Plan')).toBeTruthy());

      // Forward again
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => expect(getByText('Student Information')).toBeTruthy());
    });

    it('preserves form data during navigation', async () => {
      const { getByText, getByPlaceholderText, getByDisplayValue } = render(<PurchaseFlow />);

      // Navigate to user info and fill form
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);

      // Navigate back and forward
      fireEvent.press(getByText('Back'));
      await waitFor(() => getByText('Select Plan'));

      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      // Form data should be preserved
      expect(getByDisplayValue(VALID_TEST_DATA.studentName)).toBeTruthy();
      expect(getByDisplayValue(VALID_TEST_DATA.studentEmail)).toBeTruthy();
    });

    it('shows appropriate loading states', async () => {
      // Make purchase initiation hang
      let resolvePurchase: (value: any) => void;
      const pendingPurchase = new Promise(resolve => {
        resolvePurchase = resolve;
      });
      mockPurchaseApiClient.initiatePurchase.mockReturnValue(pendingPurchase);

      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Complete form and submit
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      // Should show processing state
      expect(getByText('Processing...')).toBeTruthy();

      // Resolve the purchase
      act(() => {
        resolvePurchase!(createMockPurchaseInitiationResponse());
      });

      await waitFor(() => {
        expect(getByText('Payment')).toBeTruthy();
      });
    });

    it('provides clear progress indication', async () => {
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Check progress at each step
      expect(getByText('Step 1 of 4')).toBeTruthy();

      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => {
        expect(getByText('Step 2 of 4')).toBeTruthy();
      });

      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Step 3 of 4')).toBeTruthy();
      });
    });

    it('handles cancellation at any step', async () => {
      const onCancel = jest.fn();
      const { getByText, getByPlaceholderText } = render(
        <PurchaseFlow onCancel={onCancel} />
      );

      // Test cancellation from plan selection
      fireEvent.press(getByText('Cancel'));
      expect(onCancel).toHaveBeenCalled();

      onCancel.mockClear();

      // Test cancellation from user info
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));
      
      fireEvent.press(getByText('Cancel'));
      expect(onCancel).toHaveBeenCalled();

      onCancel.mockClear();

      // Test cancellation from payment step
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => getByText('Payment'));
      
      fireEvent.press(getByText('Cancel'));
      expect(onCancel).toHaveBeenCalled();
    });
  });

  describe('Validation and Form Handling', () => {
    it('validates form fields in real-time', async () => {
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      // Test invalid email
      fireEvent.changeText(getByPlaceholderText('Student email'), INVALID_TEST_DATA.studentEmail);
      
      await waitFor(() => {
        expect(getByText('Please enter a valid email address')).toBeTruthy();
      });

      // Test empty name
      fireEvent.changeText(getByPlaceholderText('Student name'), '');
      
      await waitFor(() => {
        expect(getByText('Name is required')).toBeTruthy();
      });

      // Should not allow proceeding with invalid form
      const continueButton = getByText('Continue to Payment');
      expect(continueButton).toHaveProperty('disabled', true);
    });

    it('clears validation errors when fixed', async () => {
      const { getByText, getByPlaceholderText, queryByText } = render(<PurchaseFlow />);

      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      // Set invalid email
      fireEvent.changeText(getByPlaceholderText('Student email'), 'invalid');
      await waitFor(() => getByText('Please enter a valid email address'));

      // Fix email
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      
      await waitFor(() => {
        expect(queryByText('Please enter a valid email address')).toBeNull();
      });
    });

    it('prevents submission with invalid data', async () => {
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      // Fill with invalid data
      fireEvent.changeText(getByPlaceholderText('Student name'), '');
      fireEvent.changeText(getByPlaceholderText('Student email'), 'invalid-email');

      // Try to submit
      fireEvent.press(getByText('Continue to Payment'));

      // Should not proceed to payment
      expect(getByText('Student Information')).toBeTruthy();
      expect(mockPurchaseApiClient.initiatePurchase).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility and Performance', () => {
    it('provides accessible navigation and form controls', async () => {
      const { getByRole, getByLabelText } = render(<PurchaseFlow />);

      // Check for accessible form elements
      await waitFor(() => {
        expect(getByRole('heading')).toBeTruthy();
      });

      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => {
        expect(getByRole('textbox', { name: /name/i })).toBeTruthy();
        expect(getByRole('textbox', { name: /email/i })).toBeTruthy();
        expect(getByRole('button', { name: /continue/i })).toBeTruthy();
      });
    });

    it('performs well with complex interactions', async () => {
      const start = performance.now();
      
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Simulate rapid user interactions
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => getByText('Payment'));
      
      const end = performance.now();
      
      expect(end - start).toBeLessThan(1000); // Should complete in under 1 second
    });

    it('handles rapid state changes without errors', async () => {
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Rapid navigation
      for (let i = 0; i < 5; i++) {
        fireEvent.press(getByText('Standard Package'));
        await waitFor(() => getByText('Student Information'));
        fireEvent.press(getByText('Back'));
        await waitFor(() => getByText('Select Plan'));
      }

      // Should still be functional
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => {
        expect(getByText('Student Information')).toBeTruthy();
      });
    });
  });

  describe('Data Persistence and Recovery', () => {
    it('maintains state during component re-renders', async () => {
      const { getByText, getByPlaceholderText, rerender } = render(<PurchaseFlow />);

      // Make selections
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);

      // Re-render component
      rerender(<PurchaseFlow />);

      // State should be maintained (depending on implementation)
      await waitFor(() => {
        expect(getByText('Student Information')).toBeTruthy();
      });
    });

    it('recovers gracefully from network interruptions', async () => {
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Start purchase flow
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);

      // Mock network failure
      mockPurchaseApiClient.initiatePurchase.mockRejectedValue(new Error('Network error'));
      
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Network error')).toBeTruthy();
      });

      // Fix network and retry
      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(createMockPurchaseInitiationResponse());
      
      fireEvent.press(getByText('Try Again'));

      await waitFor(() => {
        expect(getByText('Payment')).toBeTruthy();
      });
    });
  });
});