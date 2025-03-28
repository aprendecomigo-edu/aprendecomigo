from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserTypeSelectionTests(TestCase):
    """Tests for the user type selection view."""

    def setUp(self):
        """Set up test users and URLs."""
        # Create a user without type
        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpass123",
            name="Test User",
            user_type="",
        )

        # Create test client
        self.client = Client()

        # URLs
        self.select_type_url = reverse("select_user_type")
        self.dashboard_url = reverse("dashboard")
        self.student_onboarding_url = reverse("student_onboarding")

    def test_get_user_type_selection(self):
        """Test that the user type selection page loads correctly."""
        # Log in
        self.client.login(email="user@example.com", password="testpass123")

        # Access the selection page
        response = self.client.get(self.select_type_url)

        # Check it loads correctly
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/select_user_type.html")

    def test_select_student_type(self):
        """Test setting user type to student."""
        # Log in
        self.client.login(email="user@example.com", password="testpass123")

        # Post student type selection
        response = self.client.post(self.select_type_url, {"user_type": "student"})

        # Check redirect to student onboarding
        self.assertRedirects(response, self.student_onboarding_url)

        # Refresh user from database
        self.user.refresh_from_db()

        # Check user type was updated
        self.assertEqual(self.user.user_type, "student")

    def test_select_teacher_type(self):
        """Test setting user type to teacher."""
        # Log in
        self.client.login(email="user@example.com", password="testpass123")

        # Post teacher type selection
        response = self.client.post(self.select_type_url, {"user_type": "teacher"})

        # Check redirect to dashboard
        self.assertRedirects(response, self.dashboard_url)

        # Refresh user from database
        self.user.refresh_from_db()

        # Check user type was updated
        self.assertEqual(self.user.user_type, "teacher")

    def test_missing_user_type(self):
        """Test submitting form without user_type parameter."""
        # Log in
        self.client.login(email="user@example.com", password="testpass123")

        # Post without user_type
        response = self.client.post(self.select_type_url, {})

        # Should stay on the same page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/select_user_type.html")

        # Refresh user from database
        self.user.refresh_from_db()

        # User type should not have changed
        self.assertEqual(self.user.user_type, "")
