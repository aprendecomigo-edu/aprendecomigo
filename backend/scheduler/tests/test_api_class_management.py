"""
API Tests for Class Management Endpoints.

Tests the class management workflow endpoints:
- POST /api/scheduler/schedules/{id}/confirm/ - Teacher confirms a scheduled class
- POST /api/scheduler/schedules/{id}/cancel/ - Cancel a class with reason
- POST /api/scheduler/schedules/{id}/reject/ - Teacher rejects a class request

Test Coverage:
- Authentication and permission checks (only appropriate users can manage classes)
- Status transition validation (SCHEDULED → CONFIRMED/CANCELLED/REJECTED)
- Required metadata capture (cancellation reasons, timestamps)
- Business rule validation (cannot modify final states)
- Error handling for invalid operations
"""

from django.urls import reverse
from rest_framework import status

from scheduler.models import ClassStatus

from .test_base import SchedulerAPITestCase


class ClassConfirmationTests(SchedulerAPITestCase):
    """Test class confirmation functionality."""

    def setUp(self):
        super().setUp()
        self.scheduled_class = self.create_class_schedule(
            status=ClassStatus.SCHEDULED, teacher=self.teacher_profile, student=self.student_user
        )
        self.confirm_url = reverse("class-schedules-confirm", kwargs={"pk": self.scheduled_class.id})

    def test_teacher_can_confirm_own_class(self):
        """Test that teachers can confirm their own scheduled classes."""
        self.authenticate_as_teacher()

        response = self.client.post(self.confirm_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.scheduled_class.refresh_from_db()
        self.assertEqual(self.scheduled_class.status, ClassStatus.CONFIRMED)

    def test_different_teacher_cannot_confirm_class(self):
        """Test that teachers cannot confirm other teachers' classes."""
        self.authenticate_as_teacher(self.teacher_user2)

        response = self.client.post(self.confirm_url)

        self.assertPermissionDenied(response)

    def test_student_cannot_confirm_class(self):
        """Test that students cannot confirm classes."""
        self.authenticate_as_student()

        response = self.client.post(self.confirm_url)

        self.assertPermissionDenied(response)

    def test_admin_can_confirm_any_class(self):
        """Test that school admins can confirm any class in their school."""
        self.authenticate_as_admin()

        response = self.client.post(self.confirm_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.scheduled_class.refresh_from_db()
        self.assertEqual(self.scheduled_class.status, ClassStatus.CONFIRMED)

    def test_unauthenticated_user_cannot_confirm(self):
        """Test that unauthenticated users cannot confirm classes."""
        response = self.client.post(self.confirm_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_confirm_invalid_status_transitions_fail(self):
        """Test that confirming classes in invalid states returns error."""
        self.authenticate_as_teacher()

        # Test invalid status transitions
        invalid_statuses = [
            (ClassStatus.CONFIRMED, "already confirmed"),
            (ClassStatus.CANCELLED, "cancelled class"),
            (ClassStatus.COMPLETED, "completed class"),
            (ClassStatus.REJECTED, "rejected class"),
        ]

        for status_value, description in invalid_statuses:
            with self.subTest(status=description):
                test_class = self.create_class_schedule(
                    status=status_value, teacher=self.teacher_profile, student=self.student_user
                )

                url = reverse("class-schedules-confirm", kwargs={"pk": test_class.id})
                response = self.client.post(url)

                self.assertValidationError(response)

    def test_confirm_nonexistent_class_returns_404(self):
        """Test that confirming non-existent class returns 404."""
        nonexistent_url = reverse("class-schedules-confirm", kwargs={"pk": 99999})

        self.authenticate_as_teacher()
        response = self.client.post(nonexistent_url)

        self.assertNotFound(response)


class ClassCancellationTests(SchedulerAPITestCase):
    """Test class cancellation functionality."""

    def setUp(self):
        super().setUp()
        self.scheduled_class = self.create_class_schedule(
            status=ClassStatus.SCHEDULED, teacher=self.teacher_profile, student=self.student_user
        )
        self.cancel_url = reverse("class-schedules-cancel", kwargs={"pk": self.scheduled_class.id})

    def test_teacher_can_cancel_own_class_with_reason(self):
        """Test that teachers can cancel their own classes with reason."""
        self.authenticate_as_teacher()

        data = {"reason": "Personal emergency"}
        response = self.client.post(self.cancel_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.scheduled_class.refresh_from_db()
        self.assertEqual(self.scheduled_class.status, ClassStatus.CANCELLED)
        self.assertEqual(self.scheduled_class.cancelled_by, self.teacher_user)
        self.assertEqual(self.scheduled_class.cancellation_reason, "Personal emergency")

    def test_student_can_cancel_own_class_with_reason(self):
        """Test that students can cancel their own classes with reason."""
        self.authenticate_as_student()

        data = {"reason": "Schedule conflict"}
        response = self.client.post(self.cancel_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.scheduled_class.refresh_from_db()
        self.assertEqual(self.scheduled_class.status, ClassStatus.CANCELLED)
        self.assertEqual(self.scheduled_class.cancelled_by, self.student_user)

    def test_admin_can_cancel_any_class(self):
        """Test that admins can cancel any class in their school."""
        self.authenticate_as_admin()

        data = {"reason": "Administrative cancellation"}
        response = self.client.post(self.cancel_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.scheduled_class.refresh_from_db()
        self.assertEqual(self.scheduled_class.status, ClassStatus.CANCELLED)

    def test_cancel_with_optional_reason(self):
        """Test that cancellation works with and without reason."""
        self.authenticate_as_teacher()

        test_cases = [
            ({}, "without reason"),
            ({"reason": "Family emergency"}, "with reason"),
        ]

        for data, description in test_cases:
            with self.subTest(description=description):
                test_class = self.create_class_schedule(
                    status=ClassStatus.SCHEDULED, teacher=self.teacher_profile, student=self.student_user
                )

                url = reverse("class-schedules-cancel", kwargs={"pk": test_class.id})
                response = self.client.post(url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                test_class.refresh_from_db()
                self.assertEqual(test_class.status, ClassStatus.CANCELLED)
                if "reason" in data:
                    self.assertEqual(test_class.cancellation_reason, data["reason"])

    def test_unauthorized_user_cannot_cancel_class(self):
        """Test that unauthorized users cannot cancel classes."""
        self.authenticate_as_student(self.student_user2)  # Different student

        data = {"reason": "Unauthorized attempt"}
        response = self.client.post(self.cancel_url, data, format="json")

        self.assertPermissionDenied(response)

    def test_cancel_confirmed_class_success(self):
        """Test that confirmed classes can still be cancelled."""
        self.scheduled_class.status = ClassStatus.CONFIRMED
        self.scheduled_class.save()

        self.authenticate_as_teacher()
        data = {"reason": "Last minute emergency"}
        response = self.client.post(self.cancel_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.scheduled_class.refresh_from_db()
        self.assertEqual(self.scheduled_class.status, ClassStatus.CANCELLED)

    def test_cancel_invalid_status_transitions_fail(self):
        """Test that cancelling classes in invalid final states returns error."""
        self.authenticate_as_teacher()

        # Only final states that cannot be cancelled
        invalid_statuses = [
            (ClassStatus.CANCELLED, "already cancelled"),
            (ClassStatus.COMPLETED, "completed class"),
        ]

        for status_value, description in invalid_statuses:
            with self.subTest(status=description):
                test_class = self.create_class_schedule(
                    status=status_value, teacher=self.teacher_profile, student=self.student_user
                )

                url = reverse("class-schedules-cancel", kwargs={"pk": test_class.id})
                data = {"reason": f"Cannot cancel {description}"}
                response = self.client.post(url, data, format="json")

                self.assertValidationError(response)


class ClassRejectionTests(SchedulerAPITestCase):
    """Test class rejection functionality."""

    def setUp(self):
        super().setUp()
        self.scheduled_class = self.create_class_schedule(
            status=ClassStatus.SCHEDULED, teacher=self.teacher_profile, student=self.student_user
        )
        self.reject_url = reverse("class-schedules-reject", kwargs={"pk": self.scheduled_class.id})

    def test_teacher_can_reject_own_scheduled_class(self):
        """Test that teachers can reject their own scheduled classes."""
        self.authenticate_as_teacher()

        data = {"reason": "Conflict with existing schedule"}
        response = self.client.post(self.reject_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.scheduled_class.refresh_from_db()
        self.assertEqual(self.scheduled_class.status, ClassStatus.REJECTED)
        # Note: rejected classes don't set cancelled_by field - rejection is a separate operation

    def test_different_teacher_cannot_reject_class(self):
        """Test that teachers cannot reject other teachers' classes."""
        self.authenticate_as_teacher(self.teacher_user2)

        data = {"reason": "Unauthorized rejection"}
        response = self.client.post(self.reject_url, data, format="json")

        self.assertPermissionDenied(response)

    def test_student_cannot_reject_class(self):
        """Test that students cannot reject classes."""
        self.authenticate_as_student()

        data = {"reason": "Student rejection attempt"}
        response = self.client.post(self.reject_url, data, format="json")

        self.assertPermissionDenied(response)

    def test_admin_can_reject_any_class(self):
        """Test that admins can reject any class in their school."""
        self.authenticate_as_admin()

        data = {"reason": "Administrative rejection"}
        response = self.client.post(self.reject_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.scheduled_class.refresh_from_db()
        self.assertEqual(self.scheduled_class.status, ClassStatus.REJECTED)

    def test_reject_with_optional_reason(self):
        """Test that rejection works with and without reason."""
        self.authenticate_as_teacher()

        test_cases = [
            ({}, "without reason"),
            ({"reason": "Schedule conflict"}, "with reason"),
        ]

        for data, description in test_cases:
            with self.subTest(description=description):
                test_class = self.create_class_schedule(
                    status=ClassStatus.SCHEDULED, teacher=self.teacher_profile, student=self.student_user
                )

                url = reverse("class-schedules-reject", kwargs={"pk": test_class.id})
                response = self.client.post(url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                test_class.refresh_from_db()
                self.assertEqual(test_class.status, ClassStatus.REJECTED)

    def test_reject_invalid_status_transitions_fail(self):
        """Test that rejecting classes in invalid states returns error."""
        self.authenticate_as_teacher()

        # Test invalid status transitions for rejection
        invalid_statuses = [
            (ClassStatus.CONFIRMED, "confirmed class"),
            (ClassStatus.CANCELLED, "cancelled class"),
            (ClassStatus.COMPLETED, "completed class"),
            (ClassStatus.REJECTED, "already rejected"),
        ]

        for status_value, description in invalid_statuses:
            with self.subTest(status=description):
                test_class = self.create_class_schedule(
                    status=status_value, teacher=self.teacher_profile, student=self.student_user
                )

                url = reverse("class-schedules-reject", kwargs={"pk": test_class.id})
                data = {"reason": f"Cannot reject {description}"}
                response = self.client.post(url, data, format="json")

                self.assertValidationError(response)


class ClassStatusTransitionTests(SchedulerAPITestCase):
    """Test valid status transitions for class management."""

    def setUp(self):
        super().setUp()
        self.authenticate_as_teacher()

    def test_valid_scheduled_to_confirmed_transition(self):
        """Test valid status transition from SCHEDULED to CONFIRMED."""
        class_schedule = self.create_class_schedule(status=ClassStatus.SCHEDULED)
        url = reverse("class-schedules-confirm", kwargs={"pk": class_schedule.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        class_schedule.refresh_from_db()
        self.assertEqual(class_schedule.status, ClassStatus.CONFIRMED)

    def test_valid_scheduled_to_cancelled_transition(self):
        """Test valid status transition from SCHEDULED to CANCELLED."""
        class_schedule = self.create_class_schedule(status=ClassStatus.SCHEDULED)
        url = reverse("class-schedules-cancel", kwargs={"pk": class_schedule.id})

        data = {"reason": "Teacher illness"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        class_schedule.refresh_from_db()
        self.assertEqual(class_schedule.status, ClassStatus.CANCELLED)

    def test_valid_scheduled_to_rejected_transition(self):
        """Test valid status transition from SCHEDULED to REJECTED."""
        class_schedule = self.create_class_schedule(status=ClassStatus.SCHEDULED)
        url = reverse("class-schedules-reject", kwargs={"pk": class_schedule.id})

        data = {"reason": "Schedule conflict discovered"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        class_schedule.refresh_from_db()
        self.assertEqual(class_schedule.status, ClassStatus.REJECTED)

    def test_confirmed_can_be_cancelled(self):
        """Test that confirmed classes can still be cancelled."""
        class_schedule = self.create_class_schedule(status=ClassStatus.CONFIRMED)
        url = reverse("class-schedules-cancel", kwargs={"pk": class_schedule.id})

        data = {"reason": "Emergency cancellation"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        class_schedule.refresh_from_db()
        self.assertEqual(class_schedule.status, ClassStatus.CANCELLED)

    def test_final_states_cannot_transition(self):
        """Test that final states (CANCELLED, REJECTED, COMPLETED) cannot transition."""
        final_statuses = [ClassStatus.CANCELLED, ClassStatus.REJECTED, ClassStatus.COMPLETED]

        for final_status in final_statuses:
            with self.subTest(status=final_status):
                class_schedule = self.create_class_schedule(status=final_status)

                # Try to confirm
                confirm_url = reverse("class-schedules-confirm", kwargs={"pk": class_schedule.id})
                response = self.client.post(confirm_url)
                self.assertValidationError(response)

                # Try to reject (if not already rejected)
                if final_status != ClassStatus.REJECTED:
                    reject_url = reverse("class-schedules-reject", kwargs={"pk": class_schedule.id})
                    data = {"reason": "Cannot reject final state"}
                    response = self.client.post(reject_url, data, format="json")
                    self.assertValidationError(response)


class ClassManagementPermissionTests(SchedulerAPITestCase):
    """Test permission requirements for cross-role class management operations."""

    def setUp(self):
        super().setUp()
        self.class_schedule = self.create_class_schedule(
            teacher=self.teacher_profile, student=self.student_user, status=ClassStatus.SCHEDULED
        )

    def test_cross_role_permission_matrix(self):
        """Test permission matrix for different roles and operations."""
        operations = [
            ("confirm", "class-schedules-confirm", {}),
            ("reject", "class-schedules-reject", {"reason": "Test rejection"}),
            ("cancel", "class-schedules-cancel", {"reason": "Test cancellation"}),
        ]

        # Permission matrix: (role, allowed_operations)
        role_permissions = [
            ("teacher", ["confirm", "reject", "cancel"]),
            ("student", ["cancel"]),  # Students can only cancel
            ("admin", ["confirm", "reject", "cancel"]),
        ]

        for role, allowed_ops in role_permissions:
            with self.subTest(role=role):
                # Authenticate as the role
                getattr(self, f"authenticate_as_{role}")()

                for op_name, url_name, data in operations:
                    with self.subTest(operation=op_name):
                        # Create fresh class for each test
                        test_class = self.create_class_schedule(
                            teacher=self.teacher_profile, student=self.student_user, status=ClassStatus.SCHEDULED
                        )

                        url = reverse(url_name, kwargs={"pk": test_class.id})
                        response = self.client.post(url, data, format="json")

                        if op_name in allowed_ops:
                            self.assertEqual(response.status_code, status.HTTP_200_OK)
                        else:
                            self.assertPermissionDenied(response)
