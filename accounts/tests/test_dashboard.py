from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Student

User = get_user_model()


class DashboardTemplateTests(TestCase):
    """Tests to ensure correct dashboard templates are loaded based on user type."""

    def setUp(self):
        """Set up test users of different types."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            name="Admin User",
            is_admin=True,
            user_type="admin",
        )

        # Create teacher user
        self.teacher_user = User.objects.create_user(
            email="teacher@example.com",
            password="testpass123",
            name="Teacher User",
            user_type="teacher",
        )

        # Create student user
        self.student_user = User.objects.create_user(
            email="student@example.com",
            password="testpass123",
            name="Student User",
            user_type="student",
        )

        # Create student profile for student user to avoid onboarding redirect
        Student.objects.create(
            user=self.student_user,
            school_year="2023",
            birth_date="2000-01-01",
            address="Test Address",
        )

        # Create student user without profile (for testing onboarding redirect)
        self.student_no_profile = User.objects.create_user(
            email="student_no_profile@example.com",
            password="testpass123",
            name="Student Without Profile",
            user_type="student",
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            email="regular@example.com",
            password="testpass123",
            name="Regular User",
            user_type="",
        )

        # Create a user for testing user type updates
        self.update_user = User.objects.create_user(
            email="update@example.com",
            password="testpass123",
            name="Update User",
            user_type="",
        )

        # Create test client
        self.client = Client()

        # URLs
        self.dashboard_url = reverse("dashboard")
        self.onboarding_url = reverse("student_onboarding")

    def test_admin_sees_admin_dashboard(self):
        """Test that admin users see the admin dashboard."""
        # Log in as admin
        self.client.login(email="admin@example.com", password="testpass123")

        # Access the dashboard
        response = self.client.get(self.dashboard_url)

        # Check status code and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_dashboard.html")

    def test_teacher_sees_teacher_dashboard(self):
        """Test that teacher users see the teacher dashboard."""
        # Log in as teacher
        self.client.login(email="teacher@example.com", password="testpass123")

        # Access the dashboard
        response = self.client.get(self.dashboard_url)

        # Check status code and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "teacher_dashboard.html")

    def test_student_sees_student_dashboard(self):
        """Test that student users see the student dashboard."""
        # Log in as student
        self.client.login(email="student@example.com", password="testpass123")

        # Access the dashboard
        response = self.client.get(self.dashboard_url)

        # Check status code and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "student_dashboard.html")

    def test_student_without_profile_redirected_to_onboarding(self):
        """Test that student users without profiles are redirected to onboarding."""
        # Log in as student without profile
        self.client.login(
            email="student_no_profile@example.com", password="testpass123"
        )

        # Access the dashboard
        response = self.client.get(self.dashboard_url)

        # Check for redirect to onboarding
        self.assertRedirects(response, self.onboarding_url)

    def test_regular_user_sees_generic_dashboard(self):
        """Test that users with no specific type see the generic dashboard."""
        # Log in as regular user
        self.client.login(email="regular@example.com", password="testpass123")

        # Access the dashboard
        response = self.client.get(self.dashboard_url)

        # Check status code and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")

    def test_superuser_sees_admin_dashboard(self):
        """Test that superusers see the admin dashboard."""
        # Create and log in as superuser
        User.objects.create_superuser(
            email="super@example.com", password="testpass123", name="Super User"
        )
        self.client.login(email="super@example.com", password="testpass123")

        # Access the dashboard
        response = self.client.get(self.dashboard_url)

        # Check status code and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_dashboard.html")

    def test_staff_sees_admin_dashboard(self):
        """Test that staff users see the admin dashboard."""
        # Create and log in as staff user
        User.objects.create_user(
            email="staff@example.com",
            password="testpass123",
            name="Staff User",
            is_staff=True,
        )
        self.client.login(email="staff@example.com", password="testpass123")

        # Access the dashboard
        response = self.client.get(self.dashboard_url)

        # Check status code and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_dashboard.html")
