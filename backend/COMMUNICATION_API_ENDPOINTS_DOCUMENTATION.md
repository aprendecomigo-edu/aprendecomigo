# Communication API Endpoints Documentation

This document provides comprehensive documentation for the enhanced communication API endpoints implemented for the teacher communication system frontend.

## Base URL
All endpoints are accessible under: `http://localhost:8000/api/accounts/`

## Authentication
All endpoints require authentication using Token Authentication:
```
Authorization: Token <your_auth_token>
```

## Permissions
All endpoints require the user to be a School Owner or School Admin (`IsSchoolOwnerOrAdmin` permission).

---

## 1. Template Management APIs

### 1.1 List All Templates
**GET** `/api/accounts/communication/templates/`

Lists all email templates for the authenticated user's schools.

**Response:**
```json
[
  {
    "id": 1,
    "school": 1,
    "template_type": "invitation",
    "name": "Teacher Invitation",
    "subject_template": "Join {{school_name}} as a Teacher",
    "html_content": "<p>Welcome {{teacher_name}} to {{school_name}}!</p>",
    "text_content": "Welcome {{teacher_name}} to {{school_name}}!",
    "use_school_branding": true,
    "custom_css": null,
    "is_active": true,
    "is_default": false,
    "created_by": 1,
    "created_by_name": "Admin User",
    "school_name": "Test School",
    "template_variables": ["teacher_name", "school_name", "platform_name"],
    "created_at": "2025-08-02T10:30:00Z",
    "updated_at": "2025-08-02T10:30:00Z"
  }
]
```

### 1.2 Create New Template
**POST** `/api/accounts/communication/templates/`

Creates a new email template.

**Request Body:**
```json
{
  "school": 1,
  "template_type": "reminder",
  "name": "Profile Reminder",
  "subject_template": "Complete Your Profile - {{school_name}}",
  "html_content": "<p>Hi {{teacher_name}}, please complete your profile.</p>",
  "text_content": "Hi {{teacher_name}}, please complete your profile.",
  "use_school_branding": true,
  "custom_css": ""
}
```

**Response:** `201 Created` with template data

### 1.3 Get Specific Template
**GET** `/api/accounts/communication/templates/{id}/`

Retrieves a specific template by ID.

**Response:** Template object (same structure as list response)

### 1.4 Update Template
**PUT** `/api/accounts/communication/templates/{id}/`

Updates an existing template.

**Request Body:** Same as create template
**Response:** `200 OK` with updated template data

### 1.5 Delete Template
**DELETE** `/api/accounts/communication/templates/{id}/`

Deletes a template.

**Response:** `204 No Content`

---

## 2. Template Preview & Testing APIs

### 2.1 Generate Template Preview
**POST** `/api/accounts/communication/templates/{id}/preview/`

Generates a preview of the template with provided variables.

**Request Body:**
```json
{
  "variables": {
    "teacher_name": "John Doe",
    "school_name": "Test School"
  }
}
```

**Response:**
```json
{
  "subject": "Join Test School as a Teacher",
  "html_content": "<p>Welcome John Doe to Test School!</p>",
  "text_content": "Welcome John Doe to Test School!",
  "variables_used": ["teacher_name", "school_name", "platform_name", "current_year"]
}
```

### 2.2 Send Test Email
**POST** `/api/accounts/communication/templates/{id}/send_test/`

Sends a test email using the template.

**Request Body:**
```json
{
  "test_email": "test@example.com",
  "variables": {
    "teacher_name": "John Doe",
    "school_name": "Test School"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Test email sent successfully"
}
```

---

## 3. School Branding APIs

### 3.1 Get School Branding Settings
**GET** `/api/accounts/communication/branding/`

Retrieves branding settings for the school.

**Response:**
```json
{
  "school_id": 1,
  "school_name": "Test School",
  "primary_color": "#3B82F6",
  "secondary_color": "#10B981",
  "text_color": "#1F2937",
  "background_color": "#F9FAFB",
  "logo_url": "/media/school_logos/logo.png"
}
```

### 3.2 Update School Branding Settings
**PUT** `/api/accounts/communication/branding/`

Updates branding settings for the school.

**Request Body:**
```json
{
  "primary_color": "#EF4444",
  "secondary_color": "#F59E0B",
  "text_color": "#111827",
  "background_color": "#F3F4F6"
}
```

**Response:** Updated branding settings

---

## 4. Analytics APIs

### 4.1 Get Email Performance Metrics
**GET** `/api/accounts/communication/analytics/`

Retrieves email performance metrics for the last 30 days.

**Response:**
```json
{
  "period": {
    "start_date": "2025-07-03",
    "end_date": "2025-08-02",
    "days": 30
  },
  "total_sent": 150,
  "delivery_rate": 98.5,
  "open_rate": 45.2,
  "click_rate": 12.8,
  "recent_communications": [
    {
      "id": 1,
      "recipient_email": "teacher@example.com",
      "subject": "Welcome to Test School",
      "delivery_status": "delivered",
      "sent_at": "2025-08-02T10:30:00Z"
    }
  ]
}
```

### 4.2 Get Template-Specific Analytics
**GET** `/api/accounts/communication/analytics/templates/`

Retrieves usage and performance statistics for each template.

**Response:**
```json
[
  {
    "template_id": 1,
    "template_name": "Teacher Invitation",
    "template_type": "invitation",
    "usage_count": 45,
    "success_rate": 98.5,
    "last_used": "2025-08-02T10:30:00Z"
  }
]
```

---

## 5. Communication Settings APIs

### 5.1 Get Communication Settings
**GET** `/api/accounts/communication/settings/`

Retrieves communication preferences for the school.

**Response:**
```json
{
  "default_from_email": "noreply@testschool.com",
  "email_signature": "Best regards,\nTest School Team",
  "auto_sequence_enabled": true,
  "notification_preferences": {
    "email_delivery_notifications": true,
    "bounce_notifications": true
  }
}
```

### 5.2 Update Communication Settings
**PUT** `/api/accounts/communication/settings/`

Updates communication preferences.

**Request Body:**
```json
{
  "default_from_email": "noreply@testschool.com",
  "email_signature": "Best regards,\nTest School Team",
  "auto_sequence_enabled": true,
  "notification_preferences": {
    "email_delivery_notifications": true,
    "bounce_notifications": true
  }
}
```

**Response:**
```json
{
  "message": "Communication settings updated successfully",
  "settings": {
    "default_from_email": "noreply@testschool.com",
    "email_signature": "Best regards,\nTest School Team",
    "auto_sequence_enabled": true,
    "notification_preferences": {
      "email_delivery_notifications": true,
      "bounce_notifications": true
    }
  }
}
```

---

## Template Variables

The following variables are available in all templates:

### Default Variables
- `{{platform_name}}` - "Aprende Comigo"
- `{{platform_url}}` - "https://aprendecomigo.com"
- `{{support_email}}` - "support@aprendecomigo.com"
- `{{current_year}}` - Current year (e.g., 2025)

### School-Specific Variables
- `{{school_name}}` - Name of the school
- `{{school_email}}` - School's contact email
- `{{school_primary_color}}` - School's primary color
- `{{school_secondary_color}}` - School's secondary color

### Context-Specific Variables
- `{{teacher_name}}` - Teacher's name (in teacher-related templates)
- `{{student_name}}` - Student's name (in student-related templates)
- `{{parent_name}}` - Parent's name (in parent-related templates)

---

## Template Types

Available template types:
- `invitation` - Teacher invitations
- `reminder` - Profile completion reminders
- `welcome` - Welcome messages
- `profile_reminder` - Profile completion reminders
- `completion_celebration` - Profile completion celebrations
- `ongoing_support` - Ongoing support messages
- `low_balance_alert` - Low balance alerts
- `package_expiring_alert` - Package expiring alerts

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK` - Successful GET/PUT requests
- `201 Created` - Successful POST requests
- `204 No Content` - Successful DELETE requests
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error responses include detailed error messages:
```json
{
  "error": "Error description",
  "details": "Detailed error information"
}
```

---

## Usage Examples

### Frontend Integration Example

```typescript
// Get all templates
const templates = await fetch('/api/accounts/communication/templates/', {
  headers: {
    'Authorization': `Token ${authToken}`,
    'Content-Type': 'application/json'
  }
}).then(res => res.json());

// Preview template
const preview = await fetch('/api/accounts/communication/templates/1/preview/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${authToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    variables: {
      teacher_name: 'John Doe',
      school_name: 'Test School'
    }
  })
}).then(res => res.json());

// Send test email
const testResult = await fetch('/api/accounts/communication/templates/1/send_test/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${authToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    test_email: 'test@example.com',
    variables: {
      teacher_name: 'John Doe'
    }
  })
}).then(res => res.json());
```

This completes the communication API implementation. All endpoints are now functional and ready for frontend integration.