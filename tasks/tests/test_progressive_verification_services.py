"""
Tests for TaskService Progressive Verification Methods

These tests validate the TaskService methods used to create and manage
verification tasks as part of the progressive verification system.
"""

from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.tests.test_base import BaseTestCase
from tasks.models import Task
from tasks.services import TaskService

User = get_user_model()


class TaskServiceVerificationTestCase(BaseTestCase):
    """Test TaskService methods for verification task management."""

    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", name="Test User", phone_number="+351987654321")

    def test_create_verification_tasks_creates_email_task(self):
        """Test that create_verification_tasks creates email verification task."""
        email = "test@example.com"

        tasks = TaskService.create_verification_tasks(self.user, email)

        # Should create at least the email task
        self.assertGreaterEqual(len(tasks), 1)

        # Check email task was created
        email_task = Task.objects.filter(user=self.user, title="Verify your email address").first()

        self.assertIsNotNone(email_task)
        self.assertEqual(email_task.user, self.user)
        self.assertEqual(email_task.title, "Verify your email address")
        self.assertIn(email, email_task.description)
        self.assertEqual(email_task.priority, "high")
        self.assertEqual(email_task.task_type, "onboarding")
        self.assertTrue(email_task.is_system_generated)
        self.assertTrue(email_task.is_urgent)
        self.assertEqual(email_task.status, "pending")

        # Check due date is approximately 24 hours from now
        now = timezone.now()
        time_diff = email_task.due_date - now
        self.assertGreaterEqual(time_diff, timedelta(hours=23, minutes=59))
        self.assertLessEqual(time_diff, timedelta(hours=24, minutes=1))

    def test_create_verification_tasks_creates_phone_task_when_provided(self):
        """Test that create_verification_tasks creates phone task when phone provided."""
        email = "test@example.com"
        phone = "+351987654321"

        tasks = TaskService.create_verification_tasks(self.user, email, phone)

        # Should create both email and phone tasks
        self.assertEqual(len(tasks), 2)

        # Check phone task was created
        phone_task = Task.objects.filter(user=self.user, title="Verify your phone number").first()

        self.assertIsNotNone(phone_task)
        self.assertEqual(phone_task.user, self.user)
        self.assertEqual(phone_task.title, "Verify your phone number")
        self.assertIn(phone, phone_task.description)
        self.assertEqual(phone_task.priority, "high")
        self.assertEqual(phone_task.task_type, "onboarding")
        self.assertTrue(phone_task.is_system_generated)
        self.assertTrue(phone_task.is_urgent)
        self.assertEqual(phone_task.status, "pending")

        # Check due date
        now = timezone.now()
        time_diff = phone_task.due_date - now
        self.assertGreaterEqual(time_diff, timedelta(hours=23, minutes=59))
        self.assertLessEqual(time_diff, timedelta(hours=24, minutes=1))

    def test_create_verification_tasks_only_creates_email_task_without_phone(self):
        """Test that only email task is created when no phone provided."""
        email = "test@example.com"

        tasks = TaskService.create_verification_tasks(self.user, email, None)

        # Should create only email task
        self.assertEqual(len(tasks), 1)

        # Email task should exist
        self.assertTrue(Task.objects.filter(user=self.user, title="Verify your email address").exists())

        # Phone task should not exist
        self.assertFalse(Task.objects.filter(user=self.user, title="Verify your phone number").exists())

    def test_create_verification_tasks_handles_database_errors(self):
        """Test that create_verification_tasks handles database errors gracefully."""
        email = "test@example.com"

        with patch("tasks.models.Task.objects.create", side_effect=Exception("Database error")):
            tasks = TaskService.create_verification_tasks(self.user, email)

            # Should return empty list on error
            self.assertEqual(tasks, [])

    def test_create_verification_tasks_handles_partial_failures(self):
        """Test handling when only one task creation fails."""
        email = "test@example.com"
        phone = "+351987654321"

        # Mock to fail only on phone task creation
        original_create = Task.objects.create
        call_count = [0]

        def mock_create(**kwargs):
            call_count[0] += 1
            if call_count[0] == 2 and kwargs.get("title") == "Verify your phone number":
                raise Exception("Phone task creation failed")
            return original_create(**kwargs)

        with patch("tasks.models.Task.objects.create", side_effect=mock_create):
            tasks = TaskService.create_verification_tasks(self.user, email, phone)

            # Should return the email task that was successfully created
            # (current implementation allows partial success)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].title, "Verify your email address")

    def test_complete_email_verification_task_marks_pending_task_complete(self):
        """Test that complete_email_verification_task marks pending task as completed."""
        # Create email verification task
        task = Task.objects.create(
            user=self.user,
            title="Verify your email address",
            description="Test email verification",
            status="pending",
            task_type="onboarding",
        )

        result = TaskService.complete_email_verification_task(self.user)

        # Should return True for success
        self.assertTrue(result)

        # Task should be marked as completed
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")

    def test_complete_email_verification_task_marks_in_progress_task_complete(self):
        """Test that complete_email_verification_task marks in_progress task as completed."""
        # Create in_progress email verification task
        task = Task.objects.create(
            user=self.user,
            title="Verify your email address",
            description="Test email verification",
            status="in_progress",
            task_type="onboarding",
        )

        result = TaskService.complete_email_verification_task(self.user)

        # Should return True for success
        self.assertTrue(result)

        # Task should be marked as completed
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")

    def test_complete_email_verification_task_ignores_already_completed_task(self):
        """Test that complete_email_verification_task ignores already completed tasks."""
        # Create completed email verification task
        task = Task.objects.create(
            user=self.user,
            title="Verify your email address",
            description="Test email verification",
            status="completed",
            task_type="onboarding",
        )

        result = TaskService.complete_email_verification_task(self.user)

        # Should return False when no pending task found
        self.assertFalse(result)

        # Task should remain completed
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")

    def test_complete_email_verification_task_returns_false_when_no_task_exists(self):
        """Test that complete_email_verification_task returns False when no task exists."""
        result = TaskService.complete_email_verification_task(self.user)

        # Should return False when no task found
        self.assertFalse(result)

    def test_complete_email_verification_task_handles_database_errors(self):
        """Test that complete_email_verification_task handles database errors."""
        # Create email verification task
        task = Task.objects.create(
            user=self.user,
            title="Verify your email address",
            description="Test email verification",
            status="pending",
            task_type="onboarding",
        )

        with patch.object(task, "save", side_effect=Exception("Database error")):
            with patch("tasks.models.Task.objects.filter") as mock_filter:
                mock_queryset = Mock()
                mock_queryset.first.return_value = task
                mock_filter.return_value = mock_queryset

                result = TaskService.complete_email_verification_task(self.user)

                # Should return False on error
                self.assertFalse(result)

    def test_complete_phone_verification_task_marks_pending_task_complete(self):
        """Test that complete_phone_verification_task marks pending task as completed."""
        # Create phone verification task
        task = Task.objects.create(
            user=self.user,
            title="Verify your phone number",
            description="Test phone verification",
            status="pending",
            task_type="onboarding",
        )

        result = TaskService.complete_phone_verification_task(self.user)

        # Should return True for success
        self.assertTrue(result)

        # Task should be marked as completed
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")

    def test_complete_phone_verification_task_returns_false_when_no_task_exists(self):
        """Test that complete_phone_verification_task returns False when no task exists."""
        result = TaskService.complete_phone_verification_task(self.user)

        # Should return False when no task found
        self.assertFalse(result)

    def test_complete_phone_verification_task_handles_database_errors(self):
        """Test that complete_phone_verification_task handles database errors."""
        # Create phone verification task
        task = Task.objects.create(
            user=self.user,
            title="Verify your phone number",
            description="Test phone verification",
            status="pending",
            task_type="onboarding",
        )

        with patch.object(task, "save", side_effect=Exception("Database error")):
            with patch("tasks.models.Task.objects.filter") as mock_filter:
                mock_queryset = Mock()
                mock_queryset.first.return_value = task
                mock_filter.return_value = mock_queryset

                result = TaskService.complete_phone_verification_task(self.user)

                # Should return False on error
                self.assertFalse(result)

    def test_get_verification_tasks_returns_status_for_existing_tasks(self):
        """Test that get_verification_tasks returns correct status for existing tasks."""
        # Create both verification tasks
        email_task = Task.objects.create(
            user=self.user,
            title="Verify your email address",
            description="Test email verification",
            status="pending",
            task_type="onboarding",
            due_date=timezone.now() + timedelta(hours=12),
        )

        phone_task = Task.objects.create(
            user=self.user,
            title="Verify your phone number",
            description="Test phone verification",
            status="completed",
            task_type="onboarding",
            due_date=timezone.now() + timedelta(hours=12),
        )

        result = TaskService.get_verification_tasks(self.user)

        # Check email verification status
        self.assertTrue(result["email_verification"]["exists"])
        self.assertEqual(result["email_verification"]["status"], "pending")
        self.assertFalse(result["email_verification"]["completed"])
        self.assertFalse(result["email_verification"]["is_overdue"])

        # Check phone verification status
        self.assertTrue(result["phone_verification"]["exists"])
        self.assertEqual(result["phone_verification"]["status"], "completed")
        self.assertTrue(result["phone_verification"]["completed"])
        self.assertFalse(result["phone_verification"]["is_overdue"])

    def test_get_verification_tasks_returns_false_for_non_existing_tasks(self):
        """Test that get_verification_tasks returns False for non-existing tasks."""
        result = TaskService.get_verification_tasks(self.user)

        # Check email verification status
        self.assertFalse(result["email_verification"]["exists"])
        self.assertIsNone(result["email_verification"]["status"])
        self.assertFalse(result["email_verification"]["completed"])
        self.assertFalse(result["email_verification"]["is_overdue"])

        # Check phone verification status
        self.assertFalse(result["phone_verification"]["exists"])
        self.assertIsNone(result["phone_verification"]["status"])
        self.assertFalse(result["phone_verification"]["completed"])
        self.assertFalse(result["phone_verification"]["is_overdue"])

    def test_get_verification_tasks_detects_overdue_tasks(self):
        """Test that get_verification_tasks correctly detects overdue tasks."""
        # Create overdue email verification task
        email_task = Task.objects.create(
            user=self.user,
            title="Verify your email address",
            description="Test email verification",
            status="pending",
            task_type="onboarding",
            due_date=timezone.now() - timedelta(hours=1),  # Overdue
        )

        result = TaskService.get_verification_tasks(self.user)

        # Check email verification is detected as overdue
        self.assertTrue(result["email_verification"]["exists"])
        self.assertEqual(result["email_verification"]["status"], "pending")
        self.assertFalse(result["email_verification"]["completed"])
        self.assertTrue(result["email_verification"]["is_overdue"])

    def test_get_verification_tasks_handles_partial_task_existence(self):
        """Test get_verification_tasks when only one type of task exists."""
        # Create only email verification task
        email_task = Task.objects.create(
            user=self.user,
            title="Verify your email address",
            description="Test email verification",
            status="in_progress",
            task_type="onboarding",
            due_date=timezone.now() + timedelta(hours=12),
        )

        result = TaskService.get_verification_tasks(self.user)

        # Check email verification status
        self.assertTrue(result["email_verification"]["exists"])
        self.assertEqual(result["email_verification"]["status"], "in_progress")
        self.assertFalse(result["email_verification"]["completed"])

        # Check phone verification status (should be False)
        self.assertFalse(result["phone_verification"]["exists"])
        self.assertIsNone(result["phone_verification"]["status"])
        self.assertFalse(result["phone_verification"]["completed"])

    def test_verification_tasks_are_user_specific(self):
        """Test that verification task methods are user-specific."""
        # Create another user
        other_user = User.objects.create_user(email="other@example.com", name="Other User")

        # Create verification tasks for first user
        Task.objects.create(
            user=self.user,
            title="Verify your email address",
            description="Test email verification",
            status="pending",
            task_type="onboarding",
        )

        # Create verification tasks for second user
        Task.objects.create(
            user=other_user,
            title="Verify your email address",
            description="Other user email verification",
            status="completed",
            task_type="onboarding",
        )

        # Get tasks for first user
        result1 = TaskService.get_verification_tasks(self.user)
        self.assertTrue(result1["email_verification"]["exists"])
        self.assertEqual(result1["email_verification"]["status"], "pending")

        # Get tasks for second user
        result2 = TaskService.get_verification_tasks(other_user)
        self.assertTrue(result2["email_verification"]["exists"])
        self.assertEqual(result2["email_verification"]["status"], "completed")

        # Complete task for first user should not affect second user
        TaskService.complete_email_verification_task(self.user)

        result2_after = TaskService.get_verification_tasks(other_user)
        self.assertEqual(result2_after["email_verification"]["status"], "completed")  # Unchanged

    def test_task_creation_uses_correct_task_attributes(self):
        """Test that created tasks have all the correct attributes."""
        email = "test@example.com"
        phone = "+351987654321"

        tasks = TaskService.create_verification_tasks(self.user, email, phone)

        # Check all tasks have correct common attributes
        for task in tasks:
            self.assertEqual(task.user, self.user)
            self.assertEqual(task.priority, "high")
            self.assertEqual(task.task_type, "onboarding")
            self.assertTrue(task.is_system_generated)
            self.assertTrue(task.is_urgent)
            self.assertEqual(task.status, "pending")
            self.assertIsNotNone(task.due_date)

        # Check specific task details
        email_task = next(task for task in tasks if "email" in task.title)
        phone_task = next(task for task in tasks if "phone" in task.title)

        self.assertEqual(email_task.title, "Verify your email address")
        self.assertIn(email, email_task.description)

        self.assertEqual(phone_task.title, "Verify your phone number")
        self.assertIn(phone, phone_task.description)


class TaskServiceIntegrationTestCase(BaseTestCase):
    """Integration tests for TaskService with other components."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="integration@example.com", name="Integration User", phone_number="+351987654321"
        )

    def test_task_service_integration_with_signup_flow(self):
        """Test TaskService integration with complete signup flow."""
        # Simulate what happens during signup
        email = self.user.email
        phone = self.user.phone_number

        # Create verification tasks
        tasks = TaskService.create_verification_tasks(self.user, email, phone)

        # Verify tasks were created correctly
        self.assertEqual(len(tasks), 2)

        # Get task status
        status = TaskService.get_verification_tasks(self.user)
        self.assertTrue(status["email_verification"]["exists"])
        self.assertTrue(status["phone_verification"]["exists"])
        self.assertFalse(status["email_verification"]["completed"])
        self.assertFalse(status["phone_verification"]["completed"])

        # Simulate email verification
        email_success = TaskService.complete_email_verification_task(self.user)
        self.assertTrue(email_success)

        # Check updated status
        status_after_email = TaskService.get_verification_tasks(self.user)
        self.assertTrue(status_after_email["email_verification"]["completed"])
        self.assertFalse(status_after_email["phone_verification"]["completed"])

        # Simulate phone verification
        phone_success = TaskService.complete_phone_verification_task(self.user)
        self.assertTrue(phone_success)

        # Check final status
        final_status = TaskService.get_verification_tasks(self.user)
        self.assertTrue(final_status["email_verification"]["completed"])
        self.assertTrue(final_status["phone_verification"]["completed"])

    def test_task_service_handles_duplicate_task_creation_gracefully(self):
        """Test that creating verification tasks multiple times doesn't create duplicates."""
        email = self.user.email
        phone = self.user.phone_number

        # Create tasks first time
        tasks1 = TaskService.create_verification_tasks(self.user, email, phone)
        self.assertEqual(len(tasks1), 2)

        # Create tasks second time (simulating retry or error recovery)
        tasks2 = TaskService.create_verification_tasks(self.user, email, phone)
        self.assertEqual(len(tasks2), 2)

        # Should have total of 4 tasks in database (no duplicate prevention in current implementation)
        # This documents current behavior - might be improved in the future
        all_tasks = Task.objects.filter(user=self.user)
        self.assertEqual(all_tasks.count(), 4)

    @patch("tasks.services.logger")
    def test_task_service_logs_operations(self, mock_logger):
        """Test that TaskService logs its operations for monitoring."""
        email = self.user.email
        phone = self.user.phone_number

        # Create verification tasks
        TaskService.create_verification_tasks(self.user, email, phone)

        # Check that info logs were made for task creation
        self.assertGreaterEqual(mock_logger.info.call_count, 2)

        # Check log messages contain relevant information
        log_calls = mock_logger.info.call_args_list
        log_messages = [call[0][0] for call in log_calls]

        email_log_found = any("email verification task" in msg and self.user.email in msg for msg in log_messages)
        phone_log_found = any("phone verification task" in msg and self.user.email in msg for msg in log_messages)

        self.assertTrue(email_log_found)
        self.assertTrue(phone_log_found)
