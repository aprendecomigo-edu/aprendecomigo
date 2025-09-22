"""
Tests for PeopleView student search functionality.

These tests focus specifically on the HTMX student search feature to prevent
bugs where multiple students with the same name are not all returned in search results.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership
from accounts.models.enums import SchoolRole
from accounts.models.profiles import StudentProfile

User = get_user_model()


class PeopleViewSearchTest(TestCase):
    """Integration tests for student search functionality in PeopleView."""

    def setUp(self):
        """Set up test data for search tests."""
        # Create a test school
        self.school = School.objects.create(name="Test School", address="123 Test St", phone_number="+351234567890")

        # Create a teacher user who can access the people view
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com", name="Test Teacher", password="testpass123"
        )

        # Add teacher to school
        SchoolMembership.objects.create(user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER.value)

    def _create_student(self, name, email, school_year="Year 7"):
        """Helper method to create a student with profile."""
        user = User.objects.create_user(email=email, name=name, password="studentpass123")

        # Create student membership
        SchoolMembership.objects.create(user=user, school=self.school, role=SchoolRole.STUDENT.value)

        # Create student profile with required fields
        StudentProfile.objects.create(
            user=user,
            name=name,  # Required field
            birth_date=date(2010, 1, 1),  # Required field
            school_year=school_year,
            account_type="ADULT_STUDENT",
        )

        return user

    def test_search_returns_multiple_students_with_same_name(self):
        """
        Test that searching for a name returns ALL students with that name.

        This test specifically addresses the bug where only one "Diana" was returned
        when multiple students with the same name exist.
        """
        # Create multiple students named Diana
        diana1 = self._create_student("Diana Santos", "diana.santos@test.com", "Year 7")
        diana2 = self._create_student("Diana Silva", "diana.silva@test.com", "Year 8")
        diana3 = self._create_student("Diana Costa", "diana.costa@test.com", "Year 9")

        # Create a student with different name to ensure search is specific
        other_student = self._create_student("Maria João", "maria.joao@test.com", "Year 7")

        # Login as teacher
        self.client.force_login(self.teacher_user)

        # Perform HTMX search for "Diana"
        response = self.client.post(
            reverse("people"), {"action": "search_students", "search": "Diana"}, headers={"hx-request": "true"}
        )

        # Verify response is successful
        self.assertEqual(response.status_code, 200)

        # Verify all Diana students are in the response
        response_content = response.content.decode()
        self.assertIn("Diana Santos", response_content)
        self.assertIn("Diana Silva", response_content)
        self.assertIn("Diana Costa", response_content)

        # Verify the other student is NOT in the response
        self.assertNotIn("Maria João", response_content)

        # Verify all three Diana students are included by checking their emails
        self.assertIn("diana.santos@test.com", response_content)
        self.assertIn("diana.silva@test.com", response_content)
        self.assertIn("diana.costa@test.com", response_content)
        self.assertNotIn("maria.joao@test.com", response_content)

    def test_comprehensive_search_functionality(self):
        """
        Test that search works correctly across all searchable fields:
        - Student name (case insensitive, partial match)
        - Student email
        - School year
        - Case sensitivity
        """
        # Create test students with varied data
        student1 = self._create_student("Ana Maria", "ana.maria@test.com", "Year 10")
        student2 = self._create_student("João Pedro", "joao.pedro@test.com", "Year 11")
        student3 = self._create_student("Sofia Almeida", "sofia@test.com", "Year 12")

        self.client.force_login(self.teacher_user)

        # Test 1: Partial name search (case insensitive)
        response = self.client.post(
            reverse("people"), {"action": "search_students", "search": "ana"}, headers={"hx-request": "true"}
        )
        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()
        self.assertIn("Ana Maria", response_content)
        self.assertNotIn("João Pedro", response_content)
        self.assertNotIn("Sofia Almeida", response_content)

        # Test 2: Email search
        response = self.client.post(
            reverse("people"),
            {"action": "search_students", "search": "joao.pedro@test.com"},
            headers={"hx-request": "true"},
        )
        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()
        self.assertIn("João Pedro", response_content)
        self.assertNotIn("Ana Maria", response_content)

        # Test 3: School year search
        response = self.client.post(
            reverse("people"), {"action": "search_students", "search": "Year 12"}, headers={"hx-request": "true"}
        )
        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()
        self.assertIn("Sofia Almeida", response_content)
        self.assertNotIn("Ana Maria", response_content)
        self.assertNotIn("João Pedro", response_content)

        # Test 4: Case insensitive search
        response = self.client.post(
            reverse("people"), {"action": "search_students", "search": "SOFIA"}, headers={"hx-request": "true"}
        )
        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()
        self.assertIn("Sofia Almeida", response_content)

        # Test 5: No results for non-existent search
        response = self.client.post(
            reverse("people"),
            {"action": "search_students", "search": "NonExistentStudent"},
            headers={"hx-request": "true"},
        )
        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()
        self.assertNotIn("Ana Maria", response_content)
        self.assertNotIn("João Pedro", response_content)
        self.assertNotIn("Sofia Almeida", response_content)

    def test_htmx_response_format(self):
        """Test that the search returns proper HTMX partial response."""
        # Create a test student
        student = self._create_student("Test Student", "test@test.com")

        self.client.force_login(self.teacher_user)

        # Perform HTMX search
        response = self.client.post(
            reverse("people"), {"action": "search_students", "search": "Test"}, headers={"hx-request": "true"}
        )

        # Verify response is successful
        self.assertEqual(response.status_code, 200)

        # Verify it returns a partial template, not a full page
        response_content = response.content.decode()
        # Should not contain full HTML page structure
        self.assertNotIn("<html>", response_content)
        self.assertNotIn("<head>", response_content)
        self.assertNotIn("<body>", response_content)

        # Should contain the student data
        self.assertIn("Test Student", response_content)

    def test_search_requires_authentication(self):
        """Test that search requires user to be logged in."""
        response = self.client.post(
            reverse("people"), {"action": "search_students", "search": "test"}, headers={"hx-request": "true"}
        )

        # Should redirect to login (302) or return 401/403
        self.assertIn(response.status_code, [302, 401, 403])

    def test_empty_search_returns_all_students(self):
        """Test that empty search query returns all students."""
        # Create test students
        student1 = self._create_student("Student One", "one@test.com")
        student2 = self._create_student("Student Two", "two@test.com")

        self.client.force_login(self.teacher_user)

        # Search with empty query
        response = self.client.post(
            reverse("people"), {"action": "search_students", "search": ""}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # Both students should be in the response
        self.assertIn("Student One", response_content)
        self.assertIn("Student Two", response_content)
