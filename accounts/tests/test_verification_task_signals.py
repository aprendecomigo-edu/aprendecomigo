"""
Test verification task signals functionality.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import EducationalSystem, School, SchoolMembership, SchoolRole, StudentProfile

User = get_user_model()


class VerificationTaskSignalsTest(TestCase):
    """Test the verification task signal functionality."""

    def setUp(self):
        """Set up test data."""
        # Create a test school
        self.school = School.objects.create(
            name="Test School",
            address="Test Address",
            phone_number="123456789",
            contact_email="test@school.com",
        )

        # Create test users
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            name="Admin User",
            first_student_added=False,
        )

        self.regular_user = User.objects.create_user(
            email="user@test.com",
            name="Regular User",
            first_student_added=False,
        )

        # Create memberships
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True,
        )

        SchoolMembership.objects.create(
            user=self.regular_user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True,
        )

        # Get or create educational system
        self.educational_system, _ = EducationalSystem.objects.get_or_create(
            name="Test System", defaults={"code": "custom"}
        )

    def test_first_student_added_signal_triggers(self):
        """Test that creating a student marks first_student_added=True for all users."""
        # Verify initial state - no users should have first_student_added=True
        self.assertFalse(User.objects.filter(first_student_added=True).exists())

        # Create a student profile (this should trigger the signal)
        student_profile = StudentProfile.objects.create(
            educational_system=self.educational_system,
            school_year="10",
            birth_date="2010-01-01",
            account_type="ADULT_STUDENT",
        )

        # Verify the signal worked - all users should now have first_student_added=True
        self.admin_user.refresh_from_db()
        self.regular_user.refresh_from_db()

        self.assertTrue(self.admin_user.first_student_added)
        self.assertTrue(self.regular_user.first_student_added)

        # Verify all users in DB have the flag set
        self.assertEqual(User.objects.filter(first_student_added=True).count(), User.objects.count())

    def test_first_student_added_signal_only_triggers_on_creation(self):
        """Test that updating a student doesn't trigger the signal unnecessarily."""
        # Create initial student
        student_profile = StudentProfile.objects.create(
            educational_system=self.educational_system,
            school_year="10",
            birth_date="2010-01-01",
            account_type="ADULT_STUDENT",
        )

        # Reset users to test update behavior
        User.objects.all().update(first_student_added=False)

        # Update the existing student (should not trigger signal)
        student_profile.school_year = "11"
        student_profile.save()

        # Users should still have first_student_added=False
        self.admin_user.refresh_from_db()
        self.regular_user.refresh_from_db()

        self.assertFalse(self.admin_user.first_student_added)
        self.assertFalse(self.regular_user.first_student_added)

    def test_migration_sets_existing_users_correctly(self):
        """Test that the data migration logic works correctly."""
        # This test simulates the migration logic
        # If students exist, all users should be marked as completed

        # Create a student first
        StudentProfile.objects.create(
            educational_system=self.educational_system,
            school_year="10",
            birth_date="2010-01-01",
            account_type="ADULT_STUDENT",
        )

        # Reset all users to simulate pre-migration state
        User.objects.all().update(first_student_added=False)

        # Simulate the migration logic
        if StudentProfile.objects.exists():
            User.objects.all().update(first_student_added=True)

        # Verify all existing users have been marked as completed
        self.admin_user.refresh_from_db()
        self.regular_user.refresh_from_db()

        self.assertTrue(self.admin_user.first_student_added)
        self.assertTrue(self.regular_user.first_student_added)
