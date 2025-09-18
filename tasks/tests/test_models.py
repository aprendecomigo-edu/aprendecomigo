"""
Tests for Task model functionality.

This module tests the unified task system model including:
- Task model fields and validation
- System task constants and unique constraints
- Task completion logic and timestamps
- Custom properties and methods
- Database constraints and indexes
"""

from datetime import UTC, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from django.test.utils import override_settings
from django.utils import timezone

from accounts.signals.verification_task_signals import create_system_tasks_for_new_user
from tasks.models import Task, TaskComment

User = get_user_model()


class TaskModelConstantsTest(TestCase):
    """Test Task model constants and choices."""

    def test_system_task_constants_defined(self):
        """Test that system task constants are properly defined."""
        self.assertEqual(Task.EMAIL_VERIFICATION, "EMAIL_VERIFICATION")
        self.assertEqual(Task.PHONE_VERIFICATION, "PHONE_VERIFICATION")
        self.assertEqual(Task.FIRST_STUDENT_ADDED, "FIRST_STUDENT_ADDED")

    def test_system_task_choices_include_constants(self):
        """Test that system task choices include all constants."""
        system_codes = [choice[0] for choice in Task.SYSTEM_TASK_CHOICES]

        self.assertIn(Task.EMAIL_VERIFICATION, system_codes)
        self.assertIn(Task.PHONE_VERIFICATION, system_codes)
        self.assertIn(Task.FIRST_STUDENT_ADDED, system_codes)

    def test_priority_choices_defined(self):
        """Test that priority choices are properly defined."""
        priorities = [choice[0] for choice in Task.PRIORITY_CHOICES]
        self.assertIn("low", priorities)
        self.assertIn("medium", priorities)
        self.assertIn("high", priorities)

    def test_status_choices_defined(self):
        """Test that status choices are properly defined."""
        statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        self.assertIn("pending", statuses)
        self.assertIn("in_progress", statuses)
        self.assertIn("completed", statuses)

    def test_task_type_choices_defined(self):
        """Test that task type choices are properly defined."""
        task_types = [choice[0] for choice in Task.TASK_TYPE_CHOICES]
        self.assertIn("onboarding", task_types)
        self.assertIn("assignment", task_types)
        self.assertIn("personal", task_types)
        self.assertIn("system", task_types)


class TaskModelCreationTest(TestCase):
    """Test Task model creation and field validation."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")

    def test_task_creation_with_minimal_data(self):
        """Test creating a task with minimal required fields."""
        task = Task.objects.create(title="Test Task", user=self.user)

        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.status, "pending")  # Default
        self.assertEqual(task.priority, "medium")  # Default
        self.assertEqual(task.task_type, "personal")  # Default
        self.assertFalse(task.is_system_generated)
        self.assertFalse(task.is_urgent)
        self.assertIsNone(task.system_code)
        self.assertIsNone(task.completed_at)

    def test_system_task_creation(self):
        """Test creating a system task with system_code."""
        # Delete existing system tasks created by signals
        Task.system_tasks.for_user(self.user).delete()

        task = Task.objects.create(
            title="Email Verification",
            user=self.user,
            task_type="system",
            system_code=Task.EMAIL_VERIFICATION,
            is_system_generated=True,
            priority="high",
        )

        self.assertEqual(task.task_type, "system")
        self.assertEqual(task.system_code, Task.EMAIL_VERIFICATION)
        self.assertTrue(task.is_system_generated)
        self.assertEqual(task.priority, "high")

    def test_task_creation_with_all_fields(self):
        """Test creating a task with all optional fields."""
        due_date = timezone.now() + timedelta(days=7)
        task = Task.objects.create(
            title="Complete Task",
            description="Detailed description",
            user=self.user,
            status="in_progress",
            priority="high",
            task_type="assignment",
            due_date=due_date,
            is_urgent=True,
        )

        self.assertEqual(task.description, "Detailed description")
        self.assertEqual(task.status, "in_progress")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.task_type, "assignment")
        self.assertEqual(task.due_date, due_date)
        self.assertTrue(task.is_urgent)

    def test_task_str_representation(self):
        """Test string representation of tasks."""
        task = Task.objects.create(title="Test Task", user=self.user)

        expected_str = f"Test Task - {self.user.email}"
        self.assertEqual(str(task), expected_str)


class TaskModelUniqueConstraintTest(TestCase):
    """Test unique constraints on Task model."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(email="user1@example.com", name="User One")
        self.user2 = User.objects.create_user(email="user2@example.com", name="User Two")

    def test_unique_system_task_per_user(self):
        """Test that users cannot have duplicate system tasks."""
        # Clear existing system tasks created by signals
        Task.system_tasks.for_user(self.user1).delete()

        # Create first system task
        Task.objects.create(
            title="Email Verification",
            user=self.user1,
            task_type="system",
            system_code=Task.EMAIL_VERIFICATION,
            is_system_generated=True,
        )

        # Attempt to create duplicate should fail
        with self.assertRaises(IntegrityError):
            Task.objects.create(
                title="Email Verification Duplicate",
                user=self.user1,
                task_type="system",
                system_code=Task.EMAIL_VERIFICATION,
                is_system_generated=True,
            )

    def test_different_users_can_have_same_system_task(self):
        """Test that different users can have the same system task type."""
        # Clear existing system tasks created by signals for both users
        Task.system_tasks.for_user(self.user1).delete()
        Task.system_tasks.for_user(self.user2).delete()

        # Both users can have EMAIL_VERIFICATION tasks
        task1 = Task.objects.create(
            title="Email Verification",
            user=self.user1,
            task_type="system",
            system_code=Task.EMAIL_VERIFICATION,
            is_system_generated=True,
        )

        task2 = Task.objects.create(
            title="Email Verification",
            user=self.user2,
            task_type="system",
            system_code=Task.EMAIL_VERIFICATION,
            is_system_generated=True,
        )

        self.assertNotEqual(task1, task2)
        self.assertEqual(task1.system_code, task2.system_code)

    def test_non_system_tasks_not_affected_by_constraint(self):
        """Test that non-system tasks are not affected by unique constraint."""
        # Create multiple personal tasks with same title - should be allowed
        Task.objects.create(title="Personal Task", user=self.user1, task_type="personal")

        Task.objects.create(title="Personal Task", user=self.user1, task_type="personal")

        # Should have 2 personal tasks with same title
        personal_tasks = Task.objects.filter(user=self.user1, task_type="personal", title="Personal Task")
        self.assertEqual(personal_tasks.count(), 2)

    def test_system_tasks_without_system_code_not_constrained(self):
        """Test that system tasks without system_code are not constrained."""
        # Create system tasks without system_code - should be allowed
        Task.objects.create(title="System Task", user=self.user1, task_type="system", is_system_generated=True)

        Task.objects.create(title="System Task", user=self.user1, task_type="system", is_system_generated=True)

        # Should have 2 system tasks without constraint violation
        system_tasks = Task.objects.filter(user=self.user1, task_type="system", system_code__isnull=True)
        self.assertEqual(system_tasks.count(), 2)


class TaskModelCompletionTest(TestCase):
    """Test Task completion logic and timestamps."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")

    @patch("django.utils.timezone.now")
    def test_completion_sets_completed_at_timestamp(self, mock_now):
        """Test that completing a task sets completed_at timestamp."""
        from datetime import timezone as dt_timezone

        mock_time = timezone.datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        mock_now.return_value = mock_time

        task = Task.objects.create(title="Test Task", user=self.user, status="pending")

        # Complete the task
        task.status = "completed"
        task.save()

        task.refresh_from_db()
        self.assertEqual(task.completed_at, mock_time)
        self.assertEqual(task.status, "completed")

    def test_uncompleting_task_clears_completed_at(self):
        """Test that uncompleting a task clears completed_at timestamp."""
        # Create completed task
        task = Task.objects.create(title="Test Task", user=self.user, status="completed")

        # Should have completed_at set
        self.assertIsNotNone(task.completed_at)

        # Uncomplete the task
        task.status = "pending"
        task.save()

        task.refresh_from_db()
        self.assertIsNone(task.completed_at)

    def test_changing_to_in_progress_clears_completed_at(self):
        """Test that changing to in_progress clears completed_at timestamp."""
        # Create completed task
        task = Task.objects.create(title="Test Task", user=self.user, status="completed")

        # Change to in_progress
        task.status = "in_progress"
        task.save()

        task.refresh_from_db()
        self.assertIsNone(task.completed_at)

    def test_multiple_completion_updates_timestamp(self):
        """Test that multiple completions update the timestamp."""
        task = Task.objects.create(title="Test Task", user=self.user, status="pending")

        # Complete first time
        task.status = "completed"
        task.save()
        first_completion = task.completed_at

        # Uncomplete
        task.status = "pending"
        task.save()

        # Complete second time
        task.status = "completed"
        task.save()
        second_completion = task.completed_at

        self.assertGreater(second_completion, first_completion)

    def test_completed_task_creation_sets_timestamp(self):
        """Test that creating a task as completed sets timestamp."""
        task = Task.objects.create(title="Test Task", user=self.user, status="completed")

        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.status, "completed")


class TaskModelPropertiesTest(TestCase):
    """Test Task model computed properties."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")

    def test_is_overdue_with_past_due_date(self):
        """Test that tasks with past due dates are overdue."""
        past_date = timezone.now() - timedelta(days=1)
        task = Task.objects.create(title="Overdue Task", user=self.user, due_date=past_date, status="pending")

        self.assertTrue(task.is_overdue)

    def test_is_overdue_with_future_due_date(self):
        """Test that tasks with future due dates are not overdue."""
        future_date = timezone.now() + timedelta(days=1)
        task = Task.objects.create(title="Future Task", user=self.user, due_date=future_date, status="pending")

        self.assertFalse(task.is_overdue)

    def test_is_overdue_without_due_date(self):
        """Test that tasks without due dates are not overdue."""
        task = Task.objects.create(title="No Due Date Task", user=self.user, status="pending")

        self.assertFalse(task.is_overdue)

    def test_is_overdue_completed_task_not_overdue(self):
        """Test that completed tasks are never overdue."""
        past_date = timezone.now() - timedelta(days=1)
        task = Task.objects.create(
            title="Completed Overdue Task", user=self.user, due_date=past_date, status="completed"
        )

        self.assertFalse(task.is_overdue)

    def test_days_until_due_with_future_date(self):
        """Test days_until_due calculation for future dates."""
        future_date = timezone.now() + timedelta(days=5, hours=12)
        task = Task.objects.create(title="Future Task", user=self.user, due_date=future_date)

        # Should return 5 days (ignores hours)
        self.assertEqual(task.days_until_due, 5)

    def test_days_until_due_with_past_date(self):
        """Test days_until_due calculation for past dates."""
        past_date = timezone.now() - timedelta(days=3, hours=1)  # Ensure it's definitely in the past
        task = Task.objects.create(title="Past Task", user=self.user, due_date=past_date)

        # Should return negative value (allow for -3 or -4 depending on timing)
        self.assertIn(task.days_until_due, [-3, -4])

    def test_days_until_due_without_due_date(self):
        """Test days_until_due returns None when no due date."""
        task = Task.objects.create(title="No Due Date Task", user=self.user)

        self.assertIsNone(task.days_until_due)


class TaskModelOnboardingTest(TestCase):
    """Test Task model onboarding functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")

    def test_create_onboarding_tasks_creates_default_tasks(self):
        """Test that create_onboarding_tasks creates expected tasks."""
        tasks = Task.create_onboarding_tasks(self.user)

        self.assertEqual(len(tasks), 2)

        # Check tasks were created
        onboarding_tasks = Task.objects.filter(user=self.user, task_type="onboarding")
        self.assertEqual(onboarding_tasks.count(), 2)

    def test_create_onboarding_tasks_properties(self):
        """Test that onboarding tasks have correct properties."""
        tasks = Task.create_onboarding_tasks(self.user)

        for task in tasks:
            self.assertEqual(task.user, self.user)
            self.assertEqual(task.task_type, "onboarding")
            self.assertTrue(task.is_system_generated)
            self.assertEqual(task.status, "pending")
            self.assertIn(task.priority, ["high", "medium"])

    def test_create_onboarding_tasks_specific_content(self):
        """Test that onboarding tasks have expected titles."""
        Task.create_onboarding_tasks(self.user)

        # Check specific task titles
        profile_task = Task.objects.filter(user=self.user, title__icontains="Complete Your Profile").first()
        self.assertIsNotNone(profile_task)

        dashboard_task = Task.objects.filter(user=self.user, title__icontains="Explore the Dashboard").first()
        self.assertIsNotNone(dashboard_task)


class TaskModelManagersTest(TestCase):
    """Test that Task model has correct managers attached."""

    def test_default_manager_exists(self):
        """Test that default objects manager exists."""
        self.assertTrue(hasattr(Task, "objects"))

    def test_system_tasks_manager_exists(self):
        """Test that system_tasks manager exists."""
        self.assertTrue(hasattr(Task, "system_tasks"))

    def test_user_tasks_manager_exists(self):
        """Test that user_tasks manager exists."""
        self.assertTrue(hasattr(Task, "user_tasks"))

    def test_onboarding_tasks_manager_exists(self):
        """Test that onboarding_tasks manager exists."""
        self.assertTrue(hasattr(Task, "onboarding_tasks"))


class TaskCommentModelTest(TestCase):
    """Test TaskComment model functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")
        self.task = Task.objects.create(title="Test Task", user=self.user)

    def test_task_comment_creation(self):
        """Test creating a task comment."""
        comment = TaskComment.objects.create(task=self.task, user=self.user, comment="This is a test comment")

        self.assertEqual(comment.task, self.task)
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.comment, "This is a test comment")
        self.assertIsNotNone(comment.created_at)

    def test_task_comment_str_representation(self):
        """Test string representation of task comments."""
        comment = TaskComment.objects.create(task=self.task, user=self.user, comment="Test comment")

        expected_str = f"Comment on {self.task.title} by {self.user.email}"
        self.assertEqual(str(comment), expected_str)

    def test_task_comment_relationship(self):
        """Test that comments are properly related to tasks."""
        comment1 = TaskComment.objects.create(task=self.task, user=self.user, comment="First comment")
        comment2 = TaskComment.objects.create(task=self.task, user=self.user, comment="Second comment")

        # Task should have related comments
        task_comments = self.task.comments.all()
        self.assertEqual(task_comments.count(), 2)
        self.assertIn(comment1, task_comments)
        self.assertIn(comment2, task_comments)

    def test_task_comment_deletion_cascade(self):
        """Test that deleting a task deletes related comments."""
        TaskComment.objects.create(task=self.task, user=self.user, comment="Test comment")

        # Should have 1 comment
        self.assertEqual(TaskComment.objects.count(), 1)

        # Delete task
        self.task.delete()

        # Comment should be deleted too
        self.assertEqual(TaskComment.objects.count(), 0)


class TaskModelIndexesTest(TestCase):
    """Test that database indexes are properly configured."""

    def test_model_meta_indexes_defined(self):
        """Test that model meta defines expected indexes."""
        indexes = Task._meta.indexes
        index_fields = [index.fields for index in indexes]

        # Check that expected index combinations exist
        expected_indexes = [
            ["user", "status"],
            ["user", "due_date"],
            ["priority", "status"],
            ["user", "system_code"],
            ["system_code", "task_type"],
        ]

        for expected in expected_indexes:
            self.assertIn(expected, index_fields)

    def test_model_meta_constraints_defined(self):
        """Test that model meta defines unique constraints."""
        constraints = Task._meta.constraints
        self.assertTrue(len(constraints) > 0)

        # Check for unique constraint on user+system_code
        unique_constraint = next((c for c in constraints if hasattr(c, "fields") and "user" in c.fields), None)
        self.assertIsNotNone(unique_constraint)


class TaskModelOrderingTest(TestCase):
    """Test Task model default ordering."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")

    def test_default_ordering_by_priority_and_dates(self):
        """Test that tasks are ordered by priority, due_date, and created_at."""
        # Clear existing system tasks to test ordering cleanly
        Task.objects.filter(user=self.user).delete()

        # Create tasks with different priorities
        low_task = Task.objects.create(title="Low Priority", user=self.user, priority="low")
        high_task = Task.objects.create(title="High Priority", user=self.user, priority="high")
        medium_task = Task.objects.create(title="Medium Priority", user=self.user, priority="medium")

        # Get ordered tasks for this user only
        ordered_tasks = list(Task.objects.filter(user=self.user))

        # Ordering is ["-priority", "due_date", "-created_at"]
        # String-based priority ordering is alphabetical (reverse): "medium", "low", "high"
        expected_order = [medium_task, low_task, high_task]
        self.assertEqual(ordered_tasks, expected_order)
