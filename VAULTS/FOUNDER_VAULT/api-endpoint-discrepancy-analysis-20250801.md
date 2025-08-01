# Critical API Endpoint Discrepancy Analysis
*Date: 2025-08-01*
*Issue: 100% invitation drop-off rate investigation*

## Current Situation

### Frontend Implementation
The frontend uses these endpoints for invitation management:

1. **Get Status**: `GET /accounts/invitations/{token}/details/`
2. **Accept**: `POST /accounts/invitations/{token}/accept/`
3. **Decline**: `POST /accounts/invitations/{token}/decline/`

### Backend URL Configuration
From `accounts/urls.py`, we have two invitation systems:

1. **SchoolInvitation System** (older):
   - Router: `/api/accounts/invitations/` → `InvitationViewSet`
   - Uses `SchoolInvitation` model
   - Lookup field: `token`

2. **TeacherInvitation System** (newer):
   - Router: `/api/accounts/teacher-invitations/` → `TeacherInvitationViewSet` 
   - Uses `TeacherInvitation` model
   - Lookup field: `token`

## The Critical Issue

### Frontend Expected Endpoints:
- Status: `GET /accounts/invitations/{token}/details/`
- Accept: `POST /accounts/invitations/{token}/accept/`
- Decline: `POST /accounts/invitations/{token}/decline/`

### Actual Backend Endpoints (based on URL patterns):
- SchoolInvitation: `GET /api/accounts/invitations/{token}/details/`
- TeacherInvitation: `GET /api/accounts/teacher-invitations/{token}/`

**MISSING API PREFIX**: The frontend is missing the `/api/` prefix!

## Root Cause Analysis

1. **Missing API Prefix**: Frontend calls `/accounts/invitations/` but should call `/api/accounts/invitations/`
2. **Dual Systems**: We have both SchoolInvitation and TeacherInvitation systems running
3. **Method Mismatch**: Frontend expects `/details/` but TeacherInvitation uses standard REST endpoints

## Evidence from Code Investigation

### Frontend API Calls (invitationApi.ts):
```typescript
// Line 250: Status endpoint
static async getInvitationStatus(token: string): Promise<InvitationStatusResponse> {
  const response = await apiClient.get(`/accounts/invitations/${token}/details/`);
  return response.data;
}

// Line 270: Accept endpoint  
static async acceptInvitation(token: string, profileData?: TeacherProfileData): Promise<...> {
  const response = await apiClient.post(`/accounts/invitations/${token}/accept/`, profileData || {});
  return response.data;
}
```

### Backend Implementation:
- `InvitationViewSet` (SchoolInvitation) has `details()`, `accept()`, `decline()` methods
- `TeacherInvitationViewSet` uses standard REST patterns
- URL routing includes `/api/` prefix in main `urls.py`

## Systems Comparison

### SchoolInvitation System
- **Model**: `SchoolInvitation` 
- **Purpose**: General school invitations
- **Methods**: Custom `details()`, `accept()`, `decline()` actions
- **Status**: Appears to be the older system

### TeacherInvitation System  
- **Model**: `TeacherInvitation`
- **Purpose**: Specific teacher invitations with profile creation
- **Methods**: Standard REST + custom actions
- **Status**: Newer system with comprehensive profile support

## Impact Assessment

This API endpoint mismatch explains:
1. **100% drop-off rate**: Invitation acceptance fails due to wrong endpoints
2. **Frontend errors**: 404 responses from missing `/api/` prefix
3. **System confusion**: Two invitation systems causing conflicts

## Recommendations

See separate recommendation document.