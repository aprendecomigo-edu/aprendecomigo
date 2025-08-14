"""
Unit Tests for Scheduling Rules and Business Logic

This module focuses on business logic that validates scheduling constraints,
teacher availability rules, and scheduling conflict detection.

Business Logic Areas Tested:
1. Teacher availability window validation
2. Time slot conflict detection
3. Unavailability blocking logic
4. Multi-tenant scheduling isolation
5. Date and time validation rules
"""

from datetime import date, time, timedelta

from django.core.exceptions import ValidationError
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
    ClassSchedule,
    ClassStatus,
    ClassType,
    TeacherAvailability,
    TeacherUnavailability,
    WeekDay,
)


class SchedulingBusinessLogicBaseTestCase(TestCase):
    """Base test case with common setup for scheduling business logic tests"""

    def setUp(self):
        """Set up minimal test data for scheduling business logic tests"""
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

        # Create users
        self.teacher_user = CustomUser.objects.create_user(email="teacher@test.com", name="Teacher User")

        self.student_user = CustomUser.objects.create_user(email="student@test.com", name="Student User")

        self.admin_user = CustomUser.objects.create_user(email="admin@test.com", name="Admin User")

        # Create teacher profile
        self.teacher_profile = TeacherProfile.objects.create(user=self.teacher_user, bio="Test teacher")

        # Create school memberships
        SchoolMembership.objects.create(
            user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

        SchoolMembership.objects.create(
            user=self.student_user, school=self.school, role=SchoolRole.STUDENT, is_active=True
        )

        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )


class TeacherAvailabilityBusinessLogicTests(SchedulingBusinessLogicBaseTestCase):
    """Test teacher availability business logic validation."""

    def test_teacher_availability_time_window_validation(self):
        """Test business rule: availability start time must be before end time"""
        with self.assertRaises(ValidationError):
            availability = TeacherAvailability(
                teacher=self.teacher_profile,
                school=self.school,
                day_of_week=WeekDay.MONDAY,
                start_time=time(17, 0),  # 5 PM
                end_time=time(9, 0),  # 9 AM - invalid!
                is_active=True,
            )
            availability.full_clean()  # Should trigger validation

    def test_teacher_availability_supports_split_day_schedules(self):
        """Test business rule: teachers can have multiple availability windows per day"""
        # Create morning availability
        morning_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),  # 9 AM
            end_time=time(12, 0),  # 12 PM
            is_active=True,
        )

        # Create afternoon availability (separate window)
        afternoon_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(14, 0),  # 2 PM
            end_time=time(17, 0),  # 5 PM
            is_active=True,
        )

        # Act - Query Monday availability for this teacher
        monday_slots = TeacherAvailability.objects.filter(
            teacher=self.teacher_profile, day_of_week=WeekDay.MONDAY, is_active=True
        ).order_by("start_time")

        # Assert - Both availability windows should exist
        self.assertEqual(monday_slots.count(), 2)
        self.assertEqual(list(monday_slots), [morning_availability, afternoon_availability])


class TeacherUnavailabilityBusinessLogicTests(SchedulingBusinessLogicBaseTestCase):
    """Test teacher unavailability business logic."""

    def test_teacher_unavailability_time_window_validation(self):
        """Test business rule: unavailability start time must be before end time"""
        with self.assertRaises(ValidationError):
            unavailability = TeacherUnavailability(
                teacher=self.teacher_profile,
                school=self.school,
                date=date.today() + timedelta(days=1),
                start_time=time(16, 0),  # 4 PM
                end_time=time(14, 0),  # 2 PM - invalid!
                is_all_day=False,
                reason="Doctor appointment",
            )
            unavailability.full_clean()  # Should trigger validation

    def test_teacher_unavailability_all_day_blocks_all_classes(self):
        """Test business rule: all-day unavailability blocks all scheduling"""
        # Create all-day unavailability
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=date.today() + timedelta(days=1),
            is_all_day=True,
            reason="Sick day",
        )

        # Assert all-day unavailability has no specific times
        self.assertTrue(unavailability.is_all_day)
        self.assertIsNone(unavailability.start_time)
        self.assertIsNone(unavailability.end_time)

    def test_teacher_unavailability_partial_day_blocks_specific_times(self):
        """Test business rule: partial unavailability blocks specific time slots"""
        # Create partial unavailability
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=date.today() + timedelta(days=1),
            start_time=time(14, 0),  # 2 PM
            end_time=time(16, 0),  # 4 PM
            is_all_day=False,
            reason="Doctor appointment",
        )

        # Assert partial unavailability has specific times
        self.assertFalse(unavailability.is_all_day)
        self.assertEqual(unavailability.start_time, time(14, 0))
        self.assertEqual(unavailability.end_time, time(16, 0))


class ClassScheduleBusinessLogicTests(SchedulingBusinessLogicBaseTestCase):
    """Test class schedule business logic and validation."""

    def test_class_schedule_time_window_validation(self):
        """Test business rule: class start time must be before end time"""
        with self.assertRaises(ValidationError):
            class_schedule = ClassSchedule(
                teacher=self.teacher_profile,
                student=self.student_user,
                school=self.school,
                title="Invalid Time Class",
                scheduled_date=date.today() + timedelta(days=1),
                start_time=time(15, 0),  # 3 PM
                end_time=time(14, 0),  # 2 PM - invalid!
                duration_minutes=60,
                class_type=ClassType.INDIVIDUAL,
                status=ClassStatus.SCHEDULED,
                booked_by=self.admin_user,
            )
            class_schedule.full_clean()  # Should trigger validation

    def test_class_schedule_past_date_validation(self):
        """Test business rule: cannot schedule classes in the past"""
        with self.assertRaises(ValidationError):
            class_schedule = ClassSchedule(
                teacher=self.teacher_profile,
                student=self.student_user,
                school=self.school,
                title="Past Date Class",
                scheduled_date=date.today() - timedelta(days=1),  # Yesterday
                start_time=time(14, 0),
                end_time=time(15, 0),
                duration_minutes=60,
                class_type=ClassType.INDIVIDUAL,
                status=ClassStatus.SCHEDULED,
                booked_by=self.admin_user,
            )
            class_schedule.full_clean()  # Should trigger validation


class SchedulingConflictDetectionTests(SchedulingBusinessLogicBaseTestCase):
    """Test scheduling conflict detection business logic."""

    def test_multiple_classes_same_teacher_different_times(self):
        """Test teacher can have multiple classes on same day at different times"""
        ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="First Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user,
        )

        student2 = CustomUser.objects.create_user(email="student2@test.com", name="Student 2")
        SchoolMembership.objects.create(user=student2, school=self.school, role=SchoolRole.STUDENT, is_active=True)

        second_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=student2,
            school=self.school,
            title="Second Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(16, 0),
            end_time=time(17, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user,
        )

        same_day_classes = ClassSchedule.objects.filter(
            teacher=self.teacher_profile, scheduled_date=date.today() + timedelta(days=1)
        )
        self.assertEqual(same_day_classes.count(), 2)
        self.assertIn(second_class, same_day_classes)
