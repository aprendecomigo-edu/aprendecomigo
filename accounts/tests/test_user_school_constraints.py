"""
Unit tests for user-school relationship constraints.

Tests the fundamental business rule: every non-superuser must have at least one active school membership.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.db_queries import create_user_school_and_membership
from accounts.models import School, SchoolMembership, SchoolRole
from accounts.tests.test_base import BaseTestCase
from tests.test_waffle_switches import get_test_password

User = get_user_model()


class UserSchoolConstraintTestCase(BaseTestCase):
    """Test user-school relationship constraints and validation"""

    def setUp(self):
        """Set up test data"""
        self.valid_user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "phone_number": "+351123456789",
            "first_name": "Test",
            "last_name": "User",
        }

        self.valid_school_name = "Test School"

    def test_create_user_school_and_membership_success(self):
        """Test successful creation of user, school, and membership"""
        # Act: Create user and school atomically
        user = User.objects.create_user(**self.valid_user_data)
        school = create_user_school_and_membership(user, self.valid_school_name)

        # Assert: User has been created
        self.assertTrue(User.objects.filter(email=self.valid_user_data["email"]).exists())

        # Assert: School has been created with correct name
        self.assertEqual(school.name, self.valid_school_name)
        self.assertEqual(school.contact_email, user.email)
        self.assertTrue(School.objects.filter(name=self.valid_school_name).exists())

        # Assert: User has school membership as owner
        membership = SchoolMembership.objects.get(user=user, school=school)
        self.assertEqual(membership.role, SchoolRole.SCHOOL_OWNER)
        self.assertTrue(membership.is_active)

        # Assert: User has exactly one active membership
        active_memberships = user.school_memberships.filter(is_active=True)
        self.assertEqual(active_memberships.count(), 1)

    def test_create_user_school_duplicate_name_handling(self):
        """Test creating multiple schools with same name for different users"""
        # Arrange: Create first user and school
        user1 = User.objects.create_user(email="user1@example.com", name="User One", first_name="User", last_name="One")
        school1 = create_user_school_and_membership(user1, self.valid_school_name)

        # Act: Create second user with same school name
        user2 = User.objects.create_user(email="user2@example.com", name="User Two", first_name="User", last_name="Two")
        school2 = create_user_school_and_membership(user2, self.valid_school_name)

        # Assert: Both schools created successfully (names can be duplicate)
        self.assertEqual(School.objects.filter(name=self.valid_school_name).count(), 2)
        self.assertNotEqual(school1.id, school2.id)

        # Assert: Each user has their own school membership
        self.assertEqual(user1.school_memberships.count(), 1)
        self.assertEqual(user2.school_memberships.count(), 1)
        self.assertEqual(user1.school_memberships.first().school, school1)
        self.assertEqual(user2.school_memberships.first().school, school2)

    def test_superuser_can_exist_without_school_membership(self):
        """Test that superusers can exist without school memberships"""
        # Act: Create superuser
        superuser = User.objects.create_superuser(
            email="admin@example.com", password=get_test_password(), name="Admin User"
        )

        # Assert: Superuser exists without memberships
        self.assertTrue(superuser.is_superuser)
        self.assertEqual(superuser.school_memberships.count(), 0)

        # Assert: No validation error when calling clean
        try:
            superuser.full_clean()
        except ValidationError:
            self.fail("Superuser should not require school membership")

    def test_regular_user_without_school_fails_validation(self):
        """Test that regular users without school memberships fail validation"""
        # Arrange: Create user without school
        user = User.objects.create_user(**self.valid_user_data)

        # Act & Assert: User validation should fail
        with self.assertRaises(ValidationError) as context:
            user.full_clean()

        self.assertIn("must have at least one active school membership", str(context.exception))

    def test_user_with_inactive_membership_fails_validation(self):
        """Test that users with only inactive memberships fail validation"""
        # Arrange: Create user with school, then deactivate membership
        user = User.objects.create_user(**self.valid_user_data)
        school = create_user_school_and_membership(user, self.valid_school_name)

        # Deactivate the membership
        membership = SchoolMembership.objects.get(user=user, school=school)
        membership.is_active = False
        membership.save()

        # Act & Assert: User validation should fail
        with self.assertRaises(ValidationError) as context:
            user.full_clean()

        self.assertIn("must have at least one active school membership", str(context.exception))

    def test_cannot_deactivate_last_active_membership(self):
        """Test that the last active membership cannot be deactivated"""
        # Arrange: Create user with single school membership
        user = User.objects.create_user(**self.valid_user_data)
        school = create_user_school_and_membership(user, self.valid_school_name)
        membership = SchoolMembership.objects.get(user=user, school=school)

        # Act: Try to deactivate the only membership
        membership.is_active = False

        # Assert: Should fail validation
        with self.assertRaises(ValidationError) as context:
            membership.full_clean()

        self.assertIn("Cannot deactivate the last active school membership", str(context.exception))

    def test_cannot_delete_last_active_membership(self):
        """Test that the last active membership cannot be deleted"""
        # Arrange: Create user with single school membership
        user = User.objects.create_user(**self.valid_user_data)
        school = create_user_school_and_membership(user, self.valid_school_name)
        membership = SchoolMembership.objects.get(user=user, school=school)

        # Act & Assert: Should fail to delete
        with self.assertRaises(ValidationError) as context:
            membership.delete()

        self.assertIn("Cannot delete the last active school membership", str(context.exception))

    def test_can_deactivate_non_last_membership(self):
        """Test that non-last memberships can be deactivated"""
        # Arrange: Create user with two school memberships
        user = User.objects.create_user(**self.valid_user_data)
        school1 = create_user_school_and_membership(user, "School 1")

        # Create second school and membership
        school2 = School.objects.create(name="School 2", contact_email=user.email)
        membership2 = SchoolMembership.objects.create(
            user=user, school=school2, role=SchoolRole.TEACHER, is_active=True
        )

        # Act: Deactivate one membership (not the last one)
        membership2.is_active = False
        membership2.save()

        # Assert: User still has one active membership
        active_memberships = user.school_memberships.filter(is_active=True)
        self.assertEqual(active_memberships.count(), 1)
        self.assertEqual(active_memberships.first().school, school1)

    def test_can_delete_non_last_membership(self):
        """Test that non-last memberships can be deleted"""
        # Arrange: Create user with two school memberships
        user = User.objects.create_user(**self.valid_user_data)
        school1 = create_user_school_and_membership(user, "School 1")

        # Create second school and membership
        school2 = School.objects.create(name="School 2", contact_email=user.email)
        membership2 = SchoolMembership.objects.create(
            user=user, school=school2, role=SchoolRole.TEACHER, is_active=True
        )

        # Act: Delete one membership (not the last one)
        membership2.delete()

        # Assert: User still has one active membership
        active_memberships = user.school_memberships.filter(is_active=True)
        self.assertEqual(active_memberships.count(), 1)
        self.assertEqual(active_memberships.first().school, school1)

    def test_superuser_can_deactivate_all_memberships(self):
        """Test that superusers can deactivate all their memberships"""
        # Arrange: Create superuser with school membership
        superuser = User.objects.create_superuser(
            email="admin@example.com", password=get_test_password(), name="Admin User"
        )
        school = create_user_school_and_membership(superuser, "Admin School")
        membership = SchoolMembership.objects.get(user=superuser, school=school)

        # Act: Deactivate membership (should be allowed for superuser)
        membership.is_active = False
        membership.save()  # Should not raise ValidationError

        # Assert: Membership was deactivated
        self.assertFalse(membership.is_active)
        active_memberships = superuser.school_memberships.filter(is_active=True)
        self.assertEqual(active_memberships.count(), 0)

    def test_superuser_can_delete_all_memberships(self):
        """Test that superusers can delete all their memberships"""
        # Arrange: Create superuser with school membership
        superuser = User.objects.create_superuser(
            email="admin@example.com", password=get_test_password(), name="Admin User"
        )
        school = create_user_school_and_membership(superuser, "Admin School")
        membership = SchoolMembership.objects.get(user=superuser, school=school)

        # Act: Delete membership (should be allowed for superuser)
        membership.delete()  # Should not raise ValidationError

        # Assert: Membership was deleted
        memberships = superuser.school_memberships.all()
        self.assertEqual(memberships.count(), 0)

    def test_create_user_school_with_custom_school_name(self):
        """Test creating user and school with custom name from form"""
        # Arrange
        custom_school_name = "My Amazing Tutoring Practice"
        user = User.objects.create_user(**self.valid_user_data)

        # Act
        school = create_user_school_and_membership(user, custom_school_name)

        # Assert: School created with exact name provided
        self.assertEqual(school.name, custom_school_name)
        self.assertNotEqual(school.name, f"{user.first_name}'s School")  # Not auto-generated

    def test_create_user_school_preserves_user_data(self):
        """Test that school creation preserves all user data correctly"""
        # Arrange
        user = User.objects.create_user(**self.valid_user_data)

        # Act
        school = create_user_school_and_membership(user, self.valid_school_name)

        # Assert: User data preserved
        refreshed_user = User.objects.get(id=user.id)
        self.assertEqual(refreshed_user.email, self.valid_user_data["email"])
        self.assertEqual(refreshed_user.name, self.valid_user_data["name"])
        self.assertEqual(refreshed_user.first_name, self.valid_user_data["first_name"])
        self.assertEqual(refreshed_user.phone_number, self.valid_user_data["phone_number"])

        # Assert: School references user correctly
        self.assertEqual(school.contact_email, user.email)
        self.assertIn(user.first_name or user.email, school.description)
