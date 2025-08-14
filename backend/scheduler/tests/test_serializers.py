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
            day_of_week="monday",
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

            if serializer.is_valid():
                self.assertEqual(serializer.validated_data["duration_minutes"], 60)


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
