"""
Integration tests for authentication views.

Tests focus on business logic, security decisions, and HTMX behavior
rather than Django's built-in functionality.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership, SchoolRole
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class SignInViewTest(BaseTestCase):
    """Test cases for the SignInView focusing on business logic."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.signin_url = reverse("accounts:signin")

    def test_signin_with_existing_user_initiates_verification_flow(self):
        """Test signin with existing user creates proper verification session."""
        user = User.objects.create_user(email="test@example.com", name="Test User", phone_number="+351987654321")

        with (
            patch("accounts.views.send_magic_link_email") as mock_email,
            patch("accounts.views.send_sms_otp") as mock_sms,
        ):
            mock_email.return_value = {"success": True}
            mock_sms.return_value = {"success": True}

            response = self.client.post(self.signin_url, {"email": "test@example.com"})

        # Should return HTMX verification partial
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "verification")

        # Should store verification data in session
        self.assertEqual(self.client.session["verification_email"], user.email)
        self.assertEqual(self.client.session["verification_user_id"], user.id)

    def test_signin_with_nonexistent_user_creates_verification_flow(self):
        """
        Test signin with nonexistent user still creates verification flow.

        SECURITY: Don't reveal whether user exists or not.
        """
        response = self.client.post(self.signin_url, {"email": "newuser@example.com"})

        # Should still show verification success (security decision)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "verification")

        # Should store email for potential account creation
        self.assertEqual(self.client.session["verification_email"], "newuser@example.com")


class ProfileViewTest(BaseTestCase):
    """Test cases for profile views focusing on multi-tenant security."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()

        self.user = User.objects.create_user(email="user@example.com", name="Test User", phone_number="+351987654321")

        self.school = School.objects.create(name="Test School", contact_email=self.user.email)

        SchoolMembership.objects.create(user=self.user, school=self.school, role=SchoolRole.TEACHER, is_active=True)

        self.client.force_login(self.user)
        self.profile_url = reverse("accounts:profile")

    def test_profile_view_shows_school_memberships(self):
        """Test profile view shows user's school memberships correctly."""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.school.name)
        self.assertContains(response, "Teacher")

    def test_profile_edit_duplicate_email_prevented(self):
        """Test profile edit prevents duplicate email addresses."""
        # Create another user with different email
        User.objects.create_user(email="existing@example.com", name="Existing User")

        edit_profile_url = reverse("accounts:profile_edit")
        response = self.client.post(
            edit_profile_url,
            {
                "name": "Test User",
                "email": "existing@example.com",  # Duplicate email
                "phone_number": "+351987654321",
            },
        )

        # Should show form with validation error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "email")  # Error message contains "email"

        # Original user email should remain unchanged
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "user@example.com")


class CustomMagicLoginViewTest(BaseTestCase):
    """Test cases for magic link login focusing on security."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        self.user = User.objects.create_user(email="user@example.com", name="Test User")

    def test_magic_login_with_valid_token_logs_in_user(self):
        """Test magic login with valid sesame token logs in user."""
        from sesame.utils import get_query_string

        token = get_query_string(self.user)
        magic_login_url = reverse("accounts:magic_login") + token

        response = self.client.get(magic_login_url)

        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)

        # User should be logged in
        user_id = self.client.session.get("_auth_user_id")
        self.assertEqual(int(user_id), self.user.id)


class SchoolMemberListViewTest(BaseTestCase):
    """Test cases for school member list focusing on authorization."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()

        self.owner = User.objects.create_user(email="owner@example.com", name="School Owner")

        self.school = School.objects.create(name="Test School", contact_email=self.owner.email)

        SchoolMembership.objects.create(
            user=self.owner, school=self.school, role=SchoolRole.SCHOOL_OWNER, is_active=True
        )

        self.teacher = User.objects.create_user(email="teacher@example.com", name="Teacher User")
        SchoolMembership.objects.create(user=self.teacher, school=self.school, role=SchoolRole.TEACHER, is_active=True)

    def test_member_list_requires_proper_authorization(self):
        """Test member list enforces proper authorization."""
        # Unauthorized user should be denied
        unauthorized_user = User.objects.create_user(email="unauthorized@example.com", name="Unauthorized")
        self.client.force_login(unauthorized_user)

        member_list_url = reverse("accounts:school_members", kwargs={"school_pk": self.school.id})
        response = self.client.get(member_list_url)

        self.assertIn(response.status_code, [403, 302])

    def test_member_list_shows_only_active_members(self):
        """Test member list excludes inactive members."""
        # Create inactive member
        inactive_user = User.objects.create_user(email="inactive@example.com", name="Inactive User")
        SchoolMembership.objects.create(
            user=inactive_user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=False,  # Inactive
        )

        self.client.force_login(self.owner)
        member_list_url = reverse("accounts:school_members", kwargs={"school_pk": self.school.id})
        response = self.client.get(member_list_url)

        self.assertEqual(response.status_code, 200)
        # Should show active members
        self.assertContains(response, self.owner.name)
        self.assertContains(response, self.teacher.name)
        # Should not show inactive member
        self.assertNotContains(response, inactive_user.name)

    def test_member_list_multi_tenant_security(self):
        """Test member list enforces multi-tenant security boundaries."""
        # Create another school with different owner
        other_school = School.objects.create(name="Other School")
        other_owner = User.objects.create_user(email="other@example.com", name="Other Owner")
        SchoolMembership.objects.create(
            user=other_owner, school=other_school, role=SchoolRole.SCHOOL_OWNER, is_active=True
        )

        # School owner should not access other school's members
        self.client.force_login(self.owner)
        other_member_list_url = reverse("accounts:school_members", kwargs={"school_pk": other_school.id})
        response = self.client.get(other_member_list_url)

        # Should be denied access
        self.assertIn(response.status_code, [403, 302, 404])
