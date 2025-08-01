# GitHub Issue #95 - Backend Wizard Orchestration API Analysis

**Date:** 2025-08-01  
**Issue:** Implement wizard orchestration API for guided profile creation  
**Status:** Implementation Planning

## Overview

Need to enhance the existing invitation acceptance endpoint to provide step-by-step guidance for teacher profile creation. The backend infrastructure (TeacherProfile model, serializers, validation) already exists but lacks wizard orchestration.

## Current State Analysis

### Existing Infrastructure ✅

1. **TeacherProfile Model** (lines 459-621 in models.py)
   - Comprehensive profile fields including structured JSON data
   - Profile completion tracking with `profile_completion_score` and `is_profile_complete`
   - Activity tracking and completion methods

2. **Serializers** (lines 275-2198 in serializers.py)
   - `TeacherSerializer` - Full profile serialization with completion data
   - `ComprehensiveTeacherProfileCreationSerializer` - Comprehensive profile creation
   - `ProfileWizardDataSerializer` - Security-focused wizard data validation
   - `ProfileWizardStepValidationSerializer` - Individual step validation

3. **Current Invitation Acceptance** (lines 3460+ in views.py)
   - `POST /api/accounts/invitations/{token}/accept/`
   - Uses `ComprehensiveTeacherProfileCreationSerializer`
   - Already creates/updates teacher profile
   - Transaction-safe implementation

### Missing Wizard Orchestration ❌

1. **Wizard Metadata Response** - Acceptance endpoint doesn't return step guidance
2. **Step-by-Step Validation** - No dedicated endpoints for real-time validation
3. **Progress Tracking API** - No endpoints to track completion progress
4. **School Policy Integration** - Rate constraints not exposed via API

## Implementation Plan

### 1. Enhance Invitation Acceptance Endpoint

Current endpoint returns basic success/error response. Need to enhance to return:

```json  
{
  "success": true,
  "invitation_accepted": true,
  "teacher_profile": {...},
  "wizard_metadata": {
    "steps": [...],
    "current_step": 0,
    "completion_status": {...},
    "school_policies": {...}
  }
}
```

### 2. Add Step Validation Endpoints

New endpoints needed:
- `POST /api/accounts/teacher-profile/validate-step/` - Real-time step validation
- `GET /api/accounts/teacher-profile/completion-status/` - Progress tracking

### 3. School Policy Integration

Need to expose school billing policies for rate validation:
- Extract from SchoolSettings
- Include in wizard metadata
- Validate rates against school constraints

## Technical Requirements

1. **Backward Compatibility** - Must not break existing invitation flow
2. **Security** - Use existing security validation from ProfileWizardDataSerializer  
3. **Performance** - Minimal database queries for wizard metadata
4. **Error Handling** - Comprehensive error responses for each step

## Files to Modify

1. `accounts/views.py` - Enhance invitation acceptance, add step validation endpoints
2. `accounts/serializers.py` - Add wizard response serializers
3. `accounts/urls.py` - Add new endpoint routes
4. Tests - Comprehensive test coverage

## Next Steps

1. ✅ Analysis complete
2. 🔄 Write tests first (TDD approach)
3. ⏳ Implement wizard orchestration serializers
4. ⏳ Enhance invitation acceptance endpoint
5. ⏳ Add step validation endpoints
6. ⏳ Test backward compatibility