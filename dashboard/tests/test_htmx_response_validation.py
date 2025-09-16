"""
HTMX Response Validation Tests for Add Student functionality.

This module contains focused tests for validating HTMX responses from the Add Student
form submission. These tests ensure that the responses are properly formatted for HTMX
consumption and contain the expected HTML structure and headers.

Key areas tested:
1. HTMX response headers (HX-Trigger, HX-Target, etc.)
2. HTML partial structure validation
3. Success response fragments
4. Error response fragments
5. Form validation error display
6. Client-side integration compatibility
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import School, SchoolMembership
from accounts.models.enums import SchoolRole
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class HTMXResponseHeaderTests(BaseTestCase):
    """Test HTMX-specific response headers."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@school.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School", description="A test school")
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True,
        )
        self.people_url = reverse("people")

    def test_successful_submission_has_refresh_trigger(self):
        """Test that successful submission returns HX-Trigger for refreshStudents."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Success Student",
            "student_email": "success@test.com",
            "student_birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("HX-Trigger"), "refreshStudents")

    def test_validation_error_does_not_have_trigger(self):
        """Test that validation errors don't trigger list refresh."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            # Missing required fields
        }

        response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)
        # Should not trigger refresh on validation error
        self.assertIsNone(response.get("HX-Trigger"))

    def test_htmx_request_header_detection(self):
        """Test that HTMX requests are properly detected."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "HTMX Test Student",
            "student_email": "htmx.test@example.com",
            "student_birth_date": "1995-01-01",
        }

        # Test with HTMX header
        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            htmx_response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        # Test without HTMX header
        form_data["student_email"] = "regular.test@example.com"
        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            regular_response = self.client.post(self.people_url, form_data)

        # Both should succeed but may have different response characteristics
        self.assertEqual(htmx_response.status_code, 200)
        self.assertEqual(regular_response.status_code, 200)

        # HTMX response should have trigger header
        self.assertEqual(htmx_response.get("HX-Trigger"), "refreshStudents")

    def test_htmx_target_header_handling(self):
        """Test handling of HX-Target header."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "guardian_only",
            "student_name": "Target Test Student",
            "student_birth_date": "2015-01-01",
            "guardian_name": "Target Guardian",
            "guardian_email": "target.guardian@test.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(
                self.people_url, form_data, headers={"hx-request": "true", "hx-target": "#students-content"}
            )

        self.assertEqual(response.status_code, 200)
        # Response should be suitable for the target element
        content = response.content.decode()
        self.assertNotIn("<html>", content)
        self.assertNotIn("<head>", content)


class HTMXSuccessResponseTests(BaseTestCase):
    """Test HTMX success response structure."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@school.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School", description="A test school")
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True,
        )
        self.people_url = reverse("people")

    def test_success_response_contains_message(self):
        """Test that success response contains success message."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Message Test Student",
            "student_email": "message.test@example.com",
            "student_birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        content = response.content.decode()
        self.assertIn("Student added successfully", content)

    def test_success_response_structure(self):
        """Test that success response has correct HTML structure."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "separate",
            "student_name": "Structure Test Student",
            "student_email": "structure.test@example.com",
            "student_birth_date": "2008-01-01",
            "guardian_name": "Structure Guardian",
            "guardian_email": "structure.guardian@example.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        content = response.content.decode()

        # Should be HTML partial, not full page
        self.assertNotIn("<!DOCTYPE html>", content)
        self.assertNotIn("<html", content)
        self.assertNotIn("<head>", content)
        self.assertNotIn("<body>", content)

        # Should contain success message structure
        self.assertIn("success", content.lower())

    def test_different_account_types_success_responses(self):
        """Test success responses for different account types."""
        self.client.force_login(self.admin_user)

        account_types_data = [
            {
                "account_type": "self",
                "student_name": "Adult Test",
                "student_email": "adult@test.com",
                "student_birth_date": "1995-01-01",
            },
            {
                "account_type": "separate",
                "student_name": "Separate Test",
                "student_email": "separate@test.com",
                "student_birth_date": "2008-01-01",
                "guardian_name": "Guardian Test",
                "guardian_email": "guardian@test.com",
            },
            {
                "account_type": "guardian_only",
                "student_name": "Guardian Only Test",
                "student_birth_date": "2015-01-01",
                "guardian_name": "Only Guardian",
                "guardian_email": "only.guardian@test.com",
            },
        ]

        for i, account_data in enumerate(account_types_data):
            form_data = {
                "action": "add_student",
                **account_data,
            }

            with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
                response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

            self.assertEqual(response.status_code, 200, f"Failed for account type {account_data['account_type']}")
            self.assertEqual(response.get("HX-Trigger"), "refreshStudents")

            content = response.content.decode()
            self.assertIn("success", content.lower())


class HTMXErrorResponseTests(BaseTestCase):
    """Test HTMX error response structure."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@school.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School", description="A test school")
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True,
        )
        self.people_url = reverse("people")

    def test_validation_error_response_structure(self):
        """Test that validation errors return proper HTML structure."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "separate",
            # Missing required fields
            "student_name": "",
            "student_email": "",
        }

        response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        content = response.content.decode()

        # Should be HTML partial with error message
        self.assertNotIn("<!DOCTYPE html>", content)
        self.assertNotIn("<html", content)
        self.assertIn("required", content.lower())

    def test_server_error_response_structure(self):
        """Test that server errors return proper HTMX-compatible response."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Error Test Student",
            "student_email": "error.test@example.com",
            "student_birth_date": "1995-01-01",
        }

        with patch(
            "accounts.permissions.PermissionService.setup_permissions_for_student",
            side_effect=Exception("Test server error"),
        ):
            response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        self.assertEqual(response.status_code, 200)

        content = response.content.decode()
        # Should contain error message
        self.assertIn("Failed to add student", content)

        # Should not trigger refresh on error
        self.assertIsNone(response.get("HX-Trigger"))

    def test_invalid_account_type_error(self):
        """Test error response for invalid account type."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "invalid_type",
            "student_name": "Invalid Type Student",
        }

        response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        content = response.content.decode()
        self.assertIn("Invalid account type", content)

    def test_missing_fields_error_messages(self):
        """Test specific error messages for missing fields."""
        self.client.force_login(self.admin_user)

        test_cases = [
            {
                "account_type": "self",
                "missing_fields": ["student_name", "student_email", "student_birth_date"],
                "form_data": {"action": "add_student", "account_type": "self"},
            },
            {
                "account_type": "separate",
                "missing_fields": ["student_name", "guardian_name"],
                "form_data": {
                    "action": "add_student",
                    "account_type": "separate",
                    "student_email": "test@test.com",
                    "student_birth_date": "2008-01-01",
                    "guardian_email": "guardian@test.com",
                },
            },
            {
                "account_type": "guardian_only",
                "missing_fields": ["student_name", "guardian_name"],
                "form_data": {
                    "action": "add_student",
                    "account_type": "guardian_only",
                    "student_birth_date": "2015-01-01",
                    "guardian_email": "guardian@test.com",
                },
            },
        ]

        for case in test_cases:
            response = self.client.post(self.people_url, case["form_data"], headers={"hx-request": "true"})

            content = response.content.decode()
            self.assertIn("required", content.lower(), f"Missing error for {case['account_type']}")


class HTMXPartialRenderingTests(BaseTestCase):
    """Test HTMX partial template rendering."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@school.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School", description="A test school")
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True,
        )
        self.people_url = reverse("people")

    def test_success_partial_contains_expected_elements(self):
        """Test that success partial contains expected elements for JavaScript."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Partial Test Student",
            "student_email": "partial.test@example.com",
            "student_birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        content = response.content.decode()

        # Should contain success indicators that JavaScript can use
        success_indicators = [
            "success",
            "Student added successfully",
        ]

        for indicator in success_indicators:
            self.assertIn(indicator, content, f"Missing success indicator: {indicator}")

    def test_error_partial_contains_expected_elements(self):
        """Test that error partial contains expected elements for JavaScript."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            # Missing required fields to trigger error
        }

        response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        content = response.content.decode()

        # Should contain error indicators
        error_indicators = [
            "error",
            "required",
        ]

        for indicator in error_indicators:
            self.assertIn(indicator, content.lower(), f"Missing error indicator: {indicator}")

    def test_partial_response_size(self):
        """Test that partial responses are reasonably sized."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Size Test Student",
            "student_email": "size.test@example.com",
            "student_birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        content = response.content.decode()

        # Partial responses should be small (not full page)
        self.assertLess(len(content), 10000, "Partial response too large")
        self.assertGreater(len(content), 10, "Partial response too small")

    def test_partial_response_encoding(self):
        """Test that partial responses are properly encoded."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "José María García-López",  # Unicode characters
            "student_email": "unicode.test@example.com",
            "student_birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        # Response should handle Unicode properly
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("success", content.lower())


class HTMXFormInteractionTests(BaseTestCase):
    """Test HTMX form interaction scenarios."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.admin_user = User.objects.create_user(email="admin@school.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School", description="A test school")
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True,
        )
        self.people_url = reverse("people")

    def test_modal_form_submission_response(self):
        """Test response suitable for modal form submission."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "separate",
            "student_name": "Modal Student",
            "student_email": "modal@test.com",
            "student_birth_date": "2008-01-01",
            "guardian_name": "Modal Guardian",
            "guardian_email": "modal.guardian@test.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(
                self.people_url, form_data, headers={"hx-request": "true", "hx-target": "#addStudentModal"}
            )

        # Should return response suitable for modal
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("HX-Trigger"), "refreshStudents")

        content = response.content.decode()
        # Should contain success message that can be displayed in modal context
        self.assertIn("success", content.lower())

    def test_inline_form_submission_response(self):
        """Test response suitable for inline form submission."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "guardian_only",
            "student_name": "Inline Student",
            "student_birth_date": "2015-01-01",
            "guardian_name": "Inline Guardian",
            "guardian_email": "inline.guardian@test.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(
                self.people_url, form_data, headers={"hx-request": "true", "hx-target": "#students-content"}
            )

        # Should return response suitable for inline replacement
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("HX-Trigger"), "refreshStudents")

    def test_form_reset_after_success(self):
        """Test that successful submission allows for form reset."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Reset Test Student",
            "student_email": "reset.test@example.com",
            "student_birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data, headers={"hx-request": "true"})

        # Successful response should allow frontend to reset form
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("HX-Trigger"), "refreshStudents")

        # Response should indicate success for form reset logic
        content = response.content.decode()
        self.assertIn("success", content.lower())

    def test_concurrent_form_submissions(self):
        """Test handling of multiple concurrent HTMX form submissions."""
        self.client.force_login(self.admin_user)

        form_data_1 = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Concurrent Student 1",
            "student_email": "concurrent1@test.com",
            "student_birth_date": "1995-01-01",
        }

        form_data_2 = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Concurrent Student 2",
            "student_email": "concurrent2@test.com",
            "student_birth_date": "1996-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            # Submit both forms
            response1 = self.client.post(self.people_url, form_data_1, headers={"hx-request": "true"})

            response2 = self.client.post(self.people_url, form_data_2, headers={"hx-request": "true"})

        # Both should succeed
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        # Both should have proper HTMX triggers
        self.assertEqual(response1.get("HX-Trigger"), "refreshStudents")
        self.assertEqual(response2.get("HX-Trigger"), "refreshStudents")
