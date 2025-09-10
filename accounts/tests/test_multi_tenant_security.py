"""
Multi-Tenant Data Isolation Unit Tests for Aprende Comigo Platform

These tests verify that data is properly isolated between different schools
at the model and queryset level. Focus on business logic and data integrity.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import (
    CustomUser,
    EducationalSystem,
    School,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherProfile,
)
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class QuerysetIsolationTestCase(BaseTestCase):
    """
    Test that queryset-level filtering properly isolates data by school.

    These tests verify that the ORM queries properly filter data
    without relying on API endpoints.
    """

    def setUp(self):
        """Set up test data."""
        self.school1 = School.objects.create(name="School 1")
        self.school2 = School.objects.create(name="School 2")

        self.user1 = CustomUser.objects.create_user(email="user1@test.com", name="User 1")
        self.user2 = CustomUser.objects.create_user(email="user2@test.com", name="User 2")

        # Create memberships
        self.membership1 = SchoolMembership.objects.create(
            user=self.user1, school=self.school1, role=SchoolRole.STUDENT
        )
        self.membership2 = SchoolMembership.objects.create(
            user=self.user2, school=self.school2, role=SchoolRole.STUDENT
        )

    def test_school_membership_queryset_filtering(self):
        """Test SchoolMembership queryset filtering by school."""
        # Filter by school - should only return relevant membership
        school1_memberships = SchoolMembership.objects.filter(school=self.school1)

        self.assertIn(self.membership1, school1_memberships)
        self.assertNotIn(self.membership2, school1_memberships)

        # Verify counts are correct
        self.assertEqual(school1_memberships.count(), 1)

    def test_teacher_profile_school_filtering(self):
        """Test that teacher profiles can be filtered by school context."""
        teacher1 = CustomUser.objects.create_user(email="teacher1@test.com", name="Teacher 1")
        teacher2 = CustomUser.objects.create_user(email="teacher2@test.com", name="Teacher 2")

        SchoolMembership.objects.create(user=teacher1, school=self.school1, role=SchoolRole.TEACHER)
        SchoolMembership.objects.create(user=teacher2, school=self.school2, role=SchoolRole.TEACHER)

        profile1 = TeacherProfile.objects.create(user=teacher1)
        profile2 = TeacherProfile.objects.create(user=teacher2)

        # Get teachers from school1 only
        school1_teacher_ids = SchoolMembership.objects.filter(
            school=self.school1, role=SchoolRole.TEACHER, is_active=True
        ).values_list("user_id", flat=True)

        school1_teachers = TeacherProfile.objects.filter(user_id__in=school1_teacher_ids)

        self.assertIn(profile1, school1_teachers)
        self.assertNotIn(profile2, school1_teachers)

    def test_student_profile_school_filtering(self):
        """Test that student profiles can be filtered by school context."""
        student1 = CustomUser.objects.create_user(email="student1@test.com", name="Student 1")
        student2 = CustomUser.objects.create_user(email="student2@test.com", name="Student 2")

        SchoolMembership.objects.create(user=student1, school=self.school1, role=SchoolRole.STUDENT)
        SchoolMembership.objects.create(user=student2, school=self.school2, role=SchoolRole.STUDENT)

        profile1 = StudentProfile.objects.create(
            user=student1, 
            educational_system=self.default_educational_system, 
            birth_date="2010-01-01", 
            school_year="5th"
        )
        profile2 = StudentProfile.objects.create(
            user=student2, 
            educational_system=self.default_educational_system, 
            birth_date="2011-01-01", 
            school_year="4th"
        )

        # Get students from school1 only
        school1_student_ids = SchoolMembership.objects.filter(
            school=self.school1, role=SchoolRole.STUDENT, is_active=True
        ).values_list("user_id", flat=True)

        school1_students = StudentProfile.objects.filter(user_id__in=school1_student_ids)

        self.assertIn(profile1, school1_students)
        self.assertNotIn(profile2, school1_students)

    def test_multi_school_user_membership_isolation(self):
        """Test that users with memberships in multiple schools have proper data isolation."""
        # Create a user who is a teacher in both schools
        multi_school_user = CustomUser.objects.create_user(email="multischool@example.com", name="Multi School User")

        # Add to both schools
        membership1 = SchoolMembership.objects.create(
            user=multi_school_user, school=self.school1, role=SchoolRole.TEACHER
        )
        membership2 = SchoolMembership.objects.create(
            user=multi_school_user, school=self.school2, role=SchoolRole.TEACHER
        )

        # Verify user has memberships in both schools
        user_memberships = SchoolMembership.objects.filter(user=multi_school_user)
        self.assertEqual(user_memberships.count(), 2)

        # Verify each membership is properly isolated by school
        school1_memberships = user_memberships.filter(school=self.school1)
        school2_memberships = user_memberships.filter(school=self.school2)

        self.assertEqual(school1_memberships.count(), 1)
        self.assertEqual(school2_memberships.count(), 1)
        self.assertEqual(school1_memberships.first(), membership1)
        self.assertEqual(school2_memberships.first(), membership2)


class DataIntegrityTestCase(TestCase):
    """Test data integrity in multi-tenant scenarios."""

    def test_user_can_have_multiple_roles_in_same_school(self):
        """Test that business logic properly handles multiple roles in same school."""
        school = School.objects.create(name="Test School")
        user = CustomUser.objects.create_user(email="test@example.com", name="Test User")

        # Create first membership
        membership1 = SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.TEACHER)

        # Business rule: users can have multiple roles in same school
        # (e.g., School Owner who also teaches)
        membership2 = SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.SCHOOL_OWNER)

        # Verify both exist
        memberships = SchoolMembership.objects.filter(user=user, school=school)
        self.assertEqual(memberships.count(), 2)

        roles = [m.role for m in memberships]
        self.assertIn(SchoolRole.TEACHER, roles)
        self.assertIn(SchoolRole.SCHOOL_OWNER, roles)

    def test_school_deletion_cascades_properly(self):
        """Test that deleting a school properly cascades to related objects."""
        school = School.objects.create(name="To Delete School")
        user = CustomUser.objects.create_user(email="test@example.com", name="Test User")

        membership = SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.STUDENT)

        # Verify membership exists
        self.assertTrue(SchoolMembership.objects.filter(school=school).exists())

        # Delete school
        school.delete()

        # Verify membership is cleaned up
        self.assertFalse(SchoolMembership.objects.filter(id=membership.id).exists())

        # Verify user still exists (should not be cascade deleted)
        self.assertTrue(CustomUser.objects.filter(id=user.id).exists())

    def test_inactive_membership_does_not_affect_active_queries(self):
        """Test that inactive memberships don't interfere with active business logic."""
        school = School.objects.create(name="Test School")
        user = CustomUser.objects.create_user(email="test@example.com", name="Test User")

        # Create active membership
        active_membership = SchoolMembership.objects.create(
            user=user, school=school, role=SchoolRole.TEACHER, is_active=True
        )

        # Create inactive membership
        inactive_membership = SchoolMembership.objects.create(
            user=user, school=school, role=SchoolRole.STUDENT, is_active=False
        )

        # Active queries should only return active membership
        active_memberships = SchoolMembership.objects.filter(user=user, school=school, is_active=True)

        self.assertEqual(active_memberships.count(), 1)
        self.assertEqual(active_memberships.first(), active_membership)
        self.assertNotIn(inactive_membership, active_memberships)

    def test_school_membership_business_logic_constraints(self):
        """Test business logic around school membership creation."""
        school = School.objects.create(name="Test School")
        user = CustomUser.objects.create_user(email="test@example.com", name="Test User")

        # Create first membership
        membership1 = SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.TEACHER)

        # Creating another membership with same user, school, different role should be allowed
        # (business rule: users can have multiple active roles)
        membership2 = SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.SCHOOL_OWNER)

        # Both should exist
        memberships = SchoolMembership.objects.filter(user=user, school=school)
        self.assertEqual(memberships.count(), 2)
