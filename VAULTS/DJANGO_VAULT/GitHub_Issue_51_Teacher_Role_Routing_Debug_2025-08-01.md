# GitHub Issue #51: Teacher Role Routing Debug Investigation

**Date**: 2025-08-01
**Status**: Investigation in Progress
**Priority**: Critical

## Problem Summary

Teachers who should have teacher role are being incorrectly routed to the school-admin dashboard (`/dashboard`) instead of the teacher dashboard (`/(teacher)/dashboard`). This prevents teachers from accessing teacher-specific functionality.

## Investigation Plan

1. **Teacher Profile Creation Process**
   - Check invitation acceptance flow
   - Verify user_type assignment
   - Check role assignment logic

2. **Authentication System Analysis**
   - Review login/authentication API responses
   - Check user_type field values
   - Verify JWT token content

3. **School Membership & Permissions**
   - Check SchoolMembership creation
   - Verify role assignments
   - Check permission system

4. **API Endpoint Testing**
   - Test teacher-specific endpoints
   - Verify data returned for teachers
   - Check permission filtering

## Debugging Steps

### Step 1: Analyze Current Authentication System
- Review User model and user_type field
- Check authentication views
- Analyze role assignment logic

### Step 2: Test Teacher Creation Flow
- Test invitation acceptance
- Check database state after acceptance
- Verify user profile creation

### Step 3: Debug API Responses
- Test authentication endpoints
- Check user data returned
- Verify role information

## Root Cause Identified

**Issue**: The `user_type` field was removed from the User model (line 177 in models.py) and replaced with a `SchoolMembership` system. However, the authentication endpoint (`VerifyCodeView`) still returns the old `UserSerializer` data which doesn't include the `user_type` field that the frontend expects for routing.

**Key Findings**:
1. The User model no longer has a `user_type` field
2. User roles are now managed through `SchoolMembership` model with roles like `TEACHER`, `SCHOOL_OWNER`, etc.
3. Authentication endpoint (`/api/accounts/verify-code/`) returns `UserSerializer` data without `user_type`
4. A separate `/api/users/dashboard_info/` endpoint correctly calculates `user_type` from roles but isn't called during authentication
5. Frontend expects `user_type` field in authentication response for routing decisions

## Solution Required

**Fix Authentication Response**: Modify the `VerifyCodeView` to return user type information similar to how the `dashboard_info` endpoint does it. This includes:
- Calculate `user_type` from `SchoolMembership` records
- Include role information in authentication response
- Ensure backward compatibility with frontend expectations

## Files to Modify

- `backend/accounts/views.py` - `VerifyCodeView` (lines 832-837)
- `backend/accounts/serializers.py` - Create/modify serializer for auth response

## Implementation Completed

### Changes Made

1. **Created AuthenticationResponseSerializer** (`backend/accounts/serializers.py`, lines 538+):
   - Extends `UserWithRolesSerializer` to include role information
   - Adds `user_type` field that calculates type from `SchoolMembership` records
   - Adds `is_admin` field for admin privilege detection
   - Uses same logic as `dashboard_info` endpoint for consistency

2. **Updated VerifyCodeView** (`backend/accounts/views.py`, lines 832-837):
   - Changed from `UserSerializer` to `AuthenticationResponseSerializer`
   - Added import for new serializer
   - Now returns user_type and role information in authentication response

3. **Logic Implementation**:
   - School owners/admins get `user_type = "admin"` -> routed to `/dashboard`
   - Teachers get `user_type = "teacher"` -> routed to `/(teacher)/dashboard`
   - Students get `user_type = "student"` -> routed to student dashboard
   - Includes complete role information for context

### API Response Structure

**Before Fix**:
```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "email": "teacher@school.com",
    "name": "Teacher Name",
    "is_student": false,
    "is_teacher": true
  }
}
```

**After Fix**:
```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "email": "teacher@school.com", 
    "name": "Teacher Name",
    "is_student": false,
    "is_teacher": true,
    "user_type": "teacher",
    "is_admin": false,
    "roles": [
      {
        "school": {"id": 1, "name": "School Name"},
        "role": "teacher",
        "role_display": "Teacher"
      }
    ]
  }
}
```

### Testing Status

- ✅ Server reloads successfully with changes
- ✅ Authentication endpoints are accessible
- ✅ Validation errors work correctly
- 🔄 End-to-end authentication flow needs verification with real teacher account

### Expected Result

Teachers will now be correctly routed to `/(teacher)/dashboard` instead of being incorrectly routed to the school-admin dashboard (`/dashboard`).