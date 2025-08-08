"""
Unit Tests for Available Slots Calculation

This module tests basic available slots calculation functionality
that is already implemented in the system.

Focus Areas:
- Teacher availability filtering
- Time slot generation
- Basic conflict detection
- Date and time validation

Key Test Scenarios:
- Available time slots based on teacher schedules
- Filtering by active availability
- Date range calculations
- Basic time overlap detection
"""

from datetime import date, datetime, time, timedelta
from django.test import TestCase
from django.utils import timezone
import pytz

# Import actual models and functionality
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
    TeacherAvailability,
    WeekDay,
)


class TeacherAvailabilitySlotTests(TestCase):
    """Test teacher availability and slot generation."""
    
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
    
    def test_create_teacher_availability_for_weekdays(self):
        """Test creating teacher availability for different weekdays."""
        # Arrange & Act
        monday_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        friday_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.FRIDAY,
            start_time=time(10, 0),
            end_time=time(16, 0),
            is_active=True
        )
        
        # Assert
        self.assertEqual(monday_availability.start_time, time(9, 0))
        self.assertEqual(monday_availability.end_time, time(17, 0))
        self.assertEqual(friday_availability.start_time, time(10, 0))
        self.assertEqual(friday_availability.end_time, time(16, 0))
    
    def test_filter_teacher_availability_by_active_status(self):
        """Test filtering teacher availability by active status."""
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
        inactive_slots = TeacherAvailability.objects.filter(is_active=False)
        
        # Assert
        self.assertIn(active_availability, active_slots)
        self.assertNotIn(inactive_availability, active_slots)
        self.assertIn(inactive_availability, inactive_slots)
        self.assertNotIn(active_availability, inactive_slots)
    
    def test_get_availability_for_specific_teacher_and_school(self):
        """Test getting availability for specific teacher and school."""
        # Arrange
        # Create another teacher
        other_teacher_user = CustomUser.objects.create_user(
            email="other@test.com",
            name="Other Teacher"
        )
        other_teacher_profile = TeacherProfile.objects.create(
            user=other_teacher_user,
            bio="Other teacher"
        )
        
        # Create availability for both teachers
        teacher1_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        
        teacher2_availability = TeacherAvailability.objects.create(
            teacher=other_teacher_profile,
            school=self.school,
            day_of_week=WeekDay.MONDAY,
            start_time=time(10, 0),
            end_time=time(16, 0),
            is_active=True
        )
        
        # Act
        teacher1_slots = TeacherAvailability.objects.filter(
            teacher=self.teacher_profile,
            school=self.school
        )
        
        # Assert
        self.assertIn(teacher1_availability, teacher1_slots)
        self.assertNotIn(teacher2_availability, teacher1_slots)
    
    def test_availability_time_validation(self):
        """Test time validation in teacher availability."""
        # Arrange & Act
        morning_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.WEDNESDAY,
            start_time=time(8, 0),   # 8 AM
            end_time=time(12, 0),    # 12 PM
            is_active=True
        )
        
        afternoon_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.WEDNESDAY,
            start_time=time(14, 0),  # 2 PM
            end_time=time(18, 0),    # 6 PM
            is_active=True
        )
        
        # Assert
        # Morning availability should be valid
        self.assertTrue(morning_availability.start_time < morning_availability.end_time)
        
        # Afternoon availability should be valid
        self.assertTrue(afternoon_availability.start_time < afternoon_availability.end_time)
        
        # Check time differences
        morning_duration = (datetime.combine(date.today(), morning_availability.end_time) - 
                          datetime.combine(date.today(), morning_availability.start_time))
        afternoon_duration = (datetime.combine(date.today(), afternoon_availability.end_time) - 
                            datetime.combine(date.today(), afternoon_availability.start_time))
        
        self.assertEqual(morning_duration.seconds, 4 * 60 * 60)  # 4 hours
        self.assertEqual(afternoon_duration.seconds, 4 * 60 * 60)  # 4 hours
    
    def test_availability_ordering_by_start_time(self):
        """Test ordering availability slots by start time."""
        # Arrange
        late_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.THURSDAY,
            start_time=time(14, 0),
            end_time=time(18, 0),
            is_active=True
        )
        
        early_availability = TeacherAvailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            day_of_week=WeekDay.THURSDAY,
            start_time=time(9, 0),
            end_time=time(13, 0),
            is_active=True
        )
        
        # Act
        ordered_availability = TeacherAvailability.objects.filter(
            day_of_week=WeekDay.THURSDAY
        ).order_by('start_time')
        
        # Assert
        self.assertEqual(list(ordered_availability), [early_availability, late_availability])


class TimeSlotUtilityTests(TestCase):
    """Test utility functions for time slots."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_timezone = pytz.timezone('America/Sao_Paulo')
        self.current_date = date(2024, 1, 15)
    
    def test_time_slot_duration_calculation(self):
        """Test calculating duration between time slots."""
        # Arrange
        start_time = time(10, 0)  # 10:00 AM
        end_time = time(11, 30)   # 11:30 AM
        
        # Act
        start_datetime = datetime.combine(self.current_date, start_time)
        end_datetime = datetime.combine(self.current_date, end_time)
        duration = end_datetime - start_datetime
        
        # Assert
        self.assertEqual(duration.total_seconds(), 90 * 60)  # 90 minutes
    
    def test_time_slot_overlap_detection(self):
        """Test detecting overlap between time slots."""
        # Arrange
        slot1_start = time(10, 0)   # 10:00 AM
        slot1_end = time(11, 0)     # 11:00 AM
        
        slot2_start = time(10, 30)  # 10:30 AM (overlaps)
        slot2_end = time(11, 30)    # 11:30 AM
        
        slot3_start = time(11, 0)   # 11:00 AM (adjacent, no overlap)
        slot3_end = time(12, 0)     # 12:00 PM
        
        # Act & Assert - overlap detection
        # Slot 1 and 2 overlap
        self.assertTrue(
            max(slot1_start, slot2_start) < min(slot1_end, slot2_end)
        )
        
        # Slot 1 and 3 don't overlap (adjacent)
        self.assertFalse(
            max(slot1_start, slot3_start) < min(slot1_end, slot3_end)
        )
    
    def test_timezone_aware_datetime_creation(self):
        """Test creating timezone-aware datetime objects."""
        # Arrange
        local_time = time(14, 30)
        test_date = self.current_date
        
        # Act
        naive_datetime = datetime.combine(test_date, local_time)
        aware_datetime = self.test_timezone.localize(naive_datetime)
        
        # Assert
        self.assertTrue(timezone.is_aware(aware_datetime))
        self.assertFalse(timezone.is_aware(naive_datetime))
        self.assertEqual(aware_datetime.time(), local_time)
        self.assertEqual(aware_datetime.date(), test_date)
    
    def test_date_range_generation(self):
        """Test generating date ranges for availability."""
        # Arrange
        start_date = date(2024, 1, 15)  # Monday
        end_date = date(2024, 1, 19)    # Friday
        
        # Act
        date_range = []
        current = start_date
        while current <= end_date:
            date_range.append(current)
            current += timedelta(days=1)
        
        # Assert
        self.assertEqual(len(date_range), 5)  # 5 weekdays
        self.assertEqual(date_range[0], start_date)
        self.assertEqual(date_range[-1], end_date)
        
        # Check all dates are consecutive
        for i in range(1, len(date_range)):
            expected_date = date_range[i-1] + timedelta(days=1)
            self.assertEqual(date_range[i], expected_date)


    
    
    
    
    
    


    
    
    
    


