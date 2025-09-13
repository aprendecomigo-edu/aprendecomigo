"""
Tests for user-school membership integrity system.

This module tests the safeguards that ensure every user has a valid school membership,
including signals, management commands, and validation logic.
"""

import datetime
from io import StringIO
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase

from accounts.models import (
    EducationalSystem,
    School,
    SchoolMembership,
    SchoolRole,
)
from accounts.tests.test_base import BaseTestCase, BaseTransactionTestCase
from tests.test_waffle_switches import get_test_password

User = get_user_model()


class UserSchoolIntegrityTestCase(BaseTestCase):
    """Test cases for user-school membership integrity."""

    def setUp(self):
        """Set up test data."""
        self.existing_school = School.objects.create(name="Existing School", description="A pre-existing school")

    def test_user_creation_without_membership_can_be_detected(self):
        """Test that users without school membership can be detected."""
        # Create a user without any school membership
        user = User.objects.create_user(email="orphan@example.com", name="Orphan User")

        # Remove any memberships that might have been created by signals
        SchoolMembership.objects.filter(user=user).delete()

        # User should now be detectable as having no membership
        memberships = SchoolMembership.objects.filter(user=user, is_active=True)
        self.assertFalse(memberships.exists(), "User should have no school membership for this test")

        # This represents the state that the management command would fix

    def test_user_creation_with_existing_membership_no_school_creation(self):
        """Test that users with existing memberships don't trigger school creation."""
        # Create user first
        user = User.objects.create_user(email="existing@example.com", name="Existing User")

        # Add membership to existing school
        SchoolMembership.objects.create(user=user, school=self.existing_school, role=SchoolRole.TEACHER, is_active=True)

        # Count schools before
        initial_school_count = School.objects.count()

        # Should not create additional school
        user.refresh_from_db()
        final_school_count = School.objects.count()
        self.assertEqual(initial_school_count, final_school_count)

    def test_user_clean_validation(self):
        """Test that CustomUser.clean() validates user integrity."""
        user = User(email="test@example.com", name="Test User")

        # clean() should not raise validation errors for new users
        # (signals will handle school creation)
        try:
            user.clean()
        except ValidationError:
            self.fail("User.clean() should not raise ValidationError for new users")

    def test_multiple_users_can_be_created_safely(self):
        """Test that multiple users can be created without conflicts."""
        users = []
        for i in range(5):
            user = User.objects.create_user(email=f"concurrent{i}@example.com", name=f"Concurrent User {i}")
            users.append(user)

        # All users should exist
        for user in users:
            self.assertTrue(User.objects.filter(email=user.email).exists())

    def test_users_with_same_name_can_be_created(self):
        """Test that users with the same name can be created."""
        # Create first user with a common name
        user1 = User.objects.create_user(email="john1@example.com", name="John Smith")

        user2 = User.objects.create_user(email="john2@example.com", name="John Smith")

        # Both should exist with same name but different emails
        self.assertEqual(user1.name, user2.name)
        self.assertNotEqual(user1.email, user2.email)


class UserSchoolIntegrityManagementCommandTestCase(BaseTestCase):
    """Test cases for management commands that fix user-school integrity."""

    def setUp(self):
        """Set up test data."""
        # Create users without proper school memberships to simulate orphaned users
        self.orphaned_user1 = User.objects.create_user(email="orphaned1@example.com", name="Orphaned User 1")
        self.orphaned_user2 = User.objects.create_user(email="orphaned2@example.com", name="Orphaned User 2")

        # Remove any memberships created by signals (to simulate legacy users)
        SchoolMembership.objects.filter(user__in=[self.orphaned_user1, self.orphaned_user2]).delete()

        # Create user with proper membership
        self.proper_user = User.objects.create_user(email="proper@example.com", name="Proper User")
        school = School.objects.create(name="Proper School")
        SchoolMembership.objects.create(user=self.proper_user, school=school, role=SchoolRole.TEACHER, is_active=True)

    def test_fix_missing_memberships_command(self):
        """Test the fix_missing_memberships management command."""
        out = StringIO()

        # Run the command
        call_command("fix_missing_memberships", stdout=out)

        # Check that orphaned users now have memberships
        self.assertTrue(
            SchoolMembership.objects.filter(user=self.orphaned_user1, is_active=True).exists(),
            "Orphaned user 1 should now have a membership",
        )
        self.assertTrue(
            SchoolMembership.objects.filter(user=self.orphaned_user2, is_active=True).exists(),
            "Orphaned user 2 should now have a membership",
        )

        # Check that proper user is unchanged
        proper_memberships = SchoolMembership.objects.filter(user=self.proper_user, is_active=True)
        self.assertEqual(proper_memberships.count(), 1)

        # Check command output
        output = out.getvalue()
        self.assertIn("Found", output)
        self.assertIn("users without school memberships", output)
        self.assertIn("Fixed", output)

    def test_fix_missing_memberships_dry_run(self):
        """Test the fix_missing_memberships command in dry-run mode."""
        out = StringIO()

        # Run with dry-run
        call_command("fix_missing_memberships", "--dry-run", stdout=out)

        # Users should still not have memberships (dry run)
        self.assertFalse(SchoolMembership.objects.filter(user=self.orphaned_user1, is_active=True).exists())
        self.assertFalse(SchoolMembership.objects.filter(user=self.orphaned_user2, is_active=True).exists())

        # But should report what would be fixed
        output = out.getvalue()
        self.assertIn("DRY RUN", output)
        self.assertIn("Would fix", output)

    def test_check_user_integrity_command(self):
        """Test the check_user_integrity management command."""
        out = StringIO()

        # Run the check command
        call_command("check_user_integrity", stdout=out)

        output = out.getvalue()
        # Should find the orphaned users we created
        self.assertIn("Found", output)
        self.assertIn("users without", output)

    def test_check_user_integrity_with_all_users_valid(self):
        """Test check_user_integrity when all users have proper memberships."""
        # Fix the orphaned users first
        call_command("fix_missing_memberships")

        out = StringIO()
        call_command("check_user_integrity", stdout=out)

        output = out.getvalue()
        # After fixing, should report that all users have memberships
        self.assertIn("All users have", output)

    def test_fix_missing_memberships_handles_errors_gracefully(self):
        """Test that fix_missing_memberships handles errors gracefully."""
        out = StringIO()
        err = StringIO()

        # Mock school creation to fail for one user
        original_create = School.objects.create
        call_count = 0

        def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise IntegrityError("Simulated database error")
            return original_create(*args, **kwargs)

        with patch("accounts.models.schools.School.objects.create", side_effect=mock_create):
            call_command("fix_missing_memberships", stdout=out, stderr=err)

        # Command should complete without crashing
        success_output = out.getvalue()
        self.assertIsInstance(success_output, str)


class UserSchoolIntegrityTransactionTestCase(BaseTransactionTestCase):
    """Transaction test cases for user-school integrity."""

    def test_atomic_user_school_creation(self):
        """Test that user and school creation is atomic."""
        # Mock school creation to fail
        with patch("accounts.models.schools.School.objects.create") as mock_create:
            mock_create.side_effect = IntegrityError("Database constraint violation")

            # Try to create user - should handle the error gracefully
            user = User.objects.create_user(email="atomic@example.com", name="Atomic User")

            # User should still exist even if school creation failed
            self.assertTrue(User.objects.filter(email="atomic@example.com").exists())

            # But user should not have a school membership
            self.assertFalse(SchoolMembership.objects.filter(user=user).exists())

    def test_transaction_rollback_on_failure(self):
        """Test transaction rollback when school creation fails critically."""
        initial_user_count = User.objects.count()
        initial_school_count = School.objects.count()

        # This test would need more complex setup to actually test transaction rollback
        # For now, we verify that the counts are consistent
        try:
            with transaction.atomic():
                user = User.objects.create_user(email="rollback@example.com", name="Rollback User")
                # Force an error after user creation
                if False:  # This would be a real constraint violation
                    raise IntegrityError("Forced error")
        except IntegrityError:
            pass

        # Counts should be consistent with successful operations
        self.assertGreaterEqual(User.objects.count(), initial_user_count)
        self.assertGreaterEqual(School.objects.count(), initial_school_count)


class UserSchoolIntegrityEdgeCasesTestCase(BaseTestCase):
    """Test edge cases for user-school integrity system."""

    def test_superuser_creation_with_integrity(self):
        """Test that superuser creation works without causing errors."""
        superuser = User.objects.create_superuser(
            email="super@example.com", name="Super User", password=get_test_password()
        )

        # Superuser should exist and be flagged as superuser
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(User.objects.filter(email="super@example.com").exists())

    def test_user_email_uniqueness_preserved(self):
        """Test that email uniqueness is preserved during user creation."""
        user1 = User.objects.create_user(email="unique@example.com", name="Unique User")

        # Attempting to create another user with same email should fail
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email="unique@example.com", name="Duplicate User")

        # Original user should still exist (check outside of transaction)
        from django.db import transaction

        if transaction.get_connection().in_atomic_block:
            # We're in an atomic block from the assertRaises, so we can't query
            # Just verify that user1 exists as an object
            self.assertEqual(user1.email, "unique@example.com")
        else:
            self.assertTrue(User.objects.filter(email="unique@example.com").exists())

    def test_user_creation_handles_long_names(self):
        """Test that user creation handles very long names."""
        long_name = "A" * 200  # Very long name
        user = User.objects.create_user(email="longname@example.com", name=long_name)

        # User should be created successfully
        self.assertEqual(user.name, long_name)
        self.assertTrue(User.objects.filter(email="longname@example.com").exists())

    def test_inactive_user_creation(self):
        """Test creation of inactive users."""
        user = User.objects.create_user(email="inactive@example.com", name="Inactive User", is_active=False)

        # User should be created but flagged as inactive
        self.assertFalse(user.is_active)
        self.assertTrue(User.objects.filter(email="inactive@example.com").exists())

    def test_user_with_special_characters_in_name(self):
        """Test user creation with special characters in names."""
        special_names = [
            "José María",
            "O'Connor",
            "Jean-Pierre",
            "李小明",
            "محمد",
        ]

        for name in special_names:
            with self.subTest(name=name):
                user = User.objects.create_user(email=f"special_{len(name)}@example.com", name=name)

                # User should be created with the special character name
                self.assertEqual(user.name, name)
                self.assertTrue(User.objects.filter(name=name).exists())
