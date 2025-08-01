# GitHub Issue #80: Backend API Documentation and Error Message Standardization Analysis

## Current State Analysis

### Existing Invitation API Endpoints

Based on my analysis of the codebase, here are the current invitation-related endpoints:

#### 1. SchoolInvitation API (InvitationViewSet)
- **Base URL**: `/api/accounts/invitations/`
- **Model**: `SchoolInvitation`
- **Lookup Field**: `token`
- **Current Actions**:
  - `POST /api/accounts/invitations/{token}/accept/` - Accept invitation

#### 2. TeacherInvitation API (TeacherInvitationViewSet)  
- **Base URL**: `/api/accounts/teacher-invitations/`
- **Model**: `TeacherInvitation`
- **Lookup Field**: `token`
- **Current Actions**:
  - `POST /api/accounts/teacher-invitations/{token}/accept/` - Accept invitation
  - `POST /api/accounts/teacher-invitations/{token}/decline/` - Decline invitation
  - `GET /api/accounts/teacher-invitations/{token}/status/` - Check status
  - `GET /api/accounts/teacher-invitations/` - List (admin only)

#### 3. SchoolInvitationLink API
- **Base URL**: `/api/accounts/invitation-links/`
- **Model**: `SchoolInvitationLink`
- **Current Actions**:
  - `GET /api/accounts/invitation-links/{token}/` - Get link details

### Current Error Handling Patterns

#### Inconsistent Error Response Formats
1. **Manual Dictionary Responses**:
   ```python
   return Response(
       {"error": "Invalid invitation token"},
       status=status.HTTP_404_NOT_FOUND,
   )
   ```

2. **Serializer Error Responses**:
   ```python
   return Response(
       {
           "error": "Invalid profile data provided",
           "errors": profile_serializer.errors
       },
       status=status.HTTP_400_BAD_REQUEST,
   )
   ```

3. **Mixed Response Structures**:
   - Some endpoints return `{"error": "message"}`
   - Others return `{"error": "message", "errors": {...}}`
   - Some include additional context like `invitation_details`

#### Authentication Error Handling
- Inconsistent authentication error messages
- Some endpoints return invitation details for unauthenticated users
- Missing rate limiting documentation

### Current Documentation State

#### Missing Documentation
1. **No centralized API documentation** in `backend/docs/`
2. **Limited docstrings** in view methods
3. **No OpenAPI schema annotations** for invitation endpoints
4. **No error response examples**
5. **No authentication requirement documentation**
6. **No rate limiting documentation**

#### Existing Swagger Setup
- Basic Swagger UI configured at `/api/swagger/`
- Uses `drf-yasg` for OpenAPI schema generation
- Currently relies on Django REST Framework's automatic schema generation

## Key Issues Identified

### 1. Error Response Standardization
- **Problem**: Multiple different error response formats
- **Impact**: Frontend team cannot reliably handle errors
- **Priority**: High

### 2. Missing API Documentation
- **Problem**: No comprehensive documentation for invitation endpoints
- **Impact**: Frontend development blocked, integration issues
- **Priority**: High

### 3. Authentication Documentation
- **Problem**: Unclear authentication requirements per endpoint
- **Impact**: Security vulnerabilities, poor UX
- **Priority**: Medium

### 4. Rate Limiting Documentation
- **Problem**: No documentation of throttling behavior
- **Impact**: Unexpected API failures, poor error handling
- **Priority**: Medium

## Recommendations

### 1. Create Standardized Error Response Format
```python
class StandardErrorResponse:
    """
    {
        "error": {
            "code": "INVITATION_NOT_FOUND",
            "message": "The invitation token is invalid or has expired",
            "details": {...}  # Optional additional context
        },
        "timestamp": "2025-08-01T10:30:00Z",
        "path": "/api/accounts/teacher-invitations/abc123/accept/"
    }
    """
```

### 2. Implement Error Response Serializers
- Create base error serializers for common error types
- Standardize validation error responses
- Implement proper HTTP status code mapping

### 3. Add OpenAPI Schema Annotations
- Use `drf_yasg.utils.swagger_auto_schema` decorators
- Document request/response schemas
- Add example payloads

### 4. Create Comprehensive Documentation
- API endpoint documentation with examples
- Authentication requirements per endpoint
- Rate limiting behavior
- Error handling guide

## Implementation Plan

1. **Create standardized error response serializers**
2. **Update all invitation views with proper error handling**
3. **Add comprehensive docstrings and OpenAPI annotations**
4. **Generate complete API documentation**
5. **Create integration testing examples**

This analysis provides the foundation for implementing GitHub Issue #80 requirements.