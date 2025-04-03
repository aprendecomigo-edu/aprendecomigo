# Financial App Permissions

## Overview

The financials app implements a role-based permission system that ensures users can only access information they're authorized to see:

- **Administrators/Staff**: Full access to all financial data, reports, and management interfaces
- **Teachers**: Access only to their own compensation data
- **Students**: Access only to their own payment data
- **Anonymous Users**: No access, redirected to login

## Permission Implementation

### Access Control Approach

1. **Anonymous User Handling**
   - All financial pages require authentication
   - Unauthenticated users are redirected to the login page with a `next` parameter

2. **Role-Based Restrictions**
   - Admin-only views return 404 for non-admin authenticated users
   - User-specific views check object ownership before allowing access
   - Forbidden access attempts display 404 (Not Found) instead of 403 (Forbidden) for better user experience

### Custom Permission Decorators

The app implements a custom `@admin_required` decorator that:

```python
def admin_required(view_func):
    """Custom decorator for admin-only views that shows 404 for non-admin logged-in users"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/accounts/login/?next={request.path}')
        if is_staff_or_admin(request.user):
            return view_func(request, *args, **kwargs)
        # Return 404 for non-admin authenticated users
        raise Http404(_("Page not found"))
    return _wrapped_view
```

### View-Level Permission Checks

For views that need to check object ownership, we implement in-view permission checks:

```python
# Check permissions
if not (is_staff_or_admin(request.user) or payment.student == request.user):
    # Show 404 instead of 403
    raise Http404(_("Page not found"))
```

## Protected Resources

The following resources have permission restrictions:

### Admin-Only Resources

- Financial Dashboard (`/financials/`)
- Payment Report (`/financials/reports/payments/`)
- Compensation Report (`/financials/reports/compensations/`)
- Financial Summary (`/financials/reports/financial-summary/`)
- Payment Plan Management

### User-Specific Resources

- Student Payment List: Students see only their payments; admins see all
- Student Payment Detail: Students see only their own payment details; admins see all
- Teacher Compensation List: Teachers see only their compensations; admins see all
- Teacher Compensation Detail: Teachers see only their own compensation details; admins see all

## Testing

The permissions system is thoroughly tested in `financials/tests.py` with the `FinancialPermissionsTestCase` class that verifies:

1. Anonymous users are redirected to login
2. Non-admin users cannot access admin-only pages
3. Students/teachers can only access their own data
4. Admins can access all data

Each test follows a pattern:
- Test anonymous access (expect redirect to login)
- Test student access (expect success for own data, 404 for others)
- Test teacher access (expect success for own data, 404 for others)
- Test admin access (expect success for all data)

Example test:

```python
def test_student_payment_list_permissions(self):
    """Test permission restrictions for student payment list view"""
    url = reverse('financials:student_payment_list')

    # Anonymous user should be redirected to login
    response = self.client.get(url)
    self.assertEqual(response.status_code, 302)
    self.assertTrue('/accounts/login/' in response.url)

    # Student user should be able to access but see only their payments
    self.client.login(email='student@test.com', password='studentpass')
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Student A Package')
    self.assertNotContains(response, 'Student B Package')

    # Teacher user should get a 404 instead of 403
    self.client.login(email='teacher@test.com', password='teacherpass')
    response = self.client.get(url)
    self.assertEqual(response.status_code, 404)

    # Admin user should be able to see all payments
    self.client.login(email='admin@test.com', password='adminpass')
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Student A Package')
    self.assertContains(response, 'Student B Package')
```

## Best Practices Applied

1. **Clean User Experience**
   - Non-existent vs. forbidden distinction is hidden from users
   - Consistent 404 responses instead of 403 for better security

2. **Comprehensive Testing**
   - Every view has permission tests
   - Tests verify both access control and content filtering
   - Test data setup ensures clean separation of user data

3. **DRY Implementation**
   - Custom decorators reduce code duplication
   - Permission helper functions ensure consistent checking
