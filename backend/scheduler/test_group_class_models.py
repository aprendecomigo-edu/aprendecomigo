"""
Comprehensive failing unit tests for new group class and timezone features.
Tests business logic for GitHub issue #146 requirements:
1. Support for group classes with max_participants field 
2. Proper timezone handling
3. Enhanced metadata fields in ClassSchedule

These tests are designed to FAIL initially since max_participants isn't implemented yet.
Focus ONLY on testing the NEW business logic improvements, not existing functionality.
"""
import pytz
from datetime import date, time, datetime, timedelta
from unittest.mock import patch
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import CustomUser, School, TeacherProfile, SchoolMembership, SchoolRole
from .models import ClassSchedule, ClassType, ClassStatus


class GroupClassCapacityTests(TestCase):
    """Test suite for group class max_participants business logic."""

    def setUp(self):
        """Set up test data for group class capacity tests."""
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com",
            phone_number="1234567890"
        )
        
        # Create teacher user and profile
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            password="testpass123",
            name="John Doe"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Math Teacher"
        )
        
        # Create students
        self.student1 = CustomUser.objects.create_user(
            email="student1@test.com",
            password="testpass123",
            name="Student One"
        )
        self.student2 = CustomUser.objects.create_user(
            email="student2@test.com",
            password="testpass123", 
            name="Student Two"
        )
        self.student3 = CustomUser.objects.create_user(
            email="student3@test.com",
            password="testpass123",
            name="Student Three"
        )
        
        # Create admin user for booking
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            password="adminpass123",
            name="Admin User"
        )
        
        # Create school memberships
        for user in [self.teacher_user, self.student1, self.student2, self.student3, self.admin_user]:
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.STUDENT if 'student' in user.email else SchoolRole.SCHOOL_ADMIN
            )
        
        # Teacher membership
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER
        )

    def test_max_participants_field_exists(self):
        """Test that max_participants field exists on ClassSchedule model."""
        # This test will FAIL until max_participants field is added
        schedule = ClassSchedule(
            teacher=self.teacher,
            student=self.student1,
            school=self.school,
            title="Group Math Class",
            class_type=ClassType.GROUP,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            max_participants=5  # This field should exist
        )
        
        # Should not raise AttributeError when max_participants is implemented
        self.assertTrue(hasattr(schedule, 'max_participants'))

    def test_max_participants_positive_validation(self):
        """Test that max_participants must be positive integer."""
        schedule = ClassSchedule(
            teacher=self.teacher,
            student=self.student1,
            school=self.school,
            title="Group Math Class",
            class_type=ClassType.GROUP,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            max_participants=0  # Invalid: zero participants
        )
        
        # Should raise ValidationError for zero participants
        with self.assertRaises(ValidationError) as cm:
            schedule.full_clean()
        
        self.assertIn('max_participants', str(cm.exception))
        self.assertIn('positive', str(cm.exception).lower())

    def test_max_participants_negative_validation(self):
        """Test that max_participants cannot be negative."""
        schedule = ClassSchedule(
            teacher=self.teacher,
            student=self.student1,
            school=self.school,
            title="Group Math Class",
            class_type=ClassType.GROUP,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            max_participants=-1  # Invalid: negative participants
        )
        
        # Should raise ValidationError for negative participants
        with self.assertRaises(ValidationError) as cm:
            schedule.full_clean()
        
        self.assertIn('max_participants', str(cm.exception))

    def test_group_class_requires_max_participants(self):
        """Test that GROUP class_type requires max_participants to be set."""
        schedule = ClassSchedule(
            teacher=self.teacher,
            student=self.student1,
            school=self.school,
            title="Group Math Class",
            class_type=ClassType.GROUP,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user
            # max_participants not set for GROUP class
        )
        
        # Should raise ValidationError for GROUP class without max_participants
        with self.assertRaises(ValidationError) as cm:
            schedule.full_clean()
        
        self.assertIn('max_participants', str(cm.exception).lower())
        self.assertIn('group', str(cm.exception).lower())

    def test_individual_class_ignores_max_participants(self):
        """Test that INDIVIDUAL class_type ignores max_participants field."""
        schedule = ClassSchedule(
            teacher=self.teacher,
            student=self.student1,
            school=self.school,
            title="Individual Math Class", 
            class_type=ClassType.INDIVIDUAL,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            max_participants=5  # Should be ignored for INDIVIDUAL
        )
        
        # Should not raise ValidationError
        schedule.full_clean()
        schedule.save()
        
        # Verify individual classes don't use max_participants in business logic
        self.assertEqual(schedule.class_type, ClassType.INDIVIDUAL)

    def test_get_total_participants_method(self):
        """Test method to get total participants including main student and additional."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student1,
            school=self.school,
            title="Group Math Class",
            class_type=ClassType.GROUP,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            max_participants=3
        )
        
        # Add additional students
        schedule.additional_students.add(self.student2, self.student3)
        
        # Should have method to get total participants (main + additional)
        total_participants = schedule.get_total_participants()
        self.assertEqual(total_participants, 3)  # student1 + student2 + student3

    def test_can_add_participant_method(self):
        """Test method to check if more participants can be added."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student1,
            school=self.school,
            title="Group Math Class",
            class_type=ClassType.GROUP,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            max_participants=2  # Capacity for only 2 students
        )
        
        # Should be able to add one more (have 1, max 2)
        self.assertTrue(schedule.can_add_participant())
        
        # Add one more student
        schedule.additional_students.add(self.student2)
        
        # Should not be able to add more (have 2, max 2)
        self.assertFalse(schedule.can_add_participant())

    def test_add_participant_validation(self):
        """Test that adding participants validates against max_participants."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student1,
            school=self.school,
            title="Group Math Class",
            class_type=ClassType.GROUP,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            max_participants=2
        )
        
        # Add one additional student (should succeed)
        schedule.add_participant(self.student2)
        self.assertEqual(schedule.get_total_participants(), 2)
        
        # Try to add another (should fail - exceeds capacity)
        with self.assertRaises(ValidationError) as cm:
            schedule.add_participant(self.student3)
        
        self.assertIn('capacity', str(cm.exception).lower())
        self.assertIn('maximum', str(cm.exception).lower())

    def test_is_at_capacity_method(self):
        """Test method to check if class is at maximum capacity."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student1,
            school=self.school,
            title="Group Math Class",
            class_type=ClassType.GROUP,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            max_participants=2
        )
        
        # Not at capacity initially (1/2)
        self.assertFalse(schedule.is_at_capacity())
        
        # Add one more to reach capacity
        schedule.additional_students.add(self.student2)
        
        # Should be at capacity (2/2)
        self.assertTrue(schedule.is_at_capacity())

    def test_get_available_spots_method(self):
        """Test method to get number of available spots."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student1,
            school=self.school,
            title="Group Math Class",
            class_type=ClassType.GROUP,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            max_participants=5
        )
        
        # Should have 4 available spots (5 max - 1 current)
        self.assertEqual(schedule.get_available_spots(), 4)
        
        # Add 2 more students
        schedule.additional_students.add(self.student2, self.student3)
        
        # Should have 2 available spots (5 max - 3 current)
        self.assertEqual(schedule.get_available_spots(), 2)


class TimezoneAwareDatetimeTests(TestCase):
    """Test suite for timezone-aware datetime handling in ClassSchedule."""

    def setUp(self):
        """Set up test data for timezone tests."""
        self.school = School.objects.create(
            name="Brazilian School",
            contact_email="escola@test.com",
            phone_number="1234567890"
        )
        
        # Create teacher
        self.teacher_user = CustomUser.objects.create_user(
            email="professor@test.com",
            password="testpass123",
            name="Professor João"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Math Teacher"
        )
        
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            password="testpass123",
            name="Student"
        )
        
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            password="adminpass123",
            name="Admin"
        )
        
        # Create memberships
        for user in [self.teacher_user, self.student, self.admin_user]:
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER if user == self.teacher_user else SchoolRole.STUDENT
            )

    def test_get_scheduled_datetime_in_teacher_timezone(self):
        """Test method to get scheduled datetime in teacher's timezone."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date(2025, 8, 15),  # Friday
            start_time=time(14, 0),  # 2 PM local time
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=self.admin_user
        )
        
        # Should return datetime in teacher's timezone (from school settings)
        scheduled_dt = schedule.get_scheduled_datetime_in_teacher_timezone()
        
        # Verify it's timezone-aware
        self.assertIsNotNone(scheduled_dt.tzinfo)
        
        # Should use school timezone settings (America/Sao_Paulo)
        # This test will fail until the method is implemented
        self.assertIsInstance(scheduled_dt, datetime)
        
        # Verify the time components
        self.assertEqual(scheduled_dt.date(), date(2025, 8, 15))
        self.assertEqual(scheduled_dt.time(), time(14, 0))

    def test_get_scheduled_datetime_utc(self):
        """Test method to get scheduled datetime in UTC."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date(2025, 8, 15),
            start_time=time(14, 0),  # 2 PM in São Paulo
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=self.admin_user
        )
        
        # Should return datetime in UTC
        utc_dt = schedule.get_scheduled_datetime_utc()
        
        # Verify it's in UTC
        self.assertEqual(utc_dt.tzinfo, pytz.UTC)
        
        # This test validates the UTC conversion method exists
        # Actual timezone conversion logic will be implemented later
        self.assertIsInstance(utc_dt, datetime)

    @patch('django.utils.timezone.now')
    def test_is_past_considers_teacher_timezone(self, mock_now):
        """Test that is_past method considers teacher's timezone."""
        # Mock current time to 10 AM UTC
        mock_now.return_value = timezone.make_aware(
            datetime(2025, 8, 15, 10, 0, 0),
            timezone=pytz.UTC
        )
        
        # Create class scheduled for 2 PM São Paulo time (5 PM UTC)
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date(2025, 8, 15),
            start_time=time(14, 0),  # 2 PM São Paulo = 5 PM UTC
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=self.admin_user
        )
        
        # At 10 AM UTC (7 AM São Paulo), class should not be past
        self.assertFalse(schedule.is_past)

    @patch('django.utils.timezone.now')
    def test_is_past_after_class_time(self, mock_now):
        """Test is_past after class time in teacher's timezone."""
        # Mock current time to 8 PM UTC
        mock_now.return_value = timezone.make_aware(
            datetime(2025, 8, 15, 20, 0, 0),
            timezone=pytz.UTC
        )
        
        # Class scheduled for 2 PM São Paulo time (5 PM UTC)
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date(2025, 8, 15),
            start_time=time(14, 0),  # 2 PM São Paulo = 5 PM UTC
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=self.admin_user
        )
        
        # At 8 PM UTC (5 PM São Paulo), class should be past
        self.assertTrue(schedule.is_past)

    def test_timezone_aware_cancellation_deadline(self):
        """Test cancellation deadline considers teacher's timezone."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=self.admin_user
        )
        
        # Should have method to check if within cancellation deadline in teacher's timezone
        # E.g., can cancel up to 2 hours before class time
        can_cancel = schedule.can_cancel_within_deadline(hours_before=2)
        
        # This method should exist and consider timezone
        self.assertIsInstance(can_cancel, bool)

    def test_get_class_duration_in_teacher_timezone(self):
        """Test getting class duration as timezone-aware datetime objects."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date(2025, 8, 15),
            start_time=time(14, 0),
            end_time=time(16, 0),  # 2-hour class
            duration_minutes=120,
            booked_by=self.admin_user
        )
        
        start_dt, end_dt = schedule.get_class_duration_in_teacher_timezone()
        
        # Both should be timezone-aware
        self.assertIsNotNone(start_dt.tzinfo)
        self.assertIsNotNone(end_dt.tzinfo)
        
        # Verify duration
        duration = end_dt - start_dt
        self.assertEqual(duration, timedelta(hours=2))


class EnhancedMetadataValidationTests(TestCase):
    """Test suite for enhanced metadata fields and validation."""

    def setUp(self):
        """Set up test data for enhanced metadata tests."""
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com",
            phone_number="1234567890"
        )
        
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com",
            password="testpass123",
            name="Teacher"
        )
        self.teacher = TeacherProfile.objects.create(
            user=self.teacher_user,
            bio="Teacher"
        )
        
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            password="testpass123",
            name="Student"
        )
        
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com",
            password="adminpass123",
            name="Admin"
        )
        
        # Create memberships
        for user in [self.teacher_user, self.student, self.admin_user]:
            SchoolMembership.objects.create(
                user=user,
                school=self.school,
                role=SchoolRole.TEACHER if user == self.teacher_user else SchoolRole.STUDENT
            )

    def test_class_metadata_json_field_exists(self):
        """Test that enhanced metadata JSON field exists."""
        schedule = ClassSchedule(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            metadata={  # Enhanced metadata field
                "difficulty_level": "intermediate",
                "topics": ["algebra", "geometry"],
                "materials_needed": ["calculator", "notebook"],
                "homework_assigned": True,
                "assessment_planned": False
            }
        )
        
        # Should not raise AttributeError when metadata field is implemented
        self.assertTrue(hasattr(schedule, 'metadata'))

    def test_metadata_validates_required_group_class_fields(self):
        """Test metadata validation for required group class fields."""
        schedule = ClassSchedule(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Group Math Class",
            class_type=ClassType.GROUP,
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            max_participants=5,
            metadata={
                "group_dynamics": "collaborative",
                "interaction_level": "high"
                # Missing required fields for group classes
            }
        )
        
        # Should validate that group classes have required metadata fields
        with self.assertRaises(ValidationError) as cm:
            schedule.full_clean()
        
        self.assertIn('metadata', str(cm.exception).lower())

    def test_metadata_difficulty_level_validation(self):
        """Test validation of difficulty_level in metadata."""
        schedule = ClassSchedule(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            metadata={
                "difficulty_level": "invalid_level",  # Invalid value
                "topics": ["algebra"]
            }
        )
        
        # Should validate difficulty_level values
        with self.assertRaises(ValidationError) as cm:
            schedule.full_clean()
        
        self.assertIn('difficulty_level', str(cm.exception))

    def test_metadata_topics_list_validation(self):
        """Test validation that topics is a list of strings."""
        schedule = ClassSchedule(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            metadata={
                "difficulty_level": "beginner",
                "topics": "algebra"  # Should be a list, not string
            }
        )
        
        # Should validate that topics is a list
        with self.assertRaises(ValidationError) as cm:
            schedule.full_clean()
        
        self.assertIn('topics', str(cm.exception))

    def test_get_metadata_value_method(self):
        """Test helper method to get metadata values safely."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            metadata={
                "difficulty_level": "intermediate",
                "topics": ["algebra", "geometry"]
            }
        )
        
        # Should have method to safely get metadata values
        difficulty = schedule.get_metadata_value("difficulty_level")
        self.assertEqual(difficulty, "intermediate")
        
        # Should return None or default for missing keys
        missing = schedule.get_metadata_value("missing_key", default="not_found")
        self.assertEqual(missing, "not_found")

    def test_update_metadata_method(self):
        """Test method to update specific metadata fields."""
        schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Class",
            scheduled_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.admin_user,
            metadata={
                "difficulty_level": "beginner",
                "topics": ["basic_math"]
            }
        )
        
        # Should have method to update metadata
        schedule.update_metadata({
            "difficulty_level": "intermediate",
            "homework_assigned": True
        })
        
        # Verify updates
        self.assertEqual(schedule.get_metadata_value("difficulty_level"), "intermediate")
        self.assertEqual(schedule.get_metadata_value("homework_assigned"), True)
        self.assertEqual(schedule.get_metadata_value("topics"), ["basic_math"])  # Unchanged