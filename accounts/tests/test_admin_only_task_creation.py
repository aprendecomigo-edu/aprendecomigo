"""
Tests for admin-only FIRST_STUDENT_ADDED task creation.

Ensures that the FIRST_STUDENT_ADDED task is only created for users who are
actual school administrators or owners, not for students or users who only
have automatically-created personal schools.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import School, SchoolMembership
from accounts.models.enums import SchoolRole
from accounts.tests.test_base import BaseTestCase
from tasks.models import Task
from tasks.services import TaskService

User = get_user_model()


class AdminOnlyTaskCreationTest(BaseTestCase):
    """Test that FIRST_STUDENT_ADDED task is only created for real admins/owners."""

    def test_real_admin_gets_first_student_added_task(self):
        """Test that admin users of real schools get FIRST_STUDENT_ADDED task."""
        # Create real school and admin user
        real_school = School.objects.create(name="Real Test School")
        admin_user = User.objects.create_user(email="realadmin@test.com", name="Real Admin")

        # Make user admin of the real school (not just personal school)
        SchoolMembership.objects.create(
            user=admin_user, school=real_school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        # Initialize system tasks
        tasks = TaskService.initialize_system_tasks(admin_user)

        # Check that FIRST_STUDENT_ADDED task was created
        first_student_task = Task.objects.filter(user=admin_user, system_code=Task.FIRST_STUDENT_ADDED).first()

        self.assertIsNotNone(first_student_task, "Real admin should get FIRST_STUDENT_ADDED task")
        self.assertIn(Task.FIRST_STUDENT_ADDED, [task.system_code for task in tasks])

    def test_real_owner_gets_first_student_added_task(self):
        """Test that owner users of real schools get FIRST_STUDENT_ADDED task."""
        # Create real school and owner user
        real_school = School.objects.create(name="Real Owner School")
        owner_user = User.objects.create_user(email="realowner@test.com", name="Real Owner")

        # Make user owner of the real school (not just personal school)
        SchoolMembership.objects.create(
            user=owner_user, school=real_school, role=SchoolRole.SCHOOL_OWNER, is_active=True
        )

        # Initialize system tasks
        tasks = TaskService.initialize_system_tasks(owner_user)

        # Check that FIRST_STUDENT_ADDED task was created
        first_student_task = Task.objects.filter(user=owner_user, system_code=Task.FIRST_STUDENT_ADDED).first()

        self.assertIsNotNone(first_student_task, "Real owner should get FIRST_STUDENT_ADDED task")
        self.assertIn(Task.FIRST_STUDENT_ADDED, [task.system_code for task in tasks])

    def test_student_with_personal_school_does_not_get_task(self):
        """Test that students with only personal schools do NOT get FIRST_STUDENT_ADDED task."""
        # Create student user (system will auto-create personal school)
        student_user = User.objects.create_user(email="student@test.com", name="Student User")

        # The system should auto-create a personal school and make them owner
        # but this should NOT qualify them for the FIRST_STUDENT_ADDED task

        # Initialize system tasks
        tasks = TaskService.initialize_system_tasks(student_user)

        # Check that FIRST_STUDENT_ADDED task was NOT created
        first_student_task = Task.objects.filter(user=student_user, system_code=Task.FIRST_STUDENT_ADDED).first()

        self.assertIsNone(
            first_student_task, "Student with only personal school should NOT get FIRST_STUDENT_ADDED task"
        )
        self.assertNotIn(Task.FIRST_STUDENT_ADDED, [task.system_code for task in tasks])

    def test_teacher_does_not_get_first_student_added_task(self):
        """Test that teachers do NOT get FIRST_STUDENT_ADDED task."""
        # Create real school and teacher user
        real_school = School.objects.create(name="Teacher Test School")
        teacher_user = User.objects.create_user(email="teacher@test.com", name="Teacher User")

        # Make user teacher of the real school
        SchoolMembership.objects.create(user=teacher_user, school=real_school, role=SchoolRole.TEACHER, is_active=True)

        # Initialize system tasks
        tasks = TaskService.initialize_system_tasks(teacher_user)

        # Check that FIRST_STUDENT_ADDED task was NOT created
        first_student_task = Task.objects.filter(user=teacher_user, system_code=Task.FIRST_STUDENT_ADDED).first()

        self.assertIsNone(first_student_task, "Teacher should NOT get FIRST_STUDENT_ADDED task")
        self.assertNotIn(Task.FIRST_STUDENT_ADDED, [task.system_code for task in tasks])

    def test_all_users_get_email_and_phone_verification_tasks(self):
        """Test that all users get email and phone verification tasks regardless of role."""
        # Create different types of users
        admin_user = User.objects.create_user(email="admin@example.com", name="Admin")
        student_user = User.objects.create_user(email="student@example.com", name="Student")

        real_school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=admin_user, school=real_school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        # Initialize tasks for both users
        admin_tasks = TaskService.initialize_system_tasks(admin_user)
        student_tasks = TaskService.initialize_system_tasks(student_user)

        # Both should get email and phone verification tasks
        for user, tasks in [(admin_user, admin_tasks), (student_user, student_tasks)]:
            task_codes = [task.system_code for task in tasks]

            # Check email verification task exists
            email_task = Task.objects.filter(user=user, system_code=Task.EMAIL_VERIFICATION).first()
            self.assertIsNotNone(email_task, f"{user.name} should get EMAIL_VERIFICATION task")

            # Check phone verification task exists
            phone_task = Task.objects.filter(user=user, system_code=Task.PHONE_VERIFICATION).first()
            self.assertIsNotNone(phone_task, f"{user.name} should get PHONE_VERIFICATION task")

    def test_is_school_admin_or_owner_method_excludes_personal_schools(self):
        """Test that _is_school_admin_or_owner correctly excludes personal schools."""
        # Create user with only personal school
        user_with_personal = User.objects.create_user(email="personal@test.com", name="Personal User")

        # Create user with real school admin role
        user_with_real_school = User.objects.create_user(email="realadmin@test.com", name="Real Admin")
        real_school = School.objects.create(name="Real School")
        SchoolMembership.objects.create(
            user=user_with_real_school, school=real_school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        # Test the method directly
        self.assertFalse(
            TaskService._is_school_admin_or_owner(user_with_personal),
            "User with only personal school should NOT be considered admin/owner",
        )

        self.assertTrue(
            TaskService._is_school_admin_or_owner(user_with_real_school),
            "User with real school admin role should be considered admin/owner",
        )
