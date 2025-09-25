"""
Comprehensive test suite for Add Student forms functionality.

CRITICAL ISSUE DISCOVERED:
The Add Student forms appear to work in the UI but no data reaches the backend.
Server logs show: "name=, email=, birth_date=, guardian_name=, guardian_email="
Even when all fields are filled correctly in the browser.

This test suite is designed to expose and catch the form data transmission bug
that prevents any student creation despite the UI appearing to work correctly.

The system must support three account types:
1. STUDENT_GUARDIAN ("separate") - Both student and guardian have accounts
2. GUARDIAN_ONLY ("guardian_only") - Only guardian has account, manages child
3. ADULT_STUDENT ("self") - Student manages everything independently

Each account type has different field requirements and creates different database objects.
"""

import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership
from accounts.models.educational import EducationalSystem
from accounts.models.enums import SchoolRole
from accounts.models.profiles import GuardianProfile, StudentProfile
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class AddStudentFormDataTransmissionTest(BaseTestCase):
    """
    CRITICAL TEST: Verify form data actually reaches the backend.

    This is the most important test - it should expose the current bug
    where form fields appear filled in the UI but reach the backend as empty strings.
    """

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@test.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        self.people_url = reverse("people")
        # New dedicated student creation endpoints
        self.student_separate_url = reverse("accounts:student_create_separate")
        self.student_guardian_only_url = reverse("accounts:student_create_guardian_only")
        self.student_adult_url = reverse("accounts:student_create_adult")

    def test_form_data_transmission_student_guardian_type(self):
        """
        CRITICAL: Test that Student+Guardian form data actually reaches backend.

        This test should FAIL with current implementation, exposing the bug
        where all field values arrive as empty strings at the backend.
        """
        self.client.force_login(self.admin_user)

        # Real form data that a user would fill in browser
        form_data = {
            "name": "Test Student Name",
            "email": "test.student@example.com",
            "birth_date": "2010-05-15",
            "school_year": "5",  # Use numeric value
            "notes": "Test student notes",
            "guardian_0_name": "Test Guardian Name",
            "guardian_0_email": "test.guardian@example.com",
            "guardian_0_phone": "+351912345678",
            "guardian_0_tax_nr": "123456789",
            "guardian_0_address": "Test Address, Lisboa",
            "guardian_0_invoice": "on",
            "guardian_0_email_notifications": "on",
            "guardian_0_sms_notifications": "on",
        }

        # This request should work with the new dedicated endpoint
        response = self.client.post(self.student_separate_url, form_data)

        # If this assertion fails, it means the form data is not reaching the backend
        # The backend will return an error about missing required fields
        # even though we're sending them correctly
        self.assertEqual(response.status_code, 200)

        # These assertions will FAIL if the bug exists
        # because no users will be created when data doesn't transmit
        try:
            student_user = User.objects.get(email="test.student@example.com")
            guardian_user = User.objects.get(email="test.guardian@example.com")

            # If we get here, data transmission worked
            self.assertEqual(student_user.name, "Test Student Name")
            self.assertEqual(guardian_user.name, "Test Guardian Name")

            # Verify profiles were created
            student_profile = StudentProfile.objects.get(user=student_user)
            guardian_profile = GuardianProfile.objects.get(user=guardian_user)

            self.assertEqual(student_profile.account_type, "STUDENT_GUARDIAN")
            self.assertEqual(student_profile.school_year, "5")
            self.assertEqual(student_profile.guardian, guardian_profile)

        except User.DoesNotExist:
            self.fail(
                "FORM DATA TRANSMISSION BUG CONFIRMED: "
                "No users were created despite sending valid form data. "
                "Check server logs - you'll see empty field values even though form data was sent."
            )

    def test_form_data_transmission_guardian_only_type(self):
        """
        CRITICAL: Test that Guardian-Only form data actually reaches backend.
        """
        self.client.force_login(self.admin_user)

        form_data = {
            "name": "Young Student Name",
            "birth_date": "2012-03-20",
            "school_year": "3",  # Use numeric value
            "notes": "Young student notes",
            "guardian_0_name": "Managing Guardian",
            "guardian_0_email": "managing.guardian@example.com",
            "guardian_0_phone": "+351987654321",
            "guardian_0_tax_nr": "987654321",
            "guardian_0_address": "Guardian Address",
            "guardian_0_invoice": "on",
            "guardian_0_email_notifications": "on",
        }

        response = self.client.post(self.student_guardian_only_url, form_data)

        self.assertEqual(response.status_code, 200)

        try:
            # Only guardian user should exist
            guardian_user = User.objects.get(email="managing.guardian@example.com")
            self.assertEqual(guardian_user.name, "Managing Guardian")

            # Student profile should exist without user account
            guardian_profile = GuardianProfile.objects.get(user=guardian_user)
            student_profile = StudentProfile.objects.get(guardian=guardian_profile, user=None)

            self.assertEqual(student_profile.account_type, "GUARDIAN_ONLY")
            self.assertEqual(student_profile.school_year, "3")

        except User.DoesNotExist:
            self.fail("FORM DATA TRANSMISSION BUG CONFIRMED: Guardian-only form data not reaching backend properly.")

    def test_form_data_transmission_adult_student_type(self):
        """
        CRITICAL: Test that Adult Student form data actually reaches backend.
        """
        self.client.force_login(self.admin_user)

        form_data = {
            "name": "Adult Student Name",
            "email": "adult.student@example.com",
            "birth_date": "1995-08-10",
            "school_year": "12",  # Use numeric value
            "phone": "+351123456789",
            "tax_nr": "111222333",
            "address": "Adult Address",
            "notes": "Adult student notes",
            "invoice": "on",
            "email_notifications": "on",
        }

        response = self.client.post(self.student_adult_url, form_data)

        self.assertEqual(response.status_code, 200)

        try:
            student_user = User.objects.get(email="adult.student@example.com")
            self.assertEqual(student_user.name, "Adult Student Name")

            student_profile = StudentProfile.objects.get(user=student_user)
            self.assertEqual(student_profile.account_type, "ADULT_STUDENT")
            self.assertEqual(student_profile.school_year, "12")
            # Adult student is their own guardian
            self.assertIsNotNone(student_profile.guardian)
            self.assertEqual(student_profile.guardian.user, student_user)

        except User.DoesNotExist:
            self.fail("FORM DATA TRANSMISSION BUG CONFIRMED: Adult student form data not reaching backend properly.")


class AddStudentFormFieldDisplayTest(BaseTestCase):
    """
    Test that forms display the correct fields for each account type.

    These tests verify the frontend form structure is correct,
    but they won't catch the data transmission bug.
    """

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@test.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        self.people_url = reverse("people")

    def test_student_guardian_form_displays_all_required_fields(self):
        """Test that Student+Guardian form shows both student and guardian sections."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        # Student section fields - now using clean names
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="birth_date"')
        self.assertContains(response, 'name="school_year"')
        self.assertContains(response, 'name="notes"')

        # Guardian section fields
        self.assertContains(response, 'name="guardian_0_name"')
        self.assertContains(response, 'name="guardian_0_email"')
        self.assertContains(response, 'name="guardian_0_phone"')
        self.assertContains(response, 'name="guardian_0_tax_nr"')
        self.assertContains(response, 'name="guardian_0_address"')

    def test_guardian_only_form_hides_student_email_field(self):
        """Test that Guardian-Only form doesn't show student email field."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        # Should have student basic info but NO student email
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="birth_date"')
        # Guardian fields should exist with indexed names (primary guardian = index 0)
        self.assertContains(response, 'name="guardian_0_name"')
        self.assertContains(response, 'name="guardian_0_email"')
        self.assertContains(response, 'name="guardian_0_phone"')

    def test_adult_student_form_hides_guardian_section(self):
        """Test that Adult Student form shows no guardian fields."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        # Should have all student fields including financial ones
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="birth_date"')
        self.assertContains(response, 'name="phone"')
        self.assertContains(response, 'name="tax_nr"')
        self.assertContains(response, 'name="address"')

    def test_account_type_tabs_present(self):
        """Test that all three account type tabs are available in DaisyUI structure."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        # Check for DaisyUI tab structure with the three form types
        self.assertContains(response, "Student with Guardian")  # Tab label
        self.assertContains(response, "Guardian-Only Account")  # Tab label
        self.assertContains(response, "Adult Student")  # Tab label

        # Check that form submission endpoints exist in the forms
        self.assertContains(response, "/students/create/separate/")
        self.assertContains(response, "/students/create/guardian-only/")
        self.assertContains(response, "/students/create/adult/")


class AddStudentFormValidationTest(BaseTestCase):
    """
    Test validation logic for each account type.

    These tests verify that proper validation occurs,
    assuming form data reaches the backend correctly.
    """

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@test.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        self.people_url = reverse("people")
        # New dedicated student creation endpoints
        self.student_separate_url = reverse("accounts:student_create_separate")
        self.student_guardian_only_url = reverse("accounts:student_create_guardian_only")
        self.student_adult_url = reverse("accounts:student_create_adult")

    def test_student_guardian_requires_both_emails(self):
        """Test that Student+Guardian type requires both student and guardian emails."""
        self.client.force_login(self.admin_user)

        # Missing guardian email
        form_data = {
            "name": "Test Student",
            "email": "student@test.com",
            "birth_date": "2010-01-01",
            "guardian_0_name": "Test Guardian",
            # Missing guardian_email
        }

        response = self.client.post(self.student_separate_url, form_data)
        # Check for validation error in response
        self.assertTrue("required" in response.content.decode().lower() or "error" in response.content.decode().lower())

    def test_guardian_only_requires_no_student_email(self):
        """Test that Guardian-Only type should NOT require student email."""
        self.client.force_login(self.admin_user)

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            form_data = {
                "name": "Young Student",
                "birth_date": "2012-01-01",
                "guardian_name": "Managing Guardian",
                "guardian_email": "guardian@test.com",
            }

            response = self.client.post(self.student_guardian_only_url, form_data)
            # Should succeed without student email
            self.assertEqual(response.status_code, 200)

    def test_adult_student_requires_student_email_no_guardian(self):
        """Test that Adult Student type requires student email but no guardian fields."""
        self.client.force_login(self.admin_user)

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            form_data = {
                "name": "Adult Student",
                "email": "adult@test.com",
                "birth_date": "1995-01-01",
                # No guardian fields needed
            }

            response = self.client.post(self.student_adult_url, form_data)
            self.assertEqual(response.status_code, 200)

    def test_empty_form_data_validation_error(self):
        """
        CRITICAL: Test what happens when completely empty form data is sent.

        This simulates the current bug condition where form fields
        reach the backend as empty strings.
        """
        self.client.force_login(self.admin_user)

        # Simulate the bug: form says it has data but backend receives empty values
        form_data = {
            "name": "",  # Empty - simulates current bug
            "email": "",  # Empty - simulates current bug
            "birth_date": "",  # Empty - simulates current bug
            "guardian_0_name": "",  # Empty - simulates current bug
            "guardian_0_email": "",  # Empty - simulates current bug
        }

        response = self.client.post(self.student_separate_url, form_data)

        # Should return validation error, not crash
        self.assertEqual(response.status_code, 200)
        # Check for validation error in response
        self.assertTrue("required" in response.content.decode().lower() or "error" in response.content.decode().lower())

        # No users should be created
        self.assertEqual(User.objects.filter(email__contains="test").count(), 1)  # Only admin


class AddStudentAccountCreationTest(BaseTestCase):
    """
    Test that correct database objects are created for each account type.

    These tests verify the business logic works correctly,
    assuming form data reaches the backend.
    """

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@test.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        self.people_url = reverse("people")
        # New dedicated student creation endpoints
        self.student_separate_url = reverse("accounts:student_create_separate")
        self.student_guardian_only_url = reverse("accounts:student_create_guardian_only")
        self.student_adult_url = reverse("accounts:student_create_adult")

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_student_guardian_creates_both_accounts(self, mock_setup):
        """Test that Student+Guardian creates both user accounts and profiles."""
        self.client.force_login(self.admin_user)

        form_data = {
            "name": "Test Student",
            "email": "student@test.com",
            "birth_date": "2010-01-01",
            "school_year": "5",
            "notes": "Test notes",
            "guardian_0_name": "Test Guardian",
            "guardian_0_email": "guardian@test.com",
            "guardian_0_phone": "+351123456789",
            "guardian_0_tax_nr": "123456789",
            "guardian_0_address": "Test Address",
            "guardian_0_email_notifications": "on",
        }

        response = self.client.post(self.student_separate_url, form_data)
        self.assertEqual(response.status_code, 200)

        # Both users should exist
        student_user = User.objects.get(email="student@test.com")
        guardian_user = User.objects.get(email="guardian@test.com")

        # Both profiles should exist and be linked
        student_profile = StudentProfile.objects.get(user=student_user)
        guardian_profile = GuardianProfile.objects.get(user=guardian_user)

        self.assertEqual(student_profile.account_type, "STUDENT_GUARDIAN")
        self.assertEqual(student_profile.guardian, guardian_profile)

        # Both should have school memberships
        self.assertTrue(
            SchoolMembership.objects.filter(user=student_user, school=self.school, role=SchoolRole.STUDENT).exists()
        )
        self.assertTrue(
            SchoolMembership.objects.filter(user=guardian_user, school=self.school, role=SchoolRole.GUARDIAN).exists()
        )

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_guardian_only_creates_guardian_account_only(self, mock_setup):
        """Test that Guardian-Only creates only guardian account."""
        self.client.force_login(self.admin_user)

        form_data = {
            "name": "Young Child",
            "birth_date": "2012-01-01",
            "school_year": "3",
            "notes": "Young child notes",
            "guardian_0_name": "Managing Guardian",
            "guardian_0_email": "managing@test.com",
            "guardian_0_phone": "+351987654321",
        }

        response = self.client.post(self.student_guardian_only_url, form_data)
        self.assertEqual(response.status_code, 200)

        # Only guardian user should exist
        guardian_user = User.objects.get(email="managing@test.com")

        # Guardian profile should exist
        guardian_profile = GuardianProfile.objects.get(user=guardian_user)

        # Student profile should exist but WITHOUT user account
        student_profile = StudentProfile.objects.get(guardian=guardian_profile, user=None)
        self.assertEqual(student_profile.account_type, "GUARDIAN_ONLY")

        # Only guardian should have school membership
        self.assertTrue(
            SchoolMembership.objects.filter(user=guardian_user, school=self.school, role=SchoolRole.GUARDIAN).exists()
        )

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_adult_student_creates_student_account_only(self, mock_setup):
        """Test that Adult Student creates only student account."""
        self.client.force_login(self.admin_user)

        form_data = {
            "name": "Adult Student",
            "email": "adult@test.com",
            "birth_date": "1990-01-01",
            "school_year": "12",
            "phone": "+351111222333",
            "tax_nr": "111222333",
            "address": "Adult Address",
            "notes": "Adult notes",
            "email_notifications": "on",
        }

        response = self.client.post(self.student_adult_url, form_data)
        self.assertEqual(response.status_code, 200)

        # Only student user should exist
        student_user = User.objects.get(email="adult@test.com")

        # Student profile should exist with student as their own guardian
        student_profile = StudentProfile.objects.get(user=student_user)
        self.assertEqual(student_profile.account_type, "ADULT_STUDENT")
        # Adult student is their own guardian
        self.assertIsNotNone(student_profile.guardian)
        self.assertEqual(student_profile.guardian.user, student_user)

        # Only student should have school membership
        self.assertTrue(
            SchoolMembership.objects.filter(user=student_user, school=self.school, role=SchoolRole.STUDENT).exists()
        )

        # Guardian profile should exist for the adult student (they are their own guardian)
        self.assertTrue(GuardianProfile.objects.filter(user=student_user).exists())


class AddStudentEdgeCaseTest(BaseTestCase):
    """
    Test edge cases and error conditions.
    """

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@test.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        self.people_url = reverse("people")
        # New dedicated student creation endpoints
        self.student_separate_url = reverse("accounts:student_create_separate")
        self.student_guardian_only_url = reverse("accounts:student_create_guardian_only")
        self.student_adult_url = reverse("accounts:student_create_adult")

    def test_duplicate_email_handling_student_guardian(self):
        """Test proper handling of duplicate emails in Student+Guardian type."""
        # Create existing user
        existing_user = User.objects.create_user(email="existing@test.com", name="Existing User")

        self.client.force_login(self.admin_user)

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            form_data = {
                "name": "New Student",
                "email": "existing@test.com",  # Duplicate email
                "birth_date": "2010-01-01",
                "guardian_0_name": "New Guardian",
                "guardian_0_email": "newguardian@test.com",
            }

            response = self.client.post(self.student_separate_url, form_data)

            # Should handle gracefully by using existing user
            self.assertEqual(response.status_code, 200)

            # Should still create profiles
            student_profile = StudentProfile.objects.get(user=existing_user)
            self.assertEqual(student_profile.account_type, "STUDENT_GUARDIAN")

    def test_malformed_birth_date_handling(self):
        """Test handling of malformed birth date."""
        self.client.force_login(self.admin_user)

        form_data = {
            "name": "Test Student",
            "email": "test@test.com",
            "birth_date": "invalid-date-format",  # Malformed date
        }

        response = self.client.post(self.student_adult_url, form_data)

        # Should handle gracefully with error message
        self.assertEqual(response.status_code, 200)

        # No user should be created
        self.assertFalse(User.objects.filter(email="test@test.com").exists())

    def test_missing_account_type_parameter(self):
        """Test handling when account_type parameter is missing."""
        self.client.force_login(self.admin_user)

        form_data = {
            "name": "Test Student",
            "email": "test@test.com",
        }

        response = self.client.post(self.student_separate_url, form_data)

        # Should handle gracefully
        self.assertEqual(response.status_code, 200)

    def test_database_rollback_on_permission_setup_failure(self):
        """Test that database changes are rolled back if permission setup fails."""
        self.client.force_login(self.admin_user)

        form_data = {
            "name": "Test Student",
            "email": "rollback@test.com",
            "birth_date": "1990-01-01",
        }

        # Mock permission setup to fail
        with patch(
            "accounts.permissions.PermissionService.setup_permissions_for_student",
            side_effect=Exception("Permission setup failed"),
        ):
            response = self.client.post(self.student_adult_url, form_data)

            # Should return error
            self.assertEqual(response.status_code, 200)
            # Check for any error response
            self.assertTrue(
                "error" in response.content.decode().lower()
                or "failed" in response.content.decode().lower()
                or response.status_code != 200
            )

            # No user should be created (transaction rolled back)
            self.assertFalse(User.objects.filter(email="rollback@test.com").exists())


class AddStudentIntegrationTest(BaseTestCase):
    """
    End-to-end integration tests that verify complete workflows.
    """

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@test.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        self.people_url = reverse("people")
        # New dedicated student creation endpoints
        self.student_separate_url = reverse("accounts:student_create_separate")
        self.student_guardian_only_url = reverse("accounts:student_create_guardian_only")
        self.student_adult_url = reverse("accounts:student_create_adult")

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_complete_form_submission_to_user_creation_workflow(self, mock_setup):
        """
        Test complete workflow from form submission to database object creation.

        This integration test verifies the entire flow works end-to-end
        for all three account types.
        """
        self.client.force_login(self.admin_user)

        # Test Student+Guardian workflow
        student_guardian_data = {
            "name": "Integration Student",
            "email": "integration.student@test.com",
            "birth_date": "2008-06-15",
            "school_year": "8",
            "guardian_0_name": "Integration Guardian",
            "guardian_0_email": "integration.guardian@test.com",
            "guardian_0_email_notifications": "on",
        }

        response = self.client.post(self.student_separate_url, student_guardian_data)
        self.assertEqual(response.status_code, 200)

        # Verify complete object creation
        student_user = User.objects.get(email="integration.student@test.com")
        guardian_user = User.objects.get(email="integration.guardian@test.com")

        student_profile = StudentProfile.objects.get(user=student_user)
        guardian_profile = GuardianProfile.objects.get(user=guardian_user)

        # Verify relationships
        self.assertEqual(student_profile.guardian, guardian_profile)

        # Verify memberships
        self.assertTrue(SchoolMembership.objects.filter(user=student_user, school=self.school).exists())
        self.assertTrue(SchoolMembership.objects.filter(user=guardian_user, school=self.school).exists())

        # Verify permission setup called
        mock_setup.assert_called_with(student_profile)

    def test_form_submission_error_handling_preserves_system_integrity(self):
        """Test that form submission errors don't corrupt the system state."""
        self.client.force_login(self.admin_user)

        # Send invalid form data
        invalid_data = {
            "name": "",  # Invalid/empty data
        }

        response = self.client.post(self.student_separate_url, invalid_data)

        # Should handle gracefully
        self.assertEqual(response.status_code, 200)

        # System should remain in consistent state
        # Only admin user should exist
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(StudentProfile.objects.count(), 0)
        self.assertEqual(GuardianProfile.objects.count(), 0)

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_all_three_account_types_can_coexist(self, mock_setup):
        """Test that all three account types can be created in the same school."""
        self.client.force_login(self.admin_user)

        # Create Student+Guardian
        response1 = self.client.post(
            self.student_separate_url,
            {
                "name": "Mixed Student",
                "email": "mixed.student@test.com",
                "birth_date": "2010-01-01",
                "guardian_0_name": "Mixed Guardian",
                "guardian_0_email": "mixed.guardian@test.com",
            },
        )
        self.assertEqual(response1.status_code, 200)

        # Create Guardian-Only
        response2 = self.client.post(
            self.student_guardian_only_url,
            {
                "name": "Young Mixed",
                "birth_date": "2013-01-01",
                "guardian_0_name": "Solo Guardian",
                "guardian_0_email": "solo.guardian@test.com",
            },
        )
        self.assertEqual(response2.status_code, 200)

        # Create Adult Student
        response3 = self.client.post(
            self.student_adult_url,
            {
                "name": "Adult Mixed",
                "email": "adult.mixed@test.com",
                "birth_date": "1992-01-01",
            },
        )
        self.assertEqual(response3.status_code, 200)

        # Verify all types exist
        student_guardian = StudentProfile.objects.get(account_type="STUDENT_GUARDIAN")
        guardian_only = StudentProfile.objects.get(account_type="GUARDIAN_ONLY")
        adult_student = StudentProfile.objects.get(account_type="ADULT_STUDENT")

        # Verify different account type characteristics
        self.assertIsNotNone(student_guardian.user)
        self.assertIsNotNone(student_guardian.guardian)

        self.assertIsNone(guardian_only.user)
        self.assertIsNotNone(guardian_only.guardian)

        self.assertIsNotNone(adult_student.user)
        # Adult student has a guardian profile (themselves)
        self.assertIsNotNone(adult_student.guardian)
        self.assertEqual(adult_student.guardian.user, adult_student.user)


class StudentCreationRefreshTest(BaseTestCase):
    """
    Test automatic refresh functionality after student creation.

    This addresses the bug where the students list doesn't automatically refresh
    after creating a new student, requiring users to manually refresh the page.
    """

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@test.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        self.student_separate_url = reverse("accounts:student_create_separate")

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_successful_student_creation_triggers_list_refresh(self, mock_setup):
        """
        Test that successful student creation returns HTMX headers to trigger students list refresh.

        This is the core test for the refresh bug. After successful student creation,
        the response should include HTMX trigger headers to refresh the students list.
        """
        self.client.force_login(self.admin_user)

        form_data = {
            "name": "New Student For Refresh",
            "email": "newstudent@refresh.test",
            "birth_date": "2010-01-01",
            "guardian_0_name": "Guardian For Refresh",
            "guardian_0_email": "guardian@refresh.test",
        }

        # Simulate HTMX request
        response = self.client.post(
            self.student_separate_url, form_data, headers={"hx-request": "true", "hx-target": "#message-area"}
        )

        self.assertEqual(response.status_code, 200)

        # Verify student was created successfully
        self.assertTrue(User.objects.filter(email="newstudent@refresh.test").exists())

        # Critical test: Response should include HTMX trigger to refresh students list
        # This is what's currently missing and causes the bug
        hx_trigger = response.get("HX-Trigger")
        if hx_trigger:
            # If HX-Trigger exists, it should include refreshStudents event
            self.assertIn("refreshStudents", hx_trigger)
        else:
            # If no HX-Trigger header, this confirms the bug exists
            # The test documents the expected behavior for fixing the issue
            self.fail(
                "REFRESH BUG CONFIRMED: No HX-Trigger header found in response. "
                "Expected 'refreshStudents' trigger to automatically refresh the students list."
            )

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_htmx_out_of_band_swap_for_students_list(self, mock_setup):
        """
        Test alternative approach: HTMX out-of-band swap to refresh students list.

        Instead of using HX-Trigger, the response could include an out-of-band swap
        that directly updates the #students-content container.
        """
        self.client.force_login(self.admin_user)

        form_data = {
            "name": "OOB Test Student",
            "email": "oob@test.com",
            "birth_date": "2010-01-01",
            "guardian_0_name": "OOB Guardian",
            "guardian_0_email": "oob.guardian@test.com",
        }

        response = self.client.post(self.student_separate_url, form_data, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)

        # Verify student was created
        self.assertTrue(User.objects.filter(email="oob@test.com").exists())

        response_content = response.content.decode()

        # Check if response includes out-of-band swap for students list
        # This would be an alternative solution to the refresh bug
        if "hx-swap-oob" in response_content and "students-content" in response_content:
            # Out-of-band swap approach is implemented
            self.assertIn('id="students-content"', response_content)
            self.assertIn('hx-swap-oob="true"', response_content)
        else:
            # Document that out-of-band swap is not currently implemented
            # This is another potential solution for the refresh bug
            print("INFO: Out-of-band swap not implemented. Students list won't auto-refresh.")
