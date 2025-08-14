"""
Permission Business Logic Unit Tests for Aprende Comigo Platform

These tests verify role-based business rules and permission constraints
at the model level without API dependencies.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherProfile,
)

User = get_user_model()


class RoleBasedBusinessLogicTestCase(TestCase):
    """
    Test suite for verifying role-based business logic at the model level.

    These tests ensure that business rules around roles and permissions
    are properly enforced without relying on API endpoints.
    """

    def setUp(self):
        """Set up test data with multiple roles."""
        self.school = School.objects.create(name="Test School", contact_email="admin@testschool.com")

        # Create users with different roles
        self.school_owner = CustomUser.objects.create_user(email="owner@example.com", name="School Owner")
        self.teacher = CustomUser.objects.create_user(email="teacher@example.com", name="Test Teacher")
        self.student = CustomUser.objects.create_user(email="student@example.com", name="Test Student")

        # Create memberships
        SchoolMembership.objects.create(user=self.school_owner, school=self.school, role=SchoolRole.SCHOOL_OWNER)
        SchoolMembership.objects.create(user=self.teacher, school=self.school, role=SchoolRole.TEACHER)
        SchoolMembership.objects.create(user=self.student, school=self.school, role=SchoolRole.STUDENT)

        # Create profiles
        self.teacher_profile = TeacherProfile.objects.create(user=self.teacher, bio="Test teacher")
        self.student_profile = StudentProfile.objects.create(
            user=self.student, birth_date="2010-01-01", school_year="5th"
        )

    def test_school_owner_can_have_teacher_role_simultaneously(self):
        """Test that school owners can also be teachers in the same school."""
        # Business rule: School owners can also teach
        teacher_membership = SchoolMembership.objects.create(
            user=self.school_owner, school=self.school, role=SchoolRole.TEACHER
        )

        # Verify both roles exist
        owner_memberships = SchoolMembership.objects.filter(user=self.school_owner, school=self.school, is_active=True)

        self.assertEqual(owner_memberships.count(), 2)
        roles = [m.role for m in owner_memberships]
        self.assertIn(SchoolRole.SCHOOL_OWNER, roles)
        self.assertIn(SchoolRole.TEACHER, roles)

    def test_teacher_profile_requires_teacher_membership(self):
        """Test business rule: TeacherProfile should be associated with users who have teacher roles."""
        # Verify teacher has correct membership
        teacher_memberships = SchoolMembership.objects.filter(
            user=self.teacher, role=SchoolRole.TEACHER, is_active=True
        )

        self.assertEqual(teacher_memberships.count(), 1)

        # Verify profile exists for user with teacher role
        self.assertTrue(TeacherProfile.objects.filter(user=self.teacher).exists())

        # Student should not have teacher profile
        self.assertFalse(TeacherProfile.objects.filter(user=self.student).exists())

    def test_student_profile_business_logic(self):
        """Test business logic around student profiles."""
        # Verify student has correct membership
        student_memberships = SchoolMembership.objects.filter(
            user=self.student, role=SchoolRole.STUDENT, is_active=True
        )

        self.assertEqual(student_memberships.count(), 1)

        # Verify profile exists for user with student role
        self.assertTrue(StudentProfile.objects.filter(user=self.student).exists())

        # Teacher should not have student profile
        self.assertFalse(StudentProfile.objects.filter(user=self.teacher).exists())

    def test_inactive_user_membership_business_rules(self):
        """Test business rules for inactive users."""
        # Create inactive user
        inactive_user = CustomUser.objects.create_user(
            email="inactive@example.com", name="Inactive User", is_active=False
        )

        # Create membership for inactive user
        membership = SchoolMembership.objects.create(user=inactive_user, school=self.school, role=SchoolRole.TEACHER)

        # Membership should exist but user is inactive
        self.assertTrue(SchoolMembership.objects.filter(user=inactive_user).exists())
        self.assertFalse(inactive_user.is_active)

        # Business logic should account for user active status
        active_teacher_memberships = SchoolMembership.objects.filter(
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True,
            user__is_active=True,  # Also check user active status
        )

        # Should not include inactive user
        self.assertNotIn(membership, active_teacher_memberships)

    def test_cross_school_role_isolation(self):
        """Test that roles in different schools are properly isolated."""
        # Create another school
        other_school = School.objects.create(name="Other School", contact_email="admin@otherschool.com")

        # Add teacher to other school with different role
        other_membership = SchoolMembership.objects.create(
            user=self.teacher, school=other_school, role=SchoolRole.SCHOOL_OWNER
        )

        # Verify teacher has different roles in different schools
        school1_memberships = SchoolMembership.objects.filter(user=self.teacher, school=self.school)
        school2_memberships = SchoolMembership.objects.filter(user=self.teacher, school=other_school)

        self.assertEqual(school1_memberships.first().role, SchoolRole.TEACHER)
        self.assertEqual(school2_memberships.first().role, SchoolRole.SCHOOL_OWNER)

    def test_role_hierarchy_business_logic(self):
        """Test business logic around role hierarchies."""
        # Get all memberships for each role type
        owner_memberships = SchoolMembership.objects.filter(
            school=self.school, role=SchoolRole.SCHOOL_OWNER, is_active=True
        )
        teacher_memberships = SchoolMembership.objects.filter(
            school=self.school, role=SchoolRole.TEACHER, is_active=True
        )
        student_memberships = SchoolMembership.objects.filter(
            school=self.school, role=SchoolRole.STUDENT, is_active=True
        )

        # Verify role distribution
        self.assertEqual(owner_memberships.count(), 1)
        self.assertEqual(teacher_memberships.count(), 1)
        self.assertEqual(student_memberships.count(), 1)

        # Business rule: Each role type should have distinct users (in this test case)
        owner_users = {m.user for m in owner_memberships}
        teacher_users = {m.user for m in teacher_memberships}
        student_users = {m.user for m in student_memberships}

        self.assertIn(self.school_owner, owner_users)
        self.assertIn(self.teacher, teacher_users)
        self.assertIn(self.student, student_users)

    def test_membership_deactivation_business_logic(self):
        """Test business logic when memberships are deactivated."""
        # Deactivate teacher membership
        teacher_membership = SchoolMembership.objects.get(
            user=self.teacher, school=self.school, role=SchoolRole.TEACHER
        )
        teacher_membership.is_active = False
        teacher_membership.save()

        # Active teacher queries should no longer include this user
        active_teachers = SchoolMembership.objects.filter(school=self.school, role=SchoolRole.TEACHER, is_active=True)

        self.assertEqual(active_teachers.count(), 0)
        self.assertNotIn(teacher_membership, active_teachers)

        # But the membership should still exist for historical purposes
        all_teacher_memberships = SchoolMembership.objects.filter(school=self.school, role=SchoolRole.TEACHER)

        self.assertEqual(all_teacher_memberships.count(), 1)
        self.assertIn(teacher_membership, all_teacher_memberships)


class UserPermissionBoundaryTestCase(TestCase):
    """Test that user permissions are properly bounded at the model level."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(name="Test School")

        # Create users with different permission levels
        self.admin_user = CustomUser.objects.create_superuser(
            email="admin@example.com", name="Admin User", password="admin123"
        )

        self.regular_user = CustomUser.objects.create_user(email="regular@example.com", name="Regular User")

        SchoolMembership.objects.create(user=self.regular_user, school=self.school, role=SchoolRole.STUDENT)

    def test_superuser_flag_business_logic(self):
        """Test business logic around superuser privileges."""
        # Verify superuser flags
        self.assertTrue(self.admin_user.is_superuser)
        self.assertTrue(self.admin_user.is_staff)
        self.assertFalse(self.regular_user.is_superuser)
        self.assertFalse(self.regular_user.is_staff)

        # Business rule: Superusers can access any school context
        # Regular users are limited to their school memberships

        regular_user_schools = SchoolMembership.objects.filter(user=self.regular_user, is_active=True).values_list(
            "school_id", flat=True
        )

        self.assertIn(self.school.id, regular_user_schools)
        self.assertEqual(len(regular_user_schools), 1)

    def test_user_active_status_business_logic(self):
        """Test business logic around user active status."""
        # Create inactive user
        inactive_user = CustomUser.objects.create_user(
            email="inactive@example.com", name="Inactive User", is_active=False
        )

        # Add membership for inactive user
        SchoolMembership.objects.create(user=inactive_user, school=self.school, role=SchoolRole.TEACHER)

        # Business rule: Inactive users should not be included in active business operations
        active_user_memberships = SchoolMembership.objects.filter(
            school=self.school, is_active=True, user__is_active=True
        )

        # Should not include inactive user
        inactive_user_memberships = active_user_memberships.filter(user=inactive_user)
        self.assertEqual(inactive_user_memberships.count(), 0)

        # Should include active user
        active_user_memberships_count = active_user_memberships.filter(user=self.regular_user)
        self.assertEqual(active_user_memberships_count.count(), 1)
