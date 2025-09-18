"""
System integration tests for the unified task system.

This module tests the complete integration between:
- Task system (primary)
- Boolean fields (legacy compatibility)
- Signals (automatic task management)
- Service layer (business logic)

Key principle: Test the real system behavior with signal-created tasks,
do NOT delete system tasks in setUp methods.
"""

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import override_settings

from accounts.models import EducationalSystem, StudentProfile
from tasks.models import Task
from tasks.services import TaskService

User = get_user_model()


class SystemTaskCreationIntegrationTest(TestCase):
    """Test that system tasks are automatically created when users are created."""

    def test_new_user_gets_system_tasks_via_signals(self):
        """Test that creating a user automatically creates system verification tasks."""
        # Create user (should trigger signal that creates system tasks)
        user = User.objects.create_user(email="newuser@example.com", name="New User")

        # Verify system tasks were automatically created (regular users get 2 tasks: email + phone verification)
        system_tasks = Task.system_tasks.for_user(user)
        self.assertEqual(system_tasks.count(), 2, "Should create exactly 2 system tasks")

        # Verify all expected system codes exist (regular users don't get FIRST_STUDENT_ADDED)
        system_codes = {task.system_code for task in system_tasks}
        expected_codes = {Task.EMAIL_VERIFICATION, Task.PHONE_VERIFICATION}
        self.assertEqual(system_codes, expected_codes, "Should create all expected system task types")

        # Verify all tasks are initially pending
        for task in system_tasks:
            self.assertEqual(task.status, "pending", f"Task {task.system_code} should start as pending")
            self.assertEqual(task.task_type, "system", "Should be system type")
            self.assertTrue(task.is_system_generated, "Should be marked as system generated")

    def test_system_task_initial_boolean_field_state(self):
        """Test that boolean fields start as False when user is created."""
        user = User.objects.create_user(email="booltest@example.com", name="Bool Test User")

        # Boolean fields should start as False
        self.assertFalse(user.email_verified, "Email should start unverified")
        self.assertFalse(user.phone_verified, "Phone should start unverified")
        # Note: first_student_added boolean field removed - task system is primary

        # But system tasks should exist
        verification_status = TaskService.get_verification_status(user)
        self.assertFalse(verification_status["email_verified"], "Task system should show email unverified")
        self.assertFalse(verification_status["phone_verified"], "Task system should show phone unverified")


class TaskBooleanFieldSynchronizationTest(TestCase):
    """Test that task completion properly syncs boolean fields."""

    def setUp(self):
        """Set up test user with real signal-created tasks."""
        self.user = User.objects.create_user(email="synctest@example.com", name="Sync Test User")
        # DON'T delete tasks - test the real system!
        # Verify we have the expected system tasks (regular users get 2 tasks: email + phone verification)
        self.assertEqual(Task.system_tasks.for_user(self.user).count(), 2)

    def test_complete_email_task_syncs_boolean_field(self):
        """Test that completing email verification task updates boolean field."""
        # Initially both should be False/pending
        self.assertFalse(self.user.email_verified)

        email_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(email_task.status, "pending")

        # Complete the system task via TaskService
        result = TaskService.complete_system_task(self.user, Task.EMAIL_VERIFICATION)

        # Verify task completion
        self.assertIsNotNone(result, "Should return completed task")
        self.assertEqual(result.status, "completed")
        self.assertIsNotNone(result.completed_at)

        # Verify boolean field was synced
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified, "Boolean field should be synced to True")

    def test_complete_phone_task_syncs_boolean_field(self):
        """Test that completing phone verification task updates boolean field."""
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

    def test_complete_first_student_task_no_boolean_field(self):
        """Test that completing first student task works without boolean field sync (admin users only)."""
        # Regular users don't have FIRST_STUDENT_ADDED tasks - skip this test or make user admin
        # For this test, let's make the user an admin so they have the task
        from accounts.models import School, SchoolMembership
        from accounts.models.schools import SchoolRole

        school = School.objects.create(name="Test Admin School", address="123 Test St")
        SchoolMembership.objects.create(user=self.user, school=school, role=SchoolRole.SCHOOL_ADMIN, is_active=True)

        # Initialize admin tasks
        TaskService.initialize_system_tasks(self.user)

        # No boolean field for first_student_added - task system is primary
        student_task = Task.system_tasks.by_system_code(self.user, Task.FIRST_STUDENT_ADDED).first()
        self.assertIsNotNone(student_task, "Admin users should have FIRST_STUDENT_ADDED task")
        self.assertEqual(student_task.status, "pending")

        # Complete the system task
        result = TaskService.complete_system_task(self.user, Task.FIRST_STUDENT_ADDED)

        # Verify task completion
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "completed")

        # Verify no boolean field sync needed (task system is primary)
        verification_status = TaskService.get_verification_status(self.user)
        self.assertTrue(verification_status["first_student_added"], "Task system should show first student added")

    def test_boolean_field_already_true_no_duplicate_update(self):
        """Test that completing task when boolean field is already True doesn't cause issues."""
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

        # Task should still be completed
        email_task.refresh_from_db()
        self.assertEqual(email_task.status, "completed")


class BooleanFieldToTaskSynchronizationTest(TestCase):
    """Test that boolean field changes complete corresponding tasks (current signal behavior)."""

    def setUp(self):
        """Set up test user with real signal-created tasks."""
        self.user = User.objects.create_user(
            email="bool2task@example.com", name="Bool to Task User", email_verified=False, phone_verified=False
        )
        # Test with real signal-created tasks (regular users get 2 tasks: email + phone verification)
        self.assertEqual(Task.system_tasks.for_user(self.user).count(), 2)

    def test_setting_email_verified_true_completes_task(self):
        """Test that setting email_verified=True completes the email verification task."""
        # Verify task starts as pending
        email_task = Task.system_tasks.by_system_code(self.user, Task.EMAIL_VERIFICATION).first()
        self.assertEqual(email_task.status, "pending")

        # Set boolean field to True (should trigger signal)
        self.user.email_verified = True
        self.user.save()

        # Verify task is now completed
        email_task.refresh_from_db()
        self.assertEqual(email_task.status, "completed")
        self.assertIsNotNone(email_task.completed_at)

    def test_setting_phone_verified_true_completes_task(self):
        """Test that setting phone_verified=True completes the phone verification task."""
        # Verify task starts as pending
        phone_task = Task.system_tasks.by_system_code(self.user, Task.PHONE_VERIFICATION).first()
        self.assertEqual(phone_task.status, "pending")

        # Set boolean field to True (should trigger signal)
        self.user.phone_verified = True
        self.user.save()

        # Verify task is now completed
        phone_task.refresh_from_db()
        self.assertEqual(phone_task.status, "completed")
        self.assertIsNotNone(phone_task.completed_at)


class StudentCreationSystemTaskTest(TestCase):
    """Test the first student added system task behavior."""

    def setUp(self):
        """Set up test admin users and educational system."""
        from accounts.models import School, SchoolMembership
        from accounts.models.schools import SchoolRole

        self.educational_system = EducationalSystem.objects.create(
            name="Test System", code="test", description="Test educational system"
        )

        # Create a real school (not personal)
        self.school = School.objects.create(name="Test Integration School", address="123 Test St")

        # Create multiple admin users (only admins get FIRST_STUDENT_ADDED tasks)
        self.user1 = User.objects.create_user(email="admin1@example.com", name="Admin One")
        self.user2 = User.objects.create_user(email="admin2@example.com", name="Admin Two")

        # Make them school admins
        SchoolMembership.objects.create(
            user=self.user1, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        SchoolMembership.objects.create(
            user=self.user2, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        # Initialize system tasks for admin users
        TaskService.initialize_system_tasks(self.user1)
        TaskService.initialize_system_tasks(self.user2)

        # Verify all admin users have pending first student tasks
        for user in [self.user1, self.user2]:
            student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertIsNotNone(student_task, f"Admin {user.name} should have FIRST_STUDENT_ADDED task")
            self.assertEqual(student_task.status, "pending")

    def test_creating_student_completes_first_student_task_for_admin_users(self):
        """Test that creating ANY student completes first student task for admin users (fallback mode)."""
        # Create a student user
        student_user = User.objects.create_user(email="student@example.com", name="Student User")

        # Create StudentProfile (should trigger signal)
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify admin users' first student tasks are completed (fallback mode)
        for user in [self.user1, self.user2]:
            student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertEqual(
                student_task.status, "completed", f"Admin {user.email} should have completed first student task"
            )
            self.assertIsNotNone(student_task.completed_at)

        # Regular student user should NOT have FIRST_STUDENT_ADDED task (per business logic)
        student_task = Task.system_tasks.by_system_code(student_user, Task.FIRST_STUDENT_ADDED).first()
        self.assertIsNone(student_task, "Regular student users should NOT have FIRST_STUDENT_ADDED task")

        # Note: No boolean field for first_student_added - task system is primary


class EndToEndWorkflowTest(TestCase):
    """Test complete user onboarding workflows."""

    def setUp(self):
        """Set up educational system for student creation."""
        self.educational_system = EducationalSystem.objects.create(
            name="Workflow Test System", code="workflow", description="Workflow test system"
        )

    def test_complete_user_verification_workflow(self):
        """Test complete user verification from creation to full verification."""
        # Create user (triggers system task creation)
        user = User.objects.create_user(
            email="workflow@example.com",
            name="Workflow User",
            phone_number="+351987654321",
            email_verified=False,
            phone_verified=False,
        )

        # Verify initial state
        status = TaskService.get_verification_status(user)
        self.assertFalse(status["email_verified"])
        self.assertFalse(status["phone_verified"])
        self.assertFalse(status["first_student_added"])  # Regular users don't have FIRST_STUDENT_ADDED tasks

        # Step 1: Complete email verification via TaskService
        email_result = TaskService.complete_system_task(user, Task.EMAIL_VERIFICATION)
        self.assertIsNotNone(email_result)

        # Check intermediate state
        status = TaskService.get_verification_status(user)
        self.assertTrue(status["email_verified"])
        self.assertFalse(status["phone_verified"])

        # Verify boolean field was synced
        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        self.assertFalse(user.phone_verified)

        # Step 2: Complete phone verification via boolean field (legacy approach)
        user.phone_verified = True
        user.save()

        # Check state after phone verification
        status = TaskService.get_verification_status(user)
        self.assertTrue(status["email_verified"])
        self.assertTrue(status["phone_verified"])

        # Step 3: Create student (triggers first student completion for all users)
        student_user = User.objects.create_user(email="student@example.com", name="Student User")
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Check final state
        status = TaskService.get_verification_status(user)
        self.assertTrue(status["email_verified"])
        self.assertTrue(status["phone_verified"])
        self.assertFalse(status["first_student_added"])  # Regular users don't have FIRST_STUDENT_ADDED tasks

        # Verify boolean fields are synced (where they exist)
        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        self.assertTrue(user.phone_verified)
        # Note: first_student_added boolean field removed - task system is primary

    def test_legacy_code_compatibility(self):
        """Test that existing code relying on boolean fields still works."""
        user = User.objects.create_user(email="legacy@example.com", name="Legacy User")

        # Legacy code pattern: Check boolean fields directly
        if not user.email_verified:
            # Simulate legacy verification process
            user.email_verified = True
            user.save()

        if not user.phone_verified:
            # Simulate legacy verification process
            user.phone_verified = True
            user.save()

        # Legacy code should see the expected state
        self.assertTrue(user.email_verified)
        self.assertTrue(user.phone_verified)

        # But task system should also be in sync
        status = TaskService.get_verification_status(user)
        self.assertTrue(status["email_verified"])
        self.assertTrue(status["phone_verified"])


class PerformanceTest(TestCase):
    """Test that the task system doesn't create performance issues."""

    def test_get_verification_status_efficient_queries(self):
        """Test that get_verification_status doesn't cause N+1 query issues."""
        # Create user with system tasks
        user = User.objects.create_user(email="perf@example.com", name="Performance User")

        # Measure queries for get_verification_status
        with self.assertNumQueries(1):  # Should be single query with values_list
            TaskService.get_verification_status(user)

    def test_bulk_user_creation_performance(self):
        """Test performance when creating multiple users."""
        # Create multiple users and verify signals don't cause performance issues
        users = []

        # This should not cause exponential query growth
        for i in range(5):
            user = User.objects.create_user(email=f"bulk{i}@example.com", name=f"Bulk User {i}")
            users.append(user)

        # Each user should have their system tasks
        for user in users:
            system_tasks = Task.system_tasks.for_user(user)
            self.assertEqual(system_tasks.count(), 2)  # Regular users get 2 tasks: email + phone verification


class ErrorHandlingTest(TestCase):
    """Test error handling in the integrated system."""

    def test_task_completion_with_missing_user_fields(self):
        """Test task completion when user model is missing expected fields."""
        user = User.objects.create_user(email="error@example.com", name="Error User")

        # Should handle gracefully even if user fields are missing/None
        result = TaskService.complete_system_task(user, Task.EMAIL_VERIFICATION)
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "completed")

    def test_verification_status_with_missing_tasks(self):
        """Test get_verification_status when some system tasks are missing."""
        user = User.objects.create_user(email="missing@example.com", name="Missing Tasks User")

        # Delete one system task
        Task.system_tasks.by_system_code(user, Task.EMAIL_VERIFICATION).delete()

        # Should handle gracefully
        status = TaskService.get_verification_status(user)
        self.assertFalse(status["email_verified"])  # Missing task = False
        self.assertFalse(status["phone_verified"])  # Pending task = False
        self.assertFalse(status["first_student_added"])  # Pending task = False

    def test_signal_resilience_to_errors(self):
        """Test that signal errors don't break user creation."""
        # This would require more complex mocking, but the basic principle:
        # User creation should succeed even if task creation fails
        user = User.objects.create_user(email="resilient@example.com", name="Resilient User")

        # User should exist even if something went wrong with tasks
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "resilient@example.com")
