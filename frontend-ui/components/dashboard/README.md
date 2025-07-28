# School Admin Dashboard Components

This directory contains the comprehensive School Admin Dashboard implementation for the Aprende Comigo platform, addressing GitHub issue #60.

## Components Overview

### 1. MetricsCard
Real-time display of school statistics including:
- Student and teacher counts with trends
- Active classes and completion rates
- Invitation acceptance rates
- Visual trend indicators and progress bars

### 2. QuickActionsPanel
Common administrative actions for school administrators:
- Invite Teacher
- Add Student
- Schedule Class
- View Messages
- Manage Users
- Settings

### 3. ActivityFeed
Real-time activity feed with:
- Paginated activity list
- Real-time updates via WebSocket
- Activity type filtering
- Pull-to-refresh functionality
- Load more pagination

### 4. SchoolInfoCard
Editable school information display:
- View/edit school details
- Contact information management
- School settings configuration
- In-place editing with validation

## Usage

```tsx
import { 
  MetricsCard, 
  QuickActionsPanel, 
  ActivityFeed, 
  SchoolInfoCard 
} from '@/components/dashboard';
import useSchoolDashboard from '@/hooks/useSchoolDashboard';

function SchoolDashboard() {
  const {
    metrics,
    schoolInfo,
    activities,
    isLoading,
    refreshAll,
    updateSchool,
    // ... other properties
  } = useSchoolDashboard({
    schoolId: 1,
    enableRealtime: true,
    refreshInterval: 30000,
  });

  return (
    <VStack space="lg">
      <MetricsCard metrics={metrics} isLoading={isLoading} />
      <QuickActionsPanel 
        onInviteTeacher={() => {/* navigation logic */}}
        onAddStudent={() => {/* navigation logic */}}
        // ... other handlers
      />
      <ActivityFeed 
        activities={activities}
        isLoading={isLoading}
        onRefresh={refreshAll}
        // ... other props
      />
      <SchoolInfoCard 
        schoolInfo={schoolInfo}
        isLoading={isLoading}
        onUpdate={updateSchool}
      />
    </VStack>
  );
}
```

## Features

### Real-time Updates
- WebSocket integration for live dashboard updates
- Automatic fallback to polling when WebSocket unavailable
- Real-time metrics and activity feed updates

### Responsive Design
- Cross-platform compatibility (web, iOS, Android)
- Adaptive layouts for different screen sizes
- Proper loading states and error handling

### Data Management
- Custom hook (`useSchoolDashboard`) for state management
- Efficient API integration with proper caching
- Pagination support for large datasets

### User Experience
- Empty states with clear calls-to-action
- Loading skeletons for better perceived performance
- Error handling with retry mechanisms
- Optimistic updates for better responsiveness

## API Integration

The dashboard integrates with the following backend endpoints:

- `GET /api/accounts/schools/{id}/metrics/` - School statistics
- `GET /api/accounts/schools/{id}/activity/` - Activity feed
- `PATCH /api/accounts/schools/{id}/` - Update school information
- WebSocket: `ws/schools/{id}/dashboard/` - Real-time updates

## TypeScript Support

All components are fully typed with comprehensive TypeScript interfaces:

- `SchoolMetrics` - School statistics data
- `SchoolActivity` - Activity feed items
- `SchoolInfo` - School information
- Custom hook types for proper state management

## Performance Considerations

- Lazy loading for large activity feeds
- Memoized components to prevent unnecessary re-renders
- Efficient WebSocket message handling
- Proper cleanup of resources and event listeners

## Accessibility

- Proper semantic structure with ARIA labels
- Keyboard navigation support
- Screen reader compatibility
- High contrast color schemes

## Testing

The dashboard is designed to work with the existing QA testing framework:

- Unit tests for individual components
- Integration tests for data flow
- E2E tests for user workflows
- Performance tests for large datasets