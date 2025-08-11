"""
Comprehensive Unit Tests for Scheduler Models

This module provides comprehensive unit tests for all scheduler models,
focusing on business logic, validation, relationships, and scheduling-specific functionality.

Test Design Principles:
- Fast: Uses minimal setup with in-memory database
- Isolated: Each test validates exactly one behavior with one clear reason to fail
- Deterministic: No dependencies on network, filesystem, or external services
- Focused: Tests public APIs and observable outcomes, not implementation details
- Behavior-oriented: Tests business rules and workflows

Coverage Areas:
- Model Validation: Field constraints, validators, choices, custom validation
- Model Methods: All custom model methods and properties
- Model Relationships: Teacher-Student-School relationships
- Scheduling Logic: Time conflicts, availability windows, booking rules
- Status Workflows: Class lifecycle, cancellation, completion
- Edge Cases: Timezone handling, overlapping schedules, capacity limits
- Business Rules: Multi-tenant isolation, permission validation
"""

import pytz
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

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
    WeekDay,
    ClassType,
    ClassStatus,
    FrequencyType,
    RecurringClassStatus,
    ReminderType,
    CommunicationChannel,
    ReminderStatus,
    TeacherAvailability,
    TeacherUnavailability,
    ClassSchedule,
    RecurringClassSchedule,
    ReminderPreference,
    ClassReminder,
)


class SchedulerModelBaseTestCase(TestCase):
    """Base test case with common setup for scheduler model tests"""
    
    def setUp(self):
        """Set up minimal test data for scheduler model tests"""
        # Create educational system
        self.edu_system, _ = EducationalSystem.objects.get_or_create(
            code="test_system",
            defaults={"name": "Test Educational System"}
        )

        # Create schools
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com"
        )
        
        self.other_school = School.objects.create(
            name="Other School",
            contact_email="other@school.com"
        )
        
        # Create school settings
        self.school_settings = SchoolSettings.objects.create(
            school=self.school,
            educational_system=self.edu_system,
            timezone="America/New_York"
        )
        
        self.other_school_settings = SchoolSettings.objects.create(
            school=self.other_school,
            educational_system=self.edu_system,
            timezone="Europe/London"
        )

        # Create users
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            name="Admin User"
        )
        
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            name="Teacher User"
        )
        
        self.teacher_user2 = CustomUser.objects.create_user(
            email="teacher2@test.com",
            name="Second Teacher"
        )
        
        self.student_user = CustomUser.objects.create_user(
            email="student@test.com",
            name="Student User"
        )
        
        self.student_user2 = CustomUser.objects.create_user(
            email="student2@test.com",
            name="Second Student"
        )
        
        # Create teacher profiles
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Test teacher"
        )
        
        self.teacher_profile2 = TeacherProfile.objects.create(
            user=self.teacher_user2,
            bio="Second teacher"
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
        
        SchoolMembership.objects.create(
            user=self.teacher_user2,
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
            user=self.student_user2,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )

        # Test dates
        self.today = timezone.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)
        self.past_date = self.today - timedelta(days=7)


class TeacherAvailabilityModelTests(SchedulerModelBaseTestCase):
    """Tests for TeacherAvailability model functionality"""

    def test_create_availability_with_valid_data_succeeds(self):
        """Test creating teacher availability with valid data succeeds"""
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
        self.assertIsNotNone(availability.created_at)
        self.assertIsNotNone(availability.updated_at)

    def test_availability_str_representation_includes_teacher_and_time(self):
        """Test string representation includes teacher name, day, and time"""
        # Arrange
        availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.TUESDAY,
            start_time=time(10, 0),
            end_time=time(16, 0),
            is_active=True
        )
        
        # Act
        str_repr = str(availability)
        
        # Assert
        self.assertIn("Teacher User", str_repr)
        self.assertIn("Tuesday", str_repr)
        self.assertIn("10:00", str_repr)
        self.assertIn("16:00", str_repr)

    def test_availability_clean_validates_start_time_before_end_time(self):
        """Test clean method validates start_time is before end_time"""
        # Arrange
        availability = TeacherAvailability(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(17, 0),  # Later than end time
            end_time=time(9, 0),
            is_active=True
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            availability.clean()
        
        self.assertIn("End time must be after start time", str(context.exception))

    def test_availability_clean_accepts_equal_start_and_end_time(self):
        """Test clean method rejects equal start and end times"""
        # Arrange
        availability = TeacherAvailability(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(10, 0),  # Same as start time
            is_active=True
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError):
            availability.clean()

    def test_unique_together_constraint_prevents_duplicate_availability(self):
        """Test unique constraint on teacher, school, day, start_time"""
        # Arrange
        TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Act & Assert
        with self.assertRaises(IntegrityError):
            TeacherAvailability.objects.create(
                teacher=self.teacher_profile,
                school=self.school,
                day_of_week=WeekDay.MONDAY,
                start_time=time(9, 0),  # Same start time
                end_time=time(16, 0),   # Different end time
                is_active=True
            )

    def test_availability_ordering_by_day_and_start_time(self):
        """Test availability objects are ordered by day_of_week and start_time"""
        # Arrange
        late_monday = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(14, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        early_monday = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(12, 0),
            is_active=True
        )
        
        tuesday = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.TUESDAY,
            start_time=time(8, 0),
            end_time=time(12, 0),
            is_active=True
        )
        
        # Act
        ordered_availability = list(TeacherAvailability.objects.all())
        
        # Assert
        self.assertEqual(ordered_availability, [early_monday, late_monday, tuesday])

    def test_availability_defaults_to_active(self):
        """Test availability is_active defaults to True"""
        # Act
        availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0)
            # is_active not specified
        )
        
        # Assert
        self.assertTrue(availability.is_active)

    def test_availability_accepts_all_weekdays(self):
        """Test availability accepts all valid weekday choices"""
        # Act & Assert
        for weekday in WeekDay.choices:
            day_value = weekday[0]
            availability = TeacherAvailability.objects.create(
                teacher=self.teacher_profile,
                school=self.school,
                day_of_week=day_value,
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True
            )
            self.assertEqual(availability.day_of_week, day_value)
            availability.delete()  # Clean up for next iteration


class TeacherUnavailabilityModelTests(SchedulerModelBaseTestCase):
    """Tests for TeacherUnavailability model functionality"""

    def test_create_unavailability_with_valid_data_succeeds(self):
        """Test creating teacher unavailability with valid data succeeds"""
        # Act
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            reason="Doctor appointment",
            is_all_day=False
        )
        
        # Assert
        self.assertEqual(unavailability.teacher, self.teacher_profile)
        self.assertEqual(unavailability.school, self.school)
        self.assertEqual(unavailability.date, self.tomorrow)
        self.assertEqual(unavailability.start_time, time(10, 0))
        self.assertEqual(unavailability.end_time, time(12, 0))
        self.assertEqual(unavailability.reason, "Doctor appointment")
        self.assertFalse(unavailability.is_all_day)

    def test_create_all_day_unavailability_succeeds(self):
        """Test creating all-day unavailability succeeds"""
        # Act
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            reason="Sick day",
            is_all_day=True
        )
        
        # Assert
        self.assertEqual(unavailability.date, self.tomorrow)
        self.assertTrue(unavailability.is_all_day)
        self.assertIsNone(unavailability.start_time)
        self.assertIsNone(unavailability.end_time)

    def test_unavailability_str_representation_includes_teacher_and_date(self):
        """Test string representation includes teacher name and date"""
        # Arrange
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            start_time=time(14, 0),
            end_time=time(16, 0),
            reason="Meeting"
        )
        
        # Act
        str_repr = str(unavailability)
        
        # Assert
        self.assertIn("Teacher User", str_repr)
        self.assertIn(str(self.tomorrow), str_repr)
        self.assertIn("14:00", str_repr)
        self.assertIn("16:00", str_repr)

    def test_unavailability_str_representation_all_day_format(self):
        """Test string representation for all-day unavailability"""
        # Arrange
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            reason="Conference",
            is_all_day=True
        )
        
        # Act
        str_repr = str(unavailability)
        
        # Assert
        self.assertIn("Teacher User", str_repr)
        self.assertIn(str(self.tomorrow), str_repr)
        self.assertIn("All Day", str_repr)

    def test_unavailability_clean_validates_partial_day_requires_times(self):
        """Test clean method validates partial day unavailability requires start and end times"""
        # Arrange
        unavailability = TeacherUnavailability(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            is_all_day=False,
            # Missing start_time and end_time
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            unavailability.clean()
        
        self.assertIn("Start time and end time are required", str(context.exception))

    def test_unavailability_clean_validates_start_time_before_end_time(self):
        """Test clean method validates start_time is before end_time for partial day"""
        # Arrange
        unavailability = TeacherUnavailability(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            start_time=time(16, 0),  # Later than end time
            end_time=time(10, 0),
            is_all_day=False
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            unavailability.clean()
        
        self.assertIn("End time must be after start time", str(context.exception))

    def test_unavailability_clean_accepts_all_day_without_times(self):
        """Test clean method accepts all-day unavailability without times"""
        # Arrange
        unavailability = TeacherUnavailability(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            is_all_day=True,
            # No start_time or end_time
        )
        
        # Act & Assert (should not raise)
        unavailability.clean()

    def test_unique_together_constraint_prevents_duplicate_unavailability(self):
        """Test unique constraint on teacher, school, date, start_time"""
        # Arrange
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            is_all_day=False
        )
        
        # Act & Assert
        with self.assertRaises(IntegrityError):
            TeacherUnavailability.objects.create(
                teacher=self.teacher_profile,
                school=self.school,
                date=self.tomorrow,
                start_time=time(10, 0),  # Same start time
                end_time=time(14, 0),   # Different end time
                is_all_day=False
            )

    def test_unavailability_ordering_by_date_and_start_time(self):
        """Test unavailability objects are ordered by date and start_time"""
        # Arrange
        later_same_day = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            start_time=time(14, 0),
            end_time=time(16, 0),
            is_all_day=False
        )
        
        earlier_same_day = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            is_all_day=False
        )
        
        next_day = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.next_week,
            start_time=time(9, 0),
            end_time=time(11, 0),
            is_all_day=False
        )
        
        # Act
        ordered_unavailability = list(TeacherUnavailability.objects.all())
        
        # Assert
        self.assertEqual(ordered_unavailability, [earlier_same_day, later_same_day, next_day])


class ClassScheduleModelTests(SchedulerModelBaseTestCase):
    """Tests for ClassSchedule model functionality"""

    def test_create_class_schedule_with_valid_data_succeeds(self):
        """Test creating class schedule with valid data succeeds"""
        # Act
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Math Tutoring",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED
        )
        
        # Assert
        self.assertEqual(class_schedule.teacher, self.teacher_profile)
        self.assertEqual(class_schedule.student, self.student_user)
        self.assertEqual(class_schedule.school, self.school)
        self.assertEqual(class_schedule.title, "Math Tutoring")
        self.assertEqual(class_schedule.scheduled_date, self.tomorrow)
        self.assertEqual(class_schedule.start_time, time(10, 0))
        self.assertEqual(class_schedule.end_time, time(11, 0))
        self.assertEqual(class_schedule.duration_minutes, 60)
        self.assertEqual(class_schedule.booked_by, self.student_user)
        self.assertEqual(class_schedule.class_type, ClassType.INDIVIDUAL)
        self.assertEqual(class_schedule.status, ClassStatus.SCHEDULED)

    def test_class_schedule_str_representation_includes_title_and_date(self):
        """Test string representation includes title, date, and time"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Physics Session",
            scheduled_date=self.tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act
        str_repr = str(class_schedule)
        
        # Assert
        self.assertIn("Physics Session", str_repr)
        self.assertIn(str(self.tomorrow), str_repr)
        self.assertIn("14:00", str_repr)

    def test_class_schedule_clean_validates_start_time_before_end_time(self):
        """Test clean method validates start_time is before end_time"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(15, 0),  # Later than end time
            end_time=time(10, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.clean()
        
        self.assertIn("End time must be after start time", str(context.exception))

    def test_class_schedule_clean_rejects_past_date(self):
        """Test clean method rejects scheduling classes in the past"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.past_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.clean()
        
        self.assertIn("Cannot schedule classes in the past", str(context.exception))

    def test_class_schedule_clean_validates_student_school_membership(self):
        """Test clean method validates student is a member of the school"""
        # Arrange
        non_member_student = CustomUser.objects.create_user(
            email="nonmember@test.com",
            name="Non Member Student"
        )
        
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=non_member_student,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=non_member_student
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.clean()
        
        self.assertIn("Student must be a member of the school", str(context.exception))

    def test_class_schedule_clean_validates_teacher_school_membership(self):
        """Test clean method validates teacher is a member of the school"""
        # Arrange
        non_member_teacher_user = CustomUser.objects.create_user(
            email="nonmemberteacher@test.com",
            name="Non Member Teacher"
        )
        non_member_teacher_profile = TeacherProfile.objects.create(
            user=non_member_teacher_user,
            bio="Non member teacher"
        )
        
        class_schedule = ClassSchedule(
            teacher=non_member_teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.clean()
        
        self.assertIn("Teacher must be a member of the school", str(context.exception))

    def test_class_schedule_clean_validates_group_class_requires_max_participants(self):
        """Test clean method validates group classes require max_participants"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=None,  # Missing for group class
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.clean()
        
        self.assertIn("Max participants is required for group classes", str(context.exception))

    def test_class_schedule_clean_validates_group_class_positive_max_participants(self):
        """Test clean method validates group classes have positive max_participants"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=0,  # Invalid value
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.clean()
        
        self.assertIn("Max participants must be a positive integer", str(context.exception))

    def test_class_schedule_clean_removes_max_participants_for_individual_class(self):
        """Test clean method removes max_participants for individual classes"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Individual Class",
            class_type=ClassType.INDIVIDUAL,
            max_participants=5,  # Should be removed
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act
        class_schedule.clean()
        
        # Assert
        self.assertIsNone(class_schedule.max_participants)

    def test_class_schedule_can_be_cancelled_when_scheduled_and_future(self):
        """Test can_be_cancelled property returns True for future scheduled classes"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            status=ClassStatus.SCHEDULED
        )
        
        # Act & Assert
        self.assertTrue(class_schedule.can_be_cancelled)

    def test_class_schedule_cannot_be_cancelled_when_completed(self):
        """Test can_be_cancelled property returns False for completed classes"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            status=ClassStatus.COMPLETED
        )
        
        # Act & Assert
        self.assertFalse(class_schedule.can_be_cancelled)

    def test_class_schedule_cannot_be_cancelled_when_already_cancelled(self):
        """Test can_be_cancelled property returns False for already cancelled classes"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            status=ClassStatus.CANCELLED
        )
        
        # Act & Assert
        self.assertFalse(class_schedule.can_be_cancelled)

    def test_get_total_participants_returns_one_for_individual_class(self):
        """Test get_total_participants returns 1 for individual classes"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Individual Class",
            class_type=ClassType.INDIVIDUAL,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        self.assertEqual(class_schedule.get_total_participants(), 1)

    def test_get_total_participants_counts_additional_students_for_group_class(self):
        """Test get_total_participants counts main student plus additional students for group classes"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        class_schedule.additional_students.add(self.student_user2)
        
        # Act & Assert
        self.assertEqual(class_schedule.get_total_participants(), 2)  # Main student + 1 additional

    def test_can_add_participant_returns_false_for_individual_class(self):
        """Test can_add_participant returns False for individual classes"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Individual Class",
            class_type=ClassType.INDIVIDUAL,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        self.assertFalse(class_schedule.can_add_participant())

    def test_can_add_participant_returns_true_when_group_has_capacity(self):
        """Test can_add_participant returns True when group class has capacity"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        self.assertTrue(class_schedule.can_add_participant())

    def test_can_add_participant_returns_false_when_group_at_capacity(self):
        """Test can_add_participant returns False when group class is at capacity"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=2,  # Low capacity
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        class_schedule.additional_students.add(self.student_user2)
        
        # Act & Assert - At capacity (1 main + 1 additional = 2 total)
        self.assertFalse(class_schedule.can_add_participant())

    def test_add_participant_raises_error_for_individual_class(self):
        """Test add_participant raises ValidationError for individual classes"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Individual Class",
            class_type=ClassType.INDIVIDUAL,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.add_participant(self.student_user2)
        
        self.assertIn("Cannot add participants to individual classes", str(context.exception))

    def test_add_participant_raises_error_when_at_capacity(self):
        """Test add_participant raises ValidationError when at capacity"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=1,  # Only main student allowed
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.add_participant(self.student_user2)
        
        self.assertIn("Class has reached maximum capacity", str(context.exception))

    def test_add_participant_raises_error_when_user_is_main_student(self):
        """Test add_participant raises ValidationError when user is already main student"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.add_participant(self.student_user)  # Already main student
        
        self.assertIn("User is already the main student", str(context.exception))

    def test_add_participant_raises_error_when_user_already_additional_student(self):
        """Test add_participant raises ValidationError when user is already an additional student"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        class_schedule.additional_students.add(self.student_user2)
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.add_participant(self.student_user2)  # Already additional student
        
        self.assertIn("User is already a participant", str(context.exception))

    def test_add_participant_succeeds_when_valid(self):
        """Test add_participant succeeds when valid conditions are met"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act
        class_schedule.add_participant(self.student_user2)
        
        # Assert
        self.assertIn(self.student_user2, class_schedule.additional_students.all())
        self.assertEqual(class_schedule.get_total_participants(), 2)

    def test_is_at_capacity_returns_true_for_individual_class(self):
        """Test is_at_capacity returns True for individual classes"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Individual Class",
            class_type=ClassType.INDIVIDUAL,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        self.assertTrue(class_schedule.is_at_capacity())

    def test_is_at_capacity_returns_false_when_group_has_spots(self):
        """Test is_at_capacity returns False when group class has available spots"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        self.assertFalse(class_schedule.is_at_capacity())

    def test_is_at_capacity_returns_true_when_group_full(self):
        """Test is_at_capacity returns True when group class is full"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=2,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        class_schedule.additional_students.add(self.student_user2)
        
        # Act & Assert - Full (1 main + 1 additional = 2 total)
        self.assertTrue(class_schedule.is_at_capacity())

    def test_get_available_spots_returns_zero_for_individual_class(self):
        """Test get_available_spots returns 0 for individual classes"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Individual Class",
            class_type=ClassType.INDIVIDUAL,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        self.assertEqual(class_schedule.get_available_spots(), 0)

    def test_get_available_spots_returns_infinity_when_no_limit(self):
        """Test get_available_spots returns infinity when no max_participants limit"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=None,  # No limit
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        self.assertEqual(class_schedule.get_available_spots(), float('inf'))

    def test_get_available_spots_calculates_remaining_spots(self):
        """Test get_available_spots calculates remaining spots correctly"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=5,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        class_schedule.additional_students.add(self.student_user2)
        
        # Act & Assert - 5 max - 2 current = 3 remaining
        self.assertEqual(class_schedule.get_available_spots(), 3)


class ClassScheduleTimezoneTests(SchedulerModelBaseTestCase):
    """Tests for ClassSchedule timezone-related functionality"""

    def test_get_scheduled_datetime_in_teacher_timezone_uses_school_timezone(self):
        """Test get_scheduled_datetime_in_teacher_timezone uses school's timezone"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,  # America/New_York timezone
            title="Test Class",
            scheduled_date=date(2024, 1, 16),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act
        scheduled_dt = class_schedule.get_scheduled_datetime_in_teacher_timezone()
        
        # Assert
        expected_tz = pytz.timezone("America/New_York")
        self.assertEqual(scheduled_dt.tzinfo.zone, expected_tz.zone)
        self.assertEqual(scheduled_dt.date(), date(2024, 1, 16))
        self.assertEqual(scheduled_dt.time(), time(10, 0))

    def test_get_scheduled_datetime_in_teacher_timezone_fallback_to_utc(self):
        """Test get_scheduled_datetime_in_teacher_timezone falls back to UTC when school has no timezone"""
        # Arrange
        # Create school without settings/timezone
        school_no_tz = School.objects.create(
            name="No Timezone School",
            contact_email="notz@school.com"
        )
        
        # Add membership
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=school_no_tz,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=school_no_tz,
            title="Test Class",
            scheduled_date=date(2024, 1, 16),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act
        scheduled_dt = class_schedule.get_scheduled_datetime_in_teacher_timezone()
        
        # Assert
        expected_tz = pytz.timezone("UTC")
        self.assertEqual(scheduled_dt.tzinfo, expected_tz)

    def test_get_scheduled_datetime_utc_converts_to_utc(self):
        """Test get_scheduled_datetime_utc converts local time to UTC"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,  # America/New_York timezone (UTC-5 in January)
            title="Test Class",
            scheduled_date=date(2024, 1, 16),
            start_time=time(10, 0),  # 10 AM in New York = 3 PM UTC
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act
        scheduled_dt_utc = class_schedule.get_scheduled_datetime_utc()
        
        # Assert
        self.assertEqual(scheduled_dt_utc.tzinfo, pytz.UTC)
        self.assertEqual(scheduled_dt_utc.date(), date(2024, 1, 16))
        self.assertEqual(scheduled_dt_utc.time(), time(15, 0))  # 10 AM EST = 3 PM UTC

    def test_is_past_returns_false_for_future_class(self):
        """Test is_past property returns False for future classes"""
        # Arrange - Use tomorrow to ensure it's in the future
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Future Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        self.assertFalse(class_schedule.is_past)

    def test_is_past_returns_true_for_past_class(self):
        """Test is_past property returns True for past classes"""
        # Arrange - Use past_date to ensure it's in the past
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Past Class",
            scheduled_date=self.past_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        self.assertTrue(class_schedule.is_past)

    @patch('django.utils.timezone.now')
    def test_can_cancel_within_deadline_returns_false_too_close(self, mock_now):
        """Test can_cancel_within_deadline returns False when within deadline"""
        # Arrange - Mock current time to be 1 hour before class
        class_time = datetime.combine(self.tomorrow, time(10, 0))
        class_time_utc = pytz.timezone("America/New_York").localize(class_time).astimezone(pytz.UTC)
        mock_now.return_value = class_time_utc - timedelta(hours=1)  # 1 hour before class
        
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Soon Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert - 1 hour before, but deadline is 2 hours before
        self.assertFalse(class_schedule.can_cancel_within_deadline(hours_before=2))

    @patch('django.utils.timezone.now')
    def test_can_cancel_within_deadline_returns_true_before_deadline(self, mock_now):
        """Test can_cancel_within_deadline returns True when before deadline"""
        # Arrange - Mock current time to be 5 hours before class
        class_time = datetime.combine(self.tomorrow, time(10, 0))
        class_time_utc = pytz.timezone("America/New_York").localize(class_time).astimezone(pytz.UTC)
        mock_now.return_value = class_time_utc - timedelta(hours=5)  # 5 hours before class
        
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Future Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert - 5 hours before, deadline is 2 hours before
        self.assertTrue(class_schedule.can_cancel_within_deadline(hours_before=2))

    def test_get_class_duration_in_teacher_timezone_returns_start_and_end_times(self):
        """Test get_class_duration_in_teacher_timezone returns localized start and end datetime objects"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,  # America/New_York timezone
            title="Test Class",
            scheduled_date=date(2024, 1, 16),
            start_time=time(10, 0),
            end_time=time(11, 30),
            duration_minutes=90,
            booked_by=self.student_user
        )
        
        # Act
        start_dt, end_dt = class_schedule.get_class_duration_in_teacher_timezone()
        
        # Assert
        expected_tz = pytz.timezone("America/New_York")
        self.assertEqual(start_dt.tzinfo.zone, expected_tz.zone)
        self.assertEqual(end_dt.tzinfo.zone, expected_tz.zone)
        self.assertEqual(start_dt.time(), time(10, 0))
        self.assertEqual(end_dt.time(), time(11, 30))
        self.assertEqual(start_dt.date(), date(2024, 1, 16))
        self.assertEqual(end_dt.date(), date(2024, 1, 16))


class ClassScheduleMetadataTests(SchedulerModelBaseTestCase):
    """Tests for ClassSchedule metadata functionality"""

    def test_get_metadata_value_returns_value_when_exists(self):
        """Test get_metadata_value returns value when key exists"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={"difficulty_level": "intermediate", "topics": ["algebra", "geometry"]}
        )
        
        # Act & Assert
        self.assertEqual(class_schedule.get_metadata_value("difficulty_level"), "intermediate")
        self.assertEqual(class_schedule.get_metadata_value("topics"), ["algebra", "geometry"])

    def test_get_metadata_value_returns_default_when_key_missing(self):
        """Test get_metadata_value returns default when key doesn't exist"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={"difficulty_level": "intermediate"}
        )
        
        # Act & Assert
        self.assertIsNone(class_schedule.get_metadata_value("missing_key"))
        self.assertEqual(class_schedule.get_metadata_value("missing_key", "default"), "default")

    def test_get_metadata_value_returns_default_when_metadata_empty(self):
        """Test get_metadata_value returns default when metadata is empty"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={}
        )
        
        # Act & Assert
        self.assertEqual(class_schedule.get_metadata_value("any_key", "fallback"), "fallback")

    def test_update_metadata_adds_new_fields(self):
        """Test update_metadata adds new metadata fields"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={"existing": "value"}
        )
        
        # Act
        class_schedule.update_metadata({"new_field": "new_value", "another": "data"})
        
        # Assert
        class_schedule.refresh_from_db()
        self.assertEqual(class_schedule.metadata["existing"], "value")
        self.assertEqual(class_schedule.metadata["new_field"], "new_value")
        self.assertEqual(class_schedule.metadata["another"], "data")

    def test_update_metadata_overwrites_existing_fields(self):
        """Test update_metadata overwrites existing metadata fields"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={"difficulty_level": "beginner"}
        )
        
        # Act
        class_schedule.update_metadata({"difficulty_level": "advanced"})
        
        # Assert
        class_schedule.refresh_from_db()
        self.assertEqual(class_schedule.metadata["difficulty_level"], "advanced")

    def test_update_metadata_raises_error_for_invalid_input(self):
        """Test update_metadata raises ValidationError for non-dictionary input"""
        # Arrange
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule.update_metadata("not_a_dict")
        
        self.assertIn("Metadata updates must be a dictionary", str(context.exception))

    def test_validate_metadata_accepts_valid_difficulty_level(self):
        """Test metadata validation accepts valid difficulty levels"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={"difficulty_level": "intermediate"}
        )
        
        # Act & Assert - should not raise
        class_schedule._validate_metadata()

    def test_validate_metadata_rejects_invalid_difficulty_level(self):
        """Test metadata validation rejects invalid difficulty levels"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={"difficulty_level": "expert"}  # Invalid level
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule._validate_metadata()
        
        self.assertIn("Invalid difficulty level", str(context.exception))

    def test_validate_metadata_accepts_valid_topics_list(self):
        """Test metadata validation accepts valid topics as list of strings"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={"topics": ["algebra", "geometry", "trigonometry"]}
        )
        
        # Act & Assert - should not raise
        class_schedule._validate_metadata()

    def test_validate_metadata_rejects_topics_as_non_list(self):
        """Test metadata validation rejects topics that are not a list"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={"topics": "algebra"}  # String instead of list
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule._validate_metadata()
        
        self.assertIn("Topics must be a list of strings", str(context.exception))

    def test_validate_metadata_rejects_non_string_topics(self):
        """Test metadata validation rejects topics that contain non-string values"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={"topics": ["algebra", 123, "geometry"]}  # Number in list
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule._validate_metadata()
        
        self.assertIn("Each topic must be a string", str(context.exception))

    def test_validate_metadata_requires_group_fields_for_group_classes(self):
        """Test metadata validation requires specific fields for group classes when metadata is provided"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={"difficulty_level": "intermediate"}  # Missing required group fields
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            class_schedule._validate_metadata()
        
        self.assertIn("Group classes must include the following metadata fields", str(context.exception))
        self.assertIn("group_dynamics", str(context.exception))
        self.assertIn("interaction_level", str(context.exception))
        self.assertIn("collaboration_type", str(context.exception))

    def test_validate_metadata_accepts_complete_group_metadata(self):
        """Test metadata validation accepts complete metadata for group classes"""
        # Arrange
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            metadata={
                "group_dynamics": "collaborative",
                "interaction_level": "high",
                "collaboration_type": "peer_learning"
            }
        )
        
        # Act & Assert - should not raise
        class_schedule._validate_metadata()


class RecurringClassScheduleModelTests(SchedulerModelBaseTestCase):
    """Tests for RecurringClassSchedule model functionality"""

    def test_create_recurring_schedule_with_valid_data_succeeds(self):
        """Test creating recurring class schedule with valid data succeeds"""
        # Act
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Weekly Math Class",
            description="Regular math tutoring",
            class_type=ClassType.INDIVIDUAL,
            frequency_type=FrequencyType.WEEKLY,
            day_of_week=WeekDay.MONDAY,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Assert
        self.assertEqual(recurring_schedule.teacher, self.teacher_profile)
        self.assertEqual(recurring_schedule.school, self.school)
        self.assertEqual(recurring_schedule.title, "Weekly Math Class")
        self.assertEqual(recurring_schedule.class_type, ClassType.INDIVIDUAL)
        self.assertEqual(recurring_schedule.frequency_type, FrequencyType.WEEKLY)
        self.assertEqual(recurring_schedule.day_of_week, WeekDay.MONDAY)
        self.assertEqual(recurring_schedule.start_time, time(14, 0))
        self.assertEqual(recurring_schedule.end_time, time(15, 0))
        self.assertEqual(recurring_schedule.duration_minutes, 60)
        self.assertEqual(recurring_schedule.start_date, self.tomorrow)
        self.assertEqual(recurring_schedule.created_by, self.admin_user)
        self.assertEqual(recurring_schedule.status, RecurringClassStatus.ACTIVE)
        self.assertTrue(recurring_schedule.is_active)

    def test_recurring_schedule_str_representation_includes_title_frequency_and_day(self):
        """Test string representation includes title, frequency, and day"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Physics Tutoring",
            frequency_type=FrequencyType.BIWEEKLY,
            day_of_week=WeekDay.WEDNESDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act
        str_repr = str(recurring_schedule)
        
        # Assert
        self.assertIn("Physics Tutoring", str_repr)
        self.assertIn("Biweekly", str_repr)
        self.assertIn("Wednesday", str_repr)
        self.assertIn("10:00", str_repr)

    def test_recurring_schedule_clean_validates_start_time_before_end_time(self):
        """Test clean method validates start_time is before end_time"""
        # Arrange
        recurring_schedule = RecurringClassSchedule(
            teacher=self.teacher_profile,
            school=self.school,
            title="Test Class",
            day_of_week=WeekDay.MONDAY,
            start_time=time(15, 0),  # Later than end time
            end_time=time(10, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            recurring_schedule.clean()
        
        self.assertIn("End time must be after start time", str(context.exception))

    def test_recurring_schedule_clean_validates_end_date_after_start_date(self):
        """Test clean method validates end_date is after start_date"""
        # Arrange
        recurring_schedule = RecurringClassSchedule(
            teacher=self.teacher_profile,
            school=self.school,
            title="Test Class",
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            end_date=self.today,  # Before start date
            created_by=self.admin_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            recurring_schedule.clean()
        
        self.assertIn("End date must be after start date", str(context.exception))

    def test_recurring_schedule_clean_validates_group_class_requires_max_participants(self):
        """Test clean method validates group classes require max_participants"""
        # Arrange
        recurring_schedule = RecurringClassSchedule(
            teacher=self.teacher_profile,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=None,  # Missing for group class
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            recurring_schedule.clean()
        
        self.assertIn("Max participants is required for group classes", str(context.exception))

    def test_recurring_schedule_clean_validates_group_class_positive_max_participants(self):
        """Test clean method validates group classes have positive max_participants"""
        # Arrange
        recurring_schedule = RecurringClassSchedule(
            teacher=self.teacher_profile,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=0,  # Invalid value
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            recurring_schedule.clean()
        
        self.assertIn("Max participants is required for group classes", str(context.exception))

    def test_get_student_count_returns_number_of_enrolled_students(self):
        """Test get_student_count returns correct number of enrolled students"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        recurring_schedule.students.add(self.student_user, self.student_user2)
        
        # Act & Assert
        self.assertEqual(recurring_schedule.get_student_count(), 2)

    def test_add_student_succeeds_for_valid_group_class(self):
        """Test add_student succeeds when adding valid student to group class"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act
        recurring_schedule.add_student(self.student_user)
        
        # Assert
        self.assertIn(self.student_user, recurring_schedule.students.all())
        self.assertEqual(recurring_schedule.get_student_count(), 1)

    def test_add_student_raises_error_for_individual_class_with_student(self):
        """Test add_student raises ValidationError when adding second student to individual class"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Individual Class",
            class_type=ClassType.INDIVIDUAL,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        recurring_schedule.students.add(self.student_user)
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            recurring_schedule.add_student(self.student_user2)
        
        self.assertIn("Individual classes can only have one student", str(context.exception))

    def test_add_student_raises_error_when_at_capacity(self):
        """Test add_student raises ValidationError when class is at capacity"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=1,  # Low capacity
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        recurring_schedule.students.add(self.student_user)
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            recurring_schedule.add_student(self.student_user2)
        
        self.assertIn("Class has reached maximum capacity", str(context.exception))

    def test_add_student_raises_error_for_non_school_member(self):
        """Test add_student raises ValidationError when student is not a school member"""
        # Arrange
        non_member_student = CustomUser.objects.create_user(
            email="nonmember@test.com",
            name="Non Member Student"
        )
        
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            recurring_schedule.add_student(non_member_student)
        
        self.assertIn("Student must be a member of the school", str(context.exception))

    def test_remove_student_removes_student_from_class(self):
        """Test remove_student removes student from recurring class"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        recurring_schedule.students.add(self.student_user, self.student_user2)
        
        # Act
        recurring_schedule.remove_student(self.student_user)
        
        # Assert
        self.assertNotIn(self.student_user, recurring_schedule.students.all())
        self.assertIn(self.student_user2, recurring_schedule.students.all())
        self.assertEqual(recurring_schedule.get_student_count(), 1)

    def test_pause_series_changes_status_to_paused(self):
        """Test pause_series changes status to PAUSED and sets timestamps"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Active Class",
            status=RecurringClassStatus.ACTIVE,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act
        result = recurring_schedule.pause_series(paused_by=self.admin_user)
        
        # Assert
        self.assertTrue(result['success'])
        recurring_schedule.refresh_from_db()
        self.assertEqual(recurring_schedule.status, RecurringClassStatus.PAUSED)
        self.assertIsNotNone(recurring_schedule.paused_at)
        self.assertEqual(recurring_schedule.paused_by, self.admin_user)
        self.assertFalse(recurring_schedule.is_active)

    def test_pause_series_returns_error_when_already_paused(self):
        """Test pause_series returns error when series is already paused"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Paused Class",
            status=RecurringClassStatus.PAUSED,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act
        result = recurring_schedule.pause_series(paused_by=self.admin_user)
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('already paused', result['error'])

    def test_resume_series_changes_status_to_active(self):
        """Test resume_series changes status to ACTIVE and clears pause info"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Paused Class",
            status=RecurringClassStatus.PAUSED,
            paused_at=timezone.now(),
            paused_by=self.admin_user,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act
        result = recurring_schedule.resume_series(resumed_by=self.admin_user)
        
        # Assert
        self.assertTrue(result['success'])
        recurring_schedule.refresh_from_db()
        self.assertEqual(recurring_schedule.status, RecurringClassStatus.ACTIVE)
        self.assertIsNone(recurring_schedule.paused_at)
        self.assertIsNone(recurring_schedule.paused_by)
        self.assertTrue(recurring_schedule.is_active)

    def test_resume_series_returns_error_when_not_paused(self):
        """Test resume_series returns error when series is not paused"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Active Class",
            status=RecurringClassStatus.ACTIVE,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act
        result = recurring_schedule.resume_series(resumed_by=self.admin_user)
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('not paused', result['error'])

    def test_cancel_series_changes_status_to_cancelled(self):
        """Test cancel_series changes status to CANCELLED and sets timestamps"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Active Class",
            status=RecurringClassStatus.ACTIVE,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Act
        result = recurring_schedule.cancel_series(reason="Teacher unavailable", cancelled_by=self.admin_user)
        
        # Assert
        self.assertTrue(result['success'])
        recurring_schedule.refresh_from_db()
        self.assertEqual(recurring_schedule.status, RecurringClassStatus.CANCELLED)
        self.assertIsNotNone(recurring_schedule.cancelled_at)
        self.assertEqual(recurring_schedule.cancelled_by, self.admin_user)
        self.assertFalse(recurring_schedule.is_active)

    def test_get_future_instances_returns_future_scheduled_instances(self):
        """Test get_future_instances returns only future instances"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Test Class",
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        recurring_schedule.students.add(self.student_user)
        
        # Create a future instance
        future_instance = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Future Class",
            scheduled_date=self.next_week,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            recurring_schedule=recurring_schedule
        )
        
        # Create a past instance
        past_instance = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Past Class",
            scheduled_date=self.past_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            recurring_schedule=recurring_schedule
        )
        
        # Act
        future_instances = recurring_schedule.get_future_instances()
        
        # Assert
        self.assertIn(future_instance, future_instances)
        self.assertNotIn(past_instance, future_instances)

    def test_get_cancelled_occurrences_returns_cancelled_dates(self):
        """Test get_cancelled_occurrences returns list of cancelled occurrence dates"""
        # Arrange
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Test Class",
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        recurring_schedule.students.add(self.student_user)
        
        # Create cancelled instance
        cancelled_date = self.next_week
        cancelled_instance = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Cancelled Class",
            scheduled_date=cancelled_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            status=ClassStatus.CANCELLED,
            recurring_schedule=recurring_schedule
        )
        
        # Act
        cancelled_dates = recurring_schedule.get_cancelled_occurrences()
        
        # Assert
        self.assertIn(cancelled_date, cancelled_dates)


class ReminderPreferenceModelTests(SchedulerModelBaseTestCase):
    """Tests for ReminderPreference model functionality"""

    def test_create_reminder_preference_with_valid_data_succeeds(self):
        """Test creating reminder preference with valid data succeeds"""
        # Act
        preference = ReminderPreference.objects.create(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours=[24, 2, 0.5],
            communication_channels=["email", "push"],
            timezone_preference="America/New_York",
            is_active=True
        )
        
        # Assert
        self.assertEqual(preference.user, self.student_user)
        self.assertEqual(preference.school, self.school)
        self.assertEqual(preference.reminder_timing_hours, [24, 2, 0.5])
        self.assertEqual(preference.communication_channels, ["email", "push"])
        self.assertEqual(preference.timezone_preference, "America/New_York")
        self.assertTrue(preference.is_active)

    def test_reminder_preference_str_representation_includes_user_and_school(self):
        """Test string representation includes user name and school"""
        # Arrange
        preference = ReminderPreference.objects.create(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours=[24],
            communication_channels=["email"],
            is_active=True
        )
        
        # Act
        str_repr = str(preference)
        
        # Assert
        self.assertIn("Student User", str_repr)
        self.assertIn("Test School", str_repr)
        self.assertIn("Preferences", str_repr)

    def test_reminder_preference_str_representation_global_preferences(self):
        """Test string representation for global preferences (no school)"""
        # Arrange
        preference = ReminderPreference.objects.create(
            user=self.student_user,
            school=None,  # Global preferences
            reminder_timing_hours=[24],
            communication_channels=["email"],
            is_active=True
        )
        
        # Act
        str_repr = str(preference)
        
        # Assert
        self.assertIn("Student User", str_repr)
        self.assertIn("Global", str_repr)

    def test_reminder_preference_clean_validates_timing_hours_as_list(self):
        """Test clean method validates reminder_timing_hours is a list"""
        # Arrange
        preference = ReminderPreference(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours="not_a_list",  # Invalid type
            communication_channels=["email"],
            is_active=True
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            preference.clean()
        
        self.assertIn("Must be a list of numbers", str(context.exception))

    def test_reminder_preference_clean_validates_timing_hours_range(self):
        """Test clean method validates timing hours are within valid range"""
        # Arrange
        preference = ReminderPreference(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours=[24, 200],  # 200 is > 168 (1 week)
            communication_channels=["email"],
            is_active=True
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            preference.clean()
        
        self.assertIn("Hours must be numbers between 0 and 168", str(context.exception))

    def test_reminder_preference_clean_validates_negative_timing_hours(self):
        """Test clean method rejects negative timing hours"""
        # Arrange
        preference = ReminderPreference(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours=[-1, 24],  # Negative value
            communication_channels=["email"],
            is_active=True
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            preference.clean()
        
        self.assertIn("Hours must be numbers between 0 and 168", str(context.exception))

    def test_reminder_preference_clean_validates_communication_channels_as_list(self):
        """Test clean method validates communication_channels is a list"""
        # Arrange
        preference = ReminderPreference(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours=[24],
            communication_channels="email",  # Should be a list
            is_active=True
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            preference.clean()
        
        self.assertIn("Must be a list of channel names", str(context.exception))

    def test_reminder_preference_clean_validates_valid_communication_channels(self):
        """Test clean method validates communication channels are valid choices"""
        # Arrange
        preference = ReminderPreference(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours=[24],
            communication_channels=["email", "invalid_channel"],  # Invalid channel
            is_active=True
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            preference.clean()
        
        self.assertIn("Invalid channel", str(context.exception))

    def test_reminder_preference_clean_validates_timezone_preference(self):
        """Test clean method validates timezone_preference is a valid timezone"""
        # Arrange
        preference = ReminderPreference(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours=[24],
            communication_channels=["email"],
            timezone_preference="Invalid/Timezone",  # Invalid timezone
            is_active=True
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            preference.clean()
        
        self.assertIn("Invalid timezone", str(context.exception))

    def test_reminder_preference_unique_together_constraint(self):
        """Test unique constraint on user and school"""
        # Arrange
        ReminderPreference.objects.create(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours=[24],
            communication_channels=["email"],
            is_active=True
        )
        
        # Act & Assert
        with self.assertRaises(IntegrityError):
            ReminderPreference.objects.create(
                user=self.student_user,  # Same user
                school=self.school,      # Same school
                reminder_timing_hours=[2],
                communication_channels=["sms"],
                is_active=True
            )

    def test_get_for_user_returns_school_specific_preference(self):
        """Test get_for_user returns school-specific preference when available"""
        # Arrange
        school_preference = ReminderPreference.objects.create(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours=[24],
            communication_channels=["email"],
            is_active=True
        )
        
        # Act
        result = ReminderPreference.get_for_user(self.student_user, self.school)
        
        # Assert
        self.assertEqual(result, school_preference)

    def test_get_for_user_returns_global_preference_when_no_school_specific(self):
        """Test get_for_user returns global preference when no school-specific exists"""
        # Arrange
        global_preference = ReminderPreference.objects.create(
            user=self.student_user,
            school=None,  # Global preference
            reminder_timing_hours=[2],
            communication_channels=["push"],
            is_active=True
        )
        
        # Act
        result = ReminderPreference.get_for_user(self.student_user, None)  # Request global
        
        # Assert
        self.assertEqual(result, global_preference)

    def test_get_for_user_returns_default_when_no_preference_exists(self):
        """Test get_for_user returns default preferences when none exist"""
        # Act
        result = ReminderPreference.get_for_user(self.student_user, self.school)
        
        # Assert
        self.assertEqual(result.user, self.student_user)
        self.assertEqual(result.school, self.school)
        self.assertEqual(result.reminder_timing_hours, [24, 1])  # Default values
        self.assertEqual(result.communication_channels, ["email"])
        self.assertTrue(result.is_active)
        self.assertIsNone(result.pk)  # Not saved to database

    def test_get_default_preferences_returns_system_defaults(self):
        """Test get_default_preferences returns system default values"""
        # Act
        result = ReminderPreference.get_default_preferences(self.student_user, self.school)
        
        # Assert
        self.assertEqual(result.user, self.student_user)
        self.assertEqual(result.school, self.school)
        self.assertEqual(result.reminder_timing_hours, [24, 1])
        self.assertEqual(result.communication_channels, ["email"])
        self.assertIsNone(result.timezone_preference)
        self.assertTrue(result.is_active)


class ClassReminderModelTests(SchedulerModelBaseTestCase):
    """Tests for ClassReminder model functionality"""

    def setUp(self):
        super().setUp()
        # Create a class schedule for reminder tests
        self.class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )

    def test_create_class_reminder_with_valid_data_succeeds(self):
        """Test creating class reminder with valid data succeeds"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        
        # Act
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_24H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            subject="Class Reminder",
            message="Your class is tomorrow at 10 AM"
        )
        
        # Assert
        self.assertEqual(reminder.class_schedule, self.class_schedule)
        self.assertEqual(reminder.reminder_type, ReminderType.REMINDER_24H)
        self.assertEqual(reminder.recipient, self.student_user)
        self.assertEqual(reminder.recipient_type, "student")
        self.assertEqual(reminder.communication_channel, CommunicationChannel.EMAIL)
        self.assertEqual(reminder.scheduled_for, scheduled_for)
        self.assertEqual(reminder.status, ReminderStatus.PENDING)
        self.assertEqual(reminder.subject, "Class Reminder")
        self.assertEqual(reminder.message, "Your class is tomorrow at 10 AM")
        self.assertEqual(reminder.retry_count, 0)
        self.assertEqual(reminder.max_retries, 3)

    def test_class_reminder_str_representation_includes_type_and_recipient(self):
        """Test string representation includes reminder type, recipient, and class"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.CONFIRMATION,
            recipient=self.teacher_user,
            recipient_type="teacher",
            communication_channel=CommunicationChannel.SMS,
            scheduled_for=scheduled_for,
            subject="Class Confirmation",
            message="Class has been confirmed"
        )
        
        # Act
        str_repr = str(reminder)
        
        # Assert
        self.assertIn("Confirmation", str_repr)
        self.assertIn("Teacher User", str_repr)
        self.assertIn("Test Class", str_repr)

    def test_class_reminder_clean_validates_future_scheduled_time(self):
        """Test clean method validates scheduled_for is in the future for new reminders"""
        # Arrange
        past_time = timezone.now() - timedelta(hours=1)
        reminder = ClassReminder(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=past_time,  # Past time
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            reminder.clean()
        
        self.assertIn("Scheduled time must be in the future", str(context.exception))

    def test_class_reminder_clean_validates_retry_count_within_limit(self):
        """Test clean method validates retry_count doesn't exceed max_retries"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        reminder = ClassReminder(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            retry_count=5,  # Exceeds default max_retries of 3
            max_retries=3
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            reminder.clean()
        
        self.assertIn("Retry count cannot exceed max retries", str(context.exception))

    def test_class_reminder_unique_constraint_prevents_duplicates(self):
        """Test unique constraint prevents duplicate reminders for same recipient and channel"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_24H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.PENDING
        )
        
        # Act & Assert
        with self.assertRaises(IntegrityError):
            ClassReminder.objects.create(
                class_schedule=self.class_schedule,
                reminder_type=ReminderType.REMINDER_24H,  # Same type
                recipient=self.student_user,              # Same recipient
                recipient_type="student",
                communication_channel=CommunicationChannel.EMAIL,  # Same channel
                scheduled_for=scheduled_for,
                status=ReminderStatus.PENDING
            )

    def test_class_reminder_can_retry_returns_true_when_eligible(self):
        """Test can_retry returns True when reminder is eligible for retry"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.FAILED,
            retry_count=1,
            max_retries=3
        )
        
        # Act & Assert
        self.assertTrue(reminder.can_retry())

    def test_class_reminder_can_retry_returns_false_when_at_max_retries(self):
        """Test can_retry returns False when at maximum retry count"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.FAILED,
            retry_count=3,
            max_retries=3
        )
        
        # Act & Assert
        self.assertFalse(reminder.can_retry())

    def test_class_reminder_can_retry_returns_false_when_not_failed(self):
        """Test can_retry returns False when status is not FAILED"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.SENT,  # Not failed
            retry_count=1,
            max_retries=3
        )
        
        # Act & Assert
        self.assertFalse(reminder.can_retry())

    def test_class_reminder_mark_sent_updates_status_and_timestamp(self):
        """Test mark_sent updates status, timestamp, and external ID"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.PENDING
        )
        
        # Act
        reminder.mark_sent(external_message_id="ext_123")
        
        # Assert
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, ReminderStatus.SENT)
        self.assertIsNotNone(reminder.sent_at)
        self.assertEqual(reminder.external_message_id, "ext_123")

    def test_class_reminder_mark_failed_updates_status_and_increments_retry(self):
        """Test mark_failed updates status, error message, and increments retry count"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.PENDING,
            retry_count=1
        )
        
        # Act
        reminder.mark_failed(error_message="SMTP connection failed", increment_retry=True)
        
        # Assert
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, ReminderStatus.FAILED)
        self.assertEqual(reminder.error_message, "SMTP connection failed")
        self.assertEqual(reminder.retry_count, 2)

    def test_class_reminder_mark_failed_without_incrementing_retry(self):
        """Test mark_failed can update status without incrementing retry count"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.PENDING,
            retry_count=1
        )
        
        # Act
        reminder.mark_failed(error_message="Validation error", increment_retry=False)
        
        # Assert
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, ReminderStatus.FAILED)
        self.assertEqual(reminder.error_message, "Validation error")
        self.assertEqual(reminder.retry_count, 1)  # Not incremented

    def test_class_reminder_mark_cancelled_updates_status_and_metadata(self):
        """Test mark_cancelled updates status and adds cancellation reason to metadata"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.PENDING,
            metadata={"existing": "data"}
        )
        
        # Act
        reminder.mark_cancelled(reason="Class was cancelled")
        
        # Assert
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, ReminderStatus.CANCELLED)
        self.assertEqual(reminder.metadata["existing"], "data")  # Preserved
        self.assertEqual(reminder.metadata["cancellation_reason"], "Class was cancelled")

    def test_class_reminder_is_overdue_returns_false_for_pending_within_grace_period(self):
        """Test is_overdue returns False for pending reminders within grace period"""
        # Arrange - Schedule reminder for 10 minutes from now (within 30min grace period)
        scheduled_for = timezone.now() + timedelta(minutes=10)
        
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.PENDING
        )
        
        # Act & Assert
        self.assertFalse(reminder.is_overdue)

    def test_class_reminder_is_overdue_returns_true_for_pending_past_grace_period(self):
        """Test is_overdue returns True for pending reminders past grace period"""
        # Arrange - Schedule reminder for 1 hour ago (past 30min grace period)
        scheduled_for = timezone.now() - timedelta(hours=1)
        
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.PENDING
        )
        
        # Act & Assert
        self.assertTrue(reminder.is_overdue)

    def test_class_reminder_is_overdue_returns_false_for_non_pending_status(self):
        """Test is_overdue returns False for non-pending reminders regardless of time"""
        # Arrange
        scheduled_for = timezone.now() - timedelta(hours=2)  # Way past
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.SENT  # Not pending
        )
        
        # Act & Assert
        self.assertFalse(reminder.is_overdue)

    def test_class_reminder_time_until_send_returns_correct_timedelta(self):
        """Test time_until_send returns correct time difference for pending reminders"""
        # Arrange - schedule for 2 hours from now
        scheduled_for = timezone.now() + timedelta(hours=2)
        
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.PENDING
        )
        
        # Act
        time_until = reminder.time_until_send
        
        # Assert - Allow some tolerance for test execution time
        self.assertAlmostEqual(time_until.total_seconds(), 7200, delta=5)  # 2 hours = 7200 seconds

    def test_class_reminder_time_until_send_returns_none_for_non_pending(self):
        """Test time_until_send returns None for non-pending reminders"""
        # Arrange
        scheduled_for = timezone.now() + timedelta(hours=2)
        reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.REMINDER_1H,
            recipient=self.student_user,
            recipient_type="student",
            communication_channel=CommunicationChannel.EMAIL,
            scheduled_for=scheduled_for,
            status=ReminderStatus.SENT  # Not pending
        )
        
        # Act & Assert
        self.assertIsNone(reminder.time_until_send)


class SchedulerModelMultiTenantTests(SchedulerModelBaseTestCase):
    """Tests for multi-tenant isolation in scheduler models"""

    def test_teacher_availability_isolated_by_school(self):
        """Test teacher availability is properly isolated by school"""
        # Arrange - Create availability in main school
        availability1 = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Create availability in other school (with membership)
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.other_school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        availability2 = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.other_school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(16, 0),
            is_active=True
        )
        
        # Act - Query by school
        school1_availability = TeacherAvailability.objects.filter(school=self.school)
        school2_availability = TeacherAvailability.objects.filter(school=self.other_school)
        
        # Assert - Each school only sees its own availability
        self.assertIn(availability1, school1_availability)
        self.assertNotIn(availability2, school1_availability)
        self.assertIn(availability2, school2_availability)
        self.assertNotIn(availability1, school2_availability)

    def test_class_schedule_isolated_by_school(self):
        """Test class schedules are properly isolated by school"""
        # Arrange - Create class in main school
        class1 = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="School 1 Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user
        )
        
        # Create teacher and student memberships for other school
        other_teacher_user = CustomUser.objects.create_user(
            email="otherteacher@test.com",
            name="Other Teacher"
        )
        other_teacher_profile = TeacherProfile.objects.create(
            user=other_teacher_user,
            bio="Other teacher"
        )
        other_student_user = CustomUser.objects.create_user(
            email="otherstudent@test.com",
            name="Other Student"
        )
        
        SchoolMembership.objects.create(
            user=other_teacher_user,
            school=self.other_school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        SchoolMembership.objects.create(
            user=other_student_user,
            school=self.other_school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Create class in other school
        class2 = ClassSchedule.objects.create(
            teacher=other_teacher_profile,
            student=other_student_user,
            school=self.other_school,
            title="School 2 Class",
            scheduled_date=self.tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=other_student_user
        )
        
        # Act - Query by school
        school1_classes = ClassSchedule.objects.filter(school=self.school)
        school2_classes = ClassSchedule.objects.filter(school=self.other_school)
        
        # Assert - Each school only sees its own classes
        self.assertIn(class1, school1_classes)
        self.assertNotIn(class2, school1_classes)
        self.assertIn(class2, school2_classes)
        self.assertNotIn(class1, school2_classes)

    def test_recurring_class_schedule_isolated_by_school(self):
        """Test recurring class schedules are properly isolated by school"""
        # Arrange - Create recurring class in main school
        recurring1 = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="School 1 Recurring",
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=self.admin_user
        )
        
        # Create admin user for other school
        other_admin_user = CustomUser.objects.create_user(
            email="otheradmin@test.com",
            name="Other Admin"
        )
        SchoolMembership.objects.create(
            user=other_admin_user,
            school=self.other_school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        
        # Create teacher for other school
        other_teacher_user = CustomUser.objects.create_user(
            email="otherteacher2@test.com",
            name="Other Teacher 2"
        )
        other_teacher_profile = TeacherProfile.objects.create(
            user=other_teacher_user,
            bio="Other teacher 2"
        )
        SchoolMembership.objects.create(
            user=other_teacher_user,
            school=self.other_school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Create recurring class in other school
        recurring2 = RecurringClassSchedule.objects.create(
            teacher=other_teacher_profile,
            school=self.other_school,
            title="School 2 Recurring",
            day_of_week=WeekDay.TUESDAY,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            start_date=self.tomorrow,
            created_by=other_admin_user
        )
        
        # Act - Query by school
        school1_recurring = RecurringClassSchedule.objects.filter(school=self.school)
        school2_recurring = RecurringClassSchedule.objects.filter(school=self.other_school)
        
        # Assert - Each school only sees its own recurring classes
        self.assertIn(recurring1, school1_recurring)
        self.assertNotIn(recurring2, school1_recurring)
        self.assertIn(recurring2, school2_recurring)
        self.assertNotIn(recurring1, school2_recurring)

    def test_reminder_preferences_isolated_by_school(self):
        """Test reminder preferences are properly isolated by school"""
        # Arrange - Create preferences for main school
        pref1 = ReminderPreference.objects.create(
            user=self.student_user,
            school=self.school,
            reminder_timing_hours=[24],
            communication_channels=["email"],
            is_active=True
        )
        
        # Create user membership for other school
        SchoolMembership.objects.create(
            user=self.student_user,
            school=self.other_school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Create preferences for other school
        pref2 = ReminderPreference.objects.create(
            user=self.student_user,
            school=self.other_school,
            reminder_timing_hours=[2],
            communication_channels=["sms"],
            is_active=True
        )
        
        # Act - Query by school
        school1_prefs = ReminderPreference.objects.filter(school=self.school)
        school2_prefs = ReminderPreference.objects.filter(school=self.other_school)
        
        # Assert - Each school only sees its own preferences
        self.assertIn(pref1, school1_prefs)
        self.assertNotIn(pref2, school1_prefs)
        self.assertIn(pref2, school2_prefs)
        self.assertNotIn(pref1, school2_prefs)