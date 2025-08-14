"""
API Tests for Class Booking Endpoint.

Tests the POST /api/scheduler/schedules/ endpoint for creating class bookings.
Covers validation, permissions, and business logic for both individual and group classes.

Test Coverage:
- Required field validation
- Optional field handling
- Authentication and permission checks
- Business rule validation (availability, conflicts)
- Group class capacity management
- Error handling and edge cases
"""

from datetime import time

from django.urls import reverse
from rest_framework import status

from scheduler.models import ClassSchedule, ClassStatus, ClassType

from .test_base import SchedulerAPITestCase


class ClassBookingRequiredFieldsTests(SchedulerAPITestCase):
    """Test validation of required fields for class booking."""

    def setUp(self):
        super().setUp()
        self.url = reverse("class-schedules-list")
        self.authenticate_as_student()

    def test_create_class_missing_teacher_returns_400(self):
        """Test that missing teacher field returns 400 Bad Request."""
        data = self.valid_class_data.copy()
        del data["teacher"]

        response = self.client.post(self.url, data, format="json")

        self.assertValidationError(response, "teacher")

    def test_create_class_missing_student_returns_400(self):
        """Test that missing student field returns 400 Bad Request."""
        data = self.valid_class_data.copy()
        del data["student"]

        response = self.client.post(self.url, data, format="json")

        self.assertValidationError(response, "student")

    def test_create_class_missing_school_returns_400(self):
        """Test that missing school field returns 400 Bad Request."""
        data = self.valid_class_data.copy()
        del data["school"]

        response = self.client.post(self.url, data, format="json")

        self.assertValidationError(response, "school")

    def test_create_class_missing_scheduled_date_returns_400(self):
        """Test that missing scheduled_date field returns 400 Bad Request."""
        data = self.valid_class_data.copy()
        del data["scheduled_date"]

        response = self.client.post(self.url, data, format="json")

        self.assertValidationError(response, "scheduled_date")

    def test_create_class_missing_start_time_returns_400(self):
        """Test that missing start_time field returns 400 Bad Request."""
        data = self.valid_class_data.copy()
        del data["start_time"]

        response = self.client.post(self.url, data, format="json")

        self.assertValidationError(response, "start_time")

    def test_create_class_invalid_foreign_keys_returns_400(self):
        """Test that invalid foreign key references return 400 Bad Request."""
        test_cases = [
            ("teacher", 99999, "Invalid teacher ID should fail"),
            ("student", 99999, "Invalid student ID should fail"),
            ("school", 99999, "Invalid school ID should fail"),
        ]

        for field, invalid_value, message in test_cases:
            with self.subTest(field=field, message=message):
                data = self.valid_class_data.copy()
                data[field] = invalid_value

                response = self.client.post(self.url, data, format="json")

                self.assertValidationError(response)

    def test_create_class_invalid_format_fields_returns_400(self):
        """Test that invalid field formats return 400 Bad Request."""
        test_cases = [
            ("scheduled_date", "not-a-date", "Invalid date format should fail"),
            ("start_time", "not-a-time", "Invalid time format should fail"),
            ("duration_minutes", "not-a-number", "Invalid duration format should fail"),
        ]

        for field, invalid_value, message in test_cases:
            with self.subTest(field=field, message=message):
                data = self.valid_class_data.copy()
                data[field] = invalid_value

                response = self.client.post(self.url, data, format="json")

                self.assertValidationError(response)


class ClassBookingOptionalFieldsTests(SchedulerAPITestCase):
    """Test handling of optional fields in class booking."""

    def setUp(self):
        super().setUp()
        self.url = reverse("class-schedules-list")
        self.authenticate_as_student()

    def test_create_class_with_title_succeeds(self):
        """Test that class creation with title succeeds."""
        data = self.valid_class_data.copy()
        data["title"] = "Custom Math Session"

        response = self.client.post(self.url, data, format="json")

        self.assertCreatedWithData(response, {"title": "Custom Math Session"})

    def test_create_class_with_custom_duration(self):
        """Test creating class with custom duration."""
        data = self.valid_class_data.copy()
        data["duration_minutes"] = 90
        data["end_time"] = "11:30:00"  # Adjust end time to match duration

        response = self.client.post(self.url, data, format="json")

        self.assertCreatedWithData(response, {"duration_minutes": 90})

    def test_create_class_with_description(self):
        """Test creating class with description."""
        data = self.valid_class_data.copy()
        data["description"] = "Advanced calculus session"

        response = self.client.post(self.url, data, format="json")

        self.assertCreatedWithData(response, {"description": "Advanced calculus session"})

    def test_create_class_defaults_to_individual_type(self):
        """Test that class_type defaults to INDIVIDUAL when not specified."""
        data = self.valid_class_data.copy()
        if "class_type" in data:
            del data["class_type"]

        response = self.client.post(self.url, data, format="json")

        self.assertCreatedWithData(response, {"class_type": ClassType.INDIVIDUAL})


class ClassBookingGroupClassTests(SchedulerAPITestCase):
    """Test group class specific booking functionality."""

    def setUp(self):
        super().setUp()
        self.url = reverse("class-schedules-list")
        self.authenticate_as_admin()  # Admins can create group classes

    def test_create_group_class_success(self):
        """Test successful group class creation (additional students not yet implemented)."""
        response = self.client.post(self.url, self.valid_group_class_data, format="json")

        self.assertCreatedWithData(response, {"class_type": ClassType.GROUP, "max_participants": 3})

        # Verify the created group class
        class_schedule = ClassSchedule.objects.get(id=response.data["id"])
        self.assertEqual(class_schedule.class_type, ClassType.GROUP)

    def test_create_group_class_with_max_participants(self):
        """Test group class creation with max_participants (capacity logic not fully implemented)."""
        data = self.valid_group_class_data.copy()
        data["max_participants"] = 2  # Set capacity

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that the class was created with correct capacity
        detail_response = self.client.get(f"{self.url}{response.data['id']}/")
        self.assertEqual(detail_response.data.get("max_participants"), 2)

    def test_create_group_class_with_valid_capacity_succeeds(self):
        """Test that group class creation with valid capacity succeeds."""
        data = self.valid_group_class_data.copy()
        data["max_participants"] = 5  # Sufficient capacity

        response = self.client.post(self.url, data, format="json")

        self.assertCreatedWithData(response, {"max_participants": 5})

    def test_create_group_class_without_metadata_allowed(self):
        """Test that group classes can be created without metadata."""
        data = self.valid_group_class_data.copy()
        del data["metadata"]

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ClassBookingAuthenticationTests(SchedulerAPITestCase):
    """Test authentication and permission requirements for class booking."""

    def setUp(self):
        super().setUp()
        self.url = reverse("class-schedules-list")

    def test_create_class_requires_authentication(self):
        """Test that creating class requires authentication."""
        # Don't authenticate client
        response = self.client.post(self.url, self.valid_class_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_can_book_individual_class(self):
        """Test that students can book individual classes."""
        self.authenticate_as_student()

        response = self.client.post(self.url, self.valid_class_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_teacher_cannot_create_class(self):
        """Test that teachers cannot create classes (permission denied)."""
        self.authenticate_as_teacher()

        response = self.client.post(self.url, self.valid_class_data, format="json")

        self.assertPermissionDenied(response)

    def test_admin_can_create_any_class(self):
        """Test that admins can create any type of class."""
        self.authenticate_as_admin()

        response = self.client.post(self.url, self.valid_group_class_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthorized_user_cannot_create_class(self):
        """Test that users without school membership cannot create classes."""
        self.authenticate_as_unauthorized()

        response = self.client.post(self.url, self.valid_class_data, format="json")

        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])


class ClassBookingBusinessLogicTests(SchedulerAPITestCase):
    """Test business logic validation for class booking."""

    def setUp(self):
        super().setUp()
        self.url = reverse("class-schedules-list")
        self.authenticate_as_student()

    def test_create_class_in_past_fails(self):
        """Test that creating class in the past returns validation error."""
        data = self.valid_class_data.copy()
        data["scheduled_date"] = self.past_date.isoformat()

        response = self.client.post(self.url, data, format="json")

        self.assertValidationError(response)

    def test_create_class_outside_teacher_availability_fails(self):
        """Test that creating class outside teacher availability fails."""
        data = self.valid_class_data.copy()
        data["start_time"] = "06:00:00"  # Before teacher availability (9AM-5PM)
        data["end_time"] = "07:00:00"
        data["duration_minutes"] = 60

        response = self.client.post(self.url, data, format="json")

        self.assertValidationError(response)

    def test_create_class_with_conflicting_schedule_fails(self):
        """Test that creating overlapping classes fails."""
        # First, create a class
        first_response = self.client.post(self.url, self.valid_class_data, format="json")
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        # Try to create overlapping class with same teacher
        overlapping_data = self.valid_class_data.copy()
        overlapping_data["start_time"] = "10:30:00"  # Overlaps with first class (10:00-11:00)
        overlapping_data["end_time"] = "11:30:00"
        overlapping_data["duration_minutes"] = 60
        overlapping_data["title"] = "Conflicting Class"

        response = self.client.post(self.url, overlapping_data, format="json")

        self.assertValidationError(response)

    def test_create_class_during_teacher_unavailability_fails(self):
        """Test that creating class during teacher unavailability fails."""
        # Create teacher unavailability
        self.create_teacher_unavailability(
            teacher=self.teacher_profile, date=self.tomorrow, start_time=time(10, 0), end_time=time(12, 0)
        )

        response = self.client.post(self.url, self.valid_class_data, format="json")

        self.assertValidationError(response)

    def test_end_time_before_start_time_fails(self):
        """Test that end_time before start_time returns validation error."""
        data = self.valid_class_data.copy()
        data["start_time"] = "11:00:00"
        data["end_time"] = "10:00:00"  # Before start time

        response = self.client.post(self.url, data, format="json")

        self.assertValidationError(response)


class ClassBookingSuccessTests(SchedulerAPITestCase):
    """Test successful class booking scenarios."""

    def setUp(self):
        super().setUp()
        self.url = reverse("class-schedules-list")
        self.authenticate_as_student()

    def test_create_individual_class_success(self):
        """Test successful individual class creation."""
        response = self.client.post(self.url, self.valid_class_data, format="json")

        self.assertCreatedWithData(
            response, {"title": "Test Class", "class_type": ClassType.INDIVIDUAL, "status": ClassStatus.SCHEDULED}
        )

        # Verify database record
        self.assertTrue(
            ClassSchedule.objects.filter(
                id=response.data["id"], teacher=self.teacher_profile, student=self.student_user
            ).exists()
        )

    def test_create_trial_class_success(self):
        """Test successful trial class creation."""
        data = self.valid_class_data.copy()
        data["class_type"] = ClassType.TRIAL

        response = self.client.post(self.url, data, format="json")

        self.assertCreatedWithData(response, {"class_type": ClassType.TRIAL})

    def test_created_class_has_correct_booked_by(self):
        """Test that created class tracks who booked it."""
        response = self.client.post(self.url, self.valid_class_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        class_schedule = ClassSchedule.objects.get(id=response.data["id"])
        self.assertEqual(class_schedule.booked_by, self.student_user)

    def test_create_class_with_valid_future_date(self):
        """Test creating class with various valid future dates."""
        data = self.valid_class_data.copy()
        data["scheduled_date"] = self.next_week.isoformat()

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
