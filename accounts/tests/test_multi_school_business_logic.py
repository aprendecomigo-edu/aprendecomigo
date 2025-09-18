"""
Unit tests for multi-school business logic scenarios.

This module tests complex multi-school business logic without API dependencies.
These tests focus on model relationships and business rules.
"""

from django.test import TestCase

from accounts.models import (
    Course,
    CustomUser,
    EducationalSystem,
    School,
    SchoolMembership,
    SchoolRole,
    TeacherCourse,
    TeacherProfile,
)
from accounts.tests.test_utils import get_unique_email, get_unique_phone_number


class MultiSchoolBusinessLogicTest(TestCase):
    """Unit tests for multi-school business scenarios."""

    def setUp(self):
        """Set up test data for multi-school business logic tests."""
        # Create test educational system and course
        self.educational_system = EducationalSystem.objects.create(
            name="Test System", code="test", description="Test system", is_active=True
        )
        self.course = Course.objects.create(
            name="Test Math", code="TEST_635", educational_system=self.educational_system, education_level="elementary"
        )

        # Create test schools
        self.school1 = School.objects.create(name="School 1", description="Test school 1", address="Address 1")
        self.school2 = School.objects.create(name="School 2", description="Test school 2", address="Address 2")

    def create_user(self, email, name, phone=None):
        """Factory method to create user."""
        if phone is None:
            phone = get_unique_phone_number()
        return CustomUser.objects.create_user(email=email, name=name, phone_number=phone)

    def create_school_membership(self, user, school, role):
        """Factory method to create school membership."""
        return SchoolMembership.objects.create(user=user, school=school, role=role, is_active=True)

    def test_same_user_teacher_in_multiple_schools_business_logic(self):
        """Test business rule: same user can be a teacher in multiple schools."""
        user = self.create_user("teacher@example.com", "Multi School Teacher")

        # Create teacher profile first
        teacher_profile = TeacherProfile.objects.create(user=user, bio="Multi-school teacher", specialty="Mathematics")

        # Add as teacher to both schools
        membership1 = self.create_school_membership(user, self.school1, SchoolRole.TEACHER)
        membership2 = self.create_school_membership(user, self.school2, SchoolRole.TEACHER)

        # Verify business logic: user can teach at multiple schools
        teacher_memberships = SchoolMembership.objects.filter(user=user, role=SchoolRole.TEACHER, is_active=True)
        self.assertEqual(teacher_memberships.count(), 2)

        # Verify teacher profile method returns both memberships
        profile_memberships = teacher_profile.get_school_memberships()
        self.assertEqual(profile_memberships.count(), 2)

        school_names = [m.school.name for m in teacher_memberships]
        self.assertIn(self.school1.name, school_names)
        self.assertIn(self.school2.name, school_names)

    def test_school_with_multiple_teachers_business_logic(self):
        """Test business rule: a school can have multiple active teachers."""
        # Create multiple teachers for school1
        teacher1 = self.create_user("teacher1@example.com", "Teacher 1")
        teacher2 = self.create_user("teacher2@example.com", "Teacher 2")
        teacher3 = self.create_user("teacher3@example.com", "Teacher 3")

        # Create teacher profiles
        TeacherProfile.objects.create(user=teacher1, bio="Teacher 1", specialty="Mathematics")
        TeacherProfile.objects.create(user=teacher2, bio="Teacher 2", specialty="Physics")
        TeacherProfile.objects.create(user=teacher3, bio="Teacher 3", specialty="Chemistry")

        # Add all as teachers to school1
        self.create_school_membership(teacher1, self.school1, SchoolRole.TEACHER)
        self.create_school_membership(teacher2, self.school1, SchoolRole.TEACHER)
        self.create_school_membership(teacher3, self.school1, SchoolRole.TEACHER)

        # Verify business logic: school can have multiple teachers
        teacher_memberships = SchoolMembership.objects.filter(
            school=self.school1, role=SchoolRole.TEACHER, is_active=True
        )
        self.assertEqual(teacher_memberships.count(), 3)

        teacher_emails = [m.user.email for m in teacher_memberships]
        self.assertIn(teacher1.email, teacher_emails)
        self.assertIn(teacher2.email, teacher_emails)
        self.assertIn(teacher3.email, teacher_emails)

    def test_user_multiple_roles_same_school_business_logic(self):
        """Test business rule: user can have multiple roles in same school."""
        # Create users for different roles
        owner = self.create_user("owner@example.com", "School Owner")
        teacher = self.create_user("teacher@example.com", "Teacher")

        # Create teacher profile for teacher
        TeacherProfile.objects.create(user=teacher, bio="Teacher bio", specialty="Math")

        # Add users with different roles to school1
        self.create_school_membership(owner, self.school1, SchoolRole.SCHOOL_OWNER)
        self.create_school_membership(teacher, self.school1, SchoolRole.TEACHER)

        # Business rule: owner can also become teacher in same school
        teacher_membership = self.create_school_membership(owner, self.school1, SchoolRole.TEACHER)

        # Verify business logic: user can have multiple roles
        owner_memberships = SchoolMembership.objects.filter(user=owner, school=self.school1, is_active=True)
        self.assertEqual(owner_memberships.count(), 2)

        roles = [m.role for m in owner_memberships]
        self.assertIn(SchoolRole.SCHOOL_OWNER, roles)
        self.assertIn(SchoolRole.TEACHER, roles)

    def test_inactive_membership_business_rule(self):
        """Test business rule: inactive memberships don't appear in active queries."""
        user = self.create_user("user@example.com", "Test User")
        TeacherProfile.objects.create(user=user, bio="Teacher bio", specialty="Math")

        # Create active membership
        active_membership = self.create_school_membership(user, self.school1, SchoolRole.TEACHER)

        # Create inactive membership with different role to avoid unique constraint
        inactive_membership = SchoolMembership.objects.create(
            user=user, school=self.school1, role=SchoolRole.STUDENT, is_active=False
        )

        # Business rule: only active memberships appear in active queries
        active_memberships = SchoolMembership.objects.filter(school=self.school1, user=user, is_active=True)
        inactive_memberships = SchoolMembership.objects.filter(school=self.school1, user=user, is_active=False)

        self.assertEqual(active_memberships.count(), 1)
        self.assertEqual(inactive_memberships.count(), 1)
        self.assertEqual(active_memberships.first(), active_membership)
        self.assertEqual(inactive_memberships.first(), inactive_membership)

    def test_teacher_course_association_business_logic(self):
        """Test business rule: teachers can be associated with multiple courses."""
        user = self.create_user("teacher@example.com", "Course Teacher")
        teacher_profile = TeacherProfile.objects.create(user=user, bio="Multi-course teacher", specialty="STEM")

        # Create additional course
        course2 = Course.objects.create(
            name="Test Physics",
            code="TEST_PHY",
            educational_system=self.educational_system,
            education_level="secondary",
        )

        # Associate teacher with multiple courses
        TeacherCourse.objects.create(teacher=teacher_profile, course=self.course)
        TeacherCourse.objects.create(teacher=teacher_profile, course=course2)

        # Verify business logic: teacher can teach multiple courses
        teacher_courses = TeacherCourse.objects.filter(teacher=teacher_profile, is_active=True)
        self.assertEqual(teacher_courses.count(), 2)

        course_names = [tc.course.name for tc in teacher_courses]
        self.assertIn(self.course.name, course_names)
        self.assertIn(course2.name, course_names)
