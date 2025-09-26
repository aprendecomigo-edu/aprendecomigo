"""
Tests for GitHub Issue 288 - Adding "Ensino Superior" and "Outro" options to school year dropdown.

This test suite ensures that:
1. All student creation forms display the new school year options ("Ensino Superior", "Outro")
2. StudentProfile model correctly saves the new school year values
3. Form validation accepts the new school year choices

Current functionality: Students can select Years 1-12
New functionality: Students can also select "Ensino Superior" (Higher Education) and "Outro" (Other)
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership
from accounts.models.enums import SchoolRole
from accounts.models.profiles import GuardianProfile, StudentProfile
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class SchoolYearDropdownOptionsTest(BaseTestCase):
    """Test that all three student forms display the enhanced school year options."""

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@test.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        self.people_url = reverse("people")

    def test_student_separate_form_displays_new_school_year_options(self):
        """Test that Student+Guardian form displays "Ensino Superior" and "Outro" options."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        # Verify form displays new school year options
        self.assertContains(response, 'value="ensino_superior"')
        self.assertContains(response, 'value="outro"')

        # Verify the option labels are correct
        self.assertContains(response, "Ensino Superior")
        self.assertContains(response, "Outro")

        # Ensure existing Year 1-12 options are still present
        self.assertContains(response, 'value="1"')
        self.assertContains(response, 'value="12"')

    def test_guardian_only_form_displays_new_school_year_options(self):
        """Test that Guardian-Only form displays "Ensino Superior" and "Outro" options."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        # Check guardian-only form section for new options
        self.assertContains(response, 'value="ensino_superior"')
        self.assertContains(response, 'value="outro"')

    def test_adult_student_form_displays_new_school_year_options(self):
        """Test that Adult Student form displays "Ensino Superior" and "Outro" options."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        # Check adult student form section for new options
        self.assertContains(response, 'value="ensino_superior"')
        self.assertContains(response, 'value="outro"')


class SchoolYearModelValidationTest(BaseTestCase):
    """Test that StudentProfile model correctly saves new school year values."""

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@test.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

    def test_student_profile_saves_ensino_superior_school_year(self):
        """Test that StudentProfile correctly saves "ensino_superior" school year."""
        student_user = User.objects.create_user(email="higher.ed@test.com", name="Higher Ed Student")

        # Create StudentProfile with "Ensino Superior" school year
        student_profile = StudentProfile.objects.create(
            user=student_user,
            name="Higher Ed Student",
            birth_date="1999-01-01",
            school_year="ensino_superior",  # New school year value
            account_type="ADULT_STUDENT",
        )

        # Verify it saves correctly
        saved_profile = StudentProfile.objects.get(id=student_profile.id)
        self.assertEqual(saved_profile.school_year, "ensino_superior")

    def test_student_profile_saves_outro_school_year(self):
        """Test that StudentProfile correctly saves "outro" school year."""
        student_user = User.objects.create_user(email="other.student@test.com", name="Other Student")

        # Create StudentProfile with "Outro" school year
        student_profile = StudentProfile.objects.create(
            user=student_user,
            name="Other Student",
            birth_date="2000-05-15",
            school_year="outro",  # New school year value
            account_type="ADULT_STUDENT",
        )

        # Verify it saves correctly
        saved_profile = StudentProfile.objects.get(id=student_profile.id)
        self.assertEqual(saved_profile.school_year, "outro")
