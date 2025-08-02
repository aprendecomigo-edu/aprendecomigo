# Dashboard Backend Cleanup Analysis - GitHub Issue #130

**Date**: August 2, 2025  
**Context**: Frontend team removed dashboard features, but backend APIs still being called  
**Investigator**: Claude Code

## Executive Summary

The frontend cleanup of GitHub issue #130 "Clean Dashboard Foundation" successfully removed UI components but left behind orphaned backend API calls. The dashboard is making **unnecessary API calls every 30 seconds** to endpoints that no longer serve any UI functionality, creating waste in:

- Database queries and CPU cycles
- Network bandwidth
- Cache utilization  
- Memory allocation

## Current API Usage Analysis

Based on backend logs (`logs/backend-20250802-202143.log`), these endpoints are being called repeatedly:

```
GET /api/accounts/schools/1/metrics/ HTTP/1.1" 200 534
GET /api/accounts/schools/1/activity/?page=1&page_size=20 HTTP/1.1" 200 52  
GET /api/notifications/counts/ HTTP/1.1" 200 132
```

### Frequency
- **Every 30 seconds** via auto-refresh in `useSchoolDashboard` hook
- **Continuous polling** during active dashboard sessions

## Detailed Findings

### 1. Metrics API (`/api/accounts/schools/{id}/metrics/`)

**Status**: ❌ **ORPHANED - Safe to Deprecate**

**Current Implementation**:
- **Location**: `backend/accounts/views.py` - `SchoolViewSet.metrics()` action
- **Service**: `SchoolMetricsService` in `backend/accounts/services/metrics_service.py`
- **Functionality**: Calculates comprehensive school metrics including:
  - Student counts and trends (daily/weekly/monthly)
  - Teacher counts and trends
  - Class session metrics and completion rates
  - Engagement metrics (invitation acceptance)
- **Cache**: 5-minute TTL with secure key generation
- **Database Impact**: Complex queries with date ranges, aggregations, joins

**Frontend Usage**: 
- ✅ API function exists: `getSchoolMetrics()` in `frontend-ui/api/userApi.ts`
- ❌ UI components removed: No metrics display in current dashboard
- 🔄 Still called: `useSchoolDashboard` hook fetches but doesn't use data

**Recommendation**: **DEPRECATE** - No UI consumes this data

### 2. Activity API (`/api/accounts/schools/{id}/activity/`)

**Status**: ⚠️ **PARTIALLY ORPHANED - Modify/Simplify**

**Current Implementation**:
- **Location**: `backend/accounts/views.py` - `SchoolViewSet.activity()` action  
- **Service**: `SchoolActivityService` in `backend/accounts/services/metrics_service.py`
- **Functionality**: Paginated activity feed with filtering
- **Database Impact**: SELECT_RELATED and PREFETCH_RELATED queries
- **Returns**: 52 bytes (minimal/empty results)

**Frontend Usage**:
- ✅ API function exists: `getSchoolActivity()` in `frontend-ui/api/userApi.ts`
- ⚠️ UI shows placeholder: "Coming Soon" message instead of activity data
- 🔄 Still called: Data fetched but not displayed

**Recommendation**: **SIMPLIFY** - Return static "coming soon" response or deprecate

### 3. Notifications API (`/api/notifications/counts/`)

**Status**: ❓ **NEEDS INVESTIGATION - Potentially Still Used**

**Current Implementation**:
- **Location**: `backend/notifications/views.py` - `notification_counts()` function
- **Marked**: Legacy endpoint with backward compatibility note
- **Returns**: 132 bytes of notification count data

**Frontend Usage**: 
- ❓ Not directly visible in dashboard hook
- ❓ May be used by other components (navigation, header)

**Recommendation**: **INVESTIGATE** - Determine if used elsewhere before removal

### 4. WebSocket Consumers

**Status**: ❌ **COMPLETELY ORPHANED**

**Current Implementation**:
- **Location**: `backend/accounts/consumers.py`
- **Class**: `SchoolDashboardConsumer`
- **Functionality**: Real-time dashboard updates via WebSocket
- **Broadcasting**: Metrics updates, activity updates, invitation status

**Frontend Usage**:
- ❌ No WebSocket connections visible in current dashboard code
- ❌ Real-time functionality removed from UI

**Recommendation**: **REMOVE** - No real-time features in current dashboard

## Specific Cleanup Recommendations

### Immediate Actions (High Priority)

1. **Remove `useSchoolDashboard` Hook Auto-refresh**
   ```typescript
   // In frontend-ui/hooks/useSchoolDashboard.ts
   // Remove or comment out the metrics and activity fetching
   ```

2. **Deprecate Metrics API Endpoint**
   ```python
   # In backend/accounts/views.py
   @action(detail=True, methods=['get'], url_path='metrics')
   def metrics(self, request, pk=None):
       return Response({
           "deprecated": True,
           "message": "This endpoint is deprecated as of Issue #130"
       }, status=status.HTTP_410_GONE)
   ```

3. **Simplify Activity API**
   ```python
   @action(detail=True, methods=['get'], url_path='activity')  
   def activity(self, request, pk=None):
       return Response({
           "count": 0,
           "next": None,
           "previous": None,
           "results": [],
           "message": "Activity feed coming soon"
       })
   ```

### Code Removal (Medium Priority)

1. **Remove WebSocket Infrastructure**
   - Delete `SchoolDashboardConsumer` class
   - Remove WebSocket routing for dashboard
   - Delete `SchoolDashboardBroadcaster` utility

2. **Remove Metrics Service Components**
   - Delete or deprecate `SchoolMetricsService` class
   - Remove `SchoolActivityService.get_activity_feed()` method
   - Clean up related serializers and tests

3. **Database Query Optimization**
   - Remove complex aggregation queries in metrics calculation
   - Simplify activity queries or remove entirely

### Testing and Validation (Low Priority)

1. **Update Tests**
   - Remove or update tests for deprecated endpoints
   - Add tests for simplified responses
   - Ensure no breaking changes for other features

2. **Monitoring**
   - Track API call reduction after changes
   - Monitor for any unexpected errors from removed endpoints

## Risk Assessment

### Low Risk ✅
- **Metrics API removal**: No UI dependencies
- **WebSocket removal**: No frontend consumers
- **Activity API simplification**: UI already shows placeholder

### Medium Risk ⚠️
- **Notifications API**: May be used by other components
- **Database migrations**: If removing models/fields

### High Risk ❌
- **None identified** - This cleanup is safe for current dashboard implementation

## Estimated Impact

### Performance Improvements
- **Database Load**: Reduce complex metric calculations every 30 seconds
- **Cache Usage**: Free up cache space from unused metrics data
- **Network Traffic**: Eliminate ~726 bytes every 30 seconds per active user
- **CPU Cycles**: Remove unnecessary service layer calculations

### Maintenance Benefits
- **Code Simplification**: Remove ~500 lines of unused metrics service code
- **Test Maintenance**: Reduce test suite by removing deprecated endpoint tests
- **API Clarity**: Clear separation between active and deprecated endpoints

## Implementation Timeline

1. **Week 1**: Frontend hook modifications (immediate relief)
2. **Week 2**: Backend API deprecation (graceful degradation)
3. **Week 3**: Code removal and cleanup (long-term maintenance)
4. **Week 4**: Testing and validation (quality assurance)

## Coordination Required

- **Frontend Team**: Confirm no hidden dependencies on metrics/activity data
- **QA Team**: Verify dashboard functionality after API changes
- **DevOps**: Monitor API usage patterns after cleanup

---

**Next Steps**: Prioritize frontend hook modification to immediately stop unnecessary API calls, then proceed with backend deprecation in a controlled manner.