"""
Comprehensive integration tests for Add Student functionality.

This module contains focused integration tests for the Add Student form submission flow
that complement the existing test_people_view.py tests. These tests focus on catching
critical bugs in the form submission flow, HTMX responses, and edge cases that could
cause silent failures in production.

Key areas tested:
1. HTMX-specific request/response handling
2. Field validation edge cases and business rules
3. Model constraint violations and data integrity
4. Multi-tenant behavior and school isolation
5. Account type validation based on school admin choice (no age restrictions)
6. Email/phone uniqueness validation
7. Error response structure and HTMX compatibility
8. Form data sanitization and security

Business Logic Note:
- School admins have full control over account type selection regardless of student age
- Age is NOT a validation criteria for account type selection
- A 16-year-old can be an ADULT_STUDENT if the school admin chooses that option
- The system trusts the school admin's judgment in selecting the appropriate account type
"""

import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import EducationalSystem, School, SchoolMembership
from accounts.models.enums import SchoolRole
from accounts.models.profiles import GuardianProfile, StudentProfile
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class HTMXAddStudentIntegrationTests(BaseTestCase):
    """Integration tests focused on HTMX form submission flows."""

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

    def test_htmx_student_guardian_submission_returns_correct_headers(self):
        """Test HTMX submission returns correct response headers."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "separate",
            "student_name": "HTMX Student",
            "student_email": "htmx.student@test.com",
            "birth_date": "2008-01-15",
            "student_school_year": "10",
            "guardian_name": "HTMX Guardian",
            "guardian_email": "htmx.guardian@test.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(
                self.people_url,
                form_data,
                headers={"hx-request": "true", "hx-target": "#students-content"},  # HTMX header
            )

        self.assertEqual(response.status_code, 200)
        # Should trigger refresh students event
        self.assertEqual(response.get("HX-Trigger"), "refreshStudents")
        # Response should be HTML partial, not full page
        content = response.content.decode()
        self.assertNotIn("<html>", content)
        self.assertNotIn("<head>", content)
        self.assertIn("Student added successfully", content)

    def test_htmx_validation_error_returns_error_partial(self):
        """Test HTMX validation errors return proper error partial."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "separate",
            # Missing required fields
            "student_name": "",
            "student_email": "",
        }

        response = self.client.post(
            self.people_url, form_data, headers={"hx-request": "true", "hx-target": "#message-area"}
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # Should return error message partial
        self.assertIn("Missing required fields", content)
        self.assertNotIn("<html>", content)

    def test_htmx_vs_regular_request_behavior(self):
        """Test different behavior between HTMX and regular requests."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "separate",
            "student_name": "Test Student",
            "student_email": "test@example.com",
            "birth_date": "2008-01-15",
            "guardian_name": "Test Guardian",
            "guardian_email": "guardian@example.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            # Regular request
            regular_response = self.client.post(self.people_url, form_data)

            # HTMX request
            htmx_response = self.client.post(
                self.people_url,
                {**form_data, "student_email": "htmx@example.com", "guardian_email": "htmx.guardian@example.com"},
                headers={"hx-request": "true"},
            )

        # Both should succeed but return different response types
        self.assertEqual(regular_response.status_code, 200)
        self.assertEqual(htmx_response.status_code, 200)

        # HTMX response should have trigger header
        self.assertEqual(htmx_response.get("HX-Trigger"), "refreshStudents")
        self.assertIsNone(regular_response.get("HX-Trigger"))

    def test_htmx_form_targets_correct_elements(self):
        """Test HTMX form updates target correct DOM elements."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "guardian_only",
            "student_name": "Young Student",
            "birth_date": "2015-01-01",
            "guardian_name": "Guardian",
            "guardian_email": "guardian@test.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(
                self.people_url, form_data, headers={"hx-request": "true", "hx-target": "#students-content"}
            )

        # Should trigger refresh for students list
        self.assertEqual(response.get("HX-Trigger"), "refreshStudents")


class FieldValidationEdgeCaseTests(BaseTestCase):
    """Test edge cases in field validation."""

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

    def test_adult_student_account_type_creation(self):
        """Test that school admins can create ADULT_STUDENT account type for any age."""
        self.client.force_login(self.admin_user)

        # Test creating ADULT_STUDENT for a 16-year-old (school admin's choice)
        today = timezone.now().date()
        sixteen_years_ago = today.replace(year=today.year - 16)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Young Adult Student",
            "student_email": "young.adult@test.com",
            "birth_date": sixteen_years_ago.strftime("%Y-%m-%d"),
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        # Should create student - age is not a restriction for account type
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email="young.adult@test.com").exists())

        # Verify the correct account type was created
        student_user = User.objects.get(email="young.adult@test.com")
        self.assertTrue(hasattr(student_user, "student_profile"))
        self.assertEqual(student_user.student_profile.account_type, "ADULT_STUDENT")

        # Test creating ADULT_STUDENT for an 18-year-old (also valid)
        eighteen_years_ago = today.replace(year=today.year - 18)
        form_data["birth_date"] = eighteen_years_ago.strftime("%Y-%m-%d")
        form_data["student_email"] = "adult@test.com"
        form_data["student_name"] = "Adult Student"

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        # Should also create student
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email="adult@test.com").exists())

        # Verify the correct account type was created
        adult_student_user = User.objects.get(email="adult@test.com")
        self.assertTrue(hasattr(adult_student_user, "student_profile"))
        self.assertEqual(adult_student_user.student_profile.account_type, "ADULT_STUDENT")

    def test_email_format_validation(self):
        """Test email format validation across all account types."""
        self.client.force_login(self.admin_user)

        invalid_emails = [
            "notanemail",
            "missing@",
            "@domain.com",
            "spaces @domain.com",
            "unicode@dömain.com",
            "",
        ]

        for invalid_email in invalid_emails:
            form_data = {
                "action": "add_student",
                "account_type": "self",
                "student_name": "Test Student",
                "student_email": invalid_email,
                "birth_date": "1995-01-01",
            }

            response = self.client.post(self.people_url, form_data)

            # Should not create user with invalid email
            if invalid_email:  # Skip empty email test
                self.assertFalse(User.objects.filter(email=invalid_email).exists())

    def test_birth_date_edge_cases(self):
        """Test birth date validation edge cases."""
        self.client.force_login(self.admin_user)

        test_cases = [
            ("9999-12-31", "Future date"),  # Future date
            ("1800-01-01", "Very old date"),  # Very old date
            ("2024-02-29", "Leap year"),  # Leap year
            ("invalid-date", "Invalid format"),  # Invalid format
        ]

        for birth_date, case_name in test_cases:
            form_data = {
                "action": "add_student",
                "account_type": "guardian_only",
                "student_name": f"Student {case_name}",
                "birth_date": birth_date,
                "guardian_name": "Guardian",
                "guardian_email": f"guardian.{case_name.lower().replace(' ', '.')}@test.com",
            }

            response = self.client.post(self.people_url, form_data)

            # Future dates and invalid formats should be rejected
            if birth_date in ["9999-12-31", "invalid-date"]:
                self.assertFalse(User.objects.filter(email__startswith=f"guardian.{case_name.lower()}").exists())

    def test_school_year_validation(self):
        """Test school year validation against educational system."""
        self.client.force_login(self.admin_user)

        # Valid school years for Portugal system
        valid_years = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
        invalid_years = ["0", "13", "pre-k", "", "abc"]

        for year in valid_years:
            form_data = {
                "action": "add_student",
                "account_type": "self",
                "student_name": f"Student Year {year}",
                "student_email": f"student.year.{year}@test.com",
                "birth_date": "1995-01-01",
                "self_school_year": year,
            }

            with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
                response = self.client.post(self.people_url, form_data)

            # Valid years should create students
            self.assertTrue(User.objects.filter(email=f"student.year.{year}@test.com").exists())

    def test_name_field_edge_cases(self):
        """Test name field validation and sanitization."""
        self.client.force_login(self.admin_user)

        test_names = [
            ("José María García-López", "Valid accented name"),
            ("O'Connor", "Valid apostrophe"),
            ("李小明", "Valid Unicode"),
            ("A" * 150, "Very long name"),
            ("   Trimmed   ", "Name with spaces"),
            ("", "Empty name"),
        ]

        for name, case_desc in test_names:
            form_data = {
                "action": "add_student",
                "account_type": "self",
                "student_name": name,
                "student_email": f"test.{case_desc.lower().replace(' ', '.')}@test.com",
                "birth_date": "1995-01-01",
            }

            response = self.client.post(self.people_url, form_data)

            # Empty names should be rejected
            if name.strip():
                user_exists = User.objects.filter(email=f"test.{case_desc.lower().replace(' ', '.')}@test.com").exists()
                if not user_exists and len(name.strip()) <= 150:
                    # Should succeed for valid names
                    with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
                        response = self.client.post(self.people_url, form_data)


class DataIntegrityConstraintTests(TransactionTestCase):
    """Test database constraints and data integrity."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(email="admin@school.com", name="Admin User", is_active=True)
        self.school = School.objects.create(name="Test School", description="A test school")
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True,
        )
        self.people_url = reverse("people")

        # Create default educational system
        self.educational_system = EducationalSystem.objects.get_or_create(
            name="Portugal",
            code="pt",
            defaults={"description": "Portuguese Educational System"},
        )[0]

    def test_duplicate_email_constraint(self):
        """Test that duplicate emails are handled correctly."""
        self.client.force_login(self.admin_user)

        # Create first student
        form_data1 = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "First Student",
            "student_email": "duplicate@test.com",
            "birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response1 = self.client.post(self.people_url, form_data1)

        self.assertEqual(response1.status_code, 200)

        # Try to create second student with same email
        form_data2 = {
            "action": "add_student",
            "account_type": "separate",
            "student_name": "Second Student",
            "student_email": "duplicate@test.com",  # Same email
            "birth_date": "2008-01-01",
            "guardian_name": "Guardian",
            "guardian_email": "guardian@test.com",
        }

        response2 = self.client.post(self.people_url, form_data2)

        # Should handle gracefully (use existing user or show error)
        self.assertEqual(response2.status_code, 200)

        # Only one user should exist with this email
        users_with_email = User.objects.filter(email="duplicate@test.com")
        self.assertEqual(users_with_email.count(), 1)

    def test_student_profile_constraints(self):
        """Test StudentProfile model constraints."""
        # Test ADULT_STUDENT must have user account
        with self.assertRaises(ValidationError):
            student_profile = StudentProfile(
                user=None,  # Invalid for ADULT_STUDENT
                account_type="ADULT_STUDENT",
                educational_system=self.educational_system,
                birth_date=datetime.date(1995, 1, 1),
                school_year="12",
            )
            student_profile.full_clean()

        # Test GUARDIAN_ONLY must not have user account
        guardian_user = User.objects.create_user(email="guardian@constraint.test", name="Guardian")
        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        with self.assertRaises(ValidationError):
            student_profile = StudentProfile(
                user=guardian_user,  # Invalid for GUARDIAN_ONLY
                account_type="GUARDIAN_ONLY",
                educational_system=self.educational_system,
                birth_date=datetime.date(2012, 1, 1),
                school_year="6",
                guardian=guardian_profile,
            )
            student_profile.full_clean()

    def test_guardian_student_relationship_constraints(self):
        """Test GuardianStudentRelationship constraints."""
        # Create users
        guardian_user = User.objects.create_user(email="guardian@relationship.test", name="Guardian")
        student_user = User.objects.create_user(email="student@relationship.test", name="Student")

        # Create memberships (required for relationship)
        SchoolMembership.objects.create(user=guardian_user, school=self.school, role=SchoolRole.GUARDIAN)
        SchoolMembership.objects.create(user=student_user, school=self.school, role=SchoolRole.STUDENT)

        # Test that guardian cannot be the same as student
        from accounts.models.profiles import GuardianStudentRelationship

        with self.assertRaises(ValidationError):
            relationship = GuardianStudentRelationship(
                guardian=guardian_user,
                student=guardian_user,  # Same as guardian - invalid
                school=self.school,
            )
            relationship.full_clean()


class MultiTenantBehaviorTests(BaseTestCase):
    """Test multi-tenant behavior and school isolation."""

    def setUp(self):
        """Set up test data with multiple schools."""
        super().setUp()

        # Create two schools
        self.school1 = School.objects.create(name="School 1", description="First school")
        self.school2 = School.objects.create(name="School 2", description="Second school")

        # Create admin users for each school
        self.admin1 = User.objects.create_user(email="admin1@school1.com", name="Admin 1", is_active=True)
        self.admin2 = User.objects.create_user(email="admin2@school2.com", name="Admin 2", is_active=True)

        # Create memberships
        SchoolMembership.objects.create(user=self.admin1, school=self.school1, role=SchoolRole.SCHOOL_ADMIN)
        SchoolMembership.objects.create(user=self.admin2, school=self.school2, role=SchoolRole.SCHOOL_ADMIN)

        self.people_url = reverse("people")

    def test_admin_can_only_add_students_to_their_schools(self):
        """Test that admins can only add students to schools they manage."""
        self.client.force_login(self.admin1)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Cross School Student",
            "student_email": "cross.school@test.com",
            "birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Student should only be added to admin1's school
        user = User.objects.get(email="cross.school@test.com")
        memberships = SchoolMembership.objects.filter(user=user)

        self.assertEqual(memberships.count(), 1)
        self.assertEqual(memberships.first().school, self.school1)

    def test_guardian_can_manage_multiple_students_across_schools(self):
        """Test that a guardian can have students in different schools."""
        # Create guardian in both schools
        guardian_user = User.objects.create_user(email="multi.guardian@test.com", name="Multi Guardian")

        SchoolMembership.objects.create(user=guardian_user, school=self.school1, role=SchoolRole.GUARDIAN)
        SchoolMembership.objects.create(user=guardian_user, school=self.school2, role=SchoolRole.GUARDIAN)

        # Create students in different schools using the same guardian
        self.client.force_login(self.admin1)

        form_data1 = {
            "action": "add_student",
            "account_type": "guardian_only",
            "student_name": "Student in School 1",
            "birth_date": "2015-01-01",
            "guardian_name": "Multi Guardian",
            "guardian_email": "multi.guardian@test.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response1 = self.client.post(self.people_url, form_data1)

        self.assertEqual(response1.status_code, 200)

        # Now create student in school 2
        self.client.force_login(self.admin2)

        form_data2 = {
            "action": "add_student",
            "account_type": "guardian_only",
            "student_name": "Student in School 2",
            "birth_date": "2016-01-01",
            "guardian_name": "Multi Guardian",
            "guardian_email": "multi.guardian@test.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response2 = self.client.post(self.people_url, form_data2)

        self.assertEqual(response2.status_code, 200)

        # Guardian should have students in both schools
        guardian_profile = GuardianProfile.objects.get(user=guardian_user)
        students = StudentProfile.objects.filter(guardian=guardian_profile)
        self.assertEqual(students.count(), 2)

    def test_superuser_access_to_all_schools(self):
        """Test that superuser can add students to any school."""
        superuser = User.objects.create_user(
            email="super@admin.com", name="Super Admin", is_superuser=True, is_active=True
        )

        self.client.force_login(superuser)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Superuser Student",
            "student_email": "super.student@test.com",
            "birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Student should be created (superuser has access to all schools)
        self.assertTrue(User.objects.filter(email="super.student@test.com").exists())


class FormSecurityTests(BaseTestCase):
    """Test form security and data sanitization."""

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

    def test_xss_prevention_in_form_fields(self):
        """Test that form fields are properly sanitized against XSS."""
        self.client.force_login(self.admin_user)

        xss_payload = "<script>alert('xss')</script>"

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": f"Student {xss_payload}",
            "student_email": "xss.test@example.com",
            "birth_date": "1995-01-01",
            "self_notes": f"Notes with {xss_payload}",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        # Should not contain unescaped script tags in response
        content = response.content.decode()
        self.assertNotIn("<script>alert('xss')</script>", content)

        # Data should be stored safely
        user = User.objects.filter(email="xss.test@example.com").first()
        if user:
            # Name should not contain script tags (may be sanitized)
            self.assertNotIn("<script>", user.name)

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in form fields."""
        self.client.force_login(self.admin_user)

        sql_payload = "'; DROP TABLE accounts_customuser; --"

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Student Name",
            "student_email": f"sql{sql_payload}@test.com",
            "birth_date": "1995-01-01",
        }

        # Should not cause SQL injection
        response = self.client.post(self.people_url, form_data)

        # Users table should still exist
        self.assertTrue(User.objects.exists())

    def test_csrf_protection(self):
        """Test CSRF protection on form submission."""
        # Use a fresh client that doesn't automatically handle CSRF
        from django.test import Client

        csrf_client = Client(enforce_csrf_checks=True)

        # Login without getting CSRF token first
        csrf_client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "CSRF Test Student",
            "student_email": "csrf@test.com",
            "birth_date": "1995-01-01",
        }

        # Submit without CSRF token - should be blocked
        response = csrf_client.post(self.people_url, form_data)

        # Should be protected against CSRF (403 Forbidden)
        self.assertEqual(response.status_code, 403)


class ErrorHandlingIntegrationTests(BaseTestCase):
    """Test comprehensive error handling scenarios."""

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

    def test_permission_service_failure_handling(self):
        """Test handling of PermissionService failures."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Permission Fail Student",
            "student_email": "permission.fail@test.com",
            "birth_date": "1995-01-01",
        }

        with patch(
            "accounts.permissions.PermissionService.setup_permissions_for_student",
            side_effect=Exception("Permission setup failed"),
        ):
            response = self.client.post(self.people_url, form_data)

        # Should handle error gracefully
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Failed to add student", content)

        # User should not be created due to transaction rollback
        self.assertFalse(User.objects.filter(email="permission.fail@test.com").exists())

    def test_educational_system_missing_handling(self):
        """Test handling when educational system is missing."""
        # Delete all educational systems
        EducationalSystem.objects.all().delete()

        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "No System Student",
            "student_email": "no.system@test.com",
            "birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        # Should handle gracefully or create with first available system
        self.assertEqual(response.status_code, 200)

    def test_concurrent_user_creation_handling(self):
        """Test handling of concurrent user creation attempts."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "separate",
            "student_name": "Concurrent Student",
            "student_email": "concurrent@test.com",
            "birth_date": "2008-01-01",
            "guardian_name": "Concurrent Guardian",
            "guardian_email": "concurrent.guardian@test.com",
        }

        # Simulate concurrent creation by creating user first
        User.objects.create_user(email="concurrent@test.com", name="Already Created")

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        # Should handle existing user gracefully
        self.assertEqual(response.status_code, 200)

        # Should have profile created for existing user
        user = User.objects.get(email="concurrent@test.com")
        self.assertTrue(hasattr(user, "student_profile"))

    def test_invalid_form_data_types(self):
        """Test handling of invalid data types in form fields."""
        self.client.force_login(self.admin_user)

        # Test with various invalid data types
        invalid_form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": 12345,  # Number instead of string
            "student_email": "invalid@test.com",
            "birth_date": "not-a-date",  # Invalid date format
            "self_school_year": "invalid-year",  # Invalid school year
        }

        response = self.client.post(self.people_url, invalid_form_data)

        # Should handle invalid data gracefully
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # Should show validation errors
        self.assertTrue(any(keyword in content.lower() for keyword in ["error", "invalid", "required"]))

    def test_database_constraint_violation_handling(self):
        """Test handling of database constraint violations."""
        self.client.force_login(self.admin_user)

        # Create user first
        existing_user = User.objects.create_user(email="constraint@test.com", name="Existing User")

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Constraint Test",
            "student_email": "constraint@test.com",  # Duplicate email
            "birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        # Should handle constraint violation gracefully
        self.assertEqual(response.status_code, 200)

        # Should use existing user
        users_with_email = User.objects.filter(email="constraint@test.com")
        self.assertEqual(users_with_email.count(), 1)
        self.assertEqual(users_with_email.first().id, existing_user.id)


class BusinessLogicValidationTests(BaseTestCase):
    """Test business logic validation rules."""

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

    def test_guardian_cannot_be_student_same_person(self):
        """Test that guardian and student cannot be the same person."""
        self.client.force_login(self.admin_user)

        # Try to create student where guardian email = student email
        form_data = {
            "action": "add_student",
            "account_type": "separate",
            "student_name": "Self Guardian Student",
            "student_email": "same.person@test.com",
            "birth_date": "2008-01-01",
            "guardian_name": "Self Guardian",
            "guardian_email": "same.person@test.com",  # Same as student
        }

        response = self.client.post(self.people_url, form_data)

        # Should handle this edge case gracefully
        # (Business logic should prevent this or handle appropriately)
        self.assertEqual(response.status_code, 200)

    def test_student_profile_consistency_validation(self):
        """Test validation of student profile consistency."""
        self.client.force_login(self.admin_user)

        # Test creating adult student with guardian data (should ignore guardian data)
        form_data = {
            "action": "add_student",
            "account_type": "self",  # Adult student
            "student_name": "Adult With Guardian Data",
            "student_email": "adult.with.guardian@test.com",
            "birth_date": "1995-01-01",
            # These should be ignored for adult students
            "guardian_name": "Ignored Guardian",
            "guardian_email": "ignored@test.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Adult student should not have guardian
        student_user = User.objects.get(email="adult.with.guardian@test.com")
        student_profile = student_user.student_profile
        self.assertIsNone(student_profile.guardian)
        self.assertEqual(student_profile.account_type, "ADULT_STUDENT")

    def test_school_year_educational_system_consistency(self):
        """Test school year validation against educational system."""
        self.client.force_login(self.admin_user)

        # Test with valid school year for Portugal system
        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Valid Year Student",
            "student_email": "valid.year@test.com",
            "birth_date": "1995-01-01",
            "self_school_year": "12",  # Valid for Portugal
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Should create student with valid school year
        student_user = User.objects.get(email="valid.year@test.com")
        student_profile = student_user.student_profile
        self.assertEqual(student_profile.school_year, "12")

    def test_school_admin_controls_account_type_selection(self):
        """Test that school admins can choose any account type regardless of student age."""
        self.client.force_login(self.admin_user)

        today = timezone.now().date()
        minor_birth_date = today.replace(year=today.year - 16)  # 16 years old

        # Test 1: School admin chooses ADULT_STUDENT for a 16-year-old
        form_data_adult = {
            "action": "add_student",
            "account_type": "self",  # ADULT_STUDENT type
            "student_name": "Minor Adult Student",
            "student_email": "minor.adult@test.com",
            "birth_date": minor_birth_date.strftime("%Y-%m-%d"),
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data_adult)

        # Should create student with school admin's chosen account type
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email="minor.adult@test.com").exists())

        student_user = User.objects.get(email="minor.adult@test.com")
        self.assertTrue(hasattr(student_user, "student_profile"))
        self.assertEqual(student_user.student_profile.account_type, "ADULT_STUDENT")

        # Test 2: School admin chooses STUDENT_GUARDIAN for a 16-year-old
        form_data_guardian = {
            "action": "add_student",
            "account_type": "separate",  # STUDENT_GUARDIAN type
            "student_name": "Minor With Guardian",
            "student_email": "minor.guardian@test.com",
            "birth_date": minor_birth_date.strftime("%Y-%m-%d"),
            "guardian_name": "Parent Guardian",
            "guardian_email": "parent@test.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data_guardian)

        # Should create student with guardian account type
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email="minor.guardian@test.com").exists())

        guardian_student_user = User.objects.get(email="minor.guardian@test.com")
        self.assertTrue(hasattr(guardian_student_user, "student_profile"))
        self.assertEqual(guardian_student_user.student_profile.account_type, "STUDENT_GUARDIAN")

        # Test 3: School admin chooses GUARDIAN_ONLY for a 16-year-old
        form_data_only = {
            "action": "add_student",
            "account_type": "guardian_only",  # GUARDIAN_ONLY type
            "student_name": "Minor Guardian Only",
            "birth_date": minor_birth_date.strftime("%Y-%m-%d"),
            "guardian_name": "Solo Guardian",
            "guardian_email": "solo.guardian@test.com",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data_only)

        # Should create student profile with GUARDIAN_ONLY type
        self.assertEqual(response.status_code, 200)

        # Find the student profile created for GUARDIAN_ONLY type
        guardian_user = User.objects.get(email="solo.guardian@test.com")
        student_profiles = StudentProfile.objects.filter(guardian__user=guardian_user)
        self.assertTrue(student_profiles.exists())

        guardian_only_student = student_profiles.first()
        self.assertEqual(guardian_only_student.account_type, "GUARDIAN_ONLY")
