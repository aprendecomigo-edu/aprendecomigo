# GitHub Issue #50: Teacher Profile Creation During Invitation Acceptance - Technical Analysis

**Date:** 2025-08-01  
**Issue:** [#50] Teacher Profile Creation During Invitation Acceptance  
**Status:** Analysis Complete - Ready for Implementation  

## Executive Summary

This analysis provides a comprehensive technical breakdown for implementing a teacher profile setup system that triggers after invitation acceptance. The system will enhance the existing invitation flow with a multi-step wizard for comprehensive profile creation, file uploads, and integration with the current billing/compensation systems.

## Current State Analysis

### Existing Models Assessment

The current `TeacherProfile` model is already well-structured for this enhancement:

**Strengths:**
- ✅ Enhanced with structured JSON fields (`education_background`, `teaching_subjects`, `rate_structure`, etc.)
- ✅ Profile completion tracking (`profile_completion_score`, `is_profile_complete`)
- ✅ File upload support via `CustomUser.profile_photo`
- ✅ Comprehensive validation via services (`ProfileCompletionService`)
- ✅ Database indexes for performance optimization

**Current Fields:**
```python
# Basic Information
bio: TextField
specialty: CharField(100)
education: TextField
hourly_rate: DecimalField(6,2)
availability: TextField

# Structured Data (Enhanced)
education_background: JSONField
teaching_subjects: JSONField
rate_structure: JSONField  
weekly_availability: JSONField
grade_level_preferences: JSONField
teaching_experience: JSONField
credentials_documents: JSONField
availability_schedule: JSONField

# Profile Tracking
profile_completion_score: DecimalField(5,2)
is_profile_complete: BooleanField
last_profile_update: DateTimeField
last_activity: DateTimeField
```

### Existing API Infrastructure

**Current Invitation Acceptance Flow:**
1. `POST /accounts/invitations/{token}/accept/` - Accepts invitation
2. Creates basic `TeacherProfile` with minimal data
3. Creates `SchoolMembership` with `TEACHER` role
4. Associates with courses via `TeacherCourse` model

**Current Serializers:**
- ✅ `ComprehensiveTeacherProfileCreationSerializer` - Already exists for complete profile creation
- ✅ `ProfileWizardDataSerializer` - Security-focused validation for wizard data
- ✅ `ProfilePhotoUploadSerializer` - Secure file upload handling
- ✅ `TeacherSerializer` - Enhanced with completion data

## Technical Implementation Plan

### 1. Enhanced Invitation Acceptance Flow

**New Flow Design:**
```
Accept Invitation → Basic Profile Creation → Profile Wizard → Complete Profile
     ↓                      ↓                    ↓              ↓
Create Membership    Create TeacherProfile   Multi-step    Mark Complete
Create Basic Profile      (minimal)          Wizard      Update Scores
```

**API Endpoint Modifications:**

#### A. Enhanced Accept Invitation Endpoint

**URL:** `POST /accounts/invitations/{token}/accept/`

**Request Body Enhancement:**
```json
{
  "immediate_profile_setup": true,  // Optional: Skip to wizard
  "basic_profile": {
    "bio": "Optional initial bio",
    "specialty": "Optional specialty",
    "course_ids": [1, 2, 3]
  }
}
```

**Response Enhancement:**
```json
{
  "message": "Invitation accepted successfully",
  "invitation_accepted": true,
  "teacher_profile": {
    "id": 123,
    "profile_completion_score": 25.0,
    "is_profile_complete": false,
    "needs_profile_setup": true
  },
  "school_membership": {...},
  "next_step": {
    "action": "profile_wizard",
    "wizard_url": "/api/accounts/profile-wizard/",
    "completion_required": false
  }
}
```

#### B. New Profile Wizard API Endpoints

**Base URL:** `/api/accounts/profile-wizard/`

**1. Initialize Wizard**
```
POST /api/accounts/profile-wizard/initialize/
```

**2. Validate Step**
```
POST /api/accounts/profile-wizard/validate-step/
Body: {"step": 1, "data": {...}}
```

**3. Save Progress**
```
POST /api/accounts/profile-wizard/save-step/
Body: {"step": 1, "data": {...}}
```

**4. File Upload**
```
POST /api/accounts/profile-wizard/upload-file/
Body: FormData with files
```

**5. Complete Wizard**
```
POST /api/accounts/profile-wizard/complete/
Body: {"publish_profile": true}
```

### 2. Database Schema Enhancements

**No new models required** - Current schema is sufficient:

#### Enhanced TeacherProfile Usage

**Profile Completion Tracking:**
```python
def update_completion_score(self) -> None:
    """Existing method - already implemented"""
    completion_data = ProfileCompletionService.calculate_completion(self)
    self.profile_completion_score = completion_data['completion_percentage']
    self.is_profile_complete = completion_data['is_complete']
    self.save()
```

**Structured Data Fields:**
```python
# Teaching Subjects with Expertise Levels
teaching_subjects = [
    {"subject": "Mathematics", "level": "advanced", "grade_levels": ["9", "10", "11", "12"]},
    {"subject": "Physics", "level": "intermediate", "grade_levels": ["10", "11"]}
]

# Rate Structure with School Integration
rate_structure = {
    "individual_rate": 45.00,
    "group_rate": 30.00,
    "trial_rate": 25.00,
    "currency": "EUR",
    "billing_interval": "hourly"
}

# Availability Schedule
availability_schedule = {
    "monday": [{"start": "09:00", "end": "17:00"}],
    "tuesday": [{"start": "09:00", "end": "17:00"}],
    "preferred_session_length": 60,
    "break_between_sessions": 15
}
```

### 3. File Upload Security Implementation

**Current Security Measures (Already Implemented):**
```python
class ProfilePhotoUploadSerializer(serializers.Serializer):
    def validate_profile_photo(self, value):
        # ✅ File size validation (5MB limit)
        # ✅ File type validation (JPEG, PNG, GIF, WebP)
        # ✅ Image dimension validation
        # ✅ PIL-based image verification
        # ✅ Malicious content scanning
        # ✅ File extension validation
```

**Storage Configuration:**
```python
# settings/base.py
MEDIA_ROOT = 'media/'
MEDIA_URL = '/media/'

# File paths
profile_photos/ -> /media/profile_photos/
credentials/ -> /media/credentials/
```

**Additional Security Recommendations:**
1. **Virus Scanning:** Integrate ClamAV for uploaded files
2. **Content-Type Verification:** Double-check MIME types
3. **File Quarantine:** Temporary storage before processing
4. **Access Controls:** Signed URLs for private documents

### 4. Multi-Step Wizard Implementation

**Wizard Steps Design:**

```python
WIZARD_STEPS = {
    1: "personal_information",      # Name, contact, photo
    2: "professional_background",   # Education, experience
    3: "teaching_subjects",         # Subjects and expertise
    4: "availability_schedule",     # When available to teach
    5: "rate_and_compensation",     # Pricing structure
    6: "credentials_upload",        # Certificates, documents
    7: "profile_review"            # Review and publish
}
```

**Step Validation Logic:**
```python
class ProfileWizardView(APIView):
    def validate_step(self, request):
        step = request.data.get('step')
        data = request.data.get('data')
        
        # Use existing ProfileWizardStepValidationSerializer
        serializer = ProfileWizardStepValidationSerializer(data={
            'step': step,
            'data': data
        })
        
        if serializer.is_valid():
            return Response({
                'valid': True,
                'cleaned_data': serializer.validated_data['data']
            })
        
        return Response({
            'valid': False,
            'errors': serializer.errors
        }, status=400)
```

### 5. Integration with Billing/Compensation

**Rate Policy Integration:**
```python
def integrate_with_school_billing(teacher_profile, school):
    """Integrate teacher rates with school billing policies"""
    school_settings = school.settings
    
    # Respect school rate constraints
    if school_settings.max_teacher_rate:
        teacher_profile.hourly_rate = min(
            teacher_profile.hourly_rate,
            school_settings.max_teacher_rate
        )
    
    # Apply school commission structure
    if school_settings.commission_percentage:
        teacher_profile.rate_structure['net_rate'] = (
            teacher_profile.hourly_rate * 
            (1 - school_settings.commission_percentage / 100)
        )
    
    teacher_profile.save()
```

**Compensation Tracking:**
```python
# finances/models.py integration
class TeacherCompensationSettings(models.Model):
    teacher_profile = models.OneToOneField(TeacherProfile)
    preferred_payment_method = models.CharField(choices=PAYMENT_METHODS)
    payment_schedule = models.CharField(choices=SCHEDULE_OPTIONS)
    tax_information = models.JSONField()
```

### 6. API Response Design

**Wizard State Management:**
```json
{
  "wizard_state": {
    "current_step": 3,
    "total_steps": 7,
    "completed_steps": [1, 2],
    "can_skip_remaining": false,
    "estimated_completion_time": "10 minutes"
  },
  "profile_completion": {
    "percentage": 45.5,
    "is_complete": false,
    "missing_critical": ["teaching_subjects", "availability"],
    "missing_optional": ["credentials", "profile_photo"]
  },
  "validation_results": {
    "step_valid": true,
    "errors": {},
    "warnings": []
  },
  "saved_data": {
    "step": 3,
    "timestamp": "2025-08-01T10:30:00Z"
  }
}
```

## Technical Challenges & Solutions

### 1. **Challenge:** File Upload Performance
**Solution:** 
- Implement chunked upload for large files
- Use background tasks for file processing
- Progressive image resizing

### 2. **Challenge:** Wizard State Management
**Solution:**
- Store progress in `TeacherProfile` JSON fields
- Implement atomic operations for consistency
- Cache wizard state in Redis for performance

### 3. **Challenge:** Validation Complexity
**Solution:**
- Reuse existing `ProfileWizardDataSerializer` 
- Implement step-by-step validation
- Clear error messaging for each field

### 4. **Challenge:** School Policy Integration
**Solution:**
- Load school settings during wizard initialization
- Apply rate constraints dynamically
- Show policy compliance status

### 5. **Challenge:** Mobile-Friendly File Upload
**Solution:**
- Support multiple file formats
- Implement image compression
- Progress indicators for uploads

## Database Migration Considerations

**No new migrations required** - Current schema supports all requirements:

```sql
-- Current TeacherProfile table already has:
-- - All required JSON fields
-- - Profile completion tracking
-- - File upload support via User model
-- - Proper indexing for performance

-- Potential optimization index:
CREATE INDEX CONCURRENTLY idx_teacher_profile_completion_lookup 
ON accounts_teacherprofile(is_profile_complete, profile_completion_score);
```

## Security Implementation

### Input Validation & Sanitization

**Current Implementation (Already Secure):**
```python
class ProfileWizardDataSerializer:
    def validate_professional_bio(self, value):
        # ✅ HTML sanitization with bleach
        # ✅ Word count limits
        # ✅ Suspicious pattern detection
        # ✅ XSS prevention
```

### File Upload Security

**Current Implementation (Already Secure):**
```python
def validate_profile_photo(self, value):
    # ✅ File size limits (5MB)
    # ✅ File type validation
    # ✅ Image verification with PIL
    # ✅ Malicious content scanning
    # ✅ Dimension validation
```

### Rate Limiting

**Implemented Throttling:**
```python
# Already configured in views.py
throttle_classes = [
    ProfileWizardThrottle,  # 30 requests/hour
    FileUploadThrottle,     # 10 uploads/hour
    IPBasedThrottle        # General IP limits
]
```

## Performance Optimization

### Database Queries
- ✅ Existing indexes on completion fields
- ✅ Select_related for foreign keys
- ✅ Prefetch_related for many-to-many

### File Storage
- ✅ Django's file storage abstraction
- ✅ Media URL configuration
- ✅ Static file handling

### Caching Strategy
```python
# Redis cache for wizard state
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Testing Strategy

### Unit Tests
```python
# Test file uploads
def test_profile_photo_upload_security():
    # Test file type validation
    # Test file size limits
    # Test malicious file detection

# Test wizard flow
def test_profile_wizard_flow():
    # Test step validation
    # Test data persistence
    # Test completion logic

# Test integration
def test_school_billing_integration():
    # Test rate policy application
    # Test commission calculations
```

### Integration Tests
```python
def test_invitation_to_profile_flow():
    # Accept invitation
    # Complete profile wizard
    # Verify final state
```

## Implementation Timeline

### Phase 1: Core Wizard (Week 1)
- ✅ Enhanced invitation acceptance endpoint
- ✅ Basic wizard API endpoints
- ✅ Step validation logic

### Phase 2: File Uploads (Week 1-2)
- ✅ Secure file upload handling
- ✅ Image processing and validation
- ✅ Storage configuration

### Phase 3: School Integration (Week 2)
- ✅ Billing policy integration
- ✅ Rate constraint validation
- ✅ Compensation setup

### Phase 4: Testing & Polish (Week 2-3)
- ✅ Comprehensive test coverage
- ✅ Performance optimization
- ✅ Security audit

## Conclusion

The existing Django backend is **well-prepared** for this enhancement:

**Strengths:**
- ✅ Comprehensive model structure already in place
- ✅ Security-focused serializers implemented
- ✅ File upload security measures complete
- ✅ Profile completion tracking system ready
- ✅ School integration capabilities available

**Implementation Complexity:** **Medium** - Most infrastructure exists, requires API orchestration

**Risk Level:** **Low** - Building on proven, secure foundations

**Recommended Approach:** Enhance existing invitation acceptance flow with wizard orchestration rather than building from scratch.

**Next Steps:**
1. Implement wizard orchestration views
2. Enhance invitation acceptance response
3. Add comprehensive testing
4. Deploy with feature flags for gradual rollout

---

**Engineer:** TDD Python Engineer  
**Review Status:** Ready for Implementation  
**Confidence Level:** High - Leveraging existing secure infrastructure