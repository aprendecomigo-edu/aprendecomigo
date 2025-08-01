# Tutor Business Management Dashboard - Implementation Plan
*Created: 2025-07-31*

## Analysis Summary

### Current Codebase Structure
- **Existing Dashboard Pattern**: School admin dashboard at `app/(school-admin)/dashboard/index.tsx`
- **API Integration**: Comprehensive `tutorApi.ts` with analytics, onboarding, and discovery APIs
- **Component Library**: Gluestack UI with established patterns for MetricsCard, QuickActionsPanel, etc.
- **Navigation**: Expo Router with group-based routing

### Available Backend APIs (Ready to Use)
- `/api/finances/tutor-analytics/<school_id>/` - Complete business analytics
- `/api/accounts/courses/` - Enhanced course catalog with market data  
- `/api/accounts/tutors/discover/` - Public tutor discovery
- Standard session, student, and payment APIs

### Implementation Strategy
1. **Create tutor route group**: `app/(tutor)/` to mirror school-admin structure
2. **Reuse existing components**: Adapt MetricsCard, QuickActionsPanel for tutor context
3. **Custom tutor components**: StudentAcquisition, BusinessAnalytics, SessionManagement
4. **Data hooks**: Custom hooks for tutor-specific data fetching

## File Structure Plan

```
frontend-ui/
├── app/(tutor)/                          # New tutor route group
│   ├── _layout.tsx                      # Tutor layout with navigation  
│   ├── dashboard/
│   │   └── index.tsx                    # Main tutor dashboard
│   ├── students/
│   │   ├── index.tsx                    # Student management
│   │   └── [id].tsx                     # Individual student detail
│   ├── analytics/
│   │   └── index.tsx                    # Business analytics dashboard
│   ├── sessions/
│   │   └── index.tsx                    # Session management 
│   └── acquisition/
│       └── index.tsx                    # Student acquisition tools
├── components/tutor-dashboard/           # Tutor-specific components
│   ├── TutorMetricsCard.tsx             # Business metrics display
│   ├── StudentAcquisitionHub.tsx        # Invitation management
│   ├── RevenueAnalytics.tsx             # Financial insights
│   ├── SessionCalendar.tsx              # Calendar with session mgmt
│   └── StudentProgressTracker.tsx       # Progress tracking
├── components/student-acquisition/       # Acquisition tools
│   ├── InvitationManager.tsx            # Multiple invitation methods
│   ├── ShareableLinkGenerator.tsx       # Branded invitation links
│   └── AcquisitionAnalytics.tsx         # Conversion tracking
└── hooks/
    ├── useTutorAnalytics.ts             # Business analytics hook
    ├── useTutorStudents.ts              # Student management hook
    └── useStudentAcquisition.ts         # Acquisition tools hook
```

## Key Components to Build

### 1. Main Dashboard (CRITICAL)
- Business metrics overview (students, sessions, earnings)
- Quick action panel (invite students, schedule sessions)
- Recent activity feed
- Revenue trends chart

### 2. Student Acquisition Hub (CRITICAL) 
- Email invitation forms
- Shareable link generation with QR codes
- Invitation tracking and conversion analytics
- Social media sharing tools

### 3. Student Management (HIGH PRIORITY)
- Enhanced student directory with tutor-relevant info
- Progress tracking with goals and milestones
- Communication history
- Session booking management

### 4. Business Analytics (HIGH PRIORITY)
- Revenue trends and forecasting
- Subject-wise performance breakdown
- Acquisition funnel analysis
- Teaching performance insights

### 5. Session Management (MEDIUM PRIORITY)
- Calendar view with availability management
- Session preparation and notes
- Billing and payment tracking
- Student attendance monitoring

## Technical Considerations

### Data Integration
- Leverage existing `getTutorAnalytics()` for comprehensive metrics
- Use enhanced course catalog APIs for subject management
- Integrate with existing session and payment systems

### UI/UX Patterns
- Follow school-admin dashboard layout patterns
- Mobile-first responsive design
- Consistent Gluestack UI component usage
- Professional tutor-focused styling

### Performance Requirements
- Page load <2s for main dashboard
- Real-time updates for session management
- Efficient data fetching with caching
- Cross-platform compatibility (web, iOS, Android)

## Implementation Priority

1. **Phase 1**: Main dashboard with core metrics
2. **Phase 2**: Student acquisition tools  
3. **Phase 3**: Business analytics and insights
4. **Phase 4**: Enhanced session/student management
5. **Phase 5**: Mobile optimization and testing

## Success Metrics
- Dashboard loads in <2s
- Student invitation conversion rate >15%
- User engagement with analytics features >60%
- Mobile usability score >4.5/5