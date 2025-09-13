# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aprende Comigo is an educational platform that has been successfully migrated from Django REST API backend + React Native frontend to a Django-powered PWA. The PWA migration referenced in `docs/PWA_MIGRATION_PRD.md` has been completed. Ignore the legacy frontend code.

**Current State**: Django-powered PWA with HTMX and Tailwind CSS ✅
**Context**: Business application where functionality takes precedence over consumer-grade animations

## Architecture & Technology Stack

### Django Framework
- **Language**: Python 3.13
- **Framework**: Django 5.2.5 with PWA capabilities
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Authentication**: django-sesame magic links with SMS OTP verification ✅
- **WebSockets**: Django Channels 4.3.1 with Redis channel layer
- **PWA Features**: django-pwa, service workers, offline capabilities

### Frontend
- **Technology**: Django Templates + HTMX + Tailwind CSS
- **UI Framework**: Custom Tailwind components with Alpine.js
- **Mobile Support**: Responsive design with bottom navigation
- **PWA Features**: App manifest, service worker, installable

### Key Business Domains
- **Multi-tenant**: Users can have multiple roles across different schools
- **Education Management**: Teachers, students, courses, scheduling
- **Financial Operations**: Stripe payments, teacher compensation, family budgets
- **Real-time Communication**: WebSocket chat, notifications
- **Multi-language**: English (UK) and Portuguese (Portugal)

## Development Commands

### Backend Development

Use the `ch` helper commands for all backend operations:
