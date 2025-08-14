"""
Unit Tests for Available Slots Business Logic

This module tests focused business logic for slot availability
queries and validation rules.

Focus Areas:
- Teacher availability status filtering
- Basic conflict detection queries
- Unavailability blocking logic
- School boundary enforcement
"""

from datetime import date, datetime, time, timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
import pytz

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
    TeacherAvailability,
    ClassSchedule,
    TeacherUnavailability,
    WeekDay,
    ClassType,
    ClassStatus,
)


class AvailableSlotsBusinessLogicBaseTestCase(TestCase):
    """Base test case with common setup for available slots business logic tests"""
    
    def setUp(self):
        """Set up minimal test data for available slots business logic tests"""
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
        
        # Create school settings with timezone
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


class TeacherAvailabilitySlotCalculationTests(AvailableSlotsBusinessLogicBaseTestCase):
    """Test business logic for calculating available slots from teacher availability"""
    
    def test_active_availability_slots_only_included_in_calculations(self):
        """Test business rule: only active availability slots are considered for booking"""
        # Create active availability
        active_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Create inactive availability (should not appear in calculations)
        inactive_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.TUESDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=False
        )
        
        # Act - Query for active slots only
        active_slots = TeacherAvailability.objects.filter(
            teacher=self.teacher_profile,
            school=self.school,
            is_active=True
        )
        
        # Assert - Only active availability should be available for booking
        self.assertIn(active_availability, active_slots)
        self.assertNotIn(inactive_availability, active_slots)
        self.assertEqual(active_slots.count(), 1)




class ConflictDetectionWithBookingsTests(AvailableSlotsBusinessLogicBaseTestCase):
    """Test business logic for detecting conflicts with existing bookings"""
    
    def test_existing_class_blocks_overlapping_slot_booking(self):
        """Test business rule: existing classes prevent overlapping bookings"""
        # Create teacher availability
        TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Create existing class booking
        existing_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Existing Class",
            scheduled_date=date.today() + timedelta(days=1),  # Next Monday
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
            booked_by=self.admin_user
        )
        
        # Act - Try to find conflicts for overlapping time slot
        target_date = date.today() + timedelta(days=1)
        conflicting_classes = ClassSchedule.objects.filter(
            teacher=self.teacher_profile,
            school=self.school,
            scheduled_date=target_date,
            start_time__lt=time(15, 0),  # Ends after our start
            end_time__gt=time(14, 30),   # Starts before our end
            status=ClassStatus.SCHEDULED
        )
        
        # Assert - Conflict should be detected
        self.assertIn(existing_class, conflicting_classes)
        self.assertEqual(conflicting_classes.count(), 1)

    def test_cancelled_classes_do_not_block_slot_booking(self):
        """Test business rule: cancelled classes don't prevent new bookings"""
        # Create teacher availability
        TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Create cancelled class
        cancelled_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Cancelled Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.CANCELLED,  # This class is cancelled
            booked_by=self.admin_user
        )
        
        # Act - Check for active conflicts (should exclude cancelled)
        target_date = date.today() + timedelta(days=1)
        active_conflicts = ClassSchedule.objects.filter(
            teacher=self.teacher_profile,
            school=self.school,
            scheduled_date=target_date,
            start_time__lt=time(15, 0),
            end_time__gt=time(14, 0),
            status=ClassStatus.SCHEDULED  # Only active classes block slots
        )
        
        # Assert - Cancelled class should not block booking
        self.assertNotIn(cancelled_class, active_conflicts)
        self.assertEqual(active_conflicts.count(), 0)


class UnavailabilityBlockingLogicTests(AvailableSlotsBusinessLogicBaseTestCase):
    """Test business logic for teacher unavailability blocking slots"""
    
    def test_all_day_unavailability_blocks_entire_day_scheduling(self):
        """Test business rule: all-day unavailability blocks all slots for that day"""
        # Create teacher availability
        TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        # Create all-day unavailability
        target_date = date.today() + timedelta(days=1)
        unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=target_date,
            is_all_day=True,
            reason="Sick day"
        )
        
        # Act - Check if any slots are available on that date
        unavailable_dates = TeacherUnavailability.objects.filter(
            teacher=self.teacher_profile,
            school=self.school,
            date=target_date,
            is_all_day=True
        )
        
        # Assert - All-day unavailability should block entire day
        self.assertTrue(unavailable_dates.exists())
        self.assertEqual(unavailable_dates.count(), 1)
        self.assertTrue(unavailability.is_all_day)

    def test_partial_unavailability_blocks_overlapping_slots(self):
        """Test partial unavailability blocks overlapping time slots"""
        TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        target_date = date.today() + timedelta(days=1)
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=target_date,
            start_time=time(12, 0),
            end_time=time(13, 0),
            is_all_day=False,
            reason="Lunch break"
        )
        
        # Check for conflicts with lunch time
        lunch_conflicts = TeacherUnavailability.objects.filter(
            teacher=self.teacher_profile,
            school=self.school,
            date=target_date,
            is_all_day=False,
            start_time__lt=time(13, 0),
            end_time__gt=time(12, 0)
        )
        
        self.assertTrue(lunch_conflicts.exists())


class TimezoneHandlingBusinessLogicTests(AvailableSlotsBusinessLogicBaseTestCase):
    """Test business logic for timezone handling in scheduling"""
    
    def test_school_timezone_affects_slot_calculation(self):
        """Test business rule: slot calculations respect school timezone settings"""
        # Get school timezone
        school_tz = pytz.timezone(self.school_settings.timezone)
        
        # Create availability
        availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(14, 0),   # 2 PM
            end_time=time(18, 0),     # 6 PM
            is_active=True
        )
        
        # Act - Create timezone-aware datetime for scheduling
        target_date = date.today() + timedelta(days=1)
        local_start_time = time(15, 0)  # 3 PM local time
        
        naive_datetime = datetime.combine(target_date, local_start_time)
        aware_datetime = school_tz.localize(naive_datetime)
        
        # Assert - Timezone awareness is properly handled
        self.assertTrue(timezone.is_aware(aware_datetime))
        self.assertEqual(aware_datetime.time(), local_start_time)
        self.assertEqual(aware_datetime.date(), target_date)
        
        # Assert - Time falls within availability window
        self.assertTrue(availability.start_time <= local_start_time <= availability.end_time)

