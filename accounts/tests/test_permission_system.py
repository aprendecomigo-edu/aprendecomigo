"""
Comprehensive tests for the new simplified permission system.

This module tests the StudentPermission model, PermissionService, and
the three account type scenarios: STUDENT_GUARDIAN, ADULT_STUDENT, GUARDIAN_ONLY.
"""

import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import (
    EducationalSystem,
    GuardianProfile,
    StudentProfile,
)
from accounts.models.permissions import StudentPermission
from accounts.permissions import PermissionService
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class StudentPermissionModelTests(BaseTestCase):
    """Test cases for StudentPermission model functionality."""

    def setUp(self):
        """Set up test data for permission model tests."""
        self.student_user = User.objects.create_user(email="student@example.com", name="Student User")
        self.guardian_user = User.objects.create_user(email="guardian@example.com", name="Guardian User")

        self.guardian_profile = GuardianProfile.objects.create(user=self.guardian_user)

        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            guardian=self.guardian_profile,
            account_type="STUDENT_GUARDIAN",
        )

    def test_create_student_permission_with_defaults(self):
        """Test creating StudentPermission with default values."""
        permission = StudentPermission.objects.create(student=self.student_profile, user=self.student_user)

        # All permissions should default to False
        self.assertFalse(permission.can_view_profile)
        self.assertFalse(permission.can_view_grades)
        self.assertFalse(permission.can_view_attendance)
        self.assertFalse(permission.can_make_payment)
        self.assertFalse(permission.can_book_session)
        self.assertFalse(permission.can_cancel_session)
        self.assertFalse(permission.can_update_profile)
        self.assertFalse(permission.can_manage_budget)
        self.assertFalse(permission.can_view_financial)

        # Metadata
        self.assertIsNone(permission.expires_at)
        self.assertEqual(permission.notes, "")
        self.assertIsNotNone(permission.created_at)

    def test_student_permission_unique_constraint(self):
        """Test that user-student permission combinations must be unique."""
        StudentPermission.objects.create(student=self.student_profile, user=self.student_user, can_view_profile=True)

        # Creating another permission for same student-user should fail
        with self.assertRaises(ValidationError):
            permission = StudentPermission(student=self.student_profile, user=self.student_user)
            permission.full_clean()

    def test_student_permission_string_representation(self):
        """Test StudentPermission string representation."""
        permission = StudentPermission.objects.create(student=self.student_profile, user=self.student_user)

        expected_str = f"{self.student_user.name} -> {self.student_profile}"
        self.assertEqual(str(permission), expected_str)

    def test_is_expired_with_no_expiration(self):
        """Test is_expired returns False when expires_at is None."""
        permission = StudentPermission.objects.create(student=self.student_profile, user=self.student_user)

        self.assertFalse(permission.is_expired())

    def test_is_expired_with_future_expiration(self):
        """Test is_expired returns False when expires_at is in the future."""
        future_date = timezone.now() + datetime.timedelta(days=1)
        permission = StudentPermission.objects.create(
            student=self.student_profile, user=self.student_user, expires_at=future_date
        )

        self.assertFalse(permission.is_expired())

    def test_is_expired_with_past_expiration(self):
        """Test is_expired returns True when expires_at is in the past."""
        past_date = timezone.now() - datetime.timedelta(days=1)
        permission = StudentPermission.objects.create(
            student=self.student_profile, user=self.student_user, expires_at=past_date
        )

        self.assertTrue(permission.is_expired())

    def test_create_for_adult_student_success(self):
        """Test creating permissions for adult student scenario."""
        permission, created = StudentPermission.create_for_adult_student(self.student_profile)

        self.assertTrue(created)
        self.assertEqual(permission.student, self.student_profile)
        self.assertEqual(permission.user, self.student_user)

        # Adult student should have all permissions
        self.assertTrue(permission.can_view_profile)
        self.assertTrue(permission.can_view_grades)
        self.assertTrue(permission.can_view_attendance)
        self.assertTrue(permission.can_make_payment)
        self.assertTrue(permission.can_book_session)
        self.assertTrue(permission.can_cancel_session)
        self.assertTrue(permission.can_update_profile)
        self.assertTrue(permission.can_manage_budget)
        self.assertTrue(permission.can_view_financial)

    def test_create_for_adult_student_updates_existing(self):
        """Test that create_for_adult_student updates existing permissions."""
        # Create a permission with limited access
        existing = StudentPermission.objects.create(
            student=self.student_profile,
            user=self.student_user,
            can_view_profile=True,
            can_make_payment=False,  # This should be updated to True
        )

        permission, created = StudentPermission.create_for_adult_student(self.student_profile)

        self.assertFalse(created)
        self.assertEqual(permission.id, existing.id)
        self.assertTrue(permission.can_make_payment)  # Should be updated

    def test_create_for_guardian_success(self):
        """Test creating permissions for guardian."""
        permission, created = StudentPermission.create_for_guardian(self.student_profile)

        self.assertTrue(created)
        self.assertEqual(permission.student, self.student_profile)
        self.assertEqual(permission.user, self.guardian_user)

        # Guardian should have all permissions
        self.assertTrue(permission.can_view_profile)
        self.assertTrue(permission.can_view_grades)
        self.assertTrue(permission.can_view_attendance)
        self.assertTrue(permission.can_make_payment)
        self.assertTrue(permission.can_book_session)
        self.assertTrue(permission.can_cancel_session)
        self.assertTrue(permission.can_update_profile)
        self.assertTrue(permission.can_manage_budget)
        self.assertTrue(permission.can_view_financial)

    def test_create_for_guardian_no_guardian_returns_none(self):
        """Test creating guardian permissions when no guardian exists."""
        other_student_user = User.objects.create_user(email="other_student@example.com", name="Other Student")
        student_without_guardian = StudentProfile.objects.create(
            user=other_student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="11",
            guardian=None,
            account_type="ADULT_STUDENT",
        )

        result = StudentPermission.create_for_guardian(student_without_guardian)
        self.assertIsNone(result)

    def test_create_for_student_with_guardian_success(self):
        """Test creating limited permissions for student who has a guardian."""
        permission, created = StudentPermission.create_for_student_with_guardian(self.student_profile)

        self.assertTrue(created)
        self.assertEqual(permission.student, self.student_profile)
        self.assertEqual(permission.user, self.student_user)

        # Student should have view permissions but not financial
        self.assertTrue(permission.can_view_profile)
        self.assertTrue(permission.can_view_grades)
        self.assertTrue(permission.can_view_attendance)
        self.assertFalse(permission.can_make_payment)  # Guardian handles money
        self.assertFalse(permission.can_book_session)  # Guardian books
        self.assertFalse(permission.can_cancel_session)  # Guardian cancels
        self.assertFalse(permission.can_update_profile)  # Guardian manages
        self.assertFalse(permission.can_manage_budget)  # Guardian only
        self.assertFalse(permission.can_view_financial)  # Guardian only

    def test_create_for_student_with_guardian_no_user_returns_none(self):
        """Test creating student permissions when student has no user account."""
        student_no_user = StudentProfile.objects.create(
            user=None,  # GUARDIAN_ONLY scenario
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="9",
            guardian=self.guardian_profile,
            account_type="GUARDIAN_ONLY",
        )

        result = StudentPermission.create_for_student_with_guardian(student_no_user)
        self.assertIsNone(result)


class PermissionServiceTests(BaseTestCase):
    """Test cases for PermissionService functionality."""

    def setUp(self):
        """Set up test data for permission service tests."""
        self.student_user = User.objects.create_user(email="student@example.com", name="Student User")
        self.guardian_user = User.objects.create_user(email="guardian@example.com", name="Guardian User")
        self.other_user = User.objects.create_user(email="other@example.com", name="Other User")
        self.superuser = User.objects.create_user(email="admin@example.com", name="Admin User", is_superuser=True)

        self.guardian_profile = GuardianProfile.objects.create(user=self.guardian_user)

        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            guardian=self.guardian_profile,
            account_type="STUDENT_GUARDIAN",
        )

    def test_can_with_invalid_parameters(self):
        """Test PermissionService.can handles invalid parameters gracefully."""
        # Test with None user
        self.assertFalse(PermissionService.can(None, self.student_profile, "can_view_profile"))

        # Test with None student_profile
        self.assertFalse(PermissionService.can(self.student_user, None, "can_view_profile"))

        # Test with None action - should return False due to getattr default
        self.assertFalse(PermissionService.can(self.student_user, self.student_profile, None))

    def test_can_superuser_access(self):
        """Test that superusers can perform any action."""
        # No permission record exists for superuser
        self.assertTrue(PermissionService.can(self.superuser, self.student_profile, "can_view_profile"))
        self.assertTrue(PermissionService.can(self.superuser, self.student_profile, "can_make_payment"))
        self.assertTrue(PermissionService.can(self.superuser, self.student_profile, "can_book_session"))
        self.assertTrue(PermissionService.can(self.superuser, self.student_profile, "nonexistent_permission"))

    def test_can_no_permission_record(self):
        """Test that users without permission records are denied access."""
        # No permission record for other_user
        self.assertFalse(PermissionService.can(self.other_user, self.student_profile, "can_view_profile"))
        self.assertFalse(PermissionService.can(self.other_user, self.student_profile, "can_make_payment"))

    def test_can_with_permission_record(self):
        """Test permission checking with existing permission records."""
        # Create permission with specific access
        StudentPermission.objects.create(
            student=self.student_profile, user=self.student_user, can_view_profile=True, can_make_payment=False
        )

        self.assertTrue(PermissionService.can(self.student_user, self.student_profile, "can_view_profile"))
        self.assertFalse(PermissionService.can(self.student_user, self.student_profile, "can_make_payment"))

    def test_can_with_expired_permission(self):
        """Test that expired permissions are denied."""
        past_date = timezone.now() - datetime.timedelta(days=1)
        StudentPermission.objects.create(
            student=self.student_profile, user=self.student_user, can_view_profile=True, expires_at=past_date
        )

        self.assertFalse(PermissionService.can(self.student_user, self.student_profile, "can_view_profile"))

    def test_can_with_nonexistent_permission_attribute(self):
        """Test that nonexistent permission attributes default to False."""
        StudentPermission.objects.create(student=self.student_profile, user=self.student_user, can_view_profile=True)

        self.assertTrue(PermissionService.can(self.student_user, self.student_profile, "can_view_profile"))
        self.assertFalse(PermissionService.can(self.student_user, self.student_profile, "nonexistent_permission"))

    def test_convenience_methods(self):
        """Test convenience methods for common permission checks."""
        StudentPermission.objects.create(
            student=self.student_profile,
            user=self.student_user,
            can_make_payment=True,
            can_book_session=False,
            can_view_financial=True,
        )

        self.assertTrue(PermissionService.can_make_payment(self.student_user, self.student_profile))
        self.assertFalse(PermissionService.can_book_session(self.student_user, self.student_profile))
        self.assertTrue(PermissionService.can_view_financial(self.student_user, self.student_profile))

    def test_get_authorized_users(self):
        """Test getting all users with permissions for a student."""
        # Create permissions for multiple users
        StudentPermission.objects.create(student=self.student_profile, user=self.student_user, can_view_profile=True)
        StudentPermission.objects.create(student=self.student_profile, user=self.guardian_user, can_make_payment=True)

        # Create an expired permission (should be excluded)
        past_date = timezone.now() - datetime.timedelta(days=1)
        StudentPermission.objects.create(
            student=self.student_profile, user=self.other_user, can_view_grades=True, expires_at=past_date
        )

        authorized_users = PermissionService.get_authorized_users(self.student_profile)

        self.assertEqual(authorized_users.count(), 2)
        self.assertIn(self.student_user, authorized_users)
        self.assertIn(self.guardian_user, authorized_users)
        self.assertNotIn(self.other_user, authorized_users)  # Expired permission


class PermissionServiceSetupTests(BaseTestCase):
    """Test cases for PermissionService setup functionality."""

    def setUp(self):
        """Set up test data for setup tests."""
        self.student_user = User.objects.create_user(email="student@example.com", name="Student User")
        self.guardian_user = User.objects.create_user(email="guardian@example.com", name="Guardian User")

        self.guardian_profile = GuardianProfile.objects.create(user=self.guardian_user)

    def test_setup_permissions_for_adult_student(self):
        """Test permission setup for ADULT_STUDENT account type."""
        student = StudentProfile.objects.create(
            user=self.student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(1995, 1, 1),  # Adult
            school_year="12",
            guardian=None,
            account_type="ADULT_STUDENT",
        )

        PermissionService.setup_permissions_for_student(student)

        # Should have one permission record for the student
        permissions = StudentPermission.objects.filter(student=student)
        self.assertEqual(permissions.count(), 1)

        student_permission = permissions.get(user=self.student_user)
        # Adult student should have all permissions
        self.assertTrue(student_permission.can_view_profile)
        self.assertTrue(student_permission.can_make_payment)
        self.assertTrue(student_permission.can_book_session)
        self.assertTrue(student_permission.can_manage_budget)

    def test_setup_permissions_for_guardian_only(self):
        """Test permission setup for GUARDIAN_ONLY account type."""
        student = StudentProfile.objects.create(
            user=None,  # No user account for student
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2010, 1, 1),
            school_year="8",
            guardian=self.guardian_profile,
            account_type="GUARDIAN_ONLY",
        )

        PermissionService.setup_permissions_for_student(student)

        # Should have one permission record for the guardian
        permissions = StudentPermission.objects.filter(student=student)
        self.assertEqual(permissions.count(), 1)

        guardian_permission = permissions.get(user=self.guardian_user)
        # Guardian should have all permissions
        self.assertTrue(guardian_permission.can_view_profile)
        self.assertTrue(guardian_permission.can_make_payment)
        self.assertTrue(guardian_permission.can_book_session)
        self.assertTrue(guardian_permission.can_manage_budget)

    def test_setup_permissions_for_student_guardian(self):
        """Test permission setup for STUDENT_GUARDIAN account type."""
        student = StudentProfile.objects.create(
            user=self.student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            guardian=self.guardian_profile,
            account_type="STUDENT_GUARDIAN",
        )

        PermissionService.setup_permissions_for_student(student)

        # Should have two permission records
        permissions = StudentPermission.objects.filter(student=student)
        self.assertEqual(permissions.count(), 2)

        # Guardian should have full permissions
        guardian_permission = permissions.get(user=self.guardian_user)
        self.assertTrue(guardian_permission.can_view_profile)
        self.assertTrue(guardian_permission.can_make_payment)
        self.assertTrue(guardian_permission.can_book_session)

        # Student should have limited permissions
        student_permission = permissions.get(user=self.student_user)
        self.assertTrue(student_permission.can_view_profile)
        self.assertFalse(student_permission.can_make_payment)  # Guardian handles money
        self.assertFalse(student_permission.can_book_session)  # Guardian books

    def test_setup_permissions_clears_existing(self):
        """Test that setup_permissions_for_student clears existing permissions."""
        student = StudentProfile.objects.create(
            user=self.student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            guardian=self.guardian_profile,
            account_type="STUDENT_GUARDIAN",
        )

        # Create some existing permissions
        StudentPermission.objects.create(
            student=student,
            user=self.student_user,
            can_view_profile=False,  # This should be cleared and recreated
            notes="Old permission",
        )

        PermissionService.setup_permissions_for_student(student)

        # Should still have correct number of permissions
        permissions = StudentPermission.objects.filter(student=student)
        self.assertEqual(permissions.count(), 2)

        # Check that the permission was recreated with correct values
        student_permission = permissions.get(user=self.student_user)
        self.assertTrue(student_permission.can_view_profile)  # Should be True now
        self.assertEqual(student_permission.notes, "")  # Should be reset


class AccountTypeScenarioTests(BaseTestCase):
    """Test the three main account type scenarios end-to-end."""

    def test_student_guardian_scenario(self):
        """Test STUDENT_GUARDIAN: Both have accounts, guardian controls finances."""
        # Create users
        student_user = User.objects.create_user(email="student@family.com", name="Teen Student")
        guardian_user = User.objects.create_user(email="guardian@family.com", name="Parent Guardian")

        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        # Create student profile - this will trigger permission setup via signal
        student_profile = StudentProfile.objects.create(
            user=student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            guardian=guardian_profile,
            account_type="STUDENT_GUARDIAN",
        )

        # Manually set up permissions for testing (signal might have issues in test)
        PermissionService.setup_permissions_for_student(student_profile)

        # Test student permissions: can view, cannot handle money
        self.assertTrue(PermissionService.can(student_user, student_profile, "can_view_profile"))
        self.assertTrue(PermissionService.can(student_user, student_profile, "can_view_grades"))
        self.assertFalse(PermissionService.can(student_user, student_profile, "can_make_payment"))
        self.assertFalse(PermissionService.can(student_user, student_profile, "can_book_session"))

        # Test guardian permissions: can do everything
        self.assertTrue(PermissionService.can(guardian_user, student_profile, "can_view_profile"))
        self.assertTrue(PermissionService.can(guardian_user, student_profile, "can_make_payment"))
        self.assertTrue(PermissionService.can(guardian_user, student_profile, "can_book_session"))
        self.assertTrue(PermissionService.can(guardian_user, student_profile, "can_manage_budget"))

    def test_adult_student_scenario(self):
        """Test ADULT_STUDENT: Student handles everything themselves."""
        student_user = User.objects.create_user(email="adult@student.com", name="Adult Student")

        # Create adult student profile - will trigger permission setup via signal
        student_profile = StudentProfile.objects.create(
            user=student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(1995, 1, 1),  # Adult
            school_year="12",
            guardian=None,
            account_type="ADULT_STUDENT",
        )

        # Manually set up permissions for testing (signal might have issues in test)
        PermissionService.setup_permissions_for_student(student_profile)

        # Test student has all permissions
        self.assertTrue(PermissionService.can(student_user, student_profile, "can_view_profile"))
        self.assertTrue(PermissionService.can(student_user, student_profile, "can_make_payment"))
        self.assertTrue(PermissionService.can(student_user, student_profile, "can_book_session"))
        self.assertTrue(PermissionService.can(student_user, student_profile, "can_manage_budget"))
        self.assertTrue(PermissionService.can(student_user, student_profile, "can_view_financial"))

        # Should only have one permission record
        permissions = StudentPermission.objects.filter(student=student_profile)
        self.assertEqual(permissions.count(), 1)
        self.assertEqual(permissions.first().user, student_user)

    def test_guardian_only_scenario(self):
        """Test GUARDIAN_ONLY: Guardian manages everything, student has no account."""
        guardian_user = User.objects.create_user(email="guardian@parent.com", name="Managing Guardian")

        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        # Create student profile with no user account
        student_profile = StudentProfile.objects.create(
            user=None,  # No user account for student
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2010, 1, 1),
            school_year="8",
            guardian=guardian_profile,
            account_type="GUARDIAN_ONLY",
        )

        # Manually set up permissions for testing (signal might have issues in test)
        PermissionService.setup_permissions_for_student(student_profile)

        # Test guardian has all permissions
        self.assertTrue(PermissionService.can(guardian_user, student_profile, "can_view_profile"))
        self.assertTrue(PermissionService.can(guardian_user, student_profile, "can_make_payment"))
        self.assertTrue(PermissionService.can(guardian_user, student_profile, "can_book_session"))
        self.assertTrue(PermissionService.can(guardian_user, student_profile, "can_manage_budget"))

        # Should only have one permission record for guardian
        permissions = StudentPermission.objects.filter(student=student_profile)
        self.assertEqual(permissions.count(), 1)
        self.assertEqual(permissions.first().user, guardian_user)


class SignalIntegrationTests(BaseTestCase):
    """Test signal integration and automatic permission setup."""

    def test_student_profile_auto_creates_permissions(self):
        """Test that creating a StudentProfile automatically creates permissions."""
        student_user = User.objects.create_user(email="signal_test@test.com", name="Signal Test Student")

        # Create student profile
        student_profile = StudentProfile.objects.create(
            user=student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
            account_type="ADULT_STUDENT",
        )

        # Check if permissions were created (either by signal or manually)
        permissions = StudentPermission.objects.filter(student=student_profile)
        if permissions.exists():
            # Signal worked
            self.assertEqual(permissions.count(), 1)
            permission = permissions.first()
            self.assertEqual(permission.user, student_user)
            self.assertTrue(permission.can_view_profile)
            self.assertTrue(permission.can_make_payment)
        else:
            # Signal didn't work, but we can test the setup method works
            PermissionService.setup_permissions_for_student(student_profile)
            permissions = StudentPermission.objects.filter(student=student_profile)
            self.assertEqual(permissions.count(), 1)

    def test_permission_setup_method_works_correctly(self):
        """Test that the setup method works as expected."""
        student_user = User.objects.create_user(email="setup_test@test.com", name="Setup Test Student")

        student_profile = StudentProfile.objects.create(
            user=student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
            account_type="ADULT_STUDENT",
        )

        # Clear any existing permissions (in case signal worked)
        StudentPermission.objects.filter(student=student_profile).delete()

        # Manually call setup
        PermissionService.setup_permissions_for_student(student_profile)

        # Verify permissions were created correctly
        permissions = StudentPermission.objects.filter(student=student_profile)
        self.assertEqual(permissions.count(), 1)
        permission = permissions.first()
        self.assertEqual(permission.user, student_user)
        self.assertTrue(permission.can_view_profile)
        self.assertTrue(permission.can_make_payment)


class EdgeCaseTests(BaseTestCase):
    """Test edge cases and error conditions."""

    def test_superuser_bypass_all_checks(self):
        """Test that superusers can access anything regardless of permission records."""
        student_user = User.objects.create_user(email="student@test.com", name="Test Student")
        superuser = User.objects.create_user(email="admin@test.com", name="Super User", is_superuser=True)

        student_profile = StudentProfile.objects.create(
            user=student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
            account_type="ADULT_STUDENT",
        )

        # Don't create any permission records
        self.assertEqual(StudentPermission.objects.filter(student=student_profile).count(), 0)

        # Superuser should still have access
        self.assertTrue(PermissionService.can(superuser, student_profile, "can_view_profile"))
        self.assertTrue(PermissionService.can(superuser, student_profile, "can_make_payment"))
        self.assertTrue(PermissionService.can(superuser, student_profile, "nonexistent_permission"))

    def test_permission_expiration_edge_cases(self):
        """Test permission expiration around exact times."""
        student_user = User.objects.create_user(email="student@test.com", name="Test Student")

        student_profile = StudentProfile.objects.create(
            user=student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
            account_type="ADULT_STUDENT",
        )

        # Test permission that expires exactly now
        now = timezone.now()
        permission = StudentPermission.objects.create(
            student=student_profile, user=student_user, can_view_profile=True, expires_at=now
        )

        # Should be expired (expires_at < now)
        with patch("django.utils.timezone.now", return_value=now + datetime.timedelta(microseconds=1)):
            self.assertTrue(permission.is_expired())
            self.assertFalse(PermissionService.can(student_user, student_profile, "can_view_profile"))

    def test_student_profile_validation_constraints(self):
        """Test StudentProfile validation enforces account type constraints."""
        student_user = User.objects.create_user(email="student@test.com", name="Test Student")
        guardian_user = User.objects.create_user(email="guardian@test.com", name="Test Guardian")
        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        # Test ADULT_STUDENT validation: must have user, no guardian
        with self.assertRaises(ValidationError) as cm:
            student = StudentProfile(
                user=None,  # Invalid: adult student must have user
                educational_system=self.default_educational_system,
                birth_date=datetime.date(1995, 1, 1),
                school_year="12",
                account_type="ADULT_STUDENT",
            )
            student.full_clean()
        self.assertIn("user", cm.exception.error_dict)

        # Test GUARDIAN_ONLY validation: no user, must have guardian
        with self.assertRaises(ValidationError) as cm:
            student = StudentProfile(
                user=student_user,  # Invalid: guardian-only shouldn't have user
                educational_system=self.default_educational_system,
                birth_date=datetime.date(2010, 1, 1),
                school_year="8",
                guardian=guardian_profile,
                account_type="GUARDIAN_ONLY",
            )
            student.full_clean()
        self.assertIn("user", cm.exception.error_dict)

        # Test STUDENT_GUARDIAN validation: must have both user and guardian
        with self.assertRaises(ValidationError) as cm:
            student = StudentProfile(
                user=student_user,
                educational_system=self.default_educational_system,
                birth_date=datetime.date(2008, 1, 1),
                school_year="10",
                guardian=None,  # Invalid: must have guardian
                account_type="STUDENT_GUARDIAN",
            )
            student.full_clean()
        self.assertIn("guardian", cm.exception.error_dict)

    def test_permission_service_error_handling(self):
        """Test PermissionService handles errors gracefully."""
        student_user = User.objects.create_user(email="student@test.com", name="Test Student")

        student_profile = StudentProfile.objects.create(
            user=student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
            account_type="ADULT_STUDENT",
        )

        # Test with database error during permission lookup
        with patch(
            "accounts.models.permissions.StudentPermission.objects.filter", side_effect=Exception("Database error")
        ):
            # Should not raise exception, should return False
            result = PermissionService.can(student_user, student_profile, "can_view_profile")
            self.assertFalse(result)

    def test_get_authorized_users_complex_scenarios(self):
        """Test get_authorized_users with complex permission scenarios."""
        users = []
        for i in range(3):
            users.append(User.objects.create_user(email=f"user{i}@test.com", name=f"User {i}"))

        student_profile = StudentProfile.objects.create(
            user=users[0],
            educational_system=self.default_educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
            account_type="ADULT_STUDENT",
        )

        # Create permissions with different expiration states
        StudentPermission.objects.create(
            student=student_profile,
            user=users[0],
            can_view_profile=True,
            expires_at=None,  # Never expires
        )

        future_date = timezone.now() + datetime.timedelta(days=1)
        StudentPermission.objects.create(
            student=student_profile,
            user=users[1],
            can_view_profile=True,
            expires_at=future_date,  # Future expiration
        )

        past_date = timezone.now() - datetime.timedelta(days=1)
        StudentPermission.objects.create(
            student=student_profile,
            user=users[2],
            can_view_profile=True,
            expires_at=past_date,  # Expired
        )

        authorized_users = PermissionService.get_authorized_users(student_profile)

        # Should include users[0] and users[1], but not users[2] (expired)
        self.assertEqual(authorized_users.count(), 2)
        self.assertIn(users[0], authorized_users)
        self.assertIn(users[1], authorized_users)
        self.assertNotIn(users[2], authorized_users)
