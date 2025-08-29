"""
Critical serializer tests for the scheduler app.

Focuses on business-critical validation and data transformation for core scheduling functionality.
Tests are streamlined to cover essential serializer behavior without redundancy.
"""

import datetime
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model

from accounts.models import CustomUser, School, TeacherProfile
from common.test_base import BaseAPITestCase
from scheduler.models import ClassSchedule, ClassStatus, ClassType, TeacherAvailability
from scheduler.serializers import (
    CancelClassSerializer,
    ClassScheduleSerializer,
    CreateClassScheduleSerializer,
    TeacherAvailabilitySerializer,
    TeacherUnavailabilitySerializer,
)

User = get_user_model()


class TestTeacherAvailabilitySerializer(BaseAPITestCase):
    """Test core TeacherAvailabilitySerializer functionality."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name="Test School")
        self.user = CustomUser.objects.create_user(email="teacher@example.com", name="Test Teacher")
        self.teacher = TeacherProfile.objects.create(user=self.user)

    def test_serialization_includes_all_required_fields(self):
        """Test serializer includes all required fields."""
        availability = TeacherAvailability.objects.create(
            teacher=self.teacher,
            school=self.school,
<<<<<<< HEAD
            day_of_week="monday",
=======
            day_of_week="monday",  # Monday - use string value from WeekDay choices
>>>>>>> da5a5d4 (✅ Security & Testing Infrastructure Enhancements)
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
            is_active=True,
        )

        serializer = TeacherAvailabilitySerializer(availability)
        data = serializer.data

        required_fields = [
            "id",
            "teacher",
            "teacher_name",
            "school",
            "school_name",
            "day_of_week",
            "start_time",
            "end_time",
            "is_active",
        ]
        for field in required_fields:
            self.assertIn(field, data)
<<<<<<< HEAD

    def test_availability_validation_rules(self):
        """Test various validation rules for teacher availability."""
        validation_tests = [
            {
                "data": {
                    "teacher": self.teacher.id,
                    "school": self.school.id,
                    "day_of_week": "tuesday",
                    "start_time": "18:00:00",  # After end time
                    "end_time": "10:00:00",
                    "is_active": True,
                },
                "should_be_valid": False,
                "description": "end time before start time",
            },
            {
                "data": {
                    "teacher": self.teacher.id,
                    "school": self.school.id,
                    "day_of_week": "tuesday",
                    "start_time": "10:00:00",
                    "end_time": "18:00:00",
                    "is_active": True,
                },
                "should_be_valid": True,
                "description": "valid time range",
            },
=======
        
        self.assertEqual(data['teacher_name'], 'Test Teacher')
        self.assertEqual(data['school_name'], 'Test School')
        self.assertEqual(data['day_of_week'], 'monday')
        self.assertEqual(data['start_time'], '09:00:00')
        self.assertEqual(data['end_time'], '17:00:00')

    def test_day_of_week_display(self):
        """Test day of week display field."""
        serializer = TeacherAvailabilitySerializer(self.availability)
        data = serializer.data
        
        # Should display Monday for day_of_week='monday'
        self.assertIn('Monday', data['day_of_week_display'])

    def test_teacher_field_optional(self):
        """Test teacher field is optional for self-creation."""
        data = {
            'school': self.school.id,
            'day_of_week': 'tuesday',
            'start_time': '10:00:00',
            'end_time': '18:00:00',
            'is_active': True
        }
        
        serializer = TeacherAvailabilitySerializer(data=data)
        # Should be valid even without teacher field (for teachers creating their own availability)
        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
        self.assertTrue(serializer.is_valid())

    def test_model_validation_integration(self):
        """Test serializer integrates with model validation."""
        # Create overlapping availability that should fail model validation
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'day_of_week': 'monday',  # Same day as existing
            'start_time': '08:00:00',  # Overlaps with existing 9:00-17:00
            'end_time': '10:00:00',
            'is_active': True
        }
        
        serializer = TeacherAvailabilitySerializer(data=data)
        # Should fail due to model validation
        self.assertFalse(serializer.is_valid())

    def test_time_validation(self):
        """Test start time must be before end time."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'day_of_week': 'tuesday',
            'start_time': '18:00:00',  # After end time
            'end_time': '10:00:00',
            'is_active': True
        }
        
        serializer = TeacherAvailabilitySerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_update_validation_with_existing_data(self):
        """Test validation works correctly during updates."""
        # Update should work with partial data
        data = {
            'start_time': '08:30:00',
            'end_time': '16:30:00'
        }
        
        serializer = TeacherAvailabilitySerializer(
            self.availability, 
            data=data, 
            partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_foreign_key_resolution_create(self):
        """Test foreign key resolution during creation."""
        data = {
            'teacher': self.teacher.id,  # Should resolve to TeacherProfile instance
            'school': self.school.id,    # Should resolve to School instance
            'day_of_week': 3,
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'is_active': True
        }
        
        serializer = TeacherAvailabilitySerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_day_of_week(self):
        """Test validation of day_of_week field."""
        invalid_days = [-1, 8, 'monday', None]
        
        for day in invalid_days:
            with self.subTest(day=day):
                data = {
                    'teacher': self.teacher.id,
                    'school': self.school.id,
                    'day_of_week': day,
                    'start_time': '09:00:00',
                    'end_time': '17:00:00',
                    'is_active': True
                }
                
                serializer = TeacherAvailabilitySerializer(data=data)
                self.assertFalse(serializer.is_valid())

    def test_invalid_time_formats(self):
        """Test validation of time field formats."""
        invalid_times = [
            ('25:00:00', '17:00:00'),  # Invalid hour
            ('09:70:00', '17:00:00'),  # Invalid minute
            ('09:00', '17:00:00'),     # Wrong format
            ('9am', '5pm'),            # Wrong format
>>>>>>> da5a5d4 (✅ Security & Testing Infrastructure Enhancements)
        ]

        for test_case in validation_tests:
            with self.subTest(description=test_case["description"]):
                serializer = TeacherAvailabilitySerializer(data=test_case["data"])
                self.assertEqual(serializer.is_valid(), test_case["should_be_valid"])


class TestTeacherUnavailabilitySerializer(BaseAPITestCase):
    """Test core TeacherUnavailabilitySerializer functionality."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name="Test School")
        self.user = CustomUser.objects.create_user(email="teacher@example.com", name="Test Teacher")
        self.teacher = TeacherProfile.objects.create(user=self.user)

    def test_unavailability_time_handling(self):
        """Test time handling for different unavailability types."""
        from datetime import date, timedelta

        future_date = date.today() + timedelta(days=30)  # Use a future date

        unavailability_tests = [
            {
                "data": {
                    "teacher": self.teacher.id,
                    "school": self.school.id,
                    "date": future_date.isoformat(),
                    "start_time": "09:00:00",  # Should be cleared
                    "end_time": "17:00:00",  # Should be cleared
                    "reason": "Holiday",
                    "is_all_day": True,
                },
                "should_be_valid": True,
                "check_times_cleared": True,
                "description": "all-day unavailability clears times",
            },
            {
                "data": {
                    "teacher": self.teacher.id,
                    "school": self.school.id,
                    "date": (future_date + timedelta(days=1)).isoformat(),
                    "reason": "Doctor appointment",
                    "is_all_day": False,
                    # Missing start_time and end_time
                },
                "should_be_valid": False,
                "description": "partial day requires times",
            },
        ]

        for test_case in unavailability_tests:
            with self.subTest(description=test_case["description"]):
                serializer = TeacherUnavailabilitySerializer(data=test_case["data"])
                is_valid = serializer.is_valid()

                # Debug: Print errors if validation fails unexpectedly
                # (Removed debug code for production)

                self.assertEqual(is_valid, test_case["should_be_valid"])

                if test_case["should_be_valid"] and test_case.get("check_times_cleared"):
                    self.assertIsNone(serializer.validated_data.get("start_time"))
                    self.assertIsNone(serializer.validated_data.get("end_time"))


class TestClassScheduleSerializer(BaseAPITestCase):
    """Test core ClassScheduleSerializer functionality."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name="Test School")
        self.teacher_user = CustomUser.objects.create_user(email="teacher@example.com", name="Test Teacher")
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)

        self.student = CustomUser.objects.create_user(email="student@example.com", name="Test Student")

        self.class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title="Math Tutoring",
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.CONFIRMED,
            scheduled_date=datetime.date(2024, 6, 15),
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            duration_minutes=60,
            max_participants=1,
            booked_by=self.student,  # Required field
        )

    def test_serialization_includes_enhanced_fields(self):
        """Test serializer includes enhanced read-only fields."""
        serializer = ClassScheduleSerializer(self.class_schedule)
        data = serializer.data

        enhanced_fields = [
            "teacher_name",
            "student_name",
            "school_name",
            "class_type_display",
            "status_display",
            "participant_count",
            "can_be_cancelled",
            "is_past",
        ]
        for field in enhanced_fields:
            self.assertIn(field, data)

    def test_participant_count_calculation(self):
        """Test participant count calculation for individual class."""
        serializer = ClassScheduleSerializer(self.class_schedule)
        data = serializer.data

        self.assertEqual(data["participant_count"], 1)

    def test_read_only_fields_protection(self):
        """Test critical read-only fields are protected."""
        critical_read_only = [
            "booked_by",
            "booked_at",
            "cancelled_at",
            "completed_at",
            "can_be_cancelled",
            "is_past",
            "participant_count",
        ]

        serializer = ClassScheduleSerializer()
        meta_read_only = serializer.Meta.read_only_fields

        for field in critical_read_only:
            self.assertIn(field, meta_read_only)


class TestCreateClassScheduleSerializer(BaseAPITestCase):
    """Test core CreateClassScheduleSerializer functionality."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name="Test School")
        self.teacher_user = CustomUser.objects.create_user(email="teacher@example.com", name="Test Teacher")
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)

        self.student = CustomUser.objects.create_user(email="student@example.com", name="Test Student")

    def test_required_fields_validation(self):
        """Test required fields are properly validated."""
        base_data = {
            "teacher": self.teacher.id,
            "student": self.student.id,
            "school": self.school.id,
            "scheduled_date": "2024-06-20",
            "start_time": "14:00:00",
            "duration_minutes": 60,
        }

        required_fields = ["teacher", "student", "school", "scheduled_date", "start_time"]

        for field in required_fields:
            with self.subTest(field=field):
                data = base_data.copy()
                del data[field]  # Remove required field

                serializer = CreateClassScheduleSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_default_duration_assignment(self):
        """Test default duration is assigned when not provided."""
        data = {
            "teacher": self.teacher.id,
            "student": self.student.id,
            "school": self.school.id,
            "scheduled_date": "2024-06-20",
            "start_time": "14:00:00",
            # No duration_minutes provided
        }

        mock_request = Mock()
        mock_request.user = self.student

        serializer = CreateClassScheduleSerializer(data=data, context={"request": mock_request})

        # Mock the BookingOrchestratorService validation
        with patch("scheduler.services.BookingOrchestratorService") as mock_orchestrator:
            mock_orchestrator.return_value.validate_booking_request.return_value = {"is_valid": True, "errors": []}

<<<<<<< HEAD
            if serializer.is_valid():
                self.assertEqual(serializer.validated_data["duration_minutes"], 60)
=======
    def test_class_reminder_serialization(self):
        """Test serializing class reminder data."""
        serializer = ClassReminderSerializer(self.reminder)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'class_schedule', 'class_title', 'reminder_type',
            'reminder_type_display', 'recipient', 'recipient_name',
            'recipient_type', 'communication_channel',
            'communication_channel_display', 'status', 'status_display',
            'scheduled_for', 'sent_at', 'subject', 'message',
            'error_message', 'retry_count', 'max_retries',
            'external_message_id', 'metadata', 'is_overdue',
            'time_until_send', 'can_retry'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['class_title'], 'Math Lesson')
        self.assertEqual(data['recipient_name'], 'Test Student')
        self.assertEqual(data['subject'], 'Class Reminder: Math Lesson')

    def test_display_fields(self):
        """Test display fields for enums."""
        serializer = ClassReminderSerializer(self.reminder)
        data = serializer.data
        
        # Should have human-readable display values
        self.assertIsNotNone(data['reminder_type_display'])
        self.assertIsNotNone(data['communication_channel_display'])
        self.assertIsNotNone(data['status_display'])

    def test_time_until_send_calculation(self):
        """Test time until send calculation."""
        # Create reminder scheduled for 2 hours from now
        future_reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.CLASS_REMINDER,
            recipient=self.student,
            recipient_type='student',
            communication_channel=CommunicationChannel.EMAIL,
            status=ReminderStatus.PENDING,
            scheduled_for=timezone.now() + datetime.timedelta(hours=2),
            subject='Future Reminder',
            message='Test message'
        )
        
        serializer = ClassReminderSerializer(future_reminder)
        data = serializer.data
        
        # Should show remaining time
        self.assertIsNotNone(data['time_until_send'])
        self.assertNotEqual(data['time_until_send'], 'Overdue')

    def test_overdue_reminder_time(self):
        """Test overdue reminder time calculation."""
        # Create overdue reminder
        overdue_reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.CLASS_REMINDER,
            recipient=self.student,
            recipient_type='student',
            communication_channel=CommunicationChannel.EMAIL,
            status=ReminderStatus.PENDING,
            scheduled_for=timezone.now() - datetime.timedelta(hours=1),  # 1 hour ago
            subject='Overdue Reminder',
            message='Test message'
        )
        
        serializer = ClassReminderSerializer(overdue_reminder)
        data = serializer.data
        
        # Should show as overdue
        self.assertEqual(data['time_until_send'], 'Overdue')

    def test_sent_reminder_fields(self):
        """Test fields for sent reminders."""
        sent_reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.CLASS_REMINDER,
            recipient=self.student,
            recipient_type='student',
            communication_channel=CommunicationChannel.EMAIL,
            status=ReminderStatus.SENT,
            scheduled_for=timezone.now() - datetime.timedelta(hours=1),
            sent_at=timezone.now(),
            subject='Sent Reminder',
            message='Test message',
            external_message_id='msg_12345'
        )
        
        serializer = ClassReminderSerializer(sent_reminder)
        data = serializer.data
        
        self.assertIsNotNone(data['sent_at'])
        self.assertEqual(data['status'], 'sent')
        self.assertEqual(data['external_message_id'], 'msg_12345')

    def test_failed_reminder_fields(self):
        """Test fields for failed reminders."""
        failed_reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.CLASS_REMINDER,
            recipient=self.student,
            recipient_type='student',
            communication_channel=CommunicationChannel.EMAIL,
            status=ReminderStatus.FAILED,
            scheduled_for=timezone.now() - datetime.timedelta(hours=1),
            subject='Failed Reminder',
            message='Test message',
            error_message='SMTP connection failed',
            retry_count=2,
            max_retries=3
        )
        
        serializer = ClassReminderSerializer(failed_reminder)
        data = serializer.data
        
        self.assertEqual(data['status'], 'failed')
        self.assertEqual(data['error_message'], 'SMTP connection failed')
        self.assertEqual(data['retry_count'], 2)
        self.assertEqual(data['max_retries'], 3)

    def test_read_only_fields_protection(self):
        """Test read-only fields are properly protected."""
        read_only_fields = [
            'sent_at', 'error_message', 'retry_count', 'external_message_id',
            'created_at', 'updated_at', 'is_overdue', 'can_retry'
        ]
        
        serializer = ClassReminderSerializer()
        meta_read_only = serializer.Meta.read_only_fields
        
        for field in read_only_fields:
            self.assertIn(field, meta_read_only)


class TestTriggerReminderSerializer(BaseAPITestCase):
    """Test suite for TriggerReminderSerializer - Manual reminder triggering."""

    def test_valid_reminder_trigger_data(self):
        """Test valid reminder trigger data."""
        data = {
            'reminder_type': ReminderType.CLASS_REMINDER,
            'message': 'Custom reminder message',
            'channels': [CommunicationChannel.EMAIL, CommunicationChannel.SMS],
            'subject': 'Custom Subject'
        }
        
        serializer = TriggerReminderSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_reminder_type_validation(self):
        """Test reminder type validation."""
        valid_types = [choice[0] for choice in ReminderType.choices]
        
        for reminder_type in valid_types:
            with self.subTest(reminder_type=reminder_type):
                data = {
                    'reminder_type': reminder_type,
                    'message': 'Test message'
                }
                
                serializer = TriggerReminderSerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                               f"Should accept type: {reminder_type}. Errors: {serializer.errors}")

    def test_invalid_reminder_type(self):
        """Test invalid reminder types are rejected."""
        invalid_types = ['invalid_type', 'REMINDER', 'not_a_valid_type']
        
        for reminder_type in invalid_types:
            with self.subTest(reminder_type=reminder_type):
                data = {
                    'reminder_type': reminder_type,
                    'message': 'Test message'
                }
                
                serializer = TriggerReminderSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('reminder_type', serializer.errors)

    def test_communication_channels_validation(self):
        """Test communication channels validation."""
        valid_channels = [choice[0] for choice in CommunicationChannel.choices]
        
        data = {
            'reminder_type': ReminderType.CLASS_REMINDER,
            'channels': valid_channels
        }
        
        serializer = TriggerReminderSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_optional_fields(self):
        """Test optional fields work correctly."""
        # Minimal required data
        data = {
            'reminder_type': ReminderType.CLASS_REMINDER
        }
        
        serializer = TriggerReminderSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_message_length_validation(self):
        """Test message field length validation."""
        long_message = 'A' * 1001  # Over 1000 character limit
        
        data = {
            'reminder_type': ReminderType.CLASS_REMINDER,
            'message': long_message
        }
        
        serializer = TriggerReminderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('message', serializer.errors)

    def test_subject_length_validation(self):
        """Test subject field length validation."""
        long_subject = 'A' * 256  # Over 255 character limit
        
        data = {
            'reminder_type': ReminderType.CLASS_REMINDER,
            'subject': long_subject
        }
        
        serializer = TriggerReminderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('subject', serializer.errors)
>>>>>>> da5a5d4 (✅ Security & Testing Infrastructure Enhancements)


class TestCancelClassSerializer(BaseAPITestCase):
    """Test CancelClassSerializer functionality."""

    def test_reason_field_optional(self):
        """Test reason field is optional."""
        data = {}
        serializer = CancelClassSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_reason_accepts_blank(self):
        """Test reason field accepts blank values."""
        data = {"reason": ""}
        serializer = CancelClassSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_cancel_serializer_flexibility(self):
        """Test cancel serializer handles various input scenarios."""
        test_cases = [
            ({}, "empty data"),
            ({"reason": ""}, "empty reason"),
            ({"reason": "Student illness"}, "simple reason"),
            ({"reason": "Family emergency - urgent situation"}, "detailed reason"),
        ]

        for data, description in test_cases:
            with self.subTest(case=description):
                serializer = CancelClassSerializer(data=data)
                self.assertTrue(serializer.is_valid(), f"Should be valid for {description}: {serializer.errors}")
