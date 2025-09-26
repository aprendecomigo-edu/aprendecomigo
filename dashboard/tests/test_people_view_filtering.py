"""
Tests for PeopleView student filtering functionality (Issue 283).

These tests verify that students can be filtered by:
- Status: active or inactive (from school membership)
- School year: using UnifiedSchoolYear enum values
- Combined filters: multiple filters working together
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership
from accounts.models.enums import SchoolRole, UnifiedSchoolYear
from accounts.models.profiles import StudentProfile

User = get_user_model()


class PeopleViewFilteringTest(TestCase):
    """Integration tests for student filtering functionality in PeopleView."""

    def setUp(self):
        """Set up test data for filtering tests."""
        # Create a test school
        self.school = School.objects.create(name="Test School", address="123 Test St", phone_number="+351234567890")

        # Create a teacher user who can access the people view
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com", name="Test Teacher", password="testpass123"
        )

        # Add teacher to school
        SchoolMembership.objects.create(user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER.value)

    def _create_student(self, name, email, school_year=None, is_active=True):
        """Helper method to create a student with profile and school membership."""
        user = User.objects.create_user(email=email, name=name, password="studentpass123")
        user.is_active = is_active
        user.save()

        # Create student membership (this determines active/inactive status)
        membership = SchoolMembership.objects.create(user=user, school=self.school, role=SchoolRole.STUDENT.value)
        membership.is_active = is_active
        membership.save()

        # Create student profile with school year
        StudentProfile.objects.create(
            user=user,
            name=name,
            birth_date=date(2010, 1, 1),
            school_year=school_year or UnifiedSchoolYear.YEAR_7.value,
            account_type="ADULT_STUDENT",
        )

        return user

    def test_student_filtering_by_status(self):
        """
        Test that students can be filtered by active/inactive status.

        This test verifies Issue 283 requirement for status filtering.
        """
        # Create students with different statuses
        active_student1 = self._create_student("Active Student 1", "active1@test.com", is_active=True)
        active_student2 = self._create_student("Active Student 2", "active2@test.com", is_active=True)
        inactive_student1 = self._create_student("Inactive Student 1", "inactive1@test.com", is_active=False)
        inactive_student2 = self._create_student("Inactive Student 2", "inactive2@test.com", is_active=False)

        self.client.force_login(self.teacher_user)

        # Test filtering for active students only
        response = self.client.post(
            reverse("people"), {"action": "filter_students", "status": "active"}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # Should include active students
        self.assertIn("Active Student 1", response_content)
        self.assertIn("Active Student 2", response_content)

        # Should NOT include inactive students
        self.assertNotIn("Inactive Student 1", response_content)
        self.assertNotIn("Inactive Student 2", response_content)

        # Test filtering for inactive students only
        response = self.client.post(
            reverse("people"), {"action": "filter_students", "status": "inactive"}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # Should include inactive students
        self.assertIn("Inactive Student 1", response_content)
        self.assertIn("Inactive Student 2", response_content)

        # Should NOT include active students
        self.assertNotIn("Active Student 1", response_content)
        self.assertNotIn("Active Student 2", response_content)

    def test_combined_filtering_status_school_year_and_search(self):
        """
        Test that multiple filters work together: status + school year + search.

        This test verifies Issue 283 requirement for combined filtering.
        """
        # Create students with different combinations of status and school year
        year7_active = self._create_student(
            "Ana Year7 Active", "ana.y7.active@test.com", UnifiedSchoolYear.YEAR_7.value, is_active=True
        )
        year7_inactive = self._create_student(
            "Ana Year7 Inactive", "ana.y7.inactive@test.com", UnifiedSchoolYear.YEAR_7.value, is_active=False
        )
        year8_active = self._create_student(
            "Ana Year8 Active", "ana.y8.active@test.com", UnifiedSchoolYear.YEAR_8.value, is_active=True
        )
        year8_inactive = self._create_student(
            "Diana Year8 Active", "diana.y8.active@test.com", UnifiedSchoolYear.YEAR_8.value, is_active=True
        )

        self.client.force_login(self.teacher_user)

        # Test combined filter: active + Year 7 + search for "Ana"
        response = self.client.post(
            reverse("people"),
            {
                "action": "filter_students",
                "status": "active",
                "school_year": UnifiedSchoolYear.YEAR_7.value,
                "search": "Ana",
            },
            headers={"hx-request": "true"},
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # Should ONLY include the student matching all criteria
        self.assertIn("Ana Year7 Active", response_content)

        # Should NOT include students that don't match all criteria
        self.assertNotIn("Ana Year7 Inactive", response_content)  # Wrong status
        self.assertNotIn("Ana Year8 Active", response_content)  # Wrong school year
        self.assertNotIn("Diana Year8 Active", response_content)  # Wrong name

        # Test combined filter: inactive + Year 7 (no search)
        response = self.client.post(
            reverse("people"),
            {"action": "filter_students", "status": "inactive", "school_year": UnifiedSchoolYear.YEAR_7.value},
            headers={"hx-request": "true"},
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # Should include the inactive Year 7 student
        self.assertIn("Ana Year7 Inactive", response_content)

        # Should NOT include other students
        self.assertNotIn("Ana Year7 Active", response_content)
        self.assertNotIn("Ana Year8 Active", response_content)
        self.assertNotIn("Diana Year8 Active", response_content)

        # Test that existing search functionality still works with filters
        response = self.client.post(
            reverse("people"), {"action": "search_students", "search": "Diana"}, headers={"hx-request": "true"}
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # Search should still work independently
        self.assertIn("Diana Year8 Active", response_content)
        self.assertNotIn("Ana", response_content)

    def test_school_year_filtering_with_unified_enum_values(self):
        """
        Test that school year filtering works with UnifiedSchoolYear enum values.

        This test verifies Issue 283 requirement for school year filtering
        using the UnifiedSchoolYear enum from Issue 288.
        """
        # Create students with different school years from UnifiedSchoolYear enum
        student_year1 = self._create_student("Student Year 1", "year1@test.com", UnifiedSchoolYear.YEAR_1.value)
        student_year7 = self._create_student("Student Year 7", "year7@test.com", UnifiedSchoolYear.YEAR_7.value)
        student_year12 = self._create_student("Student Year 12", "year12@test.com", UnifiedSchoolYear.YEAR_12.value)
        student_higher_ed = self._create_student(
            "Student Higher Ed", "higher@test.com", UnifiedSchoolYear.HIGHER_EDUCATION.value
        )
        student_other = self._create_student("Student Other", "other@test.com", UnifiedSchoolYear.OTHER.value)

        self.client.force_login(self.teacher_user)

        # Test filtering by Year 7
        response = self.client.post(
            reverse("people"),
            {"action": "filter_students", "school_year": UnifiedSchoolYear.YEAR_7.value},
            headers={"hx-request": "true"},
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # Should include only Year 7 student
        self.assertIn("Student Year 7", response_content)

        # Should NOT include other school years
        self.assertNotIn("Student Year 1", response_content)
        self.assertNotIn("Student Year 12", response_content)
        self.assertNotIn("Student Higher Ed", response_content)
        self.assertNotIn("Student Other", response_content)

        # Test filtering by Higher Education
        response = self.client.post(
            reverse("people"),
            {"action": "filter_students", "school_year": UnifiedSchoolYear.HIGHER_EDUCATION.value},
            headers={"hx-request": "true"},
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # Should include only Higher Education student
        self.assertIn("Student Higher Ed", response_content)

        # Should NOT include other school years
        self.assertNotIn("Student Year 1", response_content)
        self.assertNotIn("Student Year 7", response_content)
        self.assertNotIn("Student Year 12", response_content)
        self.assertNotIn("Student Other", response_content)

        # Test filtering by "Outro" (Other)
        response = self.client.post(
            reverse("people"),
            {"action": "filter_students", "school_year": UnifiedSchoolYear.OTHER.value},
            headers={"hx-request": "true"},
        )

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # Should include only "Other" student
        self.assertIn("Student Other", response_content)

        # Should NOT include other school years
        self.assertNotIn("Student Year 1", response_content)
        self.assertNotIn("Student Year 7", response_content)
        self.assertNotIn("Student Year 12", response_content)
        self.assertNotIn("Student Higher Ed", response_content)

    def test_filter_requires_authentication(self):
        """Test that filtering requires user to be logged in."""
        response = self.client.post(
            reverse("people"), {"action": "filter_students", "status": "active"}, headers={"hx-request": "true"}
        )

        # Should redirect to login (302) or return 401/403
        self.assertIn(response.status_code, [302, 401, 403])

    def test_htmx_filter_response_format(self):
        """Test that filter responses return proper HTMX partial response."""
        # Create a test student
        student = self._create_student("Test Student", "test@test.com")

        self.client.force_login(self.teacher_user)

        # Perform HTMX filter
        response = self.client.post(
            reverse("people"), {"action": "filter_students", "status": "active"}, headers={"hx-request": "true"}
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

    def test_no_filters_returns_all_students(self):
        """Test that when no filters are applied, all students are returned."""
        # Create students with different statuses and school years
        active_student = self._create_student("Active Student", "active@test.com", is_active=True)
        inactive_student = self._create_student("Inactive Student", "inactive@test.com", is_active=False)

        self.client.force_login(self.teacher_user)

        # Request without filters (refresh action)
        response = self.client.post(reverse("people"), {"action": "refresh_students"}, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode()

        # Should include all students regardless of status
        self.assertIn("Active Student", response_content)
        self.assertIn("Inactive Student", response_content)
