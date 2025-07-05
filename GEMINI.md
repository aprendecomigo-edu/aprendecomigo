# GEMINI.md

This file provides context and guidance for Gemini AI when working with the **Aprende Comigo** educational platform codebase.

## Project Overview

**Aprende Comigo** is an educational platform connecting schools, teachers, and students through real-time tutoring sessions. The platform handles teacher onboarding, student management, payment processing, and live classroom interactions.

### Technology Stack
- **Backend**: Django REST Framework with PostgreSQL
- **Frontend**: React Native + Expo with cross-platform support (web, iOS, Android)
- **Real-time**: WebSocket consumers for live classroom features
- **Authentication**: Passwordless email verification with JWT tokens
- **UI Framework**: Gluestack UI components for consistent cross-platform design

## Development Environment Setup

### Critical Environment Requirements

**Virtual Environment Location**: The Python virtual environment is in the **project root** (`.venv/`), NOT in the backend subfolder.

```bash
# ALWAYS activate from project root
source .venv/bin/activate
cd backend
python manage.py runserver
```

**Frontend Dependencies**: Due to React 18 compatibility patches, always use legacy peer deps:
```bash
cd frontend-ui
npm install --legacy-peer-deps
```

### Environment Variables
```bash
# Backend Django environment
export DJANGO_ENV=development  # development|staging|production|testing

# Frontend Expo environment
export EXPO_PUBLIC_ENV=development  # development|staging|production
```

## Architecture & Code Organization

### Backend Structure (`backend/`)

**Multi-app Django architecture with domain separation:**

1. **`accounts/`** - User management, authentication, teacher onboarding
   - CustomUser model with role-based access (teacher, student, school_admin)
   - Passwordless authentication flow with email verification
   - Teacher profile management and onboarding process

2. **`classroom/`** - Class sessions and real-time features
   - WebSocket consumers for live classroom interactions
   - ClassSession model for tracking individual/group sessions
   - Real-time messaging and classroom controls

3. **`finances/`** - Payment processing and teacher compensation
   - Complex compensation rules (per grade, group classes, fixed salary)
   - Trial class cost handling (absorb, split, pass-through)
   - Monthly payment calculations and billing settings

4. **`common/`** - Shared utilities and base classes
   - Custom exceptions and error handling
   - Pagination utilities
   - Shared mixins and base views

**Settings Architecture:**
- `base.py` - Common settings for all environments
- `development.py` - Local development overrides
- `production.py` - Production-specific settings
- `staging.py` - Staging environment configuration

### Frontend Structure (`frontend-ui/`)

**File-based routing with Expo Router:**
- `app/` - Primary routing structure (Expo Router convention)
- `screens/` - Legacy screen components (needs consolidation with app/)
- `components/` - Reusable UI components with platform variants
- `api/` - API clients, authentication, and context providers

**Platform-Specific Considerations:**
- Android emulator uses `10.0.2.2` for localhost
- iOS simulator uses `localhost`
- Web development uses `localhost`
- Platform-specific component variants (`.web.tsx`, `.ios.tsx`, `.android.tsx`)

## Key Business Logic

### Teacher Payment System (Core Feature)

The platform's primary business logic revolves around calculating teacher compensation:

1. **Compensation Models**:
   - Per-grade hourly rates
   - Group class multipliers
   - Fixed monthly salaries
   - Hybrid combinations

2. **Session Tracking**:
   - Individual vs group sessions
   - Grade level tracking for rate calculation
   - Duration tracking for payment calculation

3. **Trial Class Handling**:
   - School pays full cost (absorb)
   - Cost split between school and teacher
   - Teacher pays full trial cost

4. **Payment Calculations**:
   - Automated monthly summaries
   - Detailed session breakdowns
   - Tax and deduction handling

### Authentication Flow

1. **Email-Based Authentication**:
   - User enters email
   - 6-digit verification code sent
   - Code verification returns JWT tokens
   - Tokens stored in AsyncStorage (mobile) or localStorage (web)

2. **Role-Based Access**:
   - Teachers: Access to classroom, student management, earnings
   - Students: Access to classes, teacher interaction
   - School Admins: Full school management, billing, teacher oversight

## Development Patterns & Best Practices

### Django Backend Patterns

**ViewSets and Serializers**:
```python
# Use ModelViewSets for full CRUD operations
class TeacherViewSet(ModelViewSet):
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
```

**Custom Permissions**:
```python
# Role-based permission classes
class IsTeacherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['teacher', 'school_admin']
```

**Query Optimization**:
```python
# Always use select_related/prefetch_related for foreign keys
queryset = TeacherProfile.objects.select_related('user', 'school')
    .prefetch_related('class_sessions')
```

### Frontend Patterns

**API Integration**:
```typescript
// Environment-based API URLs
const API_URLS = {
  development: {
    ios: 'http://localhost:8000/api',
    android: 'http://10.0.2.2:8000/api',
    web: 'http://localhost:8000/api'
  },
  staging: 'https://aprendecomigo.eu.pythonanywhere.com/api',
  production: 'https://api.aprendecomigo.com/api'
};
```

**Form Handling**:
```typescript
// Use react-hook-form with Zod validation
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email(),
  // ... other fields
});
```

**Cross-Platform Components**:
```typescript
// Use platform-specific imports
import { Box } from '@/components/ui/box';
import { Button } from '@/components/ui/button';
```

**Browser Automation & Testing**:
```bash
# Automated testing with Playwright MCP via Gemini CLI
gemini "Test the complete user registration flow"
gemini "Navigate to teacher dashboard and verify payment calculations"
gemini "Test responsive design by resizing to mobile viewport"
gemini "Capture screenshots of auth screens for documentation"
```

## Known Issues & Technical Debt

### CRITICAL - Fix These First

1. **TypeScript Errors**:
   - Missing dependency: `@gorhom/bottom-sheet`
   - MainLayout prop errors in 3 files (use `_title` instead of `title`)
   - Component type mismatches in UI library

2. **Security Vulnerabilities**:
   - Timing attacks in authentication (accounts/views.py lines 476-489, 536-546)
   - Broken permission classes referencing non-existent `user_type` field
   - Hardcoded fallback SECRET_KEY in base settings

3. **Performance Issues**:
   - N+1 queries in admin stats (accounts/views.py lines 174-184)
   - Missing query optimizations in filtered querysets
   - Large component files affecting build performance

### Architecture Inconsistencies

1. **Dual Folder Structure**: Both `app/` and `screens/` contain similar components (consolidate to `app/`)
2. **Inconsistent URL Patterns**: Different Django apps use different URL conventions
3. **Circular Import Risks**: Some backend views have complex interdependencies
4. **Error Handling**: No standardized error handling patterns across frontend

### Large Files Requiring Refactoring

1. **`frontend-ui/app/users/index.tsx`** (531 lines) - Split into focused components
2. **`backend/accounts/views.py`** (1700+ lines) - Break into separate ViewSet files
3. **`backend/accounts/models.py`** (674 lines) - Extract into logical modules

## API Endpoints & Integration

### Key Authentication Endpoints
- `POST /api/auth/request-code/` - Request email verification code
- `POST /api/auth/verify-code/` - Verify code and get tokens
- `POST /api/auth/logout/` - Invalidate tokens

### Core Business Endpoints
- `GET /api/accounts/teachers/` - Teacher management
- `POST /api/accounts/teachers/onboarding/` - Teacher registration
- `GET /api/finances/school-billing-settings/` - Payment configuration
- `GET /api/classroom/sessions/` - Class session management
- `WebSocket /ws/classroom/{session_id}/` - Real-time classroom

### Data Flow Patterns
```typescript
// Standard API call pattern
const response = await apiClient.get('/teachers/', {
  headers: { Authorization: `Bearer ${token}` }
});
```

## Testing Strategy

### Backend Testing
```bash
cd backend
python manage.py test accounts
python manage.py test classroom
python manage.py test finances
```

### Frontend Testing
```bash
cd frontend-ui
npm run test
npm run typecheck
npm run lint

# Web platform testing with Playwright MCP
npm run web  # Start web development server
# Then use Gemini CLI for browser automation:
# "Navigate to localhost:3000 and test user authentication"
# "Test teacher onboarding form with validation errors"
# "Take screenshots of responsive design on different screen sizes"
```

### QA Test Scenarios
- Auth flow testing (`qa-tests/auth/`)
- Form validation testing (`qa-tests/form/`)
- Navigation testing (`qa-tests/nav/`)

## Deployment Configuration

### Backend Deployment
- PostgreSQL required for production
- Environment variables via `.env` file
- Django settings controlled by `DJANGO_ENV`
- WSGI/ASGI configuration for WebSocket support

### Frontend Deployment
- Expo builds with platform-specific configurations
- Netlify for web deployment
- App Store/Play Store for mobile
- Environment-specific API URL configuration

## Development Commands Reference

### Backend Commands
```bash
# Environment setup
source .venv/bin/activate
cd backend

# Development server
python manage.py runserver --settings=aprendecomigo.settings.development

# Database operations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic

# Testing
python manage.py test
python manage.py check
```

### Frontend Commands
```bash
cd frontend-ui

# Installation (CRITICAL: use legacy peer deps)
npm install --legacy-peer-deps

# Development
npm start              # Expo dev server
npm run web           # Web development
npm run android       # Android development
npm run ios           # iOS development

# Quality checks
npm run typecheck     # TypeScript validation
npm run lint          # ESLint
npm run test          # Run tests

# Production builds
npm run build:web:prod
```

## Code Style & Conventions

### Backend (Python/Django)
- Follow PEP 8 style guidelines
- Use descriptive variable names
- Add docstrings to all functions and classes
- Use type hints where appropriate
- Keep ViewSets focused on single responsibility

### Frontend (TypeScript/React Native)
- Use 2 spaces for indentation
- Interface names should be descriptive (avoid `I` prefix)
- Prefer functional components with hooks
- Use strict TypeScript mode
- Follow React Native best practices for cross-platform development

### Git Workflow
- Feature branches from `main`
- Descriptive commit messages
- Run tests before committing
- Keep commits focused and atomic

When working with this codebase, prioritize fixing the critical TypeScript errors and security vulnerabilities before implementing new features. Always test across all platforms (web, iOS, Android) when making frontend changes.

### Browser Automation with Playwright MCP

The Gemini CLI is configured with Playwright MCP server for automated web testing. This is particularly useful for:

- **Authentication Flow Testing**: Automate the passwordless email verification process
- **Teacher Onboarding**: Test the multi-step teacher registration and profile setup
- **Payment Interface**: Verify school billing settings and teacher compensation displays
- **Responsive Design**: Test cross-platform UI consistency between React Native web and mobile
- **Form Validation**: Automate testing of complex forms with validation rules
- **Real-time Features**: Test WebSocket classroom functionality in web browsers

Example automation tasks:
- Navigate to web app and complete teacher registration with test data
- Test email verification code input with various valid/invalid codes
- Verify payment calculation displays match backend business logic
- Capture screenshots of UI components for documentation
- Test navigation flows between different user roles (teacher/student/admin)
