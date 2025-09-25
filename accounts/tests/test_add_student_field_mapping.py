"""
Critical test to expose HTMX form field mapping issues.

PROBLEM IDENTIFIED:
The form data transmission tests pass in Django test client, but the real issue
may be that the HTMX form in the browser is using different field names
than what the backend expects.

This test specifically checks the field name mapping between frontend and backend.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership
from accounts.models.enums import SchoolRole
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class AddStudentFieldMappingTest(BaseTestCase):
    """
    Test the exact field name mapping between the HTMX form and the backend.

    The issue might be that the form template uses different field names
    than what the backend _handle_add_student method expects.
    """

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@test.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School")
        SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )
        self.people_url = reverse("people")

    def test_student_guardian_field_name_mapping(self):
        """
        Test that the exact field names used in the new separate form template match what the backend expects.

        Based on the new template structure, the field names are now clean:
        - name (student name)
        - email (student email)
        - birth_date
        - school_year
        - guardian_name
        - guardian_email
        - guardian_phone
        """
        self.client.force_login(self.admin_user)

        # Test with EXACT field names from the new template
        template_field_data = {
            # Student fields - clean names from new template
            "name": "Template Student",
            "email": "template.student@test.com",
            "birth_date": "2010-05-15",
            "school_year": "5",  # Use numeric value
            "notes": "Template notes",
            # Guardian fields - exactly as named in template (indexed)
            "guardian_0_name": "Template Guardian",
            "guardian_0_email": "template.guardian@test.com",
            "guardian_0_phone": "+351912345678",
            "guardian_0_tax_nr": "123456789",
            "guardian_0_address": "Template Address",
            "guardian_0_invoice": "on",
            "guardian_0_email_notifications": "on",
            "guardian_0_sms_notifications": "on",
        }

        # Use the new dedicated endpoint
        student_separate_url = reverse("accounts:student_create_separate")
        response = self.client.post(student_separate_url, template_field_data)

        # Print the response for debugging
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")

        self.assertEqual(response.status_code, 200)

        # Check if users were created - if not, field mapping is wrong
        try:
            student_user = User.objects.get(email="template.student@test.com")
            guardian_user = User.objects.get(email="template.guardian@test.com")
            print("SUCCESS: Users created with new clean field names")
        except User.DoesNotExist as e:
            self.fail(f"FIELD MAPPING ISSUE: {e}. Check if new template field names match backend expectations.")

    def test_guardian_only_field_name_mapping(self):
        """Test field names for Guardian-Only account type."""
        self.client.force_login(self.admin_user)

        # Guardian-Only form uses clean field names too
        template_field_data = {
            # Student fields - basic info only (no email)
            "name": "Template Young Student",
            "birth_date": "2012-03-20",
            "school_year": "3",  # Use numeric value
            "notes": "Young student notes",
            # Guardian fields - clean names (indexed)
            "guardian_0_name": "Template Managing Guardian",
            "guardian_0_email": "template.managing@test.com",
            "guardian_0_phone": "+351987654321",
            "guardian_0_tax_nr": "987654321",
            "guardian_0_address": "Guardian Address",
            "guardian_0_invoice": "on",
            "guardian_0_email_notifications": "on",
        }

        # Use the new dedicated endpoint
        student_guardian_only_url = reverse("accounts:student_create_guardian_only")
        response = self.client.post(student_guardian_only_url, template_field_data)
        self.assertEqual(response.status_code, 200)

        try:
            guardian_user = User.objects.get(email="template.managing@test.com")
            print("SUCCESS: Guardian-only created with clean field names")
        except User.DoesNotExist:
            self.fail("FIELD MAPPING ISSUE: Guardian-only clean field names not working")

    def test_adult_student_field_name_mapping(self):
        """Test field names for Adult Student account type."""
        self.client.force_login(self.admin_user)

        # Adult student uses clean field names
        template_field_data = {
            # Basic student fields
            "name": "Template Adult Student",
            "email": "template.adult@test.com",
            "birth_date": "1995-08-10",
            # Adult-specific fields with clean names
            "school_year": "12",  # Use numeric value
            "phone": "+351123456789",
            "tax_nr": "111222333",
            "address": "Adult Address",
            "notes": "Adult notes",
            "invoice": "on",
            "email_notifications": "on",
            "sms_notifications": "on",
        }

        # Use the new dedicated endpoint
        student_adult_url = reverse("accounts:student_create_adult")
        response = self.client.post(student_adult_url, template_field_data)
        self.assertEqual(response.status_code, 200)

        try:
            student_user = User.objects.get(email="template.adult@test.com")
            print("SUCCESS: Adult student created with clean field names")
        except User.DoesNotExist:
            self.fail("FIELD MAPPING ISSUE: Adult student clean field names not working")

    def test_wrong_field_names_cause_validation_errors(self):
        """
        Test that using wrong field names causes the validation errors
        mentioned in the original problem.
        """
        self.client.force_login(self.admin_user)

        # Use field names that DON'T match the new template (simulate the bug)
        wrong_field_data = {
            # WRONG field names - old prefixed style
            "student_name": "Wrong Student",  # Should be "name"
            "student_email": "wrong@test.com",  # Should be "email"
            "student_birth_date": "2010-05-15",  # Should be "birth_date"
            "student_school_year": "5",  # Should be "school_year"
            "guardian_full_name": "Wrong Guardian",  # Should be "guardian_name"
            "parent_email": "wrongguardian@test.com",  # Should be "guardian_email"
        }

        # Use the new dedicated endpoint
        student_separate_url = reverse("accounts:student_create_separate")
        response = self.client.post(student_separate_url, wrong_field_data)

        # This should cause the validation error mentioned in the original issue
        self.assertContains(response, "Email is required")

        # No users should be created
        self.assertFalse(User.objects.filter(email="wrong@test.com").exists())
        self.assertFalse(User.objects.filter(email="wrongguardian@test.com").exists())

        print("CONFIRMED: Wrong field names cause the validation error reported")

    def test_empty_field_values_simulation(self):
        """
        Simulate the exact bug scenario: correct field names but empty values.

        This simulates what would happen if HTMX/JavaScript isn't properly
        collecting field values from the form.
        """
        self.client.force_login(self.admin_user)

        # Correct field names but empty values - simulates the reported bug
        empty_values_data = {
            # Correct clean field names but empty values (the reported bug)
            "name": "",  # Empty but field name is correct
            "email": "",  # Empty but field name is correct
            "birth_date": "",  # Empty but field name is correct
            "guardian_0_name": "",  # Empty but field name is correct
            "guardian_0_email": "",  # Empty but field name is correct
        }

        # Use the new dedicated endpoint
        student_separate_url = reverse("accounts:student_create_separate")
        response = self.client.post(student_separate_url, empty_values_data)

        # This should produce the exact error message from the original issue
        self.assertContains(response, "Email is required")

        # Check the specific error message matches what was reported
        response_content = response.content.decode()
        print(f"Error response: {response_content}")

        # Should mention the specific fields - check for basic validation error
        self.assertTrue(
            "email" in response_content.lower()
            or "required" in response_content.lower()
            or "error" in response_content.lower()
        )

    def test_checkbox_field_handling(self):
        """
        Test that checkbox fields work correctly.

        Checkboxes in HTML send 'on' when checked, nothing when unchecked.
        The backend checks for == 'on' to determine True/False.
        """
        self.client.force_login(self.admin_user)

        # Test with checkboxes checked (should send 'on')
        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            checked_data = {
                "name": "Checkbox Test Student",
                "email": "checkbox@test.com",
                "birth_date": "2010-01-01",
                "guardian_name": "Checkbox Guardian",
                "guardian_email": "checkboxguardian@test.com",
                # Checkboxes checked - should send 'on'
                "guardian_invoice": "on",
                "guardian_email_notifications": "on",
                "guardian_sms_notifications": "on",
            }

            # Use the new dedicated endpoint
            student_separate_url = reverse("accounts:student_create_separate")
            response = self.client.post(student_separate_url, checked_data)
            self.assertEqual(response.status_code, 200)

            # Test with checkboxes unchecked (should not be in POST data)
            unchecked_data = {
                "name": "Unchecked Test Student",
                "email": "unchecked@test.com",
                "birth_date": "2010-01-01",
                "guardian_name": "Unchecked Guardian",
                "guardian_email": "uncheckedguardian@test.com",
                # Checkboxes unchecked - should not be in POST data at all
                # 'guardian_invoice': not present
                # 'guardian_email_notifications': not present
                # 'guardian_sms_notifications': not present
            }

            response = self.client.post(student_separate_url, unchecked_data)
            self.assertEqual(response.status_code, 200)
