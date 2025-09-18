"""
Comprehensive tests for school data isolation in first student task completion.

This module tests the critical multi-tenant architecture requirement that
student task completion is properly scoped to the correct school and roles:

1. **School Isolation**: Tasks completed in School A do NOT affect users in School B
2. **Role-Based Completion**: Only SCHOOL_OWNER and SCHOOL_ADMIN roles get tasks completed
3. **Multi-School Students**: Students with relationships to multiple schools complete tasks for all their schools
4. **Membership Status**: Only active memberships have tasks completed
5. **Fallback Behavior**: When no guardian relationships exist, all users get tasks completed (legacy support)

This is critical for our multi-tenant educational platform where users can belong
to multiple schools with different roles.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import (
    EducationalSystem,
    GuardianStudentRelationship,
    School,
    SchoolMembership,
    StudentProfile,
)
from accounts.models.schools import SchoolRole
from tasks.models import Task
from tasks.services import TaskService

User = get_user_model()


class SchoolTaskIsolationTest(TestCase):
    """Test that task completion is properly isolated by school."""

    def setUp(self):
        """Set up test data for school isolation tests."""
        # Create educational system
        self.educational_system = EducationalSystem.objects.create(
            name="Test System", code="test", description="Test educational system"
        )

        # Create two separate schools
        self.school_a = School.objects.create(name="School A", description="First school")
        self.school_b = School.objects.create(name="School B", description="Second school")

        # Create users for School A
        self.admin_a = User.objects.create_user(email="admin_a@school-a.com", name="Admin A")
        self.teacher_a = User.objects.create_user(email="teacher_a@school-a.com", name="Teacher A")
        self.guardian_a = User.objects.create_user(email="guardian_a@school-a.com", name="Guardian A")

        # Create users for School B
        self.admin_b = User.objects.create_user(email="admin_b@school-b.com", name="Admin B")
        self.teacher_b = User.objects.create_user(email="teacher_b@school-b.com", name="Teacher B")
        self.guardian_b = User.objects.create_user(email="guardian_b@school-b.com", name="Guardian B")

        # Create school memberships for School A
        SchoolMembership.objects.create(
            user=self.admin_a, school=self.school_a, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        SchoolMembership.objects.create(
            user=self.teacher_a, school=self.school_a, role=SchoolRole.TEACHER, is_active=True
        )
        SchoolMembership.objects.create(
            user=self.guardian_a, school=self.school_a, role=SchoolRole.PARENT, is_active=True
        )

        # Create school memberships for School B
        SchoolMembership.objects.create(
            user=self.admin_b, school=self.school_b, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        SchoolMembership.objects.create(
            user=self.teacher_b, school=self.school_b, role=SchoolRole.TEACHER, is_active=True
        )
        SchoolMembership.objects.create(
            user=self.guardian_b, school=self.school_b, role=SchoolRole.PARENT, is_active=True
        )

        # Initialize system tasks for all users
        all_users = [self.admin_a, self.teacher_a, self.guardian_a, self.admin_b, self.teacher_b, self.guardian_b]
        for user in all_users:
            TaskService.initialize_system_tasks(user)

        # Verify only admin users have pending first student tasks (per business logic)
        admin_users = [self.admin_a, self.admin_b]
        for admin_user in admin_users:
            student_task = Task.system_tasks.by_system_code(admin_user, Task.FIRST_STUDENT_ADDED).first()
            self.assertIsNotNone(student_task, f"Admin {admin_user.name} should have FIRST_STUDENT_ADDED task")
            self.assertEqual(student_task.status, "pending", f"Task should be pending for admin {admin_user.name}")

        # Verify non-admin users do NOT have first student tasks (per business logic)
        non_admin_users = [self.teacher_a, self.guardian_a, self.teacher_b, self.guardian_b]
        for user in non_admin_users:
            student_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertIsNone(student_task, f"Non-admin {user.name} should NOT have FIRST_STUDENT_ADDED task")

    def test_task_completion_isolated_by_school(self):
        """Test that adding a student to School A only affects School A admin users."""
        # Create a student user
        student_user = User.objects.create_user(email="student@school-a.com", name="Student A")

        # Create student membership in School A
        SchoolMembership.objects.create(
            user=student_user, school=self.school_a, role=SchoolRole.STUDENT, is_active=True
        )

        # Create guardian-student relationship linking student to School A BEFORE student profile
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_a, student=student_user, school=self.school_a, is_active=True
        )

        # Create student profile (this triggers the signal)
        student_profile = StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify School A admin user has completed task
        admin_a_task = Task.system_tasks.by_system_code(self.admin_a, Task.FIRST_STUDENT_ADDED).first()
        self.assertEqual(admin_a_task.status, "completed", "School A admin task should be completed")
        self.assertIsNotNone(admin_a_task.completed_at)

        # Verify School B admin user still has pending task (ISOLATION!)
        admin_b_task = Task.system_tasks.by_system_code(self.admin_b, Task.FIRST_STUDENT_ADDED).first()
        self.assertEqual(admin_b_task.status, "pending", "School B admin task should remain pending")
        self.assertIsNone(admin_b_task.completed_at)

        # Verify School A teacher does NOT have FIRST_STUDENT_ADDED task (per business logic)
        teacher_a_task = Task.system_tasks.by_system_code(self.teacher_a, Task.FIRST_STUDENT_ADDED).first()
        self.assertIsNone(teacher_a_task, "School A teacher should NOT have FIRST_STUDENT_ADDED task")

        # Verify School B teacher does NOT have FIRST_STUDENT_ADDED task (per business logic)
        teacher_b_task = Task.system_tasks.by_system_code(self.teacher_b, Task.FIRST_STUDENT_ADDED).first()
        self.assertIsNone(teacher_b_task, "School B teacher should NOT have FIRST_STUDENT_ADDED task")

    def test_only_admin_roles_get_tasks_completed(self):
        """Test that only SCHOOL_OWNER and SCHOOL_ADMIN roles have tasks completed."""
        # Create a school owner and additional admin for more comprehensive testing
        school_owner = User.objects.create_user(email="owner@school-a.com", name="Owner A")
        school_admin2 = User.objects.create_user(email="admin2@school-a.com", name="Admin2 A")

        SchoolMembership.objects.create(
            user=school_owner, school=self.school_a, role=SchoolRole.SCHOOL_OWNER, is_active=True
        )
        SchoolMembership.objects.create(
            user=school_admin2, school=self.school_a, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        # Initialize system tasks for the new admin users
        TaskService.initialize_system_tasks(school_owner)
        TaskService.initialize_system_tasks(school_admin2)

        # Create student and link to School A
        student_user = User.objects.create_user(email="student@school-a.com", name="Student A")
        SchoolMembership.objects.create(
            user=student_user, school=self.school_a, role=SchoolRole.STUDENT, is_active=True
        )

        # Create guardian-student relationship BEFORE student profile
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_a, student=student_user, school=self.school_a, is_active=True
        )

        # Create student profile (this triggers the signal)
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify SCHOOL_OWNER has task completed
        owner_task = Task.system_tasks.by_system_code(school_owner, Task.FIRST_STUDENT_ADDED).first()
        self.assertEqual(owner_task.status, "completed", "School owner task should be completed")

        # Verify SCHOOL_ADMIN users have tasks completed
        admin1_task = Task.system_tasks.by_system_code(self.admin_a, Task.FIRST_STUDENT_ADDED).first()
        admin2_task = Task.system_tasks.by_system_code(school_admin2, Task.FIRST_STUDENT_ADDED).first()
        self.assertEqual(admin1_task.status, "completed", "School admin 1 task should be completed")
        self.assertEqual(admin2_task.status, "completed", "School admin 2 task should be completed")

        # Verify TEACHER does NOT have FIRST_STUDENT_ADDED task (per business logic)
        teacher_task = Task.system_tasks.by_system_code(self.teacher_a, Task.FIRST_STUDENT_ADDED).first()
        self.assertIsNone(teacher_task, "Teacher should NOT have FIRST_STUDENT_ADDED task")

        # Verify GUARDIAN does NOT have FIRST_STUDENT_ADDED task (per business logic)
        guardian_task = Task.system_tasks.by_system_code(self.guardian_a, Task.FIRST_STUDENT_ADDED).first()
        self.assertIsNone(guardian_task, "Guardian should NOT have FIRST_STUDENT_ADDED task")

        # Verify STUDENT does NOT have FIRST_STUDENT_ADDED task (per business logic)
        student_task = Task.system_tasks.by_system_code(student_user, Task.FIRST_STUDENT_ADDED).first()
        self.assertIsNone(student_task, "Student should NOT have FIRST_STUDENT_ADDED task")

    def test_multi_school_student_completes_tasks_in_all_schools(self):
        """Test that a student belonging to multiple schools completes tasks for admins in ALL schools."""
        # Create admins for both schools
        # (admin_a and admin_b already exist from setUp)

        # Create student user
        student_user = User.objects.create_user(email="multi-student@example.com", name="Multi School Student")

        # Create memberships in BOTH schools
        SchoolMembership.objects.create(
            user=student_user, school=self.school_a, role=SchoolRole.STUDENT, is_active=True
        )
        SchoolMembership.objects.create(
            user=student_user, school=self.school_b, role=SchoolRole.STUDENT, is_active=True
        )

        # Create guardian relationships to BOTH schools BEFORE student profile
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_a, student=student_user, school=self.school_a, is_active=True
        )
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_b, student=student_user, school=self.school_b, is_active=True
        )

        # Create student profile (this triggers the signal)
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify BOTH school admins have tasks completed
        admin_a_task = Task.system_tasks.by_system_code(self.admin_a, Task.FIRST_STUDENT_ADDED).first()
        admin_b_task = Task.system_tasks.by_system_code(self.admin_b, Task.FIRST_STUDENT_ADDED).first()

        self.assertEqual(admin_a_task.status, "completed", "School A admin task should be completed")
        self.assertEqual(admin_b_task.status, "completed", "School B admin task should be completed")
        self.assertIsNotNone(admin_a_task.completed_at)
        self.assertIsNotNone(admin_b_task.completed_at)

        # Verify teachers in both schools do NOT have FIRST_STUDENT_ADDED tasks (per business logic)
        teacher_a_task = Task.system_tasks.by_system_code(self.teacher_a, Task.FIRST_STUDENT_ADDED).first()
        teacher_b_task = Task.system_tasks.by_system_code(self.teacher_b, Task.FIRST_STUDENT_ADDED).first()

        self.assertIsNone(teacher_a_task, "School A teacher should NOT have FIRST_STUDENT_ADDED task")
        self.assertIsNone(teacher_b_task, "School B teacher should NOT have FIRST_STUDENT_ADDED task")

    def test_inactive_memberships_do_not_get_tasks_completed(self):
        """Test that inactive school memberships are excluded from task completion."""
        # Create additional admin and deactivate their membership
        inactive_admin = User.objects.create_user(email="inactive-admin@school-a.com", name="Inactive Admin")
        SchoolMembership.objects.create(
            user=inactive_admin,
            school=self.school_a,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=False,  # Inactive membership
        )
        # Initialize system tasks for the inactive admin
        TaskService.initialize_system_tasks(inactive_admin)

        # Create student and link to School A
        student_user = User.objects.create_user(email="student@school-a.com", name="Student A")
        SchoolMembership.objects.create(
            user=student_user, school=self.school_a, role=SchoolRole.STUDENT, is_active=True
        )

        # Create guardian-student relationship BEFORE student profile
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_a, student=student_user, school=self.school_a, is_active=True
        )

        # Create student profile (this triggers the signal)
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify active admin has task completed
        active_admin_task = Task.system_tasks.by_system_code(self.admin_a, Task.FIRST_STUDENT_ADDED).first()
        self.assertEqual(active_admin_task.status, "completed", "Active admin task should be completed")

        # Verify inactive admin does NOT have FIRST_STUDENT_ADDED task (inactive membership)
        inactive_admin_task = Task.system_tasks.by_system_code(inactive_admin, Task.FIRST_STUDENT_ADDED).first()
        self.assertIsNone(inactive_admin_task, "Inactive admin should NOT have FIRST_STUDENT_ADDED task")

    def test_no_guardian_relationship_falls_back_to_all_users(self):
        """Test fallback behavior when no guardian relationship exists."""
        # Create student without any guardian relationships
        student_user = User.objects.create_user(email="no-guardian-student@example.com", name="No Guardian Student")

        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )
        # No GuardianStudentRelationship created - triggers fallback

        # Verify ONLY admin users have tasks completed (fallback behavior)
        admin_users = [self.admin_a, self.admin_b]
        non_admin_users = [self.teacher_a, self.guardian_a, self.teacher_b, self.guardian_b, student_user]

        # Admin users should have their tasks completed
        for admin_user in admin_users:
            admin_task = Task.system_tasks.by_system_code(admin_user, Task.FIRST_STUDENT_ADDED).first()
            self.assertEqual(
                admin_task.status, "completed", f"Task should be completed for admin {admin_user.name} in fallback mode"
            )
            self.assertIsNotNone(admin_task.completed_at)

        # Non-admin users should NOT have FIRST_STUDENT_ADDED tasks (per business logic)
        for user in non_admin_users:
            user_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertIsNone(user_task, f"Non-admin {user.name} should NOT have FIRST_STUDENT_ADDED task")

    def test_student_without_user_account_with_guardian_relationship(self):
        """Test student profile without user account but with guardian relationships."""
        # Create guardian-only managed student (no user account)
        student_profile = StudentProfile.objects.create(
            user=None,  # No user account - guardian manages
            educational_system=self.educational_system,
            birth_date="2012-01-01",
            school_year="3",
            account_type="GUARDIAN_ONLY",
        )

        # This case would need guardian relationships, but they require user accounts for students
        # So this tests the edge case where the signal handles None user gracefully
        # and falls back to completing tasks for all users

        # Verify ONLY admin users have tasks completed (fallback because student.user is None)
        admin_users = [self.admin_a, self.admin_b]
        non_admin_users = [self.teacher_a, self.guardian_a, self.teacher_b, self.guardian_b]

        # Admin users should have their tasks completed
        for admin_user in admin_users:
            admin_task = Task.system_tasks.by_system_code(admin_user, Task.FIRST_STUDENT_ADDED).first()
            self.assertEqual(
                admin_task.status,
                "completed",
                f"Task should be completed for admin {admin_user.name} when student has no user account",
            )

        # Non-admin users should NOT have FIRST_STUDENT_ADDED tasks (per business logic)
        for user in non_admin_users:
            user_task = Task.system_tasks.by_system_code(user, Task.FIRST_STUDENT_ADDED).first()
            self.assertIsNone(user_task, f"Non-admin {user.name} should NOT have FIRST_STUDENT_ADDED task")

    def test_cross_school_contamination_prevention(self):
        """Test that task completion for one school absolutely cannot affect another school."""
        # Create a third school to test isolation across multiple schools
        school_c = School.objects.create(name="School C", description="Third school")
        admin_c = User.objects.create_user(email="admin_c@school-c.com", name="Admin C")
        teacher_c = User.objects.create_user(email="teacher_c@school-c.com", name="Teacher C")

        SchoolMembership.objects.create(user=admin_c, school=school_c, role=SchoolRole.SCHOOL_ADMIN, is_active=True)
        SchoolMembership.objects.create(user=teacher_c, school=school_c, role=SchoolRole.TEACHER, is_active=True)

        # Initialize system tasks for new users
        TaskService.initialize_system_tasks(admin_c)
        TaskService.initialize_system_tasks(teacher_c)

        # Add student to School A only
        student_a = User.objects.create_user(email="student-a@school-a.com", name="Student A Only")
        SchoolMembership.objects.create(user=student_a, school=self.school_a, role=SchoolRole.STUDENT, is_active=True)

        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_a, student=student_a, school=self.school_a, is_active=True
        )

        StudentProfile.objects.create(
            user=student_a, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Add student to School B only
        student_b = User.objects.create_user(email="student-b@school-b.com", name="Student B Only")
        SchoolMembership.objects.create(user=student_b, school=self.school_b, role=SchoolRole.STUDENT, is_active=True)

        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_b, student=student_b, school=self.school_b, is_active=True
        )

        StudentProfile.objects.create(
            user=student_b, educational_system=self.educational_system, birth_date="2011-01-01", school_year="4"
        )

        # Verify School A admin is completed, others remain pending
        admin_a_task = Task.system_tasks.by_system_code(self.admin_a, Task.FIRST_STUDENT_ADDED).first()
        admin_b_task = Task.system_tasks.by_system_code(self.admin_b, Task.FIRST_STUDENT_ADDED).first()
        admin_c_task = Task.system_tasks.by_system_code(admin_c, Task.FIRST_STUDENT_ADDED).first()

        self.assertEqual(admin_a_task.status, "completed", "School A admin should be completed")
        self.assertEqual(admin_b_task.status, "completed", "School B admin should be completed")
        self.assertEqual(admin_c_task.status, "pending", "School C admin should remain pending")

        # Verify teachers do NOT have FIRST_STUDENT_ADDED tasks (per business logic)
        teacher_a_task = Task.system_tasks.by_system_code(self.teacher_a, Task.FIRST_STUDENT_ADDED).first()
        teacher_b_task = Task.system_tasks.by_system_code(self.teacher_b, Task.FIRST_STUDENT_ADDED).first()
        teacher_c_task = Task.system_tasks.by_system_code(teacher_c, Task.FIRST_STUDENT_ADDED).first()

        self.assertIsNone(teacher_a_task, "Teachers should NOT have FIRST_STUDENT_ADDED task")
        self.assertIsNone(teacher_b_task, "Teachers should NOT have FIRST_STUDENT_ADDED task")
        self.assertIsNone(teacher_c_task, "Teachers should NOT have FIRST_STUDENT_ADDED task")

    def test_user_with_multiple_roles_in_same_school(self):
        """Test user with multiple admin roles in the same school."""
        # Create user who is both owner and admin in the same school
        multi_role_user = User.objects.create_user(email="multi-role@school-a.com", name="Multi Role User")

        # Create both memberships
        SchoolMembership.objects.create(
            user=multi_role_user, school=self.school_a, role=SchoolRole.SCHOOL_OWNER, is_active=True
        )
        SchoolMembership.objects.create(
            user=multi_role_user, school=self.school_a, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        # Initialize system tasks for multi-role user
        TaskService.initialize_system_tasks(multi_role_user)

        # Add student to trigger task completion
        student_user = User.objects.create_user(email="student@school-a.com", name="Student A")
        SchoolMembership.objects.create(
            user=student_user, school=self.school_a, role=SchoolRole.STUDENT, is_active=True
        )

        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_a, student=student_user, school=self.school_a, is_active=True
        )

        # Verify multi-role user has task completed (should not be duplicated)
        multi_role_task = Task.system_tasks.by_system_code(multi_role_user, Task.FIRST_STUDENT_ADDED).first()
        self.assertEqual(multi_role_task.status, "completed", "Multi-role user should have completed task")

        # Verify only one task exists for this user (no duplicates)
        all_tasks = Task.system_tasks.filter(user=multi_role_user, system_code=Task.FIRST_STUDENT_ADDED)
        self.assertEqual(all_tasks.count(), 1, "Should only have one task per user regardless of multiple roles")

    def test_guardian_from_different_school_relationship(self):
        """Test guardian from School A creating relationship with student in School B."""
        # Create student in School B
        student_user = User.objects.create_user(email="student@school-b.com", name="Student B")
        SchoolMembership.objects.create(
            user=student_user, school=self.school_b, role=SchoolRole.STUDENT, is_active=True
        )

        # Create guardian relationship using guardian from School A but specifying School B
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_a,  # Guardian from School A
            student=student_user,  # Student from School B
            school=self.school_b,  # Relationship is in School B
            is_active=True,
        )

        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify only School B admins get task completed (relationship specifies School B)
        admin_a_task = Task.system_tasks.by_system_code(self.admin_a, Task.FIRST_STUDENT_ADDED).first()
        admin_b_task = Task.system_tasks.by_system_code(self.admin_b, Task.FIRST_STUDENT_ADDED).first()

        self.assertEqual(admin_a_task.status, "pending", "School A admin should remain pending")
        self.assertEqual(admin_b_task.status, "completed", "School B admin should be completed")


class TaskCompletionEdgeCaseTest(TestCase):
    """Test edge cases and error conditions in task completion."""

    def setUp(self):
        """Set up basic test data."""
        self.educational_system = EducationalSystem.objects.create(
            name="Edge Case System", code="edge", description="Edge case test system"
        )
        self.school = School.objects.create(name="Edge Case School", description="Edge case school")

    def test_task_completion_with_no_admin_users_in_school(self):
        """Test behavior when school has no admin users."""
        # Create school with only teachers and students
        teacher = User.objects.create_user(email="teacher@edge.com", name="Teacher Only")
        student_user = User.objects.create_user(email="student@edge.com", name="Student Only")
        guardian_user = User.objects.create_user(email="guardian@edge.com", name="Guardian Only")

        SchoolMembership.objects.create(user=teacher, school=self.school, role=SchoolRole.TEACHER, is_active=True)
        SchoolMembership.objects.create(user=student_user, school=self.school, role=SchoolRole.STUDENT, is_active=True)
        SchoolMembership.objects.create(user=guardian_user, school=self.school, role=SchoolRole.PARENT, is_active=True)

        # Create guardian relationship BEFORE student profile
        GuardianStudentRelationship.objects.create(
            guardian=guardian_user, student=student_user, school=self.school, is_active=True
        )

        # Create student profile (this triggers the signal)
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify non-admin users do NOT have FIRST_STUDENT_ADDED tasks (per business logic)
        teacher_task = Task.system_tasks.by_system_code(teacher, Task.FIRST_STUDENT_ADDED).first()
        student_task = Task.system_tasks.by_system_code(student_user, Task.FIRST_STUDENT_ADDED).first()
        guardian_task = Task.system_tasks.by_system_code(guardian_user, Task.FIRST_STUDENT_ADDED).first()

        self.assertIsNone(teacher_task, "Teacher should NOT have FIRST_STUDENT_ADDED task")
        self.assertIsNone(student_task, "Student should NOT have FIRST_STUDENT_ADDED task")
        self.assertIsNone(guardian_task, "Guardian should NOT have FIRST_STUDENT_ADDED task")

    def test_task_completion_with_inactive_guardian_relationship(self):
        """Test that inactive guardian relationships are ignored."""
        # Create admin user
        admin_user = User.objects.create_user(email="admin@edge.com", name="Admin User")
        SchoolMembership.objects.create(
            user=admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        # Initialize system tasks for admin user
        TaskService.initialize_system_tasks(admin_user)

        # Create student and guardian
        student_user = User.objects.create_user(email="student@edge.com", name="Student")
        guardian_user = User.objects.create_user(email="guardian@edge.com", name="Guardian")

        SchoolMembership.objects.create(user=student_user, school=self.school, role=SchoolRole.STUDENT, is_active=True)
        SchoolMembership.objects.create(user=guardian_user, school=self.school, role=SchoolRole.PARENT, is_active=True)

        # Create INACTIVE guardian relationship BEFORE student profile
        GuardianStudentRelationship.objects.create(
            guardian=guardian_user,
            student=student_user,
            school=self.school,
            is_active=False,  # Inactive relationship
        )

        # Create student profile (this triggers the signal)
        StudentProfile.objects.create(
            user=student_user, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Should fall back to completing tasks for admin users only (no active guardian relationships)
        admin_task = Task.system_tasks.by_system_code(admin_user, Task.FIRST_STUDENT_ADDED).first()
        student_task = Task.system_tasks.by_system_code(student_user, Task.FIRST_STUDENT_ADDED).first()
        guardian_task = Task.system_tasks.by_system_code(guardian_user, Task.FIRST_STUDENT_ADDED).first()

        self.assertEqual(admin_task.status, "completed", "Admin task should be completed (fallback)")
        # Non-admin users should NOT have FIRST_STUDENT_ADDED tasks (per business logic)
        self.assertIsNone(student_task, "Student should NOT have FIRST_STUDENT_ADDED task")
        self.assertIsNone(guardian_task, "Guardian should NOT have FIRST_STUDENT_ADDED task")

    def test_multiple_students_same_school_task_completion_idempotency(self):
        """Test that multiple students added to same school don't cause duplicate task completions."""
        # Create admin user
        admin_user = User.objects.create_user(email="admin@edge.com", name="Admin User")
        guardian_user = User.objects.create_user(email="guardian@edge.com", name="Guardian User")

        SchoolMembership.objects.create(
            user=admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        SchoolMembership.objects.create(user=guardian_user, school=self.school, role=SchoolRole.PARENT, is_active=True)

        # Initialize system tasks for admin user
        TaskService.initialize_system_tasks(admin_user)

        # Add first student
        student1 = User.objects.create_user(email="student1@edge.com", name="Student 1")
        SchoolMembership.objects.create(user=student1, school=self.school, role=SchoolRole.STUDENT, is_active=True)

        GuardianStudentRelationship.objects.create(
            guardian=guardian_user, student=student1, school=self.school, is_active=True
        )

        StudentProfile.objects.create(
            user=student1, educational_system=self.educational_system, birth_date="2010-01-01", school_year="5"
        )

        # Verify task is completed after first student
        admin_task = Task.system_tasks.by_system_code(admin_user, Task.FIRST_STUDENT_ADDED).first()
        self.assertEqual(admin_task.status, "completed")
        first_completion_time = admin_task.completed_at

        # Add second student to same school
        student2 = User.objects.create_user(email="student2@edge.com", name="Student 2")
        SchoolMembership.objects.create(user=student2, school=self.school, role=SchoolRole.STUDENT, is_active=True)

        GuardianStudentRelationship.objects.create(
            guardian=guardian_user, student=student2, school=self.school, is_active=True
        )

        StudentProfile.objects.create(
            user=student2, educational_system=self.educational_system, birth_date="2011-01-01", school_year="4"
        )

        # Verify task completion time is unchanged (idempotent)
        admin_task.refresh_from_db()
        self.assertEqual(admin_task.status, "completed")
        self.assertEqual(
            admin_task.completed_at,
            first_completion_time,
            "Task completion time should not change when adding additional students",
        )
