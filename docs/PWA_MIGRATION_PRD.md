# Product Requirements Document: Aprende Comigo PWA Migration

## Executive Summary

This document outlines the strategic migration of the Aprende Comigo educational platform from a React Native (Expo) + Django REST architecture to a Progressive Web Application (PWA) powered by Django, with the goal of simplifying development while maintaining all critical features. This is a business application with users who prioritize functionality over consumer-grade UX polish, allowing for a pragmatic migration approach.

**Document Version:** 2.0  
**Date:** January 2025  
**Status:** Planning Phase - Milestone Based
**Migration Type:** Full replacement on separate branch

---

## 1. Context & Background

### Goal Architecture
- **Frontend:** React Native with Expo SDK 53, React 19
- **Backend:** Django REST Framework with Channels for WebSockets
- **Database:** PostgreSQL
- **Authentication:** JWT-based passwordless (magic links)
- **Real-time:** Django Channels for WebSocket support
- **Payments:** Stripe integration

### Pain Points
1. Complex React maintenance and debugging
2. Separate codebases for web and mobile
3. Developer expertise requirements for React
4. Build complexity with React 19 compatibility issues

### Business Drivers
- **Leverage existing team expertise**: Developers are Django experts, not React specialists
- **Reduce development complexity**: Eliminate React debugging and build issues
- **Single codebase maintenance**: One technology stack (Python/Django)
- **Faster feature deployment**: Team can move faster in familiar territory
- **Lower technical debt**: Remove React 19 compatibility issues
- **Business app context**: Users prioritize functionality over consumer-grade animations

---

## 2. Solution Overview

### Goal Architecture
Transform the platform into a Django PWA using:
- **Django Templates** for server-side rendering
- **HTMX** for dynamic interactions without full page reloads
- **Service Workers** for offline capability and push notifications
- **django-webpush** for self-hosted push notifications (no third-party services)
- **django-sesame** for secure magic link authentication
- **Django Channels** for WebSocket real-time features
- **django-pwa** package for PWA manifest and service worker management

### Key Benefits
1. **Single Codebase:** One application for web, mobile, and desktop
2. **Simplified Stack:** Python/Django only, minimal JavaScript
3. **Native-like Experience:** Installable, offline-capable, push notifications
4. **Faster Development:** Django's rapid development with HTMX simplicity
5. **Cost Reduction:** No app store fees, single deployment pipeline

---

## 3. Technical Requirements

### Core Features Compatibility

| Feature | Current (React Native) | PWA Implementation | Status |
|---------|----------------------|-------------------|---------|
| **Magic Link Auth** | Native email client | Browser-based with return flow | ✅ Works |
| **Real-time Chat** | WebSocket + native notifications | WebSocket + FCM push notifications | ✅ Works |
| **File Upload** | Native pickers | HTML5 file input + drag-drop | ✅ Works |
| **Payments** | Stripe SDK | Stripe.js | ✅ Works |
| **Offline Mode** | AsyncStorage | Service Worker + IndexedDB | ✅ Works |
| **Push Notifications** | Native | FCM via Service Workers | ✅ Works |
| **Camera Access** | expo-image-picker | MediaDevices API | ✅ Works |
| **Multi-role Management** | React components | Django templates + HTMX | ✅ Works |

### Platform Support

#### iOS
- **Minimum Version:** iOS 16.4+ (for push notifications)
- **Installation:** Add to Home Screen via Safari (users can be directed from any browser)
- **Key Points:** 
  - Safari is always available on iOS devices
  - Simple link/QR code directs users to Safari for installation
  - Once installed, PWA runs independently like a native app
- **Known Limitations:** 
  - 50MB offline storage limit (manageable for business app)
  - No background sync API (use push notifications for critical updates)

#### Android (Chrome/Edge)
- **Minimum Version:** Chrome 89+
- **Installation:** Automatic prompt or manual
- **Full Feature Support:** Yes, including background sync

#### Desktop (All modern browsers)
- **Chrome/Edge:** Full support
- **Firefox:** Full support (except PWA install on desktop)
- **Safari:** Limited PWA features on macOS

---

## 4. Implementation Architecture

### 4.1 Backend Structure

```python
# Django app structure
aprendecomigo/
├── apps/
│   ├── accounts/          # User management, magic links
│   ├── chat/             # Real-time messaging
│   ├── classroom/        # Learning management
│   ├── finances/         # Payments, billing
│   ├── pwa/             # PWA specific features
│   └── notifications/    # FCM push notifications
├── static/
│   ├── js/
│   │   ├── service-worker.js
│   │   ├── htmx.min.js
│   │   └── app.js
│   └── manifest.json
└── templates/
    ├── base.html
    ├── components/       # HTMX partial templates
    └── views/           # Full page templates
```

### 4.2 Service Worker Architecture

```javascript
// service-worker.js - Handles offline & push notifications (using django-webpush)
self.addEventListener('install', (event) => {
  // Cache static assets
  event.waitUntil(
    caches.open('v1').then(cache => {
      return cache.addAll([
        '/',
        '/static/css/app.css',
        '/static/js/htmx.min.js'
      ]);
    })
  );
});

self.addEventListener('push', (event) => {
  // Handle push notifications from django-webpush
  const data = event.data ? event.data.json() : {};
  const options = {
    body: data.body || 'New notification',
    icon: '/static/icon-192.png',
    badge: '/static/badge-72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: data.id,
      url: data.url || '/'
    }
  };
  
  event.waitUntil(
    self.registration.showNotification(data.head || 'Aprende Comigo', options)
  );
});

self.addEventListener('notificationclick', (event) => {
  // Open PWA when notification clicked
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});
```

### 4.3 Real-time Chat Implementation

```python
# Django Channels consumer
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
    async def receive(self, text_data):
        # Handle incoming messages
        message = json.loads(text_data)
        
        # Send via WebSocket if online
        await self.channel_layer.group_send(...)
        
        # Send push notification if offline
        await self.send_push_notification(
            user_id=message['recipient'],
            title=f"New message from {message['sender']}",
            body=message['text']
        )
```

### 4.4 Push Notification Flow (Self-Hosted with django-webpush)

```python
# notifications/services.py
from django.conf import settings
from webpush import send_user_notification
from django.contrib.auth import get_user_model

User = get_user_model()

class PushNotificationService:
    def send_notification(self, user, title, body, url='/'):
        """Send push notification via django-webpush (no third-party services)"""
        payload = {
            'head': title,
            'body': body,
            'icon': settings.PWA_APP_ICONS[0]['src'],
            'url': url,
            'badge': '/static/badge-72.png'
        }
        
        try:
            send_user_notification(
                user=user,
                payload=payload,
                ttl=1000  # Time to live in seconds
            )
            return {'success': True}
        except Exception as e:
            # Log error, notification failed
            print(f"Notification failed: {e}")
            return {'success': False, 'error': str(e)}

# Generate VAPID keys (one-time setup)
# python manage.py generate_vapid_keys
# This creates public/private key pair for your server identification
```

---

## 5. Migration Strategy - Milestone Based

### Milestone 0: Risk Assessment & Prototyping
**Goal:** Validate technical feasibility of complex features
- [ ] Prototype real-time chat with HTMX and WebSockets
- [ ] Test file upload with progress indicators
- [ ] Validate complex form interactions (multi-step wizards)
- [ ] Benchmark server performance with 100 concurrent HTMX requests
- [ ] Test PWA installation flow on iOS and Android devices
- [ ] Validate push notification delivery rates

**Success Criteria:** All prototypes meet performance and UX requirements

### Milestone 1: Foundation & Infrastructure
**Goal:** Establish core PWA architecture
- [ ] Django PWA setup with service worker
- [ ] django-webpush configuration with VAPID keys
- [ ] django-sesame magic link authentication
- [ ] Base templates with HTMX and Tailwind
- [ ] WebSocket infrastructure with Django Channels
- [ ] Performance monitoring setup (Django Debug Toolbar, Django Silk)
- [ ] Error tracking (Sentry integration)

**Success Criteria:** PWA installable, authentication working, monitoring active

### Milestone 2: High-Risk Features First
**Goal:** Implement most complex features to identify issues early
- [ ] Real-time chat with offline queue
- [ ] File upload/download with progress
- [ ] Multi-step registration wizard
- [ ] Complex dashboard with live updates
- [ ] Drag-and-drop scheduling interface

**Success Criteria:** Complex interactions work smoothly with <200ms response time

### Milestone 3: Core Business Features
**Goal:** Implement essential business functionality
- [ ] Teacher dashboard with metrics
- [ ] Student management interfaces
- [ ] Payment integration (Stripe)
- [ ] Lesson scheduling system
- [ ] Basic reporting features

**Success Criteria:** Core business workflows operational

### Milestone 4: Complete Feature Parity
**Goal:** Implement remaining features
- [ ] Parent monitoring dashboards
- [ ] Admin analytics
- [ ] Notification preferences
- [ ] Profile management
- [ ] Help/support system

**Success Criteria:** All features from React Native app available

### Milestone 5: Optimization & Hardening
**Goal:** Production readiness
- [ ] Performance optimization (query optimization, caching)
- [ ] Security audit completion
- [ ] Load testing (target: 1000 concurrent users)
- [ ] Cross-browser testing
- [ ] Accessibility audit (WCAG 2.1 AA compliance)
- [ ] Documentation completion

**Success Criteria:** Meets all performance, security, and accessibility targets

### Milestone 6: Deployment & Launch
**Goal:** Production deployment
- [ ] Production environment setup
- [ ] CDN configuration
- [ ] Monitoring dashboards
- [ ] User communication plan
- [ ] Support team training
- [ ] Go-live

---

## 6. Performance & Scalability Considerations

### Server-Side Rendering Impact

#### Expected Load Increase
- **Current**: React Native app makes API calls only
- **PWA**: Every page interaction requires server rendering
- **Estimated increase**: 3-5x server CPU usage
- **Mitigation strategies**:
  - Aggressive caching with Redis
  - CDN for static assets (CloudFlare/Fastly)
  - Database connection pooling
  - Async task processing with Celery

#### Database Optimization
```python
# Prevent N+1 queries with select_related and prefetch_related
class TeacherDashboardView(View):
    def get_queryset(self):
        return Student.objects.select_related('user', 'school') \
                              .prefetch_related('lessons', 'payments') \
                              .filter(teacher=self.request.user)
```

#### Caching Strategy
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
        },
        'KEY_PREFIX': 'aprendecomigo',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Cache configuration for different content types
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes for anonymous users
CACHE_TTL = {
    'metrics': 30,      # Real-time metrics: 30 seconds
    'user_list': 300,   # User lists: 5 minutes
    'static_content': 3600,  # Static content: 1 hour
}
```

### HTMX Performance Optimization

#### Response Time Targets
- **Navigation**: < 100ms (cached)
- **Form submission**: < 200ms
- **Dashboard updates**: < 150ms
- **Search/filter**: < 100ms

#### Partial Loading Strategy
```html
<!-- Load critical content first, then enhance -->
<div id="dashboard">
    <!-- Critical: Show immediately -->
    <div id="user-info">{{ user.name }}</div>
    
    <!-- Non-critical: Load async -->
    <div hx-get="/metrics" hx-trigger="load" hx-indicator="#metrics-spinner">
        <span id="metrics-spinner" class="htmx-indicator">Loading metrics...</span>
    </div>
</div>
```

### Infrastructure Requirements

#### Recommended Stack
- **Web Server**: Nginx (static files) + Gunicorn (Django)
- **Database**: PostgreSQL with read replicas for scaling
- **Cache**: Redis for session, cache, and Channels layer
- **Queue**: Celery with Redis/RabbitMQ for async tasks
- **Storage**: S3-compatible for file uploads
- **CDN**: CloudFlare or similar for global distribution

#### Scaling Strategy
```yaml
# docker-compose.production.yml
services:
  nginx:
    image: nginx:alpine
    volumes:
      - static_volume:/static
      - media_volume:/media
    
  web:
    image: aprendecomigo:latest
    command: gunicorn config.wsgi:application --workers 4 --threads 2
    deploy:
      replicas: 2  # Start with 2, scale as needed
    
  db:
    image: postgres:15
    environment:
      POSTGRES_MAX_CONNECTIONS: 200
    
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    
  celery:
    image: aprendecomigo:latest
    command: celery -A config worker -l info --concurrency=4
```

### Monitoring & Observability

#### Key Metrics to Track
- **Response time percentiles** (p50, p95, p99)
- **Database query count per request**
- **Cache hit rates**
- **WebSocket connection count**
- **Server CPU/Memory usage**
- **Error rates by endpoint**

#### Implementation
```python
# Django Silk for development profiling
if DEBUG:
    INSTALLED_APPS += ['silk']
    MIDDLEWARE += ['silk.middleware.SilkyMiddleware']

# Production monitoring with django-prometheus
INSTALLED_APPS += ['django_prometheus']
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... other middleware
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
```

---

## 7. Technical Implementation Steps

### Step 1: Django PWA Setup

```bash
# Install required packages (all open-source, no paid services)
pip install django-pwa django-htmx django-sesame django-webpush channels channels-redis pywebpush
```

```python
# settings.py
INSTALLED_APPS = [
    # ... existing apps
    'pwa',
    'django_htmx',
    'django_sesame',
    'webpush',
    'channels',
]

# PWA Configuration
PWA_APP_NAME = 'Aprende Comigo'
PWA_APP_DESCRIPTION = "Educational Platform"
PWA_APP_THEME_COLOR = '#3B82F6'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
    {
        'src': '/static/images/icon-192.png',
        'sizes': '192x192'
    }
]
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static/js', 'service-worker.js')

# Django-Sesame Configuration for Magic Links
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'sesame.backends.ModelBackend',  # Magic link backend
]

SESAME_TOKEN_NAME = 'token'  # URL parameter name
SESAME_MAX_AGE = 600  # Link valid for 10 minutes
SESAME_ONE_TIME = True  # Token invalidated after use

# Django-WebPush Configuration (self-hosted push notifications)
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": "Your-Generated-Public-Key",
    "VAPID_PRIVATE_KEY": "Your-Generated-Private-Key",
    "VAPID_ADMIN_EMAIL": "admin@aprendecomigo.com"
}

# Generate VAPID keys with: 
# python manage.py generate_vapid --applicationServerKey
```

### Step 2: Service Worker Implementation

```javascript
// static/js/service-worker.js
const CACHE_NAME = 'aprende-comigo-v1';
const urlsToCache = [
  '/',
  '/static/css/app.css',
  '/static/js/htmx.min.js',
  '/offline.html'
];

// Install - cache assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

// Fetch - serve from cache when offline
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
      .catch(() => caches.match('/offline.html'))
  );
});
```

### Step 3: Push Notification Setup (django-webpush)

**Complete Tutorial**: [How to Send Web Push Notifications from Django Applications](https://www.digitalocean.com/community/tutorials/how-to-send-web-push-notifications-from-django-applications)

```python
# views/notifications.py
from django.shortcuts import render
from django.http import JsonResponse
from webpush import send_user_notification
import json

def subscribe_push(request):
    """Subscribe user to push notifications"""
    if request.method == 'POST':
        subscription = json.loads(request.body)
        # Save subscription info to user's profile
        request.user.push_subscription = subscription
        request.user.save()
        return JsonResponse({'status': 'subscribed'})
    
    # Return VAPID public key for frontend
    from django.conf import settings
    return JsonResponse({
        'public_key': settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY']
    })

def send_push_to_user(user, title, body, url='/'):
    """Send push notification to a specific user"""
    payload = {
        'head': title,
        'body': body,
        'url': url
    }
    send_user_notification(user=user, payload=payload, ttl=1000)
```

### Step 4: HTMX Integration

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    {% load pwa %}
    {% progressive_web_app_meta %}
    
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Aprende Comigo{% endblock %}</title>
    
    <!-- HTMX -->
    <script src="{% static 'js/htmx.min.js' %}"></script>
    
    <!-- PWA Registration -->
    <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js');
        }
    </script>
</head>
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
    {% block content %}{% endblock %}
</body>
</html>
```

### Step 5: Real-time Chat with HTMX & WebSockets

```html
<!-- templates/chat/room.html -->
<div id="chat-room" 
     hx-ext="ws" 
     ws-connect="/ws/chat/{{ room_id }}/">
    
    <div id="messages" hx-swap-oob="beforeend">
        <!-- Messages appear here -->
    </div>
    
    <form ws-send>
        <input name="message" type="text" placeholder="Type a message...">
        <button type="submit">Send</button>
    </form>
</div>

<script>
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Register for push notifications with django-webpush
    navigator.serviceWorker.ready.then(registration => {
        // Get VAPID public key from server
        return fetch('/webpush/vapid_key/')
            .then(response => response.json())
            .then(data => {
                return registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(data.public_key)
                });
            });
    }).then(subscription => {
        // Send subscription to django-webpush
        fetch('/webpush/save_information/', {
            method: 'POST',
            body: JSON.stringify(subscription),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            }
        });
    });
</script>
```

---

## 7. Limitations & Mitigations

### Known Limitations (Business App Context)

| Limitation | Business Impact | Mitigation |
|------------|--------|------------|
| iOS Safari installation required | Minor - one-time setup with clear instructions | Provide QR code or direct link to Safari |
| 50MB offline storage on iOS | Low - business users typically have connectivity | Cache critical data only, use lazy loading |
| No app store presence | Medium - but B2B users accept direct distribution | Direct onboarding, email invitations |
| No background sync on iOS | Low - push notifications cover critical updates | Use push for time-sensitive updates |
| Server rendering load | Medium - infrastructure cost increase | Aggressive caching, CDN, optimize queries |

### Risk Mitigation Strategies

1. **Progressive Enhancement:** Start with core features, add advanced capabilities gradually
2. **Feature Detection:** Check browser capabilities before using advanced APIs
3. **Fallback Options:** Provide alternatives for unsupported features
4. **User Education:** Clear onboarding explaining PWA installation benefits

---

## 8. Success Metrics

### Technical Metrics
- **Page Load Time**: < 2 seconds (acceptable for business users)
- **HTMX Response Time**: < 200ms for interactions
- **Lighthouse PWA Score**: > 85 (business app threshold)
- **Service Worker Cache Hit Rate**: > 70%
- **Concurrent User Support**: 1000+ users
- **Server CPU Usage**: < 70% at peak load

### Development Metrics
- **Feature Development Speed**: 2x faster than React Native
- **Bug Resolution Time**: < 24 hours for critical issues
- **Code Complexity**: 50% reduction in frontend code
- **Time to Deploy**: < 30 minutes
- **Developer Satisfaction**: Improved team velocity

### Business Metrics
- **User Adoption Rate**: > 90% within first month
- **Support Tickets**: 30% reduction
- **System Availability**: 99.9% uptime
- **Feature Request Turnaround**: 50% faster

---

## 9. Migration Approach

### Development Strategy
- **Branch Strategy**: Separate branch for full migration, no impact on main
- **Testing Approach**: Each milestone includes testing before proceeding
- **Rollback Plan**: Not needed - separate branch allows easy abandonment if issues arise
- **Team Focus**: Full team commitment to Django PWA, leveraging existing expertise
- **Data Migration**: Clean slate approach - no complex data migration required

### Milestone Progression
See Section 5 for detailed milestone-based approach. Key principles:
1. **Risk-first development**: Tackle complex features early
2. **Continuous validation**: Test assumptions at each milestone
3. **Performance monitoring**: Track metrics from day one
4. **No fixed timeline**: Progress based on milestone completion, not dates

---

## 10. Technical Decisions

### Why Django + HTMX for This Project?

**Team Expertise Alignment:**
- Team has deep Django expertise, limited React experience
- Python-only stack reduces context switching
- Django patterns are well-understood by team
- Faster development in familiar territory

**Business App Suitability:**
- B2B users prioritize functionality over animations
- Server-rendered pages acceptable for business workflows
- Form-heavy interfaces work well with HTMX
- Real-time features achievable with Django Channels

**vs Keeping React Native:**
- React 19 compatibility issues causing ongoing problems
- Debugging React requires expertise team doesn't have
- Build complexity slowing down releases
- Two codebases (mobile + web) increasing maintenance burden

**vs Other Alternatives:**
- Next.js/Remix: Still requires React expertise
- Flutter: Would require learning Dart
- Native Apps: Unnecessary for business application
- Vue/Angular: Same issues as React (unfamiliar frontend framework)

---

## 11. Security Considerations

### Pre-Launch Security Audit
A comprehensive security audit will be performed before production launch, covering:

1. **Infrastructure Security**
   - HTTPS enforcement (required for PWA)
   - CSP headers configuration
   - CORS policy for service workers
   - Rate limiting on all endpoints

2. **Authentication & Session Management**
   - Magic link token expiration (10 minutes)
   - Session timeout configuration
   - Concurrent login handling
   - IP validation for sensitive operations

3. **HTMX-Specific Security**
   - HTML injection prevention
   - CSRF token validation on all HTMX requests
   - Input sanitization before template rendering
   - Safe template variable escaping

4. **WebSocket Security**
   - Connection authentication
   - Message validation
   - Rate limiting per connection
   - Automatic disconnection on suspicious activity

5. **File Upload Security**
   - File type validation
   - Size limit enforcement
   - Virus scanning integration
   - Sandboxed storage location

---

## 12. Open-Source Stack Summary

### No Third-Party Service Dependencies
This implementation uses **100% open-source solutions** with no paid third-party services:

| Feature | Solution | License | Cost |
|---------|----------|---------|------|
| **Magic Links** | django-sesame | BSD | Free |
| **Push Notifications** | [django-webpush](https://www.digitalocean.com/community/tutorials/how-to-send-web-push-notifications-from-django-applications) + pywebpush | MIT | Free |
| **Real-time Chat** | Django Channels | BSD | Free |
| **PWA Support** | django-pwa | MIT | Free |
| **Dynamic UI** | HTMX | BSD 2-Clause | Free |
| **WebSockets** | channels-redis | BSD | Free |

### Key Advantages of This Stack
1. **Complete Control**: All services run on your infrastructure
2. **No Vendor Lock-in**: No Firebase, AWS SNS, or other proprietary services
3. **Privacy Compliance**: User data never leaves your servers
4. **Cost Predictable**: Only infrastructure costs, no per-notification fees
5. **GDPR Friendly**: Full data sovereignty

### Infrastructure Requirements
- **Server**: Any VPS or dedicated server (DigitalOcean, Linode, etc.)
- **Redis**: For Channels layer (can use same server)
- **PostgreSQL**: Existing database
- **SSL Certificate**: Required for PWA (Let's Encrypt free)
- **Email Service**: SMTP (can use existing provider)

## 13. Additional Resources

### Tutorials & Documentation
- **Django-WebPush Tutorial**: [DigitalOcean - How to Send Web Push Notifications from Django](https://www.digitalocean.com/community/tutorials/how-to-send-web-push-notifications-from-django-applications)
- **Django-Sesame Docs**: [Official Documentation](https://django-sesame.readthedocs.io/)
- **Django-PWA Guide**: [PyPI Package Documentation](https://pypi.org/project/django-pwa/)
- **HTMX with Django**: [Official HTMX Documentation](https://htmx.org/examples/)

## 14. Frontend Migration Guide: React Native to Django + HTMX 2 + Tailwind

### Migration Scope
- **Full migration** on separate branch - no phased approach needed
- **Clean slate** - no data migration complexity
- **Business app focus** - functionality over polish
- **Developer expertise** - leveraging Django knowledge

### 14.1 Project Structure for Django PWA

```
aprendecomigo/
├── apps/
│   ├── accounts/
│   │   └── templates/accounts/
│   │       ├── magic_link_request.html
│   │       ├── magic_link_sent.html
│   │       └── profile_wizard/
│   ├── dashboard/
│   │   └── templates/dashboard/
│   │       ├── admin/
│   │       ├── teacher/
│   │       ├── student/
│   │       └── parent/
│   ├── chat/
│   │   └── templates/chat/
│   │       ├── room.html
│   │       └── components/
│   └── payments/
│       └── templates/payments/
├── templates/
│   ├── base.html                    # Main app layout
│   ├── components/                  # Shared components
│   │   ├── ui/                     # UI library
│   │   │   ├── button.html
│   │   │   ├── card.html
│   │   │   ├── modal.html
│   │   │   ├── form/
│   │   │   │   ├── input.html
│   │   │   │   ├── select.html
│   │   │   │   └── textarea.html
│   │   │   └── navigation/
│   │   │       ├── sidebar.html
│   │   │       └── topbar.html
│   │   └── partials/               # HTMX partials
│   │       ├── metrics_row.html
│   │       ├── student_row.html
│   │       └── notification_item.html
│   └── layouts/
│       ├── app_layout.html         # Authenticated app layout
│       └── auth_layout.html        # Auth pages layout
├── static/
│   ├── css/
│   │   ├── app.css                 # Tailwind input file
│   │   └── app.min.css             # Compiled Tailwind
│   ├── js/
│   │   ├── htmx.min.js            # HTMX 2.0
│   │   ├── htmx-ws.js             # WebSocket extension
│   │   └── app.js                  # Minimal custom JS
│   └── pwa/
│       ├── manifest.json
│       └── service-worker.js
```

### 14.2 Tailwind Configuration for Django

```javascript
// tailwind.config.js
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/js/**/*.js',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Educational color palette
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        secondary: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
        },
      },
      animation: {
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-in',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

### 14.3 Component Migration Patterns

#### Base Layout Template
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Aprende Comigo{% endblock %}</title>
    
    <!-- PWA Meta -->
    {% load pwa %}
    {% progressive_web_app_meta %}
    
    <!-- Tailwind CSS -->
    <link href="{% static 'css/app.min.css' %}" rel="stylesheet">
    
    <!-- HTMX -->
    <script src="{% static 'js/htmx.min.js' %}" defer></script>
    <script>
        // HTMX config
        document.addEventListener('DOMContentLoaded', () => {
            document.body.addEventListener('htmx:configRequest', (e) => {
                e.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
            });
        });
    </script>
    {% block extra_head %}{% endblock %}
</head>
<body class="h-full bg-gray-50" hx-boost="true">
    {% block body %}{% endblock %}
    
    <!-- Global notification container -->
    <div id="toast-container" class="fixed bottom-4 right-4 z-50 space-y-2"></div>
    
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

#### App Layout with Role-based Navigation
```html
<!-- templates/layouts/app_layout.html -->
{% extends "base.html" %}

{% block body %}
<div class="flex h-full">
    <!-- Mobile menu overlay -->
    <div id="mobile-menu-overlay" class="lg:hidden"></div>
    
    <!-- Sidebar -->
    <aside class="hidden lg:flex lg:flex-shrink-0">
        <div class="flex w-64 flex-col">
            <div class="flex min-h-0 flex-1 flex-col bg-white border-r">
                <div class="flex flex-1 flex-col overflow-y-auto pt-5 pb-4">
                    <div class="flex flex-shrink-0 items-center px-4">
                        <img class="h-8 w-auto" src="{% static 'images/logo.svg' %}" alt="Aprende Comigo">
                    </div>
                    <nav class="mt-8 flex-1 space-y-1 px-2">
                        {% include "components/navigation/sidebar.html" %}
                    </nav>
                </div>
                <div class="flex flex-shrink-0 border-t p-4">
                    {% include "components/navigation/user_menu.html" %}
                </div>
            </div>
        </div>
    </aside>
    
    <!-- Main content -->
    <div class="flex flex-1 flex-col">
        <!-- Top bar -->
        <header class="bg-white shadow-sm lg:hidden">
            <div class="flex items-center justify-between px-4 py-2">
                <button hx-get="{% url 'components:mobile_menu' %}"
                        hx-target="#mobile-menu-overlay"
                        hx-swap="innerHTML"
                        class="p-2 rounded-md hover:bg-gray-100">
                    <svg class="h-6 w-6"><!-- Menu icon --></svg>
                </button>
                <img class="h-8 w-auto" src="{% static 'images/logo.svg' %}" alt="Aprende Comigo">
                <button hx-get="{% url 'notifications:panel' %}"
                        hx-target="#notification-panel"
                        hx-swap="innerHTML"
                        class="p-2 rounded-md hover:bg-gray-100 relative">
                    <svg class="h-6 w-6"><!-- Bell icon --></svg>
                    <span id="notification-badge" class="hidden absolute top-0 right-0 h-2 w-2 bg-red-500 rounded-full"></span>
                </button>
            </div>
        </header>
        
        <!-- Page content -->
        <main class="flex-1 overflow-y-auto" id="main-content">
            {% block content %}{% endblock %}
        </main>
    </div>
    
    <!-- Notification panel -->
    <div id="notification-panel"></div>
</div>
{% endblock %}
```

### 14.4 Authentication Flow Migration

#### Magic Link Request (React → Django + HTMX)
```html
<!-- templates/accounts/magic_link_request.html -->
{% extends "layouts/auth_layout.html" %}

{% block content %}
<div class="min-h-screen flex items-center justify-center px-4">
    <div class="max-w-md w-full space-y-8">
        <div class="text-center">
            <h2 class="text-3xl font-bold text-gray-900">Welcome back</h2>
            <p class="mt-2 text-gray-600">Enter your email to receive a magic link</p>
        </div>
        
        <form hx-post="{% url 'accounts:send_magic_link' %}"
              hx-target="this"
              hx-swap="outerHTML"
              class="mt-8 space-y-6">
            {% csrf_token %}
            
            <div>
                <label for="email" class="block text-sm font-medium text-gray-700">
                    Email address
                </label>
                <input type="email"
                       name="email"
                       id="email"
                       required
                       autocomplete="email"
                       class="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                       placeholder="you@example.com">
            </div>
            
            <button type="submit"
                    class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    hx-disable-elt="this">
                <span class="htmx-indicator">
                    <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                    </svg>
                    Sending...
                </span>
                <span class="htmx-indicator-hide">Send magic link</span>
            </button>
        </form>
    </div>
</div>
{% endblock %}
```

### 14.5 Dashboard Components Migration

#### Metrics Card Component
```html
<!-- templates/components/dashboard/metrics_card.html -->
<div class="bg-white rounded-lg shadow p-6">
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {% for metric in metrics %}
        <div class="flex flex-col space-y-2">
            <div class="flex items-center space-x-2">
                <div class="p-2 bg-{{ metric.color }}-100 rounded-lg">
                    {% include "components/ui/icon.html" with name=metric.icon class="w-5 h-5 text-{{ metric.color }}-600" %}
                </div>
                <span class="text-sm font-medium text-gray-600">{{ metric.title }}</span>
            </div>
            <div class="flex items-baseline space-x-2">
                <span class="text-2xl font-bold text-gray-900">{{ metric.value }}</span>
                {% if metric.change %}
                <span class="text-sm font-medium {% if metric.change > 0 %}text-green-600{% else %}text-red-600{% endif %}">
                    {% if metric.change > 0 %}+{% endif %}{{ metric.change }}%
                </span>
                {% endif %}
            </div>
            {% if metric.subtitle %}
            <p class="text-xs text-gray-500">{{ metric.subtitle }}</p>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</div>
```

#### Dynamic Dashboard with HTMX Polling
```html
<!-- templates/dashboard/teacher/index.html -->
{% extends "layouts/app_layout.html" %}

{% block content %}
<div class="p-4 sm:p-6 lg:p-8">
    <!-- Header -->
    <div class="mb-8">
        <h1 class="text-2xl font-bold text-gray-900">Teacher Dashboard</h1>
        <p class="mt-1 text-sm text-gray-600">Welcome back, {{ user.get_full_name }}</p>
    </div>
    
    <!-- Metrics with auto-refresh -->
    <div id="metrics-container"
         hx-get="{% url 'dashboard:teacher_metrics' %}"
         hx-trigger="load, every 30s"
         hx-swap="innerHTML">
        {% include "components/dashboard/metrics_card.html" %}
    </div>
    
    <!-- Students list with search -->
    <div class="mt-8 bg-white rounded-lg shadow">
        <div class="p-6 border-b">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                <h2 class="text-lg font-medium text-gray-900">Your Students</h2>
                <div class="mt-4 sm:mt-0">
                    <input type="search"
                           name="q"
                           placeholder="Search students..."
                           hx-get="{% url 'students:search' %}"
                           hx-trigger="keyup changed delay:500ms"
                           hx-target="#students-list"
                           hx-indicator="#search-indicator"
                           class="block w-full sm:w-64 rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm">
                </div>
            </div>
        </div>
        
        <div id="students-list" class="divide-y divide-gray-200">
            {% include "components/dashboard/students_list.html" %}
        </div>
        
        <div id="search-indicator" class="htmx-indicator p-4 text-center text-sm text-gray-500">
            Searching...
        </div>
    </div>
    
    <!-- Schedule widget -->
    <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div id="today-schedule"
             hx-get="{% url 'schedule:today' %}"
             hx-trigger="load"
             hx-swap="innerHTML">
            <!-- Schedule loads here -->
        </div>
        
        <div id="upcoming-payments"
             hx-get="{% url 'payments:upcoming' %}"
             hx-trigger="load"
             hx-swap="innerHTML">
            <!-- Payments info loads here -->
        </div>
    </div>
</div>
{% endblock %}
```

### 14.6 Interactive Features with HTMX 2

#### Modal Pattern
```html
<!-- templates/components/ui/modal.html -->
<div id="modal-backdrop" 
     class="fixed inset-0 z-50 overflow-y-auto"
     aria-labelledby="modal-title" 
     role="dialog" 
     aria-modal="true">
    <div class="flex min-h-screen items-center justify-center p-4">
        <!-- Background overlay -->
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
             hx-on:click="htmx.find('#modal-container').innerHTML = ''"></div>
        
        <!-- Modal panel -->
        <div class="relative transform overflow-hidden rounded-lg bg-white shadow-xl transition-all sm:w-full sm:max-w-lg">
            <div class="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                <h3 class="text-lg font-semibold leading-6 text-gray-900" id="modal-title">
                    {{ title }}
                </h3>
                <div class="mt-3">
                    {{ content|safe }}
                </div>
            </div>
            {% if footer %}
            <div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                {{ footer|safe }}
            </div>
            {% endif %}
        </div>
    </div>
</div>
```

#### Multi-step Form Wizard
```html
<!-- templates/accounts/profile_wizard/base.html -->
<div class="max-w-3xl mx-auto p-6">
    <!-- Progress bar -->
    <div class="mb-8">
        <div class="flex items-center justify-between">
            {% for step in wizard_steps %}
            <div class="flex items-center">
                <div class="flex items-center justify-center w-10 h-10 rounded-full 
                            {% if step.completed %}bg-primary-600 text-white{% elif step.current %}bg-primary-600 text-white{% else %}bg-gray-200 text-gray-600{% endif %}">
                    {% if step.completed %}
                        ✓
                    {% else %}
                        {{ forloop.counter }}
                    {% endif %}
                </div>
                {% if not forloop.last %}
                <div class="w-full h-0.5 {% if step.completed %}bg-primary-600{% else %}bg-gray-200{% endif %}"></div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        <div class="flex justify-between mt-2">
            {% for step in wizard_steps %}
            <span class="text-xs {% if step.current %}font-semibold{% endif %}">{{ step.name }}</span>
            {% endfor %}
        </div>
    </div>
    
    <!-- Step content -->
    <div id="wizard-content">
        <form hx-post="{% url 'accounts:wizard_step' step=current_step %}"
              hx-target="#wizard-content"
              hx-swap="innerHTML">
            {% csrf_token %}
            
            <div class="bg-white rounded-lg shadow p-6">
                {% block step_content %}{% endblock %}
            </div>
            
            <div class="mt-6 flex justify-between">
                {% if current_step > 1 %}
                <button type="button"
                        hx-get="{% url 'accounts:wizard_step' step=current_step|add:'-1' %}"
                        hx-target="#wizard-content"
                        hx-swap="innerHTML"
                        class="btn btn-secondary">
                    Previous
                </button>
                {% else %}
                <div></div>
                {% endif %}
                
                <button type="submit" class="btn btn-primary">
                    {% if is_last_step %}Complete{% else %}Next{% endif %}
                </button>
            </div>
        </form>
    </div>
</div>
```

### 14.7 Real-time Features

#### Chat Interface (Already covered in Appendix A)
The chat implementation uses WebSockets with Django Channels and includes HTMX for UI updates.

#### Live Notifications
```html
<!-- templates/components/notifications/live_panel.html -->
<div id="notifications-panel"
     hx-ext="ws"
     ws-connect="/ws/notifications/"
     class="fixed right-0 top-16 w-80 max-h-96 bg-white rounded-lg shadow-lg overflow-hidden hidden lg:block">
    <div class="p-4 border-b">
        <h3 class="text-sm font-semibold">Notifications</h3>
    </div>
    <div id="notification-list" class="divide-y divide-gray-100 overflow-y-auto max-h-80">
        {% for notification in notifications %}
        <div class="p-4 hover:bg-gray-50 transition-colors"
             hx-post="{% url 'notifications:mark_read' notification.id %}"
             hx-trigger="click"
             hx-swap="outerHTML">
            {% include "components/notifications/item.html" %}
        </div>
        {% empty %}
        <div class="p-4 text-center text-gray-500 text-sm">
            No new notifications
        </div>
        {% endfor %}
    </div>
</div>
```

### 14.8 Component Library

#### Django Template Tags for UI Components
```python
# templatetags/ui.py
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.inclusion_tag('components/ui/button.html')
def button(text, variant='primary', size='md', type='button', **attrs):
    """Render a button component with Tailwind classes"""
    base_classes = "inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2"
    
    variant_classes = {
        'primary': 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
        'secondary': 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-primary-500',
        'danger': 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
        'ghost': 'text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
    }
    
    size_classes = {
        'xs': 'px-2.5 py-1.5 text-xs',
        'sm': 'px-3 py-2 text-sm',
        'md': 'px-4 py-2 text-sm',
        'lg': 'px-6 py-3 text-base',
        'xl': 'px-8 py-3 text-base',
    }
    
    classes = f"{base_classes} {variant_classes.get(variant, variant_classes['primary'])} {size_classes.get(size, size_classes['md'])}"
    
    # Build HTML attributes
    attrs_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
    
    return {
        'text': text,
        'type': type,
        'classes': classes,
        'attrs': mark_safe(attrs_str),
    }

@register.simple_tag
def icon(name, size='w-5 h-5', color='text-gray-500'):
    """Render an SVG icon"""
    # Icon library mapping
    icons = {
        'home': '<path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />',
        'users': '<path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />',
        'calendar': '<path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />',
        # Add more icons as needed
    }
    
    svg = f'''
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="{size} {color}">
        {icons.get(name, '')}
    </svg>
    '''
    
    return mark_safe(svg)
```

### 14.9 Implementation Priority (Milestone-Based)

Following the risk-first approach from Section 5:

#### Priority 1: Complex UI Validation
- Multi-step wizards with HTMX
- Drag-and-drop interfaces
- Real-time updates
- File upload with progress

#### Priority 2: Core Business Logic
- Authentication flows
- Role-based dashboards
- Payment processing
- Scheduling system

#### Priority 3: Standard Features
- User profiles
- Settings management
- Reports and analytics
- Help system

### 14.10 Key Migration Principles

1. **Progressive Enhancement**: Every feature works without JavaScript
2. **Mobile-First**: Design for mobile, enhance for desktop
3. **Server-Side State**: Minimize client-side state management
4. **Partial Updates**: Use HTMX for targeted DOM updates
5. **Accessibility**: ARIA labels, keyboard navigation, screen reader support

### 14.11 Performance Optimizations

```python
# views.py - Optimized view pattern
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

@vary_on_headers('HX-Request')
@cache_page(60 * 5)  # Cache for 5 minutes
def dashboard_metrics(request):
    # Check if HTMX request
    if request.headers.get('HX-Request'):
        template = 'components/dashboard/metrics_card.html'
    else:
        template = 'dashboard/teacher/index.html'
    
    metrics = get_cached_metrics(request.user)
    return render(request, template, {'metrics': metrics})
```

### 14.12 Development Workflow

```bash
# Install dependencies
npm install -D tailwindcss @tailwindcss/forms @tailwindcss/typography

# Watch Tailwind CSS
npx tailwindcss -i ./static/css/app.css -o ./static/css/app.min.css --watch

# Django development server
python manage.py runserver

# Django Channels for WebSocket
python manage.py runserver_plus --nopin --threaded

# Generate VAPID keys for push notifications
python manage.py generate_vapid --applicationServerKey
```

## 15. Conclusion

The migration to a Django-powered PWA is a pragmatic decision driven by:
- **Team expertise** in Django vs limited React knowledge
- **Business application context** where functionality trumps consumer-grade polish
- **Development velocity** improvements by working in familiar technology
- **Reduced complexity** through single-language stack

By using a milestone-based approach with risk-first development, we can validate technical assumptions early and pivot if necessary without timeline pressure.

### Immediate Next Steps
1. **Milestone 0**: Begin prototyping complex features
2. **Performance baseline**: Establish current metrics for comparison
3. **Infrastructure planning**: Prepare for increased server load
4. **Team preparation**: Ensure all developers have HTMX knowledge

### Key Success Factors
- Prototype complex features first to validate approach
- Monitor performance metrics from day one
- Leverage Django expertise for rapid development
- Accept business-app UX trade-offs
- Focus on functionality over polish

---

## Appendix A: Complete Chat System Implementation

### A.1 Enhanced Data Models for EdTech Chat

The chat system is designed specifically for educational contexts with role-based permissions, file sharing, and rich messaging features.

```python
# models/chat.py
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
import uuid

User = get_user_model()

class ChatRoom(models.Model):
    """Flexible room model supporting different educational contexts"""
    ROOM_TYPES = [
        ('direct', 'Direct Message'),        # 1-on-1 (student-teacher, parent-teacher)
        ('tutoring', 'Tutoring Session'),    # Structured learning session
        ('classroom', 'Classroom'),          # Class-wide discussions
        ('support', 'Support'),              # Student support group
        ('announcement', 'Announcement'),    # Broadcast from teacher/admin
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255, blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    
    # Educational context
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True)
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Participants with roles
    participants = models.ManyToManyField(User, through='ChatParticipant')
    
    # Settings
    is_archived = models.BooleanField(default=False)
    allow_file_upload = models.BooleanField(default=True)
    max_file_size_mb = models.IntegerField(default=10)
    allowed_file_types = ArrayField(
        models.CharField(max_length=10),
        default=list,
        blank=True,
        help_text="e.g., ['pdf', 'doc', 'jpg', 'png']"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    message_count = models.IntegerField(default=0)  # Denormalized for performance
    
    class Meta:
        indexes = [
            models.Index(fields=['room_type', 'school']),
            models.Index(fields=['last_message_at']),
        ]


class ChatParticipant(models.Model):
    """Tracks user participation and permissions in chat rooms"""
    ROLES = [
        ('owner', 'Owner'),           # Created the room
        ('moderator', 'Moderator'),   # Can moderate messages
        ('member', 'Member'),          # Regular participant
        ('observer', 'Observer'),      # Read-only (e.g., parent monitoring)
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES, default='member')
    
    # Notification preferences
    muted_until = models.DateTimeField(null=True, blank=True)
    push_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)
    
    # Read tracking
    last_read_at = models.DateTimeField(auto_now_add=True)
    last_read_message = models.ForeignKey('Message', null=True, blank=True, on_delete=models.SET_NULL)
    unread_count = models.IntegerField(default=0)  # Denormalized
    
    # User status in this room
    is_typing = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['room', 'user']
        indexes = [
            models.Index(fields=['user', 'unread_count']),
        ]


class Message(models.Model):
    """Flexible message model supporting various educational content"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('system', 'System'),          # Join/leave notifications
        ('assignment', 'Assignment'),   # Special type for homework
        ('quiz', 'Quiz'),              # Interactive quiz
        ('announcement', 'Announcement'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Message content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(blank=True)  # Text content or description
    
    # Reply threading
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    
    # Rich content metadata
    metadata = models.JSONField(default=dict, blank=True)
    # For assignments: {"due_date": "2024-01-20", "points": 100}
    # For quizzes: {"questions": [...], "time_limit": 600}
    
    # Status tracking
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Moderation
    is_flagged = models.BooleanField(default=False)
    flagged_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='flagged_messages')
    flag_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)  # For scheduled messages
    
    class Meta:
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]
        ordering = ['created_at']


class MessageAttachment(models.Model):
    """Separate model for file attachments - supports multiple files per message"""
    FILE_CATEGORIES = [
        ('document', 'Document'),      # PDF, DOC, etc.
        ('worksheet', 'Worksheet'),    # Educational materials
        ('image', 'Image'),           # JPG, PNG, etc.
        ('video', 'Video'),           # Educational videos
        ('audio', 'Audio'),           # Voice notes, recordings
        ('code', 'Code'),             # Code files for CS classes
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    
    # File info
    file = models.FileField(upload_to='chat_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # in bytes
    file_type = models.CharField(max_length=50)  # MIME type
    category = models.CharField(max_length=20, choices=FILE_CATEGORIES)
    
    # Preview/thumbnail for images/videos
    thumbnail = models.ImageField(upload_to='chat_thumbnails/%Y/%m/%d/', null=True, blank=True)
    
    # Educational metadata
    is_homework = models.BooleanField(default=False)
    is_solution = models.BooleanField(default=False)
    
    # Security
    virus_scanned = models.BooleanField(default=False)
    virus_scan_result = models.CharField(max_length=50, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)


class MessageReaction(models.Model):
    """Support for reactions (useful for quick feedback in education)"""
    REACTION_TYPES = [
        ('👍', 'Thumbs Up'),
        ('❤️', 'Heart'),
        ('✅', 'Check'),
        ('❓', 'Question'),
        ('💡', 'Idea'),
        ('⭐', 'Star'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=2, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user', 'reaction']


class UserPresence(models.Model):
    """Track user online/offline status globally"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    
    # Which room they're currently viewing (if any)
    active_room = models.ForeignKey(ChatRoom, null=True, blank=True, on_delete=models.SET_NULL)
    
    # Connection info
    connection_id = models.CharField(max_length=100, blank=True)  # WebSocket connection ID
    device_type = models.CharField(max_length=20, blank=True)  # mobile, desktop, tablet
```

### A.2 Django Channels WebSocket Consumer

```python
# consumers/chat.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from datetime import datetime, timezone
import asyncio

class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat with educational features"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        
        # Verify user has access to this room
        if not await self.user_has_access():
            await self.close()
            return
            
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Update user presence
        await self.update_presence(online=True)
        
        # Accept connection
        await self.accept()
        
        # Send initial room state
        await self.send_room_state()
        
        # Notify others user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user_id": self.user.id,
                "username": self.user.get_full_name(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            
            handlers = {
                "message": self.handle_message,
                "typing": self.handle_typing,
                "read_receipt": self.handle_read_receipt,
                "reaction": self.handle_reaction,
                "file_upload": self.handle_file_upload,
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(data)
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
            
    async def handle_message(self, data):
        """Process and broadcast chat messages"""
        # Check permissions
        if not await self.can_send_message():
            await self.send_error("You don't have permission to send messages")
            return
            
        # Create message in database
        message = await self.create_message(
            content=data.get("content"),
            message_type=data.get("message_type", "text"),
            reply_to_id=data.get("reply_to"),
            metadata=data.get("metadata", {})
        )
        
        # Prepare message for broadcast
        message_data = await self.serialize_message(message)
        
        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message_data
            }
        )
        
        # Send push notifications to offline users
        await self.send_push_notifications(message)
        
    async def handle_typing(self, data):
        """Broadcast typing indicators"""
        is_typing = data.get("is_typing", False)
        
        # Update typing status in cache (expires after 5 seconds)
        cache_key = f"typing_{self.room_id}_{self.user.id}"
        if is_typing:
            cache.set(cache_key, True, timeout=5)
        else:
            cache.delete(cache_key)
            
        # Broadcast to others
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user_id": self.user.id,
                "username": self.user.get_full_name(),
                "is_typing": is_typing
            }
        )
        
    @database_sync_to_async
    def send_push_notifications(self, message):
        """Send push notifications to offline users using django-webpush"""
        from webpush import send_user_notification
        from .models import ChatParticipant, UserPresence
        
        # Get offline participants
        offline_participants = ChatParticipant.objects.filter(
            room=message.room,
            push_notifications=True,
            muted_until__lt=datetime.now(timezone.utc)
        ).exclude(user=message.sender).select_related('user')
        
        for participant in offline_participants:
            # Check if user is online
            try:
                presence = UserPresence.objects.get(user=participant.user)
                if presence.is_online and presence.active_room_id == message.room_id:
                    continue  # User is actively viewing this room
            except UserPresence.DoesNotExist:
                pass
                
            # Send push notification via django-webpush
            payload = {
                'head': f"New message from {message.sender.get_full_name()}",
                'body': message.content[:100] if message.content else "Sent a file",
                'icon': '/static/icon-192.png',
                'badge': '/static/badge-72.png',
                'url': f'/chat/{message.room_id}/',
                'tag': f'chat-{message.room_id}',
                'data': {
                    'room_id': str(message.room_id),
                    'message_id': str(message.id)
                }
            }
            
            try:
                send_user_notification(user=participant.user, payload=payload, ttl=1000)
            except Exception as e:
                print(f"Failed to send push notification: {e}")
```

### A.3 Frontend Chat Implementation

```html
<!-- templates/chat/room.html -->
<div id="chat-container" class="flex flex-col h-screen">
    <!-- Chat Header -->
    <div class="chat-header p-4 border-b">
        <h2>{{ room.name }}</h2>
        <div id="online-indicator" class="text-sm text-green-500"></div>
        <div id="typing-indicator" class="text-sm text-gray-500"></div>
    </div>
    
    <!-- Messages Container -->
    <div id="messages-container" class="flex-1 overflow-y-auto p-4">
        <div id="messages">
            <!-- Messages will be inserted here via WebSocket -->
        </div>
    </div>
    
    <!-- Input Area -->
    <div class="chat-input p-4 border-t">
        <!-- File Upload Progress -->
        <div id="upload-progress" class="hidden mb-2">
            <div class="bg-blue-200 rounded-full h-2">
                <div id="upload-bar" class="bg-blue-500 h-2 rounded-full" style="width: 0%"></div>
            </div>
        </div>
        
        <!-- Message Input -->
        <form id="message-form" class="flex gap-2">
            <input type="file" id="file-input" class="hidden" multiple 
                   accept="image/*,application/pdf,.doc,.docx">
            <button type="button" onclick="document.getElementById('file-input').click()" 
                    class="px-3 py-2 bg-gray-200 rounded">
                📎
            </button>
            <input 
                type="text" 
                id="message-input" 
                class="flex-1 px-4 py-2 border rounded-lg"
                placeholder="Type a message..."
                autocomplete="off"
            >
            <button type="submit" class="px-6 py-2 bg-blue-500 text-white rounded-lg">
                Send
            </button>
        </form>
    </div>
</div>

<script>
class ChatWebSocket {
    constructor(roomId) {
        this.roomId = roomId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.messageQueue = [];
        
        this.connect();
        this.setupEventListeners();
        this.setupOfflineSync();
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.roomId}/`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.flushMessageQueue();
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.attemptReconnect();
        };
    }
    
    handleMessage(data) {
        switch(data.type) {
            case 'message':
                this.displayMessage(data.message);
                this.showNotification(data.message);
                break;
            case 'typing':
                this.updateTypingIndicator(data);
                break;
            case 'user_joined':
            case 'user_left':
                this.updateOnlineUsers(data);
                break;
        }
    }
    
    sendMessage(content) {
        const message = {
            type: 'message',
            content: content,
            message_type: 'text',
            timestamp: new Date().toISOString()
        };
        
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            // Queue message for sending when reconnected
            this.messageQueue.push(message);
        }
    }
    
    displayMessage(message) {
        const messagesDiv = document.getElementById('messages');
        const messageEl = document.createElement('div');
        messageEl.className = 'message mb-4';
        
        messageEl.innerHTML = `
            <div class="flex items-start gap-3">
                <img src="${message.sender.avatar || '/static/default-avatar.png'}" 
                     class="w-10 h-10 rounded-full">
                <div class="flex-1">
                    <div class="flex items-baseline gap-2">
                        <span class="font-semibold">${message.sender.name}</span>
                        <span class="text-xs text-gray-500">${this.formatTime(message.created_at)}</span>
                    </div>
                    <div class="message-content mt-1">${this.escapeHtml(message.content)}</div>
                </div>
            </div>
        `;
        
        messagesDiv.appendChild(messageEl);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    
    setupEventListeners() {
        // Message form submission
        document.getElementById('message-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const input = document.getElementById('message-input');
            const content = input.value.trim();
            
            if (content) {
                this.sendMessage(content);
                input.value = '';
            }
        });
        
        // Typing indicator
        let typingTimeout;
        document.getElementById('message-input').addEventListener('input', (e) => {
            this.ws.send(JSON.stringify({type: 'typing', is_typing: true}));
            
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => {
                this.ws.send(JSON.stringify({type: 'typing', is_typing: false}));
            }, 2000);
        });
    }
    
    // Utility methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
}

// Initialize chat
document.addEventListener('DOMContentLoaded', () => {
    const roomId = '{{ room.id }}';
    window.chatSocket = new ChatWebSocket(roomId);
});
</script>
```

## Appendix B: Original Code Examples

### B.1 Complete Magic Link Implementation with django-sesame

```python
# accounts/views.py
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from sesame import utils as sesame_utils

User = get_user_model()

def request_magic_link(request):
    """Send magic link to user's email using django-sesame"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate magic link with django-sesame
            token = sesame_utils.get_token(user)
            magic_link = request.build_absolute_uri(
                reverse('magic-login') + f'?token={token}'
            )
            
            # Send email
            send_mail(
                subject='Your Login Link for Aprende Comigo',
                message=f'Click here to login: {magic_link}\n\nThis link expires in 10 minutes.',
                from_email='noreply@aprendecomigo.com',
                recipient_list=[email],
                html_message=f'''
                <h2>Login to Aprende Comigo</h2>
                <p>Click the button below to login:</p>
                <a href="{magic_link}" style="background: #3B82F6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Login Now
                </a>
                <p><small>This link expires in 10 minutes. If you didn't request this, please ignore this email.</small></p>
                '''
            )
            
            return render(request, 'accounts/check_email.html', {'email': email})
            
        except User.DoesNotExist:
            # Don't reveal if user exists
            return render(request, 'accounts/check_email.html', {'email': email})
    
    return render(request, 'accounts/request_magic_link.html')

def magic_login(request):
    """Verify magic link and login user"""
    # django-sesame handles the authentication automatically
    # if the token is valid, user will be logged in
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return render(request, 'accounts/invalid_link.html')

# URLs configuration
urlpatterns = [
    path('auth/request-link/', request_magic_link, name='request-magic-link'),
    path('auth/login/', magic_login, name='magic-login'),
]
```

### A.2 WebSocket Chat with Offline Support

```python
# chat/consumers.py
class ChatConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        
        # Save to database
        await self.save_message(message)
        
        # Try WebSocket delivery
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
        
        # Send push notification for offline users
        offline_users = await self.get_offline_users()
        for user in offline_users:
            await self.send_push_notification(
                user=user,
                title='New Message',
                body=message['text'][:100],
                data={'room_id': self.room_id}
            )
```

### A.3 Offline-First Data Sync

```javascript
// static/js/offline-sync.js
class OfflineSync {
    constructor() {
        this.db = new Dexie('AprendeComigo');
        this.db.version(1).stores({
            messages: '++id, room_id, timestamp, synced',
            tasks: '++id, type, data, synced'
        });
    }
    
    async saveMessage(message) {
        // Save to IndexedDB
        await this.db.messages.add({
            ...message,
            synced: false,
            timestamp: Date.now()
        });
        
        // Try to sync
        if (navigator.onLine) {
            await this.syncMessages();
        }
    }
    
    async syncMessages() {
        const unsynced = await this.db.messages
            .where('synced').equals(false)
            .toArray();
        
        for (const msg of unsynced) {
            try {
                await fetch('/api/messages/', {
                    method: 'POST',
                    body: JSON.stringify(msg)
                });
                
                await this.db.messages.update(msg.id, {synced: true});
            } catch (e) {
                console.log('Sync failed, will retry');
            }
        }
    }
}

// Listen for online event
window.addEventListener('online', () => {
    const sync = new OfflineSync();
    sync.syncMessages();
});
```

---

## Appendix B: Testing Strategy

### Testing Approach for Business Application

#### Browser Priority (Business Context)
| Browser | Usage % | Test Priority | Notes |
|---------|---------|---------------|--------|
| Chrome Desktop | 45% | Critical | Primary business use |
| Safari iOS | 25% | Critical | Mobile business users |
| Chrome Android | 20% | High | Field workers |
| Safari Desktop | 8% | Medium | Mac users |
| Firefox | 2% | Low | Minimal usage |

#### Milestone 0 Test Scenarios
1. **Complex UI Interactions**
   - Multi-step form data persistence
   - File upload progress and cancellation
   - Drag-and-drop on touch devices
   - Real-time dashboard updates

2. **Performance Benchmarks**
   - 100 concurrent HTMX requests
   - WebSocket with 500 connections
   - Page load with slow 3G
   - Server CPU/memory under load

3. **PWA Installation**
   - iOS Safari installation guide effectiveness
   - Android auto-prompt acceptance rate
   - Desktop PWA usage patterns

#### Automated Testing Strategy
```python
# Django tests for HTMX interactions
class HTMXTestCase(TestCase):
    def test_partial_update(self):
        response = self.client.get(
            '/dashboard/metrics/',
            HTTP_HX_REQUEST='true'
        )
        self.assertTemplateUsed(response, 'partials/metrics.html')
        self.assertContains(response, 'hx-swap-oob')
```

---