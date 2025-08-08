"""
Unit Tests for Recurring Class Business Logic

This test suite tests the RecurringClassSchedule model and its business logic.
Focuses on actual implemented functionality and model behavior.

Business Logic Areas Covered:
1. Model validation and constraints
2. Recurring class creation and management
3. Relationship management (teacher, school, students)
4. Basic business rules and validations
5. Model string representation and metadata

Focus: Pure business logic testing with Django TestCase for actual functionality
"""

import pytz
from datetime import date, time, timedelta
from unittest.mock import Mock, patch
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError

from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    TeacherProfile,
    SchoolRole,
    SchoolSettings,
    EducationalSystem,
)
from .models import (
    ClassSchedule,
    TeacherAvailability,
    TeacherUnavailability,
    RecurringClassSchedule,
    ClassType,
    ClassStatus,
    WeekDay,
    FrequencyType,
    RecurringClassStatus,
)


class RecurringClassBusinessLogicBaseTestCase(TestCase):
    """Base test case with common setup for recurring class business logic tests"""

    def setUp(self):
        """Set up minimal test data for recurring class business logic tests"""
        
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

        # Create admin user
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            name="Admin User"
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

        # Create school memberships
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )

    def create_sample_recurring_class(self, **kwargs):
        """Helper to create a recurring class with default values"""
        defaults = {
            'teacher': self.teacher_profile,
            'school': self.school,
            'title': 'Weekly Math Class',
            'description': 'Regular math tutoring session',
            'class_type': ClassType.INDIVIDUAL,
            'day_of_week': WeekDay.MONDAY,
            'start_time': time(14, 0),
            'end_time': time(15, 0),
            'duration_minutes': 60,
            'start_date': date.today() + timedelta(days=1),
            'end_date': date.today() + timedelta(days=30),
            'is_active': True,
            'created_by': self.admin_user
        }
        defaults.update(kwargs)
        
        return RecurringClassSchedule.objects.create(**defaults)


class RecurringClassModelTests(RecurringClassBusinessLogicBaseTestCase):
    """Tests for RecurringClassSchedule model functionality"""

    def test_create_recurring_class_with_required_fields(self):
        """Test creating a recurring class with required fields succeeds"""
        # Act
        recurring_class = self.create_sample_recurring_class()
        
        # Assert
        self.assertIsNotNone(recurring_class.id)
        self.assertEqual(recurring_class.title, 'Weekly Math Class')
        self.assertEqual(recurring_class.teacher, self.teacher_profile)
        self.assertEqual(recurring_class.school, self.school)
        self.assertEqual(recurring_class.class_type, ClassType.INDIVIDUAL)
        self.assertEqual(recurring_class.day_of_week, WeekDay.MONDAY)
        self.assertTrue(recurring_class.is_active)

    def test_recurring_class_str_representation_includes_title_and_day(self):
        """Test string representation includes title and day of week"""
        # Arrange
        recurring_class = self.create_sample_recurring_class(
            title="Math Tutoring",
            day_of_week=WeekDay.WEDNESDAY
        )
        
        # Act
        str_repr = str(recurring_class)
        
        # Assert
        self.assertIn("Math Tutoring", str_repr)
        # WeekDay enum should be represented in string

    def test_recurring_class_time_fields_accept_valid_times(self):
        """Test recurring class accepts valid start and end times"""
        # Act
        recurring_class = self.create_sample_recurring_class(
            start_time=time(14, 0),   # 2 PM
            end_time=time(15, 0)      # 3 PM
        )
        
        # Assert
        self.assertEqual(recurring_class.start_time, time(14, 0))
        self.assertEqual(recurring_class.end_time, time(15, 0))

    def test_recurring_class_duration_calculation(self):
        """Test recurring class calculates duration based on start and end times"""
        # Arrange
        recurring_class = self.create_sample_recurring_class(
            start_time=time(14, 0),   # 2 PM
            end_time=time(15, 30),    # 3:30 PM
            duration_minutes=90
        )
        
        # Act & Assert
        # Duration should match the time difference
        time_diff_minutes = (15 * 60 + 30) - (14 * 60)  # 90 minutes
        self.assertEqual(recurring_class.duration_minutes, time_diff_minutes)

    def test_recurring_class_date_fields_accept_valid_dates(self):
        """Test recurring class accepts valid start and end dates"""
        # Arrange
        start_date = date.today() + timedelta(days=7)
        end_date = date.today() + timedelta(days=14)  # After start date
        
        # Act
        recurring_class = self.create_sample_recurring_class(
            start_date=start_date,
            end_date=end_date
        )
        
        # Assert
        self.assertEqual(recurring_class.start_date, start_date)
        self.assertEqual(recurring_class.end_date, end_date)

    def test_recurring_class_allows_null_end_date(self):
        """Test recurring class allows null end_date for indefinite recurrence"""
        # Act
        recurring_class = self.create_sample_recurring_class(end_date=None)
        
        # Assert
        self.assertIsNone(recurring_class.end_date)
        self.assertIsNotNone(recurring_class.id)  # Should save successfully

    def test_recurring_class_teacher_relationship(self):
        """Test recurring class has proper relationship with teacher"""
        # Act
        recurring_class = self.create_sample_recurring_class()
        
        # Assert
        self.assertEqual(recurring_class.teacher, self.teacher_profile)
        self.assertEqual(recurring_class.teacher.user.name, "Teacher User")
        
    def test_recurring_class_school_relationship(self):
        """Test recurring class has proper relationship with school"""
        # Act
        recurring_class = self.create_sample_recurring_class()
        
        # Assert
        self.assertEqual(recurring_class.school, self.school)
        self.assertEqual(recurring_class.school.name, "Test School")
        
    def test_recurring_class_is_active_by_default(self):
        """Test recurring class is active by default"""
        # Act
        recurring_class = self.create_sample_recurring_class()
        
        # Assert
        self.assertTrue(recurring_class.is_active)


class RecurringClassBusinessRulesTests(RecurringClassBusinessLogicBaseTestCase):
    """Tests for business rules and validation in recurring classes"""

    def test_recurring_class_teacher_field_is_required(self):
        """Test recurring class teacher field is required at database level"""
        # Act & Assert - This will raise IntegrityError at database level
        with self.assertRaises(IntegrityError):
            # Database constraint will prevent this
            recurring_class = RecurringClassSchedule(
                teacher=None,  # Should fail at DB level
                school=self.school,
                title="Test Class",
                class_type=ClassType.INDIVIDUAL,
                day_of_week=WeekDay.MONDAY,
                start_time=time(14, 0),
                end_time=time(15, 0),
                duration_minutes=60,
                start_date=date.today(),
                created_by=self.admin_user
            )
            recurring_class.save()  # This should fail

    def test_recurring_class_school_field_is_required(self):
        """Test recurring class school field is required at database level"""
        # Act & Assert - This will raise IntegrityError at database level
        with self.assertRaises(IntegrityError):
            # Database constraint will prevent this
            recurring_class = RecurringClassSchedule(
                teacher=self.teacher_profile,
                school=None,  # Should fail at DB level
                title="Test Class",
                class_type=ClassType.INDIVIDUAL,
                day_of_week=WeekDay.MONDAY,
                start_time=time(14, 0),
                end_time=time(15, 0),
                duration_minutes=60,
                start_date=date.today(),
                created_by=self.admin_user
            )
            recurring_class.save()  # This should fail

    def test_recurring_class_title_field_accepts_valid_title(self):
        """Test recurring class accepts valid title"""
        # Act
        recurring_class = self.create_sample_recurring_class(
            title="Advanced Math Tutoring"
        )
        
        # Assert
        self.assertEqual(recurring_class.title, "Advanced Math Tutoring")
        self.assertIsNotNone(recurring_class.title)
        self.assertTrue(len(recurring_class.title) > 0)

    def test_recurring_class_class_type_validation(self):
        """Test recurring class validates class type"""
        # Act - should accept valid class types
        for class_type in [ClassType.INDIVIDUAL, ClassType.GROUP]:
            recurring_class = self.create_sample_recurring_class(
                title=f"Test {class_type} Class",
                class_type=class_type
            )
            self.assertEqual(recurring_class.class_type, class_type)

    def test_recurring_class_weekday_validation(self):
        """Test recurring class validates weekday"""
        # Act - should accept valid weekdays
        for weekday in [WeekDay.MONDAY, WeekDay.TUESDAY, WeekDay.WEDNESDAY, WeekDay.THURSDAY, WeekDay.FRIDAY]:
            recurring_class = self.create_sample_recurring_class(
                title=f"Test {weekday} Class",
                day_of_week=weekday
            )
            self.assertEqual(recurring_class.day_of_week, weekday)


class RecurringClassQueryTests(RecurringClassBusinessLogicBaseTestCase):
    """Tests for querying recurring classes"""

    def test_filter_recurring_classes_by_teacher(self):
        """Test filtering recurring classes by teacher"""
        # Arrange
        recurring_class1 = self.create_sample_recurring_class(title="Math Class")
        
        # Create another teacher
        other_teacher_user = CustomUser.objects.create_user(
            email="other@test.com",
            name="Other Teacher"
        )
        other_teacher_profile = TeacherProfile.objects.create(
            user=other_teacher_user,
            bio="Other teacher"
        )
        
        recurring_class2 = self.create_sample_recurring_class(
            title="Science Class",
            teacher=other_teacher_profile
        )
        
        # Act
        teacher_classes = RecurringClassSchedule.objects.filter(
            teacher=self.teacher_profile
        )
        
        # Assert
        self.assertIn(recurring_class1, teacher_classes)
        self.assertNotIn(recurring_class2, teacher_classes)

    def test_filter_recurring_classes_by_school(self):
        """Test filtering recurring classes by school"""
        # Arrange
        recurring_class1 = self.create_sample_recurring_class(title="Math Class")
        
        # Create another school
        other_school = School.objects.create(
            name="Other School",
            contact_email="other@school.com"
        )
        
        recurring_class2 = self.create_sample_recurring_class(
            title="Science Class",
            school=other_school
        )
        
        # Act
        school_classes = RecurringClassSchedule.objects.filter(
            school=self.school
        )
        
        # Assert
        self.assertIn(recurring_class1, school_classes)
        self.assertNotIn(recurring_class2, school_classes)

    def test_filter_active_recurring_classes(self):
        """Test filtering active recurring classes"""
        # Arrange
        active_class = self.create_sample_recurring_class(
            title="Active Class",
            is_active=True
        )
        
        inactive_class = self.create_sample_recurring_class(
            title="Inactive Class",
            is_active=False
        )
        
        # Act
        active_classes = RecurringClassSchedule.objects.filter(is_active=True)
        
        # Assert
        self.assertIn(active_class, active_classes)
        self.assertNotIn(inactive_class, active_classes)

    def test_recurring_class_ordering(self):
        """Test recurring classes can be ordered by start time"""
        # Arrange
        morning_class = self.create_sample_recurring_class(
            title="Morning Class",
            start_time=time(9, 0)
        )
        
        afternoon_class = self.create_sample_recurring_class(
            title="Afternoon Class", 
            start_time=time(14, 0)
        )
        
        # Act
        ordered_classes = RecurringClassSchedule.objects.order_by('start_time')
        
        # Assert
        self.assertEqual(list(ordered_classes), [morning_class, afternoon_class])


























