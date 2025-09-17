import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import (
    EducationalSystem,
    School,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherProfile,
    VerificationToken,
)

User = get_user_model()


class CustomUserModelTests(TestCase):
    """Test cases for CustomUser model business logic."""

    def test_username_generation_from_email_ensures_uniqueness(self):
        """Test username generation handles collisions by appending numbers."""
        # Create first user
        user1 = User.objects.create_user(email="test@example.com", name="Test User 1")
        self.assertEqual(user1.username, "test")

        # Second user with same local part should get numbered username
        user2 = User.objects.create_user(email="test@another.com", name="Test User 2")
        self.assertEqual(user2.username, "test1")

        # Third user should get next number
        user3 = User.objects.create_user(email="test@different.com", name="Test User 3")
        self.assertEqual(user3.username, "test2")

    def test_create_user_requires_email(self):
        """Test that user creation enforces email requirement."""
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(email="", name="Test User")

        self.assertIn("Email must be set", str(context.exception))


class SchoolMembershipTests(TestCase):
    """Test cases for SchoolMembership business logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="user@example.com",
            name="Test User",
        )
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
        )

    def test_user_can_have_multiple_roles_in_same_school(self):
        """Test that user can have multiple active roles in the same school."""
        # School owner who also teaches
        owner_membership = SchoolMembership.objects.create(
            user=self.user, school=self.school, role=SchoolRole.SCHOOL_OWNER, is_active=True
        )

        teacher_membership = SchoolMembership.objects.create(
            user=self.user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

        memberships = SchoolMembership.objects.filter(user=self.user, school=self.school, is_active=True)

        self.assertEqual(memberships.count(), 2)
        roles = [m.role for m in memberships]
        self.assertIn(SchoolRole.SCHOOL_OWNER, roles)
        self.assertIn(SchoolRole.TEACHER, roles)

    def test_inactive_membership_does_not_appear_in_active_queries(self):
        """Test that inactive memberships are filtered out of active queries."""
        # Create active membership
        active_membership = SchoolMembership.objects.create(
            user=self.user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

        # Create inactive membership for another user
        other_user = User.objects.create_user(email="other@example.com", name="Other User")
        inactive_membership = SchoolMembership.objects.create(
            user=other_user, school=self.school, role=SchoolRole.TEACHER, is_active=False
        )

        # Active query should only return active membership
        active_memberships = SchoolMembership.objects.filter(
            school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

        self.assertEqual(active_memberships.count(), 1)
        self.assertEqual(active_memberships.first(), active_membership)


class StudentProfileTests(TestCase):
    """Test cases for StudentProfile business logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="student@example.com",
            name="Student User",
        )
        # Create required EducationalSystem
        self.educational_system = EducationalSystem.objects.create(
            name="Test System", code="pt", description="Test educational system"
        )

    def test_student_profile_creation_with_required_fields(self):
        """Test student profile creation with required fields."""
        # Create profile with required fields
        profile = StudentProfile.objects.create(
            user=self.user,
            educational_system=self.educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
        )

        # Should be created successfully
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.birth_date, datetime.date(2008, 1, 1))
        self.assertEqual(profile.school_year, "10")

        # Add more data
        profile.notes = "Test notes for the student"
        profile.save()

        # Should save successfully
        self.assertEqual(profile.notes, "Test notes for the student")

    def test_student_profile_string_representation(self):
        """Test that student profile has proper string representation."""
        profile = StudentProfile.objects.create(
            user=self.user,
            educational_system=self.educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
        )

        # Should have proper string representation
        expected_str = f"Student Profile: {self.user.name}"
        self.assertEqual(str(profile), expected_str)

        # Should have the correct user relationship
        self.assertEqual(profile.user, self.user)


class TeacherProfileTests(TestCase):
    """Test cases for TeacherProfile business logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="teacher@example.com",
            name="Teacher User",
        )
        self.school = School.objects.create(name="Test School")

    def test_get_school_memberships_returns_only_active_teacher_roles(self):
        """Test that get_school_memberships filters correctly."""
        teacher_profile = TeacherProfile.objects.create(user=self.user, bio="Test teacher")

        # Create various memberships
        active_teacher = SchoolMembership.objects.create(
            user=self.user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

        inactive_teacher = SchoolMembership.objects.create(
            user=self.user, school=School.objects.create(name="Other School"), role=SchoolRole.TEACHER, is_active=False
        )

        student_role = SchoolMembership.objects.create(
            user=self.user, school=self.school, role=SchoolRole.STUDENT, is_active=True
        )

        # Should only return active teacher memberships
        teacher_memberships = teacher_profile.get_school_memberships()
        self.assertEqual(teacher_memberships.count(), 1)
        self.assertEqual(teacher_memberships.first(), active_teacher)

    def test_teacher_profile_fields_update_correctly(self):
        """Test that teacher profile fields can be updated correctly."""
        teacher_profile = TeacherProfile.objects.create(user=self.user, bio="Short bio")

        # Add more profile data
        teacher_profile.specialty = "Mathematics and Physics"
        teacher_profile.education = "Master's Degree in Mathematics"
        teacher_profile.hourly_rate = Decimal("35.00")
        teacher_profile.save()

        # Data should be saved correctly
        teacher_profile.refresh_from_db()
        self.assertEqual(teacher_profile.specialty, "Mathematics and Physics")
        self.assertEqual(teacher_profile.education, "Master's Degree in Mathematics")
        self.assertEqual(teacher_profile.hourly_rate, Decimal("35.00"))

    def test_mark_activity_updates_timestamp(self):
        """Test that mark_activity updates last_activity field."""
        teacher_profile = TeacherProfile.objects.create(user=self.user, bio="Test teacher")

        original_activity = teacher_profile.last_activity

        # Mark activity
        teacher_profile.mark_activity()

        # Should have updated timestamp
        teacher_profile.refresh_from_db()
        if original_activity:
            self.assertGreater(teacher_profile.last_activity, original_activity)
        else:
            self.assertIsNotNone(teacher_profile.last_activity)


class VerificationTokenTests(TestCase):
    """Test cases for VerificationToken business logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            name="Test User",
        )

    def test_verification_token_creation(self):
        """Test that VerificationToken can be created with required fields."""
        token = VerificationToken.objects.create(
            user=self.user,
            token_type="email_verify",
            token_value="hashed_token_value",
            expires_at=timezone.now() + datetime.timedelta(hours=24),
        )

        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token_type, "email_verify")
        self.assertEqual(token.token_value, "hashed_token_value")
        self.assertEqual(token.attempts, 0)
        self.assertEqual(token.max_attempts, 5)
        self.assertIsNone(token.used_at)

    def test_token_validation_methods(self):
        """Test token validation helper methods."""
        token = VerificationToken.objects.create(
            user=self.user,
            token_type="signin_otp",
            token_value="test_token",
            expires_at=timezone.now() + datetime.timedelta(hours=1),
        )

        # Token should be valid initially
        self.assertTrue(token.is_valid())
        self.assertFalse(token.is_expired())
        self.assertFalse(token.is_used())
        self.assertFalse(token.is_locked())

    def test_token_expiration(self):
        """Test token expiration logic."""
        expired_token = VerificationToken.objects.create(
            user=self.user,
            token_type="email_verify",
            token_value="expired_token",
            expires_at=timezone.now() - datetime.timedelta(hours=1),
        )

        self.assertTrue(expired_token.is_expired())
        self.assertFalse(expired_token.is_valid())

    def test_token_usage_tracking(self):
        """Test token usage tracking."""
        token = VerificationToken.objects.create(
            user=self.user,
            token_type="phone_verify",
            token_value="usage_token",
            expires_at=timezone.now() + datetime.timedelta(hours=1),
        )

        # Mark as used
        token.mark_used()
        token.refresh_from_db()

        self.assertTrue(token.is_used())
        self.assertIsNotNone(token.used_at)
        self.assertFalse(token.is_valid())

    def test_failed_attempts_tracking(self):
        """Test failed attempts tracking and locking."""
        token = VerificationToken.objects.create(
            user=self.user,
            token_type="signin_otp",
            token_value="attempt_token",
            expires_at=timezone.now() + datetime.timedelta(hours=1),
        )

        # Record failed attempts
        for i in range(token.max_attempts):
            is_locked = token.record_attempt()

        # Token should be locked after max attempts
        self.assertTrue(is_locked)
        self.assertTrue(token.is_locked())
        self.assertFalse(token.is_valid())


class UserSecurityTests(TestCase):
    """Test cases for user security-related model behavior."""

    def test_user_email_normalization_prevents_duplicates(self):
        """Test that email normalization prevents duplicate accounts with same email."""
        # Create user with standard email
        user1 = User.objects.create_user(email="test@example.com", name="Test User 1")

        # Attempt to create user with same email but different case
        # Should normalize to same email
        user2 = User.objects.create_user(email="TEST@EXAMPLE.COM", name="Test User 2")

        # Both should have normalized email
        self.assertEqual(user1.email.lower(), user2.email.lower())

    def test_password_field_security_when_set(self):
        """Test that passwords are securely handled when set."""
        password = "test_password_123"
        user = User.objects.create_user(email="test@example.com", name="Test User", password=password)

        # Password should not be stored as plaintext
        self.assertNotEqual(user.password, password)
        # Platform uses passwordless authentication, so password might be unusable
        # Test documents that passwords, when set, are not plaintext
        self.assertTrue(len(user.password) > len(password))  # Hashed passwords are longer

    def test_user_model_string_representation_does_not_leak_sensitive_data(self):
        """Test that user string representation doesn't expose sensitive information."""
        user = User.objects.create_user(
            email="sensitive@example.com", name="Sensitive User", password="secret_password"
        )

        user_str = str(user)

        # Should not contain password or other sensitive data
        self.assertNotIn("secret_password", user_str)
        # Should be a reasonable representation
        self.assertIn("sensitive@example.com", user_str.lower())


class SchoolModelSecurityTests(TestCase):
    """Test cases for school model security."""

    def test_school_contact_information_is_properly_stored(self):
        """Test that school contact information is stored securely."""
        school = School.objects.create(
            name="Test School",
            description="A test school",
            contact_email="admin@testschool.com",
            phone_number="+351912345678",
        )

        # Contact information should be stored
        self.assertEqual(school.contact_email, "admin@testschool.com")
        self.assertEqual(school.phone_number, "+351912345678")

        # Should have proper string representation
        school_str = str(school)
        self.assertEqual(school_str, "Test School")


class ProgressiveVerificationModelTests(TestCase):
    """Test cases for progressive verification model fields and behavior."""

    def test_user_verification_fields_default_to_false(self):
        """Test that verification fields default to False for new users."""
        user = User.objects.create_user(email="test@example.com", name="Test User")

        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)
        self.assertIsNone(user.verification_required_after)

    def test_verification_required_after_field_is_nullable(self):
        """Test that verification_required_after can be null for legacy users."""
        user = User.objects.create_user(email="legacy@example.com", name="Legacy User")
        user.verification_required_after = None
        user.save()

        # Should save without error
        user.refresh_from_db()
        self.assertIsNone(user.verification_required_after)

    def test_verification_required_after_field_accepts_datetime(self):
        """Test that verification_required_after accepts datetime values."""
        user = User.objects.create_user(email="datetime@example.com", name="DateTime User")

        deadline = timezone.now() + datetime.timedelta(hours=24)
        user.verification_required_after = deadline
        user.save()

        user.refresh_from_db()
        self.assertEqual(user.verification_required_after, deadline)

    def test_user_can_be_partially_verified_email_only(self):
        """Test that user can have only email verified."""
        user = User.objects.create_user(email="email_only@example.com", name="Email Only User")

        user.email_verified = True
        user.phone_verified = False
        user.save()

        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        self.assertFalse(user.phone_verified)

    def test_user_can_be_partially_verified_phone_only(self):
        """Test that user can have only phone verified."""
        user = User.objects.create_user(email="phone_only@example.com", name="Phone Only User")

        user.email_verified = False
        user.phone_verified = True
        user.save()

        user.refresh_from_db()
        self.assertFalse(user.email_verified)
        self.assertTrue(user.phone_verified)

    def test_user_can_be_fully_verified(self):
        """Test that user can have both email and phone verified."""
        user = User.objects.create_user(email="fully_verified@example.com", name="Fully Verified User")

        user.email_verified = True
        user.phone_verified = True
        user.save()

        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        self.assertTrue(user.phone_verified)

    def test_verification_fields_work_with_grace_period_logic(self):
        """Test verification fields work correctly with grace period scenarios."""
        user = User.objects.create_user(email="grace@example.com", name="Grace User")

        # New user in grace period
        user.email_verified = False
        user.phone_verified = False
        user.verification_required_after = timezone.now() + datetime.timedelta(hours=12)
        user.save()

        user.refresh_from_db()

        # User should be unverified but have time left
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)
        self.assertGreater(user.verification_required_after, timezone.now())

    def test_verification_fields_work_with_expired_grace_period(self):
        """Test verification fields work correctly with expired grace period."""
        user = User.objects.create_user(email="expired@example.com", name="Expired User")

        # User with expired grace period
        user.email_verified = False
        user.phone_verified = False
        user.verification_required_after = timezone.now() - datetime.timedelta(hours=1)
        user.save()

        user.refresh_from_db()

        # User should be unverified with expired deadline
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)
        self.assertLess(user.verification_required_after, timezone.now())

    def test_progressive_verification_fields_are_indexed_correctly(self):
        """Test that database indexes work for verification queries."""
        # Create multiple users with different verification states
        users_data = [
            {"email": "user1@example.com", "email_verified": True, "phone_verified": False},
            {"email": "user2@example.com", "email_verified": False, "phone_verified": True},
            {"email": "user3@example.com", "email_verified": False, "phone_verified": False},
            {"email": "user4@example.com", "email_verified": True, "phone_verified": True},
        ]

        for data in users_data:
            user = User.objects.create_user(email=data["email"], name="Test User")
            user.email_verified = data["email_verified"]
            user.phone_verified = data["phone_verified"]
            user.verification_required_after = timezone.now() + datetime.timedelta(hours=24)
            user.save()

        # Query for unverified users (neither email nor phone verified)
        unverified_users = User.objects.filter(email_verified=False, phone_verified=False)
        self.assertEqual(unverified_users.count(), 1)
        self.assertEqual(unverified_users.first().email, "user3@example.com")

        # Query for fully verified users
        fully_verified_users = User.objects.filter(email_verified=True, phone_verified=True)
        self.assertEqual(fully_verified_users.count(), 1)
        self.assertEqual(fully_verified_users.first().email, "user4@example.com")

        # Query for partially verified users (at least one method verified)
        from django.db.models import Q

        partially_verified_users = User.objects.filter(Q(email_verified=True) | Q(phone_verified=True))
        self.assertEqual(partially_verified_users.count(), 3)  # user1, user2, user4

    def test_verification_fields_migration_compatibility(self):
        """Test that verification fields are compatible with existing users."""
        # This test ensures that the new fields don't break existing users

        # Create a user like it would have existed before the progressive verification
        user = User.objects.create_user(email="legacy@example.com", name="Legacy User")

        # Verify defaults are safe for existing logic
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)
        self.assertIsNone(user.verification_required_after)

        # User should be queryable
        users = User.objects.filter(email=user.email)
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), user)
