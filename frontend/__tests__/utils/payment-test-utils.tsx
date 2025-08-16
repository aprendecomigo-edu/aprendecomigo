/**
 * Payment System Test Utilities
 *
 * Comprehensive test utilities for testing payment-related components
 * including Stripe mocks, API response factories, and WebSocket mocks.
 */

import React from 'react';

import type {
  PricingPlan,
  StudentBalanceResponse,
  PaymentMethod,
  StripeConfig,
  PurchaseInitiationResponse,
  PurchaseFlowState,
  UsePurchaseFlowResult,
} from '@/types/purchase';

// Mock Stripe instance
export const createMockStripe = () => ({
  elements: jest.fn(() => ({
    create: jest.fn(() => ({
      mount: jest.fn(),
      unmount: jest.fn(),
      update: jest.fn(),
      on: jest.fn(),
    })),
    getElement: jest.fn(() => null),
  })),
  confirmPayment: jest.fn(),
  retrievePaymentIntent: jest.fn(),
});

// Mock Stripe elements
export const createMockElements = () => ({
  create: jest.fn(() => ({
    mount: jest.fn(),
    unmount: jest.fn(),
    update: jest.fn(),
    on: jest.fn(),
  })),
  getElement: jest.fn(() => null),
});

// Test data factories
export const createMockPricingPlan = (overrides: Partial<PricingPlan> = {}): PricingPlan => ({
  id: 1,
  name: 'Standard Package',
  description: 'Perfect for regular tutoring sessions',
  plan_type: 'package',
  plan_type_display: 'Package',
  hours_included: '10.0',
  price_eur: '100.00',
  price_per_hour: '10.00',
  validity_days: 90,
  is_active: true,
  display_order: 1,
  ...overrides,
});

export const createMockPricingPlans = (): PricingPlan[] => [
  createMockPricingPlan({
    id: 1,
    name: 'Starter Package',
    hours_included: '5.0',
    price_eur: '60.00',
    price_per_hour: '12.00',
    display_order: 1,
  }),
  createMockPricingPlan({
    id: 2,
    name: 'Standard Package',
    hours_included: '10.0',
    price_eur: '100.00',
    price_per_hour: '10.00',
    display_order: 2,
  }),
  createMockPricingPlan({
    id: 3,
    name: 'Premium Package',
    hours_included: '20.0',
    price_eur: '180.00',
    price_per_hour: '9.00',
    display_order: 3,
  }),
];

export const createMockStudentBalance = (
  overrides: Partial<StudentBalanceResponse> = {},
): StudentBalanceResponse => ({
  student_info: {
    id: 1,
    name: 'John Doe',
    email: 'john@example.com',
  },
  balance_summary: {
    hours_purchased: '15.0',
    hours_consumed: '5.0',
    remaining_hours: '10.0',
    balance_amount: '100.00',
  },
  package_status: {
    active_packages: [
      {
        transaction_id: 1,
        plan_name: 'Standard Package',
        hours_included: '10.0',
        hours_consumed: '3.0',
        hours_remaining: '7.0',
        expires_at: '2024-04-01T00:00:00Z',
        days_until_expiry: 30,
        is_expired: false,
      },
    ],
    expired_packages: [],
  },
  upcoming_expirations: [
    {
      transaction_id: 1,
      plan_name: 'Standard Package',
      hours_remaining: '7.0',
      expires_at: '2024-04-01T00:00:00Z',
      days_until_expiry: 30,
    },
  ],
  ...overrides,
});

export const createMockLowBalanceStudent = (): StudentBalanceResponse =>
  createMockStudentBalance({
    balance_summary: {
      hours_purchased: '10.0',
      hours_consumed: '8.5',
      remaining_hours: '1.5',
      balance_amount: '15.00',
    },
    package_status: {
      active_packages: [
        {
          transaction_id: 1,
          plan_name: 'Standard Package',
          hours_included: '10.0',
          hours_consumed: '8.5',
          hours_remaining: '1.5',
          expires_at: '2024-04-01T00:00:00Z',
          days_until_expiry: 5,
          is_expired: false,
        },
      ],
      expired_packages: [],
    },
    upcoming_expirations: [
      {
        transaction_id: 1,
        plan_name: 'Standard Package',
        hours_remaining: '1.5',
        expires_at: '2024-04-01T00:00:00Z',
        days_until_expiry: 5,
      },
    ],
  });

export const createMockPaymentMethod = (overrides: Partial<PaymentMethod> = {}): PaymentMethod => ({
  id: 'pm_test_123',
  type: 'card',
  card: {
    brand: 'visa',
    last4: '4242',
    exp_month: 12,
    exp_year: 2025,
    funding: 'credit',
  },
  billing_details: {
    name: 'John Doe',
    email: 'john@example.com',
  },
  is_default: true,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

export const createMockPaymentMethods = (): PaymentMethod[] => [
  createMockPaymentMethod({
    id: 'pm_test_123',
    card: { brand: 'visa', last4: '4242', exp_month: 12, exp_year: 2025, funding: 'credit' },
    is_default: true,
  }),
  createMockPaymentMethod({
    id: 'pm_test_456',
    card: { brand: 'mastercard', last4: '5555', exp_month: 8, exp_year: 2026, funding: 'debit' },
    is_default: false,
  }),
];

export const createMockStripeConfig = (): StripeConfig => ({
  public_key: 'pk_test_123456789',
  success: true,
});

export const createMockPurchaseInitiationResponse = (
  overrides: Partial<PurchaseInitiationResponse> = {},
): PurchaseInitiationResponse => ({
  success: true,
  client_secret: 'pi_test_123_secret_abc',
  transaction_id: 1,
  payment_intent_id: 'pi_test_123',
  plan_details: createMockPricingPlan(),
  message: 'Purchase initiated successfully',
  ...overrides,
});

export const createMockPurchaseFlowState = (
  overrides: Partial<PurchaseFlowState> = {},
): PurchaseFlowState => ({
  step: 'plan-selection',
  formData: {
    selectedPlan: null,
    studentName: '',
    studentEmail: '',
    isProcessing: false,
    errors: {},
  },
  stripeConfig: createMockStripeConfig(),
  paymentIntentSecret: null,
  transactionId: null,
  errorMessage: null,
  ...overrides,
});

// Mock API responses
export const mockSuccessfulPurchaseApi = () => {
  const mockApiClient = {
    getStripeConfig: jest.fn().mockResolvedValue(createMockStripeConfig()),
    initiatePurchase: jest.fn().mockResolvedValue(createMockPurchaseInitiationResponse()),
    getPricingPlans: jest.fn().mockResolvedValue(createMockPricingPlans()),
    getStudentBalance: jest.fn().mockResolvedValue(createMockStudentBalance()),
    getPaymentMethods: jest.fn().mockResolvedValue(createMockPaymentMethods()),
  };
  return mockApiClient;
};

export const mockFailedPurchaseApi = () => {
  const mockApiClient = {
    getStripeConfig: jest.fn().mockRejectedValue(new Error('Failed to load Stripe config')),
    initiatePurchase: jest.fn().mockResolvedValue({
      success: false,
      message: 'Validation failed',
      field_errors: {
        'student_info.email': ['Please enter a valid email address'],
        'student_info.name': ['Name is required'],
      },
    }),
    getPricingPlans: jest.fn().mockRejectedValue(new Error('Failed to load pricing plans')),
    getStudentBalance: jest.fn().mockRejectedValue(new Error('Failed to load balance')),
    getPaymentMethods: jest.fn().mockRejectedValue(new Error('Failed to load payment methods')),
  };
  return mockApiClient;
};

// Stripe test card numbers
export const STRIPE_TEST_CARDS = {
  VALID: {
    VISA: '4242424242424242',
    VISA_DEBIT: '4000056655665556',
    MASTERCARD: '5555555555554444',
    AMEX: '378282246310005',
  },
  DECLINED: {
    GENERIC: '4000000000000002',
    INSUFFICIENT_FUNDS: '4000000000009995',
    LOST_CARD: '4000000000009987',
    STOLEN_CARD: '4000000000009979',
  },
  REQUIRE_3DS: '4000002500003155',
  EXPIRE_IMMEDIATELY: '4000000000000069',
};

// Mock Stripe payment outcomes
export const createMockStripeSuccess = () => ({
  error: null,
  paymentIntent: {
    id: 'pi_test_123',
    status: 'succeeded',
  },
});

export const createMockStripeError = (message = 'Your card was declined.') => ({
  error: {
    type: 'card_error',
    code: 'card_declined',
    message,
  },
  paymentIntent: null,
});

export const createMockStripe3DSRequired = () => ({
  error: {
    type: 'card_error',
    code: 'authentication_required',
    message: 'This payment requires authentication.',
  },
  paymentIntent: {
    id: 'pi_test_123',
    status: 'requires_action',
  },
});

// WebSocket mock utilities
export const createMockWebSocket = () => {
  const mockWs = {
    send: jest.fn(),
    close: jest.fn(),
    readyState: 1, // OPEN
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    onopen: null,
    onclose: null,
    onerror: null,
    onmessage: null,
  };

  // Mock WebSocket constructor
  global.WebSocket = jest.fn(() => mockWs) as any;

  return mockWs;
};

// Balance update WebSocket message factory
export const createBalanceUpdateMessage = (balance: Partial<StudentBalanceResponse> = {}) => ({
  type: 'balance_update',
  data: {
    ...createMockStudentBalance(),
    ...balance,
  },
});

export const createPaymentStatusMessage = (status: 'succeeded' | 'failed', transactionId = 1) => ({
  type: 'payment_status',
  data: {
    transaction_id: transactionId,
    status,
    message: status === 'succeeded' ? 'Payment completed successfully' : 'Payment failed',
  },
});

// Form validation test utilities
export const VALID_TEST_DATA = {
  studentName: 'John Doe',
  studentEmail: 'john@example.com',
  cardNumber: STRIPE_TEST_CARDS.VALID.VISA,
  cvv: '123',
  expiry: '12/25',
};

export const INVALID_TEST_DATA = {
  studentName: '', // Too short
  studentEmail: 'invalid-email', // Invalid format
  cardNumber: '1234', // Too short
  cvv: '12', // Too short
  expiry: '13/20', // Invalid month/past year
};

// Mock usePurchaseFlow hook
export const createMockUsePurchaseFlow = (
  overrides: Partial<UsePurchaseFlowResult> = {},
): UsePurchaseFlowResult => ({
  state: createMockPurchaseFlowState(),
  actions: {
    selectPlan: jest.fn(),
    updateStudentInfo: jest.fn(),
    initiatePurchase: jest.fn().mockResolvedValue(undefined),
    confirmPayment: jest.fn().mockResolvedValue(undefined),
    resetFlow: jest.fn(),
    setError: jest.fn(),
  },
  isLoading: false,
  canProceed: false,
  ...overrides,
});

// Test helper functions
export const waitForStripeToLoad = () => new Promise(resolve => setTimeout(resolve, 100));

export const simulateStripeCardInput = (element: any, cardNumber: string) => {
  element.on.mock.calls.forEach(([event, handler]) => {
    if (event === 'change') {
      handler({
        complete: cardNumber === STRIPE_TEST_CARDS.VALID.VISA,
        error:
          cardNumber === STRIPE_TEST_CARDS.DECLINED.GENERIC
            ? { message: 'Your card was declined.' }
            : null,
      });
    }
  });
};

export const simulatePaymentSubmission = async (stripe: any, shouldSucceed = true) => {
  if (shouldSucceed) {
    stripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());
  } else {
    stripe.confirmPayment.mockResolvedValue(createMockStripeError());
  }
};

// Error scenario test data
export const NETWORK_ERROR = new Error('Network request failed');
export const VALIDATION_ERROR = new Error('Validation failed');
export const STRIPE_ERROR = new Error('Stripe initialization failed');

// Performance test utilities
export const measureRenderTime = (renderFn: () => void) => {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
};

export const expectFastRender = (renderTime: number, maxMs = 100) => {
  expect(renderTime).toBeLessThan(maxMs);
};

// Accessibility test helpers
export const expectPaymentFormAccessibility = (getByRole: any) => {
  expect(getByRole('form')).toBeTruthy();
  expect(getByRole('textbox', { name: /name/i })).toBeTruthy();
  expect(getByRole('textbox', { name: /email/i })).toBeTruthy();
  expect(getByRole('button', { name: /pay/i })).toBeTruthy();
};

// Component prop factories
export const createMockPurchaseFlowProps = (overrides = {}) => ({
  onPurchaseComplete: jest.fn(),
  onCancel: jest.fn(),
  className: '',
  ...overrides,
});

export const createMockStripePaymentFormProps = (overrides = {}) => ({
  stripeConfig: createMockStripeConfig(),
  clientSecret: 'pi_test_123_secret_abc',
  selectedPlan: createMockPricingPlan(),
  onPaymentSuccess: jest.fn(),
  onPaymentError: jest.fn(),
  disabled: false,
  className: '',
  ...overrides,
});

export const createMockStudentBalanceCardProps = (overrides = {}) => ({
  email: 'john@example.com',
  onRefresh: jest.fn(),
  className: '',
  showStudentInfo: true,
  showStatusBar: true,
  compact: false,
  ...overrides,
});

// Integration test utilities
export const simulateCompleteePurchaseFlow = async (
  getByText: any,
  getByPlaceholderText: any,
  fireEvent: any,
  waitFor: any,
) => {
  // Step 1: Select a plan
  fireEvent.press(getByText('Standard Package'));
  await waitFor(() => expect(getByText('Student Information')).toBeTruthy());

  // Step 2: Fill in student information
  fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
  fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
  fireEvent.press(getByText('Continue to Payment'));
  await waitFor(() => expect(getByText('Payment')).toBeTruthy());

  // Step 3: Complete payment
  fireEvent.press(getByText(/pay/i));
  await waitFor(() => expect(getByText('Purchase Successful!')).toBeTruthy());
};

// Clean up utilities
export const cleanupMocks = () => {
  jest.clearAllMocks();
  delete (global as any).WebSocket;
};
