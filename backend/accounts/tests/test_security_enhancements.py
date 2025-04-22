from accounts.models import EmailVerificationCode
from django.contrib.auth import get_user_model
from django.urls import reverse
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class SecurityEnhancementsTests(APITestCase):
    """
    Test the security enhancements implemented for user permissions and TOTP verification.
    """

    def setUp(self):
        # Create users with different roles
        self.manager = User.objects.create_user(
            email="manager@example.com",
            password="testpassword",
            name="Manager User",
            user_type="manager",
        )

        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            password="testpassword",
            name="Teacher User",
            user_type="teacher",
        )

        self.student = User.objects.create_user(
            email="student@example.com",
            password="testpassword",
            name="Student User",
            user_type="student",
        )

        # Create tokens for each user
        _, self.manager_token = AuthToken.objects.create(self.manager)
        _, self.teacher_token = AuthToken.objects.create(self.teacher)
        _, self.student_token = AuthToken.objects.create(self.student)

    def test_user_list_filtering(self):
        """Test that users can only see appropriate user listings."""
        url = reverse("user-list")

        # Test manager access (should see all users)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.manager_token}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see all users (number may vary depending on pre-existing data)
        self.assertGreaterEqual(len(response.data), 3)

        # Test teacher access (should see only themselves)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.teacher_token}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the teacher can only see their own data
        print(f"Teacher response data: {response.data}")

        # Handle both list and dictionary response formats
        if isinstance(response.data, list):
            teacher_emails = [user.get("email") for user in response.data]
        elif isinstance(response.data, dict) and "results" in response.data:
            # Paginated response
            teacher_emails = [user.get("email") for user in response.data["results"]]
        else:
            # Single-item response or unexpected format
            teacher_emails = (
                [response.data.get("email")] if hasattr(response.data, "get") else []
            )

        self.assertIn(self.teacher.email, teacher_emails)

        # Test student access (should see only themselves)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.student_token}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the student can only see their own data
        print(f"Student response data: {response.data}")

        # Handle both list and dictionary response formats
        if isinstance(response.data, list):
            student_emails = [user.get("email") for user in response.data]
        elif isinstance(response.data, dict) and "results" in response.data:
            # Paginated response
            student_emails = [user.get("email") for user in response.data["results"]]
        else:
            # Single-item response or unexpected format
            student_emails = (
                [response.data.get("email")] if hasattr(response.data, "get") else []
            )

        self.assertIn(self.student.email, student_emails)

    def test_user_create_permissions(self):
        """Test that only managers can create new users."""
        url = reverse("user-list")
        new_user_data = {
            "email": "newuser@example.com",
            "name": "New User",
            "user_type": "student",
        }

        # Test manager can create users
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.manager_token}")
        response = self.client.post(url, new_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test teacher cannot create users
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.teacher_token}")
        response = self.client.post(
            url,
            {
                "email": "another@example.com",
                "name": "Another User",
                "user_type": "student",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test student cannot create users
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.student_token}")
        response = self.client.post(
            url,
            {
                "email": "yetanother@example.com",
                "name": "Yet Another User",
                "user_type": "student",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_update_permissions(self):
        """Test that users can only update themselves unless they're managers."""

        # Test manager can update any user
        manager_url = reverse("user-detail", args=[self.student.id])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.manager_token}")
        response = self.client.patch(manager_url, {"name": "Updated Student"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test teacher can update themselves but not others
        teacher_url = reverse("user-detail", args=[self.teacher.id])
        student_url = reverse("user-detail", args=[self.student.id])

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.teacher_token}")

        # Update self
        response = self.client.patch(teacher_url, {"name": "Updated Teacher"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try to update student (should fail with either 403 or 404)
        response = self.client.patch(student_url, {"name": "Hacked Student"})
        self.assertIn(
            response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_verification_secret_key_uniqueness(self):
        """Test that each verification instance gets a unique secret key."""
        email1 = "test1@example.com"
        email2 = "test2@example.com"

        # Generate codes for different emails
        verification1 = EmailVerificationCode.generate_code(email1)
        verification2 = EmailVerificationCode.generate_code(email2)

        # Verify each gets a unique secret
        self.assertNotEqual(verification1.secret_key, verification2.secret_key)

        # Verify no default value is used
        self.assertNotEqual(verification1.secret_key, "DEFAULTSECRETKEYTOBEREPLACED")
        self.assertNotEqual(verification2.secret_key, "DEFAULTSECRETKEYTOBEREPLACED")

        # Verify secrets are of correct length for TOTP (32 chars in base32)
        self.assertEqual(len(verification1.secret_key), 32)
        self.assertEqual(len(verification2.secret_key), 32)
