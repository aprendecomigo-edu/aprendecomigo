# Accounts App Documentation

## Overview

The accounts app manages users, authentication, authorization, and permissions for the Aprende Comigo platform. It serves as the foundation for the educational system, defining user roles (managers, teachers, students, parents) and implementing the security layer.

The app currently uses a passwordless approach with Time-based One-Time Password (TOTP) verification codes and Knox token-based authentication for session management.

## Key Components

### 1. Passwordless Authentication Flow with TOTP

- User requests a verification code by submitting their email
- System generates a TOTP secret key and sends the current code to the user's email
- TOTP codes are time-synchronized and change every 30 seconds
- User verifies their identity by entering the correct code
- Upon successful verification, a Knox token is issued for continued authentication

### 2. Knox Token Authentication

- Server-side token storage for improved security
- Token revocation capabilities (logout and logoutall endpoints)
- Support for multiple devices per user (each with its own token)
- Configurable token expiration (currently set to 10 hours)

### 3. Security Enhancements

- **Time-based One-Time Passwords**: Much more secure than static codes
- **Secure Token Storage**: Using SecureStore on the frontend with AsyncStorage fallback
- **Rate Limiting**:
  - 5 code requests per hour per IP
  - 10 verification attempts per hour per IP
- **Brute Force Protection**: Max 5 failed verification attempts before requiring a new code
- **Failed Attempt Tracking**: Monitoring and limiting invalid verification attempts
- **Consistent Authentication**: Base classes for all authenticated views and viewsets

## API Endpoints

- `POST /api/auth/request-code/`: Request a TOTP verification code
- `POST /api/auth/verify-code/`: Verify the TOTP code and get authentication token
- `POST /api/auth/logout/`: Invalidate the current token
- `POST /api/auth/logoutall/`: Invalidate all tokens for the user
- `GET/PUT /api/auth/profile/`: Get or update user profile

## TOTP Implementation Details

### Backend

- **Secret Key Generation**: Uses `pyotp` library to generate secure random base32 keys
- **Code Verification**: Validates TOTP codes against the stored secret
- **Code Expiry**: TOTP codes change every 30 seconds, reducing the window for attacks
- **QR Code Support**: Provisioning URIs are provided for authenticator app integration
- **Progressive Enhancement**: Fallback to email delivery for users without authenticator apps

### Email Delivery

Instead of requiring an authenticator app, the system sends the current TOTP code via email, providing:
- Enhanced security over static codes
- Familiar user experience (still using email verification)
- No need to install additional apps

### API Response Format

When requesting a verification code, the API response includes:
```json
{
  "message": "Verification code sent to your email",
  "secret": "BASE32_SECRET_KEY",
  "provisioning_uri": "otpauth://totp/test@example.com?secret=BASE32_SECRET_KEY&issuer=Aprende%20Comigo"
}
```

- The `secret` can be used by developers to generate valid codes during testing
- The `provisioning_uri` can be converted to a QR code for authenticator apps

## Implementation Details

### Frontend

- Token is stored securely using expo-secure-store when available
- API requests include the token in the Authorization header
- Automatic token handling in the API client

### Backend

- Django REST Framework with Knox authentication
- TOTP verification system with security limits
- Custom throttling classes for rate limiting
- Base classes for authenticated views:
  - `KnoxAuthenticatedAPIView`: Base class for simple API views
  - `KnoxAuthenticatedViewSet`: Base class for model viewsets

### Authentication Protection

All endpoints (except for the authentication endpoints) are protected with Knox authentication:

- Unauthenticated requests receive a 401 Unauthorized response
- Invalid tokens (expired, malformed, or tampered) are rejected
- Each user can only access their own resources
- Token expiration is enforced to mitigate token theft
- Comprehensive tests verify authentication behavior in all cases

## User Roles, Models, and Permissions

### User Types and Permissions

Based on our brainstorming sessions and product requirements, we've defined the following user roles:

1. **Manager (School Administrator)**
   - **Access Level**: System-wide administrative access
   - **Permissions**:
     - Manage all users (create, edit, deactivate)
     - Access all student and teacher information
     - Configure system settings and permissions
     - Generate and view reports
     - Manage financial information
     - Approve/reject teacher applications
     - Create and manage courses/classes
     - Access to onboarding for all users
     - Define which users can be inscribed and when

2. **Teacher**
   - **Access Level**: Access to assigned students and own information
   - **Permissions**:
     - Manage their own profile
     - Create and manage class materials
     - View and grade assigned students
     - Communicate with students and parents
     - Manage their availability and schedule
     - Access teaching resources
     - View their payment information
     - Manage classes and disciplines they teach

3. **Student**
   - **Access Level**: Access to own information and assigned classes
   - **Permissions**:
     - View their schedule and classes
     - Access assigned learning materials
     - Submit assignments and participate in classes
     - Communicate with teachers
     - View their own grades/progress
     - Manage their profile
     - View billing information
     - Register for available classes (if allowed)

4. **Parent**
   - **Access Level**: Access to linked students' information
   - **Permissions**:
     - View linked students' schedules and progress
     - Monitor linked students' grades
     - Communicate with teachers
     - Make payments
     - Receive notifications about student activity
     - Register new students (their children)
     - Manage consent and permissions for minor students

5. **Educational Functionary** *(proposed)*
   - **Access Level**: Administrative access without teaching capabilities
   - **Permissions**:
     - Assist with student registration
     - Manage calendars and scheduling
     - View (but not edit) student records
     - Handle administrative tasks
     - Support teachers and students with platform usage

### Current Models Implementation

The user system currently has these models:

- **CustomUser**: Base user model with common fields and authentication
  - Fields: email, name, phone_number, user_type
  - Handles authentication and base information

- **Student**: Profile model with student-specific information
  - Fields: school_year, birth_date, address, CC information
  - Linked to CustomUser via one-to-one relationship

- **Teacher**: Profile model with teacher-specific information
  - Fields: bio, specialty, education, hourly_rate, availability
  - Linked to CustomUser via one-to-one relationship

### Next Steps for Implementation

Based on the brainstorming images, current codebase analysis, and roadmap planning, we're focusing on these implementation priorities:

1. **Parent Profile Model**:
   - Create a Parent model similar to Student and Teacher models
   - Implement a many-to-many relationship with Student records
   - Add verification mechanism for parent-student relationships
   - Develop parent dashboard with views for children's information
   - Create APIs for parent-student linking

2. **Educational Functionary Role**:
   - Define and implement the educational functionary role
   - Create appropriate permission sets for administrative tasks
   - Develop interfaces for functionaries to assist with registration
   - Establish clear boundaries between functionary and teacher roles

3. **Permission Refinement**:
   - Create custom permission classes for each user type
   - Implement object-level permissions for Student and Teacher resources
   - Build middleware to enforce role-based access control consistently
   - Add audit logging for sensitive permission actions
   - Define who can access/edit what information across the platform

4. **Onboarding Flows**:
   - Complete student onboarding (profile creation, preferences)
   - Design and implement teacher onboarding with verification steps
   - Create parent registration and student linking process
   - Add administration approval steps where needed
   - Develop discipline/subject selection for students

5. **Authentication Enhancements**:
   - Implement proper token refresh mechanisms
   - Add session timeout handling
   - Integrate social login options (Google)
   - Consider optional password-based authentication as fallback
   - Enhance security logging and monitoring

## Design Decisions & Open Questions

Based on our brainstorming sessions, we've made several key decisions while identifying questions that need resolution before implementation.

### Recent Security Enhancements

We've implemented several security improvements to strengthen the accounts app:

1. **Removed Hardcoded Secrets**: Eliminated the default secret key in EmailVerificationCode model to prevent predictable TOTP seeds.

2. **Enhanced Permission System**: Implemented granular role-based access control with the following new permission classes:
   - `IsManagerOrAdmin`: Restricts actions to managers and administrators only
   - `IsOwnerOrManager`: Object-level permissions allowing both owners and managers/admins

3. **Comprehensive Test Coverage**: Added detailed security tests ensuring:
   - User list filtering based on role
   - Role-appropriate creation permissions
   - Object access restrictions
   - Verification secret key uniqueness

### Current Design Decisions

1. **Authentication Model: Passwordless with TOTP**
   - **Decision**: Use Time-based One-Time Password (TOTP) codes sent via email for authentication.
   - **Rationale**:
     - Eliminates password-related security issues (weak passwords, reuse, etc.)
     - Provides stronger security than simple email magic links
     - Familiar user experience (similar to 2FA)
     - No need for password reset flows

2. **User Profile Separation**
   - **Decision**: Separate core user model from role-specific profile models.
   - **Rationale**:
     - Maintains clean separation of concerns
     - Allows for role-specific fields and behaviors
     - Simpler to extend in the future
     - Role transitions can be handled by creating/updating profiles

3. **Permission Structure**
   - **Decision**: Use a role-based permission system with Django's built-in permissions framework.
   - **Rationale**:
     - Aligns with Django's built-in authentication
     - Simple to understand and implement
     - Flexible enough for current requirements

4. **Multi-tier User Types**
   - **Decision**: Implement a system with manager, teacher, student, parent, and (potentially) functionary roles.
   - **Rationale**:
     - Covers all the educational platform needs identified in brainstorming
     - Allows for clear permission boundaries
     - Maps closely to real-world educational structures

### Open Questions & Implementation Considerations

1. **Parent-Student Relationship**:
   - How to model and verify parent-student relationships?
   - Should parents be able to register students or should admin approval be required?
   - What level of access should parents have to student information?
   - How to handle verification of parent-child relationships?
   - Privacy concerns for student data
   - Legal requirements for minors vs. adult students

2. **Educational Functionary Role**:
   - Should there be a dedicated role for school staff who aren't teachers?
   - What permissions would this role have?
   - How would this role interact with teachers and students?
   - Administrative requirements vs. teaching requirements

3. **Multi-level Administrative Roles**:
   - Should we implement hierarchical admin roles (super admin, department admin, etc.)?
   - How to delegate permissions between admin levels?
   - Complexity vs. flexibility trade-off
   - Audit trail requirements
   - Delegation needs for larger organizations

4. **Student Age Considerations**:
   - How should permissions differ for adult students vs. minors?
   - Should adult students have parent-like permissions for their own accounts?

5. **Class/Subject Relationships**:
   - How to model subjects associated with classes?
   - Should teachers have different access levels for different subjects?
   - How many disciplines should a class have?

6. **Permission Inheritance**:
   - Should certain roles automatically inherit permissions from other roles?
   - Can users have multiple roles (e.g., teacher who is also a manager)?
   - Should admins be able to be teachers too?

7. **Social Login Integration**:
   - Should we integrate social login options, particularly Google authentication?
   - Benefits and drawbacks of OAuth integration
   - Support for multiple social providers
   - User preference and convenience vs. security implications

8. **Teacher Approval Workflow**:
   - How should new teacher onboarding be handled?
   - Admin approval for all new teachers vs. self-registration
   - Verification of credentials
   - Onboarding efficiency

## Implementation Guidelines

Based on our brainstorming and planning, here are guidelines for implementing the accounts app features.

### 1. User Model Extensions

When creating new user profile models (like the Parent model):

```python
class Parent(models.Model):
    """
    Parent profile model with additional fields specific to parents
    """
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="parent_profile"
    )
    # Parent-specific fields
    occupation = models.CharField(max_length=100, blank=True)
    relationship_to_student = models.CharField(
        max_length=50,
        choices=[
            ("parent", _("Parent")),
            ("guardian", _("Legal Guardian")),
            ("other", _("Other")),
        ],
    )
    # Many-to-many relationship with students
    students = models.ManyToManyField(
        "Student",
        related_name="parents",
        blank=True,
    )

    def save(self, *args, **kwargs):
        # Ensure the associated user has the parent type
        if self.user.user_type != "parent":
            self.user.user_type = "parent"
            self.user.save()
        super().save(*args, **kwargs)
```

### 2. Permission Implementation

Implement role-based permission classes:

```python
class IsManager(BasePermission):
    """
    Permission to only allow managers to access the view.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == "manager"

class CanAccessStudent(BasePermission):
    """
    Permission to only allow appropriate users to access student data.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.user_type == "manager":
            return True
        elif user.user_type == "teacher":
            # Check if teacher is assigned to this student
            return user.teacher_profile.students.filter(id=obj.id).exists()
        elif user.user_type == "parent":
            # Check if parent is linked to this student
            return user.parent_profile.students.filter(id=obj.id).exists()
        elif user.user_type == "student":
            # Students can only access their own data
            return user.id == obj.user.id
        return False
```

### 3. Using Base Classes

Always extend the provided base classes for new views or viewsets:

```python
# For simple API views
class MySecureAPIView(KnoxAuthenticatedAPIView):
    def get(self, request):
        # Your logic here - authentication is already handled
        return Response({"data": "Secure data"})

# For model-based views
class MyModelViewSet(KnoxAuthenticatedViewSet):
    serializer_class = MyModelSerializer

    def get_queryset(self):
        # Restrict queryset to user's data
        return MyModel.objects.filter(user=self.request.user)
```

### 4. Security Best Practices

When creating new views:

1. **Protect All Non-Authentication Endpoints**: Use the base classes for all views except those explicitly handling authentication
2. **Implement Proper Authorization**: Always check that users can only access their own data
3. **Add Rate Limiting**: Apply throttling to sensitive endpoints
4. **Handle Failures Gracefully**: Don't reveal sensitive information in error messages
5. **Test Authentication Logic**: Write tests to verify authentication behavior

### 5. Testing Guidelines

Ensure comprehensive testing of all authentication and authorization code:

```bash
# Run all account-related tests
pytest accounts/

# Run specific test files
pytest accounts/tests/test_auth.py

# Test specific functionality
pytest accounts/tests/test_permissions.py::TestStudentAccess
```
