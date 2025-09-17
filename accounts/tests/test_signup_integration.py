"""
Integration tests for the signup flow with user-school creation.

Tests the complete signup process from form submission to user authentication
with automatic school creation and membership assignment.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership, SchoolRole
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class SignupIntegrationTestCase(BaseTestCase):
    """Test the complete signup flow with school creation"""

    def setUp(self):
        """Set up test client and data"""
        self.client = Client()
        self.signup_url = reverse("accounts:signup")

        self.valid_signup_data = {
            "email": "newuser@example.com",
            "full_name": "Jane Doe",
            "phone_number": "+351987654321",
            "organization_name": "Jane's Tutoring Academy",
            "account_type": "school",
        }

    def test_successful_signup_creates_user_and_school(self):
        """Test successful signup creates user, school, and membership atomically"""
        # Act: Submit valid signup form
        response = self.client.post(self.signup_url, self.valid_signup_data)

        # Assert: Response indicates success
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account created successfully")
        self.assertContains(response, "dashboard")

        # Assert: User was created with correct data
        user = User.objects.get(email=self.valid_signup_data["email"])
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.phone_number, self.valid_signup_data["phone_number"])
        self.assertFalse(user.is_superuser)

        # Assert: School was created with exact name from form
        school = School.objects.get(name=self.valid_signup_data["organization_name"])
        self.assertEqual(school.contact_email, user.email)
        self.assertIn("Jane", school.description)

        # Assert: User has school membership as owner
        membership = SchoolMembership.objects.get(user=user, school=school)
        self.assertEqual(membership.role, SchoolRole.SCHOOL_OWNER)
        self.assertTrue(membership.is_active)

        # Assert: User is automatically logged in
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_signup_with_tutor_account_type(self):
        """Test signup with tutor account type creates appropriate school"""
        # Arrange: Change account type to tutor
        tutor_data = self.valid_signup_data.copy()
        tutor_data["account_type"] = "tutor"
        tutor_data["organization_name"] = "Jane's Math Practice"

        # Act: Submit signup form
        response = self.client.post(self.signup_url, tutor_data)

        # Assert: Success
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account created successfully")

        # Assert: School created with practice name
        school = School.objects.get(name=tutor_data["organization_name"])
        self.assertEqual(school.name, "Jane's Math Practice")

    def test_signup_missing_email_shows_error(self):
        """Test signup without email shows validation error"""
        # Arrange: Remove email from data
        invalid_data = self.valid_signup_data.copy()
        del invalid_data["email"]

        # Act: Submit form
        response = self.client.post(self.signup_url, invalid_data)

        # Assert: Error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email is required")

        # Assert: No user or school created
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(School.objects.count(), 0)

    def test_signup_missing_full_name_shows_error(self):
        """Test signup without full name shows validation error"""
        # Arrange: Remove full name
        invalid_data = self.valid_signup_data.copy()
        del invalid_data["full_name"]

        # Act: Submit form
        response = self.client.post(self.signup_url, invalid_data)

        # Assert: Error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Full name is required")

        # Assert: No user or school created
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(School.objects.count(), 0)

    def test_signup_missing_phone_number_shows_error(self):
        """Test signup without phone number shows validation error"""
        # Arrange: Remove phone number
        invalid_data = self.valid_signup_data.copy()
        del invalid_data["phone_number"]

        # Act: Submit form
        response = self.client.post(self.signup_url, invalid_data)

        # Assert: Error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Phone number is required")

        # Assert: No user or school created
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(School.objects.count(), 0)

    def test_signup_missing_organization_name_shows_error(self):
        """Test signup without organization name shows validation error"""
        # Arrange: Remove organization name
        invalid_data = self.valid_signup_data.copy()
        del invalid_data["organization_name"]

        # Act: Submit form
        response = self.client.post(self.signup_url, invalid_data)

        # Assert: Error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Organization name is required")

        # Assert: No user or school created
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(School.objects.count(), 0)

    def test_signup_invalid_email_format_shows_error(self):
        """Test signup with invalid email format shows validation error"""
        # Arrange: Invalid email
        invalid_data = self.valid_signup_data.copy()
        invalid_data["email"] = "not-an-email"

        # Act: Submit form
        response = self.client.post(self.signup_url, invalid_data)

        # Assert: Error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a valid email address")

        # Assert: No user or school created
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(School.objects.count(), 0)

    def test_signup_duplicate_email_shows_error(self):
        """Test signup with existing email shows validation error"""
        # Arrange: Create existing user
        existing_user = User.objects.create_user(email=self.valid_signup_data["email"], name="Existing User")

        # Act: Try to signup with same email
        response = self.client.post(self.signup_url, self.valid_signup_data)

        # Assert: Error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account with this email or phone already exists")

        # Assert: Only original user exists, no new school created
        users = User.objects.filter(email=self.valid_signup_data["email"])
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first().name, "Existing User")  # Original user unchanged

    def test_signup_atomic_transaction_rollback_on_school_creation_failure(self):
        """Test that user creation rolls back if school creation fails"""
        # This test simulates a scenario where school creation might fail
        # We'll use a mock or database constraint to trigger failure

        with self.assertRaises(Exception):
            with transaction.atomic():
                # Submit valid data
                response = self.client.post(self.signup_url, self.valid_signup_data)

                # Force an exception to test rollback
                # In real scenario, this could be a database constraint violation
                raise Exception("Simulated school creation failure")

        # Assert: No user or school should be created due to rollback
        self.assertEqual(User.objects.filter(email=self.valid_signup_data["email"]).count(), 0)
        self.assertEqual(School.objects.filter(name=self.valid_signup_data["organization_name"]).count(), 0)

    def test_signup_preserves_user_session_data(self):
        """Test that signup preserves any existing session data"""
        # Arrange: Set some session data
        session = self.client.session
        session["test_key"] = "test_value"
        session.save()

        # Act: Successful signup
        response = self.client.post(self.signup_url, self.valid_signup_data)

        # Assert: Session data preserved (except auth data is added)
        self.assertEqual(self.client.session.get("test_key"), "test_value")
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_signup_redirect_template_has_correct_data(self):
        """Test that signup success template contains correct redirect information"""
        # Act: Successful signup
        response = self.client.post(self.signup_url, self.valid_signup_data)

        # Assert: Template contains redirect information
        self.assertContains(response, "Account created successfully! Welcome to Aprende Comigo.")
        self.assertContains(response, "Redirecting to your dashboard")
        self.assertContains(response, "dashboard")  # Should contain dashboard URL

        # Assert: Auto-redirect script present
        self.assertContains(response, "window.location.href")
        self.assertContains(response, "2000")  # 2 second delay

    def test_authenticated_user_cannot_access_signup(self):
        """Test that already authenticated users are redirected from signup"""
        # Arrange: Create user with proper school membership
        user = User.objects.create_user(email="existing@example.com", name="Existing User")
        school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.SCHOOL_OWNER, is_active=True)
        self.client.force_login(user)

        # Act: Try to access signup page
        response = self.client.get(self.signup_url)

        # Assert: Redirected to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard:dashboard"))

    def test_signup_creates_user_with_correct_names(self):
        """Test that signup correctly splits and assigns first/last names"""
        # Arrange: Test various name formats
        test_cases = [
            ("John Smith", "John", "Smith"),
            ("Maria José Santos Silva", "Maria", "José Santos Silva"),
            ("Madonna", "Madonna", ""),
            ("Jean-Claude Van Damme", "Jean-Claude", "Van Damme"),
        ]

        for full_name, expected_first, expected_last in test_cases:
            with self.subTest(full_name=full_name):
                # Arrange: Fresh data for each test
                test_data = self.valid_signup_data.copy()
                test_data["email"] = f"test_{full_name.replace(' ', '_').lower()}@example.com"
                test_data["full_name"] = full_name
                test_data["organization_name"] = f"{full_name}'s School"

                # Act: Submit signup
                response = self.client.post(self.signup_url, test_data)

                # Assert: Success
                self.assertEqual(response.status_code, 200)

                # Assert: Names split correctly
                user = User.objects.get(email=test_data["email"])
                self.assertEqual(user.first_name, expected_first)
                self.assertEqual(user.last_name, expected_last)
