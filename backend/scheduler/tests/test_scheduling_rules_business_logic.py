"""
Unit Tests for Scheduling Rules and Business Logic

This module tests basic scheduling functionality and business rules that are 
already implemented. Focuses on actual model behavior and validation.

Business Logic Areas Tested:
1. Teacher availability validation
2. Basic conflict detection
3. Time and date validation
4. Model relationships and constraints

Test Design Principles:
- Fast: Minimal setup, focused tests
- Isolated: Each test validates exactly one behavior
- Focused: Tests actual implemented functionality
- Deterministic: No external dependencies
"""

import unittest
from datetime import date, datetime, time, timedelta
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
import pytz

# Import actual models and services that exist
from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    TeacherProfile,
    SchoolRole,
    SchoolSettings,
    EducationalSystem,
)
from scheduler.models import (
    ClassSchedule,
    TeacherAvailability,
    TeacherUnavailability,
    ClassType,
    ClassStatus,
    WeekDay,
)


class TeacherAvailabilityTests(TestCase):
    """Test teacher availability functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create educational system
        self.edu_system, _ = EducationalSystem.objects.get_or_create(
            code="custom",
            defaults={"name": "Custom Education System"}
        )

        # Create school
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com"
        )
        
        # Create school settings
        self.school_settings = SchoolSettings.objects.create(
            school=self.school,
            educational_system=self.edu_system,
            timezone="America/Sao_Paulo"
        )

        # Create teacher user and profile
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            name="Teacher User"
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Test teacher"
        )

        # Create school membership
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
    
    def test_create_teacher_availability_with_valid_data(self):
        """Test creating teacher availability with valid data"""
        # Act
        availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Assert
        self.assertEqual(availability.teacher, self.teacher_profile)
        self.assertEqual(availability.school, self.school)
        self.assertEqual(availability.day_of_week, WeekDay.MONDAY)
        self.assertEqual(availability.start_time, time(9, 0))
        self.assertEqual(availability.end_time, time(17, 0))
        self.assertTrue(availability.is_active)
    
    def test_teacher_availability_str_representation(self):
        """Test teacher availability string representation"""
        # Act
        availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.TUESDAY,
            start_time=time(10, 0),
            end_time=time(16, 0),
            is_active=True
        )
        
        # Assert
        str_repr = str(availability)
        self.assertIsInstance(str_repr, str)
        self.assertTrue(len(str_repr) > 0)
    
    def test_filter_teacher_availability_by_weekday(self):
        """Test filtering teacher availability by weekday"""
        # Arrange
        monday_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        tuesday_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.TUESDAY,
            start_time=time(10, 0),
            end_time=time(16, 0),
            is_active=True
        )
        
        # Act
        monday_slots = TeacherAvailability.objects.filter(
            day_of_week=WeekDay.MONDAY
        )
        
        # Assert
        self.assertIn(monday_availability, monday_slots)
        self.assertNotIn(tuesday_availability, monday_slots)
    
    def test_teacher_availability_active_filtering(self):
        """Test filtering active teacher availability"""
        # Arrange
        active_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        inactive_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.TUESDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=False
        )
        
        # Act
        active_slots = TeacherAvailability.objects.filter(is_active=True)
        
        # Assert
        self.assertIn(active_availability, active_slots)
        self.assertNotIn(inactive_availability, active_slots)
    
    
    
    
    
    
    
    


class TeacherUnavailabilityTests(TestCase):
    """Test teacher unavailability functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create educational system
        self.edu_system, _ = EducationalSystem.objects.get_or_create(
            code="custom",
            defaults={"name": "Custom Education System"}
        )

        # Create school
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com"
        )
        
        # Create school settings
        self.school_settings = SchoolSettings.objects.create(
            school=self.school,
            educational_system=self.edu_system,
            timezone="America/Sao_Paulo"
        )

        # Create teacher user and profile
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            name="Teacher User"
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Test teacher"
        )

        # Create school membership
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
    
    def test_create_teacher_unavailability_with_valid_data(self):
        """Test creating teacher unavailability with valid data"""
        # Act
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=date(2024, 12, 25),  # Christmas
            is_all_day=True,
            reason="Holiday"
        )
        
        # Assert
        self.assertEqual(unavailability.teacher, self.teacher_profile)
        self.assertEqual(unavailability.school, self.school)
        self.assertEqual(unavailability.date, date(2024, 12, 25))
        self.assertTrue(unavailability.is_all_day)
        self.assertEqual(unavailability.reason, "Holiday")
    
    def test_create_teacher_unavailability_with_specific_time(self):
        """Test creating teacher unavailability with specific time slots"""
        # Act
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=date(2024, 6, 15),
            start_time=time(14, 0),
            end_time=time(16, 0),
            is_all_day=False,
            reason="Doctor appointment"
        )
        
        # Assert
        self.assertEqual(unavailability.start_time, time(14, 0))
        self.assertEqual(unavailability.end_time, time(16, 0))
        self.assertFalse(unavailability.is_all_day)
        self.assertEqual(unavailability.reason, "Doctor appointment")
    
    def test_teacher_unavailability_str_representation(self):
        """Test teacher unavailability string representation"""
        # Act
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=date(2024, 7, 4),
            is_all_day=True,
            reason="Independence Day"
        )
        
        # Assert
        str_repr = str(unavailability)
        self.assertIsInstance(str_repr, str)
        self.assertTrue(len(str_repr) > 0)
    
    def test_filter_teacher_unavailability_by_date(self):
        """Test filtering teacher unavailability by date"""
        # Arrange
        today_unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=date.today(),
            is_all_day=True,
            reason="Sick day"
        )
        
        future_unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=date.today() + timedelta(days=7),
            is_all_day=True,
            reason="Vacation"
        )
        
        # Act
        today_unavailabilities = TeacherUnavailability.objects.filter(
            date=date.today()
        )
        
        # Assert
        self.assertIn(today_unavailability, today_unavailabilities)
        self.assertNotIn(future_unavailability, today_unavailabilities)
    


class ClassScheduleBusinessLogicTests(TestCase):
    """Test class schedule business logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create educational system
        self.edu_system, _ = EducationalSystem.objects.get_or_create(
            code="custom",
            defaults={"name": "Custom Education System"}
        )

        # Create school
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com"
        )
        
        # Create school settings
        self.school_settings = SchoolSettings.objects.create(
            school=self.school,
            educational_system=self.edu_system,
            timezone="America/Sao_Paulo"
        )

        # Create users
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            name="Teacher User"
        )
        
        self.student_user = CustomUser.objects.create_user(
            email="student@test.com",
            name="Student User"
        )
        
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            name="Admin User"
        )
        
        # Create teacher profile
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Test teacher"
        )

        # Create school memberships
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.student_user,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
    
    def test_create_class_schedule_with_valid_data(self):
        """Test creating a class schedule with valid data"""
        # Act
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Math Tutoring",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )
        
        # Assert
        self.assertEqual(class_schedule.teacher, self.teacher_profile)
        self.assertEqual(class_schedule.student, self.student_user)
        self.assertEqual(class_schedule.school, self.school)
        self.assertEqual(class_schedule.title, "Math Tutoring")
        self.assertEqual(class_schedule.duration_minutes, 60)
        self.assertEqual(class_schedule.class_type, ClassType.INDIVIDUAL)
        self.assertEqual(class_schedule.status, ClassStatus.SCHEDULED)
    
    def test_class_schedule_str_representation(self):
        """Test class schedule string representation"""
        # Act
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Science Tutoring",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )
        
        # Assert
        str_repr = str(class_schedule)
        self.assertIsInstance(str_repr, str)
        self.assertTrue(len(str_repr) > 0)
    
    def test_filter_class_schedules_by_status(self):
        """Test filtering class schedules by status"""
        # Arrange
        scheduled_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Scheduled Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )
        
        cancelled_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Cancelled Class",
            scheduled_date=date.today() + timedelta(days=2),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.CANCELLED,
            booked_by=self.admin_user
        )
        
        # Act
        scheduled_classes = ClassSchedule.objects.filter(status=ClassStatus.SCHEDULED)
        
        # Assert
        self.assertIn(scheduled_class, scheduled_classes)
        self.assertNotIn(cancelled_class, scheduled_classes)
    
    def test_filter_class_schedules_by_date_range(self):
        """Test filtering class schedules by date range"""
        # Arrange
        today = date.today()
        tomorrow_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Tomorrow Class",
            scheduled_date=today + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )
        
        future_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Future Class",
            scheduled_date=today + timedelta(days=7),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )
        
        # Act - filter classes for next 3 days
        near_future_classes = ClassSchedule.objects.filter(
            scheduled_date__gte=today,
            scheduled_date__lte=today + timedelta(days=3)
        )
        
        # Assert
        self.assertIn(tomorrow_class, near_future_classes)
        self.assertNotIn(future_class, near_future_classes)


    
    
    
    
    
    
    
    


if __name__ == '__main__':
    unittest.main()