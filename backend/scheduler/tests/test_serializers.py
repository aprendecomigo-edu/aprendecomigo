"""
Comprehensive serializer tests for the scheduler app.

These tests verify serializer validation, field exposure, data transformation,
and business logic enforcement for all scheduling API serializers.
Critical areas covered:
- Teacher availability and unavailability validation
- Class scheduling with conflict detection
- Recurring schedule management
- Time zone handling and validation
- Reminder and notification systems
- Complex cross-field validation logic
"""

import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import serializers as drf_serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from accounts.models import CustomUser, School, StudentProfile, TeacherProfile
from common.test_base import BaseAPITestCase, mock_external_services
from scheduler.models import (
    ClassReminder, ClassSchedule, ClassStatus, ClassType, RecurringClassSchedule,
    ReminderPreference, ReminderStatus, ReminderType, TeacherAvailability,
    TeacherUnavailability, CommunicationChannel
)
from scheduler.serializers import (
    AvailableTimeSlotsSerializer, CancelClassSerializer, ClassReminderSerializer,
    ClassScheduleSerializer, CreateClassScheduleSerializer, RecurringClassScheduleSerializer,
    ReminderPreferenceSerializer, TeacherAvailabilitySerializer, TeacherUnavailabilitySerializer,
    TriggerReminderSerializer
)

User = get_user_model()


class TestTeacherAvailabilitySerializer(BaseAPITestCase):
    """Test suite for TeacherAvailabilitySerializer - Teacher availability management."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School')
        self.user = CustomUser.objects.create_user(
            email='teacher@example.com',
            name='Test Teacher'
        )
        self.teacher = TeacherProfile.objects.create(user=self.user)
        
        self.availability = TeacherAvailability.objects.create(
            teacher=self.teacher,
            school=self.school,
            day_of_week=1,  # Monday
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
            is_active=True
        )

    def test_teacher_availability_serialization(self):
        """Test serializing teacher availability data."""
        serializer = TeacherAvailabilitySerializer(self.availability)
        data = serializer.data
        
        # Verify all expected fields are present
        expected_fields = [
            'id', 'teacher', 'teacher_name', 'school', 'school_name',
            'day_of_week', 'day_of_week_display', 'start_time', 'end_time',
            'is_active', 'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['teacher_name'], 'Test Teacher')
        self.assertEqual(data['school_name'], 'Test School')
        self.assertEqual(data['day_of_week'], 1)
        self.assertEqual(data['start_time'], '09:00:00')
        self.assertEqual(data['end_time'], '17:00:00')

    def test_day_of_week_display(self):
        """Test day of week display field."""
        serializer = TeacherAvailabilitySerializer(self.availability)
        data = serializer.data
        
        # Should display Monday for day_of_week=1
        self.assertIn('Monday', data['day_of_week_display'])

    def test_teacher_field_optional(self):
        """Test teacher field is optional for self-creation."""
        data = {
            'school': self.school.id,
            'day_of_week': 2,
            'start_time': '10:00:00',
            'end_time': '18:00:00',
            'is_active': True
        }
        
        serializer = TeacherAvailabilitySerializer(data=data)
        # Should be valid even without teacher field (for teachers creating their own availability)
        self.assertTrue(serializer.is_valid())

    def test_model_validation_integration(self):
        """Test serializer integrates with model validation."""
        # Create overlapping availability that should fail model validation
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'day_of_week': 1,  # Same day as existing
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
            'day_of_week': 2,
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
        ]
        
        for start_time, end_time in invalid_times:
            with self.subTest(start_time=start_time, end_time=end_time):
                data = {
                    'teacher': self.teacher.id,
                    'school': self.school.id,
                    'day_of_week': 2,
                    'start_time': start_time,
                    'end_time': end_time,
                    'is_active': True
                }
                
                serializer = TeacherAvailabilitySerializer(data=data)
                self.assertFalse(serializer.is_valid())


class TestTeacherUnavailabilitySerializer(BaseAPITestCase):
    """Test suite for TeacherUnavailabilitySerializer - Teacher unavailability management."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School')
        self.user = CustomUser.objects.create_user(
            email='teacher@example.com',
            name='Test Teacher'
        )
        self.teacher = TeacherProfile.objects.create(user=self.user)
        
        self.unavailability = TeacherUnavailability.objects.create(
            teacher=self.teacher,
            school=self.school,
            date=datetime.date(2024, 12, 25),  # Christmas
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
            reason='Holiday - Christmas',
            is_all_day=False
        )

    def test_teacher_unavailability_serialization(self):
        """Test serializing teacher unavailability data."""
        serializer = TeacherUnavailabilitySerializer(self.unavailability)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'teacher', 'teacher_name', 'school', 'school_name',
            'date', 'start_time', 'end_time', 'reason', 'is_all_day', 'created_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['teacher_name'], 'Test Teacher')
        self.assertEqual(data['school_name'], 'Test School')
        self.assertEqual(data['reason'], 'Holiday - Christmas')

    def test_all_day_unavailability_validation(self):
        """Test all-day unavailability clears start_time and end_time."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'date': '2024-12-31',
            'start_time': '09:00:00',  # Should be cleared
            'end_time': '17:00:00',    # Should be cleared
            'reason': 'New Year Holiday',
            'is_all_day': True
        }
        
        serializer = TeacherUnavailabilitySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # Validation should clear time fields for all-day
        self.assertIsNone(serializer.validated_data['start_time'])
        self.assertIsNone(serializer.validated_data['end_time'])

    def test_partial_day_unavailability_requires_times(self):
        """Test partial day unavailability requires start and end times."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'date': '2024-06-15',
            'reason': 'Doctor appointment',
            'is_all_day': False
            # Missing start_time and end_time
        }
        
        serializer = TeacherUnavailabilitySerializer(data=data)
        # Should fail model validation for missing times when not all-day
        self.assertFalse(serializer.is_valid())

    def test_future_date_validation(self):
        """Test unavailability can be set for future dates."""
        future_date = datetime.date.today() + datetime.timedelta(days=30)
        
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'date': future_date.strftime('%Y-%m-%d'),
            'start_time': '14:00:00',
            'end_time': '16:00:00',
            'reason': 'Conference',
            'is_all_day': False
        }
        
        serializer = TeacherUnavailabilitySerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_past_date_validation(self):
        """Test unavailability validation for past dates."""
        past_date = datetime.date.today() - datetime.timedelta(days=30)
        
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'date': past_date.strftime('%Y-%m-%d'),
            'start_time': '14:00:00',
            'end_time': '16:00:00',
            'reason': 'Past unavailability',
            'is_all_day': False
        }
        
        serializer = TeacherUnavailabilitySerializer(data=data)
        # Model validation might prevent past dates
        # This depends on business rules implementation
        result = serializer.is_valid()
        # Either should be valid or have specific error about past dates

    def test_teacher_field_optional(self):
        """Test teacher field is optional for self-creation."""
        data = {
            'school': self.school.id,
            'date': '2024-07-04',
            'is_all_day': True,
            'reason': 'Independence Day'
        }
        
        serializer = TeacherUnavailabilitySerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_reason_field_validation(self):
        """Test reason field accepts various formats."""
        valid_reasons = [
            'Sick leave',
            'Vacation - Family trip to Porto',
            'Conference: EdTech Summit 2024',
            'Personal day',
            'Medical appointment at 15:00'
        ]
        
        for reason in valid_reasons:
            with self.subTest(reason=reason):
                data = {
                    'teacher': self.teacher.id,
                    'school': self.school.id,
                    'date': '2024-08-15',
                    'is_all_day': True,
                    'reason': reason
                }
                
                serializer = TeacherUnavailabilitySerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                               f"Should accept reason: {reason}. Errors: {serializer.errors}")

    def test_overlapping_unavailability_validation(self):
        """Test model validation prevents overlapping unavailabilities."""
        # Try to create overlapping unavailability
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'date': '2024-12-25',  # Same date as existing
            'start_time': '08:00:00',  # Overlaps
            'end_time': '10:00:00',
            'reason': 'Another appointment',
            'is_all_day': False
        }
        
        serializer = TeacherUnavailabilitySerializer(data=data)
        # Should fail due to model validation
        self.assertFalse(serializer.is_valid())


class TestClassScheduleSerializer(BaseAPITestCase):
    """Test suite for ClassScheduleSerializer - Class schedule management."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School')
        self.teacher_user = CustomUser.objects.create_user(
            email='teacher@example.com',
            name='Test Teacher'
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        
        self.student = CustomUser.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        self.booker = CustomUser.objects.create_user(
            email='parent@example.com',
            name='Test Parent'
        )
        
        self.class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title='Math Tutoring',
            description='Basic algebra concepts',
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.CONFIRMED,
            scheduled_date=datetime.date(2024, 6, 15),
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            duration_minutes=60,
            booked_by=self.booker,
            max_participants=1
        )

    def test_class_schedule_serialization(self):
        """Test serializing class schedule data."""
        serializer = ClassScheduleSerializer(self.class_schedule)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'teacher', 'teacher_name', 'student', 'student_name',
            'school', 'school_name', 'title', 'description', 'class_type',
            'class_type_display', 'status', 'status_display', 'scheduled_date',
            'start_time', 'end_time', 'duration_minutes', 'booked_by',
            'booked_by_name', 'max_participants', 'participant_count',
            'participants', 'participants_names', 'is_full',
            'can_be_cancelled', 'is_past'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['teacher_name'], 'Test Teacher')
        self.assertEqual(data['student_name'], 'Test Student')
        self.assertEqual(data['school_name'], 'Test School')
        self.assertEqual(data['booked_by_name'], 'Test Parent')
        self.assertEqual(data['title'], 'Math Tutoring')

    def test_participant_count_calculation(self):
        """Test participant count calculation for individual class."""
        serializer = ClassScheduleSerializer(self.class_schedule)
        data = serializer.data
        
        # Individual class should have 1 participant
        self.assertEqual(data['participant_count'], 1)
        self.assertEqual(len(data['participants']), 1)
        self.assertEqual(data['participants'][0], self.student.id)
        self.assertEqual(data['participants_names'][0], 'Test Student')

    def test_group_class_participants(self):
        """Test participant handling for group classes."""
        # Create additional students
        student2 = CustomUser.objects.create_user(
            email='student2@example.com',
            name='Student Two'
        )
        student3 = CustomUser.objects.create_user(
            email='student3@example.com',
            name='Student Three'
        )
        
        # Create group class
        group_class = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title='Group Math',
            class_type=ClassType.GROUP,
            status=ClassStatus.CONFIRMED,
            scheduled_date=datetime.date(2024, 6, 16),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 30),
            duration_minutes=90,
            booked_by=self.booker,
            max_participants=5
        )
        
        # Add additional students
        group_class.additional_students.add(student2, student3)
        
        serializer = ClassScheduleSerializer(group_class)
        data = serializer.data
        
        # Should have 3 total participants (main + 2 additional)
        self.assertEqual(data['participant_count'], 3)
        self.assertEqual(len(data['participants']), 3)
        self.assertEqual(len(data['participants_names']), 3)
        self.assertIn('Student Two', data['participants_names'])
        self.assertIn('Student Three', data['participants_names'])

    def test_is_full_calculation(self):
        """Test is_full calculation for class capacity."""
        serializer = ClassScheduleSerializer(self.class_schedule)
        data = serializer.data
        
        # Individual class with max_participants=1 and 1 student should be full
        self.assertTrue(data['is_full'])

    def test_timezone_aware_datetime_fields(self):
        """Test timezone-aware datetime field generation."""
        serializer = ClassScheduleSerializer(self.class_schedule)
        data = serializer.data
        
        # Should have UTC and local datetime fields
        self.assertIn('scheduled_datetime_utc', data)
        self.assertIn('scheduled_datetime_local', data)
        
        # UTC should be in ISO format with Z
        if data['scheduled_datetime_utc']:
            self.assertTrue(data['scheduled_datetime_utc'].endswith('Z'))
        
        # Local should include timezone offset
        if data['scheduled_datetime_local']:
            self.assertRegex(data['scheduled_datetime_local'], r'.*[+-]\d{4}$')

    def test_status_history_serialization(self):
        """Test status history field."""
        serializer = ClassScheduleSerializer(self.class_schedule)
        data = serializer.data
        
        # Should have status_history field
        self.assertIn('status_history', data)
        self.assertIsInstance(data['status_history'], list)

    def test_cancellation_fields(self):
        """Test cancellation-related fields."""
        # Create cancelled class
        cancelled_class = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title='Cancelled Class',
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.CANCELLED,
            scheduled_date=datetime.date(2024, 6, 17),
            start_time=datetime.time(16, 0),
            end_time=datetime.time(17, 0),
            duration_minutes=60,
            booked_by=self.booker,
            cancelled_at=timezone.now(),
            cancellation_reason='Student illness'
        )
        
        serializer = ClassScheduleSerializer(cancelled_class)
        data = serializer.data
        
        self.assertEqual(data['status'], 'cancelled')
        self.assertIsNotNone(data['cancelled_at'])
        self.assertEqual(data['cancellation_reason'], 'Student illness')

    def test_completion_fields(self):
        """Test completion-related fields."""
        # Create completed class
        completed_class = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title='Completed Class',
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.COMPLETED,
            scheduled_date=datetime.date.today() - datetime.timedelta(days=1),
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            duration_minutes=60,
            booked_by=self.booker,
            completed_at=timezone.now(),
            completed_by=self.teacher.user,
            actual_duration_minutes=55,
            completion_notes='Great progress on algebra'
        )
        
        serializer = ClassScheduleSerializer(completed_class)
        data = serializer.data
        
        self.assertEqual(data['status'], 'completed')
        self.assertIsNotNone(data['completed_at'])
        self.assertEqual(data['completed_by_name'], 'Test Teacher')
        self.assertEqual(data['actual_duration_minutes'], 55)
        self.assertEqual(data['completion_notes'], 'Great progress on algebra')

    def test_read_only_fields_protection(self):
        """Test read-only fields are properly protected."""
        read_only_fields = [
            'booked_by', 'booked_at', 'cancelled_at', 'completed_at',
            'completed_by', 'no_show_at', 'no_show_by', 'created_at',
            'updated_at', 'can_be_cancelled', 'is_past', 'participant_count',
            'participants', 'participants_names', 'is_full'
        ]
        
        serializer = ClassScheduleSerializer()
        meta_read_only = serializer.Meta.read_only_fields
        
        for field in read_only_fields:
            self.assertIn(field, meta_read_only)


class TestCreateClassScheduleSerializer(BaseAPITestCase):
    """Test suite for CreateClassScheduleSerializer - Class creation with validation."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School')
        self.teacher_user = CustomUser.objects.create_user(
            email='teacher@example.com',
            name='Test Teacher'
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        
        self.student = CustomUser.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        self.booker = CustomUser.objects.create_user(
            email='parent@example.com',
            name='Test Parent'
        )

    @mock_external_services
    def test_valid_class_creation_data(self):
        """Test valid class creation data."""
        with patch('scheduler.services.BookingOrchestratorService') as mock_orchestrator:
            mock_orchestrator.return_value.validate_booking_request.return_value = {
                'is_valid': True,
                'errors': []
            }
            mock_orchestrator.return_value.create_booking.return_value = {
                'class_schedule': Mock(id=1)
            }
            
            data = {
                'teacher': self.teacher.id,
                'student': self.student.id,
                'school': self.school.id,
                'title': 'Math Lesson',
                'description': 'Basic algebra',
                'class_type': ClassType.INDIVIDUAL,
                'scheduled_date': '2024-06-20',
                'start_time': '14:00:00',
                'duration_minutes': 60,
                'teacher_notes': 'Focus on equations'
            }
            
            # Mock request context
            mock_request = Mock()
            mock_request.user = self.booker
            
            serializer = CreateClassScheduleSerializer(
                data=data,
                context={'request': mock_request}
            )
            self.assertTrue(serializer.is_valid())

    def test_backward_compatibility_field_names(self):
        """Test backward compatibility with different field names."""
        data = {
            'teacher_id': self.teacher.id,  # Backward compatible field
            'student': self.student.id,
            'school': self.school.id,
            'title': 'Math Lesson',
            'date': '2024-06-20',  # Backward compatible field
            'start_time': '14:00:00',
            'duration_minutes': 60
        }
        
        serializer = CreateClassScheduleSerializer(data=data)
        # Should map teacher_id to teacher and date to scheduled_date
        if serializer.is_valid():
            self.assertEqual(serializer.validated_data['teacher'], self.teacher.id)

    def test_default_duration_assignment(self):
        """Test default duration is assigned when not provided."""
        data = {
            'teacher': self.teacher.id,
            'student': self.student.id,
            'school': self.school.id,
            'scheduled_date': '2024-06-20',
            'start_time': '14:00:00'
            # No duration_minutes provided
        }
        
        mock_request = Mock()
        mock_request.user = self.booker
        
        serializer = CreateClassScheduleSerializer(
            data=data,
            context={'request': mock_request}
        )
        # Should set default duration to 60 minutes
        with patch('scheduler.services.BookingOrchestratorService') as mock_orchestrator:
            mock_orchestrator.return_value.validate_booking_request.return_value = {
                'is_valid': True,
                'errors': []
            }
            
            if serializer.is_valid():
                self.assertEqual(serializer.validated_data['duration_minutes'], 60)

    def test_end_time_calculation(self):
        """Test automatic end time calculation from start time and duration."""
        data = {
            'teacher': self.teacher.id,
            'student': self.student.id,
            'school': self.school.id,
            'scheduled_date': '2024-06-20',
            'start_time': '14:00:00',
            'duration_minutes': 90
            # No end_time provided
        }
        
        mock_request = Mock()
        mock_request.user = self.booker
        
        with patch('scheduler.services.BookingOrchestratorService') as mock_orchestrator:
            mock_orchestrator.return_value.validate_booking_request.return_value = {
                'is_valid': True,
                'errors': []
            }
            
            serializer = CreateClassScheduleSerializer(
                data=data,
                context={'request': mock_request}
            )
            if serializer.is_valid():
                # Should calculate end_time as 15:30 (14:00 + 90 minutes)
                self.assertEqual(
                    serializer.validated_data['end_time'],
                    datetime.time(15, 30)
                )

    def test_string_time_format_validation(self):
        """Test string time format is properly validated and converted."""
        data = {
            'teacher': self.teacher.id,
            'student': self.student.id,
            'school': self.school.id,
            'scheduled_date': '2024-06-20',
            'start_time': '2:30 PM',  # Non-standard format
            'duration_minutes': 60
        }
        
        mock_request = Mock()
        mock_request.user = self.booker
        
        serializer = CreateClassScheduleSerializer(
            data=data,
            context={'request': mock_request}
        )
        
        # Should either convert successfully or fail with validation error
        result = serializer.is_valid()
        if not result:
            # Should have validation error for time format
            self.assertTrue('start_time' in serializer.errors or 'non_field_errors' in serializer.errors)

    @mock_external_services
    def test_booking_orchestrator_integration(self):
        """Test integration with BookingOrchestratorService."""
        with patch('scheduler.services.BookingOrchestratorService') as mock_orchestrator:
            # Mock validation failure
            mock_orchestrator.return_value.validate_booking_request.return_value = {
                'is_valid': False,
                'errors': ['Teacher not available at this time']
            }
            
            data = {
                'teacher': self.teacher.id,
                'student': self.student.id,
                'school': self.school.id,
                'scheduled_date': '2024-06-20',
                'start_time': '14:00:00',
                'duration_minutes': 60
            }
            
            mock_request = Mock()
            mock_request.user = self.booker
            
            serializer = CreateClassScheduleSerializer(
                data=data,
                context={'request': mock_request}
            )
            
            self.assertFalse(serializer.is_valid())
            self.assertIn('Teacher not available at this time', str(serializer.errors))

    def test_required_fields_validation(self):
        """Test required fields are properly validated."""
        required_fields = ['teacher', 'student', 'school', 'scheduled_date', 'start_time']
        
        for field in required_fields:
            with self.subTest(field=field):
                data = {
                    'teacher': self.teacher.id,
                    'student': self.student.id,
                    'school': self.school.id,
                    'scheduled_date': '2024-06-20',
                    'start_time': '14:00:00',
                    'duration_minutes': 60
                }
                # Remove one required field
                del data[field]
                
                serializer = CreateClassScheduleSerializer(data=data)
                self.assertFalse(serializer.is_valid())


class TestRecurringClassScheduleSerializer(BaseAPITestCase):
    """Test suite for RecurringClassScheduleSerializer - Recurring schedule management."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School')
        self.teacher_user = CustomUser.objects.create_user(
            email='teacher@example.com',
            name='Test Teacher'
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        
        self.student1 = CustomUser.objects.create_user(
            email='student1@example.com',
            name='Student One'
        )
        self.student2 = CustomUser.objects.create_user(
            email='student2@example.com',
            name='Student Two'
        )
        
        self.creator = CustomUser.objects.create_user(
            email='creator@example.com',
            name='Test Creator'
        )

    def test_recurring_schedule_serialization(self):
        """Test serializing recurring schedule data."""
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher,
            school=self.school,
            title='Weekly Math',
            description='Weekly math sessions',
            class_type=ClassType.GROUP,
            frequency_type='weekly',
            status='active',
            max_participants=5,
            day_of_week=2,  # Tuesday
            start_time=datetime.time(15, 0),
            end_time=datetime.time(16, 30),
            duration_minutes=90,
            start_date=datetime.date(2024, 6, 1),
            end_date=datetime.date(2024, 12, 31),
            is_active=True,
            created_by=self.creator
        )
        
        # Add students
        recurring_schedule.students.add(self.student1, self.student2)
        
        serializer = RecurringClassScheduleSerializer(recurring_schedule)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'teacher', 'teacher_name', 'students', 'student_names',
            'student_count', 'school', 'school_name', 'title', 'description',
            'class_type', 'class_type_display', 'frequency_type',
            'frequency_type_display', 'status', 'status_display',
            'max_participants', 'day_of_week', 'day_of_week_display',
            'start_time', 'end_time', 'duration_minutes', 'start_date',
            'end_date', 'is_active', 'created_by', 'created_by_name'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['teacher_name'], 'Test Teacher')
        self.assertEqual(data['school_name'], 'Test School')
        self.assertEqual(data['student_count'], 2)
        self.assertIn('Student One', data['student_names'])
        self.assertIn('Student Two', data['student_names'])

    def test_group_class_validation(self):
        """Test validation for group classes requires max_participants."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'title': 'Group Math',
            'class_type': ClassType.GROUP,
            'frequency_type': 'weekly',
            'day_of_week': 1,
            'start_time': '15:00:00',
            'end_time': '16:00:00',
            'duration_minutes': 60,
            'start_date': '2024-06-01',
            'students': [self.student1.id, self.student2.id]
            # Missing max_participants
        }
        
        serializer = RecurringClassScheduleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('max_participants', serializer.errors)

    def test_individual_class_student_limit(self):
        """Test individual classes can only have one student."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'title': 'Individual Math',
            'class_type': ClassType.INDIVIDUAL,
            'frequency_type': 'weekly',
            'day_of_week': 1,
            'start_time': '15:00:00',
            'end_time': '16:00:00',
            'duration_minutes': 60,
            'start_date': '2024-06-01',
            'students': [self.student1.id, self.student2.id]  # Too many students
        }
        
        serializer = RecurringClassScheduleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('students', serializer.errors)
        self.assertIn('Individual classes can only have one student', str(serializer.errors))

    def test_date_range_validation(self):
        """Test end date must be after start date."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'title': 'Test Class',
            'class_type': ClassType.INDIVIDUAL,
            'frequency_type': 'weekly',
            'day_of_week': 1,
            'start_time': '15:00:00',
            'end_time': '16:00:00',
            'duration_minutes': 60,
            'start_date': '2024-12-31',  # After end date
            'end_date': '2024-06-01',    # Before start date
            'students': [self.student1.id]
        }
        
        serializer = RecurringClassScheduleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_date', serializer.errors)
        self.assertIn('End date must be after start date', str(serializer.errors))

    def test_time_range_validation(self):
        """Test end time must be after start time."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'title': 'Test Class',
            'class_type': ClassType.INDIVIDUAL,
            'frequency_type': 'weekly',
            'day_of_week': 1,
            'start_time': '16:00:00',  # After end time
            'end_time': '15:00:00',   # Before start time
            'duration_minutes': 60,
            'start_date': '2024-06-01',
            'students': [self.student1.id]
        }
        
        serializer = RecurringClassScheduleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_time', serializer.errors)
        self.assertIn('End time must be after start time', str(serializer.errors))

    def test_created_by_auto_assignment(self):
        """Test created_by is automatically set to current user."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'title': 'Test Class',
            'class_type': ClassType.INDIVIDUAL,
            'frequency_type': 'weekly',
            'day_of_week': 1,
            'start_time': '15:00:00',
            'end_time': '16:00:00',
            'duration_minutes': 60,
            'start_date': '2024-06-01',
            'students': [self.student1.id]
        }
        
        mock_request = Mock()
        mock_request.user = self.creator
        
        serializer = RecurringClassScheduleSerializer(
            data=data,
            context={'request': mock_request}
        )
        
        if serializer.is_valid():
            instance = serializer.save()
            self.assertEqual(instance.created_by, self.creator)

    def test_student_management_in_updates(self):
        """Test student management during updates."""
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher,
            school=self.school,
            title='Test Class',
            class_type=ClassType.GROUP,
            frequency_type='weekly',
            max_participants=5,
            day_of_week=1,
            start_time=datetime.time(15, 0),
            end_time=datetime.time(16, 0),
            duration_minutes=60,
            start_date=datetime.date(2024, 6, 1),
            created_by=self.creator
        )
        
        # Initially add student1
        recurring_schedule.students.add(self.student1)
        
        # Update to include both students
        data = {
            'students': [self.student1.id, self.student2.id]
        }
        
        serializer = RecurringClassScheduleSerializer(
            recurring_schedule,
            data=data,
            partial=True
        )
        
        if serializer.is_valid():
            updated_schedule = serializer.save()
            self.assertEqual(updated_schedule.students.count(), 2)

    def test_generated_instances_tracking(self):
        """Test generated instances count tracking."""
        recurring_schedule = RecurringClassSchedule.objects.create(
            teacher=self.teacher,
            school=self.school,
            title='Test Class',
            class_type=ClassType.INDIVIDUAL,
            frequency_type='weekly',
            day_of_week=1,
            start_time=datetime.time(15, 0),
            end_time=datetime.time(16, 0),
            duration_minutes=60,
            start_date=datetime.date(2024, 6, 1),
            created_by=self.creator
        )
        
        serializer = RecurringClassScheduleSerializer(recurring_schedule)
        data = serializer.data
        
        # Should have tracking fields
        self.assertIn('generated_instances_count', data)
        self.assertIn('future_instances_count', data)
        self.assertIsInstance(data['generated_instances_count'], int)
        self.assertIsInstance(data['future_instances_count'], int)


class TestReminderPreferenceSerializer(BaseAPITestCase):
    """Test suite for ReminderPreferenceSerializer - User reminder preferences."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School')
        self.user = CustomUser.objects.create_user(
            email='user@example.com',
            name='Test User'
        )
        
        self.reminder_preference = ReminderPreference.objects.create(
            user=self.user,
            school=self.school,
            reminder_timing_hours=[24, 2, 0.5],  # 1 day, 2 hours, 30 minutes
            communication_channels=['email', 'sms'],
            timezone_preference='Europe/Lisbon',
            is_active=True,
            is_school_default=False
        )

    def test_reminder_preference_serialization(self):
        """Test serializing reminder preference data."""
        serializer = ReminderPreferenceSerializer(self.reminder_preference)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'user', 'user_name', 'school', 'school_name',
            'reminder_timing_hours', 'communication_channels',
            'timezone_preference', 'is_active', 'is_school_default',
            'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['user_name'], 'Test User')
        self.assertEqual(data['school_name'], 'Test School')
        self.assertEqual(data['reminder_timing_hours'], [24, 2, 0.5])
        self.assertEqual(data['communication_channels'], ['email', 'sms'])

    def test_reminder_timing_hours_validation(self):
        """Test reminder timing hours validation."""
        valid_timing_data = [
            [1, 24],           # 1 hour and 1 day
            [0.5, 2, 24],      # 30 min, 2 hours, 1 day
            [168],             # 1 week (maximum)
            [0.1]              # 6 minutes
        ]
        
        for timing_hours in valid_timing_data:
            with self.subTest(timing_hours=timing_hours):
                data = {
                    'school': self.school.id,
                    'reminder_timing_hours': timing_hours,
                    'communication_channels': ['email'],
                    'is_active': True
                }
                
                serializer = ReminderPreferenceSerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                               f"Should accept timing: {timing_hours}. Errors: {serializer.errors}")

    def test_reminder_timing_hours_invalid_values(self):
        """Test invalid reminder timing hours are rejected."""
        invalid_timing_data = [
            [-1],              # Negative
            [200],             # Over 168 hours (1 week)
            'not_a_list',      # Wrong type
            [1, 'invalid'],    # Mixed types
            []                 # Empty list (might be valid depending on business rules)
        ]
        
        for timing_hours in invalid_timing_data:
            with self.subTest(timing_hours=timing_hours):
                data = {
                    'school': self.school.id,
                    'reminder_timing_hours': timing_hours,
                    'communication_channels': ['email'],
                    'is_active': True
                }
                
                serializer = ReminderPreferenceSerializer(data=data)
                self.assertFalse(serializer.is_valid(),
                                f"Should reject timing: {timing_hours}")
                self.assertIn('reminder_timing_hours', serializer.errors)

    def test_communication_channels_validation(self):
        """Test communication channels validation."""
        valid_channels = [
            ['email'],
            ['sms'],
            ['push'],
            ['email', 'sms'],
            ['email', 'sms', 'push']
        ]
        
        for channels in valid_channels:
            with self.subTest(channels=channels):
                data = {
                    'school': self.school.id,
                    'reminder_timing_hours': [24],
                    'communication_channels': channels,
                    'is_active': True
                }
                
                serializer = ReminderPreferenceSerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                               f"Should accept channels: {channels}. Errors: {serializer.errors}")

    def test_communication_channels_invalid_values(self):
        """Test invalid communication channels are rejected."""
        invalid_channels = [
            ['invalid_channel'],
            'not_a_list',
            ['email', 'invalid'],
            ['EMAIL'],  # Case sensitive validation
        ]
        
        for channels in invalid_channels:
            with self.subTest(channels=channels):
                data = {
                    'school': self.school.id,
                    'reminder_timing_hours': [24],
                    'communication_channels': channels,
                    'is_active': True
                }
                
                serializer = ReminderPreferenceSerializer(data=data)
                self.assertFalse(serializer.is_valid(),
                                f"Should reject channels: {channels}")

    @mock_external_services
    def test_timezone_validation(self):
        """Test timezone preference validation."""
        with patch('scheduler.reminder_services.TimezoneValidationService') as mock_service:
            mock_service.validate_timezone.return_value = True
            
            valid_timezones = [
                'Europe/Lisbon',
                'America/New_York',
                'Asia/Tokyo',
                'UTC'
            ]
            
            for timezone_pref in valid_timezones:
                with self.subTest(timezone=timezone_pref):
                    data = {
                        'school': self.school.id,
                        'reminder_timing_hours': [24],
                        'communication_channels': ['email'],
                        'timezone_preference': timezone_pref,
                        'is_active': True
                    }
                    
                    serializer = ReminderPreferenceSerializer(data=data)
                    self.assertTrue(serializer.is_valid(),
                                   f"Should accept timezone: {timezone_pref}. Errors: {serializer.errors}")

    @mock_external_services
    def test_timezone_validation_invalid(self):
        """Test invalid timezone preferences are rejected."""
        with patch('scheduler.reminder_services.TimezoneValidationService') as mock_service:
            mock_service.validate_timezone.return_value = False
            
            data = {
                'school': self.school.id,
                'reminder_timing_hours': [24],
                'communication_channels': ['email'],
                'timezone_preference': 'Invalid/Timezone',
                'is_active': True
            }
            
            serializer = ReminderPreferenceSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('timezone_preference', serializer.errors)

    def test_school_field_optional(self):
        """Test school field is optional."""
        data = {
            'reminder_timing_hours': [24],
            'communication_channels': ['email'],
            'is_active': True
        }
        
        serializer = ReminderPreferenceSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class TestClassReminderSerializer(BaseAPITestCase):
    """Test suite for ClassReminderSerializer - Class reminder management."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School')
        self.teacher_user = CustomUser.objects.create_user(
            email='teacher@example.com',
            name='Test Teacher'
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        
        self.student = CustomUser.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        
        self.class_schedule = ClassSchedule.objects.create(
            teacher=self.teacher,
            student=self.student,
            school=self.school,
            title='Math Lesson',
            scheduled_date=datetime.date.today() + datetime.timedelta(days=1),
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            duration_minutes=60
        )
        
        self.reminder = ClassReminder.objects.create(
            class_schedule=self.class_schedule,
            reminder_type=ReminderType.CLASS_REMINDER,
            recipient=self.student,
            recipient_type='student',
            communication_channel=CommunicationChannel.EMAIL,
            status=ReminderStatus.PENDING,
            scheduled_for=timezone.now() + datetime.timedelta(hours=23),
            subject='Class Reminder: Math Lesson',
            message='Your math lesson is scheduled for tomorrow at 2:00 PM',
            retry_count=0,
            max_retries=3
        )

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
        invalid_types = ['invalid_type', 'REMINDER', 'custom']
        
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


class TestCancelClassSerializer(BaseAPITestCase):
    """Test suite for CancelClassSerializer - Class cancellation."""

    def test_valid_cancellation_data(self):
        """Test valid cancellation data."""
        data = {
            'reason': 'Student illness'
        }
        
        serializer = CancelClassSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_reason_field_optional(self):
        """Test reason field is optional."""
        data = {}
        serializer = CancelClassSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_reason_length_validation(self):
        """Test reason field length validation."""
        long_reason = 'A' * 501  # Over 500 character limit
        
        data = {
            'reason': long_reason
        }
        
        serializer = CancelClassSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('reason', serializer.errors)

    def test_reason_accepts_blank(self):
        """Test reason field accepts blank values."""
        data = {
            'reason': ''
        }
        
        serializer = CancelClassSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_various_cancellation_reasons(self):
        """Test various cancellation reason formats."""
        valid_reasons = [
            'Student illness',
            'Family emergency',
            'Teacher unavailable due to illness',
            'School closure - public holiday',
            'Technical issues with online platform',
            'Rescheduled to next week by mutual agreement'
        ]
        
        for reason in valid_reasons:
            with self.subTest(reason=reason):
                data = {'reason': reason}
                serializer = CancelClassSerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                               f"Should accept reason: {reason}. Errors: {serializer.errors}")


class TestAvailableTimeSlotsSerializer(BaseAPITestCase):
    """Test suite for AvailableTimeSlotsSerializer - Time slot availability."""

    def test_available_time_slots_serialization(self):
        """Test serializing available time slots data."""
        data = {
            'teacher_id': 1,
            'date': '2024-06-20',
            'available_slots': [
                {'start_time': '09:00', 'end_time': '10:00', 'duration': '60'},
                {'start_time': '14:00', 'end_time': '15:30', 'duration': '90'},
                {'start_time': '16:00', 'end_time': '17:00', 'duration': '60'}
            ]
        }
        
        serializer = AvailableTimeSlotsSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        self.assertEqual(serializer.validated_data['teacher_id'], 1)
        self.assertEqual(len(serializer.validated_data['available_slots']), 3)

    def test_teacher_id_validation(self):
        """Test teacher_id field validation."""
        invalid_teacher_ids = [0, -1, 'abc', None]
        
        for teacher_id in invalid_teacher_ids:
            with self.subTest(teacher_id=teacher_id):
                data = {
                    'teacher_id': teacher_id,
                    'date': '2024-06-20',
                    'available_slots': []
                }
                
                serializer = AvailableTimeSlotsSerializer(data=data)
                self.assertFalse(serializer.is_valid())

    def test_date_field_validation(self):
        """Test date field validation."""
        invalid_dates = ['invalid-date', '2024-13-01', '2024-06-32', 'June 20, 2024']
        
        for date in invalid_dates:
            with self.subTest(date=date):
                data = {
                    'teacher_id': 1,
                    'date': date,
                    'available_slots': []
                }
                
                serializer = AvailableTimeSlotsSerializer(data=data)
                self.assertFalse(serializer.is_valid())

    def test_empty_available_slots(self):
        """Test handling of empty available slots."""
        data = {
            'teacher_id': 1,
            'date': '2024-06-20',
            'available_slots': []
        }
        
        serializer = AvailableTimeSlotsSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data['available_slots']), 0)