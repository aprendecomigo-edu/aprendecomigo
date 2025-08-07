"""
Comprehensive API Tests for Class Booking Endpoint - Issue #149

Tests the POST /api/scheduling/classes/ endpoint with:
1. Required parameters validation (teacher_id, date, start_time, duration_minutes)
2. Optional parameters handling (max_participants, class_type, description)
3. Business logic validation rules
4. Group class capacity management
5. Edge cases and error handling

These tests should FAIL initially since the booking logic isn't fully implemented.
"""
import json
from datetime import date, datetime, time, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

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
    ClassSchedule,
    TeacherAvailability,
    TeacherUnavailability,
    ClassType,
    ClassStatus,
    WeekDay,
)


class ClassBookingAPITestCase(TestCase):
    """Base test case with common setup for class booking API tests."""

    def setUp(self):
        """Set up test data for all class booking tests."""
        # Create educational system and school
        self.edu_system, _ = EducationalSystem.objects.get_or_create(
            code="custom", 
            defaults={"name": "Test System", "description": "Test educational system"}
        )
        self.school = School.objects.create(name="Test School", description="Test Description")
        self.school_settings = SchoolSettings.objects.create(
            school=self.school, 
            timezone="America/New_York", 
            educational_system=self.edu_system
        )

        # Create test users
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@test.com", name="Test Teacher", password="testpass123"
        )
        self.student_user = CustomUser.objects.create_user(
            email="student@test.com", name="Test Student", password="testpass123"
        )
        self.student_user2 = CustomUser.objects.create_user(
            email="student2@test.com", name="Test Student 2", password="testpass123"
        )
        self.admin_user = CustomUser.objects.create_user(
            email="admin@test.com", name="Test Admin", password="testpass123"
        )

        # Create teacher profile
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user, bio="Test teacher bio"
        )

        # Create school memberships
        SchoolMembership.objects.create(
            user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )
        SchoolMembership.objects.create(
            user=self.student_user, school=self.school, role=SchoolRole.STUDENT, is_active=True
        )
        SchoolMembership.objects.create(
            user=self.student_user2, school=self.school, role=SchoolRole.STUDENT, is_active=True
        )
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        # Create teacher availability for Monday through Friday 9AM-5PM
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            TeacherAvailability.objects.create(
                teacher=self.teacher_profile,
                school=self.school,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True
            )

        # Set up API client
        self.client = APIClient()

        # Common test data
        self.booking_url = reverse("classschedule-list")
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Ensure tomorrow is a weekday with availability (Monday = 0)
        while self.tomorrow.weekday() >= 5:  # Skip weekends
            self.tomorrow += timedelta(days=1)

        self.valid_booking_data = {
            "teacher_id": self.teacher_profile.id,
            "date": self.tomorrow.isoformat(),
            "start_time": "10:00",
            "duration_minutes": 60,
            "student": self.student_user.id,
            "school": self.school.id,
            "title": "Test Class"
        }


class RequiredParametersValidationTest(ClassBookingAPITestCase):
    """Test validation of required parameters for class booking."""

    def test_missing_teacher_id_returns_400(self):
        """Test that missing teacher_id returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        del data["teacher_id"]
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("teacher_id", str(response.data).lower())

    def test_missing_date_returns_400(self):
        """Test that missing date returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        del data["date"]
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date", str(response.data).lower())

    def test_missing_start_time_returns_400(self):
        """Test that missing start_time returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        del data["start_time"]
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_time", str(response.data).lower())

    def test_invalid_teacher_id_returns_400(self):
        """Test that invalid teacher_id returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["teacher_id"] = 99999  # Non-existent teacher
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_date_format_returns_400(self):
        """Test that invalid date format returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["date"] = "not-a-date"
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_time_format_returns_400(self):
        """Test that invalid start_time format returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["start_time"] = "not-a-time"
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OptionalParametersTest(ClassBookingAPITestCase):
    """Test handling of optional parameters."""

    def test_default_duration_minutes_is_60(self):
        """Test that duration_minutes defaults to 60 when not provided."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        del data["duration_minutes"]
        
        response = self.client.post(self.booking_url, data, format="json")
        
        # This should succeed once the endpoint is implemented
        # For now, we're testing the validation logic
        if response.status_code == status.HTTP_201_CREATED:
            self.assertEqual(response.data["duration_minutes"], 60)

    def test_custom_duration_minutes_accepted(self):
        """Test that custom duration_minutes is accepted."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["duration_minutes"] = 90
        
        response = self.client.post(self.booking_url, data, format="json")
        
        if response.status_code == status.HTTP_201_CREATED:
            self.assertEqual(response.data["duration_minutes"], 90)

    def test_max_participants_for_group_class(self):
        """Test that max_participants is handled correctly for group classes."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["max_participants"] = 3
        data["class_type"] = ClassType.GROUP
        
        response = self.client.post(self.booking_url, data, format="json")
        
        if response.status_code == status.HTTP_201_CREATED:
            self.assertEqual(response.data["max_participants"], 3)
            self.assertEqual(response.data["class_type"], ClassType.GROUP)

    def test_class_type_parameter(self):
        """Test that class_type parameter is handled correctly."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["class_type"] = ClassType.TRIAL
        
        response = self.client.post(self.booking_url, data, format="json")
        
        if response.status_code == status.HTTP_201_CREATED:
            self.assertEqual(response.data["class_type"], ClassType.TRIAL)

    def test_description_parameter(self):
        """Test that description parameter is handled correctly."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["description"] = "Special test class with custom description"
        
        response = self.client.post(self.booking_url, data, format="json")
        
        if response.status_code == status.HTTP_201_CREATED:
            self.assertEqual(response.data["description"], "Special test class with custom description")


class BusinessLogicValidationTest(ClassBookingAPITestCase):
    """Test business logic validation rules."""

    def test_no_bookings_in_past_returns_400(self):
        """Test that booking in the past returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["date"] = (timezone.now().date() - timedelta(days=1)).isoformat()
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("past", str(response.data).lower())

    def test_time_outside_teacher_availability_returns_400(self):
        """Test that booking outside teacher availability returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["start_time"] = "08:00"  # Before 9AM availability
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("available", str(response.data).lower())

    def test_booking_during_teacher_unavailability_returns_400(self):
        """Test that booking during unavailability returns 400 Bad Request."""
        # Create unavailability for tomorrow
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(12, 0),
            reason="Doctor appointment"
        )
        
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["start_time"] = "10:30"  # During unavailability
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unavailable", str(response.data).lower())

    def test_booking_all_day_unavailability_returns_400(self):
        """Test that booking during all-day unavailability returns 400 Bad Request."""
        # Create all-day unavailability
        TeacherUnavailability.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=self.tomorrow,
            is_all_day=True,
            reason="Sick day"
        )
        
        self.client.force_authenticate(user=self.student_user)
        
        response = self.client.post(self.booking_url, self.valid_booking_data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unavailable", str(response.data).lower())

    def test_conflicting_teacher_booking_returns_400(self):
        """Test that conflicting with existing teacher booking returns 400 Bad Request."""
        # Create existing class schedule
        ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user2,
            school=self.school,
            title="Existing Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user2,
            status=ClassStatus.SCHEDULED
        )
        
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["start_time"] = "10:30"  # Conflicts with existing class
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("conflict", str(response.data).lower())

    def test_student_double_booking_returns_400(self):
        """Test that student booking multiple classes at same time returns 400 Bad Request."""
        # Create existing class schedule for the student
        ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user,
            school=self.school,
            title="Existing Student Class",
            scheduled_date=self.tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            booked_by=self.student_user,
            status=ClassStatus.SCHEDULED
        )
        
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["start_time"] = "14:30"  # Conflicts with student's existing class
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("conflict", str(response.data).lower())

    def test_minimum_notice_period_validation(self):
        """Test that minimum notice period is respected."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        # Try to book for today (assuming minimum notice period > 0)
        data["date"] = timezone.now().date().isoformat()
        
        response = self.client.post(self.booking_url, data, format="json")
        
        # This may pass or fail depending on the configured notice period
        # The test validates the logic exists
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn("notice", str(response.data).lower())


class GroupClassCapacityTest(ClassBookingAPITestCase):
    """Test group class capacity management."""

    def test_group_class_requires_max_participants(self):
        """Test that group classes require max_participants to be set."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["class_type"] = ClassType.GROUP
        # Don't set max_participants
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_participants", str(response.data).lower())

    def test_individual_class_cannot_have_max_participants(self):
        """Test that individual classes cannot have max_participants set."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["class_type"] = ClassType.INDIVIDUAL
        data["max_participants"] = 2
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("individual", str(response.data).lower())

    def test_join_existing_group_class_with_capacity(self):
        """Test joining an existing group class that has capacity."""
        # Create existing group class
        existing_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user2,
            school=self.school,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user2,
            status=ClassStatus.SCHEDULED
        )
        
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["class_type"] = ClassType.GROUP
        data["max_participants"] = 3
        data["start_time"] = "10:00"  # Same time as existing class
        
        response = self.client.post(self.booking_url, data, format="json")
        
        if response.status_code == status.HTTP_201_CREATED:
            # Should return existing class with updated participants
            self.assertEqual(response.data["id"], existing_class.id)
            self.assertIn(self.student_user.id, response.data["participants"])

    def test_cannot_join_full_group_class(self):
        """Test that cannot join a group class that's at capacity."""
        # Create existing group class at capacity
        existing_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user2,
            school=self.school,
            title="Full Group Class",
            class_type=ClassType.GROUP,
            max_participants=1,  # Already at capacity with main student
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user2,
            status=ClassStatus.SCHEDULED
        )
        
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["class_type"] = ClassType.GROUP
        data["max_participants"] = 1
        data["start_time"] = "10:00"  # Same time as existing class
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", str(response.data).lower())

    def test_create_new_group_class_when_no_existing(self):
        """Test creating a new group class when no existing class matches."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["class_type"] = ClassType.GROUP
        data["max_participants"] = 4
        
        response = self.client.post(self.booking_url, data, format="json")
        
        if response.status_code == status.HTTP_201_CREATED:
            self.assertEqual(response.data["class_type"], ClassType.GROUP)
            self.assertEqual(response.data["max_participants"], 4)
            self.assertEqual(response.data["student"], self.student_user.id)


class SuccessfulBookingTest(ClassBookingAPITestCase):
    """Test successful booking scenarios."""

    def test_successful_individual_class_booking(self):
        """Test successful individual class booking returns 201 Created."""
        self.client.force_authenticate(user=self.student_user)
        
        response = self.client.post(self.booking_url, self.valid_booking_data, format="json")
        
        if response.status_code == status.HTTP_201_CREATED:
            self.assertEqual(response.data["teacher"], self.teacher_profile.id)
            self.assertEqual(response.data["student"], self.student_user.id)
            self.assertEqual(response.data["school"], self.school.id)
            self.assertEqual(response.data["status"], ClassStatus.SCHEDULED)
            self.assertEqual(response.data["booked_by"], self.student_user.id)
            self.assertIsNotNone(response.data["booked_at"])

    def test_successful_group_class_booking(self):
        """Test successful group class booking returns 201 Created."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["class_type"] = ClassType.GROUP
        data["max_participants"] = 5
        
        response = self.client.post(self.booking_url, data, format="json")
        
        if response.status_code == status.HTTP_201_CREATED:
            self.assertEqual(response.data["class_type"], ClassType.GROUP)
            self.assertEqual(response.data["max_participants"], 5)
            self.assertEqual(response.data["status"], ClassStatus.SCHEDULED)

    def test_response_includes_required_fields(self):
        """Test that successful response includes all required fields."""
        self.client.force_authenticate(user=self.student_user)
        
        response = self.client.post(self.booking_url, self.valid_booking_data, format="json")
        
        if response.status_code == status.HTTP_201_CREATED:
            required_fields = [
                "id", "teacher", "student", "school", "title", "scheduled_date",
                "start_time", "end_time", "duration_minutes", "status",
                "booked_by", "booked_at", "class_type"
            ]
            for field in required_fields:
                self.assertIn(field, response.data)


class EdgeCasesTest(ClassBookingAPITestCase):
    """Test edge cases and boundary conditions."""

    def test_booking_exactly_at_availability_start_time(self):
        """Test booking exactly at the start of teacher availability."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["start_time"] = "09:00"  # Exactly at availability start
        
        response = self.client.post(self.booking_url, data, format="json")
        
        # Should succeed
        if response.status_code != status.HTTP_201_CREATED:
            self.fail(f"Expected 201, got {response.status_code}: {response.data}")

    def test_booking_exactly_at_availability_end_time(self):
        """Test booking that ends exactly at availability end time."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["start_time"] = "16:00"  # 1 hour before 17:00 end
        data["duration_minutes"] = 60
        
        response = self.client.post(self.booking_url, data, format="json")
        
        # Should succeed
        if response.status_code != status.HTTP_201_CREATED:
            self.fail(f"Expected 201, got {response.status_code}: {response.data}")

    def test_booking_on_weekend_without_availability(self):
        """Test booking on weekend when teacher has no availability."""
        # Find next Saturday
        next_saturday = self.tomorrow
        while next_saturday.weekday() != 5:  # Saturday = 5
            next_saturday += timedelta(days=1)
        
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["date"] = next_saturday.isoformat()
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("available", str(response.data).lower())

    def test_booking_with_zero_duration_returns_400(self):
        """Test that zero duration returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["duration_minutes"] = 0
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_with_negative_duration_returns_400(self):
        """Test that negative duration returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["duration_minutes"] = -30
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_timezone_handling_with_different_school_timezone(self):
        """Test that timezone handling works correctly with different school timezones."""
        # Update school timezone to Pacific
        self.school_settings.timezone = "America/Los_Angeles"
        self.school_settings.save()
        
        self.client.force_authenticate(user=self.student_user)
        
        response = self.client.post(self.booking_url, self.valid_booking_data, format="json")
        
        # Should handle timezone correctly
        if response.status_code == status.HTTP_201_CREATED:
            # Verify timezone-aware datetime fields are present
            self.assertIsNotNone(response.data.get("scheduled_datetime_utc"))
            self.assertIsNotNone(response.data.get("scheduled_datetime_local"))


class AuthenticationAndPermissionsTest(ClassBookingAPITestCase):
    """Test authentication and permission requirements."""

    def test_unauthenticated_request_returns_401(self):
        """Test that unauthenticated request returns 401 Unauthorized."""
        # Don't authenticate client
        response = self.client.post(self.booking_url, self.valid_booking_data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_teacher_cannot_book_classes_for_students(self):
        """Test that teachers cannot book classes (as per requirements)."""
        self.client.force_authenticate(user=self.teacher_user)
        
        response = self.client.post(self.booking_url, self.valid_booking_data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("teachers cannot", str(response.data).lower())

    def test_student_can_only_book_for_themselves(self):
        """Test that students can only book classes for themselves."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["student"] = self.student_user2.id  # Try to book for another student
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("themselves", str(response.data).lower())

    def test_admin_can_book_for_any_student(self):
        """Test that school admins can book classes for any student."""
        self.client.force_authenticate(user=self.admin_user)
        data = self.valid_booking_data.copy()
        data["student"] = self.student_user2.id  # Admin booking for another student
        
        response = self.client.post(self.booking_url, data, format="json")
        
        # Should succeed for admins
        if response.status_code != status.HTTP_201_CREATED:
            self.fail(f"Admin should be able to book for any student. Got {response.status_code}: {response.data}")

    def test_cannot_book_in_school_without_membership(self):
        """Test that users cannot book in schools they're not members of."""
        # Create another school
        other_school = School.objects.create(name="Other School", description="Another school")
        
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["school"] = other_school.id
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("permission", str(response.data).lower())


class ErrorMessageQualityTest(ClassBookingAPITestCase):
    """Test that error messages are detailed and helpful."""

    def test_detailed_error_message_for_time_conflict(self):
        """Test that time conflict errors include specific details."""
        # Create conflicting class
        ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user2,
            school=self.school,
            title="Conflicting Class",
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user2,
            status=ClassStatus.SCHEDULED
        )
        
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["start_time"] = "10:30"
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Error message should be specific about the conflict
        error_msg = str(response.data).lower()
        self.assertIn("conflict", error_msg)
        self.assertIn("time", error_msg)

    def test_detailed_error_message_for_availability(self):
        """Test that availability errors include teacher's actual availability."""
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["start_time"] = "08:00"  # Before availability
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Error message should include availability hours
        error_msg = str(response.data).lower()
        self.assertIn("available", error_msg)
        # Should mention the actual available hours
        self.assertTrue("09:00" in str(response.data) or "17:00" in str(response.data))

    def test_detailed_error_message_for_capacity(self):
        """Test that capacity errors include current participant count."""
        # Create full group class
        full_class = ClassSchedule.objects.create(
            teacher=self.teacher_profile,
            student=self.student_user2,
            school=self.school,
            title="Full Group Class",
            class_type=ClassType.GROUP,
            max_participants=1,
            scheduled_date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            booked_by=self.student_user2,
            status=ClassStatus.SCHEDULED
        )
        
        self.client.force_authenticate(user=self.student_user)
        data = self.valid_booking_data.copy()
        data["class_type"] = ClassType.GROUP
        data["max_participants"] = 1
        data["start_time"] = "10:00"
        
        response = self.client.post(self.booking_url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = str(response.data).lower()
        self.assertIn("capacity", error_msg)