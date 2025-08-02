// Enhanced Teacher Dashboard Components for GitHub Issue #91
// Comprehensive teacher dashboard implementation with responsive design,
// advanced student management, performance analytics, and accessibility features

export { default as TodaysOverview } from './TodaysOverview';
export { default as StudentManagement } from './StudentManagement';
export { default as QuickActionsPanel } from './QuickActionsPanel';
export { default as PerformanceAnalytics } from './PerformanceAnalytics';
export { default as DashboardSkeleton } from './DashboardSkeleton';

// Re-export existing dashboard components for backward compatibility
export { default as ActivityFeed } from '../dashboard/ActivityFeed';
export { default as MetricsCard } from '../dashboard/MetricsCard';
export { default as QuickActionsPanel as LegacyQuickActionsPanel } from '../dashboard/QuickActionsPanel';
export { default as SchoolInfoCard } from '../dashboard/SchoolInfoCard';