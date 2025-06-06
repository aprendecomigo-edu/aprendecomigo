# API Specifications for Teacher Profile Feature

## Overview
The frontend has implemented a teacher profile creation modal that requires two main API endpoints. This document provides the exact specifications needed for backend implementation.

## 📍 **Frontend Implementation Location**
- **Modal Component**: `frontend-ui/components/modals/add-teacher-modal.tsx`
- **Mock Functions**: Lines 153-167 (to be replaced with real API calls)

---

## 🔗 **Required API Endpoints**

### 1. **GET /api/accounts/courses** - Load Available Courses

**Purpose**: Fetch all available courses/subjects that teachers can select from.

**Request**:
```http
GET /api/accounts/courses
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Expected Response**:
```json
[
  {
    "id": 1,
    "name": "Português",
    "code": "639",
    "educational_system": "portugal",
    "education_level": "ensino_secundario",
    "description": "Curso do ensino secundário português: Português",
    "created_at": "2025-06-06T13:45:12.123456Z",
    "updated_at": "2025-06-06T13:45:12.123456Z"
  },
  {
    "id": 2,
    "name": "Matemática A",
    "code": "635",
    "educational_system": "portugal",
    "education_level": "ensino_secundario",
    "description": "Curso do ensino secundário português: Matemática A",
    "created_at": "2025-06-06T13:45:12.234567Z",
    "updated_at": "2025-06-06T13:45:12.234567Z"
  }
]
```

**Error Response**:
```json
{
  "success": false,
  "error": "Failed to load courses",
  "message": "User-friendly error message"
}
```

---

### 2. **POST /api/teacher-profile** - Create Teacher Profile

**Purpose**: Save a teacher profile with selected courses for the current authenticated user.

**Request**:
```http
POST /api/teacher-profile
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "courseIds": [1, 3, 5]
}
```

**Expected Response** (Success):
```json
{
  "success": true,
  "data": {
    "teacherId": "teacher_123",
    "userId": "user_456",
    "courses": [
      {
        "id": 1,
        "name": "Português",
        "code": "639",
        "educational_system": "portugal",
        "education_level": "ensino_secundario",
        "description": "Curso do ensino secundário português: Português",
        "created_at": "2025-06-06T13:45:12.123456Z",
        "updated_at": "2025-06-06T13:45:12.123456Z"
      },
      {
        "id": 3,
        "name": "História A",
        "code": "623",
        "educational_system": "portugal",
        "education_level": "ensino_secundario",
        "description": "Curso do ensino secundário português: História A",
        "created_at": "2025-06-06T13:45:12.345678Z",
        "updated_at": "2025-06-06T13:45:12.345678Z"
      }
    ],
    "createdAt": "2025-01-23T10:30:00Z"
  },
  "message": "Teacher profile created successfully"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "At least one course must be selected",
  "details": {
    "field": "courseIds",
    "code": "REQUIRED"
  }
}
```

---

## 📋 **Data Models**

### Course Model
```typescript
interface Course {
  id: number;                   // Unique identifier (numeric)
  name: string;                 // Course name (e.g., "Português")
  code: string;                 // Course code (e.g., "639")
  educational_system: string;   // Education system (e.g., "portugal")
  education_level: string;      // Education level (e.g., "ensino_secundario")
  description: string;          // Full description
  created_at: string;           // ISO timestamp
  updated_at: string;           // ISO timestamp
}
```

### Teacher Profile Model
```typescript
interface TeacherProfile {
  id: string;
  userId: string;       // Reference to user account
  courseIds: number[];  // Array of course IDs (numeric)
  createdAt: string;    // ISO timestamp
  updatedAt: string;    // ISO timestamp
}
```

---

## 🔐 **Authentication & Authorization**

- **Authentication**: JWT Bearer token required for both endpoints
- **Authorization**: User must be authenticated and have permission to create teacher profiles
- **User Context**: The teacher profile should be created for the authenticated user

---

## ⚠️ **Business Rules & Validation**

### Course Endpoint:
- Return only active courses that can be taught
- Order courses alphabetically by name
- Include proper descriptions for search functionality
- Response should be a direct array of course objects

### Teacher Profile Endpoint:
- **Required**: At least one course must be selected
- **Validation**: All provided courseIds must exist and be valid (numeric IDs)
- **Uniqueness**: Check if user already has a teacher profile (update vs create)
- **Permissions**: Verify user has rights to become a teacher

---

## 🚀 **Implementation Notes**

### Frontend Integration Points:
```typescript
// Replace these mock functions in add-teacher-modal.tsx:

const loadCourses = async (): Promise<Course[]> => {
  const response = await fetch('/api/accounts/courses', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error('Failed to load courses');
  }

  return await response.json(); // Direct array response
};

const saveTeacherProfile = async (selectedCourseIds: number[]): Promise<void> => {
  const response = await fetch('/api/teacher-profile', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      courseIds: selectedCourseIds
    })
  });

  const data = await response.json();

  if (!data.success) {
    throw new Error(data.message);
  }
};
```

---

## 🧪 **Testing Requirements**

### Test Cases to Implement:

**GET /api/accounts/courses**:
- ✅ Successfully returns course array
- ✅ Returns empty array when no courses exist
- ✅ Handles authentication errors
- ✅ Returns proper error for invalid tokens
- ✅ Courses include all required fields (id, name, code, etc.)

**POST /api/teacher-profile**:
- ✅ Successfully creates teacher profile
- ✅ Validates required courseIds field
- ✅ Validates courseIds array is not empty
- ✅ Validates all courseIds exist (numeric validation)
- ✅ Handles duplicate teacher profile creation
- ✅ Returns proper error for invalid authentication

---

## 📊 **Database Schema Suggestions**

```sql
-- Courses table
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) NOT NULL UNIQUE,
    educational_system VARCHAR(50) NOT NULL,
    education_level VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Teacher profiles table
CREATE TABLE teacher_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Teacher courses junction table
CREATE TABLE teacher_courses (
    teacher_profile_id UUID REFERENCES teacher_profiles(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (teacher_profile_id, course_id)
);
```

---

## 🔄 **Next Steps**

1. **Backend Team**: Implement the two endpoints according to specifications
2. **Testing**: Test endpoints with provided test cases
3. **Frontend Team**: Replace mock functions with real API calls
4. **Integration Testing**: Test the complete flow end-to-end

---

## 📞 **Contact**

If you have questions about the frontend requirements or need clarification on any specifications, please reach out to the frontend team.

**Frontend Implementation Status**: ✅ Complete (using mocks)
**Backend Implementation Status**: ⏳ Pending
**Integration Status**: ⏳ Waiting for backend APIs
