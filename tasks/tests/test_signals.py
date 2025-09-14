"""
Tests for verification task signal handlers.

This module tests the Django signals that automatically handle
system verification task completion when certain conditions are met:
- User creation triggers system task creation
- Email verification completion
- Phone verification completion
- First student creation completion
"""

import logging
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings

from accounts.models import EducationalSystem, StudentProfile
from accounts.signals.verification_task_signals import (
    complete_email_verification_task,
    complete_first_student_task,
    complete_phone_verification_task,
    create_system_tasks_for_new_user,
)
from tasks.models import Task
from tasks.services import TaskService

User = get_user_model()


class UserCreationSignalTest(TestCase):
    """Test signals triggered when users are created."""

    def test_create_system_tasks_for_new_user_signal_triggered(self):
        """Test that creating a new user triggers system task creation."""
        # Create user (should trigger signal)
        user = User.objects.create_user(email="newuser@example.com", name="New User")

        # Verify system tasks were created
        system_tasks = Task.system_tasks.for_user(user)
        self.assertEqual(system_tasks.count(), 3)

        # Verify all expected system codes exist
        system_codes = {task.system_code for task in system_tasks}
        expected_codes = {Task.EMAIL_VERIFICATION, Task.PHONE_VERIFICATION, Task.FIRST_STUDENT_ADDED}
        self.assertEqual(system_codes, expected_codes)

    def test_existing_user_update_no_new_tasks_created(self):
        """Test that updating an existing user doesn't create new tasks."""
        # Create user (triggers signal)
        user = User.objects.create_user(email="existing@example.com", name="Existing User")

        # Verify initial task count
        initial_count = Task.system_tasks.for_user(user).count()
        self.assertEqual(initial_count, 3)

        # Update user (should not create new tasks)
        user.name = "Updated Name"
        user.save()

        # Task count should remain the same
        final_count = Task.system_tasks.for_user(user).count()
        self.assertEqual(final_count, initial_count)

    @patch("accounts.signals.verification_task_signals.TaskService.initialize_system_tasks")
    def test_signal_calls_task_service(self, mock_initialize):
        """Test that the signal properly calls TaskService."""
        mock_initialize.return_value = []

        # Create user
        user = User.objects.create_user(email="test@example.com", name="Test User")

        # Verify TaskService was called
        mock_initialize.assert_called_once_with(user)

    @patch("accounts.signals.verification_task_signals.logger")
    def test_signal_logs_user_creation(self, mock_logger):
        """Test that user creation is logged."""
        user = User.objects.create_user(email="logged@example.com", name="Logged User")

        # Verify logging occurred
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn("Creating system tasks for new user", log_message)
        self.assertIn(user.email, log_message)

    def test_signal_handles_multiple_user_creation(self):
        """Test signal works correctly with multiple user creations."""
        users = []
        for i in range(3):
            user = User.objects.create_user(email=f"user{i}@example.com", name=f"User {i}")
            users.append(user)

        # Each user should have their own system tasks
        for user in users:
            system_tasks = Task.system_tasks.for_user(user)
            self.assertEqual(system_tasks.count(), 3)

        # Total system tasks should be 3 per user
        total_system_tasks = Task.system_tasks.all().count()
        self.assertEqual(total_system_tasks, 9)


class EmailVerificationSignalTest(TestCase):
    """Test signals triggered when email verification is completed."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User", email_verified=False)

    def test_email_verification_signal_triggered(self):
        """Test that setting email_verified=True triggers task completion."""
        # Verify task is initially pending
        email_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(email_task.status, "pending")

        # Set email as verified (should trigger signal)
        self.user.email_verified = True
        self.user.save()

        # Verify task is now completed
        email_task.refresh_from_db()
        self.assertEqual(email_task.status, "completed")
        self.assertIsNotNone(email_task.completed_at)

    def test_email_already_verified_no_change(self):
        """Test that updating already verified email doesn't change anything."""
        # Complete email verification first
        TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)

        # Get completed task
        email_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        original_completion_time = email_task.completed_at

        # Set email as verified again (should not affect task)
        self.user.email_verified = True
        self.user.save()

        # Task completion time should remain unchanged
        email_task.refresh_from_db()
        self.assertEqual(email_task.completed_at, original_completion_time)

    def test_email_verification_false_no_task_completion(self):
        """Test that setting email_verified=False doesn't complete task."""
        # Verify task is initially pending
        email_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(email_task.status, "pending")

        # Set email_verified=False explicitly
        self.user.email_verified = False
        self.user.save()

        # Task should remain pending
        email_task.refresh_from_db()
        self.assertEqual(email_task.status, "pending")
        self.assertIsNone(email_task.completed_at)

    def test_user_without_email_task_no_error(self):
        """Test that signal handles users without email verification tasks."""
        # Create user without system tasks
        new_user = User.objects.create_user(email="notasks@example.com", name="No Tasks User", email_verified=False)

        # Delete the system tasks that were auto-created
        Task.system_tasks.for_user(new_user).delete()

        # Setting email_verified=True should not cause error
        new_user.email_verified = True
        new_user.save()  # Should not raise exception

    @patch("accounts.signals.verification_task_signals.TaskService.complete_system_task")
    def test_signal_calls_task_service(self, mock_complete):
        """Test that the signal properly calls TaskService."""
        mock_complete.return_value = MagicMock()

        # Set email as verified
        self.user.email_verified = True
        self.user.save()

        # Verify TaskService was called
        mock_complete.assert_called_once_with(self.user, Task.EMAIL_VERIFICATION)

    def test_bulk_email_verification_updates(self):
        """Test signal works with bulk updates."""
        # Create multiple users
        users = []
        for i in range(3):
            user = User.objects.create_user(email=f"bulk{i}@example.com", name=f"Bulk User {i}", email_verified=False)
            users.append(user)

        # Verify all email tasks are pending
        for user in users:
            email_task = Task.system_tasks.by_system_code(user, Task.EMAIL_VERIFICATION).first()
            self.assertEqual(email_task.status, "pending")

        # Bulk update email verification
        for user in users:
            user.email_verified = True
            user.save()

        # Verify all email tasks are completed
        for user in users:
            email_task = Task.system_tasks.by_system_code(user, Task.EMAIL_VERIFICATION).first()
            self.assertEqual(email_task.status, "completed")


class PhoneVerificationSignalTest(TestCase):
    """Test signals triggered when phone verification is completed."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com", name="Test User", phone_number="+351987654321", phone_verified=False
        )

    def test_phone_verification_signal_triggered(self):
        """Test that setting phone_verified=True triggers task completion."""
        # Verify task is initially pending
        phone_task = Task.system_tasks.by_system_code(self.user, Task.PHONE_VERIFICATION).first()
        self.assertEqual(phone_task.status, "pending")

        # Set phone as verified (should trigger signal)
        self.user.phone_verified = True
        self.user.save()

        # Verify task is now completed
        phone_task.refresh_from_db()
        self.assertEqual(phone_task.status, "completed")
        self.assertIsNotNone(phone_task.completed_at)

    def test_phone_already_verified_no_change(self):
        """Test that updating already verified phone doesn't change anything."""
        # Complete phone verification first
        TaskService.complete_system_task(self.user, Task.PHONE_VERIFICATION)

        # Get completed task
        phone_task = Task.system_tasks.by_system_code(self.user, Task.PHONE_VERIFICATION).first()
        original_completion_time = phone_task.completed_at

        # Set phone as verified again (should not affect task)
        self.user.phone_verified = True
        self.user.save()

        # Task completion time should remain unchanged
        phone_task.refresh_from_db()
        self.assertEqual(phone_task.completed_at, original_completion_time)

    def test_phone_verification_false_no_task_completion(self):
        """Test that setting phone_verified=False doesn't complete task."""
        # Verify task is initially pending
        phone_task = Task.system_tasks.by_system_code(self.user, Task.PHONE_VERIFICATION).first()
        self.assertEqual(phone_task.status, "pending")

        # Set phone_verified=False explicitly
        self.user.phone_verified = False
        self.user.save()

        # Task should remain pending
        phone_task.refresh_from_db()
        self.assertEqual(phone_task.status, "pending")
        self.assertIsNone(phone_task.completed_at)

    @patch("accounts.signals.verification_task_signals.TaskService.complete_system_task")
    def test_signal_calls_task_service(self, mock_complete):
        """Test that the signal properly calls TaskService."""
        mock_complete.return_value = MagicMock()

        # Set phone as verified
        self.user.phone_verified = True
        self.user.save()

        # Verify TaskService was called
        mock_complete.assert_called_once_with(self.user, Task.PHONE_VERIFICATION)


class StudentProfileSignalTest(TestCase):
    """Test signals triggered when student profiles are created."""

    def setUp(self):
        """Set up test data."""
        # Create educational system (required for StudentProfile)
        self.educational_system = EducationalSystem.objects.create(
            name="Test System", code="pt", description="Test educational system"
        )

        # Create multiple users
        self.user1 = User.objects.create_user(email="user1@example.com", name="User One")
        self.user2 = User.objects.create_user(email="user2@example.com", name="User Two")
        self.user3 = User.objects.create_user(email="user3@example.com", name="User Three")

        # Verify all users have pending first student tasks
        for user in [self.user1, self.user2, self.user3]:
            student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertEqual(student_task.status, "pending")

    def test_first_student_creation_completes_all_user_tasks(self):
        """Test that creating first student completes task for ALL users."""
        # Create a student user
        student_user = User.objects.create_user(email="student@example.com", name="Student User")

        # Create StudentProfile (should trigger signal)
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify ALL users' first student tasks are completed
        for user in [self.user1, self.user2, self.user3, student_user]:
            student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertEqual(student_task.status, "completed")
            self.assertIsNotNone(student_task.completed_at)

    def test_second_student_creation_no_change(self):
        """Test that creating additional students doesn't change task status."""
        # Create first student
        student1_user = User.objects.create_user(email="student1@example.com", name="Student One")
        student_profile1 = StudentProfile.objects.create(
            user=student1_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Get completion time after first student
        user1_task = Task.system_tasks.by_system_code(self.user1, Task.FIRST_STUDENT_ADDED).first()
        first_completion_time = user1_task.completed_at

        # Create second student
        student2_user = User.objects.create_user(email="student2@example.com", name="Student Two")
        StudentProfile.objects.create(
            user=student2_user, educational_system=self.educational_system, birth_date="2011-01-01", school_year="4"
        )

        # Task completion time should remain unchanged
        user1_task.refresh_from_db()
        self.assertEqual(user1_task.completed_at, first_completion_time)

    def test_student_profile_update_no_task_completion(self):
        """Test that updating student profile doesn't trigger task completion."""
        # Create student first
        student_user = User.objects.create_user(email="student@example.com", name="Student User")
        student_profile = StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Tasks should already be completed from creation
        user1_task = Task.system_tasks.by_system_code(self.user1, Task.FIRST_STUDENT_ADDED).first()
        original_completion_time = user1_task.completed_at

        # Update student profile (should not affect task)
        student_profile.school_year = "6"
        student_profile.save()

        # Task completion time should remain unchanged
        user1_task.refresh_from_db()
        self.assertEqual(user1_task.completed_at, original_completion_time)

    @patch("accounts.signals.verification_task_signals.TaskService.complete_system_task")
    @patch("accounts.signals.verification_task_signals.logger")
    def test_signal_logs_and_calls_service(self, mock_logger, mock_complete):
        """Test that signal properly logs and calls TaskService."""
        mock_complete.return_value = MagicMock()

        # Create student user
        student_user = User.objects.create_user(email="student@example.com", name="Student User")

        # Create student profile (triggers signal)
        student_profile = StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify logging occurred
        self.assertEqual(mock_logger.info.call_count, 2)  # One for creation, one for completion

        # Check creation log
        creation_log = mock_logger.info.call_args_list[0][0][0]
        self.assertIn("Student profile created", creation_log)

        # Check completion log
        completion_log = mock_logger.info.call_args_list[1][0][0]
        self.assertIn("Completed FIRST_STUDENT_ADDED task for all users", completion_log)

        # Verify TaskService was called for all users (4 users total)
        self.assertEqual(mock_complete.call_count, 4)

    def test_signal_handles_users_without_student_tasks(self):
        """Test that signal handles users without student tasks gracefully."""
        # Create user and delete their system tasks
        orphan_user = User.objects.create_user(email="orphan@example.com", name="Orphan User")
        Task.system_tasks.for_user(orphan_user).delete()

        # Create student (should not cause error)
        student_user = User.objects.create_user(email="student@example.com", name="Student User")
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Should complete without errors
        # Other users' tasks should still be completed
        for user in [self.user1, self.user2, self.user3]:
            student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertEqual(student_task.status, "completed")

    def test_student_without_user_account(self):
        """Test creating student profile without user account."""
        # Create student profile without user (user=None)
        StudentProfile.objects.create(
            user=None,  # Guardian-managed student
            educational_system=self.educational_system,
            birth_date="2012-01-01",
            school_year="3",
        )

        # Should still complete tasks for all users
        for user in [self.user1, self.user2, self.user3]:
            student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertEqual(student_task.status, "completed")


class SignalIntegrationTest(TestCase):
    """Test integration scenarios with multiple signals."""

    def setUp(self):
        """Set up test data."""
        self.educational_system = EducationalSystem.objects.create(
            name="Integration Test System", code="int", description="Integration test system"
        )

    def test_complete_user_verification_workflow(self):
        """Test complete user workflow with all signals."""
        # Create user (triggers system task creation)
        user = User.objects.create_user(
            email="complete@example.com",
            name="Complete User",
            phone_number="+351123456789",
            email_verified=False,
            phone_verified=False,
        )

        # Verify all tasks are initially pending
        status = TaskService.get_verification_status(user)
        self.assertFalse(status["email_verified"])
        self.assertFalse(status["phone_verified"])
        self.assertFalse(status["first_student_added"])

        # Complete email verification (triggers signal)
        user.email_verified = True
        user.save()

        # Check status after email verification
        status = TaskService.get_verification_status(user)
        self.assertTrue(status["email_verified"])
        self.assertFalse(status["phone_verified"])
        self.assertFalse(status["first_student_added"])

        # Complete phone verification (triggers signal)
        user.phone_verified = True
        user.save()

        # Check status after phone verification
        status = TaskService.get_verification_status(user)
        self.assertTrue(status["email_verified"])
        self.assertTrue(status["phone_verified"])
        self.assertFalse(status["first_student_added"])

        # Create student (triggers signal)
        student_user = User.objects.create_user(email="student@example.com", name="Student User")
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Check final status
        status = TaskService.get_verification_status(user)
        self.assertTrue(status["email_verified"])
        self.assertTrue(status["phone_verified"])
        self.assertTrue(status["first_student_added"])

    def test_multiple_users_independent_verification(self):
        """Test that verification signals work independently for different users."""
        # Create two users
        user1 = User.objects.create_user(
            email="user1@example.com", name="User One", email_verified=False, phone_verified=False
        )
        user2 = User.objects.create_user(
            email="user2@example.com", name="User Two", email_verified=False, phone_verified=False
        )

        # Verify user1 email only
        user1.email_verified = True
        user1.save()

        # Check that only user1's email task is completed
        user1_status = TaskService.get_verification_status(user1)
        user2_status = TaskService.get_verification_status(user2)

        self.assertTrue(user1_status["email_verified"])
        self.assertFalse(user1_status["phone_verified"])
        self.assertFalse(user1_status["first_student_added"])

        self.assertFalse(user2_status["email_verified"])
        self.assertFalse(user2_status["phone_verified"])
        self.assertFalse(user2_status["first_student_added"])

        # Verify user2 phone only
        user2.phone_verified = True
        user2.save()

        # Check that only user2's phone task is completed
        user1_status = TaskService.get_verification_status(user1)
        user2_status = TaskService.get_verification_status(user2)

        self.assertTrue(user1_status["email_verified"])
        self.assertFalse(user1_status["phone_verified"])
        self.assertFalse(user1_status["first_student_added"])

        self.assertFalse(user2_status["email_verified"])
        self.assertTrue(user2_status["phone_verified"])
        self.assertFalse(user2_status["first_student_added"])


class SignalDisconnectionTest(TestCase):
    """Test behavior when signals are disconnected."""

    def test_signals_can_be_disconnected_and_reconnected(self):
        """Test that signals can be temporarily disconnected."""
        # Disconnect the user creation signal
        post_save.disconnect(create_system_tasks_for_new_user, sender=User)

        try:
            # Create user without signal
            user = User.objects.create_user(email="nosignal@example.com", name="No Signal User")

            # No system tasks should be created
            system_tasks = Task.system_tasks.for_user(user)
            self.assertEqual(system_tasks.count(), 0)

        finally:
            # Reconnect the signal
            post_save.connect(create_system_tasks_for_new_user, sender=User)

        # Create another user with signal reconnected
        user2 = User.objects.create_user(email="withsignal@example.com", name="With Signal User")

        # System tasks should be created
        system_tasks = Task.system_tasks.for_user(user2)
        self.assertEqual(system_tasks.count(), 3)


class SignalErrorHandlingTest(TransactionTestCase):
    """Test signal error handling scenarios."""

    def test_signal_handles_database_errors_gracefully(self):
        """Test that signals handle database errors without breaking user creation."""
        # This test would require more complex database error simulation
        # For now, we test basic error resilience

        with patch("accounts.signals.verification_task_signals.TaskService.initialize_system_tasks") as mock_init:
            # Make TaskService raise an exception
            mock_init.side_effect = Exception("Database error")

            # User creation should still succeed even if signal fails
            user = User.objects.create_user(email="errortest@example.com", name="Error Test User")

            # User should exist
            self.assertIsNotNone(user)
            self.assertEqual(user.email, "errortest@example.com")

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
    def test_signals_work_without_logging(self):
        """Test that signals work even when logging is disabled."""
        # Should work normally even without logging
        user = User.objects.create_user(email="nolog@example.com", name="No Log User")

        # System tasks should still be created
        system_tasks = Task.system_tasks.for_user(user)
        self.assertEqual(system_tasks.count(), 3)
