# Database Test Scenarios for QA Testing

This document provides Django management commands and database setup scenarios for comprehensive QA testing of the "Add me as teacher" button visibility logic and related UX features.

## Overview

The button visibility logic depends on whether the current user has an existing `TeacherProfile` record. These scenarios help create different user states for thorough testing.

## Prerequisites

```bash
cd /Users/anapmc/Code/aprendecomigo
source .venv/bin/activate
cd backend
```

## Scenario 1: User Without Teacher Profile (Button Should Show)

### Setup Commands
```bash
# Ensure user exists but has no teacher profile
python manage.py shell -c "
from accounts.models import CustomUser, TeacherProfile
user, created = CustomUser.objects.get_or_create(
    email='test.no.teacher@example.com',
    defaults={
        'name': 'Test User No Teacher',
        'user_type': 'school_owner',
        'is_admin': True
    }
)
# Remove any existing teacher profile
TeacherProfile.objects.filter(user=user).delete()
print(f'User created: {created}')
print(f'User has teacher profile: {TeacherProfile.objects.filter(user=user).exists()}')
"
```

### Expected Button State
- ✅ "Add me as teacher" button SHOULD be visible
- ✅ Button should be enabled and clickable

## Scenario 2: User With Existing Teacher Profile (Button Should Hide)

### Setup Commands
```bash
# Create user with teacher profile
python manage.py shell -c "
from accounts.models import CustomUser, TeacherProfile, Course
from django.utils import timezone

# Create user
user, created = CustomUser.objects.get_or_create(
    email='test.has.teacher@example.com',
    defaults={
        'name': 'Test User Has Teacher',
        'user_type': 'school_owner',
        'is_admin': True
    }
)

# Create teacher profile if it doesn't exist
teacher_profile, profile_created = TeacherProfile.objects.get_or_create(
    user=user,
    defaults={
        'bio': 'Test teacher profile',
        'specialty': 'Mathematics',
        'education': 'Masters in Education',
        'hourly_rate': 25.00,
        'availability': 'Weekdays 9-17',
        'address': 'Test Address',
        'phone_number': '+351912345678'
    }
)

print(f'User created: {created}')
print(f'Teacher profile created: {profile_created}')
print(f'User has teacher profile: {True}')
"
```

### Expected Button State
- ❌ "Add me as teacher" button SHOULD be hidden
- ✅ Only "Convidar professor" button should be visible

## Scenario 3: Multiple Users for Comprehensive Testing

### Setup Commands
```bash
# Create multiple test users with different states
python manage.py shell -c "
from accounts.models import CustomUser, TeacherProfile

# User 1: No teacher profile
user1, _ = CustomUser.objects.get_or_create(
    email='qa.user1@test.com',
    defaults={
        'name': 'QA User 1 - No Teacher',
        'user_type': 'school_owner',
        'is_admin': True
    }
)
TeacherProfile.objects.filter(user=user1).delete()

# User 2: Has teacher profile
user2, _ = CustomUser.objects.get_or_create(
    email='qa.user2@test.com',
    defaults={
        'name': 'QA User 2 - Has Teacher',
        'user_type': 'school_owner',
        'is_admin': True
    }
)
TeacherProfile.objects.get_or_create(
    user=user2,
    defaults={
        'bio': 'QA Test Teacher',
        'specialty': 'Science',
        'education': 'Bachelor in Science',
        'hourly_rate': 20.00,
        'availability': 'Flexible',
        'address': 'QA Test Address',
        'phone_number': '+351987654321'
    }
)

# User 3: Regular teacher (not school owner)
user3, _ = CustomUser.objects.get_or_create(
    email='qa.teacher@test.com',
    defaults={
        'name': 'QA Regular Teacher',
        'user_type': 'teacher',
        'is_admin': False
    }
)
TeacherProfile.objects.get_or_create(
    user=user3,
    defaults={
        'bio': 'Regular teacher account',
        'specialty': 'Language Arts',
        'education': 'Bachelor in Literature',
        'hourly_rate': 18.00,
        'availability': 'Mornings',
        'address': 'Teacher Address',
        'phone_number': '+351123456789'
    }
)

print('Test users created:')
print(f'User 1 (no teacher): {user1.email} - Has profile: {TeacherProfile.objects.filter(user=user1).exists()}')
print(f'User 2 (has teacher): {user2.email} - Has profile: {TeacherProfile.objects.filter(user=user2).exists()}')
print(f'User 3 (regular teacher): {user3.email} - Has profile: {TeacherProfile.objects.filter(user=user3).exists()}')
"
```

## Scenario 4: Dynamic State Change Testing

### Commands for State Transitions
```bash
# Remove teacher profile for state transition testing
python manage.py shell -c "
from accounts.models import CustomUser, TeacherProfile
user = CustomUser.objects.get(email='test.has.teacher@example.com')
TeacherProfile.objects.filter(user=user).delete()
print(f'Teacher profile removed for {user.email}')
print(f'User now has teacher profile: {TeacherProfile.objects.filter(user=user).exists()}')
"

# Add teacher profile back
python manage.py shell -c "
from accounts.models import CustomUser, TeacherProfile
user = CustomUser.objects.get(email='test.has.teacher@example.com')
teacher_profile, created = TeacherProfile.objects.get_or_create(
    user=user,
    defaults={
        'bio': 'Restored teacher profile',
        'specialty': 'Physics',
        'education': 'PhD in Physics',
        'hourly_rate': 30.00,
        'availability': 'Evenings',
        'address': 'Physics Dept',
        'phone_number': '+351555123456'
    }
)
print(f'Teacher profile restored for {user.email}')
print(f'User now has teacher profile: {True}')
"
```

## Scenario 5: Course Data for Teacher Registration

### Ensure Courses Exist for Testing
```bash
# Create test courses for teacher onboarding
python manage.py shell -c "
from accounts.models import Course

courses_data = [
    {
        'name': 'Matemática - 5º Ano',
        'code': 'MAT-5',
        'educational_system': 'Portuguese',
        'education_level': 'Elementary',
        'description': 'Mathematics for 5th grade students'
    },
    {
        'name': 'Português - 6º Ano',
        'code': 'POR-6',
        'educational_system': 'Portuguese',
        'education_level': 'Elementary',
        'description': 'Portuguese language for 6th grade students'
    },
    {
        'name': 'Ciências - 7º Ano',
        'code': 'SCI-7',
        'educational_system': 'Portuguese',
        'education_level': 'Middle School',
        'description': 'Science subjects for 7th grade students'
    }
]

for course_data in courses_data:
    course, created = Course.objects.get_or_create(
        code=course_data['code'],
        defaults=course_data
    )
    print(f'Course {course.code}: {\"created\" if created else \"exists\"}')
"
```

## Verification Commands

### Check Current User States
```bash
# Verify all test user states
python manage.py shell -c "
from accounts.models import CustomUser, TeacherProfile

test_emails = [
    'test.no.teacher@example.com',
    'test.has.teacher@example.com',
    'qa.user1@test.com',
    'qa.user2@test.com',
    'qa.teacher@test.com'
]

print('Current user states:')
print('-' * 50)
for email in test_emails:
    try:
        user = CustomUser.objects.get(email=email)
        has_profile = TeacherProfile.objects.filter(user=user).exists()
        print(f'{email}: Has teacher profile = {has_profile}')
    except CustomUser.DoesNotExist:
        print(f'{email}: User does not exist')
"
```

### List All Teachers
```bash
# See all teachers in the system
python manage.py shell -c "
from accounts.models import TeacherProfile

teachers = TeacherProfile.objects.select_related('user').all()
print(f'Total teachers in system: {teachers.count()}')
print('-' * 40)
for teacher in teachers:
    print(f'{teacher.user.name} ({teacher.user.email})')
    print(f'  Specialty: {teacher.specialty}')
    print(f'  User Type: {teacher.user.user_type}')
    print()
"
```

## Cleanup Commands

### Remove Test Data
```bash
# Clean up test users and profiles
python manage.py shell -c "
from accounts.models import CustomUser, TeacherProfile

test_emails = [
    'test.no.teacher@example.com',
    'test.has.teacher@example.com',
    'qa.user1@test.com',
    'qa.user2@test.com',
    'qa.teacher@test.com'
]

for email in test_emails:
    try:
        user = CustomUser.objects.get(email=email)
        TeacherProfile.objects.filter(user=user).delete()
        user.delete()
        print(f'Deleted user: {email}')
    except CustomUser.DoesNotExist:
        print(f'User {email} not found')
"
```

## Usage Instructions for QA Testing

1. **Setup Phase**: Run the appropriate scenario setup command based on what you want to test
2. **Testing Phase**:
   - Login as the test user
   - Navigate to /users page
   - Check Teachers tab for button visibility
   - Test button functionality if visible
3. **Verification Phase**: Use verification commands to confirm database state matches UI behavior
4. **Cleanup Phase**: Run cleanup commands after testing to reset environment

## Integration with QA Test Cases

These scenarios directly support:
- **FORM-004**: "Add me as teacher" Button Visibility Logic
- **FORM-002**: Add Teacher Profile Self-Registration Modal
- **FORM-005**: Enhanced Student Creation Modal UX

Use these database states to systematically test all combinations of user states and verify that the button visibility logic works correctly in all scenarios.
