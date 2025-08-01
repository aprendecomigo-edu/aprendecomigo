# GitHub Issue #50: Teacher Profile Creation During Invitation Acceptance - Frontend Implementation Plan

**Date**: 2025-08-01  
**Status**: Implementation Plan Complete  
**Priority**: High  
**Issue Type**: Component Integration & Missing Dependencies  

## Executive Summary

The frontend infrastructure for issue #50 is **85% complete** with comprehensive wizard logic, API integration, and state management already implemented. The primary issue is **missing step components** that match the ProfileWizard's expected interface, preventing the profile wizard from rendering properly during invitation acceptance.

## Current Infrastructure Analysis

### ✅ **Existing & Complete Components**

1. **ProfileWizard.tsx** - Complete 8-step wizard orchestrator
2. **useInvitationProfileWizard.ts** - Comprehensive state management hook
3. **Invitation acceptance flow** - `/accept-invitation/[token].tsx`
4. **API Integration** - `invitationApi.ts` with TeacherProfileData interface
5. **Backend APIs** - All endpoints functional and tested

### ❌ **Missing Components (Blocking)**

The ProfileWizard imports step components from `./steps/` directory that don't exist:

```typescript
// Missing imports in ProfileWizard.tsx
import BasicInformationStep from './steps/BasicInformationStep';
import TeachingSubjectsStep from './steps/TeachingSubjectsStep';
import GradeLevelStep from './steps/GradeLevelStep';
import AvailabilityStep from './steps/AvailabilityStep';
import RatesCompensationStep from './steps/RatesCompensationStep';
import CredentialsStep from './steps/CredentialsStep';
import ProfileMarketingStep from './steps/ProfileMarketingStep';
import PreviewSubmitStep from './steps/PreviewSubmitStep';
import StepIndicator from './StepIndicator';
```

### 🔄 **Interface Mismatch Issue**

Existing step components in the directory use a different interface:
- **Existing**: `BasicInfoFormData` interface with custom validation
- **Required**: `TeacherProfileData` interface from API

## Implementation Plan

### **Phase 1: Create Missing Step Components** (Priority: Critical)

#### 1.1 Create Steps Directory Structure
```
frontend-ui/components/profile-wizard/steps/
├── BasicInformationStep.tsx
├── TeachingSubjectsStep.tsx  
├── GradeLevelStep.tsx
├── AvailabilityStep.tsx
├── RatesCompensationStep.tsx
├── CredentialsStep.tsx
├── ProfileMarketingStep.tsx
├── PreviewSubmitStep.tsx
└── index.ts
```

#### 1.2 Common Step Interface
```typescript
interface StepProps {
  profileData: TeacherProfileData;
  updateProfileData: (updates: Partial<TeacherProfileData>) => void;
  validationErrors: { [key: string]: string };
  invitationData?: any;
}
```

#### 1.3 Step Components Breakdown

**BasicInformationStep.tsx**
- Profile photo upload (React Native Image Picker integration)
- Contact preferences (email, SMS, call notifications)
- Brief introduction text area
- Professional title input
- Languages spoken (multi-select with custom entries)

**TeachingSubjectsStep.tsx**
- Subject selection with autocomplete from `COMMON_SUBJECTS`
- Custom subject entry capability
- Experience level per subject (beginner, intermediate, advanced, expert)
- Years of experience per subject
- Add/remove subject functionality

**GradeLevelStep.tsx**
- Grade level preference checkboxes:
  - Elementary (K-5)
  - Middle School (6-8) 
  - High School (9-12)
  - University Level
  - Adult Education
- Multi-select with validation (at least one required)

**AvailabilityStep.tsx**
- Weekly schedule grid component (7 days x time slots)
- Timezone selector with common Portuguese-speaking regions
- Availability notes text field
- Time slot management (add/remove availability blocks)
- Visual calendar-like interface

**RatesCompensationStep.tsx**
- Hourly rate input with currency selector (EUR default)
- Rate negotiability toggle
- Payment preferences:
  - Preferred method (bank transfer, PayPal, Stripe)
  - Invoice frequency (weekly, biweekly, monthly)
  - Tax information toggle
- Rate suggestions based on school policies

**CredentialsStep.tsx**
- Education background entries:
  - Degree, field of study, institution, graduation year
  - Highest degree indicator
  - Add/remove education entries
- Teaching experience entries:
  - Role, institution, dates, description
  - Current position indicator
- Certification file uploads:
  - PDF/image upload with file picker
  - Expiry date tracking
  - Issuing organization

**ProfileMarketingStep.tsx**
- Teaching philosophy rich text editor
- Teaching approach description
- Specializations (multi-select tags)
- Achievements list (add/remove)
- Student testimonials section (optional)

**PreviewSubmitStep.tsx**
- Profile preview in student-facing format
- Edit button for each section (goes back to specific step)
- Completion status indicators
- Final submit button with loading state
- Success/error handling

#### 1.4 Supporting Components

**StepIndicator.tsx**
- Progress indicator showing current step
- Step completion status
- Click-to-navigate functionality
- Responsive design for mobile/web

### **Phase 2: File Upload Integration** (Priority: High)

#### 2.1 React Native File Upload Strategy
```typescript
// Use expo-image-picker for photos
import * as ImagePicker from 'expo-image-picker';

// Use expo-document-picker for documents
import * as DocumentPicker from 'expo-document-picker';
```

#### 2.2 Cross-Platform Upload Handling
- **Web**: HTML5 file input with drag-and-drop
- **Mobile**: Native file pickers via Expo APIs
- **Upload Progress**: Show progress bars during upload
- **File Validation**: Size limits, file type checking

#### 2.3 File Storage Integration
- Upload to backend `/api/files/upload/` endpoint
- Store file URLs in TeacherProfileData
- Thumbnail generation for images
- File preview functionality

### **Phase 3: Integration with Invitation Flow** (Priority: Medium)

#### 3.1 Modify Invitation Acceptance Flow

Update `/app/accept-invitation/[token].tsx`:

```typescript
const handleAcceptInvitation = async () => {
  // ... existing validation ...
  
  if (invitation.role === 'teacher') {
    // Navigate to profile wizard instead of dashboard
    router.push({
      pathname: '/accept-invitation/profile-wizard',
      params: { token: token! }
    });
  } else {
    // Existing flow for non-teacher roles
    // ... existing code ...
  }
};
```

#### 3.2 Create Profile Wizard Route

New file: `/app/accept-invitation/profile-wizard.tsx`
```typescript
export default function ProfileWizardPage() {
  const { token } = useLocalSearchParams();
  const router = useRouter();
  
  const handleSuccess = () => {
    router.push('/(tutor)/dashboard');
  };
  
  const handleCancel = () => {
    router.push(`/accept-invitation/${token}`);
  };
  
  return (
    <ProfileWizard
      invitationToken={token}
      onSuccess={handleSuccess}
      onCancel={handleCancel}
    />
  );
}
```

### **Phase 4: Form State Management & Validation** (Priority: Medium)

#### 4.1 Enhanced Validation Rules
- Real-time validation per field
- Cross-field validation (e.g., experience vs. years)
- File upload validation (size, type, content)
- Email format validation
- Phone number format validation

#### 4.2 Auto-Save Functionality
- AsyncStorage integration (already implemented in hook)
- Save progress after each field change (debounced)
- Recovery of unsaved data on return
- Clear saved data after successful submission

#### 4.3 Offline Capability
- Cache form data locally
- Queue file uploads for when online
- Show offline indicators
- Sync when connection restored

### **Phase 5: Cross-Platform Compatibility** (Priority: Medium)

#### 5.1 Responsive Design
- Mobile-first approach with breakpoints
- Touch-optimized interfaces
- Keyboard navigation support
- Screen reader compatibility

#### 5.2 Platform-Specific Optimizations
- **Web**: Keyboard shortcuts, mouse interactions
- **iOS**: Native iOS design patterns, haptic feedback
- **Android**: Material Design elements, back button handling

#### 5.3 Performance Optimizations
- Lazy loading of step components
- Image compression before upload
- Efficient re-renders with React.memo
- Bundle size optimization

## Technical Challenges & Solutions

### **Challenge 1: File Uploads in React Native**
**Solution**: Use Expo APIs with progressive enhancement
- expo-image-picker for photos
- expo-document-picker for documents
- FormData for upload with progress tracking

### **Challenge 2: Rich Text Editing**
**Solution**: Use react-native-render-html or similar
- Cross-platform rich text component
- HTML output compatible with backend
- Markdown fallback for mobile

### **Challenge 3: Complex Form State**
**Solution**: Existing useInvitationProfileWizard hook handles this
- Centralized state management
- Validation per step
- Auto-save with AsyncStorage

### **Challenge 4: Weekly Schedule UI**
**Solution**: Custom calendar-like component
- Grid layout with time slots
- Touch/drag interaction for time blocks
- Timezone-aware time display

## Success Metrics

### **Functional Requirements**
- ✅ All 8 wizard steps render correctly
- ✅ Form validation works per step
- ✅ File uploads work on all platforms
- ✅ Auto-save/recovery functionality
- ✅ Profile preview matches student view
- ✅ Integration with invitation acceptance flow

### **Performance Requirements**  
- ✅ Step navigation < 100ms
- ✅ File upload with progress indicators
- ✅ Form auto-save < 1s after field change
- ✅ Mobile scroll performance optimized

### **Cross-Platform Requirements**
- ✅ Consistent UI on web, iOS, Android
- ✅ Touch and keyboard navigation
- ✅ Responsive design (mobile-first)
- ✅ Accessibility compliance

## Implementation Timeline

### **Sprint 1** (Days 1-2): Missing Step Components
- Create all 8 step components with basic UI
- Implement StepIndicator component
- Basic form fields without file uploads

### **Sprint 2** (Days 3-4): File Upload Integration
- Implement photo upload for profile and credentials
- Cross-platform file picker integration
- Upload progress and error handling

### **Sprint 3** (Day 5): Integration & Testing  
- Integrate wizard with invitation acceptance flow
- End-to-end testing on all platforms
- Bug fixes and refinements

## Risk Mitigation

### **High Risk**: File Upload Complexity
**Mitigation**: Start with basic file selection, add upload progress later

### **Medium Risk**: Cross-Platform UI Consistency  
**Mitigation**: Use Gluestack UI components throughout, test on all platforms

### **Low Risk**: Form State Complexity
**Mitigation**: Existing hook handles most complexity, well-tested

## Conclusion

The frontend implementation for GitHub issue #50 requires primarily **creating missing step components** that integrate with the existing comprehensive wizard infrastructure. The bulk of the complex logic (state management, validation, API integration, auto-save) is already implemented and tested.

**Estimated Effort**: 3-5 development days
**Complexity**: Medium (mostly component creation)
**Risk**: Low (leveraging existing infrastructure)

The implementation focuses on component creation rather than architectural changes, making it a straightforward enhancement to the existing robust foundation.