# Teacher Invitation System API Documentation

## Overview

The Teacher Invitation System provides a comprehensive API for managing teacher invitations to schools within the Aprende Comigo platform. This system supports email-based invitations, generic invitation links, profile creation during acceptance, and real-time status tracking.

## Base URL

```
https://api.aprendecomigo.com/api/accounts/teacher-invitations/
```

## Authentication

The invitation endpoints use a combination of authentication methods:

- **Token-based**: Invitation operations (accept, decline, status) use the invitation token for authorization
- **JWT Authentication**: Admin operations require valid JWT tokens
- **Knox Authentication**: Session-based authentication for authenticated users

## Rate Limiting

All endpoints are protected by rate limiting:

- **IP-based**: 100 requests per minute per IP address
- **User-based**: 50 requests per minute per authenticated user
- **Invitation operations**: 10 requests per minute per invitation token

## Error Response Format

All error responses follow a standardized format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Optional additional context
    }
  },
  "timestamp": "2025-08-01T10:30:00Z",
  "path": "/api/accounts/teacher-invitations/abc123/accept/"
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVITATION_NOT_FOUND` | Invitation token invalid or not found | 404 |
| `INVITATION_EXPIRED` | Invitation has expired | 400 |
| `INVITATION_ALREADY_ACCEPTED` | Invitation already accepted | 400 |
| `INVITATION_ALREADY_DECLINED` | Invitation already declined | 400 |
| `INVITATION_INVALID_RECIPIENT` | Invitation not for authenticated user | 403 |
| `AUTHENTICATION_REQUIRED` | Authentication required | 401 |
| `VALIDATION_FAILED` | Request data validation failed | 400 |
| `PROFILE_CREATION_FAILED` | Teacher profile creation failed | 500 |

## Endpoints

### 1. Accept Teacher Invitation

Accept a teacher invitation and create/update teacher profile.

```http
POST /api/accounts/teacher-invitations/{token}/accept/
```

#### Request Body

```json
{
  "bio": "Experienced mathematics teacher with passion for helping students",
  "specialty": "Mathematics, Physics", 
  "hourly_rate": 45.00,
  "phone_number": "+1234567890",
  "address": "123 Main St, City, Country",
  "teaching_subjects": ["Mathematics", "Physics", "Calculus"],
  "education_background": {
    "degree": "Masters in Mathematics",
    "university": "University Name",
    "graduation_year": 2018,
    "certifications": ["Teaching Certificate", "Mathematics Specialist"]
  },
  "teaching_experience": {
    "years": 5,
    "description": "5 years teaching high school mathematics",
    "previous_schools": ["High School A", "High School B"]
  },
  "rate_structure": {
    "base_rate": 45.00,
    "group_discount": 0.15,
    "package_discount": 0.10
  },
  "weekly_availability": {
    "monday": ["09:00-12:00", "14:00-17:00"],
    "tuesday": ["09:00-12:00"],
    "wednesday": ["14:00-17:00"],
    "thursday": ["09:00-12:00", "14:00-17:00"],
    "friday": ["09:00-12:00"]
  },
  "grade_level_preferences": ["9th", "10th", "11th", "12th"],
  "credentials_documents": [
    {
      "type": "degree",
      "filename": "masters_degree.pdf",
      "url": "https://storage.example.com/docs/masters_degree.pdf"
    }
  ]
}
```

#### Success Response (200 OK)

```json
{
  "success": true,
  "invitation_accepted": true,
  "teacher_profile": {
    "id": 123,
    "bio": "Experienced mathematics teacher...",
    "specialty": "Mathematics, Physics",
    "hourly_rate": 45.00,
    "profile_completion_score": 85.5,
    "is_profile_complete": false
  },
  "school_membership": {
    "id": 456,
    "school": {
      "id": 789,
      "name": "Test School"
    },
    "role": "teacher",
    "is_active": true,
    "joined_at": "2025-08-01T10:30:00Z"
  },
  "wizard_metadata": {
    "next_steps": ["complete_profile", "upload_documents"],
    "completion_percentage": 75,
    "required_fields": ["credentials_documents"]
  }
}
```

#### Error Responses

**400 Bad Request - Validation Error**
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Invalid teacher profile data provided",
    "details": {
      "field_errors": {
        "hourly_rate": ["Ensure this value is less than or equal to 200."],
        "phone_number": ["Enter a valid phone number."]
      },
      "non_field_errors": ["Bio and specialty cannot both be empty."]
    }
  },
  "timestamp": "2025-08-01T10:30:00Z",
  "path": "/api/accounts/teacher-invitations/abc123/accept/"
}
```

**401 Unauthorized - Authentication Required**
```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication required to accept invitation",
    "details": {
      "invitation_details": {
        "school_name": "Test School",
        "email": "teacher@example.com",
        "expires_at": "2025-08-08T10:30:00Z",
        "role": "Teacher"
      }
    }
  },
  "timestamp": "2025-08-01T10:30:00Z",
  "path": "/api/accounts/teacher-invitations/abc123/accept/"
}
```

### 2. Decline Teacher Invitation

Decline a teacher invitation with optional reason.

```http
POST /api/accounts/teacher-invitations/{token}/decline/
```

#### Request Body

```json
{
  "reason": "Not interested at this time" // Optional, max 500 characters
}
```

#### Success Response (200 OK)

```json
{
  "success": true,
  "invitation_declined": true,
  "message": "Invitation declined successfully",
  "invitation_details": {
    "school_name": "Test School",
    "role": "teacher",
    "declined_at": "2025-08-01T10:30:00Z"
  }
}
```

### 3. Get Invitation Status

Check the current status of a teacher invitation.

```http
GET /api/accounts/teacher-invitations/{token}/status/
```

#### Success Response (200 OK)

```json
{
  "status": "pending",
  "status_display": "Pending",
  "invitation_details": {
    "email": "teacher@example.com",
    "school_name": "Test School",
    "role": "teacher",
    "role_display": "Teacher",
    "created_at": "2025-08-01T09:00:00Z",
    "expires_at": "2025-08-08T09:00:00Z",
    "is_valid": true,
    "is_expired": false,
    "is_accepted": false,
    "accepted_at": null,
    "declined_at": null,
    "viewed_at": "2025-08-01T10:30:00Z",
    "custom_message": "Welcome to our school!"
  },
  "email_delivery": {
    "status": "delivered",
    "status_display": "Delivered",
    "sent_at": "2025-08-01T09:05:00Z",
    "delivered_at": "2025-08-01T09:06:00Z",
    "failure_reason": null,
    "retry_count": 0
  },
  "user_context": {
    "is_authenticated": true,
    "is_intended_recipient": true,
    "can_accept": true,
    "can_decline": true
  }
}
```

## Status Values

| Status | Description |
|--------|-------------|
| `pending` | Invitation created but not yet sent |
| `sent` | Email successfully sent to recipient |
| `delivered` | Email confirmed delivered |
| `viewed` | Recipient has viewed the invitation |
| `accepted` | Invitation accepted by recipient |
| `declined` | Invitation declined by recipient |
| `expired` | Invitation has expired |
| `cancelled` | Invitation cancelled by sender |

## Integration Examples

### JavaScript/Frontend Integration

```javascript
// Accept invitation with profile data
async function acceptInvitation(token, profileData) {
  try {
    const response = await fetch(`/api/accounts/teacher-invitations/${token}/accept/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userToken}` // User must be authenticated
      },
      body: JSON.stringify(profileData)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`${errorData.error.code}: ${errorData.error.message}`);
    }
    
    const result = await response.json();
    console.log('Invitation accepted successfully:', result);
    return result;
    
  } catch (error) {
    console.error('Failed to accept invitation:', error);
    throw error;
  }
}

// Check invitation status (no authentication required)
async function checkInvitationStatus(token) {
  try {
    const response = await fetch(`/api/accounts/teacher-invitations/${token}/status/`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`${errorData.error.code}: ${errorData.error.message}`);
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('Failed to check invitation status:', error);
    throw error;
  }
}

// Decline invitation (no authentication required)
async function declineInvitation(token, reason = '') {
  try {
    const response = await fetch(`/api/accounts/teacher-invitations/${token}/decline/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ reason })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`${errorData.error.code}: ${errorData.error.message}`);
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('Failed to decline invitation:', error);
    throw error;
  }
}
```

### Python/Backend Integration

```python
import requests
from typing import Dict, Any, Optional

class TeacherInvitationAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def accept_invitation(self, token: str, profile_data: Dict[str, Any], 
                         user_token: str) -> Dict[str, Any]:
        """Accept a teacher invitation with profile data."""
        url = f"{self.base_url}/api/accounts/teacher-invitations/{token}/accept/"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {user_token}'
        }
        
        response = requests.post(url, json=profile_data, headers=headers)
        
        if not response.ok:
            error_data = response.json()
            raise Exception(f"{error_data['error']['code']}: {error_data['error']['message']}")
        
        return response.json()
    
    def check_status(self, token: str) -> Dict[str, Any]:
        """Check invitation status (no authentication required)."""
        url = f"{self.base_url}/api/accounts/teacher-invitations/{token}/status/"
        
        response = requests.get(url)
        
        if not response.ok:
            error_data = response.json()
            raise Exception(f"{error_data['error']['code']}: {error_data['error']['message']}")
        
        return response.json()
    
    def decline_invitation(self, token: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Decline a teacher invitation."""
        url = f"{self.base_url}/api/accounts/teacher-invitations/{token}/decline/"
        data = {'reason': reason} if reason else {}
        
        response = requests.post(url, json=data)
        
        if not response.ok:
            error_data = response.json()
            raise Exception(f"{error_data['error']['code']}: {error_data['error']['message']}")
        
        return response.json()

# Usage example
api = TeacherInvitationAPI('https://api.aprendecomigo.com')

# Check invitation status
status = api.check_status('abc123token')
print(f"Invitation status: {status['status']}")

# Accept invitation (requires authentication)
profile_data = {
    'bio': 'Experienced teacher',
    'specialty': 'Mathematics',
    'hourly_rate': 45.00
}
result = api.accept_invitation('abc123token', profile_data, 'user_jwt_token')
print(f"Invitation accepted: {result['success']}")
```

## Validation Rules

### Profile Data Validation

| Field | Type | Rules | Required |
|-------|------|-------|----------|
| `bio` | string | Max 1000 characters | No |
| `specialty` | string | Max 200 characters | No |
| `hourly_rate` | number | 5.00 - 200.00 | No |
| `phone_number` | string | Valid international format | No |
| `address` | string | Max 500 characters | No |
| `teaching_subjects` | array | Max 10 items, each max 100 chars | No |
| `education_background` | object | See nested rules | No |
| `teaching_experience` | object | See nested rules | No |
| `weekly_availability` | object | Valid time slots | No |
| `grade_level_preferences` | array | Valid grade levels | No |

### Education Background Rules

| Field | Type | Rules | Required |
|-------|------|-------|----------|
| `degree` | string | Max 200 characters | No |
| `university` | string | Max 200 characters | No |
| `graduation_year` | integer | 1950 - current year + 1 | No |
| `certifications` | array | Max 10 items | No |

### Teaching Experience Rules

| Field | Type | Rules | Required |
|-------|------|-------|----------|
| `years` | integer | 0 - 50 | No |
| `description` | string | Max 1000 characters | No |
| `previous_schools` | array | Max 20 items | No |

## Security Considerations

### Token Security
- Invitation tokens are single-use for acceptance/decline
- Tokens expire after 7 days by default
- Tokens are cryptographically secure (64 character random strings)
- All token operations should use HTTPS

### Rate Limiting
- IP-based rate limiting prevents abuse
- Per-token rate limiting prevents token spam
- Exponential backoff recommended for failed requests

### Data Validation
- All input data is sanitized and validated
- File uploads are scanned for malware
- Profile data is encrypted at rest

### Authentication
- JWT tokens required for acceptance (user must be authenticated)
- Email verification ensures user owns the email address
- Multi-factor authentication supported

## Testing

### Unit Tests

```python
# Example unit test for invitation acceptance
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import TeacherInvitation, School

class TestTeacherInvitationAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        self.invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            token="test_token_123"
        )
    
    def test_accept_invitation_success(self):
        # Authenticate user
        user = self.create_authenticated_user("teacher@example.com")
        self.client.force_authenticate(user=user)
        
        profile_data = {
            "bio": "Test bio",
            "specialty": "Mathematics",
            "hourly_rate": 45.00
        }
        
        response = self.client.post(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/",
            data=profile_data,
            format="json"
        )
        
        assert response.status_code == 200
        assert response.data["success"] == True
        assert response.data["invitation_accepted"] == True
    
    def test_invitation_not_found(self):
        response = self.client.get(
            "/api/accounts/teacher-invitations/invalid_token/status/"
        )
        
        assert response.status_code == 404
        assert response.data["error"]["code"] == "INVITATION_NOT_FOUND"
```

### Integration Tests

```bash
# Test invitation acceptance flow
curl -X POST "https://api.aprendecomigo.com/api/accounts/teacher-invitations/abc123/accept/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "bio": "Experienced mathematics teacher",
    "specialty": "Mathematics",
    "hourly_rate": 45.00
  }'

# Test invitation status check
curl -X GET "https://api.aprendecomigo.com/api/accounts/teacher-invitations/abc123/status/"

# Test invitation decline
curl -X POST "https://api.aprendecomigo.com/api/accounts/teacher-invitations/abc123/decline/" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Not interested at this time"
  }'
```

## Support and Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure JWT token is valid and not expired
   - Verify user email matches invitation email
   - Check token format: `Bearer <token>`

2. **Validation Errors**
   - Check field length limits
   - Verify data types match requirements
   - Ensure required fields are provided

3. **Rate Limiting**
   - Implement exponential backoff
   - Check rate limit headers in response
   - Use appropriate delays between requests

### Contact Information

- **API Support**: api-support@aprendecomigo.com
- **Documentation Issues**: docs@aprendecomigo.com
- **Security Issues**: security@aprendecomigo.com

## Changelog

### Version 1.2.0 (2025-08-01)
- **Added**: Standardized error response format
- **Added**: Comprehensive OpenAPI documentation
- **Added**: Enhanced profile creation during acceptance
- **Added**: Wizard orchestration metadata
- **Improved**: Error handling and validation
- **Fixed**: Authentication flow consistency

### Version 1.1.0 (2025-07-15)
- **Added**: Invitation decline endpoint
- **Added**: Email delivery status tracking
- **Added**: Bulk invitation management
- **Improved**: Rate limiting implementation

### Version 1.0.0 (2025-07-01)
- **Initial**: Teacher invitation system release
- **Added**: Accept invitation endpoint
- **Added**: Invitation status endpoint
- **Added**: JWT authentication integration