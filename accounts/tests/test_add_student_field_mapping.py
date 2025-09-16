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
        Test that the exact field names used in the template match what the backend expects.

        Based on the template, the field names should be:
        - student_name (not name)
        - student_email (not email)
        - birth_date (not student_birth_date)
        - student_school_year (not school_year)
        - guardian_name (not name)
        - guardian_email (not email)
        - guardian_phone (not phone)
        """
        self.client.force_login(self.admin_user)

        # Test with EXACT field names from the template
        template_field_data = {
            "action": "add_student",
            "account_type": "separate",
            # Student fields - exactly as named in template
            "student_name": "Template Student",
            "student_email": "template.student@test.com",
            "birth_date": "2010-05-15",  # Note: birth_date not student_birth_date
            "student_school_year": "5º ano",
            "student_notes": "Template notes",
            # Guardian fields - exactly as named in template
            "guardian_name": "Template Guardian",
            "guardian_email": "template.guardian@test.com",
            "guardian_phone": "+351912345678",
            "guardian_tax_nr": "123456789",
            "guardian_address": "Template Address",
            "guardian_invoice": "on",
            "guardian_email_notifications": "on",
            "guardian_sms_notifications": "on",
        }

        response = self.client.post(self.people_url, template_field_data)

        # Print the response for debugging
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")

        self.assertEqual(response.status_code, 200)

        # Check if users were created - if not, field mapping is wrong
        try:
            student_user = User.objects.get(email="template.student@test.com")
            guardian_user = User.objects.get(email="template.guardian@test.com")
            print("SUCCESS: Users created with template field names")
        except User.DoesNotExist as e:
            self.fail(f"FIELD MAPPING ISSUE: {e}. Check if template field names match backend expectations.")

    def test_guardian_only_field_name_mapping(self):
        """Test field names for Guardian-Only account type."""
        self.client.force_login(self.admin_user)

        # Based on template analysis, Guardian-Only uses prefixed field names
        template_field_data = {
            "action": "add_student",
            "account_type": "guardian_only",
            # Student fields - basic info only
            "student_name": "Template Young Student",
            "birth_date": "2012-03-20",  # Note: birth_date not student_birth_date
            "guardian_only_student_school_year": "3º ano",  # Prefixed!
            "guardian_only_student_notes": "Young student notes",  # Prefixed!
            # Guardian fields - all prefixed for guardian_only type
            "guardian_name": "Template Managing Guardian",
            "guardian_email": "template.managing@test.com",
            "guardian_only_guardian_phone": "+351987654321",  # Prefixed!
            "guardian_only_guardian_tax_nr": "987654321",  # Prefixed!
            "guardian_only_guardian_address": "Guardian Address",  # Prefixed!
            "guardian_only_guardian_invoice": "on",  # Prefixed!
            "guardian_only_guardian_email_notifications": "on",  # Prefixed!
        }

        response = self.client.post(self.people_url, template_field_data)
        self.assertEqual(response.status_code, 200)

        try:
            guardian_user = User.objects.get(email="template.managing@test.com")
            print("SUCCESS: Guardian-only created with prefixed field names")
        except User.DoesNotExist:
            self.fail("FIELD MAPPING ISSUE: Guardian-only prefixed field names not working")

    def test_adult_student_field_name_mapping(self):
        """Test field names for Adult Student account type."""
        self.client.force_login(self.admin_user)

        # Adult student uses 'self_' prefixes for many fields
        template_field_data = {
            "action": "add_student",
            "account_type": "self",
            # Basic student fields
            "student_name": "Template Adult Student",
            "student_email": "template.adult@test.com",
            "birth_date": "1995-08-10",  # Note: birth_date not student_birth_date
            # Adult-specific fields with 'self_' prefix
            "self_school_year": "12º ano",  # Prefixed!
            "self_phone": "+351123456789",  # Prefixed!
            "self_tax_nr": "111222333",  # Prefixed!
            "self_address": "Adult Address",  # Prefixed!
            "self_notes": "Adult notes",  # Prefixed!
            "self_invoice": "on",  # Prefixed!
            "self_email_notifications": "on",  # Prefixed!
            "self_sms_notifications": "on",  # Prefixed!
        }

        response = self.client.post(self.people_url, template_field_data)
        self.assertEqual(response.status_code, 200)

        try:
            student_user = User.objects.get(email="template.adult@test.com")
            print("SUCCESS: Adult student created with self_ prefixed field names")
        except User.DoesNotExist:
            self.fail("FIELD MAPPING ISSUE: Adult student self_ prefixed field names not working")

    def test_wrong_field_names_cause_validation_errors(self):
        """
        Test that using wrong field names causes the validation errors
        mentioned in the original problem.
        """
        self.client.force_login(self.admin_user)

        # Use field names that DON'T match the template (simulate the bug)
        wrong_field_data = {
            "action": "add_student",
            "account_type": "separate",
            # WRONG field names - what happens if browser sends these?
            "name": "Wrong Student",  # Should be student_name
            "email": "wrong@test.com",  # Should be student_email
            "student_birth_date": "2010-05-15",  # Should be birth_date
            "school_year": "5º ano",  # Should be student_school_year
            "guardian_full_name": "Wrong Guardian",  # Should be guardian_name
            "parent_email": "wrongguardian@test.com",  # Should be guardian_email
        }

        response = self.client.post(self.people_url, wrong_field_data)

        # This should cause the validation error mentioned in the original issue
        self.assertContains(response, "Missing required fields")

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
            "action": "add_student",
            "account_type": "separate",
            # Correct field names but empty values (the reported bug)
            "student_name": "",  # Empty but field name is correct
            "student_email": "",  # Empty but field name is correct
            "birth_date": "",  # Empty but field name is correct
            "guardian_name": "",  # Empty but field name is correct
            "guardian_email": "",  # Empty but field name is correct
        }

        response = self.client.post(self.people_url, empty_values_data)

        # This should produce the exact error message from the original issue
        self.assertContains(response, "Missing required fields")

        # Check the specific error message matches what was reported
        response_content = response.content.decode()
        print(f"Error response: {response_content}")

        # Should mention the specific fields
        self.assertTrue(
            "student name" in response_content.lower()
            or "student email" in response_content.lower()
            or "guardian name" in response_content.lower()
            or "guardian email" in response_content.lower()
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
                "action": "add_student",
                "account_type": "separate",
                "student_name": "Checkbox Test Student",
                "student_email": "checkbox@test.com",
                "birth_date": "2010-01-01",
                "guardian_name": "Checkbox Guardian",
                "guardian_email": "checkboxguardian@test.com",
                # Checkboxes checked - should send 'on'
                "guardian_invoice": "on",
                "guardian_email_notifications": "on",
                "guardian_sms_notifications": "on",
            }

            response = self.client.post(self.people_url, checked_data)
            self.assertEqual(response.status_code, 200)

            # Test with checkboxes unchecked (should not be in POST data)
            unchecked_data = {
                "action": "add_student",
                "account_type": "separate",
                "student_name": "Unchecked Test Student",
                "student_email": "unchecked@test.com",
                "birth_date": "2010-01-01",
                "guardian_name": "Unchecked Guardian",
                "guardian_email": "uncheckedguardian@test.com",
                # Checkboxes unchecked - should not be in POST data at all
                # 'guardian_invoice': not present
                # 'guardian_email_notifications': not present
                # 'guardian_sms_notifications': not present
            }

            response = self.client.post(self.people_url, unchecked_data)
            self.assertEqual(response.status_code, 200)
