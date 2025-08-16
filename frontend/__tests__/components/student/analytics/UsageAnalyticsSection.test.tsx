/**
 * UsageAnalyticsSection Component Tests
 *
 * Comprehensive test suite for the usage analytics component.
 * Tests data visualization, time range selection, statistics display, and chart rendering.
 */

import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import React from 'react';

import { createMockAnalyticsData, cleanupStudentMocks } from '@/__tests__/utils/student-test-utils';
import { UsageAnalyticsSection } from '@/components/student/analytics/UsageAnalyticsSection';
import { useAnalytics } from '@/hooks/useAnalytics';

// Mock the analytics hook
jest.mock('@/hooks/useAnalytics');
const mockUseAnalytics = useAnalytics as jest.MockedFunction<typeof useAnalytics>;

// Mock child components
jest.mock('@/components/student/analytics/UsagePatternChart', () => ({
  UsagePatternChart: ({ patterns, loading, timeRange }: any) => (
    <div testID="usage-pattern-chart">
      <span>Time Range: {timeRange}</span>
      <span>Loading: {loading.toString()}</span>
      <span>Patterns: {patterns ? 'Available' : 'None'}</span>
    </div>
  ),
}));

jest.mock('@/components/student/analytics/LearningInsightsCard', () => ({
  LearningInsightsCard: ({ insights, onRefresh }: any) => (
    <div testID="learning-insights-card">
      <span>Insights: {insights ? 'Available' : 'None'}</span>
      <button testID="insights-refresh" onPress={onRefresh}>
        Refresh Insights
      </button>
    </div>
  ),
}));

describe('UsageAnalyticsSection Component', () => {
  const mockAnalyticsData = createMockAnalyticsData();
  const defaultProps = {
    email: 'student@test.com',
  };

  beforeEach(() => {
    cleanupStudentMocks();

    // Default successful mock return
    mockUseAnalytics.mockReturnValue({
      usageStats: {
        total_sessions: 25,
        sessions_this_month: 8,
        total_hours_consumed: 45.5,
        hours_this_month: 12.5,
        average_session_duration: 1.8,
        streak_days: 5,
        most_active_subject: 'Mathematics',
        preferred_time_slot: 'Evening',
        ...mockAnalyticsData,
      },
      usageStatsLoading: false,
      usageStatsError: null,
      insights: mockAnalyticsData,
      patterns: mockAnalyticsData.performance_trends,
      refreshUsageStats: jest.fn().mockResolvedValue(undefined),
      refreshInsights: jest.fn().mockResolvedValue(undefined),
      refreshPatterns: jest.fn().mockResolvedValue(undefined),
      refreshAll: jest.fn().mockResolvedValue(undefined),
    });
  });

  describe('Loading State', () => {
    it('displays loading state when data is being fetched', () => {
      mockUseAnalytics.mockReturnValue({
        usageStats: null,
        usageStatsLoading: true,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { getByText, getByTestId } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Usage Analytics')).toBeTruthy();
      expect(getByTestId('spinner')).toBeTruthy();
      expect(getByText('Loading analytics...')).toBeTruthy();
    });

    it('does not show loading when analytics data exists', () => {
      const { queryByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(queryByText('Loading analytics...')).toBeNull();
    });
  });

  describe('Error State', () => {
    it('displays error state when analytics loading fails', () => {
      mockUseAnalytics.mockReturnValue({
        usageStats: null,
        usageStatsLoading: false,
        usageStatsError: 'Failed to load analytics data',
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Usage Analytics')).toBeTruthy();
      expect(getByText('Unable to Load Analytics')).toBeTruthy();
      expect(getByText('Failed to load analytics data')).toBeTruthy();
      expect(getByText('Try Again')).toBeTruthy();
    });

    it('allows retry when error occurs', () => {
      const mockRefreshAll = jest.fn();
      mockUseAnalytics.mockReturnValue({
        usageStats: null,
        usageStatsLoading: false,
        usageStatsError: 'Network error',
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: mockRefreshAll,
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      fireEvent.press(getByText('Try Again'));
      expect(mockRefreshAll).toHaveBeenCalled();
    });

    it('does not show error when analytics data exists', () => {
      const { queryByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(queryByText('Unable to Load Analytics')).toBeNull();
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no analytics data exists', () => {
      mockUseAnalytics.mockReturnValue({
        usageStats: null,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Usage Analytics')).toBeTruthy();
      expect(getByText('No Analytics Data')).toBeTruthy();
      expect(
        getByText('Start attending tutoring sessions to see your learning analytics here'),
      ).toBeTruthy();
    });
  });

  describe('Analytics Data Display', () => {
    it('renders main analytics header correctly', () => {
      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Usage Analytics')).toBeTruthy();
      expect(getByText('Track your learning progress and session patterns')).toBeTruthy();
    });

    it('displays refresh button', () => {
      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Refresh')).toBeTruthy();
    });

    it('shows loading state on refresh button when refreshing', () => {
      mockUseAnalytics.mockReturnValue({
        usageStats: { total_sessions: 25 } as any,
        usageStatsLoading: true,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Refreshing...')).toBeTruthy();
    });

    it('displays overview statistics correctly', () => {
      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Overview Statistics')).toBeTruthy();
      expect(getByText('Total Sessions')).toBeTruthy();
      expect(getByText('25')).toBeTruthy(); // total_sessions value
      expect(getByText('Sessions completed')).toBeTruthy();
      expect(getByText('8 this month')).toBeTruthy(); // sessions trend

      expect(getByText('Hours Consumed')).toBeTruthy();
      expect(getByText('45.5h')).toBeTruthy(); // total_hours_consumed
      expect(getByText('Total learning time')).toBeTruthy();
      expect(getByText('12.5h this month')).toBeTruthy(); // hours trend

      expect(getByText('Average Session')).toBeTruthy();
      expect(getByText('1.8h')).toBeTruthy(); // average_session_duration
      expect(getByText('Session duration')).toBeTruthy();

      expect(getByText('Learning Streak')).toBeTruthy();
      expect(getByText('5 days')).toBeTruthy(); // streak_days
      expect(getByText('Current streak')).toBeTruthy();
    });

    it('displays learning preferences when available', () => {
      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Learning Preferences')).toBeTruthy();
      expect(getByText('Most Active Subject:')).toBeTruthy();
      expect(getByText('Mathematics')).toBeTruthy();
      expect(getByText('Preferred Time:')).toBeTruthy();
      expect(getByText('Evening')).toBeTruthy();
    });

    it('hides learning preferences when not available', () => {
      mockUseAnalytics.mockReturnValue({
        usageStats: {
          total_sessions: 25,
          sessions_this_month: 8,
          total_hours_consumed: 45.5,
          hours_this_month: 12.5,
          average_session_duration: 1.8,
          streak_days: 5,
          most_active_subject: null,
          preferred_time_slot: null,
        } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { queryByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(queryByText('Learning Preferences')).toBeNull();
    });

    it('displays streak motivation messages correctly', () => {
      // Test high streak (> 7 days)
      mockUseAnalytics.mockReturnValue({
        usageStats: { streak_days: 10 } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { getByText, rerender } = render(<UsageAnalyticsSection {...defaultProps} />);
      expect(getByText('Great momentum!')).toBeTruthy();

      // Test medium streak (1-7 days)
      mockUseAnalytics.mockReturnValue({
        usageStats: { streak_days: 3 } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      rerender(<UsageAnalyticsSection {...defaultProps} />);
      expect(getByText('Keep it up!')).toBeTruthy();

      // Test no streak (0 days)
      mockUseAnalytics.mockReturnValue({
        usageStats: { streak_days: 0 } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      rerender(<UsageAnalyticsSection {...defaultProps} />);
      expect(getByText('Start a streak')).toBeTruthy();
    });
  });

  describe('Time Range Selector', () => {
    it('displays time range selector buttons', () => {
      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Time Period')).toBeTruthy();
      expect(getByText('This Week')).toBeTruthy();
      expect(getByText('This Month')).toBeTruthy();
      expect(getByText('Last 3 Months')).toBeTruthy();
      expect(getByText('This Year')).toBeTruthy();
    });

    it('defaults to "This Month" selection', () => {
      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      const monthButton = getByText('This Month');
      expect(monthButton.closest('*').props.action).toBe('primary'); // Selected state
    });

    it('changes time range when different period is selected', async () => {
      const mockRefreshUsageStats = jest.fn().mockResolvedValue(undefined);
      const mockRefreshPatterns = jest.fn().mockResolvedValue(undefined);

      mockUseAnalytics.mockReturnValue({
        usageStats: { total_sessions: 25 } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: mockRefreshUsageStats,
        refreshInsights: jest.fn(),
        refreshPatterns: mockRefreshPatterns,
        refreshAll: jest.fn(),
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      // Select "This Week"
      await act(async () => {
        fireEvent.press(getByText('This Week'));
      });

      // Should refresh data with new time range
      expect(mockRefreshUsageStats).toHaveBeenCalled();
      expect(mockRefreshPatterns).toHaveBeenCalled();

      const callArgs = mockRefreshUsageStats.mock.calls[0][0];
      expect(callArgs).toHaveProperty('start_date');
      expect(callArgs).toHaveProperty('end_date');
    });

    it('calculates correct date ranges for different periods', async () => {
      const mockRefreshUsageStats = jest.fn();
      const mockRefreshPatterns = jest.fn();

      mockUseAnalytics.mockReturnValue({
        usageStats: { total_sessions: 25 } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: mockRefreshUsageStats,
        refreshInsights: jest.fn(),
        refreshPatterns: mockRefreshPatterns,
        refreshAll: jest.fn(),
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      // Test week range
      await act(async () => {
        fireEvent.press(getByText('This Week'));
      });

      let timeRange = mockRefreshUsageStats.mock.calls[0][0];
      const weekStart = new Date(timeRange.start_date);
      const weekEnd = new Date(timeRange.end_date);
      const daysDiff = Math.ceil((weekEnd.getTime() - weekStart.getTime()) / (1000 * 60 * 60 * 24));
      expect(daysDiff).toBeLessThanOrEqual(7);

      // Test quarter range
      mockRefreshUsageStats.mockClear();
      await act(async () => {
        fireEvent.press(getByText('Last 3 Months'));
      });

      timeRange = mockRefreshUsageStats.mock.calls[0][0];
      const quarterStart = new Date(timeRange.start_date);
      const quarterEnd = new Date(timeRange.end_date);
      const quarterDays = Math.ceil(
        (quarterEnd.getTime() - quarterStart.getTime()) / (1000 * 60 * 60 * 24),
      );
      expect(quarterDays).toBeLessThanOrEqual(90);
    });

    it('handles time range change errors gracefully', async () => {
      const mockRefreshUsageStats = jest.fn().mockRejectedValue(new Error('Network error'));
      const mockRefreshPatterns = jest.fn().mockResolvedValue(undefined);

      mockUseAnalytics.mockReturnValue({
        usageStats: { total_sessions: 25 } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: mockRefreshUsageStats,
        refreshInsights: jest.fn(),
        refreshPatterns: mockRefreshPatterns,
        refreshAll: jest.fn(),
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      // Should not throw when time range change fails
      await act(async () => {
        fireEvent.press(getByText('This Week'));
      });

      expect(mockRefreshUsageStats).toHaveBeenCalled();
    });
  });

  describe('Child Components', () => {
    it('renders UsagePatternChart with correct props', () => {
      const { getByTestId } = render(<UsageAnalyticsSection {...defaultProps} />);

      const chartComponent = getByTestId('usage-pattern-chart');
      expect(chartComponent).toBeTruthy();
      expect(chartComponent).toHaveTextContent('Time Range: month');
      expect(chartComponent).toHaveTextContent('Loading: false');
      expect(chartComponent).toHaveTextContent('Patterns: Available');
    });

    it('renders LearningInsightsCard with correct props', () => {
      const { getByTestId } = render(<UsageAnalyticsSection {...defaultProps} />);

      const insightsComponent = getByTestId('learning-insights-card');
      expect(insightsComponent).toBeTruthy();
      expect(insightsComponent).toHaveTextContent('Insights: Available');
    });

    it('passes updated time range to UsagePatternChart when changed', async () => {
      const { getByText, getByTestId } = render(<UsageAnalyticsSection {...defaultProps} />);

      await act(async () => {
        fireEvent.press(getByText('This Week'));
      });

      const chartComponent = getByTestId('usage-pattern-chart');
      expect(chartComponent).toHaveTextContent('Time Range: week');
    });
  });

  describe('Refresh Functionality', () => {
    it('calls refreshAll when refresh button is clicked', () => {
      const mockRefreshAll = jest.fn();
      mockUseAnalytics.mockReturnValue({
        usageStats: { total_sessions: 25 } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: mockRefreshAll,
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      fireEvent.press(getByText('Refresh'));
      expect(mockRefreshAll).toHaveBeenCalled();
    });

    it('disables refresh button when loading', () => {
      mockUseAnalytics.mockReturnValue({
        usageStats: { total_sessions: 25 } as any,
        usageStatsLoading: true,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      const refreshButton = getByText('Refreshing...');
      expect(refreshButton.closest('*').props.disabled).toBe(true);
    });

    it('passes refreshInsights to LearningInsightsCard', () => {
      const mockRefreshInsights = jest.fn();
      mockUseAnalytics.mockReturnValue({
        usageStats: { total_sessions: 25 } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: mockAnalyticsData,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: mockRefreshInsights,
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { getByTestId } = render(<UsageAnalyticsSection {...defaultProps} />);

      const insightsRefreshButton = getByTestId('insights-refresh');
      fireEvent.press(insightsRefreshButton);
      expect(mockRefreshInsights).toHaveBeenCalled();
    });
  });

  describe('Props Handling', () => {
    it('passes email prop to useAnalytics hook', () => {
      const testEmail = 'test@example.com';
      render(<UsageAnalyticsSection email={testEmail} />);

      expect(mockUseAnalytics).toHaveBeenCalledWith(testEmail);
    });

    it('handles undefined email prop', () => {
      render(<UsageAnalyticsSection />);

      expect(mockUseAnalytics).toHaveBeenCalledWith(undefined);
    });
  });

  describe('Performance', () => {
    it('renders quickly', () => {
      const start = performance.now();
      render(<UsageAnalyticsSection {...defaultProps} />);
      const end = performance.now();

      expect(end - start).toBeLessThan(100);
    });

    it('handles re-renders efficiently', () => {
      const { rerender } = render(<UsageAnalyticsSection {...defaultProps} />);

      const start = performance.now();
      rerender(<UsageAnalyticsSection {...defaultProps} />);
      const end = performance.now();

      expect(end - start).toBeLessThan(50);
    });
  });

  describe('Accessibility', () => {
    it('provides proper headings structure', () => {
      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Usage Analytics')).toBeTruthy();
      expect(getByText('Overview Statistics')).toBeTruthy();
      expect(getByText('Learning Preferences')).toBeTruthy();
    });

    it('provides accessible time range selector', () => {
      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Time Period')).toBeTruthy();
      expect(getByText('This Week')).toBeTruthy();
      expect(getByText('This Month')).toBeTruthy();
    });

    it('provides accessible error messages', () => {
      mockUseAnalytics.mockReturnValue({
        usageStats: null,
        usageStatsLoading: false,
        usageStatsError: 'Failed to load data',
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Unable to Load Analytics')).toBeTruthy();
      expect(getByText('Failed to load data')).toBeTruthy();
    });
  });

  describe('Edge Cases', () => {
    it('handles missing statistics gracefully', () => {
      mockUseAnalytics.mockReturnValue({
        usageStats: {
          total_sessions: null,
          sessions_this_month: undefined,
          total_hours_consumed: 0,
          hours_this_month: 0,
          average_session_duration: 0,
          streak_days: 0,
        } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      expect(() => {
        render(<UsageAnalyticsSection {...defaultProps} />);
      }).not.toThrow();
    });

    it('handles very large numbers in statistics', () => {
      mockUseAnalytics.mockReturnValue({
        usageStats: {
          total_sessions: 9999,
          sessions_this_month: 999,
          total_hours_consumed: 9999.99,
          hours_this_month: 999.99,
          average_session_duration: 99.99,
          streak_days: 365,
          most_active_subject: 'A Very Long Subject Name That Should Be Handled Properly',
          preferred_time_slot: 'Very Early Morning',
        } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { getByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('9999')).toBeTruthy();
      expect(getByText('9999.99h')).toBeTruthy();
      expect(getByText('365 days')).toBeTruthy();
    });

    it('handles partial learning preferences data', () => {
      mockUseAnalytics.mockReturnValue({
        usageStats: {
          total_sessions: 25,
          most_active_subject: 'Mathematics',
          preferred_time_slot: null, // Only one preference available
        } as any,
        usageStatsLoading: false,
        usageStatsError: null,
        insights: null,
        patterns: null,
        refreshUsageStats: jest.fn(),
        refreshInsights: jest.fn(),
        refreshPatterns: jest.fn(),
        refreshAll: jest.fn(),
      });

      const { getByText, queryByText } = render(<UsageAnalyticsSection {...defaultProps} />);

      expect(getByText('Learning Preferences')).toBeTruthy();
      expect(getByText('Mathematics')).toBeTruthy();
      expect(queryByText('Preferred Time:')).toBeNull();
    });
  });
});
