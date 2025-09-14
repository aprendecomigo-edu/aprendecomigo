"""
Tests for TaskService functionality.

This module tests the TaskService class which provides programmatic
task management including:
- System task initialization
- Task completion logic
- Verification status queries
- Legacy compatibility methods
"""

import logging
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from tasks.models import Task
from tasks.services import TaskService

User = get_user_model()


class TaskServiceInitializationTest(TestCase):
    """Test TaskService system task initialization."""

    def setUp(self):
        """Set up test data."""
        # Create user WITHOUT deleting signal-created tasks
        # We want to test the real system behavior
        pass

    def test_initialize_system_tasks_creates_all_tasks(self):
        """Test that initialize_system_tasks creates all expected system tasks."""
        # Create a fresh user for this test
        user = User.objects.create_user(email="init_test@example.com", name="Init Test User")

        # Signals should have already created 3 system tasks
        system_tasks = Task.system_tasks.for_user(user)
        self.assertEqual(system_tasks.count(), 3, "Signals should create 3 system tasks")

        # Calling initialize again should be idempotent (no new tasks created)
        created_tasks = TaskService.initialize_system_tasks(user)
        self.assertEqual(len(created_tasks), 0, "Should not create duplicate tasks")

        # Total should still be 3
        system_tasks = Task.system_tasks.for_user(user)
        self.assertEqual(system_tasks.count(), 3)

        # Verify specific system codes exist
        email_task = system_tasks.filter(system_code=Task.EMAIL_VERIFICATION).first()
        phone_task = system_tasks.filter(system_code=Task.PHONE_VERIFICATION).first()
        student_task = system_tasks.filter(system_code=Task.FIRST_STUDENT_ADDED).first()

        self.assertIsNotNone(email_task)
        self.assertIsNotNone(phone_task)
        self.assertIsNotNone(student_task)

    def test_initialize_system_tasks_creates_correct_properties(self):
        """Test that system tasks are created with correct properties."""
        user = User.objects.create_user(email="props_test@example.com", name="Props Test User")

        # System tasks should have been created by signals
        system_tasks = Task.system_tasks.for_user(user)

        for task in system_tasks:
            self.assertEqual(task.user, user)
            self.assertEqual(task.task_type, "system")
            self.assertTrue(task.is_system_generated)
            self.assertEqual(task.status, "pending")
            self.assertIsNotNone(task.system_code)
            self.assertIn(
                task.system_code, [Task.EMAIL_VERIFICATION, Task.PHONE_VERIFICATION, Task.FIRST_STUDENT_ADDED]
            )

    def test_initialize_system_tasks_sets_correct_priorities(self):
        """Test that system tasks are created with correct priorities."""
        user = User.objects.create_user(email="priority_test@example.com", name="Priority Test User")

        # Email and phone should be high priority
        email_task = Task.system_tasks.by_system_code(user, Task.EMAIL_VERIFICATION).first()
        phone_task = Task.system_tasks.by_system_code(user, Task.PHONE_VERIFICATION).first()
        self.assertEqual(email_task.priority, "high")
        self.assertEqual(phone_task.priority, "high")

        # First student should be medium priority
        student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
        self.assertEqual(student_task.priority, "medium")

    def test_initialize_system_tasks_is_idempotent(self):
        """Test that calling initialize_system_tasks multiple times doesn't create duplicates."""
        user = User.objects.create_user(email="idempotent_test@example.com", name="Idempotent Test User")

        # Signals should have created 3 tasks
        self.assertEqual(Task.system_tasks.for_user(user).count(), 3)

        # First call should not create new tasks (they already exist)
        first_call_tasks = TaskService.initialize_system_tasks(user)
        self.assertEqual(len(first_call_tasks), 0)

        # Second call should still not create new tasks
        second_call_tasks = TaskService.initialize_system_tasks(user)
        self.assertEqual(len(second_call_tasks), 0)

        # Total tasks should still be 3
        system_tasks = Task.system_tasks.for_user(user)
        self.assertEqual(system_tasks.count(), 3)

    def test_initialize_system_tasks_with_partial_existing_tasks(self):
        """Test initialization when some system tasks already exist."""
        # Create one system task manually (existing signal-created tasks were cleared)
        existing_task = Task.objects.create(
            title="Existing Email Verification",
            user=self.user,
            task_type="system",
            system_code=Task.EMAIL_VERIFICATION,
            is_system_generated=True,
        )

        # Initialize system tasks
        created_tasks = TaskService.initialize_system_tasks(self.user)

        # Should only create 2 new tasks (phone and student)
        self.assertEqual(len(created_tasks), 2)

        # Total should be 3
        system_tasks = Task.system_tasks.for_user(self.user)
        self.assertEqual(system_tasks.count(), 3)

        # Existing task should still exist
        self.assertTrue(Task.objects.filter(id=existing_task.id).exists())

    @patch("tasks.services.logger")
    def test_initialize_system_tasks_logs_creation(self, mock_logger):
        """Test that task creation is logged."""
        TaskService.initialize_system_tasks(self.user)

        # Should have logged creation of 3 tasks
        self.assertEqual(mock_logger.info.call_count, 3)

        # Verify log messages contain expected information
        log_calls = mock_logger.info.call_args_list
        for call in log_calls:
            message = call[0][0]
            self.assertIn("Created system task", message)
            self.assertIn(self.user.email, message)


class TaskServiceCompletionTest(TestCase):
    """Test TaskService task completion functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="completion_test@example.com", name="Completion Test User")
        # DON'T delete signal-created tasks - test the real system!
        # Verify we have the expected system tasks
        self.assertEqual(Task.system_tasks.for_user(self.user).count(), 3)

    def test_complete_system_task_marks_task_completed(self):
        """Test that complete_system_task marks task as completed."""
        result = TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)

        # Should return the completed task
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Task)

        # Task should be completed
        task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(task.status, "completed")
        self.assertIsNotNone(task.completed_at)

    def test_complete_system_task_sets_timestamp(self):
        """Test that completing a system task sets completed_at timestamp."""
        before_completion = timezone.now()
        result = TaskService.complete_system_task(self.user, Task.PHONE_VERIFICATION)
        after_completion = timezone.now()

        self.assertIsNotNone(result.completed_at)
        self.assertGreaterEqual(result.completed_at, before_completion)
        self.assertLessEqual(result.completed_at, after_completion)

    def test_complete_system_task_already_completed(self):
        """Test completing an already completed task."""
        # Complete the task first time
        first_result = TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)
        first_completion_time = first_result.completed_at

        # Complete again
        second_result = TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)

        # Should return None since task was already completed
        self.assertIsNone(second_result)

        # Original completion time should be preserved
        task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(task.completed_at, first_completion_time)

    def test_complete_system_task_nonexistent_task(self):
        """Test completing a system task that doesn't exist."""
        result = TaskService.complete_system_task(self.user, "NONEXISTENT_CODE")

        self.assertIsNone(result)

    def test_complete_system_task_wrong_user(self):
        """Test completing a system task for wrong user."""
        other_user = User.objects.create_user(email="other@example.com", name="Other User")

        result = TaskService.complete_system_task(other_user, Task.EMAIL_VERIFICATION)

        self.assertIsNone(result)

        # Original task should remain unchanged
        original_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(original_task.status, "pending")

    @patch("tasks.services.logger")
    def test_complete_system_task_logs_completion(self, mock_logger):
        """Test that task completion is logged."""
        TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)

        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn("Completed system task", log_message)
        self.assertIn(Task.EMAIL_VERIFICATION, log_message)
        self.assertIn(self.user.email, log_message)

    @patch("tasks.services.logger")
    def test_complete_system_task_logs_not_found(self, mock_logger):
        """Test that missing task is logged as warning."""
        TaskService.complete_system_task(self.user, "NONEXISTENT_CODE")

        mock_logger.warning.assert_called_once()
        log_message = mock_logger.warning.call_args[0][0]
        self.assertIn("System task NONEXISTENT_CODE not found", log_message)
        self.assertIn(self.user.email, log_message)


class TaskServiceVerificationStatusTest(TestCase):
    """Test TaskService verification status functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")
        # Clear system tasks created by signals
        Task.system_tasks.for_user(self.user).delete()
        # Create system tasks
        TaskService.initialize_system_tasks(self.user)

    def test_get_verification_status_all_pending(self):
        """Test verification status when all tasks are pending."""
        status = TaskService.get_verification_status(self.user)

        expected = {
            "email_verified": False,
            "phone_verified": False,
            "first_student_added": False,
        }

        self.assertEqual(status, expected)

    def test_get_verification_status_mixed_completion(self):
        """Test verification status with some tasks completed."""
        # Complete email verification
        TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)

        status = TaskService.get_verification_status(self.user)

        expected = {
            "email_verified": True,
            "phone_verified": False,
            "first_student_added": False,
        }

        self.assertEqual(status, expected)

    def test_get_verification_status_all_completed(self):
        """Test verification status when all tasks are completed."""
        # Complete all tasks
        TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)
        TaskService.complete_system_task(self.user, Task.PHONE_VERIFICATION)
        TaskService.complete_system_task(self.user, Task.FIRST_STUDENT_ADDED)

        status = TaskService.get_verification_status(self.user)

        expected = {
            "email_verified": True,
            "phone_verified": True,
            "first_student_added": True,
        }

        self.assertEqual(status, expected)

    def test_get_verification_status_user_without_tasks(self):
        """Test verification status for user without system tasks."""
        new_user = User.objects.create_user(email="new@example.com", name="New User")

        status = TaskService.get_verification_status(new_user)

        # Should return all False
        expected = {
            "email_verified": False,
            "phone_verified": False,
            "first_student_added": False,
        }

        self.assertEqual(status, expected)

    def test_get_verification_status_partial_tasks(self):
        """Test verification status when user has only some system tasks."""
        new_user = User.objects.create_user(email="partial@example.com", name="Partial User")

        # Complete only email verification task (signals already created all system tasks)
        TaskService.complete_system_task(new_user, Task.EMAIL_VERIFICATION)

        status = TaskService.get_verification_status(new_user)

        expected = {
            "email_verified": True,
            "phone_verified": False,
            "first_student_added": False,
        }

        self.assertEqual(status, expected)


class TaskServiceBooleanFieldSyncTest(TestCase):
    """Test TaskService boolean field synchronization functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="sync_test@example.com", name="Sync Test User")
        # Work with real signal-created tasks
        self.assertEqual(Task.system_tasks.for_user(self.user).count(), 3)

    def test_complete_email_task_syncs_boolean_field(self):
        """Test that completing email verification task updates user.email_verified."""
        # Initially both should be False/pending
        self.assertFalse(self.user.email_verified)
        email_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(email_task.status, "pending")

        # Complete the system task
        result = TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)

        # Verify task completion
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "completed")

        # Verify boolean field was synced
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified, "Boolean field should be synced to True")

    def test_complete_phone_task_syncs_boolean_field(self):
        """Test that completing phone verification task updates user.phone_verified."""
        # Initially both should be False/pending
        self.assertFalse(self.user.phone_verified)
        phone_task = Task.system_tasks.by_system_code(self.user, Task.PHONE_VERIFICATION).first()
        self.assertEqual(phone_task.status, "pending")

        # Complete the system task
        result = TaskService.complete_system_task(self.user, Task.PHONE_VERIFICATION)

        # Verify task completion
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "completed")

        # Verify boolean field was synced
        self.user.refresh_from_db()
        self.assertTrue(self.user.phone_verified, "Boolean field should be synced to True")

    def test_complete_task_when_boolean_already_true_no_duplicate_update(self):
        """Test completing task when boolean field is already True doesn't cause issues."""
        # Set boolean field to True first (this triggers signal to complete the task)
        self.user.email_verified = True
        self.user.save()

        # Task should now already be completed by the signal
        email_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(email_task.status, "completed", "Signal should have completed the task")

        # Calling complete_system_task again should return None (already completed)
        result = TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)
        self.assertIsNone(result, "Should return None when task is already completed")

        # Boolean field should remain True
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_sync_only_updates_relevant_boolean_field(self):
        """Test that completing one task doesn't affect other boolean fields."""
        # Complete only email verification
        result = TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)
        self.assertIsNotNone(result)

        # Check that only email_verified is updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified, "Email should be verified")
        self.assertFalse(self.user.phone_verified, "Phone should remain unverified")

    @patch("tasks.services.logger")
    def test_boolean_field_sync_is_logged(self, mock_logger):
        """Test that boolean field synchronization is logged."""
        TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)

        # Should have logged both task completion and boolean field update
        self.assertEqual(mock_logger.info.call_count, 2)

        # Check boolean field update log
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        boolean_log = next((log for log in log_calls if "Updated boolean fields" in log), None)
        self.assertIsNotNone(boolean_log, "Should log boolean field update")
        self.assertIn(self.user.email, boolean_log)
        self.assertIn(Task.EMAIL_VERIFICATION, boolean_log)


class TaskServiceLegacyCompatibilityTest(TestCase):
    """Test TaskService legacy compatibility methods."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")
        # Clear system tasks created by signals
        Task.system_tasks.for_user(self.user).delete()
        TaskService.initialize_system_tasks(self.user)

    @patch("tasks.services.logger")
    def test_create_verification_tasks_redirects_to_initialize(self, mock_logger):
        """Test that create_verification_tasks redirects to initialize_system_tasks."""
        # Call legacy method
        result = TaskService.create_verification_tasks(self.user, "test@example.com", "+1234567890")

        # Should log deprecation warning
        mock_logger.warning.assert_called_once()
        warning_message = mock_logger.warning.call_args[0][0]
        self.assertIn("create_verification_tasks is deprecated", warning_message)

        # Should return empty list since tasks already exist
        self.assertEqual(result, [])

    @patch("tasks.services.logger")
    def test_complete_email_verification_task_redirects(self, mock_logger):
        """Test that complete_email_verification_task redirects properly."""
        result = TaskService.complete_email_verification_task(self.user)

        # Should log deprecation warning
        mock_logger.warning.assert_called_once()
        warning_message = mock_logger.warning.call_args[0][0]
        self.assertIn("complete_email_verification_task is deprecated", warning_message)

        # Should return True for successful completion
        self.assertTrue(result)

        # Task should be completed
        task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(task.status, "completed")

    @patch("tasks.services.logger")
    def test_complete_phone_verification_task_redirects(self, mock_logger):
        """Test that complete_phone_verification_task redirects properly."""
        result = TaskService.complete_phone_verification_task(self.user)

        # Should log deprecation warning
        mock_logger.warning.assert_called_once()
        warning_message = mock_logger.warning.call_args[0][0]
        self.assertIn("complete_phone_verification_task is deprecated", warning_message)

        # Should return True for successful completion
        self.assertTrue(result)

        # Task should be completed
        task = Task.system_tasks.by_system_code(self.user, Task.PHONE_VERIFICATION).first()
        self.assertEqual(task.status, "completed")

    @patch("tasks.services.logger")
    def test_get_verification_tasks_returns_legacy_format(self, mock_logger):
        """Test that get_verification_tasks returns legacy format."""
        # Complete email verification
        TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)

        result = TaskService.get_verification_tasks(self.user)

        # Should log deprecation warning
        mock_logger.warning.assert_called_once()
        warning_message = mock_logger.warning.call_args[0][0]
        self.assertIn("get_verification_tasks is deprecated", warning_message)

        # Should return legacy format
        expected = {
            "email_verification": {
                "exists": True,
                "status": "completed",
                "is_overdue": False,
                "completed": True,
            },
            "phone_verification": {
                "exists": True,
                "status": "pending",
                "is_overdue": False,
                "completed": False,
            },
        }

        self.assertEqual(result, expected)

    def test_legacy_methods_handle_missing_tasks(self):
        """Test that legacy methods handle missing tasks gracefully."""
        new_user = User.objects.create_user(email="new@example.com", name="New User")

        # Test completion methods return False when no task exists
        email_result = TaskService.complete_email_verification_task(new_user)
        phone_result = TaskService.complete_phone_verification_task(new_user)

        self.assertFalse(email_result)
        self.assertFalse(phone_result)

        # Test get_verification_tasks returns appropriate legacy format
        result = TaskService.get_verification_tasks(new_user)

        expected = {
            "email_verification": {
                "exists": True,
                "status": "pending",
                "is_overdue": False,
                "completed": False,
            },
            "phone_verification": {
                "exists": True,
                "status": "pending",
                "is_overdue": False,
                "completed": False,
            },
        }

        self.assertEqual(result, expected)


class TaskServiceIntegrationTest(TestCase):
    """Test TaskService integration scenarios."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(email="user1@example.com", name="User One")
        self.user2 = User.objects.create_user(email="user2@example.com", name="User Two")

    def test_full_verification_workflow(self):
        """Test complete verification workflow for a user."""
        # Initialize system tasks
        created_tasks = TaskService.initialize_system_tasks(self.user1)
        self.assertEqual(len(created_tasks), 3)

        # Check initial status
        status = TaskService.get_verification_status(self.user1)
        self.assertFalse(status["email_verified"])
        self.assertFalse(status["phone_verified"])

        # Complete email verification
        email_task = TaskService.complete_system_task(self.user1, Task.EMAIL_VERIFICATION)
        self.assertIsNotNone(email_task)

        # Check status after email completion
        status = TaskService.get_verification_status(self.user1)
        self.assertTrue(status["email_verified"])
        self.assertFalse(status["phone_verified"])

        # Complete phone verification
        phone_task = TaskService.complete_system_task(self.user1, Task.PHONE_VERIFICATION)
        self.assertIsNotNone(phone_task)

        # Complete first student
        student_task = TaskService.complete_system_task(self.user1, Task.FIRST_STUDENT_ADDED)
        self.assertIsNotNone(student_task)

        # Check final status
        status = TaskService.get_verification_status(self.user1)
        self.assertTrue(status["email_verified"])
        self.assertTrue(status["phone_verified"])

    def test_multi_user_isolation(self):
        """Test that system tasks are properly isolated between users."""
        # Initialize tasks for both users
        TaskService.initialize_system_tasks(self.user1)
        TaskService.initialize_system_tasks(self.user2)

        # Complete email verification for user1 only
        TaskService.complete_system_task(self.user1, Task.EMAIL_VERIFICATION)

        # Check user1 status
        user1_status = TaskService.get_verification_status(self.user1)
        self.assertTrue(user1_status["email_verified"])

        # Check user2 status (should be unaffected)
        user2_status = TaskService.get_verification_status(self.user2)
        self.assertFalse(user2_status["email_verified"])

        # Verify user2's task is still pending
        user2_email_task = Task.system_tasks.by_system_code(self.user2, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(user2_email_task.status, "pending")

    def test_error_handling_and_recovery(self):
        """Test service behavior with various error conditions."""
        # Test with user that has no tasks
        status = TaskService.get_verification_status(self.user1)
        expected = {
            "email_verified": False,
            "phone_verified": False,
            "first_student_added": False,
        }
        self.assertEqual(status, expected)

        # Test completion with no tasks
        result = TaskService.complete_system_task(self.user1, Task.EMAIL_VERIFICATION)
        self.assertIsNone(result)

        # Initialize tasks and test again
        TaskService.initialize_system_tasks(self.user1)
        result = TaskService.complete_system_task(self.user1, Task.EMAIL_VERIFICATION)
        self.assertIsNotNone(result)

    @override_settings(
        LOGGING={
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "null": {
                    "class": "logging.NullHandler",
                },
            },
            "root": {
                "handlers": ["null"],
            },
        }
    )
    def test_service_with_disabled_logging(self):
        """Test that service works correctly even when logging is disabled."""
        # Should work normally even without logging
        created_tasks = TaskService.initialize_system_tasks(self.user1)
        self.assertEqual(len(created_tasks), 3)

        result = TaskService.complete_system_task(self.user1, Task.EMAIL_VERIFICATION)
        self.assertIsNotNone(result)

        status = TaskService.get_verification_status(self.user1)
        self.assertTrue(status["email_verified"])
