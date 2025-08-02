# Teacher Profile Wizard Mobile Dropdown Fix Analysis

**Date:** 2025-08-02  
**Issue:** Critical mobile UI issues preventing dropdown interactions in Profile Wizard  
**Impact:** Mobile users cannot complete teacher onboarding - blocking ~40-60% of traffic

## Problem Analysis

### Critical Issues Identified
1. **Mobile dropdown interactions completely blocked** - Touch events intercepted by UI overlays
2. **Cannot complete wizard on mobile** due to inaccessible required form fields
3. **CSS z-index conflicts** preventing proper touch interaction with dropdowns

### Technical Root Cause
The QA report indicates that footer/navigation elements are overlaying form components, intercepting touch events that should reach dropdown elements. This appears to be a CSS z-index stacking context issue.

### Affected Components
- **BasicInformationStep.tsx**: Contact method preference dropdown
- **TeachingSubjectsStep.tsx**: Subject expertise level dropdown
- **Other wizard steps**: Likely all steps with Select components

### Current Implementation Analysis

The Select component uses ActionSheet for mobile interactions:
- Uses `@gluestack-ui/select` with ActionSheet portal
- ActionSheet content has `web:pointer-events-auto web:select-none`
- Backdrop uses `web:cursor-default web:pointer-events-auto`

### Z-Index Configuration Issues

**ActionSheet Components:**
- `actionsheetStyle`: `w-full h-full web:pointer-events-none`
- `actionsheetContentStyle`: `web:pointer-events-auto web:select-none shadow-lg`
- `actionsheetBackdropStyle`: `web:cursor-default web:pointer-events-auto`

**ProfileWizard Layout:**
- Footer navigation positioned with `border-t border-gray-200 px-6 py-4`
- No explicit z-index management visible

## Technical Fix Strategy

### 1. Z-Index Management
Need to ensure proper stacking order:
- ActionSheet Portal: z-index > Footer navigation
- ActionSheet Backdrop: High z-index for proper overlay
- ActionSheet Content: Higher than backdrop

### 2. Pointer Events Fix
- Ensure ActionSheet components receive touch events
- Prevent footer from intercepting mobile touches
- Fix web vs mobile pointer event handling

### 3. Mobile-Specific Optimization
- Add mobile-specific z-index classes
- Ensure proper touch target sizes (min 44px)
- Verify ActionSheet positioning on mobile viewports

## Implementation Plan

1. **Fix ActionSheet Z-Index**: Add explicit z-index classes to ActionSheet components
2. **Update Footer CSS**: Ensure footer doesn't interfere with modal overlays
3. **Mobile Touch Optimization**: Improve touch targets and interaction areas
4. **Cross-platform Testing**: Verify fixes work on iOS, Android, and web

## Business Impact
- **Revenue Risk**: Mobile users (40-60% of traffic) cannot complete onboarding
- **Teacher Acquisition**: Critical bottleneck in teacher signup funnel
- **User Experience**: Professional teachers expect mobile-friendly interfaces
- **Competitive Position**: Mobile-first design is table stakes for modern platforms

## Files to Modify
1. `/frontend-ui/components/ui/select/select-actionsheet.tsx`
2. `/frontend-ui/components/profile-wizard/ProfileWizard.tsx`
3. Possibly other wizard step components using Select

## Success Criteria
- ✅ Mobile dropdowns open and close properly
- ✅ Touch events reach correct elements
- ✅ Full wizard completion possible on mobile
- ✅ No regression on desktop functionality