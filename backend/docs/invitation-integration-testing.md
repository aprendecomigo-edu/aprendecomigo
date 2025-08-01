# Teacher Invitation System - Integration Testing Guide

## Overview

This guide provides comprehensive integration testing examples for the Teacher Invitation System, including test scenarios, expected responses, and best practices for testing invitation flows.

## Test Environment Setup

### Prerequisites

```bash
# Backend API running
python manage.py runserver

# Test database with sample data
python manage.py migrate
python manage.py loaddata test_fixtures.json

# Test user accounts
python manage.py create_teacher_test_user
```

### Test Configuration

```python
# Django test settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Rate limiting disabled for tests
TESTING = True
THROTTLE_TESTING = True
```

## Test Scenarios

### Scenario 1: Complete Invitation Acceptance Flow

This scenario tests the complete flow from invitation creation to acceptance with profile creation.

#### Step 1: Create Test Invitation

```python
# Create test invitation (backend operation)
from accounts.models import School, TeacherInvitation
from django.contrib.auth import get_user_model

User = get_user_model()

# Create test school and admin user
school = School.objects.create(
    name="Test High School",
    description="A test school for integration testing",
    contact_email="admin@testschool.com"
)

admin_user = User.objects.create_user(
    email="admin@testschool.com",
    name="School Admin"
)

# Create teacher invitation
invitation = TeacherInvitation.objects.create(
    school=school,
    email="teacher@example.com",
    invited_by=admin_user,
    role="teacher",
    custom_message="Welcome to our school! We're excited to have you join our team."
)

print(f"Invitation token: {invitation.token}")
```

#### Step 2: Check Initial Status

```bash
curl -X GET "http://localhost:8000/api/accounts/teacher-invitations/${TOKEN}/status/" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "status": "pending",
  "status_display": "Pending",
  "invitation_details": {
    "email": "teacher@example.com",
    "school_name": "Test High School",
    "role": "teacher",
    "role_display": "Teacher",
    "created_at": "2025-08-01T10:00:00Z",
    "expires_at": "2025-08-08T10:00:00Z",
    "is_valid": true,
    "is_expired": false,
    "custom_message": "Welcome to our school! We're excited to have you join our team."
  },
  "user_context": {
    "is_authenticated": false,
    "is_intended_recipient": false,
    "can_accept": false,
    "can_decline": true
  }
}
```

#### Step 3: Attempt Acceptance Without Authentication

```bash
curl -X POST "http://localhost:8000/api/accounts/teacher-invitations/${TOKEN}/accept/" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Experienced mathematics teacher",
    "specialty": "Mathematics",
    "hourly_rate": 45.00
  }'
```

**Expected Response (401 Unauthorized):**
```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication required to accept invitation",
    "details": {
      "invitation_details": {
        "school_name": "Test High School",
        "email": "teacher@example.com",
        "expires_at": "2025-08-08T10:00:00Z",
        "role": "Teacher"
      }
    }
  },
  "timestamp": "2025-08-01T10:30:00Z",
  "path": "/api/accounts/teacher-invitations/abc123/accept/"
}
```

#### Step 4: Create and Authenticate Teacher User

```python
# Create teacher user account
teacher_user = User.objects.create_user(
    email="teacher@example.com",
    name="Jane Teacher"
)

# Generate JWT token for testing
from knox.models import AuthToken
token, key = AuthToken.objects.create(teacher_user)
print(f"JWT Token: {key}")
```

#### Step 5: Accept Invitation with Authentication

```bash
curl -X POST "http://localhost:8000/api/accounts/teacher-invitations/${INVITATION_TOKEN}/accept/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token ${JWT_TOKEN}" \
  -d '{
    "bio": "Experienced mathematics teacher with 5 years of teaching experience. Passionate about helping students understand complex mathematical concepts through interactive learning.",
    "specialty": "Mathematics, Algebra, Calculus",
    "hourly_rate": 45.00,
    "phone_number": "+1234567890",
    "address": "123 Main Street, City, State 12345",
    "teaching_subjects": ["Mathematics", "Algebra", "Calculus", "Statistics"],
    "education_background": {
      "degree": "Masters in Mathematics Education",
      "university": "State University",
      "graduation_year": 2018,
      "certifications": ["Teaching License", "Mathematics Specialist Certification"]
    },
    "teaching_experience": {
      "years": 5,
      "description": "5 years teaching high school mathematics at various institutions",
      "previous_schools": ["Central High School", "Westside Academy"]
    },
    "weekly_availability": {
      "monday": ["09:00-12:00", "14:00-17:00"],
      "tuesday": ["09:00-12:00", "14:00-17:00"],
      "wednesday": ["14:00-17:00"],
      "thursday": ["09:00-12:00", "14:00-17:00"],
      "friday": ["09:00-12:00"]
    },
    "grade_level_preferences": ["9th", "10th", "11th", "12th"]
  }'
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "invitation_accepted": true,
  "teacher_profile": {
    "id": 123,
    "bio": "Experienced mathematics teacher with 5 years...",
    "specialty": "Mathematics, Algebra, Calculus",
    "hourly_rate": 45.00,
    "phone_number": "+1234567890",
    "profile_completion_score": 92.5,
    "is_profile_complete": true,
    "teaching_subjects": ["Mathematics", "Algebra", "Calculus", "Statistics"],
    "education_background": {
      "degree": "Masters in Mathematics Education",
      "university": "State University"
    }
  },
  "school_membership": {
    "id": 456,
    "school": {
      "id": 789,
      "name": "Test High School"
    },
    "role": "teacher",
    "is_active": true,
    "joined_at": "2025-08-01T10:30:00Z"
  },
  "wizard_metadata": {
    "next_steps": [],
    "completion_percentage": 92,
    "required_fields": []
  }
}
```

#### Step 6: Verify Final Status

```bash
curl -X GET "http://localhost:8000/api/accounts/teacher-invitations/${TOKEN}/status/" \
  -H "Authorization: Token ${JWT_TOKEN}"
```

**Expected Response:**
```json
{
  "status": "accepted",
  "status_display": "Accepted",
  "invitation_details": {
    "email": "teacher@example.com",
    "school_name": "Test High School",
    "is_accepted": true,
    "accepted_at": "2025-08-01T10:30:00Z"
  },
  "user_context": {
    "is_authenticated": true,
    "is_intended_recipient": true,
    "can_accept": false,
    "can_decline": false
  }
}
```

### Scenario 2: Invitation Decline Flow

This scenario tests declining an invitation with optional reason.

#### Step 1: Create Test Invitation

```python
decline_invitation = TeacherInvitation.objects.create(
    school=school,
    email="teacher2@example.com",
    invited_by=admin_user,
    role="teacher",
    custom_message="Join our mathematics department!"
)
```

#### Step 2: Check Status

```bash
curl -X GET "http://localhost:8000/api/accounts/teacher-invitations/${DECLINE_TOKEN}/status/"
```

#### Step 3: Decline with Reason

```bash
curl -X POST "http://localhost:8000/api/accounts/teacher-invitations/${DECLINE_TOKEN}/decline/" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "I have accepted a position elsewhere. Thank you for the opportunity."
  }'
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "invitation_declined": true,
  "message": "Invitation declined successfully",
  "invitation_details": {
    "school_name": "Test High School",
    "role": "teacher",
    "declined_at": "2025-08-01T11:00:00Z"
  }
}
```

#### Step 4: Verify Decline Status

```bash
curl -X GET "http://localhost:8000/api/accounts/teacher-invitations/${DECLINE_TOKEN}/status/"
```

**Expected Response:**
```json
{
  "status": "declined",
  "status_display": "Declined",
  "invitation_details": {
    "declined_at": "2025-08-01T11:00:00Z",
    "is_accepted": false
  },
  "user_context": {
    "can_accept": false,
    "can_decline": false
  }
}
```

### Scenario 3: Error Handling Tests

#### Test 3.1: Invalid Token

```bash
curl -X GET "http://localhost:8000/api/accounts/teacher-invitations/invalid_token_123/status/"
```

**Expected Response (404 Not Found):**
```json
{
  "error": {
    "code": "INVITATION_NOT_FOUND",
    "message": "The invitation token is invalid or does not exist"
  },
  "timestamp": "2025-08-01T12:00:00Z",
  "path": "/api/accounts/teacher-invitations/invalid_token_123/status/"
}
```

#### Test 3.2: Expired Invitation

```python
# Create expired invitation
from datetime import timedelta
from django.utils import timezone

expired_invitation = TeacherInvitation.objects.create(
    school=school,
    email="expired@example.com",
    invited_by=admin_user,
    role="teacher",
    expires_at=timezone.now() - timedelta(days=1)  # Expired yesterday
)
```

```bash
curl -X POST "http://localhost:8000/api/accounts/teacher-invitations/${EXPIRED_TOKEN}/accept/" \
  -H "Authorization: Token ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"bio": "Test bio"}'
```

**Expected Response (400 Bad Request):**
```json
{
  "error": {
    "code": "INVITATION_EXPIRED",
    "message": "This invitation has expired and is no longer valid",
    "details": {
      "expired_at": "2025-07-31T12:00:00Z"
    }
  },
  "timestamp": "2025-08-01T12:00:00Z",
  "path": "/api/accounts/teacher-invitations/expired123/accept/"
}
```

#### Test 3.3: Validation Errors

```bash
curl -X POST "http://localhost:8000/api/accounts/teacher-invitations/${TOKEN}/accept/" \
  -H "Authorization: Token ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "hourly_rate": 500.00,
    "phone_number": "invalid-phone",
    "bio": ""
  }'
```

**Expected Response (400 Bad Request):**
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Invalid teacher profile data provided",
    "details": {
      "field_errors": {
        "hourly_rate": ["Ensure this value is less than or equal to 200."],
        "phone_number": ["Enter a valid phone number format."]
      }
    }
  },
  "timestamp": "2025-08-01T12:00:00Z",
  "path": "/api/accounts/teacher-invitations/abc123/accept/"
}
```

#### Test 3.4: Wrong Recipient

```python
# Create user with different email
wrong_user = User.objects.create_user(
    email="wrong@example.com",
    name="Wrong User"
)
wrong_token, wrong_key = AuthToken.objects.create(wrong_user)
```

```bash
curl -X POST "http://localhost:8000/api/accounts/teacher-invitations/${TOKEN}/accept/" \
  -H "Authorization: Token ${WRONG_JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"bio": "Test bio"}'
```

**Expected Response (403 Forbidden):**
```json
{
  "error": {
    "code": "INVITATION_INVALID_RECIPIENT",
    "message": "This invitation is not intended for your account",
    "details": {
      "expected_email": "teacher@example.com"
    }
  },
  "timestamp": "2025-08-01T12:00:00Z",
  "path": "/api/accounts/teacher-invitations/abc123/accept/"
}
```

### Scenario 4: Rate Limiting Tests

#### Test 4.1: IP Rate Limiting

```bash
# Send multiple requests quickly to trigger rate limiting
for i in {1..10}; do
  curl -X GET "http://localhost:8000/api/accounts/teacher-invitations/${TOKEN}/status/" &
done
wait
```

**Expected Response (429 Too Many Requests):**
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "retry_after": 60,
      "limit": "100/minute"
    }
  },
  "timestamp": "2025-08-01T12:00:00Z",
  "path": "/api/accounts/teacher-invitations/abc123/status/"
}
```

## Automated Test Suite

### Django Unit Tests

```python
# tests/test_invitation_integration.py
import json
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import School, TeacherInvitation
from knox.models import AuthToken

User = get_user_model()

class TeacherInvitationIntegrationTest(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test school and admin
        self.school = School.objects.create(
            name="Integration Test School",
            contact_email="admin@testschool.com"
        )
        
        self.admin_user = User.objects.create_user(
            email="admin@testschool.com",
            name="Test Admin"
        )
        
        # Create teacher user
        self.teacher_user = User.objects.create_user(
            email="teacher@example.com",
            name="Test Teacher"
        )
        
        # Create teacher JWT token
        self.token, self.key = AuthToken.objects.create(self.teacher_user)
        
        # Create test invitation
        self.invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="teacher@example.com",
            invited_by=self.admin_user,
            role="teacher",
            custom_message="Test invitation"
        )
    
    def test_complete_acceptance_flow(self):
        """Test complete invitation acceptance flow."""
        
        # Step 1: Check initial status
        response = self.client.get(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/status/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "pending")
        self.assertFalse(response.data["user_context"]["is_authenticated"])
        
        # Step 2: Attempt acceptance without auth (should fail)
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"]["code"], "AUTHENTICATION_REQUIRED")
        
        # Step 3: Authenticate and accept
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.key}')
        
        response = self.client.post(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/",
            data=profile_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertTrue(response.data["invitation_accepted"])
        
        # Step 4: Verify final status
        response = self.client.get(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/status/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "accepted")
        self.assertTrue(response.data["user_context"]["is_authenticated"])
        self.assertTrue(response.data["user_context"]["is_intended_recipient"])
        
        # Verify profile was created
        self.teacher_user.refresh_from_db()
        self.assertTrue(hasattr(self.teacher_user, 'teacher_profile'))
        
        # Verify school membership was created
        membership = self.teacher_user.school_memberships.filter(school=self.school).first()
        self.assertIsNotNone(membership)
        self.assertTrue(membership.is_active)
    
    def test_decline_flow(self):
        """Test invitation decline flow."""
        
        # Check initial status
        response = self.client.get(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/status/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["user_context"]["can_decline"])
        
        # Decline with reason
        decline_data = {
            "reason": "Not interested at this time"
        }
        
        response = self.client.post(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/decline/",
            data=decline_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertTrue(response.data["invitation_declined"])
        
        # Verify final status
        response = self.client.get(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/status/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "declined")
        self.assertFalse(response.data["user_context"]["can_accept"])
        self.assertFalse(response.data["user_context"]["can_decline"])
    
    def test_error_scenarios(self):
        """Test various error scenarios."""
        
        # Test invalid token
        response = self.client.get(
            "/api/accounts/teacher-invitations/invalid_token/status/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"]["code"], "INVITATION_NOT_FOUND")
        
        # Test wrong recipient
        wrong_user = User.objects.create_user(
            email="wrong@example.com",
            name="Wrong User"
        )
        wrong_token, wrong_key = AuthToken.objects.create(wrong_user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {wrong_key}')
        
        response = self.client.post(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/",
            data={"bio": "Test"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "INVITATION_INVALID_RECIPIENT")
        
        # Test validation errors
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.key}')
        
        invalid_data = {
            "hourly_rate": 500.00,  # Too high
            "phone_number": "invalid"  # Invalid format
        }
        
        response = self.client.post(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/",
            data=invalid_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_FAILED")
        self.assertIn("field_errors", response.data["error"]["details"])

    def test_double_acceptance_prevention(self):
        """Test that invitations cannot be accepted twice."""
        
        # Accept invitation first time
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.key}')
        
        profile_data = {"bio": "Test bio", "specialty": "Math"}
        
        response = self.client.post(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/",
            data=profile_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to accept again (should fail)
        response = self.client.post(
            f"/api/accounts/teacher-invitations/{self.invitation.token}/accept/",
            data=profile_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "INVITATION_ALREADY_ACCEPTED")
```

### Running Integration Tests

```bash
# Run all integration tests
python manage.py test tests.test_invitation_integration

# Run specific test method
python manage.py test tests.test_invitation_integration.TeacherInvitationIntegrationTest.test_complete_acceptance_flow

# Run with verbose output
python manage.py test tests.test_invitation_integration -v 2

# Run with coverage
coverage run --source='.' manage.py test tests.test_invitation_integration
coverage report
```

## Performance Testing

### Load Testing with Apache Bench

```bash
# Test status endpoint performance
ab -n 100 -c 10 http://localhost:8000/api/accounts/teacher-invitations/test_token/status/

# Test with authentication headers
ab -n 50 -c 5 -H "Authorization: Token test_token_here" \
  -p profile_data.json -T application/json \
  http://localhost:8000/api/accounts/teacher-invitations/test_token/accept/
```

### Load Testing with Python

```python
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def test_invitation_status(session, token):
    """Test single invitation status check."""
    url = f"http://localhost:8000/api/accounts/teacher-invitations/{token}/status/"
    async with session.get(url) as response:
        return await response.json()

async def load_test_status_endpoint(num_requests=100, concurrency=10):
    """Load test the status endpoint."""
    connector = aiohttp.TCPConnector(limit=concurrency)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Create test tokens
        tokens = [f"test_token_{i}" for i in range(num_requests)]
        
        start_time = time.time()
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_test(token):
            async with semaphore:
                return await test_invitation_status(session, token)
        
        # Run all requests
        tasks = [bounded_test(token) for token in tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Analyze results
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        
        print(f"Load Test Results:")
        print(f"Total Requests: {num_requests}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Requests/second: {num_requests/duration:.2f}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        return results

# Run load test
if __name__ == "__main__":
    asyncio.run(load_test_status_endpoint(100, 10))
```

## Monitoring and Metrics

### Key Metrics to Track

1. **Response Times**
   - Accept invitation: < 2 seconds
   - Status check: < 500ms
   - Decline invitation: < 1 second

2. **Success Rates**
   - Invitation acceptance: > 95%
   - Status checks: > 99%
   - Error handling: 100% standardized format

3. **Error Rates**
   - 4xx errors: < 5% (excluding expected validation errors)
   - 5xx errors: < 1%
   - Rate limiting: Track and adjust limits

### Monitoring Setup

```python
# Custom Django middleware for metrics
import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('invitation_metrics')

class InvitationMetricsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if '/teacher-invitations/' in request.path:
            request._invitation_start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, '_invitation_start_time'):
            duration = time.time() - request._invitation_start_time
            
            logger.info(
                'invitation_request',
                extra={
                    'path': request.path,
                    'method': request.method,
                    'status_code': response.status_code,
                    'duration_ms': duration * 1000,
                    'user_authenticated': request.user.is_authenticated,
                }
            )
        
        return response
```

## Troubleshooting Guide

### Common Issues and Solutions

1. **Authentication Failures**
   - **Symptom**: 401 Unauthorized responses
   - **Check**: JWT token format, expiration, user email match
   - **Solution**: Regenerate token, verify user account

2. **Validation Errors**
   - **Symptom**: 400 Bad Request with field errors
   - **Check**: Data types, field lengths, required fields
   - **Solution**: Review validation rules, fix input data

3. **Rate Limiting**
   - **Symptom**: 429 Too Many Requests
   - **Check**: Request frequency, IP address, user limits
   - **Solution**: Implement backoff, optimize request patterns

4. **Database Errors**
   - **Symptom**: 500 Internal Server Error
   - **Check**: Database connections, migrations, constraints
   - **Solution**: Check logs, verify database state

### Debug Commands

```bash
# Check invitation status in database
python manage.py shell -c "
from accounts.models import TeacherInvitation
inv = TeacherInvitation.objects.get(token='your_token_here')
print(f'Status: {inv.status}')
print(f'Valid: {inv.is_valid()}')
print(f'Expires: {inv.expires_at}')
"

# Verify user authentication
python manage.py shell -c "
from django.contrib.auth import get_user_model
from knox.models import AuthToken
User = get_user_model()
user = User.objects.get(email='teacher@example.com')
tokens = AuthToken.objects.filter(user=user)
print(f'Active tokens: {tokens.count()}')
"

# Check school membership
python manage.py shell -c "
from accounts.models import SchoolMembership
membership = SchoolMembership.objects.filter(
    user__email='teacher@example.com'
).first()
if membership:
    print(f'School: {membership.school.name}')
    print(f'Role: {membership.role}')
    print(f'Active: {membership.is_active}')
else:
    print('No membership found')
"
```

This comprehensive integration testing guide provides everything needed to test the Teacher Invitation System thoroughly, from basic functionality to error handling and performance testing.