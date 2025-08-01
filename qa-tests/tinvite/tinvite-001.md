# Teacher Invitation Acceptance QA Test
**Test ID**: TINVITE-001  
**Date**: 2025-08-01  
**Target**: Simplified Teacher Invitation System  
**Issue**: GitHub #52  

## Test Objective
Validate that the simplified teacher invitation acceptance system works correctly for core business requirements.

## Prerequisites
- ✅ Development environment running (localhost:8081)
- ✅ Backend API available (localhost:8000)
- ⏳ Valid teacher invitation token from backend
- ⏳ Invalid/expired token for error testing

## Test Scenarios

### Scenario 1: Valid Invitation Display
**URL**: `/accept-invitation/[valid-token]`
**Expected**: 
- Page loads without JavaScript errors
- Shows school name and invitation details
- Displays "Accept" and "Decline" buttons
- Shows invitation expiration date
- Shows who sent the invitation

### Scenario 2: Accept Invitation Flow
**URL**: `/accept-invitation/[valid-token]`
**Steps**:
1. Click "Accept" button
2. If not logged in, should prompt for authentication
3. If logged in, should show success message
4. Should redirect to appropriate dashboard

**Expected**:
- ✅ Button click responds
- ✅ Success message appears
- ✅ Navigation to dashboard works

### Scenario 3: Decline Invitation Flow  
**URL**: `/accept-invitation/[valid-token]`
**Steps**:
1. Click "Decline" button
2. Confirm decline in alert dialog
3. Should show decline confirmation

**Expected**:
- ✅ Confirmation dialog appears
- ✅ Decline processes successfully
- ✅ Clear confirmation message

### Scenario 4: Invalid Token Handling
**URL**: `/accept-invitation/invalid-token-123`
**Expected**:
- ✅ Shows clear error message
- ✅ No JavaScript console errors
- ✅ "Voltar ao Início" button works

### Scenario 5: Authentication Required
**URL**: `/accept-invitation/[valid-token]` (logged out)
**Expected**:
- ✅ Shows authentication prompt
- ✅ Login/signup buttons work
- ✅ Redirects back to invitation after auth

## Success Criteria
- [ ] All scenarios load without crashes
- [ ] No JavaScript console errors
- [ ] Accept/decline buttons functional
- [ ] Error handling works correctly  
- [ ] Navigation flows work properly
- [ ] Portuguese language displays correctly

## Mobile/Responsive Testing
- [ ] Layout works on mobile viewport
- [ ] Buttons are touch-friendly
- [ ] Text is readable on small screens
- [ ] No horizontal scrolling required

## Technical Validation
- [ ] API calls to `/api/accounts/teacher-invitations/{token}/status/` work
- [ ] Accept API call to `/api/accounts/teacher-invitations/{token}/accept/` works
- [ ] Decline API call to `/api/accounts/teacher-invitations/{token}/decline/` works
- [ ] Error responses handled gracefully

## Notes
This test focuses on the simplified implementation that replaced the complex 540+ line version with import/export issues. The goal is to validate that core business functionality works reliably.

## Test Execution Log
*To be filled during actual testing*

**Tester**: _____________________  
**Date**: _____________________  
**Status**: PENDING  
**Pass/Fail**: _____________________  
**Notes**: _____________________