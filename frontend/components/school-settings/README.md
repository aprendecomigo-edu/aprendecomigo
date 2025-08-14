# School Settings Implementation

This directory contains the comprehensive school settings interface implementation for GitHub issue #69.

## Components

### SchoolSettingsForm.tsx
The main settings form component with the following sections:

1. **School Profile** - Basic school information, logo, contact details, branding colors
2. **Educational System** - Educational system selection and grade level configuration  
3. **Operational** - Trial cost absorption, session duration, timezone, currency, language
4. **Billing** - Billing contact information, address, tax ID
5. **Schedule & Availability** - Working hours, working days, reminder settings
6. **Communication** - Email and SMS notification preferences
7. **Permissions** - Student enrollment, parent approval, teacher assignment settings
8. **Integrations** - Calendar and email provider integrations
9. **Privacy & Compliance** - GDPR compliance, data retention, export settings

## Features

- ✅ Comprehensive form validation using Zod schema
- ✅ Mobile-responsive design with adaptive layouts
- ✅ Tabbed interface for easy navigation between sections
- ✅ Integration with backend APIs via useSchoolSettings hook
- ✅ Proper TypeScript typing throughout
- ✅ Consistent with existing Gluestack UI patterns
- ✅ Save/cancel functionality with confirmation dialogs
- ✅ Loading states and error handling

## Usage

The settings form is accessible via the school admin route:
```
/app/(school-admin)/settings.tsx
```

## API Integration

- **GET** `/api/accounts/schools/{id}/settings/` - Fetch school settings
- **PATCH** `/api/accounts/schools/{id}/settings/` - Update school settings
- **GET** `/api/accounts/schools/{id}/settings/educational-systems/` - Fetch educational systems

## Mobile Responsiveness

The form uses responsive layouts that adapt to different screen sizes:
- Two-column layouts on desktop collapse to single column on mobile
- Tabbed navigation adapts to smaller screens
- Form fields stack vertically on mobile devices