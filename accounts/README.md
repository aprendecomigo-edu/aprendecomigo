# Accounts App

This app contains customized user models and authentication-related functionality.

## Authentication URLs

**IMPORTANT:** This app uses Django's default authentication URLs and views from `django.contrib.auth.urls` instead of custom implementations.

These include:
- `/login/` - Login view
- `/logout/` - Logout view
- `/password_change/` - Password change view
- `/password_change/done/` - Password change success view
- `/password_reset/` - Password reset view
- `/password_reset/done/` - Password reset sent view
- `/reset/<uidb64>/<token>/` - Password reset confirmation view
- `/reset/done/` - Password reset complete view

Custom password reset URLs are defined in this app's `urls.py` but they follow the same pattern as Django's defaults.

## Custom User Model

The app uses a custom user model (`CustomUser`) with:
- Email as the authentication field instead of username
- Additional fields like `name` and `phone_number`
- Custom user manager for creating users and superusers

## Testing

Tests for this app are split into:
- `tests.py` - Unit tests for models, views, and forms
- `tests_ui.py` - Selenium-based UI tests (more brittle, run separately)

Note that UI tests should use the correct URLs from Django's auth system.
