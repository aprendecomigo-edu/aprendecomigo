"""
Unit Tests for Scheduler Models - Business Logic Focus

This module provides focused unit tests for scheduler model validation
and business rules that directly impact user functionality.

Test Design Principles:
- Fast: Minimal setup, focused on model validation
- Isolated: Each test validates exactly one business behavior
- Deterministic: No external dependencies
- Behavior-oriented: Tests outcomes that matter to users

Coverage Areas:
- Time and date validation logic
- Required field constraints
- Multi-tenant isolation
- Status workflow validation
"""

from datetime import date, datetime, time, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
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
    TeacherAvailability,
    TeacherUnavailability,
    ClassSchedule,
    RecurringClassSchedule,
)


class SchedulerModelBaseTestCase(TestCase):
    """Base test case with minimal setup for scheduler model tests"""
    
    def setUp(self):
        """Set up minimal test data for scheduler model tests"""
        # Create educational system
        self.edu_system, _ = EducationalSystem.objects.get_or_create(
            code="test_system",
            defaults={"name": "Test Educational System"}
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
            timezone="America/New_York"
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
        
        self.student_user = CustomUser.objects.create_user(
            email="student@test.com",
            name="Student User"
        )
        
        # Create teacher profile
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Test teacher profile"
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
            user=self.student_user,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )


class TeacherAvailabilityBusinessLogicTests(SchedulerModelBaseTestCase):
    """Test teacher availability business logic and validation"""

    def test_availability_time_window_validation(self):
        """Test business rule: availability start time must be before end time"""
        with self.assertRaises(ValidationError):
            availability = TeacherAvailability(
                teacher=self.teacher_profile,
                school=self.school,
                day_of_week=WeekDay.MONDAY,
                start_time=time(17, 0),  # 5 PM
                end_time=time(9, 0),     # 9 AM - invalid
                is_active=True
            )
            availability.full_clean()

    def test_availability_requires_teacher_field(self):
        """Test business rule: availability requires teacher field"""
        with self.assertRaises(IntegrityError):
            TeacherAvailability.objects.create(
                teacher=None,
                school=self.school,
                day_of_week=WeekDay.MONDAY,
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True
            )

    def test_availability_supports_multiple_windows_per_day(self):
        """Test business rule: teachers can have multiple availability windows per day"""
        # Create morning window
        morning = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(12, 0),
            is_active=True
        )
        
        # Create afternoon window
        afternoon = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(14, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Both should exist
        monday_windows = TeacherAvailability.objects.filter(
            teacher=self.teacher_profile,
            day_of_week=WeekDay.MONDAY
        )
        self.assertEqual(monday_windows.count(), 2)


class TeacherUnavailabilityBusinessLogicTests(SchedulerModelBaseTestCase):
    """Test teacher unavailability business logic and validation"""

    def test_unavailability_time_window_validation(self):
        """Test business rule: unavailability start time must be before end time"""
        with self.assertRaises(ValidationError):
            unavailability = TeacherUnavailability(
                teacher=self.teacher_profile,
                school=self.school,
                date=date.today() + timedelta(days=1),
                start_time=time(16, 0),  # 4 PM
                end_time=time(14, 0),    # 2 PM - invalid
                is_all_day=False,
                reason="Invalid time window"
            )
            unavailability.full_clean()

    def test_all_day_unavailability_business_logic(self):
        """Test business rule: all-day unavailability should not have specific times"""
        # All-day unavailability should allow null times
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=date.today() + timedelta(days=1),
            is_all_day=True,
            reason="Sick day"
        )
        
        self.assertTrue(unavailability.is_all_day)
        self.assertIsNone(unavailability.start_time)
        self.assertIsNone(unavailability.end_time)

    def test_partial_unavailability_requires_time_window(self):
        """Test business rule: partial unavailability must have start and end times"""
        # Partial unavailability should require specific times
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(16, 0),
            is_all_day=False,
            reason="Doctor appointment"
        )
        
        self.assertFalse(unavailability.is_all_day)
        self.assertEqual(unavailability.start_time, time(14, 0))
        self.assertEqual(unavailability.end_time, time(16, 0))


class ClassScheduleBusinessLogicTests(SchedulerModelBaseTestCase):
    """Test class schedule business logic and validation"""

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
                end_time=time(14, 0),    # 2 PM - invalid
                duration_minutes=60,
                class_type=ClassType.INDIVIDUAL,
                status=ClassStatus.SCHEDULED,
                booked_by=self.admin_user
            )
            class_schedule.full_clean()

    def test_class_schedule_accepts_valid_duration(self):
        """Test class schedule accepts valid duration values"""
        class_schedule = ClassSchedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Valid Duration",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )
        class_schedule.full_clean()
        class_schedule.save()
        
        self.assertEqual(class_schedule.duration_minutes, 60)

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
                booked_by=self.admin_user
            )
            class_schedule.full_clean()

    def test_class_schedule_status_updates_successfully(self):
        """Test class schedule status can be updated"""
        class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Test Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )
        
        class_schedule.status = ClassStatus.COMPLETED
        class_schedule.save()
        
        self.assertEqual(class_schedule.status, ClassStatus.COMPLETED)

    def test_group_class_stores_metadata(self):
        """Test group class can store additional metadata"""
        group_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Group Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.GROUP,
            max_participants=5,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user,
            metadata={'group_dynamics': 'collaborative'}
        )
        
        self.assertEqual(group_class.class_type, ClassType.GROUP)
        self.assertEqual(group_class.max_participants, 5)
        self.assertIn('group_dynamics', group_class.metadata)


class RecurringClassScheduleBusinessLogicTests(SchedulerModelBaseTestCase):
    """Test recurring class schedule business logic"""

    def test_recurring_class_time_validation(self):
        """Test business rule: recurring class start time must be before end time"""
        with self.assertRaises(ValidationError):
            recurring_class = RecurringClassSchedule(
                teacher=self.teacher_profile,
                school=self.school,
                title="Invalid Recurring Class",
                class_type=ClassType.INDIVIDUAL,
                day_of_week=WeekDay.MONDAY,
                start_time=time(15, 0),  # 3 PM
                end_time=time(14, 0),    # 2 PM - invalid
                duration_minutes=60,
                start_date=date.today() + timedelta(days=1),
                created_by=self.admin_user
            )
            recurring_class.full_clean()

    def test_recurring_class_date_sequence_validation(self):
        """Test business rule: end date must be after start date when provided"""
        with self.assertRaises(ValidationError):
            recurring_class = RecurringClassSchedule(
                teacher=self.teacher_profile,
                school=self.school,
                title="Invalid Date Sequence",
                class_type=ClassType.INDIVIDUAL,
                day_of_week=WeekDay.MONDAY,
                start_time=time(14, 0),
                end_time=time(15, 0),
                duration_minutes=60,
                start_date=date.today() + timedelta(days=7),
                end_date=date.today() + timedelta(days=1),  # Before start
                created_by=self.admin_user
            )
            recurring_class.full_clean()

    def test_recurring_class_allows_indefinite_schedule(self):
        """Test business rule: recurring classes can run indefinitely (null end date)"""
        recurring_class = RecurringClassSchedule.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            title="Indefinite Class",
            class_type=ClassType.INDIVIDUAL,
            day_of_week=WeekDay.MONDAY,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            start_date=date.today() + timedelta(days=1),
            end_date=None,  # Indefinite
            created_by=self.admin_user
        )
        
        self.assertIsNone(recurring_class.end_date)
        self.assertIsNotNone(recurring_class.id)


class SchedulerModelMultiTenantTests(SchedulerModelBaseTestCase):
    """Test multi-tenant isolation for scheduler models"""

    def test_teacher_availability_respects_school_boundaries(self):
        """Test availability queries are filtered by school"""
        other_school = School.objects.create(
            name="Other School",
            contact_email="other@school.com"
        )
        
        school1_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=other_school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(16, 0),
            is_active=True
        )
        
        school1_slots = TeacherAvailability.objects.filter(school=self.school)
        
        self.assertEqual(school1_slots.count(), 1)
        self.assertEqual(school1_slots.first(), school1_availability)

    def test_class_schedule_respects_school_boundaries(self):
        """Test class schedule queries are filtered by school"""
        other_school = School.objects.create(
            name="Other School",
            contact_email="other@school.com"
        )
        
        school1_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="School 1 Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )
        
        ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=other_school,
            title="School 2 Class",
            scheduled_date=date.today() + timedelta(days=2),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )
        
        school1_classes = ClassSchedule.objects.filter(school=self.school)
        
        self.assertEqual(school1_classes.count(), 1)
        self.assertEqual(school1_classes.first(), school1_class)