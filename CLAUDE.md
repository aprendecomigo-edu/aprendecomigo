# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

**Aprende Comigo** is an educational platform connecting schools, teachers, and students. It consists of a Django REST Framework backend and a React Native frontend with cross-platform support (web, iOS, Android).

### Key Architecture
- **Frontend**: React Native + Expo with Gluestack UI components (`frontend-ui/`)
- **Backend**: Django REST Framework with multiple apps (`backend/`)
- **Virtual Environment**: Located in project root (`.venv/`), NOT in backend subfolder
- **Authentication**: Passwordless email verification

## Essential Commands

### Backend Development
```bash
# CRITICAL: Virtual environment is in project root
source .venv/bin/activate  # From project root
cd backend

# Development
python manage.py runserver
python manage.py runserver --settings=aprendecomigo.settings.development

# Database operations
python manage.py migrate
python manage.py createsuperuser

# Django system check
python manage.py check
```

### Frontend Development
```bash
cd frontend-ui

# CRITICAL: Always use legacy peer deps due to React 18 compatibility patches
npm install --legacy-peer-deps

# Development
npm start                # Expo dev server
npm run web             # Web development
npm run android         # Android development
npm run ios             # iOS development

# Build & Deploy
npm run typecheck       # TypeScript validation
npm run lint            # ESLint
npm run build:web:prod  # Production web build
```

### Environment Configuration
```bash
# Backend: Set Django environment
export DJANGO_ENV=development  # development|staging|production|testing

# Frontend: Set Expo environment
export EXPO_PUBLIC_ENV=development  # development|staging|production
```

## Architecture Overview

### Django Backend (`backend/`)
**Multi-app architecture with domain separation:**

- **`accounts/`**: User management, authentication, teacher onboarding
- **`classroom/`**: Class sessions, WebSocket consumers for real-time features
- **`finances/`**: Teacher compensation, billing settings, payment calculations
- **`common/`**: Shared utilities, exceptions, pagination

**Settings Structure:**
- `aprendecomigo/settings/base.py` - Common settings
- `aprendecomigo/settings/development.py` - Local development
- `aprendecomigo/settings/production.py` - Production overrides
- Environment controlled by `DJANGO_ENV` variable

**Key Models:**
- `CustomUser` - Extended user model with role-based access
- `TeacherProfile` - Teacher-specific data and compensation
- `School` - Educational institutions with billing settings
- `ClassSession` - Individual tutoring sessions for payment calculation

### React Native Frontend (`frontend-ui/`)

**File-based routing with Expo Router:**
- `app/` - Primary routing structure (Expo Router convention)
- `screens/` - Legacy screen components (architectural inconsistency to resolve)
- `components/` - Reusable UI components with platform-specific variants
- `api/` - API clients and authentication services

**Cross-platform considerations:**
- Uses Gluestack UI for consistent cross-platform components
- Platform-specific API URLs (Android emulator uses `10.0.2.2`)

## Business Logic

### Teacher Payment System
The core business logic centers around calculating teacher compensation:

1. **Compensation Rules**: Teachers have different rates per grade level, group classes, or fixed salaries
2. **Session Tracking**: Individual and group sessions are tracked with duration and grade level
3. **Trial Handling**: Schools can absorb, split, or pass trial class costs to teachers
4. **Monthly Calculations**: Automated payment summaries with detailed breakdowns

### Authentication Flow
1. **Email Verification**: Passwordless login with 6-digit codes
2. **Token Management**: JWT tokens with AsyncStorage
3. **Role-based Access**: Teachers, students, school admins with different permissions

## Development Patterns

### Frontend State Management
- React Context for authentication state (`api/authContext.tsx`)
- Form handling with `react-hook-form` and Zod validation
- Platform-specific API clients with environment-based URLs

### Backend API Design
- ViewSets for CRUD operations with DRF conventions
- Knox token authentication with custom base classes
- Comprehensive serializers with nested relationships
- Custom pagination and filtering

## Known Issues & Technical Debt

### CRITICAL TypeScript Errors (Fix First)
- Missing dependency: `@gorhom/bottom-sheet`
- MainLayout prop errors: `title` should be `_title` in 3 files:
  - `app/chat/channel/[id].tsx:52`
  - `screens/chat/channel-list/index.tsx:119`
  - `screens/dashboard/admin-dashboard/index.tsx:407`
- Component type mismatches in UI library

### Large Files Requiring Refactoring
- `frontend-ui/app/users/index.tsx` (531 lines) - Split into focused components
- `backend/accounts/views.py` (1700+ lines) - Break into separate ViewSet files
- `backend/accounts/models.py` (674 lines) - Extract into logical modules

### Security Issues
- Broken permission classes in `accounts/permissions.py` referencing non-existent `user_type` field
- Timing attack vulnerabilities in authentication flows (lines 476-489, 536-546 in `accounts/views.py`)
- Hardcoded fallback SECRET_KEY in base settings

### Architecture Inconsistencies
- Dual folder structure: Both `app/` and `screens/` contain similar components
- Inconsistent URL patterns between Django apps
- Circular import risks in backend views
- No standardized error handling patterns

## API Integration

### Environment-Specific URLs
```typescript
// Frontend API configuration
development: {
  ios: 'http://localhost:8000/api',
  android: 'http://10.0.2.2:8000/api',
  web: 'http://localhost:8000/api'
}
staging: 'https://aprendecomigo.eu.pythonanywhere.com/api'
production: 'https://api.aprendecomigo.com/api'
```

### Key Endpoints
- `/api/auth/request-code/` - Email verification
- `/api/auth/verify-code/` - Token authentication
- `/api/finances/school-billing-settings/` - Payment configuration
- `/api/accounts/teachers/onboarding/` - Teacher registration
- `/api/classroom/` - Session management

## Deployment Notes

### Backend Deployment
- PostgreSQL database required for production
- Environment variables via `.env` file (copy from `env.example`)
- Django settings split by environment

### Frontend Deployment
- Expo builds with environment-specific configurations
- Netlify deployment for web platform
- Platform-specific build commands for iOS/Android
- API URL configuration must match backend deployment

## Performance Considerations

### Database Optimization
- N+1 query issues in `accounts/views.py` admin stats (lines 174-184)
- Missing `select_related`/`prefetch_related` in filtered querysets
- Complex compensation calculations requiring query optimization

### Frontend Performance
- Large component files affecting build times
- UI library type issues causing compilation slowdown
- Asset optimization needed for cross-platform deployment

## Development Notes

### Frontend Dependencies
- **Patched packages**: `@gluestack-ui/checkbox` patched for React 18 compatibility
- **Missing dependencies**: Install `@gorhom/bottom-sheet` to fix bottomsheet component
- **Legacy peer deps**: Always use `npm install --legacy-peer-deps`
- **Removed dependencies**: `expo-local-authentication` and `expo-secure-store` removed (no longer needed)

### Backend Virtual Environment
- Virtual environment is in **project root** (`.venv/`), not in `backend/` folder
- Always activate from project root: `source .venv/bin/activate`
- Then navigate to backend: `cd backend`
