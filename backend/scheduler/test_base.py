"""
Base test classes for Scheduler API tests.

Provides common setup and utilities for testing scheduler API endpoints.
Follows DRF testing best practices with comprehensive test data setup.
"""
from datetime import date, datetime, time, timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    TeacherProfile,
    SchoolRole,
    SchoolSettings,
    EducationalSystem,
)
from django.utils import timezone
from .models import (
    ClassSchedule,
    TeacherAvailability,
    TeacherUnavailability,
    ClassType,
    ClassStatus,
    WeekDay,
)


class SchedulerAPITestCase(APITestCase):
    """
    Base test case for scheduler API tests.
    
    Provides:
    - Common test data setup (schools, users, teacher profiles, availability)
    - Helper methods for authentication and data creation
    - Standard assertion methods for API responses
    - Test data cleanup
    """
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data that doesn't change during test execution."""
        # Educational system and school
        cls.edu_system, _ = EducationalSystem.objects.get_or_create(
            code="test_system",
            defaults={"name": "Test Educational System", "description": "Test system"}
        )
        
        cls.school = School.objects.create(
            name="Test School",
            description="Primary test school"
        )
        
        cls.school2 = School.objects.create(
            name="Other School", 
            description="Secondary test school"
        )
        
        # School settings
        cls.school_settings = SchoolSettings.objects.create(
            school=cls.school,
            timezone="America/New_York",
            educational_system=cls.edu_system
        )
        
        # Test users
        cls.admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            name="Test Admin",
            password="testpass123"
        )
        
        cls.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            name="Test Teacher",
            password="testpass123"
        )
        
        cls.teacher_user2 = CustomUser.objects.create_user(
            email="teacher2@test.com",
            name="Second Teacher", 
            password="testpass123"
        )
        
        cls.student_user = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student",
            password="testpass123"
        )
        
        cls.student_user2 = CustomUser.objects.create_user(
            email="student2@test.com",
            name="Second Student",
            password="testpass123"
        )
        
        cls.unauthorized_user = CustomUser.objects.create_user(
            email="unauthorized@test.com",
            name="Unauthorized User",
            password="testpass123"
        )
        
        # Teacher profiles
        cls.teacher_profile = TeacherProfile.objects.create(
            user=cls.teacher_user,
            bio="Primary test teacher"
        )
        
        cls.teacher_profile2 = TeacherProfile.objects.create(
            user=cls.teacher_user2,
            bio="Secondary test teacher"
        )
        
        # School memberships
        SchoolMembership.objects.create(
            user=cls.admin_user,
            school=cls.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=cls.teacher_user,
            school=cls.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=cls.teacher_user2,
            school=cls.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=cls.student_user,
            school=cls.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=cls.student_user2,
            school=cls.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Test dates
        cls.today = timezone.now().date()
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.next_week = cls.today + timedelta(days=7)
        cls.past_date = cls.today - timedelta(days=7)
        
        # Ensure test dates fall on weekdays for availability
        while cls.tomorrow.weekday() >= 5:  # Skip weekends
            cls.tomorrow += timedelta(days=1)
            
        while cls.next_week.weekday() >= 5:  # Skip weekends  
            cls.next_week += timedelta(days=1)
        
        # Teacher availability (Monday-Friday 9AM-5PM)
        for day_name in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            TeacherAvailability.objects.create(
                teacher=cls.teacher_profile,
                school=cls.school,
                day_of_week=day_name,
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True
            )
            
            TeacherAvailability.objects.create(
                teacher=cls.teacher_profile2,
                school=cls.school,
                day_of_week=day_name,
                start_time=time(10, 0),
                end_time=time(16, 0),
                is_active=True
            )
    
    def setUp(self):
        """Set up data that might change during tests."""
        # Start each test with clean client
        self.client.logout()
        
        # Sample valid class data for API tests
        self.valid_class_data = {
            'teacher': self.teacher_profile.id,
            'student': self.student_user.id,
            'school': self.school.id,
            'title': 'Test Class',
            'scheduled_date': self.tomorrow.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'duration_minutes': 60,
            'class_type': ClassType.INDIVIDUAL,
        }
        
        self.valid_group_class_data = {
            **self.valid_class_data,
            'class_type': ClassType.GROUP,
            'max_participants': 3,
            'additional_students': [self.student_user2.id],
            'metadata': {
                'group_dynamics': 'collaborative',
                'interaction_level': 'high',
                'collaboration_type': 'peer_learning'
            }
        }
    
    # Helper methods for authentication
    def authenticate_as_admin(self):
        """Authenticate client as school admin."""
        self.client.force_authenticate(user=self.admin_user)
        
    def authenticate_as_teacher(self, teacher_user=None):
        """Authenticate client as teacher."""
        user = teacher_user or self.teacher_user
        self.client.force_authenticate(user=user)
        
    def authenticate_as_student(self, student_user=None):
        """Authenticate client as student."""
        user = student_user or self.student_user
        self.client.force_authenticate(user=user)
        
    def authenticate_as_unauthorized(self):
        """Authenticate client as user with no school permissions."""
        self.client.force_authenticate(user=self.unauthorized_user)
    
    # Helper methods for test data creation
    def create_class_schedule(self, **kwargs):
        """Create a test class schedule with sensible defaults."""
        defaults = {
            'teacher': self.teacher_profile,
            'student': self.student_user,
            'school': self.school,
            'title': 'Test Class',
            'scheduled_date': self.tomorrow,
            'start_time': time(10, 0),
            'end_time': time(11, 0),
            'duration_minutes': 60,
            'booked_by': self.student_user,
            'status': ClassStatus.SCHEDULED,
            'class_type': ClassType.INDIVIDUAL,
        }
        defaults.update(kwargs)
        return ClassSchedule.objects.create(**defaults)
    
    def create_teacher_unavailability(self, teacher=None, **kwargs):
        """Create teacher unavailability with sensible defaults."""
        defaults = {
            'teacher': teacher or self.teacher_profile,
            'school': self.school,
            'date': self.tomorrow,
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'reason': 'Test unavailability',
        }
        defaults.update(kwargs)
        return TeacherUnavailability.objects.create(**defaults)
    
    # Helper methods for API response assertions
    def assertValidationError(self, response, field_name=None):
        """Assert that response is a 400 validation error, optionally for specific field."""
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if field_name:
            self.assertIn(field_name, str(response.data).lower())
    
    def assertPermissionDenied(self, response):
        """Assert that response is a 403 permission denied error."""
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def assertNotFound(self, response):
        """Assert that response is a 404 not found error."""
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def assertCreatedWithData(self, response, expected_data=None):
        """Assert that response is 201 created with optional data validation."""
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        if expected_data:
            for key, value in expected_data.items():
                self.assertEqual(response.data.get(key), value, 
                               f"Expected {key}={value}, got {response.data.get(key)}")
                               
    def assertListResponse(self, response, expected_count=None):
        """Assert that response is a valid list response."""
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('results', response.data)
        if expected_count is not None:
            self.assertEqual(len(response.data['results']), expected_count)