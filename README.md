# Aprende Comigo

Educational platform built with Django PWA for seamless learning experiences.

## Overview

Aprende Comigo is an educational platform that has been successfully migrated from a Django REST API backend + React Native frontend to a Django-powered PWA. The application provides multi-tenant educational management with real-time communication, scheduling, and financial operations.

## Technology Stack

- **Framework**: Django 5.2.5 with PWA capabilities
- **Frontend**: Django Templates + HTMX + Tailwind CSS + Alpine.js
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: django-sesame magic links with SMS OTP verification
- **WebSockets**: Django Channels with Redis channel layer
- **Payments**: Stripe integration
- **Languages**: English (UK) and Portuguese (Portugal)

## Feature Switching

This project uses django-waffle for feature flags to control the availability of features across different environments.

### Environment Configuration

Features are controlled by the `WAFFLE_DEFAULT_STATE` environment variable:

- **Production**: Features are **ON** by default (`WAFFLE_DEFAULT_STATE=true`)
- **Staging**: Features are **OFF** by default (`WAFFLE_DEFAULT_STATE=false`)
- **Development**: Defaults to DEBUG value (True), but configurable for testing

### Available Features

- `schedule_feature`: Calendar, Scheduling, Teacher Availability
- `chat_feature`: Chat, Messaging, Real-time Communication

### Development Testing

Test different feature states in development:

```bash
# Test with all features disabled
export WAFFLE_DEFAULT_STATE=false && python manage.py runserver

# Test with all features enabled
export WAFFLE_DEFAULT_STATE=true && python manage.py runserver

# Test with mixed feature states (default off, but schedule enabled)
export WAFFLE_DEFAULT_STATE=false WAFFLE_SWITCH_SCHEDULE_FEATURE=true && python manage.py runserver

# Test with default behavior (follows DEBUG setting)
unset WAFFLE_DEFAULT_STATE && python manage.py runserver
```

### Individual Feature Override

You can override specific features regardless of the default state:

```bash
# Override individual features
export WAFFLE_SWITCH_SCHEDULE_FEATURE=true   # Force schedule feature ON
export WAFFLE_SWITCH_CHAT_FEATURE=false      # Force chat feature OFF
```

### Priority Order

Feature switches follow this priority order:

1. **Individual feature env var** (e.g., `WAFFLE_SWITCH_SCHEDULE_FEATURE`)
2. **Global default** (`WAFFLE_DEFAULT_STATE`)
3. **DEBUG setting** (fallback)

### Feature Switch Testing Tool

Use the built-in testing tool to check current feature states:

```bash
# Check current status of all features
python manage.py shell -c "
from waffle import switch_is_active
print('Schedule feature:', switch_is_active('schedule_feature'))
print('Chat feature:', switch_is_active('chat_feature'))
"

# Or use the test script
python tests/test_feature_switches.py
```

## Development Setup

1. Clone the repository
2. Create virtual environment: `python -m venv .venv`
3. Activate virtual environment: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements/development.txt`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run development server: `python manage.py runserver`

## Key Business Domains

- **Multi-tenant**: Users can have multiple roles across different schools
- **Education Management**: Teachers, students, courses, scheduling
- **Financial Operations**: Stripe payments, teacher compensation, family budgets
- **Real-time Communication**: WebSocket chat, notifications
- **Multi-language**: English (UK) and Portuguese (Portugal)

## Environment Settings

The application uses environment-specific settings files:

- `development.py`: Local development with SQLite
- `staging.py`: Staging environment with PostgreSQL on Railway
- `production.py`: Production environment with optimized settings

## Documentation

- [Internationalization Guide](docs/INTERNATIONALIZATION.md)
- [Railway Health Checks](docs/RAILWAY_HEALTH_CHECKS.md)
- [PWA Migration Documentation](docs/PWA_MIGRATION_PRD.md)
