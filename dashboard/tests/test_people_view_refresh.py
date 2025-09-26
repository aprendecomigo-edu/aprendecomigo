"""
Test for the student list refresh functionality in PeopleView.

This test verifies that the new refresh_students action works correctly
to fix the HTMX refresh bug after student creation (Issue #279).
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership
from accounts.models.enums import SchoolRole
from accounts.models.profiles import StudentProfile

User = get_user_model()


class PeopleViewRefreshTest(TestCase):
    """Test the refresh_students action in PeopleView for HTMX list refresh."""

    def setUp(self):
        """Set up test data for refresh tests."""
        # Create a test school
        self.school = School.objects.create(name="Test School", address="123 Test St", phone_number="+351234567890")

        # Create a teacher user who can access the people view
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com", name="Test Teacher", password="testpass123"
        )

        # Add teacher to school
        SchoolMembership.objects.create(user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER.value)

        self.client = Client()

    def _create_student(self, name, email, school_year="Year 7"):
        """Helper method to create a student with profile."""
        user = User.objects.create_user(email=email, name=name, password="studentpass123")

        # Create student membership
        SchoolMembership.objects.create(user=user, school=self.school, role=SchoolRole.STUDENT.value)

        # Create student profile with required fields
        StudentProfile.objects.create(
            user=user,
            name=name,
            birth_date=date(2010, 1, 1),
            school_year=school_year,
            account_type="ADULT_STUDENT",
        )
        return user

    def test_refresh_students_action_requires_authentication(self):
        """Test that refresh_students action requires authentication."""
        response = self.client.post("/people/", {"action": "refresh_students"})
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_refresh_students_action_returns_student_list_partial(self):
        """Test that refresh_students action returns the students list partial."""
        # Login as teacher
        self.client.login(email="teacher@test.com", password="testpass123")

        # Create some students
        student1 = self._create_student("Alice Johnson", "alice@test.com", "Year 8")
        student2 = self._create_student("Bob Smith", "bob@test.com", "Year 9")

        # Call the refresh_students action
        response = self.client.post("/people/", {"action": "refresh_students"})

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Should return HTML content (not JSON)
        self.assertIn("text/html", response.get("Content-Type", ""))

        # Should contain the students list partial structure
        content = response.content.decode()
        self.assertIn('id="students-content"', content)
        self.assertIn("Alice Johnson", content)
        self.assertIn("Bob Smith", content)
        self.assertIn("alice@test.com", content)
        self.assertIn("bob@test.com", content)

    def test_refresh_students_action_with_no_students(self):
        """Test refresh_students action when no students exist."""
        # Login as teacher
        self.client.login(email="teacher@test.com", password="testpass123")

        # Call the refresh_students action
        response = self.client.post("/people/", {"action": "refresh_students"})

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Should contain empty state content
        content = response.content.decode()
        self.assertIn('id="students-content"', content)
        self.assertIn("No students found", content)
        self.assertIn("Add First Student", content)

    def test_refresh_students_action_updates_after_new_creation(self):
        """Test that refresh_students shows newly created students (simulates the bug fix)."""
        # Login as teacher
        self.client.login(email="teacher@test.com", password="testpass123")

        # Initially no students
        response = self.client.post("/people/", {"action": "refresh_students"})
        content = response.content.decode()
        self.assertIn("No students found", content)

        # Create a new student (simulating what happens after successful creation)
        student = self._create_student("New Student", "new@test.com", "Year 10")

        # Call refresh_students action (simulating HTMX trigger)
        response = self.client.post("/people/", {"action": "refresh_students"})

        # Should now show the new student
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("New Student", content)
        self.assertIn("new@test.com", content)
        self.assertNotIn("No students found", content)
