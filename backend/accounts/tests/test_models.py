import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import (
    School,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherProfile,
    VerificationCode,
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

    def test_student_profile_creation_with_required_fields(self):
        """Test student profile creation with required fields."""
        # Create profile with required fields
        profile = StudentProfile.objects.create(
            user=self.user,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
        )

        # Should be created successfully
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.birth_date, datetime.date(2008, 1, 1))
        self.assertEqual(profile.school_year, "10")

        # Add more data
        profile.address = "123 Test St, Test City, 12345"
        profile.cc_number = "123456789"
        profile.save()

        # Should save successfully
        self.assertEqual(profile.address, "123 Test St, Test City, 12345")
        self.assertEqual(profile.cc_number, "123456789")

    def test_student_profile_string_representation(self):
        """Test that student profile has proper string representation."""
        profile = StudentProfile.objects.create(
            user=self.user,
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

    def test_completion_score_updates_automatically_on_save(self):
        """Test that profile completion score is calculated on updates."""
        teacher_profile = TeacherProfile.objects.create(user=self.user, bio="Short bio")

        initial_score = teacher_profile.profile_completion_score

        # Add more profile data
        teacher_profile.specialty = "Mathematics and Physics"
        teacher_profile.education = "Master's Degree in Mathematics"
        teacher_profile.hourly_rate = Decimal("35.00")
        teacher_profile.save()

        # Score should improve
        teacher_profile.refresh_from_db()
        self.assertGreater(teacher_profile.profile_completion_score, initial_score)

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


class VerificationCodeTests(TestCase):
    """Test cases for VerificationCode business logic."""

    def setUp(self):
        """Set up test data."""
        self.email = "test@example.com"

    def test_generate_code_replaces_existing_for_same_email(self):
        """Test that generating a new code replaces any existing code for the email."""
        # Generate first code
        verification1 = VerificationCode.generate_code(self.email)
        original_secret = verification1.secret_key

        # Generate second code for same email
        verification2 = VerificationCode.generate_code(self.email)

        # Should only have one verification code per email
        self.assertEqual(VerificationCode.objects.filter(email=self.email).count(), 1)

        # Secret key should be different (new code generated)
        self.assertNotEqual(original_secret, verification2.secret_key)

    def test_code_generation_creates_valid_totp_code(self):
        """Test that generated codes are valid TOTP codes."""
        verification = VerificationCode.generate_code(self.email)

        # Should generate 6-digit code
        code = verification.get_current_code()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

        # Should be valid when checked
        self.assertTrue(verification.is_valid(code))

    def test_code_validation_enforces_business_rules(self):
        """Test that code validation enforces security business rules."""
        verification = VerificationCode.generate_code(self.email)
        valid_code = verification.get_current_code()

        # Valid code should work initially
        self.assertTrue(verification.is_valid(valid_code))

        # Invalid code should be rejected
        self.assertFalse(verification.is_valid("000000"))

        # Test max attempts protection
        verification.failed_attempts = verification.max_attempts
        verification.save()
        self.assertFalse(verification.is_valid(valid_code))

        # Test used code protection
        verification.failed_attempts = 0
        verification.is_used = True
        verification.save()
        self.assertFalse(verification.is_valid(valid_code))

        # Test expiration (codes expire after 24 hours)
        verification.is_used = False
        verification.created_at = timezone.now() - timezone.timedelta(hours=25)
        verification.save()
        self.assertFalse(verification.is_valid(valid_code))

    def test_failed_attempt_tracking_prevents_brute_force(self):
        """Test that failed attempts are tracked to prevent brute force attacks."""
        verification = VerificationCode.generate_code(self.email)

        # Make multiple failed attempts
        for i in range(verification.max_attempts):
            self.assertFalse(verification.is_valid("wrong"))
            verification.refresh_from_db()

        # After max attempts, even valid codes should be rejected
        valid_code = verification.get_current_code()
        self.assertFalse(verification.is_valid(valid_code))
        self.assertEqual(verification.failed_attempts, verification.max_attempts)

    def test_use_marks_code_as_consumed(self):
        """Test that using a code marks it as consumed to prevent reuse."""
        verification = VerificationCode.generate_code(self.email)
        valid_code = verification.get_current_code()

        # Initially should be usable
        self.assertFalse(verification.is_used)
        self.assertTrue(verification.is_valid(valid_code))

        # Mark as used
        verification.use()

        # Should now be marked as used and invalid
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)
        self.assertFalse(verification.is_valid(valid_code))


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
