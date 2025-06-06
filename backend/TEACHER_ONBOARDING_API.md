# Teacher Onboarding API Documentation

This document outlines the three endpoints for teacher onboarding in the Aprende Comigo platform.

## Overview

The teacher onboarding system supports three distinct scenarios:

1. **Self-Onboarding**: Current user becomes a teacher
2. **Add Existing User**: School admin adds an existing user as teacher
3. **Invite New User**: School admin creates and invites a new user as teacher

---

## 1. Self-Onboarding

### Endpoint
```
POST /api/accounts/teachers/onboarding/
```

### Purpose
Allows the current authenticated user to create their own teacher profile.

### Authentication
- **Required**: Yes
- **Permission**: `IsAuthenticated`
- **Header**: `Authorization: Token <your-token-here>`

### Request Payload
```json
{
  "bio": "string (optional)",
  "specialty": "string (optional, max 100 chars)",
  "course_ids": [1, 2, 3] // optional array of course IDs
}
```

### Example Request
```json
{
  "bio": "Experienced mathematics teacher with passion for education",
  "specialty": "Mathematics and Physics",
  "course_ids": [1, 5, 8]
}
```

### Success Response (201 Created)
```json
{
  "message": "Teacher profile created successfully",
  "courses_added": 3,
  "teacher": {
    "id": 1,
    "user": {
      "id": 123,
      "email": "teacher@example.com",
      "name": "Maria Silva",
      "phone_number": "+351 912 345 678",
      "is_student": false,
      "is_teacher": true
    },
    "bio": "Experienced mathematics teacher with passion for education",
    "specialty": "Mathematics and Physics",
    "education": "",
    "courses": [
      {
        "id": 1,
        "course": {
          "id": 1,
          "name": "Matemática A",
          "code": "635",
          "educational_system": "portugal",
          "education_level": "ensino_secundario"
        },
        "hourly_rate": null,
        "is_active": true,
        "started_teaching": "2025-06-06"
      }
    ]
  }
}
```

### Error Responses

#### 400 - Already Has Profile
```json
{
  "error": "You already have a teacher profile"
}
```

#### 400 - Invalid Course IDs
```json
{
  "course_ids": ["Invalid course IDs: [999, 888]"]
}
```

#### 500 - Server Error
```json
{
  "error": "Failed to create teacher profile. Please try again."
}
```

---

## 2. Add Existing User as Teacher

### Endpoint
```
POST /api/accounts/teachers/add-existing/
```

### Purpose
Allows school owners/admins to add an existing user as a teacher in their school.

### Authentication
- **Required**: Yes
- **Permission**: `IsSchoolOwnerOrAdmin`
- **Header**: `Authorization: Token <your-token-here>`

### Request Payload
```json
{
  "email": "existing.user@example.com", // required - must be existing user
  "school_id": 1, // required - school to add teacher to
  "bio": "string (optional)",
  "specialty": "string (optional, max 100 chars)",
  "course_ids": [1, 2, 3] // optional array of course IDs
}
```

### Example Request
```json
{
  "email": "maria.silva@example.com",
  "school_id": 1,
  "bio": "Expert in secondary mathematics education",
  "specialty": "Mathematics",
  "course_ids": [1, 2, 5]
}
```

### Success Response (201 Created)
```json
{
  "message": "Teacher profile created and added to school successfully",
  "courses_added": 3,
  "teacher": {
    "id": 2,
    "user": {
      "id": 456,
      "email": "maria.silva@example.com",
      "name": "Maria Silva",
      "phone_number": "+351 912 345 678",
      "is_student": false,
      "is_teacher": true
    },
    "bio": "Expert in secondary mathematics education",
    "specialty": "Mathematics",
    "education": "",
    "courses": [...]
  },
  "school_membership": {
    "id": 10,
    "school": {
      "id": 1,
      "name": "Escola Secundária do Porto"
    },
    "role": "teacher",
    "is_active": true,
    "joined_at": "2025-06-06T14:30:00Z"
  }
}
```

### Error Responses

#### 400 - User Not Found
```json
{
  "error": "User with email 'notfound@example.com' does not exist"
}
```

#### 400 - User Already Has Teacher Profile
```json
{
  "error": "User already has a teacher profile"
}
```

#### 403 - Not School Admin
```json
{
  "error": "You don't have permission to add teachers to this school"
}
```

#### 404 - School Not Found
```json
{
  "error": "School with ID 999 does not exist"
}
```

---

## 3. Invite New User as Teacher

### Endpoint
```
POST /api/accounts/teachers/invite-new/
```

### Purpose
Allows school owners/admins to create a new user account and invite them as a teacher.

### Authentication
- **Required**: Yes
- **Permission**: `IsSchoolOwnerOrAdmin`
- **Header**: `Authorization: Token <your-token-here>`

### Request Payload
```json
{
  "email": "newteacher@example.com", // required - must be new email
  "name": "João Santos", // required - full name for new user
  "school_id": 1, // required - school to invite teacher to
  "bio": "string (optional)",
  "specialty": "string (optional, max 100 chars)",
  "course_ids": [1, 2, 3], // optional array of course IDs
  "phone_number": "+351 912 345 678" // optional - phone for new user
}
```

### Example Request
```json
{
  "email": "joao.santos@example.com",
  "name": "João Santos",
  "school_id": 1,
  "bio": "Physics teacher with 5 years experience",
  "specialty": "Physics and Chemistry",
  "course_ids": [5, 8],
  "phone_number": "+351 912 987 654"
}
```

### Success Response (201 Created)
```json
{
  "message": "User created, teacher profile setup, and invitation sent successfully",
  "courses_added": 2,
  "user_created": true,
  "invitation_sent": true,
  "teacher": {
    "id": 3,
    "user": {
      "id": 789,
      "email": "joao.santos@example.com",
      "name": "João Santos",
      "phone_number": "+351 912 987 654",
      "is_student": false,
      "is_teacher": true
    },
    "bio": "Physics teacher with 5 years experience",
    "specialty": "Physics and Chemistry",
    "education": "",
    "courses": [...]
  },
  "school_membership": {
    "id": 11,
    "school": {
      "id": 1,
      "name": "Escola Secundária do Porto"
    },
    "role": "teacher",
    "is_active": true,
    "joined_at": "2025-06-06T14:30:00Z"
  },
  "invitation": {
    "id": 5,
    "token": "abc123def456",
    "expires_at": "2025-06-13T14:30:00Z"
  }
}
```

### Error Responses

#### 400 - Email Already Exists
```json
{
  "error": "User with email 'existing@example.com' already exists"
}
```

#### 400 - Invalid Email
```json
{
  "email": ["Enter a valid email address."]
}
```

#### 400 - Missing Required Fields
```json
{
  "name": ["This field is required."],
  "email": ["This field is required."]
}
```

#### 403 - Not School Admin
```json
{
  "error": "You don't have permission to invite teachers to this school"
}
```

#### 500 - Failed to Send Invitation
```json
{
  "error": "User and teacher profile created, but failed to send invitation email"
}
```

---

## Common Response Fields

### Teacher Object
```json
{
  "id": 1,
  "user": {
    "id": 123,
    "email": "teacher@example.com",
    "name": "Teacher Name",
    "phone_number": "+351 912 345 678",
    "is_student": false,
    "is_teacher": true
  },
  "bio": "Teacher biography",
  "specialty": "Teaching specialty",
  "education": "Educational background",
  "courses": [
    {
      "id": 1,
      "course": {
        "id": 1,
        "name": "Course Name",
        "code": "123",
        "educational_system": "portugal",
        "education_level": "ensino_secundario"
      },
      "hourly_rate": null,
      "is_active": true,
      "started_teaching": "2025-06-06"
    }
  ]
}
```

### School Membership Object
```json
{
  "id": 10,
  "school": {
    "id": 1,
    "name": "School Name"
  },
  "role": "teacher",
  "is_active": true,
  "joined_at": "2025-06-06T14:30:00Z"
}
```

---

## Usage Guidelines

### When to Use Each Endpoint

1. **`/onboarding/`**: User wants to become a teacher themselves
2. **`/add-existing/`**: You know someone is already registered and want to make them a teacher
3. **`/invite-new/`**: You want to invite someone who doesn't have an account yet

### Security Notes

- Self-onboarding requires only basic authentication
- Adding/inviting others requires school admin permissions
- All operations are atomic (rollback on failure)
- Email invitations include secure tokens with expiration

### Best Practices

- Always validate email format before sending requests
- Handle partial failures gracefully (user created but email failed)
- Show clear success messages with course count
- Provide retry mechanisms for failed operations 