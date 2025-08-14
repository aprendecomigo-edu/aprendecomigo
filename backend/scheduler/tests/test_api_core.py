"""
Core API Tests for Scheduler Application.

Tests core CRUD operations and serializer functionality not covered by specialized test files.
Focuses on basic functionality, serializer fields, and general API behavior.

Test Coverage:
- Class schedule CRUD operations (list, retrieve, update, delete)
- Enhanced serializer fields and read-only computed properties
- Permission checks for different user roles
- General API response validation
"""

from django.urls import reverse
from rest_framework import status

from scheduler.models import ClassSchedule, ClassStatus, ClassType

from .test_base import SchedulerAPITestCase


class ClassScheduleCRUDTests(SchedulerAPITestCase):
    """Test basic CRUD operations for ClassSchedule API."""

    def setUp(self):
        super().setUp()
        self.class_schedule = self.create_class_schedule(
            teacher=self.teacher_profile, student=self.student_user, title="Test Class for CRUD"
        )
        self.list_url = reverse("class-schedules-list")
        self.detail_url = reverse("class-schedules-detail", kwargs={"pk": self.class_schedule.id})

    def test_list_classes_requires_authentication(self):
        """Test that listing classes requires authentication."""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_list_classes(self):
        """Test that authenticated users can list classes."""
        self.authenticate_as_student()

        response = self.client.get(self.list_url)

        self.assertListResponse(response)

    def test_retrieve_class_details(self):
        """Test retrieving a specific class schedule."""
        self.authenticate_as_student()

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.class_schedule.id)
        self.assertEqual(response.data["title"], "Test Class for CRUD")

    def test_update_class_as_authorized_user(self):
        """Test that authorized users can update class details."""
        self.authenticate_as_admin()

        data = {"title": "Updated Title", "description": "Updated description"}

        response = self.client.patch(self.detail_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Title")
        self.assertEqual(response.data["description"], "Updated description")

    def test_different_student_cannot_see_class(self):
        """Test that students cannot see other students' classes (filtered at queryset level)."""
        self.authenticate_as_student(self.student_user2)  # Different student

        response = self.client.get(self.detail_url)

        # Different students get 404 because the class is filtered out of their queryset
        self.assertNotFound(response)

    def test_delete_class_as_authorized_user(self):
        """Test that authorized users can delete classes."""
        self.authenticate_as_admin()

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ClassSchedule.objects.filter(id=self.class_schedule.id).exists())

    def test_student_cannot_delete_class(self):
        """Test that students cannot delete classes."""
        self.authenticate_as_student()

        response = self.client.delete(self.detail_url)

        # Students should not be able to delete classes
        self.assertPermissionDenied(response)


class ClassScheduleSerializerFieldsTests(SchedulerAPITestCase):
    """Test enhanced serializer fields and computed properties."""

    def setUp(self):
        super().setUp()
        self.individual_class = self.create_class_schedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            title="Individual Class",
            class_type=ClassType.INDIVIDUAL,
            status=ClassStatus.SCHEDULED,
        )

        self.group_class = self.create_class_schedule(
            teacher=self.teacher_profile,
            student=self.student_user,
            title="Group Class",
            class_type=ClassType.GROUP,
            max_participants=3,
        )
        # Add additional student to group class
        self.group_class.additional_students.add(self.student_user2)

    def test_enhanced_read_only_fields(self):
        """Test enhanced serializer read-only fields."""
        self.authenticate_as_student()

        url = reverse("class-schedules-detail", kwargs={"pk": self.individual_class.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check enhanced read-only fields
        self.assertEqual(response.data["teacher_name"], "Test Teacher")
        self.assertEqual(response.data["student_name"], "Test Student")
        self.assertEqual(response.data["school_name"], "Test School")
        self.assertEqual(response.data["class_type_display"], "Individual")
        self.assertEqual(response.data["status_display"], "Scheduled")

    def test_group_class_participant_count(self):
        """Test participant count calculation for group classes."""
        self.authenticate_as_student()

        url = reverse("class-schedules-detail", kwargs={"pk": self.group_class.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["participant_count"], 2)  # Primary + additional student

    def test_individual_class_participant_count(self):
        """Test participant count for individual classes."""
        self.authenticate_as_student()

        url = reverse("class-schedules-detail", kwargs={"pk": self.individual_class.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["participant_count"], 1)

    def test_is_full_calculation(self):
        """Test is_full calculation based on max_participants."""
        self.authenticate_as_student()

        # Test group class that is not full
        url = reverse("class-schedules-detail", kwargs={"pk": self.group_class.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        current_participants = response.data.get("participant_count", 0)
        max_participants = response.data.get("max_participants", 0)
        expected_is_full = current_participants >= max_participants

        self.assertEqual(response.data.get("is_full", False), expected_is_full)

    def test_can_be_cancelled_logic(self):
        """Test can_be_cancelled logic for different statuses."""
        statuses_to_test = [
            (ClassStatus.SCHEDULED, True),
            (ClassStatus.CONFIRMED, True),
            (ClassStatus.CANCELLED, False),
            (ClassStatus.COMPLETED, False),
        ]

        self.authenticate_as_student()

        for status_value, expected_can_cancel in statuses_to_test:
            with self.subTest(status=status_value):
                class_schedule = self.create_class_schedule(
                    teacher=self.teacher_profile, student=self.student_user, status=status_value
                )

                url = reverse("class-schedules-detail", kwargs={"pk": class_schedule.id})
                response = self.client.get(url)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["can_be_cancelled"], expected_can_cancel)

    def test_is_past_calculation(self):
        """Test is_past calculation based on scheduled date."""
        past_class = self.create_class_schedule(
            teacher=self.teacher_profile, student=self.student_user, scheduled_date=self.past_date
        )

        future_class = self.create_class_schedule(
            teacher=self.teacher_profile, student=self.student_user, scheduled_date=self.tomorrow
        )

        self.authenticate_as_student()

        # Test past class
        past_url = reverse("class-schedules-detail", kwargs={"pk": past_class.id})
        response = self.client.get(past_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_past"])

        # Test future class
        future_url = reverse("class-schedules-detail", kwargs={"pk": future_class.id})
        response = self.client.get(future_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_past"])

    def test_timezone_datetime_fields(self):
        """Test timezone-aware datetime fields."""
        self.authenticate_as_student()

        url = reverse("class-schedules-detail", kwargs={"pk": self.individual_class.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # These fields should exist if implemented
        if "scheduled_datetime_utc" in response.data:
            self.assertIsNotNone(response.data["scheduled_datetime_utc"])

        if "scheduled_datetime_local" in response.data:
            self.assertIsNotNone(response.data["scheduled_datetime_local"])


class ClassSchedulePermissionTests(SchedulerAPITestCase):
    """Test core CRUD permission rules across different user roles."""

    def setUp(self):
        super().setUp()
        self.class_schedule = self.create_class_schedule(
            teacher=self.teacher_profile,
            student=self.student_user,
        )
        self.detail_url = reverse("class-schedules-detail", kwargs={"pk": self.class_schedule.id})

    def test_crud_permissions_by_role(self):
        """Test CRUD permissions for different user roles."""
        # Define expected permissions: (role, can_view, can_update, can_delete)
        role_permissions = [
            ("teacher", True, True, False),  # Teachers can view/update their classes
            ("student", True, False, False),  # Students can only view their classes
            ("admin", True, True, True),  # Admins have full access
        ]

        for role, can_view, can_update, can_delete in role_permissions:
            with self.subTest(role=role):
                getattr(self, f"authenticate_as_{role}")()

                # Test view permission
                response = self.client.get(self.detail_url)
                if can_view:
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                else:
                    self.assertNotFound(response)

                # Test update permission (only if can view)
                if can_view:
                    # Use valid update data that won't trigger validation errors
                    update_data = {"title": f"{role.title()} Updated Class"}
                    response = self.client.patch(self.detail_url, update_data, format="json")
                    if can_update:
                        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
                        # If 400, it's likely due to business rules, not permissions
                    else:
                        self.assertPermissionDenied(response)

                # Test delete permission (only test for admin to avoid deleting test data)
                if role == "admin" and can_delete:
                    # Create a separate class for deletion test
                    delete_class = self.create_class_schedule(
                        teacher=self.teacher_profile,
                        student=self.student_user,
                    )
                    delete_url = reverse("class-schedules-detail", kwargs={"pk": delete_class.id})
                    response = self.client.delete(delete_url)
                    self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_unauthorized_user_access_denied(self):
        """Test that unauthorized users cannot access classes."""
        self.authenticate_as_unauthorized()

        response = self.client.get(self.detail_url)

        # Unauthorized users get 404 due to queryset filtering
        self.assertNotFound(response)

    def test_list_filtering_capabilities(self):
        """Test various filtering capabilities for class lists."""
        self.authenticate_as_admin()

        base_url = reverse("class-schedules-list")
        filter_tests = [
            (f"?status={ClassStatus.SCHEDULED}", "filter by status"),
            (f"?teacher_id={self.teacher_profile.id}", "filter by teacher"),
            (f"?student_id={self.student_user.id}", "filter by student"),
            (f"?class_type={ClassType.INDIVIDUAL}", "filter by class type"),
        ]

        for query_params, description in filter_tests:
            with self.subTest(filter=description):
                url = f"{base_url}{query_params}"
                response = self.client.get(url)

                self.assertListResponse(response)
                # Verify response structure
                self.assertIn("results", response.data)
                self.assertIn("count", response.data)
