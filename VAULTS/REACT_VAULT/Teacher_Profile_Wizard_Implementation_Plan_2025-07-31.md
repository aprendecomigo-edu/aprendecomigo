# Teacher Profile Creation Wizard Implementation Plan
*Date: 2025-07-31*
*Issue: #50 - Teacher Acceptance Workflow - Complete Profile Creation*

## Overview
Transform the invitation acceptance flow to include a comprehensive teacher profile setup wizard with 8 steps, replacing the simple "accept invitation" button with a guided onboarding experience.

## Current State Analysis
- **Accept Invitation Page**: `/frontend-ui/app/accept-invitation/[token].tsx` - Simple acceptance flow with basic UI
- **API Interface**: `/frontend-ui/api/invitationApi.ts` - Has basic profile data support in `acceptInvitation()`
- **Hooks**: `/frontend-ui/hooks/useInvitations.ts` - Working acceptance flow

## Implementation Plan

### Phase 1: Enhanced API Interface
**File**: `/frontend-ui/api/invitationApi.ts`
- Expand `TeacherProfileData` interface with comprehensive fields
- Update `acceptInvitation()` method signature
- Add file upload support interfaces

### Phase 2: Profile Wizard Components
**Directory**: `/frontend-ui/components/profile-wizard/`
- `ProfileWizard.tsx` - Main wizard container with step management
- `StepIndicator.tsx` - Progress indicator component
- Step components:
  - `BasicInformationStep.tsx` (Step 1)
  - `TeachingSubjectsStep.tsx` (Step 2)
  - `GradeLevelStep.tsx` (Step 3)
  - `AvailabilityStep.tsx` (Step 4)
  - `RatesCompensationStep.tsx` (Step 5)
  - `CredentialsStep.tsx` (Step 6)
  - `ProfileMarketingStep.tsx` (Step 7)
  - `PreviewSubmitStep.tsx` (Step 8)

### Phase 3: Form Management
- Custom hook `useProfileWizard` for form state management
- Validation schemas for each step
- Auto-save functionality
- File upload handling

### Phase 4: Integration with Invitation Flow
**File**: `/frontend-ui/app/accept-invitation/[token].tsx`
- Add wizard after invitation acceptance
- Maintain existing flow logic
- Handle success/error states

## Technical Requirements

### Wizard Step Data Structure
```typescript
interface TeacherProfileData {
  // Step 1: Basic Information
  profile_photo?: File;
  contact_preferences?: ContactPreferences;
  introduction?: string;
  
  // Step 2: Teaching Subjects
  teaching_subjects: SubjectExpertise[];
  custom_subjects?: string[];
  
  // Step 3: Grade Levels
  grade_levels: GradeLevel[];
  
  // Step 4: Availability
  availability_schedule: WeeklySchedule;
  timezone: string;
  availability_notes?: string;
  
  // Step 5: Rates & Compensation
  hourly_rate: number;
  rate_negotiable: boolean;
  payment_preferences?: PaymentPreferences;
  
  // Step 6: Credentials
  education_background: EducationEntry[];
  teaching_experience: ExperienceEntry[];
  certifications: CertificationFile[];
  
  // Step 7: Marketing
  teaching_philosophy: string;
  teaching_approach: string;
  specializations: string[];
  achievements?: string[];
}
```

### UI Components Requirements
- **Gluestack UI**: All components must use Gluestack UI library
- **Responsive Design**: Mobile-first, tablet and desktop responsive
- **Form Validation**: Real-time validation with clear error messages
- **File Upload**: Image compression, file type validation, preview
- **Progress Saving**: Local storage backup, server-side save

### Navigation Flow
1. **Invitation Acceptance** → Basic invitation validation
2. **Profile Wizard** → 8-step guided setup
3. **Final Submission** → Complete profile + invitation acceptance
4. **Dashboard Redirect** → Navigate to tutor dashboard

## Success Criteria
- [ ] All 8 wizard steps implemented with proper UI
- [ ] Form validation and error handling
- [ ] File upload functionality (photos, documents)
- [ ] Profile preview with edit capability
- [ ] Integration with existing invitation flow
- [ ] Mobile-responsive design
- [ ] TypeScript typing throughout
- [ ] Auto-save and progress preservation
- [ ] Comprehensive testing coverage

## Files to Create/Update
### New Files
- `/frontend-ui/components/profile-wizard/ProfileWizard.tsx`
- `/frontend-ui/components/profile-wizard/StepIndicator.tsx`
- `/frontend-ui/components/profile-wizard/steps/BasicInformationStep.tsx`
- `/frontend-ui/components/profile-wizard/steps/TeachingSubjectsStep.tsx`
- `/frontend-ui/components/profile-wizard/steps/GradeLevelStep.tsx`
- `/frontend-ui/components/profile-wizard/steps/AvailabilityStep.tsx`
- `/frontend-ui/components/profile-wizard/steps/RatesCompensationStep.tsx`
- `/frontend-ui/components/profile-wizard/steps/CredentialsStep.tsx`
- `/frontend-ui/components/profile-wizard/steps/ProfileMarketingStep.tsx`
- `/frontend-ui/components/profile-wizard/steps/PreviewSubmitStep.tsx`
- `/frontend-ui/hooks/useProfileWizard.ts`

### Updated Files
- `/frontend-ui/api/invitationApi.ts` - Enhanced interface
- `/frontend-ui/app/accept-invitation/[token].tsx` - Wizard integration
- `/frontend-ui/hooks/useInvitations.ts` - Enhanced acceptance flow

## Implementation Priority
1. **High**: Core wizard structure and basic steps
2. **Medium**: File upload and advanced form features
3. **Low**: Advanced UI polish and animations

*Ready to begin implementation...*