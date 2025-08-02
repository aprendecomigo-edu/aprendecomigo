# Dashboard Redesign - User Stories & Issues

**Date:** August 2, 2025  
**Status:** Analysis Complete - Ready for Development  
**Priority:** High (B2B Value Proposition Critical)

## Current Problems Analysis

### Major Issues Identified:
1. **Design System Violations**: Dashboard doesn't follow styling guidelines
2. **Broken Navigation**: Sidebar navigation is not functional
3. **Unnecessary Features**: Real-time updates, search, metrics clutter
4. **Poor Information Architecture**: Wrong content hierarchy
5. **Technical Debt**: Placeholder components, commented imports

## User Stories

### Epic 1: Clean Dashboard Foundation
**As a school administrator, I want a clean, professional dashboard that reflects our platform's quality so that I trust the platform for managing my school.**

#### Story 1.1: Remove Unnecessary Features
```
As a school administrator
I want the dashboard to show only essential information
So that I can focus on what matters most for daily operations

Acceptance Criteria:
- Remove "Resumo Rápido" metrics section entirely
- Remove search functionality from header
- Remove real-time updates warning message
- Remove WebSocket connection status indicators
- Clean up all placeholder content
```

#### Story 1.2: Fix Navigation
```
As a school administrator  
I want a properly functioning sidebar navigation
So that I can easily navigate between different sections

Acceptance Criteria:
- Fix broken sidebar navigation styling
- Apply proper design system patterns (glass-nav, proper spacing)
- Remove unnecessary breadcrumb navigation (Home > school-admin > Dashboard)
- Ensure navigation works on all platforms (web, iOS, Android)
```

#### Story 1.3: Apply Design System
```
As a school administrator
I want the dashboard to follow our professional design guidelines
So that the platform looks trustworthy and modern

Acceptance Criteria:
- Apply bg-gradient-page to main background
- Use glass-container for main content areas
- Apply proper typography (font-primary for headings, font-body for content)
- Use feature-card-gradient for Quick Actions items
- Remove all custom styling that violates design system
```

### Epic 2: Essential Content Implementation
**As a school administrator, I want to see the most important information at a glance so that I can manage my school efficiently.**

#### Story 2.1: Upcoming Events Table
```
As a school administrator
I want to see upcoming classes and events in a table format
So that I can stay on top of my school's schedule

Acceptance Criteria:
- Create a clean table showing upcoming events/classes
- Include filters for: Today, This Week, This Month
- Show: Date/Time, Subject, Teacher, Student, Status
- Use glass-container styling
- Replace the current ActivityFeed placeholder
- No real-time updates - simple static data
```

#### Story 2.2: To-Do Task List
```
As a school administrator
I want a personal to-do list on my dashboard
So that I can track important tasks and follow-ups

Acceptance Criteria:
- Create a simple to-do list component
- Allow adding, completing, and removing tasks
- Use glass-light styling for individual tasks
- Show task priority and due dates
- Replace one of the placeholder content areas
```

### Epic 3: Quick Actions Redesign
**As a school administrator, I want streamlined access to common actions so that I can complete routine tasks efficiently.**

#### Story 3.1: Redesign Quick Actions
```
As a school administrator
I want the Quick Actions section to look professional and be easy to use
So that I can quickly perform common administrative tasks

Acceptance Criteria:
- Apply feature-card-gradient styling to each action item
- Use proper design system colors for different action types
- Improve spacing and layout using design system patterns
- Ensure hover and active states work properly
- Remove any custom color schemes that aren't in design system
```

### Epic 4: School Selector Fix
**As a school administrator with multiple schools, I want a working school selector so that I can switch between my schools easily.**

#### Story 4.1: Fix School Dropdown
```
As a school administrator
I want the school selector dropdown to work properly
So that I can switch between my schools when I manage multiple institutions

Acceptance Criteria:
- Fix broken school dropdown functionality
- Apply proper design system styling
- Show clear visual feedback for selected school
- Ensure it works on all platforms
```

## Technical Issues for Developers

### Issue #1: Remove Real-Time Infrastructure
**Priority:** High  
**Files Affected:** 
- `hooks/useSchoolDashboard.ts`
- `app/(school-admin)/dashboard/index.tsx`

**Tasks:**
- Remove WebSocket connection logic from useSchoolDashboard hook
- Remove enableRealtime parameter and related code
- Remove wsError and isConnected state
- Remove real-time update warning messages
- Clean up WebSocket message handlers

### Issue #2: Clean Up Placeholder Components  
**Priority:** High  
**Files Affected:**
- `app/(school-admin)/dashboard/index.tsx`

**Tasks:**
- Remove placeholder MetricsCard, ActivityFeed, SchoolInfoCard components
- Remove commented import statements (lines 17-18, 133-134)
- Clean up temporary debugging code

### Issue #3: Remove Metrics Section
**Priority:** High  
**Files Affected:**
- `app/(school-admin)/dashboard/index.tsx`
- `hooks/useSchoolDashboard.ts`

**Tasks:**
- Remove "Resumo Rápido" section (lines 487-520)
- Remove metrics fetching from useSchoolDashboard hook
- Remove metrics state and related API calls
- Clean up metric-related imports

### Issue #4: Remove Search Functionality
**Priority:** High  
**Files Affected:**
- `app/(school-admin)/dashboard/index.tsx`
- Main layout components

**Tasks:**
- Remove search input from header
- Clean up search-related state and handlers
- Remove search icons and related imports

### Issue #5: Apply Design System Patterns
**Priority:** High  
**Files Affected:**
- `app/(school-admin)/dashboard/index.tsx`

**Tasks:**
- Replace `bg-gray-50` with `bg-gradient-page`
- Apply `glass-nav` to navigation elements
- Use `glass-container` for main content areas
- Apply `feature-card-gradient` to Quick Actions
- Fix typography with proper font classes
- Remove custom gradient (lines 489: `bg-gradient-to-r from-blue-500 to-purple-600`)

### Issue #6: Implement Upcoming Events Table
**Priority:** Medium  
**Files Needed:**
- New component: `components/dashboard/UpcomingEventsTable.tsx`

**Requirements:**
- Create table with filtering capabilities
- Use design system patterns
- Replace ActivityFeed placeholder
- Static data initially (no real-time)

### Issue #7: Implement To-Do List Component
**Priority:** Medium  
**Files Needed:**
- New component: `components/dashboard/TodoList.tsx`

**Requirements:**
- Simple task management
- Use glass-light for task items
- Local state management initially

### Issue #8: Fix School Selector
**Priority:** High  
**Files Affected:**
- `app/(school-admin)/dashboard/index.tsx`
- `components/multi-school/SchoolSwitcher.tsx`

**Tasks:**
- Fix dropdown functionality (lines 381-399)
- Apply proper design system styling
- Ensure cross-platform compatibility

## Validation Criteria

### Design System Compliance
- [ ] No custom gradients or colors outside design system
- [ ] Proper use of glass effects and typography
- [ ] Consistent spacing and layout patterns
- [ ] Cross-platform compatibility verified

### Functionality
- [ ] Dashboard loads without placeholder content
- [ ] Navigation works properly
- [ ] School selector functions correctly
- [ ] Quick Actions navigate to correct pages
- [ ] No console errors or warnings

### Performance
- [ ] No unnecessary real-time connections
- [ ] Fast loading without WebSocket overhead
- [ ] Proper error handling for API calls
- [ ] Mobile-responsive layout

## Success Metrics
- Professional appearance that builds trust
- Faster dashboard load times (no WebSocket)
- Reduced user confusion (focused content)
- Improved task completion rates for school admins