/**
 * usePurchaseFlow Hook Tests
 *
 * Comprehensive test suite for the purchase flow state management hook.
 * Tests state transitions, form validation, API integration, and error handling.
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';

import {
  createMockPricingPlan,
  createMockStripeConfig,
  createMockPurchaseInitiationResponse,
  createMockStripe,
  createMockElements,
  STRIPE_TEST_CARDS,
  createMockStripeSuccess,
  createMockStripeError,
  VALID_TEST_DATA,
  INVALID_TEST_DATA,
} from '@/__tests__/utils/payment-test-utils';
import { PurchaseApiClient } from '@/api/purchaseApi';
import { usePurchaseFlow } from '@/hooks/usePurchaseFlow';

// Mock the API client
jest.mock('@/api/purchaseApi');
const mockPurchaseApiClient = PurchaseApiClient as jest.Mocked<typeof PurchaseApiClient>;

// Mock React Native Alert
jest.mock('react-native', () => ({
  Alert: {
    alert: jest.fn(),
  },
}));

describe('usePurchaseFlow Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Setup default successful API responses
    mockPurchaseApiClient.getStripeConfig.mockResolvedValue(createMockStripeConfig());
  });

  describe('Initial State', () => {
    it('initializes with correct default state', () => {
      const { result } = renderHook(() => usePurchaseFlow());

      expect(result.current.state.step).toBe('plan-selection');
      expect(result.current.state.formData.selectedPlan).toBeNull();
      expect(result.current.state.formData.studentName).toBe('');
      expect(result.current.state.formData.studentEmail).toBe('');
      expect(result.current.state.formData.isProcessing).toBe(false);
      expect(result.current.state.formData.errors).toEqual({});
      expect(result.current.state.paymentIntentSecret).toBeNull();
      expect(result.current.state.transactionId).toBeNull();
      expect(result.current.state.errorMessage).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.canProceed).toBe(false);
    });

    it('loads Stripe configuration on mount', async () => {
      const stripeConfig = createMockStripeConfig();
      mockPurchaseApiClient.getStripeConfig.mockResolvedValue(stripeConfig);

      const { result } = renderHook(() => usePurchaseFlow());

      await waitFor(() => {
        expect(result.current.state.stripeConfig).toEqual(stripeConfig);
      });

      expect(mockPurchaseApiClient.getStripeConfig).toHaveBeenCalledTimes(1);
    });

    it('handles Stripe configuration loading error', async () => {
      const error = new Error('Failed to load Stripe config');
      mockPurchaseApiClient.getStripeConfig.mockRejectedValue(error);

      const { result } = renderHook(() => usePurchaseFlow());

      await waitFor(() => {
        expect(result.current.state.errorMessage).toBe('Failed to load Stripe config');
      });
    });
  });

  describe('Plan Selection', () => {
    it('selects plan and transitions to user-info step', () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      expect(result.current.state.step).toBe('user-info');
      expect(result.current.state.formData.selectedPlan).toEqual(plan);
      expect(result.current.state.formData.errors).toEqual({});
      expect(result.current.state.errorMessage).toBeNull();
    });

    it('enables canProceed when plan is selected', () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      // Should be able to proceed from plan selection
      act(() => {
        result.current.actions.selectPlan(plan);
      });

      expect(result.current.state.step).toBe('user-info');
    });
  });

  describe('Student Information', () => {
    it('updates student information correctly', () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      expect(result.current.state.formData.studentName).toBe(VALID_TEST_DATA.studentName);
      expect(result.current.state.formData.studentEmail).toBe(VALID_TEST_DATA.studentEmail);
    });

    it('validates student name correctly', () => {
      const { result } = renderHook(() => usePurchaseFlow());

      act(() => {
        result.current.actions.updateStudentInfo('', VALID_TEST_DATA.studentEmail);
      });

      expect(result.current.state.formData.errors.name).toBe('Name is required');

      act(() => {
        result.current.actions.updateStudentInfo('A', VALID_TEST_DATA.studentEmail);
      });

      // Should still have error for too short name
      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      expect(result.current.state.formData.errors.name).toBeUndefined();
    });

    it('validates email format correctly', () => {
      const { result } = renderHook(() => usePurchaseFlow());

      act(() => {
        result.current.actions.updateStudentInfo(VALID_TEST_DATA.studentName, '');
      });

      expect(result.current.state.formData.errors.email).toBe('Email is required');

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          INVALID_TEST_DATA.studentEmail
        );
      });

      expect(result.current.state.formData.errors.email).toBe('Please enter a valid email address');

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      expect(result.current.state.formData.errors.email).toBeUndefined();
    });

    it('trims and normalizes email input', () => {
      const { result } = renderHook(() => usePurchaseFlow());

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          '  JOHN@EXAMPLE.COM  '
        );
      });

      expect(result.current.state.formData.studentEmail).toBe('john@example.com');
    });

    it('calculates canProceed correctly for user-info step', () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      // Should not proceed with invalid data
      expect(result.current.canProceed).toBe(false);

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      expect(result.current.canProceed).toBe(true);
    });
  });

  describe('Purchase Initiation', () => {
    it('successfully initiates purchase with valid data', async () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();
      const response = createMockPurchaseInitiationResponse();

      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(response);

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      await act(async () => {
        await result.current.actions.initiatePurchase();
      });

      expect(mockPurchaseApiClient.initiatePurchase).toHaveBeenCalledWith({
        plan_id: plan.id,
        student_info: {
          name: VALID_TEST_DATA.studentName,
          email: VALID_TEST_DATA.studentEmail,
        },
      });

      expect(result.current.state.step).toBe('payment');
      expect(result.current.state.paymentIntentSecret).toBe(response.client_secret);
      expect(result.current.state.transactionId).toBe(response.transaction_id);
    });

    it('prevents initiation with invalid form data', async () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      // Don't fill in student info - should be invalid
      await act(async () => {
        await result.current.actions.initiatePurchase();
      });

      expect(mockPurchaseApiClient.initiatePurchase).not.toHaveBeenCalled();
      expect(result.current.state.step).toBe('user-info');
      expect(result.current.state.formData.errors).toEqual({
        name: 'Name is required',
        email: 'Email is required',
      });
    });

    it('prevents initiation without selected plan', async () => {
      const { result } = renderHook(() => usePurchaseFlow());

      await act(async () => {
        await result.current.actions.initiatePurchase();
      });

      expect(result.current.state.step).toBe('error');
      expect(result.current.state.errorMessage).toBe('No plan selected');
    });

    it('handles API validation errors', async () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();
      const errorResponse = {
        success: false,
        message: 'Validation failed',
        field_errors: {
          'student_info.email': ['Email already exists'],
          'student_info.name': ['Name is too short'],
        },
      };

      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(errorResponse);

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      await act(async () => {
        await result.current.actions.initiatePurchase();
      });

      expect(result.current.state.formData.errors).toEqual({
        email: 'Email already exists',
        name: 'Name is too short',
      });
      expect(result.current.state.errorMessage).toBe('Validation failed');
      expect(result.current.state.step).toBe('user-info');
    });

    it('handles API network errors', async () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();
      const error = new Error('Network error');

      mockPurchaseApiClient.initiatePurchase.mockRejectedValue(error);

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      await act(async () => {
        await result.current.actions.initiatePurchase();
      });

      expect(result.current.state.errorMessage).toBe('Network error');
      expect(result.current.state.formData.isProcessing).toBe(false);
    });

    it('shows loading state during purchase initiation', async () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();

      // Make the API call hang to test loading state
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockPurchaseApiClient.initiatePurchase.mockReturnValue(pendingPromise);

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      act(() => {
        result.current.actions.initiatePurchase();
      });

      expect(result.current.state.formData.isProcessing).toBe(true);
      expect(result.current.isLoading).toBe(true);

      // Resolve the promise
      act(() => {
        resolvePromise!(createMockPurchaseInitiationResponse());
      });

      await waitFor(() => {
        expect(result.current.state.formData.isProcessing).toBe(false);
      });
    });
  });

  describe('Payment Confirmation', () => {
    it('successfully confirms payment', async () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const mockStripe = createMockStripe();
      const mockElements = createMockElements();

      // Setup payment step
      act(() => {
        result.current.actions.selectPlan(createMockPricingPlan());
      });

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      // Manually set payment step with secret
      act(() => {
        const currentState = result.current.state;
        result.current.state.step = 'payment';
        result.current.state.paymentIntentSecret = 'pi_test_123_secret';
      });

      mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());

      await act(async () => {
        await result.current.actions.confirmPayment(mockStripe as any, mockElements as any);
      });

      expect(mockStripe.confirmPayment).toHaveBeenCalledWith({
        elements: mockElements,
        confirmParams: {
          return_url: `${window.location.origin}/purchase/success`,
        },
        redirect: 'if_required',
      });

      expect(result.current.state.step).toBe('success');
    });

    it('handles payment confirmation errors', async () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const mockStripe = createMockStripe();
      const mockElements = createMockElements();

      // Setup payment step
      act(() => {
        result.current.actions.selectPlan(createMockPricingPlan());
      });

      // Manually set payment step with secret
      act(() => {
        const currentState = result.current.state;
        result.current.state.step = 'payment';
        result.current.state.paymentIntentSecret = 'pi_test_123_secret';
      });

      const errorMessage = 'Your card was declined';
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeError(errorMessage));

      await act(async () => {
        await result.current.actions.confirmPayment(mockStripe as any, mockElements as any);
      });

      expect(result.current.state.step).toBe('error');
      expect(result.current.state.errorMessage).toBe(errorMessage);
    });

    it('handles incomplete payment processing', async () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const mockStripe = createMockStripe();
      const mockElements = createMockElements();

      // Setup payment step
      act(() => {
        const currentState = result.current.state;
        result.current.state.step = 'payment';
        result.current.state.paymentIntentSecret = 'pi_test_123_secret';
      });

      mockStripe.confirmPayment.mockResolvedValue({
        error: null,
        paymentIntent: {
          id: 'pi_test_123',
          status: 'processing', // Not succeeded
        },
      });

      await act(async () => {
        await result.current.actions.confirmPayment(mockStripe as any, mockElements as any);
      });

      expect(result.current.state.step).toBe('error');
      expect(result.current.state.errorMessage).toBe('Payment processing incomplete');
    });

    it('prevents payment confirmation without payment intent secret', async () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const mockStripe = createMockStripe();
      const mockElements = createMockElements();

      await act(async () => {
        await result.current.actions.confirmPayment(mockStripe as any, mockElements as any);
      });

      expect(result.current.state.step).toBe('error');
      expect(result.current.state.errorMessage).toBe('No payment intent available');
    });

    it('shows loading state during payment confirmation', async () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const mockStripe = createMockStripe();
      const mockElements = createMockElements();

      // Setup payment step
      act(() => {
        const currentState = result.current.state;
        result.current.state.step = 'payment';
        result.current.state.paymentIntentSecret = 'pi_test_123_secret';
      });

      // Make the payment confirmation hang
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockStripe.confirmPayment.mockReturnValue(pendingPromise);

      act(() => {
        result.current.actions.confirmPayment(mockStripe as any, mockElements as any);
      });

      expect(result.current.state.formData.isProcessing).toBe(true);
      expect(result.current.isLoading).toBe(true);

      // Resolve the promise
      act(() => {
        resolvePromise!(createMockStripeSuccess());
      });

      await waitFor(() => {
        expect(result.current.state.formData.isProcessing).toBe(false);
      });
    });
  });

  describe('Flow Control', () => {
    it('resets flow to initial state', () => {
      const { result } = renderHook(() => usePurchaseFlow());

      // Make some changes
      act(() => {
        result.current.actions.selectPlan(createMockPricingPlan());
      });

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      act(() => {
        result.current.actions.setError('Test error');
      });

      // Reset
      act(() => {
        result.current.actions.resetFlow();
      });

      expect(result.current.state.step).toBe('plan-selection');
      expect(result.current.state.formData.selectedPlan).toBeNull();
      expect(result.current.state.formData.studentName).toBe('');
      expect(result.current.state.formData.studentEmail).toBe('');
      expect(result.current.state.errorMessage).toBeNull();
      expect(result.current.state.paymentIntentSecret).toBeNull();
      expect(result.current.state.transactionId).toBeNull();
    });

    it('sets error and transitions to error step', () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const errorMessage = 'Test error message';

      act(() => {
        result.current.actions.setError(errorMessage);
      });

      expect(result.current.state.step).toBe('error');
      expect(result.current.state.errorMessage).toBe(errorMessage);
      expect(result.current.state.formData.isProcessing).toBe(false);
    });
  });

  describe('Computed Properties', () => {
    it('calculates isLoading correctly', () => {
      const { result } = renderHook(() => usePurchaseFlow());

      expect(result.current.isLoading).toBe(false);

      // Simulate processing state
      act(() => {
        const currentState = result.current.state;
        result.current.state.formData.isProcessing = true;
      });

      expect(result.current.isLoading).toBe(true);
    });

    it('calculates canProceed for different steps', () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();

      // Plan selection step
      expect(result.current.canProceed).toBe(false);

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      // User info step - should not proceed without valid info
      expect(result.current.canProceed).toBe(false);

      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      expect(result.current.canProceed).toBe(true);

      // Payment step - need stripe config and payment intent
      act(() => {
        const currentState = result.current.state;
        result.current.state.step = 'payment';
      });

      expect(result.current.canProceed).toBe(false); // No payment intent

      act(() => {
        const currentState = result.current.state;
        result.current.state.paymentIntentSecret = 'pi_test_123_secret';
        result.current.state.stripeConfig = createMockStripeConfig();
      });

      expect(result.current.canProceed).toBe(true);

      // Success and error steps
      act(() => {
        const currentState = result.current.state;
        result.current.state.step = 'success';
      });

      expect(result.current.canProceed).toBe(false);

      act(() => {
        const currentState = result.current.state;
        result.current.state.step = 'error';
      });

      expect(result.current.canProceed).toBe(false);
    });
  });

  describe('Form Validation', () => {
    it('validates complete form correctly', () => {
      const { result } = renderHook(() => usePurchaseFlow());
      const plan = createMockPricingPlan();

      act(() => {
        result.current.actions.selectPlan(plan);
      });

      // Test validation with empty fields
      act(() => {
        result.current.actions.updateStudentInfo('', '');
      });

      expect(result.current.state.formData.errors).toEqual({
        name: 'Name is required',
        email: 'Email is required',
      });

      // Test validation with short name
      act(() => {
        result.current.actions.updateStudentInfo('A', VALID_TEST_DATA.studentEmail);
      });

      // Test validation with invalid email
      act(() => {
        result.current.actions.updateStudentInfo(VALID_TEST_DATA.studentName, 'invalid-email');
      });

      // Test validation with valid data
      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      expect(Object.keys(result.current.state.formData.errors)).toHaveLength(0);
    });

    it('validates email format with various inputs', () => {
      const { result } = renderHook(() => usePurchaseFlow());

      const testCases = [
        { email: '', shouldBeValid: false },
        { email: 'invalid', shouldBeValid: false },
        { email: '@example.com', shouldBeValid: false },
        { email: 'user@', shouldBeValid: false },
        { email: 'user@.com', shouldBeValid: false },
        { email: 'user@example', shouldBeValid: false },
        { email: 'user@example.', shouldBeValid: false },
        { email: 'user@example.com', shouldBeValid: true },
        { email: 'user.name@example.com', shouldBeValid: true },
        { email: 'user+tag@example.co.uk', shouldBeValid: true },
      ];

      testCases.forEach(({ email, shouldBeValid }) => {
        act(() => {
          result.current.actions.updateStudentInfo(VALID_TEST_DATA.studentName, email);
        });

        const hasEmailError = !!result.current.state.formData.errors.email;
        expect(hasEmailError).toBe(!shouldBeValid);
      });
    });
  });

  describe('Error Recovery', () => {
    it('clears errors when taking corrective actions', () => {
      const { result } = renderHook(() => usePurchaseFlow());

      // Set an error
      act(() => {
        result.current.actions.setError('Test error');
      });

      expect(result.current.state.errorMessage).toBe('Test error');

      // Select a plan should clear error
      act(() => {
        result.current.actions.selectPlan(createMockPricingPlan());
      });

      expect(result.current.state.errorMessage).toBeNull();
    });

    it('clears field errors when updating correct data', () => {
      const { result } = renderHook(() => usePurchaseFlow());

      // Set validation errors
      act(() => {
        result.current.actions.updateStudentInfo('', '');
      });

      expect(result.current.state.formData.errors.name).toBeTruthy();
      expect(result.current.state.formData.errors.email).toBeTruthy();

      // Fix name error
      act(() => {
        result.current.actions.updateStudentInfo(VALID_TEST_DATA.studentName, '');
      });

      expect(result.current.state.formData.errors.name).toBeUndefined();
      expect(result.current.state.formData.errors.email).toBeTruthy();

      // Fix email error
      act(() => {
        result.current.actions.updateStudentInfo(
          VALID_TEST_DATA.studentName,
          VALID_TEST_DATA.studentEmail
        );
      });

      expect(result.current.state.formData.errors.name).toBeUndefined();
      expect(result.current.state.formData.errors.email).toBeUndefined();
    });
  });
});
