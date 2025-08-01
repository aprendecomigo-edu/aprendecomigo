# Teacher Invitation Acceptance Analysis - GitHub Issue #49

## Current Status Assessment

### What Exists ✅
1. **Backend Infrastructure** (Complete):
   - `SchoolInvitation` model with proper validation
   - `TeacherInvitation` model with enhanced features (bulk processing, tracking)
   - `InvitationViewSet` with `accept` and `details` endpoints
   - `TeacherInvitationViewSet` with comprehensive management
   - Token-based invitation system with expiration
   - User authentication and authorization

2. **Frontend Infrastructure** (Partially Complete):
   - Invitation acceptance page at `/app/accept-invitation/[token].tsx`
   - Comprehensive API client (`invitationApi.ts`)
   - React hooks for invitation management (`useInvitations.ts`)
   - UI components using Gluestack UI

### Critical Issues Identified ❌

1. **API Endpoint Mismatch**:
   - Frontend uses: `teacher-invitations/${token}/status/` and `teacher-invitations/${token}/accept/`
   - Backend has: `invitations/${token}/details/` and `invitations/${token}/accept/`
   - **Result**: API calls are failing, causing 100% drop-off

2. **Missing Authentication Handling**:
   - Current flow assumes user is already authenticated
   - No handling for new users who need to sign up first
   - No bridge between invitation acceptance and user creation

3. **Incomplete Profile Setup**:
   - No teacher profile wizard integration after acceptance
   - Missing compensation preference setup
   - No subject/grade level selection

4. **Missing User Flow Integration**:
   - No decline functionality
   - No proper redirect to dashboard after acceptance
   - No email confirmation handling

## Required Fixes for 100% Drop-Off Resolution

### 1. Fix API Endpoint Routing (CRITICAL)
- Update frontend API calls to match backend endpoints
- Ensure proper token-based authentication
- Add proper error handling for API failures

### 2. Implement Authentication Bridge (CRITICAL)
- Handle new user registration via invitation
- Integrate with existing auth flow
- Manage user creation + invitation acceptance in single transaction

### 3. Add Profile Setup Wizard (HIGH)
- Integrate teacher profile completion after acceptance
- Add subject selection, grade levels, availability
- Include compensation preference setup

### 4. Complete User Experience (HIGH)
- Add decline invitation functionality
- Implement proper navigation after acceptance
- Add email confirmation system
- Handle expired token scenarios gracefully

## Action Plan for Implementation

### Phase 1: Fix Critical API Issues
1. Update `invitationApi.ts` endpoints
2. Fix authentication flow for invitation acceptance
3. Test basic accept/decline functionality

### Phase 2: Enhance User Experience
1. Add teacher profile setup wizard
2. Implement proper authentication bridge
3. Add decline functionality and error handling

### Phase 3: Complete Integration
1. Add dashboard redirect after acceptance
2. Implement email confirmation
3. End-to-end testing of entire flow

## Backend Endpoints Reference

Based on `accounts/urls.py` and `accounts/views.py`:
- Invitation details: `GET /api/accounts/invitations/{token}/details/` (AllowAny)
- Accept invitation: `POST /api/accounts/invitations/{token}/accept/` (Authenticated)
- Teacher invitations: `GET /api/accounts/teacher-invitations/` (with status filtering)

## Frontend Component Architecture

Current structure works well, just needs:
1. API endpoint corrections
2. Authentication state management
3. Profile wizard integration
4. Navigation improvements

The core issue is the API mismatch - once fixed, the foundation is solid for completing the full invitation flow.