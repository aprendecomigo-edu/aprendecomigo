# User Onboarding Flow

This document outlines the user onboarding flow for Aprende Comigo and provides details about the API endpoints that are available for this process.

## Overview

The onboarding flow consists of the following steps:

1. User fills out form with info and selects primary contact (email or phone number)
2. (backend) - verification code is sent to primary contact
3. User verifies primary contact and is redirect to dashboard

## API Endpoints

### 1. Fill out form and create user

**Endpoint:** `POST /api/accounts/create/`

**Headers:**
```
Authorization: Token <auth-token-value>
```

**Request Body:**
```json
{
  "user": {
    "name": "Full Name",
    "phone_number": "+351987654321"
  },
  "school": {
    "name": "My School Name",
    "description": "Description of my school",
    "address": "School Address",
    "contact_email": "school@example.com",
    "phone_number": "+351123456789",
    "primary_contact": "email"
    "website": "https://school-website.com"
  }
}
```

**Response:**
```json
{
  "message": "Onboarding completed successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "Full Name",
    "phone_number": "+351987654321",
    "created_at": "2023-06-15T10:00:00Z",
    "updated_at": "2023-06-15T10:30:00Z",
    "roles": [
      {
        "school": {
          "id": 1,
          "name": "My School Name"
        },
        "role": "school_owner",
        "role_display": "School Owner"
      }
    ]
  },
  "schools": [
    {
      "id": 1,
      "name": "My School Name",
      "description": "Description of my school",
      "address": "School Address",
      "contact_email": "school@example.com",
      "phone_number": "+351123456789",
      "website": "https://school-website.com",
      "created_at": "2023-06-15T10:00:00Z",
      "updated_at": "2023-06-15T10:30:00Z"
    }
  ]
}
```


### 2. Verify primary contact

**Endpoint:** `POST /api/accounts/auth/verify-code/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response:**
```json
{
  "token": "auth-token-value",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "user",
    "phone_number": "",
    "created_at": "2023-06-15T10:00:00Z",
    "updated_at": "2023-06-15T10:00:00Z"
  },
  "is_new_user": true,
  "school": {
    "id": 1,
    "name": "user's School"
  }
}
```

Notes:
- The `is_new_user` field will be `true` for users signing up for the first time
- A default school is automatically created for new users, with the user as the school owner
- The auth token should be stored and included in all subsequent requests in the `Authorization` header as `Token <token-value>`
- Both `user` and `school` objects are optional, allowing the frontend to update them separately if needed
- The onboarding endpoint returns the updated user with their roles and the updated school information

## Frontend Implementation Guidelines
### Error Handling

- **Request Code Errors:**
  - Invalid email/phone format
  - Rate limiting (too many attempts)

- **Verify Code Errors:**
  - Invalid code
  - Expired code
  - Too many failed attempts

- **Onboarding Errors:**
  - Validation errors for user or school data
  - Authentication errors

### Validation Requirements

- **User Name:** Required, max 150 characters
- **Phone Number:** Optional, max 20 characters, should be validated as a phone number
- **School Name:** Required, max 150 characters
- **School Description:** Optional
- **School Address:** Optional
- **Contact Email:** Optional, but should be validated as an email if provided
- **School Phone:** Optional, max 20 characters, should be validated as a phone number
- **Website:** Optional, should be validated as a URL if provided

## Role-Based Permissions

After onboarding, users are automatically assigned the "school_owner" role for their school. This role gives them full permissions to:

- Manage their school information
- Invite other users to their school (teachers, students, etc.)
- Access all areas of the application related to their school

Future flows will include invitation acceptance and role-specific onboarding for teachers and students.
