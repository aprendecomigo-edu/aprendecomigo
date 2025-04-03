# Template Structure

This directory contains all the templates for the Aprende Comigo application.

## Organization

```
templates/
├── base.html                 # Main base template with common elements
├── dashboard/                # Dashboard templates
│   ├── base.html             # Dashboard specific base template
│   ├── index.html            # Redirects to appropriate dashboard
│   ├── admin.html            # Admin dashboard
│   ├── student.html          # Student dashboard
│   └── teacher.html          # Teacher dashboard
├── profile/                  # Profile templates
│   ├── base.html             # Profile page base template
│   └── edit.html             # Profile edit template
└── partials/                 # HTMX partial templates
    ├── navigation.html       # Navigation component
    ├── profile_card.html     # User profile card
    ├── notifications.html    # Notifications component
    ├── sessions_table.html   # Sessions table for admin
    └── upcoming_classes.html # Upcoming classes for students
```

## Usage

- All templates extend from `base.html`
- Dashboard templates extend from `dashboard/base.html`
- Profile templates extend from `profile/base.html`
- Partials are designed to be included or loaded via HTMX

## HTMX Integration

This template structure is designed to work with HTMX for dynamic updates:

1. HTMX is included in `base.html`
2. CSRF token is automatically included with `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'`
3. Partials are designed for use with HTMX attributes like `hx-get`, `hx-post`, `hx-target`
4. Action buttons use HTMX for seamless UI updates

## URL Structure

The recommended URL structure for this template system:

```python
# Dashboard URLs
path('dashboard/', views.dashboard, name='dashboard'),
path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),

# Profile URLs
path('profile/', views.profile, name='profile'),
path('profile/edit/', views.profile_edit, name='profile_edit'),
path('profile/update/', views.profile_update, name='profile_update'),

# HTMX endpoints
path('htmx/upcoming-classes/', views.upcoming_classes, name='upcoming_classes'),
path('htmx/today-schedule/', views.today_schedule, name='today_schedule'),
path('htmx/session-filter/', views.filter_sessions, name='filter_sessions'),
```
