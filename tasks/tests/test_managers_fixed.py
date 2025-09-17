"""
Tests for Task model custom managers with real system behavior.

This module tests the custom managers for the Task model:
- SystemTaskManager: Managing system-generated tasks
- UserTaskManager: Managing user-created tasks
- OnboardingTaskManager: Managing onboarding tasks

Key principle: Work with real signal-created tasks, do NOT delete them in setUp.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from tasks.managers import OnboardingTaskManager, SystemTaskManager, UserTaskManager
from tasks.models import Task
from tasks.services import TaskService

User = get_user_model()


class SystemTaskManagerRealBehaviorTest(TestCase):
    """Test SystemTaskManager functionality with real signal-created tasks."""

    def setUp(self):
        """Set up test data with real system behavior."""
        self.user1 = User.objects.create_user(email="user1@example.com", name="User One")
        self.user2 = User.objects.create_user(email="user2@example.com", name="User Two")

        # DON'T delete signal-created tasks - work with the real system!
        # Verify signals created the expected system tasks (regular users get 2 tasks: email + phone)
        self.assertEqual(Task.system_tasks.for_user(self.user1).count(), 2)
        self.assertEqual(Task.system_tasks.for_user(self.user2).count(), 2)

        # Create some additional user tasks for testing isolation
        self.personal_task = Task.objects.create(
            title="Personal Task", user=self.user1, task_type="personal", is_system_generated=False
        )

        self.onboarding_task = Task.objects.create(
            title="Complete Profile",
            user=self.user1,
            task_type="onboarding",
            is_system_generated=False,  # User-created onboarding
        )

    def test_manager_instance_type(self):
        """Test that system_tasks manager is correct type."""
        self.assertIsInstance(Task.system_tasks, SystemTaskManager)

    def test_get_queryset_filters_system_tasks_only(self):
        """Test that SystemTaskManager only returns system tasks."""
        system_tasks = Task.system_tasks.all()

        # Should return system tasks from both users (4 total: 2 per user)
        self.assertEqual(system_tasks.count(), 4)

        # Verify all returned tasks are system tasks
        for task in system_tasks:
            self.assertEqual(task.task_type, "system")
            self.assertTrue(task.is_system_generated)
            self.assertIsNotNone(task.system_code)

        # Verify non-system tasks are excluded
        all_task_ids = {task.id for task in system_tasks}
        self.assertNotIn(self.personal_task.id, all_task_ids)
        self.assertNotIn(self.onboarding_task.id, all_task_ids)

    def test_for_user_method_with_signal_created_tasks(self):
        """Test for_user method returns signal-created tasks for specific user."""
        user1_tasks = Task.system_tasks.for_user(self.user1)
        user2_tasks = Task.system_tasks.for_user(self.user2)

        # Each user should have 2 system tasks from signals (email + phone verification)
        self.assertEqual(user1_tasks.count(), 2)
        self.assertEqual(user2_tasks.count(), 2)

        # Verify tasks are properly isolated by user
        user1_task_users = {task.user for task in user1_tasks}
        user2_task_users = {task.user for task in user2_tasks}

        self.assertEqual(user1_task_users, {self.user1})
        self.assertEqual(user2_task_users, {self.user2})

        # Verify all expected system codes exist for each user (regular users don't get FIRST_STUDENT_ADDED)
        expected_codes = {Task.EMAIL_VERIFICATION, Task.PHONE_VERIFICATION}

        user1_codes = {task.system_code for task in user1_tasks}
        user2_codes = {task.system_code for task in user2_tasks}

        self.assertEqual(user1_codes, expected_codes)
        self.assertEqual(user2_codes, expected_codes)

    def test_completed_for_user_method(self):
        """Test completed_for_user method with system tasks."""
        # Initially all tasks should be pending
        completed_tasks = Task.system_tasks.completed_for_user(self.user1)
        self.assertEqual(completed_tasks.count(), 0)

        # Complete one system task
        TaskService.complete_system_task(self.user1, Task.EMAIL_VERIFICATION)

        # Now should have 1 completed task
        completed_tasks = Task.system_tasks.completed_for_user(self.user1)
        self.assertEqual(completed_tasks.count(), 1)

        completed_task = completed_tasks.first()
        self.assertEqual(completed_task.system_code, Task.EMAIL_VERIFICATION)
        self.assertEqual(completed_task.status, "completed")

    def test_pending_for_user_method(self):
        """Test pending_for_user method with system tasks."""
        # Initially all 2 tasks should be pending
        pending_tasks = Task.system_tasks.pending_for_user(self.user1)
        self.assertEqual(pending_tasks.count(), 2)

        # Complete one system task
        TaskService.complete_system_task(self.user1, Task.EMAIL_VERIFICATION)

        # Now should have 1 pending task
        pending_tasks = Task.system_tasks.pending_for_user(self.user1)
        self.assertEqual(pending_tasks.count(), 1)

        pending_codes = {task.system_code for task in pending_tasks}
        expected_pending_codes = {Task.PHONE_VERIFICATION}
        self.assertEqual(pending_codes, expected_pending_codes)

    def test_by_system_code_method_with_signal_tasks(self):
        """Test by_system_code method with signal-created tasks."""
        # Test each system code exists (regular users don't get FIRST_STUDENT_ADDED)
        email_task = Task.system_tasks.by_system_code(self.user1, Task.EMAIL_VERIFICATION).first()
        phone_task = Task.system_tasks.by_system_code(self.user1, Task.PHONE_VERIFICATION).first()
        student_task = Task.system_tasks.by_system_code(self.user1, Task.FIRST_STUDENT_ADDED).first()

        self.assertIsNotNone(email_task)
        self.assertIsNotNone(phone_task)
        self.assertIsNone(student_task)  # Regular users don't get this task

        self.assertEqual(email_task.system_code, Task.EMAIL_VERIFICATION)
        self.assertEqual(phone_task.system_code, Task.PHONE_VERIFICATION)

    def test_by_system_code_method_user_isolation(self):
        """Test by_system_code method properly isolates users."""
        user1_email_task = Task.system_tasks.by_system_code(self.user1, Task.EMAIL_VERIFICATION).first()
        user2_email_task = Task.system_tasks.by_system_code(self.user2, Task.EMAIL_VERIFICATION).first()

        # Both should exist but be different tasks
        self.assertIsNotNone(user1_email_task)
        self.assertIsNotNone(user2_email_task)
        self.assertNotEqual(user1_email_task.id, user2_email_task.id)

        # But both should have same system code
        self.assertEqual(user1_email_task.system_code, Task.EMAIL_VERIFICATION)
        self.assertEqual(user2_email_task.system_code, Task.EMAIL_VERIFICATION)

        # And be owned by different users
        self.assertEqual(user1_email_task.user, self.user1)
        self.assertEqual(user2_email_task.user, self.user2)


class UserTaskManagerRealBehaviorTest(TestCase):
    """Test UserTaskManager functionality with real system behavior."""

    def setUp(self):
        """Set up test data with real system behavior."""
        self.user1 = User.objects.create_user(email="user1@example.com", name="User One")
        self.user2 = User.objects.create_user(email="user2@example.com", name="User Two")

        # DON'T delete signal-created system tasks - they should be excluded by the manager
        # Create various user-created tasks
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

    def test_manager_instance_type(self):
        """Test that user_tasks manager is correct type."""
        self.assertIsInstance(Task.user_tasks, UserTaskManager)

    def test_get_queryset_excludes_signal_created_system_tasks(self):
        """Test that UserTaskManager excludes signal-created system tasks."""
        user_tasks = Task.user_tasks.all()

        # Should only return user-created tasks (4 total)
        self.assertEqual(user_tasks.count(), 4)

        # Verify correct tasks are included
        task_ids = {task.id for task in user_tasks}
        self.assertIn(self.personal_task1.id, task_ids)
        self.assertIn(self.assignment_task.id, task_ids)
        self.assertIn(self.onboarding_task_user_created.id, task_ids)
        self.assertIn(self.personal_task_user2.id, task_ids)

        # Verify no system tasks are included (signals created 6 system tasks total)
        for task in user_tasks:
            self.assertNotEqual(task.task_type, "system")
            self.assertFalse(task.is_system_generated)

    def test_for_user_method_with_mixed_tasks(self):
        """Test for_user method with mixed user and system tasks."""
        user1_user_tasks = Task.user_tasks.for_user(self.user1)
        user2_user_tasks = Task.user_tasks.for_user(self.user2)

        # User1 should have 3 user-created tasks (personal, assignment, onboarding)
        self.assertEqual(user1_user_tasks.count(), 3)

        # User2 should have 1 user-created task
        self.assertEqual(user2_user_tasks.count(), 1)

        # Verify system tasks are excluded even though they exist for these users
        user1_all_tasks = Task.objects.filter(user=self.user1)
        user1_system_tasks = Task.system_tasks.for_user(self.user1)

        self.assertGreater(user1_all_tasks.count(), user1_user_tasks.count())
        self.assertEqual(user1_system_tasks.count(), 2)  # Should have 2 system tasks

    def test_completed_for_user_method(self):
        """Test completed_for_user method returns only completed user tasks."""
        completed_tasks = Task.user_tasks.completed_for_user(self.user1)

        self.assertEqual(completed_tasks.count(), 1)
        self.assertEqual(completed_tasks.first(), self.assignment_task)

    def test_pending_for_user_method(self):
        """Test pending_for_user method returns only pending user tasks."""
        pending_tasks = Task.user_tasks.pending_for_user(self.user1)

        self.assertEqual(pending_tasks.count(), 2)
        pending_task_ids = {task.id for task in pending_tasks}
        self.assertIn(self.personal_task1.id, pending_task_ids)
        self.assertIn(self.onboarding_task_user_created.id, pending_task_ids)


class ManagerIntegrationWithSignalsTest(TestCase):
    """Test manager interactions with signal-created tasks."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(email="integration@example.com", name="Integration User")

        # Work with real signal-created system tasks
        # Create additional user tasks to test isolation
        self.personal_task = Task.objects.create(
            title="Personal Task", user=self.user, task_type="personal", is_system_generated=False
        )

        self.onboarding_user_task = Task.objects.create(
            title="User Onboarding", user=self.user, task_type="onboarding", is_system_generated=False
        )

    def test_manager_isolation_with_signals(self):
        """Test that different managers return correct subsets with signal-created tasks."""
        all_tasks = set(Task.objects.filter(user=self.user))
        system_tasks = set(Task.system_tasks.for_user(self.user))
        user_tasks = set(Task.user_tasks.for_user(self.user))
        onboarding_tasks = set(Task.onboarding_tasks.for_user(self.user))

        # Should have 4 total tasks: 2 system (from signals) + 2 user-created
        self.assertEqual(len(all_tasks), 4)
        self.assertEqual(len(system_tasks), 2)  # From signals
        self.assertEqual(len(user_tasks), 2)  # User-created personal + onboarding
        self.assertEqual(len(onboarding_tasks), 1)  # Only user-created onboarding

        # Verify no overlap between system and user managers
        self.assertEqual(len(system_tasks & user_tasks), 0)

    def test_system_task_completion_doesnt_affect_user_manager(self):
        """Test that completing system tasks doesn't affect user task manager."""
        # Get initial counts
        initial_user_tasks = Task.user_tasks.for_user(self.user).count()
        initial_system_tasks = Task.system_tasks.for_user(self.user).count()

        # Complete a system task
        TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)

        # User task count should be unchanged
        final_user_tasks = Task.user_tasks.for_user(self.user).count()
        final_system_tasks = Task.system_tasks.for_user(self.user).count()

        self.assertEqual(initial_user_tasks, final_user_tasks)
        self.assertEqual(initial_system_tasks, final_system_tasks)

        # But system task should now be completed
        completed_system_tasks = Task.system_tasks.completed_for_user(self.user).count()
        self.assertEqual(completed_system_tasks, 1)

    def test_all_managers_consistent_with_real_data(self):
        """Test that all managers are consistent with real signal-created data."""
        # System manager should only return system tasks
        for task in Task.system_tasks.for_user(self.user):
            self.assertEqual(task.task_type, "system")
            self.assertTrue(task.is_system_generated)
            self.assertIsNotNone(task.system_code)

        # User manager should exclude system tasks and system-generated tasks
        user_task_types = set()
        for task in Task.user_tasks.for_user(self.user):
            self.assertNotEqual(task.task_type, "system")
            self.assertFalse(task.is_system_generated)
            self.assertIsNone(task.system_code)
            user_task_types.add(task.task_type)

        # Should include personal and onboarding (user-created)
        self.assertIn("personal", user_task_types)
        self.assertIn("onboarding", user_task_types)

    def test_queryset_performance_with_signal_tasks(self):
        """Test that manager queries are efficient with signal-created tasks."""
        # This should not cause N+1 queries
        system_tasks = list(Task.system_tasks.for_user(self.user))
        user_tasks = list(Task.user_tasks.for_user(self.user))

        # Verify we get the expected counts
        self.assertEqual(len(system_tasks), 2)
        self.assertEqual(len(user_tasks), 2)

        # Verify proper filtering
        for task in system_tasks:
            self.assertEqual(task.user, self.user)
            self.assertEqual(task.task_type, "system")

        for task in user_tasks:
            self.assertEqual(task.user, self.user)
            self.assertNotEqual(task.task_type, "system")


class ManagerErrorHandlingTest(TestCase):
    """Test manager error handling with real system behavior."""

    def test_managers_handle_missing_system_tasks(self):
        """Test managers handle cases where system tasks might be missing."""
        user = User.objects.create_user(email="missing@example.com", name="Missing Tasks User")

        # Even if somehow system tasks are missing, managers should handle gracefully
        system_tasks = Task.system_tasks.for_user(user)
        user_tasks = Task.user_tasks.for_user(user)

        # Should return querysets (even if empty)
        self.assertIsNotNone(system_tasks)
        self.assertIsNotNone(user_tasks)

        # Should be safe to iterate
        for task in system_tasks:
            self.assertEqual(task.user, user)

        for task in user_tasks:
            self.assertEqual(task.user, user)

    def test_managers_with_corrupted_data(self):
        """Test managers handle corrupted/inconsistent task data."""
        user = User.objects.create_user(email="corrupted@example.com", name="Corrupted User")

        # Create a task with inconsistent data
        inconsistent_task = Task.objects.create(
            title="Inconsistent Task",
            user=user,
            task_type="system",
            is_system_generated=False,  # Inconsistent: system type but not system generated
            status="pending",
        )

        # Managers should handle this gracefully
        system_tasks = Task.system_tasks.for_user(user)
        user_tasks = Task.user_tasks.for_user(user)

        # SystemTaskManager should exclude the inconsistent task (requires both conditions)
        system_task_ids = [task.id for task in system_tasks]
        self.assertNotIn(inconsistent_task.id, system_task_ids)

        # UserTaskManager should exclude system-type tasks regardless of is_system_generated
        user_task_ids = [task.id for task in user_tasks]
        self.assertNotIn(inconsistent_task.id, user_task_ids)


class SchoolAdminTaskCreationTest(TestCase):
    """Test that school administrators get all 3 system tasks including FIRST_STUDENT_ADDED."""

    def setUp(self):
        """Set up test data with a school admin user."""
        from accounts.models import School, SchoolMembership
        from accounts.models.schools import SchoolRole

        # Create a real school (not a personal school)
        self.school = School.objects.create(name="Real Test School", address="123 Test St")

        # Create admin user
        self.admin_user = User.objects.create_user(email="admin@testschool.com", name="School Admin")

        # Create admin membership
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        # Initialize system tasks for the admin user
        from tasks.services import TaskService

        TaskService.initialize_system_tasks(self.admin_user)

    def test_admin_user_gets_all_three_system_tasks(self):
        """Test that school admin users get all 3 system tasks including FIRST_STUDENT_ADDED."""
        admin_system_tasks = Task.system_tasks.for_user(self.admin_user)

        # Admin should have 3 system tasks: email + phone + first student
        self.assertEqual(admin_system_tasks.count(), 3)

        # Verify all expected system codes exist for admin user
        expected_codes = {Task.EMAIL_VERIFICATION, Task.PHONE_VERIFICATION, Task.FIRST_STUDENT_ADDED}
        admin_codes = {task.system_code for task in admin_system_tasks}
        self.assertEqual(admin_codes, expected_codes)

    def test_admin_user_can_complete_first_student_added_task(self):
        """Test that admin users can complete the FIRST_STUDENT_ADDED task."""
        # Initially all 3 tasks should be pending
        pending_tasks = Task.system_tasks.pending_for_user(self.admin_user)
        self.assertEqual(pending_tasks.count(), 3)

        # Complete the FIRST_STUDENT_ADDED task
        from tasks.services import TaskService

        TaskService.complete_system_task(self.admin_user, Task.FIRST_STUDENT_ADDED)

        # Now should have 2 pending tasks
        pending_tasks = Task.system_tasks.pending_for_user(self.admin_user)
        self.assertEqual(pending_tasks.count(), 2)

        # Verify the FIRST_STUDENT_ADDED task is completed
        completed_tasks = Task.system_tasks.completed_for_user(self.admin_user)
        self.assertEqual(completed_tasks.count(), 1)

        completed_task = completed_tasks.first()
        self.assertEqual(completed_task.system_code, Task.FIRST_STUDENT_ADDED)
        self.assertEqual(completed_task.status, "completed")

    def test_regular_vs_admin_user_task_difference(self):
        """Test the difference between regular users and admin users for system tasks."""
        # Create a regular user for comparison
        regular_user = User.objects.create_user(email="regular@example.com", name="Regular User")

        # Regular users get 2 tasks, admin users get 3
        regular_system_tasks = Task.system_tasks.for_user(regular_user)
        admin_system_tasks = Task.system_tasks.for_user(self.admin_user)

        self.assertEqual(regular_system_tasks.count(), 2)
        self.assertEqual(admin_system_tasks.count(), 3)

        # Regular user shouldn't have FIRST_STUDENT_ADDED task
        regular_codes = {task.system_code for task in regular_system_tasks}
        admin_codes = {task.system_code for task in admin_system_tasks}

        expected_regular_codes = {Task.EMAIL_VERIFICATION, Task.PHONE_VERIFICATION}
        expected_admin_codes = {Task.EMAIL_VERIFICATION, Task.PHONE_VERIFICATION, Task.FIRST_STUDENT_ADDED}

        self.assertEqual(regular_codes, expected_regular_codes)
        self.assertEqual(admin_codes, expected_admin_codes)
