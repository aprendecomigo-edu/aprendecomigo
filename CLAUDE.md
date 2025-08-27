# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aprende Comigo is an educational platform that has been successfully migrated from Django REST API backend + React Native frontend to a Django-powered PWA. The PWA migration referenced in `docs/PWA_MIGRATION_PRD.md` has been completed. Ignore the legacy frontend code.

**Current State**: Django-powered PWA with HTMX and Tailwind CSS ✅
**Legacy Code**: React Native frontend code remains but is no longer used
**Context**: Business application where functionality takes precedence over consumer-grade animations

## Architecture & Technology Stack

### Backend (Django Framework) - ./backend folder
- **Language**: Python 3.13
- **Framework**: Django 5.2.5 with PWA capabilities
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Authentication**: django-sesame magic links with SMS OTP verification ✅
- **WebSockets**: Django Channels 4.3.1 with Redis channel layer
- **PWA Features**: django-pwa, service workers, offline capabilities

### Frontend (PWA Implementation) ✅
- **Technology**: Django Templates + HTMX + Tailwind CSS
- **UI Framework**: Custom Tailwind components with Alpine.js
- **Mobile Support**: Responsive design with bottom navigation
- **PWA Features**: App manifest, service worker, installable
- **Legacy**: React Native code in ./frontend (no longer active)

### Key Business Domains
- **Multi-tenant**: Users can have multiple roles across different schools
- **Education Management**: Teachers, students, courses, scheduling
- **Financial Operations**: Stripe payments, teacher compensation, family budgets
- **Real-time Communication**: WebSocket chat, notifications
- **Multi-language**: English (UK) and Portuguese (Portugal)

## Development Commands

### Backend Development

Use the `ch` helper commands for all backend operations:

```bash
# Server Management
ch dj runserver              # Start development server
ch dj runserver --prod       # Start with Uvicorn (production-like with WebSocket)
ch dj stop                   # Stop all Django servers

# Code Quality (ALWAYS USE BEFORE COMMITS)
ch dj lint                   # Check for linting issues
ch dj lint fix               # Auto-fix safe issues
ch dj format                 # Format code with Ruff
ch dj typecheck              # Run mypy type checking

# Testing
ch dj test                   # Run all tests
ch dj test accounts          # Run tests for specific app
ch dj test --coverage        # Run with coverage report
ch dj test --parallel        # Run tests in parallel

# Database Management
ch dj migrate                # Apply migrations
ch dj makemigrations         # Create new migrations
ch dj shell                  # Django shell

# Dependencies (ALWAYS USE THESE INSTEAD OF pip)
ch dj install <package>      # Install package and update requirements
ch dj uninstall <package>    # Uninstall package and clean requirements
ch dj install                # Install dev dependencies
ch dj install prod           # Install production dependencies
ch dj audit                  # Security vulnerability scan
```

## PWA Migration Status

**COMPLETED**: The PWA migration outlined in `docs/PWA_MIGRATION_PRD.md` has been successfully implemented! ✅

### Migration Achievements
1. ✅ **Foundation Completed**: PWA setup, authentication system, base templates
2. ✅ **Authentication Migration**: django-sesame magic links with SMS OTP verification
3. ✅ **Dashboard Implementation**: Mobile-responsive dashboard with HTMX interactions
4. ✅ **PWA Infrastructure**: django-pwa, service workers, offline capabilities
5. 🔄 **Remaining Work**: Real-time chat, file handling, payments integration

### Current Architecture Patterns

#### Backend Patterns
- **Modular Django Apps**: Each app handles specific business domain
- **DRY Principles**: Shared utilities in `common/` app
- **Multi-tenancy**: Users can belong to multiple schools with different roles
- **Security**: Comprehensive logging system, PII redaction, rate limiting
- **Performance**: Query optimization with select_related/prefetch_related
- **Timezone Handling**: Always use `timezone.now()`, store in UTC

#### Authentication Architecture ✅
- **Implemented**: django-sesame magic links (10-minute expiration, one-time use)
- **Dual Verification**: Email magic links + SMS OTP for new user signup
- **Session-based**: Django sessions
- **Multi-role Support**: Users can be teachers across multiple schools

#### Database Optimization
- **Indexing**: Strategic indexes on foreign keys and query patterns
- **Query Optimization**: Prevent N+1 queries with proper relationships
- **Connection Handling**: Connection pooling for production

## Testing Standards

### Backend Testing
```bash
# Use specialized test engineers
ch dj test                   # Run all tests
# Test patterns: Django TestCase, fixtures, mocked Stripe services
# Use existing test utilities in common/test_base.py
```

### Frontend Testing (Legacy - No longer active)
```bash
# Note: React Native frontend is no longer used
# npm test                     # Jest + React Native Testing Library (Legacy)
# Test utilities available in __tests__/utils/ (Legacy)
# Mock services for WebSocket, payments, etc. (Legacy)
```

### PWA Testing ✅
- **Django Templates**: Server-side rendering, no separate frontend tests needed
- **HTMX Interactions**: Tested through Django test client
- **PWA Features**: Service worker and manifest tested via browser dev tools

## Performance Considerations

### Current System Performance Targets
- **API Response Time**: < 200ms for standard endpoints
- **WebSocket Latency**: < 100ms for real-time features
- **Database Query Time**: < 50ms for optimized queries
- **Frontend Load Time**: < 3 seconds on 3G

### Migration Performance Impact
- **Expected Server Load Increase**: 3-5x CPU usage (SSR vs API-only)
- **Mitigation Strategies**: Redis caching, CDN, query optimization, connection pooling
- **Monitoring**: Django Silk (development), Prometheus (production)

## Security & Compliance

### Authentication Security
- **Magic Links**: 10-minute expiration, one-time use, IP validation
- **Session Management**: Secure cookies, HTTPS enforcement
- **Rate Limiting**: Comprehensive throttling per endpoint type
- **Multi-factor**: Biometric support on mobile devices

### Financial Security (PCI Compliance)
- **Stripe Integration**: Never store card data, webhook signature validation
- **Audit Trail**: All financial operations logged to `business.log`
- **Fraud Detection**: Real-time monitoring and alerting

### Data Privacy
- **GDPR Compliance**: PII redaction in logs, data sovereignty
- **Logging**: Hierarchical system with sensitive data filtering
- **File Security**: Virus scanning, sandboxed storage, type validation

## Debugging & Logging

### Backend Logging
```bash
# Log files location: backend/logs/
tail -f logs/django.log      # General application logs
tail -f logs/business.log    # Financial operations, sessions
tail -f logs/security.log    # Authentication, security events
tail -f logs/performance.log # Query performance, bottlenecks
```

### Logger Hierarchy
- **Business Events**: `business.*` loggers for audit trails
- **Security Events**: `security.*` loggers for auth failures, threats
- **Performance**: `performance.*` for slow queries, bottlenecks
- **App-Specific**: `accounts.*`, `finances.*`, etc.

## Environment Configuration

### Backend Settings Structure
```
aprendecomigo/settings/
├── base.py          # Common settings
├── development.py   # Local development
├── staging.py       # Pre-production
├── production.py    # Live environment
└── testing.py       # Test runner configuration
```

Set environment via `DJANGO_ENV` variable (development|staging|production|testing).

### Frontend Environment Detection (Legacy)
Legacy React Native platform detection (no longer used):
```typescript
// import { isWeb, isMobile, platformFeatures, buildEnv } from '@/utils/platform'; // Legacy
```

## PWA Development Approach ✅

The PWA migration has been completed successfully using:

1. ✅ **Django Expertise**: Leveraged team's Django knowledge, eliminated React complexity
2. ✅ **Business App UX**: Functionality-first approach, server-rendered forms implemented
3. ✅ **Foundation-First**: Implemented authentication and dashboard foundation
4. ✅ **Performance Optimized**: Server-side rendering with HTMX for dynamic interactions
5. ✅ **Progressive Enhancement**: All features work without JavaScript

### Implemented PWA Tools ✅
- ✅ **django-sesame**: Passwordless magic link authentication implemented
- ✅ **HTMX**: Dynamic interactions without full page reloads
- ✅ **django-pwa**: PWA manifest and service worker management
- 🔄 **django-webpush**: Self-hosted push notifications (pending implementation)

## Development Workflow Best Practices ✅

1. **Start Development**: Run `ch dj runserver` for the Django PWA server
2. **Code Quality**: Use `ch dj lint fix` and `ch dj format` before commits
3. **Testing**: Run `ch dj test` for comprehensive Django testing
4. **PWA Testing**: Use browser dev tools to test PWA features and responsiveness
5. **Performance**: Monitor server performance and Django query optimization
6. **Legacy Code**: Ignore React Native frontend code in ./frontend (no longer active)

## Common Issues & Solutions

### Django Channels WebSocket
- **Issue**: WebSocket connection failures
- **Solution**: Ensure Redis is running, check CHANNEL_LAYERS config
- **Debug**: Check `logs/performance.log` for connection issues

### Stripe Webhook Validation
- **Issue**: Webhook signature validation failures
- **Solution**: Verify STRIPE_WEBHOOK_SECRET matches dashboard
- **Debug**: Check `logs/business.log` for webhook events

### Multi-tenant Data Isolation
- **Issue**: Data leaking between schools
- **Solution**: Always filter by user's school relationships
- **Pattern**: Use queryset methods that enforce tenant isolation

### PWA-Specific Issues ✅
- **Issue**: Service worker registration
- **Solution**: django-pwa handles automatic registration
- **Debug**: Check browser dev tools > Application > Service Workers

**Success**: PWA migration completed! This is now a Django expert team leveraging existing skills with a modern PWA interface. The React Native frontend is legacy code and should be ignored.