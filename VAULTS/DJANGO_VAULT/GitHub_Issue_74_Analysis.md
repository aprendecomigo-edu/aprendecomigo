# GitHub Issue #74: Individual Tutor Platform Enhancements - Backend Analysis

**Date**: 2025-01-31
**Issue**: Backend support for individual tutors (Flow B)

## Current State Analysis

### Existing Models (75-80% complete)
- ✅ **TeacherProfile**: Enhanced with structured data fields, completion tracking
- ✅ **Course**: Educational system-aware course management
- ✅ **ClassSession**: Comprehensive session tracking with hour deduction
- ✅ **School**: Multi-tenant school model (individual tutors create schools)
- ✅ **SchoolMembership**: Role-based access control
- ✅ **TeacherInvitation**: Enhanced invitation system with analytics
- ✅ **StudentAccountBalance**: Hour-based billing system
- ✅ **PurchaseTransaction**: Stripe-integrated payment tracking

### Existing APIs
- ✅ `/api/accounts/courses/` - Basic course listing
- ✅ `/api/accounts/teachers/` - Teacher management
- ✅ `/api/accounts/schools/` - School management
- ✅ `/api/finances/` - Basic financial models

### Missing Components for Issue #74

#### 1. Tutor Analytics API (`/api/finances/tutor-analytics/`)
**Purpose**: Business metrics for individual tutors
**Data needed**:
- Revenue trends over time
- Session completion rates
- Student retention metrics
- Course performance analytics
- Monthly/weekly earnings breakdown

#### 2. Enhanced Course Catalog API
**Purpose**: Advanced filtering and market data for course selection
**Enhancements needed**:
- Market demand indicators
- Pricing suggestions
- Competition analysis
- Advanced filtering (education level, system, popularity)
- Search functionality

#### 3. Tutor Discovery API (`/api/accounts/tutors/discover/`)
**Purpose**: Public endpoint for students to find tutors
**Features needed**:
- Public tutor profiles
- Course/subject filtering
- Rate range filtering
- Availability filtering
- Location-based search
- Rating/review integration

#### 4. Performance Optimizations
**Areas**:
- Database indexing for analytics queries
- Caching for course catalog
- Query optimization for discovery endpoint
- Efficient aggregations for metrics

## Implementation Plan

### Phase 1: Analytics Foundation
1. Create analytics service classes
2. Add database indexes for performance
3. Implement tutor analytics API
4. Add caching layer

### Phase 2: Enhanced Course Catalog
1. Add market data calculations
2. Enhance filtering capabilities
3. Implement search functionality
4. Add caching for course data

### Phase 3: Tutor Discovery
1. Create public tutor discovery endpoint
2. Implement filtering and search
3. Add privacy controls
4. Performance optimization

### Phase 4: Enhanced Invitations
1. Tutor-specific invitation templates
2. Invitation analytics tracking
3. Performance metrics

## Database Schema Changes

### New Indexes Needed
```sql
-- Analytics performance
CREATE INDEX idx_class_session_teacher_date ON finances_classsession(teacher_id, date);
CREATE INDEX idx_class_session_school_status ON finances_classsession(school_id, status);
CREATE INDEX idx_purchase_transaction_student_created ON finances_purchasetransaction(student_id, created_at);

-- Course catalog performance
CREATE INDEX idx_course_educational_system_level ON accounts_course(educational_system_id, education_level);
CREATE INDEX idx_teacher_course_active ON accounts_teachercourse(is_active, teacher_id);

-- Discovery performance
CREATE INDEX idx_teacher_profile_completion ON accounts_teacherprofile(is_profile_complete, profile_completion_score);
CREATE INDEX idx_school_membership_role_active ON accounts_schoolmembership(role, is_active, school_id);
```

### New Models (if needed)
- Potential `TutorMarketData` model for caching market analytics
- Potential `CoursePopularity` model for tracking course demand

## API Endpoints to Implement

### 1. `/api/finances/tutor-analytics/`
- **Method**: GET
- **Permission**: Teacher for own school
- **Parameters**: time_range, metrics_type
- **Response**: Revenue, sessions, students, trends

### 2. `/api/accounts/courses/` (Enhanced)
- **Method**: GET
- **Permission**: Public/Authenticated
- **Parameters**: education_system, level, search, include_market_data
- **Response**: Courses with market data, pricing suggestions

### 3. `/api/accounts/tutors/discover/`
- **Method**: GET
- **Permission**: Public
- **Parameters**: subjects, rate_min, rate_max, availability, location
- **Response**: Public tutor profiles with basic info

### 4. `/api/accounts/teacher-invitations/` (Enhanced)
- **Method**: POST, GET
- **Features**: Bulk operations, analytics, templates

## Security Considerations

1. **Data Privacy**: Discovery API should only expose public profile data
2. **School Isolation**: Analytics must be school-scoped
3. **Rate Limiting**: Discovery API needs aggressive rate limiting
4. **Sensitive Data**: Ensure no personal info leaks in public endpoints

## Testing Strategy

1. **Unit Tests**: Service classes, model methods
2. **Integration Tests**: API endpoints with realistic data
3. **Performance Tests**: Analytics queries under load
4. **Security Tests**: Data isolation, permission enforcement

## Dependencies

- Django REST Framework (existing)
- Django Cache Framework (for performance)
- Existing authentication system
- Existing school/teacher models