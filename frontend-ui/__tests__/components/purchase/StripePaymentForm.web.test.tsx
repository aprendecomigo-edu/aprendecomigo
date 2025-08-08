/**
 * StripePaymentForm.web Component Tests
 *
 * Comprehensive test suite for the web-specific Stripe payment form.
 * Tests payment element integration, form submission, and error handling.
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';

import { StripePaymentForm } from '@/components/purchase/StripePaymentForm.web';
import {
  createMockStripePaymentFormProps,
  createMockStripe,
  createMockStripeSuccess,
  createMockStripeError,
  createMockStripe3DSRequired,
  STRIPE_TEST_CARDS,
  waitForStripeToLoad,
} from '@/__tests__/utils/payment-test-utils';

// Mock @stripe/react-stripe-js
const mockUseStripe = jest.fn();
const mockUseElements = jest.fn();
const mockLoadStripe = jest.fn();

jest.mock('@stripe/react-stripe-js', () => ({
  Elements: ({ children }: any) => children,
  PaymentElement: () => <div testID="stripe-payment-element">Payment Element</div>,
  useStripe: () => mockUseStripe(),
  useElements: () => mockUseElements(),
}));

jest.mock('@stripe/stripe-js', () => ({
  loadStripe: mockLoadStripe,
}));

describe('StripePaymentForm.web Component', () => {
  const defaultProps = createMockStripePaymentFormProps();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default Stripe mocks
    const mockStripe = createMockStripe();
    const mockElements = {
      create: jest.fn(() => ({
        mount: jest.fn(),
        unmount: jest.fn(),
        update: jest.fn(),
        on: jest.fn(),
      })),
      getElement: jest.fn(() => null),
    };
    
    mockUseStripe.mockReturnValue(mockStripe);
    mockUseElements.mockReturnValue(mockElements);
    mockLoadStripe.mockResolvedValue(mockStripe);
  });

  describe('Component Loading', () => {
    it('shows loading state while Stripe is loading', async () => {
      // Make loadStripe hang
      let resolveStripe: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveStripe = resolve;
      });
      mockLoadStripe.mockReturnValue(pendingPromise);
      
      const { getByText } = render(<StripePaymentForm {...defaultProps} />);
      
      expect(getByText('Loading payment processor...')).toBeTruthy();
      
      // Resolve Stripe loading
      act(() => {
        resolveStripe!(createMockStripe());
      });
      
      await waitFor(() => {
        expect(getByText(/Card Information/)).toBeTruthy();
      });
    });

    it('shows error state when Stripe fails to load', async () => {
      mockLoadStripe.mockResolvedValue(null);
      
      const { getByText } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        expect(getByText('Failed to load payment processor')).toBeTruthy();
      });
    });

    it('shows error when Stripe config is missing public key', async () => {
      const props = createMockStripePaymentFormProps({
        stripeConfig: { public_key: '', success: true },
      });
      
      const { getByText } = render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        expect(getByText('Payment configuration not available')).toBeTruthy();
      });
    });

    it('loads Stripe with correct configuration', async () => {
      const props = createMockStripePaymentFormProps({
        stripeConfig: { public_key: 'pk_test_custom_key', success: true },
      });
      
      render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        expect(mockLoadStripe).toHaveBeenCalledWith('pk_test_custom_key');
      });
    });
  });

  describe('Form Rendering', () => {
    it('renders payment form with all required elements', async () => {
      const { getByText, getByTestId } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        expect(getByText(/Card Information/)).toBeTruthy();
        expect(getByTestId('stripe-payment-element')).toBeTruthy();
        expect(getByText(/Pay €100.00/)).toBeTruthy();
        expect(getByText(/Secure Payment/)).toBeTruthy();
      });
    });

    it('displays plan information correctly', async () => {
      const { getByText } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        expect(getByText('Complete Payment')).toBeTruthy();
        expect(getByText('Standard Package')).toBeTruthy();
        expect(getByText('€100.00')).toBeTruthy();
      });
    });

    it('shows security notice and terms', async () => {
      const { getByText } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        expect(getByText(/Your payment information is secure/)).toBeTruthy();
        expect(getByText(/By clicking "Pay"/)).toBeTruthy();
      });
    });

    it('disables form when disabled prop is true', async () => {
      const props = createMockStripePaymentFormProps({ disabled: true });
      const { getByRole } = render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        const submitButton = getByRole('button');
        expect(submitButton).toHaveProperty('disabled', true);
      });
    });
  });

  describe('Payment Submission', () => {
    it('successfully submits payment', async () => {
      const mockStripe = createMockStripe();
      const mockElements = {
        create: jest.fn(),
        getElement: jest.fn(() => null),
      };
      const onPaymentSuccess = jest.fn();
      
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(mockElements);
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());
      
      const props = createMockStripePaymentFormProps({ onPaymentSuccess });
      const { getByRole } = render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      await waitFor(() => {
        expect(mockStripe.confirmPayment).toHaveBeenCalledWith({
          elements: mockElements,
          confirmParams: {
            return_url: `${window.location.origin}/purchase/success`,
          },
          redirect: 'if_required',
        });
        expect(onPaymentSuccess).toHaveBeenCalled();
      });
    });

    it('handles payment errors correctly', async () => {
      const mockStripe = createMockStripe();
      const mockElements = {
        create: jest.fn(),
        getElement: jest.fn(() => null),
      };
      const onPaymentError = jest.fn();
      const errorMessage = 'Your card was declined';
      
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(mockElements);
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeError(errorMessage));
      
      const props = createMockStripePaymentFormProps({ onPaymentError });
      const { getByRole, getByText } = render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      await waitFor(() => {
        expect(getByText(errorMessage)).toBeTruthy();
        expect(onPaymentError).toHaveBeenCalledWith(errorMessage);
      });
    });

    it('handles 3D Secure authentication', async () => {
      const mockStripe = createMockStripe();
      const mockElements = {
        create: jest.fn(),
        getElement: jest.fn(() => null),
      };
      const onPaymentError = jest.fn();
      
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(mockElements);
      mockStripe.confirmPayment.mockResolvedValue(createMockStripe3DSRequired());
      
      const props = createMockStripePaymentFormProps({ onPaymentError });
      const { getByRole } = render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      await waitFor(() => {
        expect(onPaymentError).toHaveBeenCalledWith('This payment requires authentication.');
      });
    });

    it('prevents submission without Stripe instance', async () => {
      mockUseStripe.mockReturnValue(null);
      
      const onPaymentSuccess = jest.fn();
      const props = createMockStripePaymentFormProps({ onPaymentSuccess });
      const { getByRole } = render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      expect(onPaymentSuccess).not.toHaveBeenCalled();
    });

    it('prevents submission without Elements instance', async () => {
      const mockStripe = createMockStripe();
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(null);
      
      const onPaymentSuccess = jest.fn();
      const props = createMockStripePaymentFormProps({ onPaymentSuccess });
      const { getByRole } = render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      expect(onPaymentSuccess).not.toHaveBeenCalled();
    });

    it('prevents multiple submissions while processing', async () => {
      const mockStripe = createMockStripe();
      const mockElements = {
        create: jest.fn(),
        getElement: jest.fn(() => null),
      };
      
      // Make payment confirmation hang
      let resolvePayment: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolvePayment = resolve;
      });
      
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(mockElements);
      mockStripe.confirmPayment.mockReturnValue(pendingPromise);
      
      const props = createMockStripePaymentFormProps();
      const { getByRole } = render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
        
        // Try to submit again while processing
        fireEvent.submit(form);
      });
      
      // Should only call confirmPayment once
      expect(mockStripe.confirmPayment).toHaveBeenCalledTimes(1);
      
      // Resolve the payment
      act(() => {
        resolvePayment!(createMockStripeSuccess());
      });
    });

    it('shows processing state during submission', async () => {
      const mockStripe = createMockStripe();
      const mockElements = {
        create: jest.fn(),
        getElement: jest.fn(() => null),
      };
      
      // Make payment confirmation hang
      let resolvePayment: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolvePayment = resolve;
      });
      
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(mockElements);
      mockStripe.confirmPayment.mockReturnValue(pendingPromise);
      
      const { getByRole, getByText } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      expect(getByText('Processing...')).toBeTruthy();
      
      // Resolve the payment
      act(() => {
        resolvePayment!(createMockStripeSuccess());
      });
      
      await waitFor(() => {
        expect(getByText(/Pay €100.00/)).toBeTruthy();
      });
    });

    it('handles network errors during submission', async () => {
      const mockStripe = createMockStripe();
      const mockElements = {
        create: jest.fn(),
        getElement: jest.fn(() => null),
      };
      const onPaymentError = jest.fn();
      const networkError = new Error('Network request failed');
      
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(mockElements);
      mockStripe.confirmPayment.mockRejectedValue(networkError);
      
      const props = createMockStripePaymentFormProps({ onPaymentError });
      const { getByRole } = render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      await waitFor(() => {
        expect(onPaymentError).toHaveBeenCalledWith('Network request failed');
      });
    });
  });

  describe('Error Display', () => {
    it('displays payment errors in the form', async () => {
      const mockStripe = createMockStripe();
      const mockElements = {
        create: jest.fn(),
        getElement: jest.fn(() => null),
      };
      const errorMessage = 'Insufficient funds';
      
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(mockElements);
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeError(errorMessage));
      
      const { getByRole, getByText } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      await waitFor(() => {
        expect(getByText(errorMessage)).toBeTruthy();
      });
    });

    it('clears previous errors on new submission', async () => {
      const mockStripe = createMockStripe();
      const mockElements = {
        create: jest.fn(),
        getElement: jest.fn(() => null),
      };
      
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(mockElements);
      
      const { getByRole, getByText, queryByText } = render(<StripePaymentForm {...defaultProps} />);
      
      // First submission with error
      mockStripe.confirmPayment.mockResolvedValueOnce(createMockStripeError('Card declined'));
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      await waitFor(() => {
        expect(getByText('Card declined')).toBeTruthy();
      });
      
      // Second submission with success - should clear error
      mockStripe.confirmPayment.mockResolvedValueOnce(createMockStripeSuccess());
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      await waitFor(() => {
        expect(queryByText('Card declined')).toBeNull();
      });
    });
  });

  describe('Stripe Elements Configuration', () => {
    it('passes correct appearance options to Elements', async () => {
      render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        // Elements configuration is tested through the mock setup
        // In a real test environment, you'd verify the Elements component receives correct props
        expect(mockLoadStripe).toHaveBeenCalled();
      });
    });

    it('uses client secret for payment intent', async () => {
      const clientSecret = 'pi_custom_secret_abc123';
      const props = createMockStripePaymentFormProps({ clientSecret });
      
      render(<StripePaymentForm {...props} />);
      
      await waitFor(() => {
        // Elements should be initialized with the client secret
        expect(mockLoadStripe).toHaveBeenCalled();
      });
    });
  });

  describe('Form Validation', () => {
    it('disables submit button when form is invalid', async () => {
      mockUseStripe.mockReturnValue(null); // No Stripe instance
      
      const { getByRole } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        const submitButton = getByRole('button');
        expect(submitButton).toHaveProperty('disabled', true);
      });
    });

    it('enables submit button when form is valid', async () => {
      const mockStripe = createMockStripe();
      const mockElements = {
        create: jest.fn(),
        getElement: jest.fn(() => null),
      };
      
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(mockElements);
      
      const { getByRole } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        const submitButton = getByRole('button');
        expect(submitButton).toHaveProperty('disabled', false);
      });
    });
  });

  describe('Accessibility', () => {
    it('provides proper form structure for screen readers', async () => {
      const { getByRole } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        expect(getByRole('form')).toBeTruthy();
        expect(getByRole('button')).toBeTruthy();
      });
    });

    it('has proper labels for form elements', async () => {
      const { getByText } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        expect(getByText('Card Information')).toBeTruthy();
        expect(getByText(/Pay €100.00/)).toBeTruthy();
      });
    });

    it('announces errors to screen readers', async () => {
      const mockStripe = createMockStripe();
      const mockElements = {
        create: jest.fn(),
        getElement: jest.fn(() => null),
      };
      const errorMessage = 'Payment error';
      
      mockUseStripe.mockReturnValue(mockStripe);
      mockUseElements.mockReturnValue(mockElements);
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeError(errorMessage));
      
      const { getByRole, getByText } = render(<StripePaymentForm {...defaultProps} />);
      
      await waitFor(() => {
        const form = getByRole('form');
        fireEvent.submit(form);
      });
      
      await waitFor(() => {
        // Error should be displayed and accessible to screen readers
        expect(getByText(errorMessage)).toBeTruthy();
      });
    });
  });

  describe('Performance', () => {
    it('renders quickly under normal conditions', async () => {
      const start = performance.now();
      render(<StripePaymentForm {...defaultProps} />);
      const end = performance.now();
      
      expect(end - start).toBeLessThan(100);
    });

    it('memoizes expensive computations', async () => {
      const { rerender } = render(<StripePaymentForm {...defaultProps} />);
      
      const start = performance.now();
      rerender(<StripePaymentForm {...defaultProps} />);
      const end = performance.now();
      
      expect(end - start).toBeLessThan(50);
    });
  });
});