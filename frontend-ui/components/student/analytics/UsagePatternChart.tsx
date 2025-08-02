/**
 * Usage Pattern Chart Component - Fallback Implementation
 *
 * Main entry point with Platform.OS fallback.
 * Platform-specific files should override this implementation.
 */

import React from 'react';
import { Platform } from 'react-native';

import {
  UsagePatternChartProps,
  useProcessedChartData,
  usePatternInsights,
  LoadingState,
  EmptyState,
} from './usage-pattern-common';

// Export types for external usage
export type { UsagePatternChartProps };

/**
 * Fallback Usage Pattern Chart Component.
 * Platform-specific implementations should override this.
 */
export function UsagePatternChart({ patterns, loading, timeRange }: UsagePatternChartProps) {
  const chartData = useProcessedChartData(patterns);
  const insights = usePatternInsights(patterns);

  if (loading) {
    return <LoadingState />;
  }

  if (!chartData || patterns.length === 0) {
    return <EmptyState />;
  }

  // This fallback shouldn't be reached due to platform file resolution
  // but provides a basic implementation if needed
  return <EmptyState />;
}
