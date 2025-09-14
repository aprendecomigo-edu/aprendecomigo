"""
Tests for verification task signal handlers.

This module tests the Django signals that automatically handle
system verification task completion when certain conditions are met:
- User creation triggers system task creation
- Email verification completion
- Phone verification completion
- First student creation completion
"""

from unittest.mock import MagicMock, patch

from django.db.models.signals import post_save
from django.test import TestCase

from accounts.models import CustomUser as User, EducationalSystem, StudentProfile
from accounts.signals.verification_task_signals import create_system_tasks_for_new_user
from tasks.models import Task
from tasks.services import TaskService


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
        User.objects.create_user(email="test@example.com", name="Test User")

        # Verify TaskService was called
        mock_initialize.assert_called_once()

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


class EmailVerificationSignalTest(TestCase):
    """Test signals for email verification completion."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")

    def test_email_verification_signal_triggered(self):
        """Test that setting email_verified=True triggers task completion."""
        # Get the email verification task
        email_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertIsNotNone(email_task)
        self.assertEqual(email_task.status, "pending")

        # Trigger email verification (should trigger signal)
        self.user.email_verified = True
        self.user.save()

        # Task should now be completed
        email_task.refresh_from_db()
        self.assertEqual(email_task.status, "completed")
        self.assertIsNotNone(email_task.completed_at)

    def test_email_verification_false_no_task_completion(self):
        """Test that setting email_verified=False doesn't complete task."""
        # Ensure task starts as pending
        email_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(email_task.status, "pending")

        # Set email_verified to False (should not trigger completion)
        self.user.email_verified = False
        self.user.save()

        # Task should still be pending
        email_task.refresh_from_db()
        self.assertEqual(email_task.status, "pending")

    def test_email_already_verified_no_change(self):
        """Test that updating already verified email doesn't change anything."""
        # Complete the task first
        self.user.email_verified = True
        self.user.save()

        email_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        original_completion_time = email_task.completed_at

        # Update email_verified again (should not change completion time)
        self.user.email_verified = True
        self.user.save()

        # Completion time should remain unchanged
        email_task.refresh_from_db()
        self.assertEqual(email_task.completed_at, original_completion_time)


class PhoneVerificationSignalTest(TestCase):
    """Test signals for phone verification completion."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")

    def test_phone_verification_signal_triggered(self):
        """Test that setting phone_verified=True triggers task completion."""
        # Get the phone verification task
        phone_task = Task.system_tasks.by_system_code(self.user, Task.PHONE_VERIFICATION).first()
        self.assertIsNotNone(phone_task)
        self.assertEqual(phone_task.status, "pending")

        # Trigger phone verification (should trigger signal)
        self.user.phone_verified = True
        self.user.save()

        # Task should now be completed
        phone_task.refresh_from_db()
        self.assertEqual(phone_task.status, "completed")
        self.assertIsNotNone(phone_task.completed_at)

    def test_phone_verification_false_no_task_completion(self):
        """Test that setting phone_verified=False doesn't complete task."""
        # Ensure task starts as pending
        phone_task = Task.system_tasks.by_system_code(self.user, Task.PHONE_VERIFICATION).first()
        self.assertEqual(phone_task.status, "pending")

        # Set phone_verified to False (should not trigger completion)
        self.user.phone_verified = False
        self.user.save()

        # Task should still be pending
        phone_task.refresh_from_db()
        self.assertEqual(phone_task.status, "pending")

    def test_phone_already_verified_no_change(self):
        """Test that updating already verified phone doesn't change anything."""
        # Complete the task first
        self.user.phone_verified = True
        self.user.save()

        phone_task = Task.system_tasks.by_system_code(self.user, Task.PHONE_VERIFICATION).first()
        original_completion_time = phone_task.completed_at

        # Update phone_verified again (should not change completion time)
        self.user.phone_verified = True
        self.user.save()

        # Completion time should remain unchanged
        phone_task.refresh_from_db()
        self.assertEqual(phone_task.completed_at, original_completion_time)


class StudentProfileSignalTest(TestCase):
    """Test signals for student profile creation (fallback mode only)."""

    def setUp(self):
        """Set up test data."""
        self.educational_system = EducationalSystem.objects.create(
            name="Test System", code="test", description="Test educational system"
        )
        # Create multiple users to test fallback behavior
        self.user1 = User.objects.create_user(email="user1@example.com", name="User 1")
        self.user2 = User.objects.create_user(email="user2@example.com", name="User 2")
        self.user3 = User.objects.create_user(email="user3@example.com", name="User 3")

    def test_first_student_creation_completes_all_user_tasks(self):
        """Test that creating first student completes task for ALL users (fallback mode)."""
        # Verify all users have pending student tasks
        for user in [self.user1, self.user2, self.user3]:
            student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertEqual(student_task.status, "pending")

        # Create student user and profile (triggers signal)
        student_user = User.objects.create_user(email="student@example.com", name="Student User")
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # All users should now have completed tasks (fallback mode)
        for user in [self.user1, self.user2, self.user3, student_user]:
            student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertEqual(student_task.status, "completed")
            self.assertIsNotNone(student_task.completed_at)

    def test_student_without_user_account(self):
        """Test creating student profile without user account (fallback mode)."""
        # Create student profile without user account
        StudentProfile.objects.create(
            user=None,  # No user account
            educational_system=self.educational_system,
            birth_date="2010-01-01",
            school_year="5",
        )

        # All existing users should have completed tasks (fallback mode)
        for user in [self.user1, self.user2, self.user3]:
            student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertEqual(student_task.status, "completed")

    @patch("accounts.signals.verification_task_signals.TaskService.complete_system_task")
    @patch("accounts.signals.verification_task_signals.logger")
    def test_signal_logs_and_calls_service(self, mock_logger, mock_complete):
        """Test that signal properly logs and calls TaskService."""
        mock_complete.return_value = MagicMock()

        # Create student user
        student_user = User.objects.create_user(email="student@example.com", name="Student User")

        # Create student profile (triggers signal)
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify logging occurred (3 info logs: user creation, student profile creation, completion)
        self.assertEqual(mock_logger.info.call_count, 3)
        self.assertEqual(mock_logger.warning.call_count, 1)  # Warning about no guardian relationship

        # Check user creation log (from creating student_user)
        user_creation_log = mock_logger.info.call_args_list[0][0][0]
        self.assertIn("Creating system tasks for new user", user_creation_log)

        # Check student profile creation log
        creation_log = mock_logger.info.call_args_list[1][0][0]
        self.assertIn("Student profile created", creation_log)

        # Check warning log
        warning_log = mock_logger.warning.call_args_list[0][0][0]
        self.assertIn("No guardian relationship found", warning_log)
        self.assertIn("Falling back", warning_log)

        # Check completion log
        completion_log = mock_logger.info.call_args_list[2][0][0]
        self.assertIn("Completed FIRST_STUDENT_ADDED task for all users (fallback mode)", completion_log)

        # Verify TaskService was called for all users (4 users total)
        self.assertEqual(mock_complete.call_count, 4)


class SignalErrorHandlingTest(TestCase):
    """Test error handling in signal handlers."""

    @patch("accounts.signals.verification_task_signals.TaskService.initialize_system_tasks")
    def test_signal_handles_database_errors_gracefully(self, mock_init):
        """Test that signals handle database errors without breaking user creation."""
        # Make TaskService raise an exception
        mock_init.side_effect = Exception("Database error")

        # User creation should still succeed even if signal fails
        user = User.objects.create_user(email="errortest@example.com", name="Error Test User")

        # User should exist
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "errortest@example.com")


class SignalDisconnectionTest(TestCase):
    """Test signal disconnection and reconnection."""

    def test_signals_can_be_disconnected_and_reconnected(self):
        """Test that signals can be temporarily disconnected."""
        # Disconnect the signal
        post_save.disconnect(create_system_tasks_for_new_user, sender=User)

        try:
            # Create user with signal disconnected
            user = User.objects.create_user(email="disconnected@example.com", name="Disconnected User")

            # No tasks should be created
            system_tasks = Task.system_tasks.for_user(user)
            self.assertEqual(system_tasks.count(), 0)

        finally:
            # Reconnect the signal
            post_save.connect(create_system_tasks_for_new_user, sender=User)

        # Create another user with signal reconnected
        user2 = User.objects.create_user(email="reconnected@example.com", name="Reconnected User")

        # Tasks should be created
        system_tasks = Task.system_tasks.for_user(user2)
        self.assertEqual(system_tasks.count(), 3)
