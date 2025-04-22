# API Contract Documentation

This document serves as a contract between the backend and frontend teams, detailing the API endpoints, expected request/response formats, and authentication requirements.

## Quick Start

The API is accessible at the following URLs:

- Base API URL: `/api/`
- Swagger UI (interactive documentation): `/api/swagger/`
- ReDoc (more readable documentation): `/api/redoc/`

## Authentication

### Authentication Flow

The API uses a passwordless authentication system with time-based one-time passwords (TOTP):

1. **Request a verification code**:
   ```
   POST /api/auth/request-code/
   Content-Type: application/json

   {
     "email": "user@example.com"
   }
   ```

2. **Verify the code** (sent to the user's email):
   ```
   POST /api/auth/verify-code/
   Content-Type: application/json

   {
     "email": "user@example.com",
     "code": "123456"  // 6-digit code from email
   }
   ```

   Response includes a token:
   ```json
   {
     "user": {
       "id": 1,
       "email": "user@example.com",
       "name": "User Name",
       "phone_number": "",
       "user_type": "student",
       "created_at": "2023-01-01T00:00:00Z",
       "updated_at": "2023-01-01T00:00:00Z"
     },
     "token": "your-auth-token-here",
     "expiry": "2023-01-01T10:00:00Z"
   }
   ```

3. **Use the token for all subsequent requests**:
   ```
   GET /api/users/
   Authorization: Token your-auth-token-here
   ```

### Logout

To invalidate the current token:
```
POST /api/auth/logout/
Authorization: Token your-auth-token-here
```

To invalidate all tokens for the user:
```
POST /api/auth/logoutall/
Authorization: Token your-auth-token-here
```

## Core Resources

### Users

**Endpoints**:
- `GET /api/users/` - List users (filtered by permissions)
- `POST /api/users/` - Create a user (admin only)
- `GET /api/users/{id}/` - Retrieve a user
- `PATCH /api/users/{id}/` - Update a user
- `DELETE /api/users/{id}/` - Delete a user

**User Dashboard Information**:
- `GET /api/users/dashboard_info/` - Get dashboard information for current user

### Students

**Endpoints**:
- `GET /api/students/` - List students
- `POST /api/students/` - Create a student profile
- `GET /api/students/{id}/` - Retrieve a student
- `PATCH /api/students/{id}/` - Update a student
- `DELETE /api/students/{id}/` - Delete a student

**Student Onboarding**:
- `POST /api/students/onboarding/` - Complete student profile setup

### Teachers

**Endpoints**:
- `GET /api/teachers/` - List teachers
- `POST /api/teachers/` - Create a teacher profile
- `GET /api/teachers/{id}/` - Retrieve a teacher
- `PATCH /api/teachers/{id}/` - Update a teacher
- `DELETE /api/teachers/{id}/` - Delete a teacher


## Available Endpoints

### Api

- `api/scheduling/api/sessions/filter/`: filter_sessions
  - View: filter_sessions
- `api/scheduling/api/student/upcoming-classes/`: upcoming_classes
  - View: upcoming_classes
- `api/scheduling/api/teacher/today-schedule/`: today_schedule
  - View: today_schedule

## Response Format

All responses follow a standard format:

### Success Response (200 OK)

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "User Name",
  ...
}
```

For list endpoints:
```json
{
  "count": 10,
  "next": "http://api.example.org/accounts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "email": "user1@example.com",
      ...
    },
    {
      "id": 2,
      "email": "user2@example.com",
      ...
    }
  ]
}
```

### Error Response (4xx/5xx)

```json
{
  "error": "Descriptive error message",
  "detail": "More detailed explanation",
  "code": "ERROR_CODE"
}
```

or for validation errors:

```json
{
  "email": ["This field is required."],
  "name": ["Ensure this field has no more than 150 characters."]
}
```

## Versioning

API versioning is handled in the URL path: `/api/v1/...`

The current version is `v1`.

## Keeping the Contract Updated

This contract is generated from the actual API implementation and is updated with each significant change to the API. Frontend developers can rely on this document as a source of truth for API interactions.

For the most up-to-date and interactive documentation, refer to the Swagger UI at `/api/swagger/`.

## Best Practices for Frontend Developers

1. **Always check HTTP status codes**: Don't assume requests succeeded
2. **Handle token expiration**: Redirect to login when 401 responses are received
3. **Use proper error handling**: Display appropriate messages based on error responses
4. **Implement proper token storage**: Store tokens securely in the frontend
5. **Throttling awareness**: Implement exponential backoff for retry mechanisms

---

*Last updated: April 22, 2025*
