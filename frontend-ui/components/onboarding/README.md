# Individual Tutor Onboarding System

This directory contains the complete onboarding flow for individual tutors creating their own tutoring business on the Aprende Comigo platform.

## Overview

The individual tutor onboarding flow guides tutors through setting up their complete tutoring profile in 6 main steps:

1. **Account Creation** - Basic user registration with email/phone verification
2. **Practice Setup** - Create their tutoring business profile 
3. **Educational System Selection** - Choose curriculum (Portugal, Brazil, or Custom)
4. **Subject Selection** - Select courses/subjects they want to teach
5. **Rate Configuration** - Set pricing for each subject
6. **Teacher Profile Completion** - Complete professional profile details

## Components

### Core Flow Components

- **`TutorOnboardingFlow`** - Main orchestrator component that manages the entire flow
- **`TutorOnboardingProgress`** - Progress tracking and step navigation
- **`OnboardingSuccessScreen`** - Completion celebration with next steps

### Step-Specific Components

- **`TutorSchoolCreationModal`** - Simple school setup modal for individual tutors
- **`EducationalSystemSelector`** - Educational system selection with market data
- **`CourseCatalogBrowser`** - Hierarchical course browsing with search and filters
- **`CourseSelectionManager`** - Multi-select course management with drag & drop
- **`RateConfigurationManager`** - Per-course pricing setup with smart suggestions

### Integration Components

- **`UserTypeSelection`** - Pre-signup user type selection screen
- Enhanced signup flow with tutor-specific routing

## Key Features

### User Experience
- **Mobile-First Design** - Touch-optimized interface that works on all devices
- **Progress Tracking** - Clear indication of completion status and time estimates
- **Smart Defaults** - Auto-generated school names, suggested rates, and intelligent presets
- **Contextual Help** - Tooltips, guides, and best practice suggestions throughout

### Technical Features
- **Real-time Validation** - Client and server-side validation with helpful error messages
- **Auto-save Progress** - Automatic saving of progress with ability to resume later
- **API Integration** - Full integration with Django backend APIs
- **Cross-platform** - Works seamlessly on web, iOS, and Android via Expo
- **Accessibility** - WCAG compliant with proper labels and navigation

### Business Intelligence
- **Market Data Integration** - Shows demand levels, competitor rates, and student counts
- **Rate Suggestions** - AI-powered pricing recommendations based on market data
- **Course Analytics** - Popular subjects and trending educational content
- **Completion Analytics** - Track onboarding funnel and drop-off points

## API Integration

The system integrates with these backend endpoints:

```typescript
// School creation for individual tutors
POST /api/accounts/schools/create-tutor-school/

// Educational systems and courses
GET /api/accounts/educational-systems/
GET /api/accounts/courses/?educational_system=1

// Onboarding progress
POST /api/accounts/tutors/onboarding/start/
POST /api/accounts/tutors/onboarding/save-progress/
POST /api/accounts/tutors/onboarding/complete/

// Analytics and discovery
GET /api/finances/tutor-analytics/
GET /api/accounts/tutors/discover/
```

## Usage

### Basic Implementation

```tsx
import { TutorOnboardingFlow } from '@/components/onboarding';

export default function OnboardingScreen() {
  return (
    <TutorOnboardingFlow
      onComplete={() => router.push('/dashboard')}
      onExit={() => router.back()}
      userName="John Doe"
      userEmail="john@example.com"
    />
  );
}
```

### With Custom Step Handling

```tsx
import { TutorOnboardingFlow } from '@/components/onboarding';

export default function OnboardingScreen() {
  const handleStepComplete = (step: string, data: any) => {
    // Custom logic for each step
    analytics.track('onboarding_step_complete', { step, data });
  };

  return (
    <TutorOnboardingFlow
      initialStep="educational-system"
      onComplete={() => {
        analytics.track('onboarding_complete');
        router.push('/dashboard');
      }}
      onStepComplete={handleStepComplete}
    />
  );
}
```

### Individual Components

You can also use individual components for custom flows:

```tsx
import { 
  EducationalSystemSelector,
  CourseCatalogBrowser,
  RateConfigurationManager 
} from '@/components/onboarding';

// Use components individually
<EducationalSystemSelector
  onSystemSelect={handleSystemSelect}
  selectedSystemId={selectedSystem?.id}
/>
```

## Customization

### Theming
The components use Gluestack UI with NativeWind CSS classes, making them fully customizable via your theme configuration.

### Content Customization
Key text and labels can be customized via props:

```tsx
<TutorOnboardingFlow
  title="Start Your Teaching Journey"
  subtitle="Set up your professional tutoring business"
  successMessage="Welcome to the Aprende Comigo community!"
/>
```

### Step Configuration
The onboarding steps can be customized:

```tsx
const customSteps = [
  {
    id: 'custom-step',
    title: 'Custom Step',
    component: CustomStepComponent,
    isRequired: true,
    estimatedTime: 5,
  },
  ...DEFAULT_TUTOR_ONBOARDING_STEPS
];
```

## Testing

The onboarding flow includes comprehensive test coverage:

- **Unit Tests** - Individual component testing
- **Integration Tests** - Full flow testing with mocked APIs
- **E2E Tests** - Complete user journey testing
- **Accessibility Tests** - WCAG compliance testing

Run tests with:
```bash
npm test components/onboarding
```

## Performance Considerations

- **Lazy Loading** - Components are loaded on-demand
- **Optimistic Updates** - UI updates immediately with rollback on errors  
- **Caching** - Educational systems and courses are cached locally
- **Bundle Splitting** - Onboarding code is split into separate chunks

## Accessibility

The onboarding system is fully accessible:
- **Screen Reader Support** - Proper ARIA labels and descriptions
- **Keyboard Navigation** - Full keyboard accessibility
- **Focus Management** - Logical focus flow between steps
- **High Contrast** - Supports high contrast and dark mode
- **Voice Control** - Compatible with voice navigation systems

## Localization

The system supports multiple languages:
- **Portuguese (Portugal)** - pt-PT
- **Portuguese (Brazil)** - pt-BR  
- **English** - en-US
- **Spanish** - es-ES

Language files are located in `/i18n/onboarding/`.

## Analytics Events

The system tracks these key events:
- `onboarding_started` - User begins onboarding
- `onboarding_step_complete` - Each step completion
- `onboarding_abandoned` - User exits without completing
- `onboarding_resumed` - User returns to complete
- `onboarding_completed` - Full completion
- `tutor_profile_published` - Profile goes live

## Support

For issues or questions:
1. Check the [API documentation](../../../backend/accounts/README.md)
2. Review [common issues](./TROUBLESHOOTING.md)
3. Contact the development team

## Contributing

When adding new features:
1. Follow the existing component patterns
2. Add comprehensive tests
3. Update this documentation
4. Consider accessibility implications
5. Test on multiple devices and browsers