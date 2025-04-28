# User Onboarding Flow

This document outlines the user onboarding flow for Aprende Comigo and provides details about the API endpoints that are available for this process.

## Overview

The onboarding flow consists of the following steps:

1. User fills out form with info and selects primary contact (email or phone number)
2. Backend sends verification code to the selected primary contact
3. User verifies primary contact by submitting the verification code
4. User is redirected to dashboard after successful verification

## API Endpoints

### 1. Create User

**Endpoint:** `POST /api/accounts/create/`

**Authentication:** No authentication required

**Request Body:**
```json
{
  "name": "Full Name",
  "email": "user@example.com",
  "phone_number": "+351987654321",
  "primary_contact": "email",
  "school": {
    "name": "My School Name",
    "description": "Description of my school",
    "address": "School Address",
    "contact_email": "school@example.com",
    "phone_number": "+351123456789",
    "website": "https://school-website.com"
  }
}
```

**Response:**
```json
{
  "message": "User created successfully. Verification code sent to your email.",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "Full Name",
    "phone_number": "+351987654321",
    "primary_contact": "email"
  },
  "school": {
    "id": 1,
    "name": "My School Name"
  }
}
```

### 2. Verify Contact

**Endpoint:** `POST /api/accounts/auth/verify-code/`

**Authentication:** No authentication required

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
    "name": "Full Name",
    "phone_number": "+351987654321",
    "primary_contact": "email",
    "email_verified": true,
    "phone_verified": false,
    "created_at": "2023-06-15T10:00:00Z",
    "updated_at": "2023-06-15T10:30:00Z"
  },
  "is_new_user": true,
  "school": {
    "id": 1,
    "name": "My School Name"
  }
}
```

### 3. Verify Additional Contact (Authenticated)

**Endpoint:** `POST /api/accounts/users/verify_contact/`

**Headers:**
```
Authorization: Token <auth-token-value>
```

**Request Body:**
```json
{
  "contact_type": "phone",
  "code": "123456"
}
```

**Response:**
```json
{
  "message": "Your phone has been verified successfully.",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "Full Name",
    "phone_number": "+351987654321",
    "primary_contact": "email",
    "email_verified": true,
    "phone_verified": true,
    "created_at": "2023-06-15T10:00:00Z",
    "updated_at": "2023-06-15T10:30:00Z"
  }
}
```

### 4. Set Primary Contact (Authenticated)

**Endpoint:** `POST /api/accounts/users/set_primary_contact/`

**Headers:**
```
Authorization: Token <auth-token-value>
```

**Request Body:**
```json
{
  "primary_contact": "phone"
}
```

**Response:**
```json
{
  "message": "Your primary contact has been updated to phone.",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "Full Name",
    "phone_number": "+351987654321",
    "primary_contact": "phone",
    "email_verified": true,
    "phone_verified": true,
    "created_at": "2023-06-15T10:00:00Z",
    "updated_at": "2023-06-15T10:30:00Z"
  }
}
```

## Notes:

- Both email and phone number are required fields during user creation
- Users must select a primary contact method (email or phone) during registration
- Verification code is sent to the selected primary contact during registration
- Users can verify additional contact methods after registration
- Users can change their primary contact method after verifying both contact methods
- The auth token should be stored and included in all subsequent requests in the `Authorization` header as `Token <token-value>`
- A default school is automatically created for new users, with the user as the school owner

## Frontend Implementation Guidelines

### Error Handling

- **Create User Errors:**
  - Email already exists
  - Invalid phone number format
  - Required fields missing
  - Invalid school data

- **Verify Code Errors:**
  - Invalid code
  - Expired code
  - Too many failed attempts

### Validation Requirements

- **User Name:** Required, max 150 characters
- **Email:** Required, valid email format
- **Phone Number:** Required, valid phone number format, max 20 characters
- **Primary Contact:** Required, must be either "email" or "phone"
- **School Name:** Required if school data is provided, max 150 characters
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
