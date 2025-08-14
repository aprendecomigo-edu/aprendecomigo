/**
 * Student Dashboard Test Utilities
 *
 * Comprehensive test utilities for testing student dashboard components
 * including mock data factories, API mocks, and WebSocket connection mocks.
 */

import React from 'react';

import type {
  StudentBalanceResponse,
  PaginatedTransactionHistory,
  PaginatedPurchaseHistory,
  DashboardState,
  TopUpPackage,
  TransactionHistoryItem,
  PurchaseHistoryItem,
  UseStudentBalanceResult,
  TransactionFilterOptions,
  PurchaseFilterOptions,
} from '@/types/purchase';

// Define UseStudentDashboardResult since it's not exported from the types
interface UseStudentDashboardResult {
  state: DashboardState;
  balance: StudentBalanceResponse | null;
  balanceLoading: boolean;
  balanceError: string | null;
  transactions: PaginatedTransactionHistory | null;
  transactionsLoading: boolean;
  transactionsError: string | null;
  purchases: PaginatedPurchaseHistory | null;
  purchasesLoading: boolean;
  purchasesError: string | null;
  actions: {
    setActiveTab: (tab: DashboardState['activeTab']) => void;
    setTransactionFilters: (filters: Partial<TransactionFilterOptions>) => void;
    setPurchaseFilters: (filters: Partial<PurchaseFilterOptions>) => void;
    setSearchQuery: (query: string) => void;
    refreshBalance: () => Promise<void>;
    refreshTransactions: (page?: number) => Promise<void>;
    refreshPurchases: (page?: number) => Promise<void>;
    refreshAll: () => Promise<void>;
    loadMoreTransactions: () => Promise<void>;
    loadMorePurchases: () => Promise<void>;
  };
}

// Student Test Data Pattern as specified in the issue
export const StudentTestData = {
  profile: {
    id: '123',
    name: 'Test Student',
    email: 'student@test.com',
  },
  balance: {
    current: 5000,
    currency: 'BRL',
    lastUpdated: new Date(),
  },
  transactions: [
    {
      id: '1',
      type: 'top-up' as const,
      amount: 2000,
      date: '2025-01-01',
    },
    {
      id: '2',
      type: 'usage' as const,
      amount: -500,
      date: '2025-01-02',
    },
  ],
  analytics: {
    sessionsThisWeek: 5,
    totalHours: 10,
    streak: 3,
  },
};

// Mock student balance data factory
export const createMockStudentBalance = (
  overrides: Partial<StudentBalanceResponse> = {}
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

// Low balance scenario
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

// Critical balance scenario (almost empty)
export const createMockCriticalBalanceStudent = (): StudentBalanceResponse =>
  createMockStudentBalance({
    balance_summary: {
      hours_purchased: '5.0',
      hours_consumed: '4.8',
      remaining_hours: '0.2',
      balance_amount: '2.00',
    },
    package_status: {
      active_packages: [
        {
          transaction_id: 1,
          plan_name: 'Starter Package',
          hours_included: '5.0',
          hours_consumed: '4.8',
          hours_remaining: '0.2',
          expires_at: '2024-04-01T00:00:00Z',
          days_until_expiry: 1,
          is_expired: false,
        },
      ],
      expired_packages: [],
    },
    upcoming_expirations: [
      {
        transaction_id: 1,
        plan_name: 'Starter Package',
        hours_remaining: '0.2',
        expires_at: '2024-04-01T00:00:00Z',
        days_until_expiry: 1,
      },
    ],
  });

// Empty balance scenario
export const createMockEmptyBalanceStudent = (): StudentBalanceResponse =>
  createMockStudentBalance({
    balance_summary: {
      hours_purchased: '0.0',
      hours_consumed: '0.0',
      remaining_hours: '0.0',
      balance_amount: '0.00',
    },
    package_status: {
      active_packages: [],
      expired_packages: [],
    },
    upcoming_expirations: [],
  });

// Mock transaction history item factory
export const createMockTransactionItem = (
  overrides: Partial<TransactionHistoryItem> = {}
): TransactionHistoryItem => ({
  id: 1,
  transaction_id: 'txn_123',
  transaction_type: 'purchase',
  transaction_type_display: 'Package Purchase',
  amount: '100.00',
  hours_changed: '10.0',
  payment_status: 'succeeded',
  payment_status_display: 'Completed',
  plan_name: 'Standard Package',
  description: 'Standard Package - 10 hours',
  created_at: '2024-01-01T10:00:00Z',
  processed_at: '2024-01-01T10:05:00Z',
  ...overrides,
});

// Mock paginated transaction history
export const createMockTransactionHistory = (
  overrides: Partial<PaginatedTransactionHistory> = {}
): PaginatedTransactionHistory => ({
  count: 25,
  next: 'http://api.example.com/transactions?page=2',
  previous: null,
  results: [
    createMockTransactionItem({
      id: 1,
      transaction_id: 'txn_1',
      transaction_type: 'purchase',
      transaction_type_display: 'Package Purchase',
      amount: '100.00',
      hours_changed: '10.0',
      description: 'Standard Package - 10 hours',
      created_at: '2024-01-15T10:00:00Z',
    }),
    createMockTransactionItem({
      id: 2,
      transaction_id: 'txn_2',
      transaction_type: 'consumption',
      transaction_type_display: 'Session Usage',
      amount: '0.00',
      hours_changed: '-1.0',
      description: 'Tutoring session with Maria Silva',
      created_at: '2024-01-14T15:30:00Z',
    }),
    createMockTransactionItem({
      id: 3,
      transaction_id: 'txn_3',
      transaction_type: 'refund',
      transaction_type_display: 'Refund',
      amount: '50.00',
      hours_changed: '5.0',
      payment_status: 'refunded',
      payment_status_display: 'Refunded',
      description: 'Partial refund - cancelled package',
      created_at: '2024-01-10T09:15:00Z',
    }),
  ],
  ...overrides,
});

// Mock purchase history item factory
export const createMockPurchaseItem = (
  overrides: Partial<PurchaseHistoryItem> = {}
): PurchaseHistoryItem => ({
  id: 1,
  transaction_id: 'txn_123',
  plan_name: 'Standard Package',
  plan_type: 'package',
  hours_included: '10.0',
  hours_consumed: '3.0',
  hours_remaining: '7.0',
  price_paid: '100.00',
  currency: 'EUR',
  purchase_date: '2024-01-01T10:00:00Z',
  expires_at: '2024-04-01T00:00:00Z',
  days_until_expiry: 30,
  is_expired: false,
  status: 'active',
  payment_method: {
    type: 'card',
    brand: 'visa',
    last4: '4242',
  },
  consumption_details: [
    {
      session_date: '2024-01-05T14:00:00Z',
      teacher_name: 'Maria Silva',
      hours_consumed: '1.0',
      subject: 'Mathematics',
    },
    {
      session_date: '2024-01-08T16:00:00Z',
      teacher_name: 'João Santos',
      hours_consumed: '2.0',
      subject: 'Physics',
    },
  ],
  ...overrides,
});

// Mock paginated purchase history
export const createMockPurchaseHistory = (
  overrides: Partial<PaginatedPurchaseHistory> = {}
): PaginatedPurchaseHistory => ({
  count: 12,
  next: null,
  previous: null,
  results: [
    createMockPurchaseItem({
      id: 1,
      transaction_id: 'txn_recent',
      plan_name: 'Premium Package',
      hours_included: '20.0',
      hours_consumed: '5.0',
      hours_remaining: '15.0',
      purchase_date: '2024-01-15T10:00:00Z',
      expires_at: '2024-04-15T00:00:00Z',
      days_until_expiry: 45,
    }),
    createMockPurchaseItem({
      id: 2,
      transaction_id: 'txn_older',
      plan_name: 'Standard Package',
      hours_included: '10.0',
      hours_consumed: '10.0',
      hours_remaining: '0.0',
      purchase_date: '2023-12-01T10:00:00Z',
      expires_at: '2024-03-01T00:00:00Z',
      days_until_expiry: -10,
      is_expired: true,
      status: 'expired',
    }),
  ],
  ...overrides,
});

// Mock top-up package factory
export const createMockTopUpPackage = (overrides: Partial<TopUpPackage> = {}): TopUpPackage => ({
  id: 1,
  name: '5 Hour Package',
  hours: 5,
  price_eur: '60.00',
  price_per_hour: '12.00',
  discount_percentage: undefined,
  is_popular: false,
  display_order: 1,
  ...overrides,
});

// Mock top-up packages
export const createMockTopUpPackages = (): TopUpPackage[] => [
  createMockTopUpPackage({
    id: 1,
    name: '5 Hour Quick Top-Up',
    hours: 5,
    price_eur: '60.00',
    price_per_hour: '12.00',
    display_order: 1,
  }),
  createMockTopUpPackage({
    id: 2,
    name: '10 Hour Standard',
    hours: 10,
    price_eur: '100.00',
    price_per_hour: '10.00',
    discount_percentage: 17,
    is_popular: true,
    display_order: 2,
  }),
  createMockTopUpPackage({
    id: 3,
    name: '20 Hour Value Pack',
    hours: 20,
    price_eur: '180.00',
    price_per_hour: '9.00',
    discount_percentage: 25,
    display_order: 3,
  }),
];

// Mock dashboard state factory
export const createMockDashboardState = (
  overrides: Partial<DashboardState> = {}
): DashboardState => ({
  activeTab: 'overview',
  transactionFilters: {
    payment_status: undefined,
    transaction_type: undefined,
    date_from: undefined,
    date_to: undefined,
  },
  purchaseFilters: {
    active_only: false,
    include_consumption: true,
    date_from: undefined,
    date_to: undefined,
  },
  searchQuery: '',
  ...overrides,
});

// Mock useStudentBalance hook result
export const createMockUseStudentBalance = (
  overrides: Partial<UseStudentBalanceResult> = {}
): UseStudentBalanceResult => ({
  balance: createMockStudentBalance(),
  loading: false,
  error: null,
  refetch: jest.fn().mockResolvedValue(undefined),
  ...overrides,
});

// Mock useStudentDashboard hook result
export const createMockUseStudentDashboard = (
  overrides: Partial<UseStudentDashboardResult> = {}
): UseStudentDashboardResult => ({
  state: createMockDashboardState(),
  balance: createMockStudentBalance(),
  balanceLoading: false,
  balanceError: null,
  transactions: createMockTransactionHistory(),
  transactionsLoading: false,
  transactionsError: null,
  purchases: createMockPurchaseHistory(),
  purchasesLoading: false,
  purchasesError: null,
  actions: {
    setActiveTab: jest.fn(),
    setTransactionFilters: jest.fn(),
    setPurchaseFilters: jest.fn(),
    setSearchQuery: jest.fn(),
    refreshBalance: jest.fn().mockResolvedValue(undefined),
    refreshTransactions: jest.fn().mockResolvedValue(undefined),
    refreshPurchases: jest.fn().mockResolvedValue(undefined),
    refreshAll: jest.fn().mockResolvedValue(undefined),
    loadMoreTransactions: jest.fn().mockResolvedValue(undefined),
    loadMorePurchases: jest.fn().mockResolvedValue(undefined),
  },
  ...overrides,
});

// API Mock utilities
export const mockStudentApiCalls = {
  getStudentBalance: jest.fn(),
  getTransactionHistory: jest.fn(),
  getPurchaseHistory: jest.fn(),
  getTopUpPackages: jest.fn(),
  quickTopUp: jest.fn(),
};

export const mockSuccessfulStudentApi = () => {
  mockStudentApiCalls.getStudentBalance.mockResolvedValue(createMockStudentBalance());
  mockStudentApiCalls.getTransactionHistory.mockResolvedValue(createMockTransactionHistory());
  mockStudentApiCalls.getPurchaseHistory.mockResolvedValue(createMockPurchaseHistory());
  mockStudentApiCalls.getTopUpPackages.mockResolvedValue(createMockTopUpPackages());
  mockStudentApiCalls.quickTopUp.mockResolvedValue({
    success: true,
    message: 'Purchase completed successfully',
    transaction_id: 'txn_success_123',
  });

  return mockStudentApiCalls;
};

export const mockFailedStudentApi = () => {
  const error = new Error('Failed to load student data');
  mockStudentApiCalls.getStudentBalance.mockRejectedValue(error);
  mockStudentApiCalls.getTransactionHistory.mockRejectedValue(error);
  mockStudentApiCalls.getPurchaseHistory.mockRejectedValue(error);
  mockStudentApiCalls.getTopUpPackages.mockRejectedValue(error);
  mockStudentApiCalls.quickTopUp.mockRejectedValue(error);

  return mockStudentApiCalls;
};

// WebSocket mock for real-time balance updates
export const createMockStudentWebSocket = () => {
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

  global.WebSocket = jest.fn(() => mockWs) as any;
  return mockWs;
};

// Balance update WebSocket message factory
export const createBalanceUpdateWebSocketMessage = (
  balance: Partial<StudentBalanceResponse> = {}
) => ({
  type: 'balance_update',
  data: {
    ...createMockStudentBalance(),
    ...balance,
  },
});

// Transaction update WebSocket message factory
export const createTransactionUpdateWebSocketMessage = (
  transaction: Partial<TransactionHistoryItem> = {}
) => ({
  type: 'transaction_update',
  data: {
    ...createMockTransactionItem(),
    ...transaction,
  },
});

// Analytics mock data
export const createMockAnalyticsData = (overrides = {}) => ({
  weekly_sessions: 5,
  total_hours_this_month: 18.5,
  learning_streak: 7,
  favorite_subjects: ['Mathematics', 'Physics', 'Chemistry'],
  performance_trends: {
    sessions_per_week: [3, 4, 5, 4, 6],
    hours_per_week: [2.5, 3.0, 4.5, 3.5, 5.0],
    weeks: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'],
  },
  teacher_ratings: {
    average_rating: 4.8,
    total_reviews: 12,
  },
  ...overrides,
});

// Test helper functions
export const simulateBalanceUpdate = (mockWs: any, newBalance: Partial<StudentBalanceResponse>) => {
  const message = createBalanceUpdateWebSocketMessage(newBalance);

  // Simulate WebSocket message
  const messageHandler = mockWs.addEventListener.mock.calls.find(
    call => call[0] === 'message'
  )?.[1];

  if (messageHandler) {
    messageHandler({ data: JSON.stringify(message) });
  }
};

export const simulateTransactionUpdate = (
  mockWs: any,
  transaction: Partial<TransactionHistoryItem>
) => {
  const message = createTransactionUpdateWebSocketMessage(transaction);

  const messageHandler = mockWs.addEventListener.mock.calls.find(
    call => call[0] === 'message'
  )?.[1];

  if (messageHandler) {
    messageHandler({ data: JSON.stringify(message) });
  }
};

// Performance test utilities
export const measureStudentDashboardRender = (renderFn: () => void) => {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
};

export const expectFastStudentRender = (renderTime: number, maxMs = 100) => {
  expect(renderTime).toBeLessThan(maxMs);
};

// Accessibility test helpers for student components
export const expectStudentDashboardAccessibility = (getByRole: any) => {
  expect(getByRole('tablist')).toBeTruthy();
  expect(getByRole('tab', { name: /overview/i })).toBeTruthy();
  expect(getByRole('tab', { name: /transactions/i })).toBeTruthy();
  expect(getByRole('tab', { name: /purchases/i })).toBeTruthy();
};

export const expectBalanceStatusAccessibility = (container: any) => {
  // Check for proper ARIA labels on progress bars and status indicators
  const progressBars = container.querySelectorAll('[role="progressbar"]');
  expect(progressBars.length).toBeGreaterThan(0);
};

// Cleanup utilities
export const cleanupStudentMocks = () => {
  jest.clearAllMocks();
  delete (global as any).WebSocket;

  // Reset API mocks
  Object.values(mockStudentApiCalls).forEach(mock => {
    if (typeof mock === 'function' && 'mockReset' in mock) {
      mock.mockReset();
    }
  });
};

// Component prop factories for consistent testing
export const createMockStudentDashboardProps = (overrides = {}) => ({
  email: 'student@test.com',
  className: '',
  ...overrides,
});

export const createMockBalanceStatusBarProps = (overrides = {}) => ({
  remainingHours: 10.5,
  totalHours: 15.0,
  daysUntilExpiry: 30,
  showDetails: true,
  className: '',
  ...overrides,
});

export const createMockQuickTopUpPanelProps = (overrides = {}) => ({
  email: 'student@test.com',
  onTopUpSuccess: jest.fn(),
  onTopUpError: jest.fn(),
  isModal: false,
  onClose: jest.fn(),
  ...overrides,
});

// Edge case scenarios
export const createEdgeCaseBalanceScenarios = () => ({
  zeroBigBalance: createMockStudentBalance({
    balance_summary: {
      hours_purchased: '0.0',
      hours_consumed: '0.0',
      remaining_hours: '0.0',
      balance_amount: '0.00',
    },
    package_status: { active_packages: [], expired_packages: [] },
    upcoming_expirations: [],
  }),

  expiredPackages: createMockStudentBalance({
    package_status: {
      active_packages: [],
      expired_packages: [
        {
          transaction_id: 1,
          plan_name: 'Expired Package',
          hours_included: '10.0',
          hours_consumed: '8.0',
          hours_remaining: '2.0',
          expires_at: '2023-12-01T00:00:00Z',
          days_until_expiry: -30,
          is_expired: true,
        },
      ],
    },
    upcoming_expirations: [],
  }),

  multipleActivePackages: createMockStudentBalance({
    package_status: {
      active_packages: [
        {
          transaction_id: 1,
          plan_name: 'Package A',
          hours_included: '10.0',
          hours_consumed: '3.0',
          hours_remaining: '7.0',
          expires_at: '2024-04-01T00:00:00Z',
          days_until_expiry: 30,
          is_expired: false,
        },
        {
          transaction_id: 2,
          plan_name: 'Package B',
          hours_included: '5.0',
          hours_consumed: '1.0',
          hours_remaining: '4.0',
          expires_at: '2024-05-01T00:00:00Z',
          days_until_expiry: 60,
          is_expired: false,
        },
      ],
      expired_packages: [],
    },
  }),
});
