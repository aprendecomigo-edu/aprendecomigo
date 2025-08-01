# GitHub Issue #49 - Backend Invitation System Analysis

**Date**: 2025-08-01  
**Issue**: Teacher invitation acceptance frontend implementation  
**Scope**: Backend API contract analysis for frontend development

## Executive Summary

The backend invitation system has **two distinct invitation models** with different endpoints and capabilities:

1. **SchoolInvitation** - Legacy system for general school invitations
2. **TeacherInvitation** - Enhanced system specifically for teacher invitations

**Key Finding**: The frontend should use the **TeacherInvitation** system (`/api/accounts/teacher-invitations/{token}/`) as it provides more comprehensive functionality for teacher onboarding.

## Current Backend State

### 1. Invitation Endpoints Available

#### TeacherInvitation System (Recommended)
- **Base URL**: `/api/accounts/teacher-invitations/{token}/`
- **Status Check**: `GET /api/accounts/teacher-invitations/{token}/status/` ✅
- **Accept**: `POST /api/accounts/teacher-invitations/{token}/accept/` ✅
- **Decline**: ❌ **NOT IMPLEMENTED** - needs backend work

#### SchoolInvitation System (Legacy)
- **Base URL**: `/api/accounts/invitations/{token}/`
- **Accept**: `POST /api/accounts/invitations/{token}/accept/` ✅
- **Decline**: `POST /api/accounts/invitations/{token}/decline/` ✅

### 2. TeacherInvitation Model Structure

```python
class TeacherInvitation(models.Model):
    # Core fields
    school = ForeignKey(School)
    email = EmailField()
    invited_by = ForeignKey(CustomUser)
    role = CharField(choices=SchoolRole.choices, default=TEACHER)
    
    # Enhanced fields
    custom_message = TextField(max_length=1000)
    batch_id = UUIDField()
    
    # Status tracking
    status = CharField(choices=InvitationStatus.choices)
    
    # Email delivery tracking
    email_delivery_status = CharField(choices=EmailDeliveryStatus.choices)
    email_sent_at = DateTimeField()
    email_delivered_at = DateTimeField()
    email_failure_reason = TextField()
    retry_count = PositiveSmallIntegerField(default=0)
    
    # Core invitation tracking
    token = CharField(max_length=64, unique=True)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()
    is_accepted = BooleanField(default=False)
    accepted_at = DateTimeField()
    viewed_at = DateTimeField()
```

### 3. Token Validation & Expiration

#### Token Generation
- **Algorithm**: `secrets.token_hex(32)` (64-character hex string)
- **Uniqueness**: Database constraint ensures uniqueness
- **Auto-generation**: Created on model save if not provided

#### Validation Logic (`invitation.is_valid()`)
```python
def is_valid(self) -> bool:
    if self.is_accepted:
        return False
    if timezone.now() > self.expires_at:
        return False
    if self.status in [CANCELLED, EXPIRED, DECLINED]:
        return False
    return True
```

#### Default Expiration
- **Duration**: 7 days from creation
- **Auto-set**: On model save if not provided

### 4. TeacherProfile Creation Flow

#### During Invitation Acceptance
```python
# Check if user already has teacher profile
if hasattr(request.user, "teacher_profile"):
    teacher_profile = request.user.teacher_profile
else:
    # Create comprehensive teacher profile
    teacher_profile = TeacherProfile.objects.create(
        user=request.user,
        bio=validated_data.get('bio', ''),
        specialty=validated_data.get('specialty', ''),
        hourly_rate=validated_data.get('hourly_rate'),
        # ... extensive field mapping
    )
```

#### Profile Creation Serializer
- **Serializer**: `ComprehensiveTeacherProfileCreationSerializer`
- **Supports**: File uploads, structured JSON data, extensive validation
- **Fields**: 20+ fields including bio, specialty, rates, availability, education, etc.

### 5. API Response Formats

#### Status Check Response (`GET /teacher-invitations/{token}/status/`)
```json
{
  "invitation": {
    "id": 123,
    "email": "teacher@example.com",
    "status": "pending",
    "is_accepted": false,
    "is_valid": true,
    "school": {
      "id": 1,
      "name": "Demo School",
      "description": "..."
    },
    "role": "teacher",
    "role_display": "Teacher",
    "invited_by": {
      "name": "School Admin",
      "email": "admin@school.com"
    },
    "created_at": "2025-08-01T10:00:00Z",
    "expires_at": "2025-08-08T10:00:00Z",
    "accepted_at": null,
    "viewed_at": "2025-08-01T10:30:00Z",
    "custom_message": "Welcome to our school!"
  },
  "email_delivery": {
    "status": "delivered",
    "sent_at": "2025-08-01T10:01:00Z",
    "delivered_at": "2025-08-01T10:02:00Z",
    "failure_reason": null,
    "retry_count": 0,
    "can_retry": false
  },
  "user_context": {
    "is_authenticated": true,
    "is_correct_user": true,
    "can_accept": true
  }
}
```

#### Successful Acceptance Response
```json
{
  "message": "Invitation accepted successfully! You are now a teacher at this school.",
  "teacher_profile": {
    "id": 456,
    "user": {...},
    "bio": "...",
    "specialty": "...",
    // ... full teacher profile data
  },
  "school_membership": {
    "id": 789,
    "school": {...},
    "role": "teacher",
    "is_active": true
  },
  "invitation": {
    "token": "abc123...",
    "is_accepted": true,
    "accepted_at": "2025-08-01T11:00:00Z"
  }
}
```

#### Error Response Examples
```json
// Invalid token
{
  "error": "Invalid invitation token"
}

// Expired invitation
{
  "error": "This invitation has expired or is no longer valid"
}

// Already accepted
{
  "error": "This invitation has already been accepted"
}

// Wrong user
{
  "error": "This invitation is not for your account"
}

// Not authenticated
{
  "error": "Authentication required to accept invitation",
  "invitation_details": {
    "school_name": "Demo School",
    "email": "teacher@example.com",
    "expires_at": "2025-08-08T10:00:00Z"
  }
}
```

## Backend Gaps Identified

### 1. Missing Decline Endpoint ❌
- **Gap**: TeacherInvitationViewSet has no `decline` action
- **Impact**: Frontend cannot allow users to decline invitations
- **Recommendation**: Implement decline action similar to SchoolInvitation

### 2. Authentication Requirements
- **Status Check**: `AllowAny` ✅ (Good for sharing links)
- **Accept**: `AllowAny` with email validation ✅
- **Decline**: Not implemented ❌

### 3. Permissions System
- **Current**: Token-based validation with email matching
- **Security**: Secure - requires correct user email
- **Public Access**: Status endpoint allows public viewing (good for sharing)

## Frontend Implementation Recommendations

### 1. Primary Endpoints to Use
```typescript
// Status check (public, no auth required)
GET /api/accounts/teacher-invitations/{token}/status/

// Accept invitation (requires auth + email match)
POST /api/accounts/teacher-invitations/{token}/accept/
Body: ComprehensiveTeacherProfileCreationSerializer data

// Decline - NEEDS BACKEND IMPLEMENTATION
POST /api/accounts/teacher-invitations/{token}/decline/
```

### 2. Flow Implementation
1. **Landing**: Use status endpoint to get invitation details
2. **Authentication**: Check user_context.can_accept
3. **Profile Form**: Use comprehensive serializer for rich profile creation
4. **Acceptance**: Submit full profile data with acceptance
5. **Decline**: **Backend work needed first**

### 3. Error Handling
- **Token validation**: Handle 404 for invalid tokens
- **Expiration**: Check is_valid field and expires_at
- **Authentication**: Handle 401 responses
- **Email mismatch**: Handle 403 responses

## Required Backend Work for Issue #49

### 1. Implement Decline Action ⚠️ **CRITICAL**
```python
@action(detail=True, methods=["post"], permission_classes=[AllowAny])
def decline(self, request, token=None):
    # Similar to SchoolInvitation.decline
    # Update status to DECLINED
    # Log activity
    # Return success response
```

### 2. Update Permissions (Optional)
- Consider if decline should require authentication
- Current accept flow allows unauthenticated users to see invitation details

### 3. Response Standardization (Optional)
- Ensure consistent error message formats
- Add more user-friendly error messages

## Security Considerations

### 1. Token Security ✅
- Cryptographically secure generation
- 64-character hex tokens
- Unique database constraint

### 2. Email Validation ✅
- Accepts only match invitation.email
- Prevents token hijacking

### 3. Expiration Handling ✅
- 7-day default expiration
- Proper validation in is_valid()

### 4. Status Tracking ✅
- Comprehensive status enum
- Audit trail with timestamps

## Conclusion

The backend invitation system is **85% ready** for frontend implementation. The TeacherInvitation system provides robust functionality with comprehensive profile creation support. 

**Only critical gap**: Missing decline action for TeacherInvitation.

**Recommendation**: Implement the decline action first, then proceed with frontend development using the TeacherInvitation endpoints.