"""
Tests for Task model custom managers.

This module tests the custom managers for the Task model:
- SystemTaskManager: Managing system-generated tasks
- UserTaskManager: Managing user-created tasks
- OnboardingTaskManager: Managing onboarding tasks
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from tasks.managers import OnboardingTaskManager, SystemTaskManager, UserTaskManager
from tasks.models import Task

User = get_user_model()


class SystemTaskManagerTest(TestCase):
    """Test SystemTaskManager functionality."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(email="user1@example.com", name="User One")
        self.user2 = User.objects.create_user(email="user2@example.com", name="User Two")

        # Clear system tasks created by signals
        Task.system_tasks.for_user(self.user1).delete()
        Task.system_tasks.for_user(self.user2).delete()

        # Create various types of tasks
        self.system_task1 = Task.objects.create(
            title="Email Verification",
            user=self.user1,
            task_type="system",
            system_code=Task.EMAIL_VERIFICATION,
            is_system_generated=True,
            status="pending",
        )

        self.system_task2 = Task.objects.create(
            title="Phone Verification",
            user=self.user1,
            task_type="system",
            system_code=Task.PHONE_VERIFICATION,
            is_system_generated=True,
            status="completed",
        )

        self.system_task_user2 = Task.objects.create(
            title="Email Verification",
            user=self.user2,
            task_type="system",
            system_code=Task.EMAIL_VERIFICATION,
            is_system_generated=True,
            status="pending",
        )

        self.personal_task = Task.objects.create(
            title="Personal Task", user=self.user1, task_type="personal", is_system_generated=False
        )

        self.onboarding_task = Task.objects.create(
            title="Complete Profile", user=self.user1, task_type="onboarding", is_system_generated=True
        )

    def test_manager_instance_type(self):
        """Test that system_tasks manager is correct type."""
        self.assertIsInstance(Task.system_tasks, SystemTaskManager)

    def test_get_queryset_filters_system_tasks_only(self):
        """Test that SystemTaskManager only returns system tasks."""
        system_tasks = Task.system_tasks.all()

        # Should return only system tasks
        self.assertEqual(system_tasks.count(), 3)

        # Verify all returned tasks are system tasks
        for task in system_tasks:
            self.assertEqual(task.task_type, "system")
            self.assertTrue(task.is_system_generated)

        # Verify specific tasks are included
        self.assertIn(self.system_task1, system_tasks)
        self.assertIn(self.system_task2, system_tasks)
        self.assertIn(self.system_task_user2, system_tasks)

        # Verify non-system tasks are excluded
        self.assertNotIn(self.personal_task, system_tasks)
        self.assertNotIn(self.onboarding_task, system_tasks)

    def test_for_user_method(self):
        """Test for_user method returns tasks for specific user."""
        user1_tasks = Task.system_tasks.for_user(self.user1)
        user2_tasks = Task.system_tasks.for_user(self.user2)

        # User1 should have 2 system tasks
        self.assertEqual(user1_tasks.count(), 2)
        self.assertIn(self.system_task1, user1_tasks)
        self.assertIn(self.system_task2, user1_tasks)
        self.assertNotIn(self.system_task_user2, user1_tasks)

        # User2 should have 1 system task
        self.assertEqual(user2_tasks.count(), 1)
        self.assertIn(self.system_task_user2, user2_tasks)
        self.assertNotIn(self.system_task1, user2_tasks)
        self.assertNotIn(self.system_task2, user2_tasks)

    def test_completed_for_user_method(self):
        """Test completed_for_user method returns completed tasks for user."""
        completed_tasks = Task.system_tasks.completed_for_user(self.user1)

        self.assertEqual(completed_tasks.count(), 1)
        self.assertIn(self.system_task2, completed_tasks)
        self.assertNotIn(self.system_task1, completed_tasks)

    def test_pending_for_user_method(self):
        """Test pending_for_user method returns pending tasks for user."""
        pending_tasks = Task.system_tasks.pending_for_user(self.user1)

        self.assertEqual(pending_tasks.count(), 1)
        self.assertIn(self.system_task1, pending_tasks)
        self.assertNotIn(self.system_task2, pending_tasks)

    def test_by_system_code_method(self):
        """Test by_system_code method returns task with specific code."""
        email_task = Task.system_tasks.by_system_code(self.user1, Task.EMAIL_VERIFICATION).first()

        self.assertEqual(email_task, self.system_task1)

        phone_task = Task.system_tasks.by_system_code(self.user1, Task.PHONE_VERIFICATION).first()

        self.assertEqual(phone_task, self.system_task2)

    def test_by_system_code_method_different_users(self):
        """Test by_system_code method isolates by user."""
        user1_email_task = Task.system_tasks.by_system_code(self.user1, Task.EMAIL_VERIFICATION).first()

        user2_email_task = Task.system_tasks.by_system_code(self.user2, Task.EMAIL_VERIFICATION).first()

        self.assertEqual(user1_email_task, self.system_task1)
        self.assertEqual(user2_email_task, self.system_task_user2)
        self.assertNotEqual(user1_email_task, user2_email_task)

    def test_by_system_code_method_nonexistent_code(self):
        """Test by_system_code method with nonexistent code."""
        nonexistent_task = Task.system_tasks.by_system_code(self.user1, "NONEXISTENT_CODE").first()

        self.assertIsNone(nonexistent_task)

    def test_chaining_manager_methods(self):
        """Test chaining multiple manager methods."""
        # Chain for_user with completed
        completed_user1 = Task.system_tasks.for_user(self.user1).filter(status="completed")
        self.assertEqual(completed_user1.count(), 1)
        self.assertIn(self.system_task2, completed_user1)

        # Chain for_user with pending
        pending_user1 = Task.system_tasks.for_user(self.user1).filter(status="pending")
        self.assertEqual(pending_user1.count(), 1)
        self.assertIn(self.system_task1, pending_user1)


class UserTaskManagerTest(TestCase):
    """Test UserTaskManager functionality."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(email="user1@example.com", name="User One")
        self.user2 = User.objects.create_user(email="user2@example.com", name="User Two")

        # Clear system tasks created by signals
        Task.system_tasks.for_user(self.user1).delete()
        Task.system_tasks.for_user(self.user2).delete()

        # Create various types of tasks
        self.personal_task1 = Task.objects.create(
            title="Personal Task 1", user=self.user1, task_type="personal", is_system_generated=False, status="pending"
        )

        self.assignment_task = Task.objects.create(
            title="Assignment Task",
            user=self.user1,
            task_type="assignment",
            is_system_generated=False,
            status="completed",
        )

        self.onboarding_task_user_created = Task.objects.create(
            title="Custom Onboarding",
            user=self.user1,
            task_type="onboarding",
            is_system_generated=False,  # User-created onboarding task
            status="pending",
        )

        self.personal_task_user2 = Task.objects.create(
            title="Personal Task User 2", user=self.user2, task_type="personal", is_system_generated=False
        )

        self.system_task = Task.objects.create(
            title="Email Verification",
            user=self.user1,
            task_type="system",
            system_code=Task.EMAIL_VERIFICATION,
            is_system_generated=True,
        )

        self.onboarding_task_system_generated = Task.objects.create(
            title="System Onboarding",
            user=self.user1,
            task_type="onboarding",
            is_system_generated=True,  # System-generated onboarding task
        )

    def test_manager_instance_type(self):
        """Test that user_tasks manager is correct type."""
        self.assertIsInstance(Task.user_tasks, UserTaskManager)

    def test_get_queryset_filters_user_tasks_only(self):
        """Test that UserTaskManager only returns user-created tasks."""
        user_tasks = Task.user_tasks.all()

        # Should return only user-created tasks (personal, assignment, onboarding with is_system_generated=False)
        self.assertEqual(user_tasks.count(), 4)

        # Verify correct tasks are included
        self.assertIn(self.personal_task1, user_tasks)
        self.assertIn(self.assignment_task, user_tasks)
        self.assertIn(self.onboarding_task_user_created, user_tasks)
        self.assertIn(self.personal_task_user2, user_tasks)

        # Verify system-generated tasks are excluded
        self.assertNotIn(self.system_task, user_tasks)
        self.assertNotIn(self.onboarding_task_system_generated, user_tasks)

    def test_get_queryset_includes_correct_task_types(self):
        """Test that UserTaskManager includes correct task types."""
        user_tasks = Task.user_tasks.all()

        task_types = {task.task_type for task in user_tasks}
        expected_types = {"personal", "assignment", "onboarding"}

        # Should include personal, assignment, and onboarding
        self.assertTrue(expected_types.issubset(task_types))

        # Should not include system
        self.assertNotIn("system", task_types)

    def test_get_queryset_excludes_system_generated(self):
        """Test that UserTaskManager excludes system-generated tasks."""
        user_tasks = Task.user_tasks.all()

        # All returned tasks should be user-generated
        for task in user_tasks:
            self.assertFalse(task.is_system_generated)

    def test_for_user_method(self):
        """Test for_user method returns tasks for specific user."""
        user1_tasks = Task.user_tasks.for_user(self.user1)
        user2_tasks = Task.user_tasks.for_user(self.user2)

        # User1 should have 3 user tasks
        self.assertEqual(user1_tasks.count(), 3)
        self.assertIn(self.personal_task1, user1_tasks)
        self.assertIn(self.assignment_task, user1_tasks)
        self.assertIn(self.onboarding_task_user_created, user1_tasks)
        self.assertNotIn(self.personal_task_user2, user1_tasks)

        # User2 should have 1 user task
        self.assertEqual(user2_tasks.count(), 1)
        self.assertIn(self.personal_task_user2, user2_tasks)

    def test_completed_for_user_method(self):
        """Test completed_for_user method returns completed tasks for user."""
        completed_tasks = Task.user_tasks.completed_for_user(self.user1)

        self.assertEqual(completed_tasks.count(), 1)
        self.assertIn(self.assignment_task, completed_tasks)

    def test_pending_for_user_method(self):
        """Test pending_for_user method returns pending tasks for user."""
        pending_tasks = Task.user_tasks.pending_for_user(self.user1)

        self.assertEqual(pending_tasks.count(), 2)
        self.assertIn(self.personal_task1, pending_tasks)
        self.assertIn(self.onboarding_task_user_created, pending_tasks)

    def test_chaining_manager_methods(self):
        """Test chaining multiple manager methods."""
        # Chain for_user with filter by task_type
        personal_tasks_user1 = Task.user_tasks.for_user(self.user1).filter(task_type="personal")
        self.assertEqual(personal_tasks_user1.count(), 1)
        self.assertIn(self.personal_task1, personal_tasks_user1)

        assignment_tasks_user1 = Task.user_tasks.for_user(self.user1).filter(task_type="assignment")
        self.assertEqual(assignment_tasks_user1.count(), 1)
        self.assertIn(self.assignment_task, assignment_tasks_user1)


class OnboardingTaskManagerTest(TestCase):
    """Test OnboardingTaskManager functionality."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(email="user1@example.com", name="User One")
        self.user2 = User.objects.create_user(email="user2@example.com", name="User Two")

        # Clear system tasks created by signals
        Task.system_tasks.for_user(self.user1).delete()
        Task.system_tasks.for_user(self.user2).delete()

        # Create various types of tasks
        self.onboarding_task1 = Task.objects.create(
            title="Complete Profile",
            user=self.user1,
            task_type="onboarding",
            is_system_generated=True,
            status="pending",
        )

        self.onboarding_task2 = Task.objects.create(
            title="Explore Dashboard",
            user=self.user1,
            task_type="onboarding",
            is_system_generated=True,
            status="completed",
        )

        self.onboarding_task_user_created = Task.objects.create(
            title="Custom Onboarding",
            user=self.user1,
            task_type="onboarding",
            is_system_generated=False,
            status="pending",
        )

        self.onboarding_task_user2 = Task.objects.create(
            title="User 2 Onboarding", user=self.user2, task_type="onboarding", is_system_generated=True
        )

        self.personal_task = Task.objects.create(
            title="Personal Task", user=self.user1, task_type="personal", is_system_generated=False
        )

        self.system_task = Task.objects.create(
            title="Email Verification",
            user=self.user1,
            task_type="system",
            system_code=Task.EMAIL_VERIFICATION,
            is_system_generated=True,
        )

    def test_manager_instance_type(self):
        """Test that onboarding_tasks manager is correct type."""
        self.assertIsInstance(Task.onboarding_tasks, OnboardingTaskManager)

    def test_get_queryset_filters_onboarding_tasks_only(self):
        """Test that OnboardingTaskManager only returns onboarding tasks."""
        onboarding_tasks = Task.onboarding_tasks.all()

        # Should return all onboarding tasks regardless of is_system_generated
        self.assertEqual(onboarding_tasks.count(), 4)

        # Verify all returned tasks are onboarding tasks
        for task in onboarding_tasks:
            self.assertEqual(task.task_type, "onboarding")

        # Verify specific onboarding tasks are included
        self.assertIn(self.onboarding_task1, onboarding_tasks)
        self.assertIn(self.onboarding_task2, onboarding_tasks)
        self.assertIn(self.onboarding_task_user_created, onboarding_tasks)
        self.assertIn(self.onboarding_task_user2, onboarding_tasks)

        # Verify non-onboarding tasks are excluded
        self.assertNotIn(self.personal_task, onboarding_tasks)
        self.assertNotIn(self.system_task, onboarding_tasks)

    def test_for_user_method(self):
        """Test for_user method returns onboarding tasks for specific user."""
        user1_tasks = Task.onboarding_tasks.for_user(self.user1)
        user2_tasks = Task.onboarding_tasks.for_user(self.user2)

        # User1 should have 3 onboarding tasks
        self.assertEqual(user1_tasks.count(), 3)
        self.assertIn(self.onboarding_task1, user1_tasks)
        self.assertIn(self.onboarding_task2, user1_tasks)
        self.assertIn(self.onboarding_task_user_created, user1_tasks)
        self.assertNotIn(self.onboarding_task_user2, user1_tasks)

        # User2 should have 1 onboarding task
        self.assertEqual(user2_tasks.count(), 1)
        self.assertIn(self.onboarding_task_user2, user2_tasks)

    def test_completed_for_user_method(self):
        """Test completed_for_user method returns completed onboarding tasks."""
        completed_tasks = Task.onboarding_tasks.completed_for_user(self.user1)

        self.assertEqual(completed_tasks.count(), 1)
        self.assertIn(self.onboarding_task2, completed_tasks)
        self.assertNotIn(self.onboarding_task1, completed_tasks)
        self.assertNotIn(self.onboarding_task_user_created, completed_tasks)

    def test_chaining_manager_methods(self):
        """Test chaining multiple manager methods."""
        # Chain for_user with filter by is_system_generated
        system_onboarding = Task.onboarding_tasks.for_user(self.user1).filter(is_system_generated=True)
        self.assertEqual(system_onboarding.count(), 2)
        self.assertIn(self.onboarding_task1, system_onboarding)
        self.assertIn(self.onboarding_task2, system_onboarding)
        self.assertNotIn(self.onboarding_task_user_created, system_onboarding)

        user_onboarding = Task.onboarding_tasks.for_user(self.user1).filter(is_system_generated=False)
        self.assertEqual(user_onboarding.count(), 1)
        self.assertIn(self.onboarding_task_user_created, user_onboarding)


class ManagerInteractionTest(TestCase):
    """Test interactions between different managers."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="test@example.com", name="Test User")

        # Clear system tasks created by signals
        Task.system_tasks.for_user(self.user).delete()

        # Create one of each task type
        self.system_task = Task.objects.create(
            title="System Task",
            user=self.user,
            task_type="system",
            system_code=Task.EMAIL_VERIFICATION,
            is_system_generated=True,
        )

        self.personal_task = Task.objects.create(
            title="Personal Task", user=self.user, task_type="personal", is_system_generated=False
        )

        self.assignment_task = Task.objects.create(
            title="Assignment Task", user=self.user, task_type="assignment", is_system_generated=False
        )

        self.onboarding_system_task = Task.objects.create(
            title="System Onboarding", user=self.user, task_type="onboarding", is_system_generated=True
        )

        self.onboarding_user_task = Task.objects.create(
            title="User Onboarding", user=self.user, task_type="onboarding", is_system_generated=False
        )

    def test_manager_isolation(self):
        """Test that different managers return different subsets."""
        all_tasks = set(Task.objects.all())
        system_tasks = set(Task.system_tasks.all())
        user_tasks = set(Task.user_tasks.all())
        onboarding_tasks = set(Task.onboarding_tasks.all())

        # Total should be sum of system + user (no overlap)
        self.assertEqual(len(all_tasks), 5)
        self.assertEqual(len(system_tasks), 1)
        self.assertEqual(len(user_tasks), 3)  # personal + assignment + user onboarding
        self.assertEqual(len(onboarding_tasks), 2)  # system + user onboarding

        # Verify no overlap between system and user managers
        self.assertEqual(len(system_tasks & user_tasks), 0)

        # Verify onboarding manager includes both system and user onboarding
        self.assertIn(self.onboarding_system_task, onboarding_tasks)
        self.assertIn(self.onboarding_user_task, onboarding_tasks)

    def test_default_manager_includes_all(self):
        """Test that default manager includes all tasks."""
        all_tasks_default = set(Task.objects.all())
        system_tasks = set(Task.system_tasks.all())
        user_tasks = set(Task.user_tasks.all())

        # Default manager should include everything
        self.assertTrue(system_tasks.issubset(all_tasks_default))
        self.assertTrue(user_tasks.issubset(all_tasks_default))

    def test_manager_consistency(self):
        """Test that manager filtering is consistent."""
        # System manager should only return system tasks
        for task in Task.system_tasks.all():
            self.assertEqual(task.task_type, "system")
            self.assertTrue(task.is_system_generated)

        # User manager should exclude system tasks
        user_task_types = {task.task_type for task in Task.user_tasks.all()}
        self.assertNotIn("system", user_task_types)

        # Onboarding manager should only return onboarding tasks
        for task in Task.onboarding_tasks.all():
            self.assertEqual(task.task_type, "onboarding")
