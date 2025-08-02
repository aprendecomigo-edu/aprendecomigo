# Tailwind Safelist Audit Findings
*Generated: 2025-01-02*

## Current Safelist Analysis
Current minimal safelist in `tailwind.config.js`:
```javascript
safelist: ['gap-x-2', 'gap-y-6', 'pl-4', 'flex-wrap', 'mb-12', 'basis-[10%]']
```

## Critical Dynamic Class Patterns Found

### 1. Color-based Dynamic Classes
**Files with `bg-${color}-{number}` patterns:**
- `/components/dashboard/QuickActionsPanel.tsx`: 
  - Colors: green, blue, purple, orange, indigo, teal, gray
  - Pattern: `border-${action.color}-200 bg-${action.color}-50 hover:bg-${action.color}-100`
- `/components/dashboard/ActivityFeed.tsx`:
  - Pattern: `bg-${color}-100`
- `/components/ui/file-upload/FileUploadProgress.tsx`:
  - Colors: blue, green, red, gray
  - Pattern: `bg-${getStatusColor()}-600`

**Files with `text-${color}-{number}` patterns:**
- `/components/tutor-dashboard/TutorMetricsCard.tsx`: `text-${color}-600`
- `/components/student/dashboard/DashboardOverview.tsx`: 
  - Colors: primary, secondary, tertiary, success
  - Pattern: `text-${action.color}-600`
- `/components/student/dashboard/TransactionHistory.tsx`: `text-${typeConfig.color}-600`
- `/components/dashboard/ActivityFeed.tsx`: `text-${color}-600`
- `/components/dashboard/MetricsCard.tsx`: `text-${color}-600`

### 2. Template Literal Patterns
**Files with extensive template literal concatenation:**
- 80+ instances of `className={\`${variable} other-classes\`}` patterns across:
  - `/components/invitations/SchoolStats.tsx`
  - `/components/invitations/InvitationErrorDisplay.tsx`
  - `/components/teacher-dashboard/PerformanceAnalytics.tsx`
  - `/components/wizard/` directory (multiple files)
  - `/screens/onboarding/` directory (multiple files)

### 3. Function-generated Classes
**Files with color generation functions:**
- `/components/invitations/SchoolStats.tsx`: `getStatColor()` returns combinations like:
  - `text-green-600 bg-green-50`
  - `text-blue-600 bg-blue-50`
  - `text-yellow-600 bg-yellow-50`
  - `text-red-600 bg-red-50`
  - `text-gray-600 bg-gray-50`

## Color Palette Used in Dynamic Classes
**Standard colors:** red, green, blue, yellow, orange, purple, indigo, teal, gray
**Custom colors:** primary, secondary, tertiary, success, error, warning, info
**Shades:** 50, 100, 200, 300, 400, 500, 600, 700, 800, 900

## Risk Assessment
- **HIGH RISK**: Dynamic color interpolation could be purged in production
- **MEDIUM RISK**: Template literal classes might not be detected by Tailwind's purge scanner
- **LOW RISK**: Function-generated classes are static and should be detected

## Recommended Classes for Safelist
All combinations of the following patterns need to be included.