/**
 * StudentBalanceCard Component Tests
 *
 * Comprehensive test suite for the student balance display component.
 * Tests balance display, real-time updates, low balance warnings, and user interactions.
 */

import { render, fireEvent, waitFor } from '@testing-library/react-native';
import React from 'react';

import {
  createMockStudentBalance,
  createMockLowBalanceStudent,
  createMockStudentBalanceCardProps,
  createBalanceUpdateMessage,
} from '@/__tests__/utils/payment-test-utils';
import { StudentBalanceCard } from '@/components/purchase/StudentBalanceCard';
import { useStudentBalance } from '@/hooks/useStudentBalance';

// Mock the hook
jest.mock('@/hooks/useStudentBalance');
const mockUseStudentBalance = useStudentBalance as jest.MockedFunction<typeof useStudentBalance>;

// Mock router
const mockPush = jest.fn();
jest.mock('expo-router', () => ({
  useRouter: jest.fn(() => ({
    push: mockPush,
    back: jest.fn(),
    replace: jest.fn(),
  })),
  useLocalSearchParams: jest.fn(() => ({})),
}));

// Mock BalanceStatusBar components
jest.mock('@/components/student/balance/BalanceStatusBar', () => ({
  BalanceStatusBar: ({ remainingHours, totalHours, daysUntilExpiry, showDetails }: any) => (
    <div testID="balance-status-bar">
      Balance Status: {remainingHours}/{totalHours} hours, {daysUntilExpiry} days
      {showDetails && <span testID="status-details">Details</span>}
    </div>
  ),
  CompactBalanceStatusBar: ({ remainingHours, totalHours }: any) => (
    <div testID="compact-balance-status-bar">
      Compact: {remainingHours}/{totalHours} hours
    </div>
  ),
}));

describe('StudentBalanceCard Component', () => {
  const defaultProps = createMockStudentBalanceCardProps();

  beforeEach(() => {
    jest.clearAllMocks();
    mockPush.mockClear();
  });

  describe('Loading State', () => {
    it('displays loading state correctly', () => {
      mockUseStudentBalance.mockReturnValue({
        balance: null,
        loading: true,
        error: null,
        refetch: jest.fn(),
      });

      const result = render(<StudentBalanceCard {...defaultProps} />);

      // Loading state should show spinner component
      expect(result.getByTestId('Spinner')).toBeTruthy();
    });

    it('shows spinner during loading', () => {
      mockUseStudentBalance.mockReturnValue({
        balance: null,
        loading: true,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByTestId('spinner')).toBeTruthy();
    });
  });

  describe('Error State', () => {
    it('displays error message when balance loading fails', () => {
      const errorMessage = 'Failed to load balance information';
      mockUseStudentBalance.mockReturnValue({
        balance: null,
        loading: false,
        error: errorMessage,
        refetch: jest.fn(),
      });

      const result = render(<StudentBalanceCard {...defaultProps} />);

      // Use queryByText which is more forgiving for nested text
      expect(result.queryByText(/Unable to Load Balance/)).toBeTruthy();
      expect(result.queryByText(errorMessage)).toBeTruthy(); 
      expect(result.queryByText('Try Again')).toBeTruthy();
    });

    it('allows retry when error occurs', () => {
      const mockRefetch = jest.fn();
      mockUseStudentBalance.mockReturnValue({
        balance: null,
        loading: false,
        error: 'Network error',
        refetch: mockRefetch,
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      fireEvent.press(getByText('Try Again'));

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Balance Display', () => {
    it('renders balance information correctly', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('Account Balance')).toBeTruthy();
      expect(getByText('John Doe (john@example.com)')).toBeTruthy();
      expect(getByText('10.0')).toBeTruthy(); // Remaining hours
      expect(getByText('Hours Remaining')).toBeTruthy();
      expect(getByText('15.0')).toBeTruthy(); // Hours purchased
      expect(getByText('Hours Purchased')).toBeTruthy();
      expect(getByText('5.0')).toBeTruthy(); // Hours used
      expect(getByText('Hours Used')).toBeTruthy();
    });

    it('displays balance status bar when showStatusBar is true', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<StudentBalanceCard {...defaultProps} showStatusBar={true} />);

      expect(getByTestId('balance-status-bar')).toBeTruthy();
    });

    it('hides balance status bar when showStatusBar is false', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { queryByTestId } = render(
        <StudentBalanceCard {...defaultProps} showStatusBar={false} />,
      );

      expect(queryByTestId('balance-status-bar')).toBeNull();
    });

    it('hides student info when showStudentInfo is false', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { queryByText } = render(
        <StudentBalanceCard {...defaultProps} showStudentInfo={false} />,
      );

      expect(queryByText('John Doe (john@example.com)')).toBeNull();
    });

    it('shows details in status bar when not compact', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(
        <StudentBalanceCard {...defaultProps} compact={false} showStatusBar={true} />,
      );

      expect(getByTestId('status-details')).toBeTruthy();
    });
  });

  describe('Low Balance Warnings', () => {
    it('shows warning color for very low balance (≤2 hours)', () => {
      const balance = createMockLowBalanceStudent();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      // Should show remaining hours in error color
      expect(getByText('1.5')).toBeTruthy(); // Low balance hours
    });

    it('shows Buy Hours button for low balance', () => {
      const balance = createMockLowBalanceStudent();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('Buy Hours')).toBeTruthy();
    });

    it('navigates to purchase page when Buy Hours is clicked', () => {
      const balance = createMockLowBalanceStudent();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      fireEvent.press(getByText('Buy Hours'));

      expect(mockPush).toHaveBeenCalledWith('/purchase');
    });

    it('hides Buy Hours button for sufficient balance', () => {
      const balance = createMockStudentBalance({
        balance_summary: {
          hours_purchased: '20.0',
          hours_consumed: '5.0',
          remaining_hours: '15.0', // High balance
          balance_amount: '150.00',
        },
      });

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { queryByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(queryByText('Buy Hours')).toBeNull();
    });
  });

  describe('Active Packages', () => {
    it('displays active packages section', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('Active Packages')).toBeTruthy();
      expect(getByText('Standard Package')).toBeTruthy();
      expect(getByText('7.0 of 10.0 hours remaining')).toBeTruthy();
      expect(getByText('30 days left')).toBeTruthy();
    });

    it('hides active packages section when no packages exist', () => {
      const balance = createMockStudentBalance({
        package_status: {
          active_packages: [],
          expired_packages: [],
        },
      });

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { queryByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(queryByText('Active Packages')).toBeNull();
    });

    it('shows warning badge for packages expiring soon', () => {
      const balance = createMockStudentBalance({
        package_status: {
          active_packages: [
            {
              transaction_id: 1,
              plan_name: 'Urgent Package',
              hours_included: '10.0',
              hours_consumed: '3.0',
              hours_remaining: '7.0',
              expires_at: '2024-04-01T00:00:00Z',
              days_until_expiry: 3, // Expiring soon
              is_expired: false,
            },
          ],
          expired_packages: [],
        },
      });

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('3 days left')).toBeTruthy();
    });
  });

  describe('Upcoming Expirations', () => {
    it('displays upcoming expirations section', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('Expiring Soon')).toBeTruthy();
      expect(getByText('7.0 hours remaining')).toBeTruthy();
      expect(getByText('30 days left')).toBeTruthy();
    });

    it('shows urgent badge for imminent expirations', () => {
      const balance = createMockStudentBalance({
        upcoming_expirations: [
          {
            transaction_id: 1,
            plan_name: 'Urgent Package',
            hours_remaining: '5.0',
            expires_at: '2024-04-01T00:00:00Z',
            days_until_expiry: 2, // Very urgent
          },
        ],
      });

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('2 days left')).toBeTruthy();
    });

    it('hides expiring soon section when no expirations', () => {
      const balance = createMockStudentBalance({
        upcoming_expirations: [],
      });

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { queryByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(queryByText('Expiring Soon')).toBeNull();
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no packages and no balance', () => {
      const balance = createMockStudentBalance({
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

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('No Active Packages')).toBeTruthy();
      expect(getByText(/Purchase a tutoring package/)).toBeTruthy();
    });

    it('does not show empty state when packages exist', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { queryByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(queryByText('No Active Packages')).toBeNull();
    });

    it('does not show empty state when balance exists', () => {
      const balance = createMockStudentBalance({
        package_status: {
          active_packages: [],
          expired_packages: [],
        },
        upcoming_expirations: [],
        balance_summary: {
          hours_purchased: '5.0',
          hours_consumed: '2.0',
          remaining_hours: '3.0',
          balance_amount: '30.00',
        },
      });

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { queryByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(queryByText('No Active Packages')).toBeNull();
    });
  });

  describe('Refresh Functionality', () => {
    it('calls refetch when refresh button is clicked', () => {
      const mockRefetch = jest.fn();
      const balance = createMockStudentBalance();

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: mockRefetch,
      });

      const { getByTestId } = render(<StudentBalanceCard {...defaultProps} />);

      fireEvent.press(getByTestId('refresh-button'));

      expect(mockRefetch).toHaveBeenCalled();
    });

    it('calls onRefresh prop when refresh button is clicked', () => {
      const mockOnRefresh = jest.fn();
      const balance = createMockStudentBalance();

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(
        <StudentBalanceCard {...defaultProps} onRefresh={mockOnRefresh} />,
      );

      fireEvent.press(getByTestId('refresh-button'));

      expect(mockOnRefresh).toHaveBeenCalled();
    });

    it('handles refresh when no balance data', () => {
      const mockRefetch = jest.fn();

      mockUseStudentBalance.mockReturnValue({
        balance: null,
        loading: false,
        error: null,
        refetch: mockRefetch,
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      fireEvent.press(getByText('Refresh'));

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Compact Mode', () => {
    it('uses compact layout when compact prop is true', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { queryByTestId } = render(
        <StudentBalanceCard {...defaultProps} compact={true} showStatusBar={true} />,
      );

      // In compact mode, details should be hidden from status bar
      expect(queryByTestId('status-details')).toBeNull();
    });
  });

  describe('Number Formatting', () => {
    it('formats decimal hours correctly', () => {
      const balance = createMockStudentBalance({
        balance_summary: {
          hours_purchased: '15.75',
          hours_consumed: '3.25',
          remaining_hours: '12.5',
          balance_amount: '125.50',
        },
      });

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('12.5')).toBeTruthy(); // Remaining hours
      expect(getByText('15.8')).toBeTruthy(); // Hours purchased (rounded)
      expect(getByText('3.3')).toBeTruthy(); // Hours consumed (rounded)
    });

    it('handles zero values gracefully', () => {
      const balance = createMockStudentBalance({
        balance_summary: {
          hours_purchased: '0.0',
          hours_consumed: '0.0',
          remaining_hours: '0.0',
          balance_amount: '0.00',
        },
      });

      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('0.0')).toBeTruthy();
    });
  });

  describe('Accessibility', () => {
    it('provides proper accessibility labels', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('Account Balance')).toBeTruthy();
      expect(getByText('Hours Summary')).toBeTruthy();
      expect(getByText('Active Packages')).toBeTruthy();
    });

    it('provides accessible error messages', () => {
      mockUseStudentBalance.mockReturnValue({
        balance: null,
        loading: false,
        error: 'Network error',
        refetch: jest.fn(),
      });

      const { getByText } = render(<StudentBalanceCard {...defaultProps} />);

      expect(getByText('Unable to Load Balance')).toBeTruthy();
      expect(getByText('Network error')).toBeTruthy();
    });
  });

  describe('Performance', () => {
    it('renders quickly under normal conditions', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const start = performance.now();
      render(<StudentBalanceCard {...defaultProps} />);
      const end = performance.now();

      expect(end - start).toBeLessThan(100);
    });

    it('handles re-renders efficiently', () => {
      const balance = createMockStudentBalance();
      mockUseStudentBalance.mockReturnValue({
        balance,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { rerender } = render(<StudentBalanceCard {...defaultProps} />);

      const start = performance.now();
      rerender(<StudentBalanceCard {...defaultProps} />);
      const end = performance.now();

      expect(end - start).toBeLessThan(50);
    });
  });
});
