"""
Unit Tests for Recurring Class Business Logic

This test suite focuses on business validation rules and core functionality
for RecurringClassSchedule models, testing behavior that matters to users.

Business Logic Areas Covered:
1. Time validation rules (start < end time)
2. Date validation rules (end > start date)
3. Duration consistency validation
4. Required field validation
5. Multi-tenant isolation (school boundaries)
"""

from datetime import date, time, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from accounts.models import (
    CustomUser,
    EducationalSystem,
    School,
    SchoolMembership,
    SchoolRole,
    SchoolSettings,
    TeacherProfile,
)
from scheduler.models import (
    ClassType,
    RecurringClassSchedule,
    WeekDay,
)


class RecurringClassBusinessLogicBaseTestCase(TestCase):
    """Base test case with minimal setup for recurring class business logic tests"""

    def setUp(self):
        """Set up minimal test data for recurring class business logic tests"""

        # Create educational system
        self.edu_system, _ = EducationalSystem.objects.get_or_create(
            code="custom", defaults={"name": "Custom Education System"}
        )

        # Create school
        self.school = School.objects.create(name="Test School", contact_email="test@school.com")

        # Create school settings
        self.school_settings = SchoolSettings.objects.create(
            school=self.school, educational_system=self.edu_system, timezone="America/Sao_Paulo"
        )

        # Create admin user
        self.admin_user = CustomUser.objects.create_user(email="admin@test.com", name="Admin User")

        # Create teacher user and profile
        self.teacher_user = CustomUser.objects.create_user(email="teacher@test.com", name="Teacher User")

        self.teacher_profile = TeacherProfile.objects.create(user=self.teacher_user, bio="Test teacher")

        # Create school memberships
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        SchoolMembership.objects.create(
            user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

    def create_sample_recurring_class(self, **kwargs):
        """Helper to create a recurring class with default values"""
        defaults = {
            "teacher": self.teacher_profile,
            "school": self.school,
            "title": "Weekly Math Class",
            "description": "Regular math tutoring session",
            "class_type": ClassType.INDIVIDUAL,
            "day_of_week": WeekDay.MONDAY,
            "start_time": time(14, 0),
            "end_time": time(15, 0),
            "duration_minutes": 60,
            "start_date": date.today() + timedelta(days=1),
            "end_date": date.today() + timedelta(days=30),
            "is_active": True,
            "created_by": self.admin_user,
        }
        defaults.update(kwargs)

        return RecurringClassSchedule.objects.create(**defaults)


class RecurringClassModelTests(RecurringClassBusinessLogicBaseTestCase):
    """Tests for RecurringClassSchedule model core functionality"""

    def test_create_recurring_class_with_required_fields_succeeds(self):
        """Test creating a recurring class with required fields succeeds"""
        # Act
        recurring_class = self.create_sample_recurring_class()

        # Assert
        self.assertIsNotNone(recurring_class.id)
        self.assertEqual(recurring_class.title, "Weekly Math Class")
        self.assertEqual(recurring_class.teacher, self.teacher_profile)
        self.assertEqual(recurring_class.school, self.school)
        self.assertEqual(recurring_class.class_type, ClassType.INDIVIDUAL)
        self.assertEqual(recurring_class.day_of_week, WeekDay.MONDAY)
        self.assertTrue(recurring_class.is_active)

    def test_recurring_class_allows_null_end_date_for_indefinite_recurrence(self):
        """Test recurring class allows null end_date for indefinite recurrence"""
        # Act
        recurring_class = self.create_sample_recurring_class(end_date=None)

        # Assert
        self.assertIsNone(recurring_class.end_date)
        self.assertIsNotNone(recurring_class.id)  # Should save successfully


class RecurringClassBusinessRulesTests(RecurringClassBusinessLogicBaseTestCase):
    """Tests for business rules and validation in recurring classes"""

    def test_recurring_class_teacher_field_required(self):
        """Test recurring class requires teacher field"""
        with self.assertRaises(IntegrityError):
            recurring_class = RecurringClassSchedule(
                teacher=None,
                school=self.school,
                title="Test Class",
                class_type=ClassType.INDIVIDUAL,
                day_of_week=WeekDay.MONDAY,
                start_time=time(14, 0),
                end_time=time(15, 0),
                duration_minutes=60,
                start_date=date.today(),
                created_by=self.admin_user,
            )
            recurring_class.save()

    def test_recurring_class_school_field_required(self):
        """Test recurring class requires school field"""
        with self.assertRaises(IntegrityError):
            recurring_class = RecurringClassSchedule(
                teacher=self.teacher_profile,
                school=None,
                title="Test Class",
                class_type=ClassType.INDIVIDUAL,
                day_of_week=WeekDay.MONDAY,
                start_time=time(14, 0),
                end_time=time(15, 0),
                duration_minutes=60,
                start_date=date.today(),
                created_by=self.admin_user,
            )
            recurring_class.save()


class RecurringClassBusinessValidationTests(RecurringClassBusinessLogicBaseTestCase):
    """Tests for recurring class business validation rules"""

    def test_recurring_class_start_time_before_end_time_validation(self):
        """Test business rule: start time must be before end time"""
        # This should be validated at the business logic level
        with self.assertRaises(ValidationError):
            recurring_class = RecurringClassSchedule(
                teacher=self.teacher_profile,
                school=self.school,
                title="Invalid Time Class",
                class_type=ClassType.INDIVIDUAL,
                day_of_week=WeekDay.MONDAY,
                start_time=time(15, 0),  # Later time
                end_time=time(14, 0),  # Earlier time - should fail
                duration_minutes=60,
                start_date=date.today() + timedelta(days=1),
                created_by=self.admin_user,
            )
            recurring_class.full_clean()  # Trigger validation

    def test_recurring_class_end_date_after_start_date_validation(self):
        """Test business rule: end date must be after start date when provided"""
        with self.assertRaises(ValidationError):
            recurring_class = RecurringClassSchedule(
                teacher=self.teacher_profile,
                school=self.school,
                title="Invalid Date Class",
                class_type=ClassType.INDIVIDUAL,
                day_of_week=WeekDay.MONDAY,
                start_time=time(14, 0),
                end_time=time(15, 0),
                duration_minutes=60,
                start_date=date.today() + timedelta(days=7),
                end_date=date.today() + timedelta(days=1),  # Before start date
                created_by=self.admin_user,
            )
            recurring_class.full_clean()  # Trigger validation

    def test_recurring_class_accepts_valid_duration(self):
        """Test recurring class accepts valid duration values"""
        recurring_class = RecurringClassSchedule(
            teacher=self.teacher_profile,
            school=self.school,
            title="Valid Duration Class",
            class_type=ClassType.INDIVIDUAL,
            day_of_week=WeekDay.MONDAY,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            start_date=date.today() + timedelta(days=1),
            created_by=self.admin_user,
        )
        recurring_class.full_clean()
        recurring_class.save()

        self.assertEqual(recurring_class.duration_minutes, 60)

    def test_recurring_class_respects_school_boundaries(self):
        """Test recurring classes are filtered by school"""
        other_school = School.objects.create(name="Other School", contact_email="other@school.com")

        class1 = self.create_sample_recurring_class(title="School 1 Class")
        self.create_sample_recurring_class(title="School 2 Class", school=other_school)

        school1_classes = RecurringClassSchedule.objects.filter(school=self.school)

        self.assertEqual(school1_classes.count(), 1)
        self.assertEqual(school1_classes.first(), class1)
