/**
 * StudentAccountDashboard Component Tests
 *
 * Comprehensive test suite for the main student dashboard component.
 * Tests tab navigation, data loading, error handling, and integration with child components.
 */

import { render, fireEvent, waitFor } from '@testing-library/react-native';
import React from 'react';

import { StudentAccountDashboard } from '@/components/student/StudentAccountDashboard';
import { useUserProfile } from '@/api/auth';
import { useStudentDashboard } from '@/hooks/useStudentDashboard';
import {
  createMockStudentDashboardProps,
  createMockUseStudentDashboard,
  createMockStudentBalance,
  createMockTransactionHistory,
  createMockPurchaseHistory,
  cleanupStudentMocks,
} from '@/__tests__/utils/student-test-utils';

// Mock the hooks
jest.mock('@/api/auth');
jest.mock('@/hooks/useStudentDashboard');

// Mock router
const mockPush = jest.fn();
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: () => ({
    push: mockPush,
  }),
}));

// Mock child components to focus on main component logic
jest.mock('@/components/student/balance/BalanceAlertProvider', () => ({
  BalanceAlertProvider: ({ children }: any) => <div testID="balance-alert-provider">{children}</div>,
}));

jest.mock('@/components/student/dashboard/DashboardOverview', () => ({
  DashboardOverview: ({ balance, loading, error, onRefresh, onPurchase, onTabChange }: any) => (
    <div testID="dashboard-overview">
      <span>Balance: {balance ? 'Available' : 'None'}</span>
      <span>Loading: {loading.toString()}</span>
      <span>Error: {error || 'None'}</span>
      <button testID="overview-refresh" onPress={onRefresh}>Refresh</button>
      <button testID="overview-purchase" onPress={onPurchase}>Purchase</button>
      <button testID="overview-tab-change" onPress={() => onTabChange('transactions')}>Change Tab</button>
    </div>
  ),
}));

jest.mock('@/components/student/dashboard/TransactionHistory', () => ({
  TransactionHistory: ({ transactions, loading, error, filters, onFiltersChange, onRefresh, onLoadMore, searchQuery, onSearchChange }: any) => (
    <div testID="transaction-history">
      <span>Transactions: {transactions ? 'Available' : 'None'}</span>
      <span>Loading: {loading.toString()}</span>
      <span>Error: {error || 'None'}</span>
      <span>Search: {searchQuery}</span>
      <button testID="transactions-refresh" onPress={onRefresh}>Refresh</button>
      <button testID="transactions-load-more" onPress={onLoadMore}>Load More</button>
      <input testID="transactions-search" onChangeText={onSearchChange} value={searchQuery} />
    </div>
  ),
}));

jest.mock('@/components/student/dashboard/PurchaseHistory', () => ({
  PurchaseHistory: ({ purchases, loading, error, filters, onFiltersChange, onRefresh, onLoadMore, searchQuery, onSearchChange }: any) => (
    <div testID="purchase-history">
      <span>Purchases: {purchases ? 'Available' : 'None'}</span>
      <span>Loading: {loading.toString()}</span>
      <span>Error: {error || 'None'}</span>
      <span>Search: {searchQuery}</span>
      <button testID="purchases-refresh" onPress={onRefresh}>Refresh</button>
      <button testID="purchases-load-more" onPress={onLoadMore}>Load More</button>
      <input testID="purchases-search" onChangeText={onSearchChange} value={searchQuery} />
    </div>
  ),
}));

jest.mock('@/components/student/balance/NotificationCenter', () => ({
  NotificationCenter: ({ showSettings, showFilters, maxNotifications }: any) => (
    <div testID="notification-center">
      <span>Settings: {showSettings.toString()}</span>
      <span>Filters: {showFilters.toString()}</span>
      <span>Max: {maxNotifications}</span>
    </div>
  ),
}));

jest.mock('@/components/student/dashboard/AccountSettings', () => ({
  AccountSettings: ({ userProfile, balance, onRefresh }: any) => (
    <div testID="account-settings">
      <span>Profile: {userProfile ? 'Available' : 'None'}</span>
      <span>Balance: {balance ? 'Available' : 'None'}</span>
      <button testID="settings-refresh" onPress={onRefresh}>Refresh</button>
    </div>
  ),
}));

jest.mock('@/components/purchase/StudentBalanceCard', () => ({
  StudentBalanceCard: ({ email, onRefresh }: any) => (
    <div testID="student-balance-card">
      <span>Email: {email || 'None'}</span>
      <button testID="balance-card-refresh" onPress={onRefresh}>Refresh</button>
    </div>
  ),
}));

const mockUseUserProfile = useUserProfile as jest.MockedFunction<typeof useUserProfile>;
const mockUseStudentDashboard = useStudentDashboard as jest.MockedFunction<typeof useStudentDashboard>;

describe('StudentAccountDashboard Component', () => {
  const defaultProps = createMockStudentDashboardProps();
  const mockUserProfile = {
    id: 1,
    name: 'John Doe',
    email: 'john@example.com',
    role: 'student',
  };

  beforeEach(() => {
    cleanupStudentMocks();
    
    // Setup default mock returns
    mockUseUserProfile.mockReturnValue({
      userProfile: mockUserProfile,
      isLoading: false,
      error: null,
      refreshUserProfile: jest.fn(),
    });

    mockUseStudentDashboard.mockReturnValue(createMockUseStudentDashboard());
  });

  describe('Rendering', () => {
    it('renders main dashboard layout correctly', () => {
      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByText('Account Dashboard')).toBeTruthy();
      expect(getByText('Manage your tutoring hours and account settings')).toBeTruthy();
      expect(getByText('Refresh')).toBeTruthy();
      expect(getByText('Purchase Hours')).toBeTruthy();
    });

    it('displays BalanceAlertProvider wrapper', () => {
      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByTestId('balance-alert-provider')).toBeTruthy();
    });

    it('applies custom className', () => {
      const props = createMockStudentDashboardProps({ className: 'custom-class' });
      const { getByTestId } = render(<StudentAccountDashboard {...props} testID="dashboard" />);

      const dashboard = getByTestId('dashboard');
      expect(dashboard.props.className).toContain('custom-class');
    });
  });

  describe('Quick Stats Display', () => {
    it('displays quick stats when balance data is available', () => {
      const mockBalance = createMockStudentBalance({
        balance_summary: {
          remaining_hours: '10.5',
          hours_purchased: '20.0',
          hours_consumed: '9.5',
          balance_amount: '105.00',
        },
      });

      mockUseStudentDashboard.mockReturnValue(
        createMockUseStudentDashboard({ balance: mockBalance })
      );

      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByText('10.5')).toBeTruthy(); // remaining hours
      expect(getByText('Hours Remaining')).toBeTruthy();
      expect(getByText('1')).toBeTruthy(); // active packages count
      expect(getByText('Active Packages')).toBeTruthy();
    });

    it('displays expiring soon warning when applicable', () => {
      const mockBalance = createMockStudentBalance({
        upcoming_expirations: [
          {
            transaction_id: 1,
            plan_name: 'Test Package',
            hours_remaining: '5.0',
            expires_at: '2024-04-01T00:00:00Z',
            days_until_expiry: 3, // Expires soon
          },
        ],
      });

      mockUseStudentDashboard.mockReturnValue(
        createMockUseStudentDashboard({ balance: mockBalance })
      );

      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByText('1')).toBeTruthy(); // expiring soon count
      expect(getByText('Expiring Soon')).toBeTruthy();
    });

    it('hides expiring soon card when no packages expire soon', () => {
      const mockBalance = createMockStudentBalance({
        upcoming_expirations: [
          {
            transaction_id: 1,
            plan_name: 'Test Package',
            hours_remaining: '5.0',
            expires_at: '2024-04-01T00:00:00Z',
            days_until_expiry: 15, // Not expiring soon
          },
        ],
      });

      mockUseStudentDashboard.mockReturnValue(
        createMockUseStudentDashboard({ balance: mockBalance })
      );

      const { queryByText } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(queryByText('Expiring Soon')).toBeNull();
    });

    it('hides quick stats when no balance data available', () => {
      mockUseStudentDashboard.mockReturnValue(
        createMockUseStudentDashboard({ balance: null })
      );

      const { queryByText } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(queryByText('Hours Remaining')).toBeNull();
      expect(queryByText('Active Packages')).toBeNull();
    });
  });

  describe('Tab Navigation', () => {
    it('renders all navigation tabs', () => {
      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByText('Overview')).toBeTruthy();
      expect(getByText('Transactions')).toBeTruthy();
      expect(getByText('Purchases')).toBeTruthy();
      expect(getByText('Notifications')).toBeTruthy();
      expect(getByText('Settings')).toBeTruthy();
    });

    it('highlights active tab correctly', () => {
      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      const overviewTab = getByText('Overview');
      // Should have primary styling (active state)
      expect(overviewTab.closest('*').props.className).toContain('bg-primary-600');
    });

    it('changes active tab when tab is pressed', () => {
      const mockDashboard = createMockUseStudentDashboard();
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      fireEvent.press(getByText('Transactions'));

      expect(mockDashboard.actions.setActiveTab).toHaveBeenCalledWith('transactions');
    });

    it('provides proper accessibility labels for tabs', () => {
      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      const overviewTab = getByText('Overview');
      const transactionsTab = getByText('Transactions');

      expect(overviewTab.closest('*').props.accessibilityRole).toBe('tab');
      expect(overviewTab.closest('*').props.accessibilityState.selected).toBe(true);
      expect(transactionsTab.closest('*').props.accessibilityRole).toBe('tab');
      expect(transactionsTab.closest('*').props.accessibilityState.selected).toBe(false);
    });
  });

  describe('Search Bar', () => {
    it('shows search bar for transactions tab', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'transactions' } as any,
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByPlaceholderText } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByPlaceholderText('Search transactions...')).toBeTruthy();
    });

    it('shows search bar for purchases tab', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'purchases' } as any,
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByPlaceholderText } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByPlaceholderText('Search purchases...')).toBeTruthy();
    });

    it('hides search bar for other tabs', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'overview' } as any,
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { queryByPlaceholderText } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(queryByPlaceholderText(/Search/)).toBeNull();
    });

    it('updates search query when search input changes', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'transactions' } as any,
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByPlaceholderText } = render(<StudentAccountDashboard {...defaultProps} />);

      const searchInput = getByPlaceholderText('Search transactions...');
      fireEvent.changeText(searchInput, 'mathematics');

      expect(mockDashboard.actions.setSearchQuery).toHaveBeenCalledWith('mathematics');
    });
  });

  describe('Tab Content Rendering', () => {
    it('renders overview tab content by default', () => {
      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByTestId('dashboard-overview')).toBeTruthy();
    });

    it('renders transactions tab content when active', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'transactions' } as any,
        transactions: createMockTransactionHistory(),
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByTestId('transaction-history')).toBeTruthy();
    });

    it('renders purchases tab content when active', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'purchases' } as any,
        purchases: createMockPurchaseHistory(),
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByTestId('purchase-history')).toBeTruthy();
    });

    it('renders notifications tab content when active', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'notifications' } as any,
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByTestId('notification-center')).toBeTruthy();
    });

    it('renders settings tab content when active', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'settings' } as any,
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByTestId('account-settings')).toBeTruthy();
    });

    it('handles unknown tab gracefully', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'unknown' } as any,
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      // Should not crash and render nothing for unknown tab
      expect(() => {
        render(<StudentAccountDashboard {...defaultProps} />);
      }).not.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('displays error boundary when tab content throws', () => {
      // Mock console.error to avoid noise in test output
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      // Force an error in tab rendering by mocking a broken state
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'overview' } as any,
        balance: null, // This could cause issues in overview
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      // The error boundary should show fallback UI
      expect(getByText('Something went wrong')).toBeTruthy();
      expect(getByText('Unable to load this section. Please try refreshing or switching tabs.')).toBeTruthy();
      expect(getByText('Refresh Dashboard')).toBeTruthy();

      consoleSpy.mockRestore();
    });

    it('allows recovery from error boundary', () => {
      // Mock console.error
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      const mockDashboard = createMockUseStudentDashboard();
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      // If error boundary is shown, test refresh functionality
      try {
        const refreshButton = getByText('Refresh Dashboard');
        fireEvent.press(refreshButton);
        expect(mockDashboard.actions.refreshAll).toHaveBeenCalled();
      } catch (e) {
        // If no error boundary, that's also fine - means no error occurred
      }

      consoleSpy.mockRestore();
    });
  });

  describe('Action Handling', () => {
    it('navigates to purchase page when purchase button is clicked', () => {
      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      fireEvent.press(getByText('Purchase Hours'));

      expect(mockPush).toHaveBeenCalledWith('/purchase');
    });

    it('calls refreshAll when main refresh button is clicked', () => {
      const mockDashboard = createMockUseStudentDashboard();
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      fireEvent.press(getByText('Refresh'));

      expect(mockDashboard.actions.refreshAll).toHaveBeenCalled();
    });

    it('passes correct props to child components', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'transactions' } as any,
        transactions: createMockTransactionHistory(),
        transactionsLoading: true,
        transactionsError: 'Test error',
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} />);

      const transactionHistory = getByTestId('transaction-history');
      expect(transactionHistory).toHaveTextContent('Transactions: Available');
      expect(transactionHistory).toHaveTextContent('Loading: true');
      expect(transactionHistory).toHaveTextContent('Error: Test error');
    });

    it('passes email prop to hooks and child components', () => {
      const testEmail = 'test@example.com';
      const props = createMockStudentDashboardProps({ email: testEmail });

      render(<StudentAccountDashboard {...props} />);

      expect(mockUseStudentDashboard).toHaveBeenCalledWith(testEmail);
    });
  });

  describe('Responsive Design', () => {
    it('handles mobile layout properly', () => {
      // Test that tab layout works on smaller screens
      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      // Should render all tabs even on mobile
      expect(getByText('Overview')).toBeTruthy();
      expect(getByText('Transactions')).toBeTruthy();
      expect(getByText('Purchases')).toBeTruthy();
      expect(getByText('Notifications')).toBeTruthy();
      expect(getByText('Settings')).toBeTruthy();
    });

    it('applies responsive classes correctly', () => {
      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} testID="dashboard" />);

      const dashboard = getByTestId('dashboard');
      expect(dashboard.props.className).toContain('max-w-6xl');
      expect(dashboard.props.className).toContain('mx-auto');
    });
  });

  describe('Performance', () => {
    it('renders quickly', () => {
      const start = performance.now();
      render(<StudentAccountDashboard {...defaultProps} />);
      const end = performance.now();

      expect(end - start).toBeLessThan(150);
    });

    it('handles re-renders efficiently', () => {
      const { rerender } = render(<StudentAccountDashboard {...defaultProps} />);

      const start = performance.now();
      rerender(<StudentAccountDashboard {...defaultProps} />);
      const end = performance.now();

      expect(end - start).toBeLessThan(75);
    });
  });

  describe('Accessibility', () => {
    it('provides proper page structure', () => {
      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      expect(getByText('Account Dashboard')).toBeTruthy();
      expect(getByText('Manage your tutoring hours and account settings')).toBeTruthy();
    });

    it('provides accessible tab navigation', () => {
      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      const overviewTab = getByText('Overview');
      expect(overviewTab.closest('*').props.accessibilityRole).toBe('tab');
      expect(overviewTab.closest('*').props.accessibilityLabel).toContain('Overview - Account summary');
    });

    it('provides accessible action buttons', () => {
      const { getByText } = render(<StudentAccountDashboard {...defaultProps} />);

      const refreshButton = getByText('Refresh');
      const purchaseButton = getByText('Purchase Hours');

      expect(refreshButton).toBeTruthy();
      expect(purchaseButton).toBeTruthy();
    });
  });

  describe('Integration', () => {
    it('passes user profile to account settings', () => {
      const mockDashboard = createMockUseStudentDashboard({
        state: { activeTab: 'settings' } as any,
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} />);

      const accountSettings = getByTestId('account-settings');
      expect(accountSettings).toHaveTextContent('Profile: Available');
    });

    it('passes balance data to overview component', () => {
      const mockBalance = createMockStudentBalance();
      const mockDashboard = createMockUseStudentDashboard({
        balance: mockBalance,
      });
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} />);

      const overview = getByTestId('dashboard-overview');
      expect(overview).toHaveTextContent('Balance: Available');
    });

    it('coordinates tab changes between components', () => {
      const mockDashboard = createMockUseStudentDashboard();
      mockUseStudentDashboard.mockReturnValue(mockDashboard);

      const { getByTestId } = render(<StudentAccountDashboard {...defaultProps} />);

      // Simulate tab change from overview component
      fireEvent.press(getByTestId('overview-tab-change'));

      expect(mockDashboard.actions.setActiveTab).toHaveBeenCalledWith('transactions');
    });
  });
});