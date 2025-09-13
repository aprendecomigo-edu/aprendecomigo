"""
Comprehensive tests for the refactored PeopleView in dashboard/views.py.

This module tests the view layer for creating different types of users in the
school management system, specifically the three account type scenarios:
1. STUDENT_GUARDIAN - Both student and guardian have accounts, guardian handles finances
2. ADULT_STUDENT - Student manages everything themselves
3. GUARDIAN_ONLY - Student has no account, guardian manages everything

These tests focus on HTTP request/response handling and complement the existing
permission system tests in accounts/tests/test_permission_system.py.
"""

import datetime
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from accounts.models import EducationalSystem, School, SchoolMembership
from accounts.models.enums import SchoolRole
from accounts.models.profiles import GuardianProfile, StudentProfile, TeacherProfile
from accounts.permissions import PermissionService
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class PeopleViewTestCase(BaseTestCase):
    """Base test case for PeopleView tests with common setup."""

    def setUp(self):
        """Set up test data for PeopleView tests."""
        # Create test users
        self.admin_user = User.objects.create_user(email="admin@school.com", name="Admin User", is_active=True)

        self.teacher_user = User.objects.create_user(email="teacher@school.com", name="Teacher User", is_active=True)

        self.student_user = User.objects.create_user(email="student@school.com", name="Student User", is_active=True)

        # Create test school
        self.school = School.objects.create(name="Test School", description="A test school for unit tests")

        # Create school memberships
        self.admin_membership = SchoolMembership.objects.create(
            user=self.admin_user, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        self.teacher_membership = SchoolMembership.objects.create(
            user=self.teacher_user, school=self.school, role=SchoolRole.TEACHER, is_active=True
        )

        # Create teacher profile for teacher user
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user, bio="Experienced teacher", specialty="Mathematics"
        )

        # URL for the PeopleView
        self.people_url = reverse("people")

    def _get_valid_student_guardian_data(self):
        """Get valid form data for STUDENT_GUARDIAN account type."""
        return {
            "action": "add_student",
            "account_type": "separate",
            "student_name": "Test Student",
            "student_email": "test.student@school.com",
            "student_birth_date": "2008-01-15",
            "student_school_year": "10",
            "student_notes": "Test notes",
            "guardian_name": "Test Guardian",
            "guardian_email": "guardian@family.com",
            "guardian_phone": "+351912345678",
            "guardian_tax_nr": "123456789",
            "guardian_address": "Test Address, Lisboa",
            "guardian_invoice": "on",
            "guardian_email_notifications": "on",
            "guardian_sms_notifications": "on",
        }

    def _get_valid_adult_student_data(self):
        """Get valid form data for ADULT_STUDENT account type."""
        return {
            "action": "add_student",
            "account_type": "self",
            "self_name": "Adult Student",
            "self_email": "adult.student@school.com",
            "self_phone": "+351987654321",
            "self_birth_date": "1995-05-20",
            "self_school_year": "12",
            "self_tax_nr": "987654321",
            "self_address": "Adult Address, Porto",
            "self_notes": "Adult student notes",
            "self_invoice": "on",
            "self_email_notifications": "on",
            "self_sms_notifications": "",  # Not checked
        }

    def _get_valid_guardian_only_data(self):
        """Get valid form data for GUARDIAN_ONLY account type."""
        return {
            "action": "add_student",
            "account_type": "guardian_only",
            "guardian_only_student_name": "Young Student",
            "guardian_only_student_birth_date": "2012-03-10",
            "guardian_only_student_school_year": "6",
            "guardian_only_student_notes": "Young student notes",
            "guardian_only_guardian_name": "Managing Guardian",
            "guardian_only_guardian_email": "managing.guardian@family.com",
            "guardian_only_guardian_phone": "+351123456789",
            "guardian_only_guardian_tax_nr": "111222333",
            "guardian_only_guardian_address": "Guardian Address, Coimbra",
            "guardian_only_guardian_invoice": "on",
            "guardian_only_guardian_email_notifications": "on",
            "guardian_only_guardian_sms_notifications": "",  # Not checked
        }


class PeopleViewGetRequestsTests(PeopleViewTestCase):
    """Test GET requests to PeopleView."""

    def test_get_people_view_requires_authentication(self):
        """Test that GET requests require user authentication."""
        response = self.client.get(self.people_url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/signin/", response.url)

    def test_get_people_view_authenticated_user_success(self):
        """Test GET request by authenticated user returns success."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "People - Aprende Comigo")

    def test_get_people_view_includes_existing_teachers(self):
        """Test that GET request includes existing teachers in context."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        self.assertEqual(response.status_code, 200)

        # Check context data
        teachers = response.context["teachers"]
        self.assertEqual(len(teachers), 1)
        self.assertEqual(teachers[0]["email"], self.teacher_user.email)
        self.assertEqual(teachers[0]["specialty"], "Mathematics")

    def test_get_people_view_includes_existing_students(self):
        """Test that GET request includes existing students in context."""
        # Create a student membership first
        student_membership = SchoolMembership.objects.create(
            user=self.student_user, school=self.school, role=SchoolRole.STUDENT, is_active=True
        )

        # Create student profile
        student_profile = StudentProfile.objects.create(
            user=self.student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            account_type="ADULT_STUDENT",
        )

        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        self.assertEqual(response.status_code, 200)

        # Check context data
        students = response.context["students"]
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["email"], self.student_user.email)
        self.assertEqual(students[0]["school_year"], "10")

    def test_get_people_view_calculates_stats_correctly(self):
        """Test that GET request calculates teacher and student stats correctly."""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.people_url)

        # Check teacher stats
        teacher_stats = response.context["teacher_stats"]
        self.assertEqual(teacher_stats["total"], 1)
        self.assertEqual(teacher_stats["active"], 1)
        self.assertEqual(teacher_stats["inactive"], 0)

    def test_get_people_view_with_superuser(self):
        """Test that superuser can access people view."""
        superuser = User.objects.create_user(
            email="super@admin.com", name="Super Admin", is_superuser=True, is_active=True
        )

        self.client.force_login(superuser)
        response = self.client.get(self.people_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "People - Aprende Comigo")


class PeopleViewStudentGuardianTests(PeopleViewTestCase):
    """Test STUDENT_GUARDIAN account type creation in PeopleView."""

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_create_student_guardian_success(self, mock_setup_permissions):
        """Test successful creation of STUDENT_GUARDIAN account type."""
        self.client.force_login(self.admin_user)

        form_data = self._get_valid_student_guardian_data()
        response = self.client.post(self.people_url, form_data)

        # Should return success response (200) with updated students partial
        self.assertEqual(response.status_code, 200)

        # Check that users were created
        student_user = User.objects.get(email="test.student@school.com")
        guardian_user = User.objects.get(email="guardian@family.com")

        self.assertEqual(student_user.name, "Test Student")
        self.assertEqual(guardian_user.name, "Test Guardian")
        self.assertEqual(guardian_user.phone_number, "+351912345678")

        # Check that guardian profile was created
        guardian_profile = GuardianProfile.objects.get(user=guardian_user)
        self.assertEqual(guardian_profile.tax_nr, "123456789")
        self.assertEqual(guardian_profile.address, "Test Address, Lisboa")
        self.assertTrue(guardian_profile.invoice)
        self.assertTrue(guardian_profile.email_notifications_enabled)
        self.assertTrue(guardian_profile.sms_notifications_enabled)

        # Check that student profile was created correctly
        student_profile = StudentProfile.objects.get(user=student_user)
        self.assertEqual(student_profile.account_type, "STUDENT_GUARDIAN")
        self.assertEqual(student_profile.school_year, "10")
        self.assertEqual(student_profile.birth_date, datetime.date(2008, 1, 15))
        self.assertEqual(student_profile.guardian, guardian_profile)
        self.assertEqual(student_profile.notes, "Test notes")

        # Check that school memberships were created
        student_membership = SchoolMembership.objects.get(user=student_user, school=self.school)
        guardian_membership = SchoolMembership.objects.get(user=guardian_user, school=self.school)

        self.assertEqual(student_membership.role, SchoolRole.STUDENT.value)
        self.assertEqual(guardian_membership.role, SchoolRole.GUARDIAN.value)
        self.assertTrue(student_membership.is_active)
        self.assertTrue(guardian_membership.is_active)

        # Verify permission setup was called
        mock_setup_permissions.assert_called_once_with(student_profile)

    def test_create_student_guardian_missing_required_fields(self):
        """Test validation with missing required fields for STUDENT_GUARDIAN."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "separate",
            # Missing required fields
        }

        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "required")

        # Should not create any users
        self.assertFalse(User.objects.filter(email__contains="test").exists())

    def test_create_student_guardian_existing_users(self):
        """Test creation when users already exist."""
        # Create existing users first
        existing_student = User.objects.create_user(email="test.student@school.com", name="Existing Student")
        existing_guardian = User.objects.create_user(email="guardian@family.com", name="Existing Guardian")

        self.client.force_login(self.admin_user)
        form_data = self._get_valid_student_guardian_data()

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Should use existing users, not create new ones
        student_user = User.objects.get(email="test.student@school.com")
        guardian_user = User.objects.get(email="guardian@family.com")

        self.assertEqual(student_user.id, existing_student.id)
        self.assertEqual(guardian_user.id, existing_guardian.id)

        # But profiles should still be created
        self.assertTrue(StudentProfile.objects.filter(user=student_user).exists())
        self.assertTrue(GuardianProfile.objects.filter(user=guardian_user).exists())

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_create_student_guardian_checkbox_handling(self, mock_setup_permissions):
        """Test proper handling of checkbox fields in STUDENT_GUARDIAN creation."""
        self.client.force_login(self.admin_user)

        form_data = self._get_valid_student_guardian_data()
        # Remove checkbox fields to test False values
        del form_data["guardian_invoice"]
        del form_data["guardian_email_notifications"]
        del form_data["guardian_sms_notifications"]

        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Check guardian profile checkbox fields are False
        guardian_user = User.objects.get(email="guardian@family.com")
        guardian_profile = GuardianProfile.objects.get(user=guardian_user)

        self.assertFalse(guardian_profile.invoice)
        self.assertFalse(guardian_profile.email_notifications_enabled)
        self.assertFalse(guardian_profile.sms_notifications_enabled)


class PeopleViewAdultStudentTests(PeopleViewTestCase):
    """Test ADULT_STUDENT account type creation in PeopleView."""

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_create_adult_student_success(self, mock_setup_permissions):
        """Test successful creation of ADULT_STUDENT account type."""
        self.client.force_login(self.admin_user)

        form_data = self._get_valid_adult_student_data()
        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Check that user was created
        user = User.objects.get(email="adult.student@school.com")
        self.assertEqual(user.name, "Adult Student")
        self.assertEqual(user.phone_number, "+351987654321")

        # Check that student profile was created correctly
        student_profile = StudentProfile.objects.get(user=user)
        self.assertEqual(student_profile.account_type, "ADULT_STUDENT")
        self.assertEqual(student_profile.school_year, "12")
        self.assertEqual(student_profile.birth_date, datetime.date(1995, 5, 20))
        self.assertEqual(student_profile.notes, "Adult student notes")
        self.assertEqual(student_profile.address, "Adult Address, Porto")
        self.assertEqual(student_profile.tax_nr, "987654321")
        self.assertTrue(student_profile.invoice)
        self.assertTrue(student_profile.email_notifications_enabled)
        self.assertFalse(student_profile.sms_notifications_enabled)  # Was not checked
        self.assertIsNone(student_profile.guardian)  # Adult students have no guardian

        # Check that school membership was created
        membership = SchoolMembership.objects.get(user=user, school=self.school)
        self.assertEqual(membership.role, SchoolRole.STUDENT.value)
        self.assertTrue(membership.is_active)

        # Verify permission setup was called
        mock_setup_permissions.assert_called_once_with(student_profile)

    def test_create_adult_student_missing_required_fields(self):
        """Test validation with missing required fields for ADULT_STUDENT."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "self_name": "Adult Student",
            # Missing email and birth_date
        }

        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "required")

        # Should not create any users
        self.assertFalse(User.objects.filter(email="adult.student@school.com").exists())

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_create_adult_student_updates_existing_profile(self, mock_setup_permissions):
        """Test that ADULT_STUDENT creation updates existing profile correctly."""
        # Create existing user and profile
        existing_user = User.objects.create_user(email="adult.student@school.com", name="Old Name")
        existing_profile = StudentProfile.objects.create(
            user=existing_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(1990, 1, 1),
            school_year="10",
            account_type="STUDENT_GUARDIAN",  # Different type initially
        )

        self.client.force_login(self.admin_user)
        form_data = self._get_valid_adult_student_data()
        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Profile should be updated
        existing_profile.refresh_from_db()
        self.assertEqual(existing_profile.account_type, "ADULT_STUDENT")
        self.assertEqual(existing_profile.school_year, "12")  # Updated
        self.assertEqual(existing_profile.birth_date, datetime.date(1995, 5, 20))  # Updated
        self.assertIsNone(existing_profile.guardian)  # Cleared for adult student


class PeopleViewGuardianOnlyTests(PeopleViewTestCase):
    """Test GUARDIAN_ONLY account type creation in PeopleView."""

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_create_guardian_only_success(self, mock_setup_permissions):
        """Test successful creation of GUARDIAN_ONLY account type."""
        self.client.force_login(self.admin_user)

        form_data = self._get_valid_guardian_only_data()
        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Check that guardian user was created
        guardian_user = User.objects.get(email="managing.guardian@family.com")
        self.assertEqual(guardian_user.name, "Managing Guardian")
        self.assertEqual(guardian_user.phone_number, "+351123456789")

        # Check that guardian profile was created
        guardian_profile = GuardianProfile.objects.get(user=guardian_user)
        self.assertEqual(guardian_profile.tax_nr, "111222333")
        self.assertEqual(guardian_profile.address, "Guardian Address, Coimbra")
        self.assertTrue(guardian_profile.invoice)
        self.assertTrue(guardian_profile.email_notifications_enabled)
        self.assertFalse(guardian_profile.sms_notifications_enabled)  # Not checked

        # Check that student profile was created correctly (without user account)
        student_profile = StudentProfile.objects.get(guardian=guardian_profile)
        self.assertIsNone(student_profile.user)  # No user account for GUARDIAN_ONLY
        self.assertEqual(student_profile.account_type, "GUARDIAN_ONLY")
        self.assertEqual(student_profile.school_year, "6")
        self.assertEqual(student_profile.birth_date, datetime.date(2012, 3, 10))
        self.assertEqual(student_profile.guardian, guardian_profile)
        self.assertEqual(student_profile.notes, "Young student notes")

        # Check that only guardian has school membership (student has no account)
        guardian_membership = SchoolMembership.objects.get(user=guardian_user, school=self.school)
        self.assertEqual(guardian_membership.role, SchoolRole.GUARDIAN.value)
        self.assertTrue(guardian_membership.is_active)

        # Student should not have any membership since they have no user account
        student_memberships = (
            SchoolMembership.objects.filter(school=self.school)
            .exclude(user=guardian_user)
            .exclude(user=self.admin_user)
            .exclude(user=self.teacher_user)
        )
        self.assertEqual(student_memberships.count(), 0)

        # Verify permission setup was called
        mock_setup_permissions.assert_called_once_with(student_profile)

    def test_create_guardian_only_missing_required_fields(self):
        """Test validation with missing required fields for GUARDIAN_ONLY."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "guardian_only",
            "guardian_only_student_name": "Young Student",
            # Missing other required fields
        }

        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "required")

        # Should not create any users or profiles
        self.assertFalse(User.objects.filter(email="managing.guardian@family.com").exists())
        self.assertFalse(StudentProfile.objects.filter(user=None).exists())

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_create_guardian_only_existing_guardian_user(self, mock_setup_permissions):
        """Test GUARDIAN_ONLY creation when guardian user already exists."""
        # Create existing guardian user
        existing_guardian = User.objects.create_user(email="managing.guardian@family.com", name="Existing Guardian")

        self.client.force_login(self.admin_user)
        form_data = self._get_valid_guardian_only_data()
        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Should use existing user
        guardian_user = User.objects.get(email="managing.guardian@family.com")
        self.assertEqual(guardian_user.id, existing_guardian.id)

        # Profile should still be created
        self.assertTrue(GuardianProfile.objects.filter(user=guardian_user).exists())
        self.assertTrue(StudentProfile.objects.filter(guardian__user=guardian_user, user=None).exists())


class PeopleViewErrorHandlingTests(PeopleViewTestCase):
    """Test error handling and edge cases in PeopleView."""

    def test_invalid_action_parameter(self):
        """Test handling of invalid action parameter."""
        self.client.force_login(self.admin_user)

        response = self.client.post(
            self.people_url,
            {
                "action": "invalid_action",
            },
        )

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn("error", response_data)
        self.assertEqual(response_data["error"], "Invalid action")

    def test_invalid_account_type(self):
        """Test handling of invalid account type."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "invalid_type",
        }

        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid account type")

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_permission_service_exception_handling(self, mock_setup_permissions):
        """Test handling of exceptions from PermissionService."""
        mock_setup_permissions.side_effect = Exception("Permission setup failed")

        self.client.force_login(self.admin_user)
        form_data = self._get_valid_adult_student_data()
        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Failed to add student")

    def test_database_transaction_rollback_on_error(self):
        """Test that database transactions are rolled back on errors."""
        self.client.force_login(self.admin_user)

        form_data = self._get_valid_adult_student_data()

        # Mock PermissionService to raise an exception after user creation
        with patch(
            "accounts.permissions.PermissionService.setup_permissions_for_student",
            side_effect=Exception("Rollback test"),
        ):
            response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # User should not exist due to transaction rollback
        self.assertFalse(User.objects.filter(email="adult.student@school.com").exists())

    def test_no_school_membership_error(self):
        """Test handling when user has no school memberships."""
        # Create user with no school membership
        orphan_user = User.objects.create_user(email="orphan@user.com", name="Orphan User", is_active=True)

        self.client.force_login(orphan_user)
        response = self.client.post(
            self.people_url,
            {
                "action": "add_student",
                "account_type": "self",
            },
        )

        # Should handle gracefully
        self.assertEqual(response.status_code, 200)


class PeopleViewAuthorizationTests(PeopleViewTestCase):
    """Test authorization requirements for PeopleView."""

    def test_post_request_requires_authentication(self):
        """Test that POST requests require authentication."""
        response = self.client.post(
            self.people_url,
            {
                "action": "add_student",
            },
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/signin/", response.url)

    def test_authenticated_user_can_access_post(self):
        """Test that authenticated users can make POST requests."""
        self.client.force_login(self.admin_user)

        response = self.client.post(
            self.people_url,
            {
                "action": "invalid_action",  # Will return 400, but won't redirect
            },
        )

        # Should not redirect to login
        self.assertNotEqual(response.status_code, 302)

    def test_superuser_can_access_all_schools(self):
        """Test that superuser can access students from all schools."""
        # Create another school with students
        other_school = School.objects.create(name="Other School", description="Another school")

        other_user = User.objects.create_user(email="other@school.com", name="Other User")

        SchoolMembership.objects.create(user=other_user, school=other_school, role=SchoolRole.STUDENT, is_active=True)

        superuser = User.objects.create_user(
            email="super@admin.com", name="Super Admin", is_superuser=True, is_active=True
        )

        self.client.force_login(superuser)

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            form_data = self._get_valid_adult_student_data()
            response = self.client.post(self.people_url, form_data)

        # Superuser should be able to create students
        self.assertEqual(response.status_code, 200)


class PeopleViewAddTeacherTests(PeopleViewTestCase):
    """Test teacher addition functionality in PeopleView."""

    def test_add_teacher_success(self):
        """Test successful teacher addition."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_teacher",
            "email": "new.teacher@school.com",
            "bio": "Experienced physics teacher",
            "specialty": "Physics",
        }

        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Check teacher was created
        teacher_user = User.objects.get(email="new.teacher@school.com")
        teacher_profile = TeacherProfile.objects.get(user=teacher_user)

        self.assertEqual(teacher_profile.bio, "Experienced physics teacher")
        self.assertEqual(teacher_profile.specialty, "Physics")

        # Check school membership
        membership = SchoolMembership.objects.get(user=teacher_user, school=self.school)
        self.assertEqual(membership.role, SchoolRole.TEACHER.value)

    def test_add_teacher_missing_email(self):
        """Test teacher addition with missing email."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_teacher",
            "bio": "Experienced teacher",
            "specialty": "Math",
        }

        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email is required")

    def test_add_teacher_existing_user(self):
        """Test adding teacher for existing user creates profile."""
        # Create existing user without teacher profile
        existing_user = User.objects.create_user(email="existing@teacher.com", name="Existing User")

        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_teacher",
            "email": "existing@teacher.com",
            "bio": "New teacher bio",
            "specialty": "Chemistry",
        }

        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Should create teacher profile for existing user
        teacher_profile = TeacherProfile.objects.get(user=existing_user)
        self.assertEqual(teacher_profile.bio, "New teacher bio")
        self.assertEqual(teacher_profile.specialty, "Chemistry")


class PeopleViewPartialRenderingTests(PeopleViewTestCase):
    """Test partial template rendering methods in PeopleView."""

    def test_render_teachers_partial(self):
        """Test _render_teachers_partial method returns correct template."""
        self.client.force_login(self.admin_user)

        # Call add_teacher to trigger teachers partial rendering
        form_data = {
            "action": "add_teacher",
            "email": "partial.teacher@school.com",
        }

        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)
        # Response should contain teacher data - specific template content depends on implementation

    def test_render_students_partial(self):
        """Test _render_students_partial method returns correct template."""
        self.client.force_login(self.admin_user)

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            form_data = self._get_valid_adult_student_data()
            response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)
        # Response should contain student data - specific template content depends on implementation


class PeopleViewIntegrationTests(PeopleViewTestCase):
    """Integration tests that test complete workflows."""

    @patch("accounts.permissions.PermissionService.setup_permissions_for_student")
    def test_complete_student_guardian_workflow(self, mock_setup_permissions):
        """Test complete workflow for creating student with guardian."""
        self.client.force_login(self.admin_user)

        # Create student with guardian
        form_data = self._get_valid_student_guardian_data()
        response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        # Verify all database objects were created correctly
        student_user = User.objects.get(email="test.student@school.com")
        guardian_user = User.objects.get(email="guardian@family.com")

        student_profile = StudentProfile.objects.get(user=student_user)
        guardian_profile = GuardianProfile.objects.get(user=guardian_user)

        # Test relationships
        self.assertEqual(student_profile.guardian, guardian_profile)
        self.assertEqual(student_profile.account_type, "STUDENT_GUARDIAN")

        # Test memberships
        self.assertTrue(
            SchoolMembership.objects.filter(
                user=student_user, school=self.school, role=SchoolRole.STUDENT.value
            ).exists()
        )
        self.assertTrue(
            SchoolMembership.objects.filter(
                user=guardian_user, school=self.school, role=SchoolRole.GUARDIAN.value
            ).exists()
        )

        # Test permission setup was called
        mock_setup_permissions.assert_called_once()

        # Verify we can now retrieve these users in GET request
        get_response = self.client.get(self.people_url)
        self.assertContains(get_response, "test.student@school.com")

    def test_multiple_account_types_in_same_school(self):
        """Test that different account types can coexist in the same school."""
        self.client.force_login(self.admin_user)

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            # Create adult student
            adult_data = self._get_valid_adult_student_data()
            response1 = self.client.post(self.people_url, adult_data)
            self.assertEqual(response1.status_code, 200)

            # Create student with guardian
            guardian_data = self._get_valid_student_guardian_data()
            response2 = self.client.post(self.people_url, guardian_data)
            self.assertEqual(response2.status_code, 200)

            # Create guardian-only student
            guardian_only_data = self._get_valid_guardian_only_data()
            response3 = self.client.post(self.people_url, guardian_only_data)
            self.assertEqual(response3.status_code, 200)

        # Verify all account types were created
        adult_student = StudentProfile.objects.get(account_type="ADULT_STUDENT")
        student_guardian = StudentProfile.objects.get(account_type="STUDENT_GUARDIAN")
        guardian_only = StudentProfile.objects.get(account_type="GUARDIAN_ONLY")

        self.assertIsNotNone(adult_student.user)
        self.assertIsNone(adult_student.guardian)

        self.assertIsNotNone(student_guardian.user)
        self.assertIsNotNone(student_guardian.guardian)

        self.assertIsNone(guardian_only.user)
        self.assertIsNotNone(guardian_only.guardian)

    def test_educational_system_assignment(self):
        """Test that students are assigned correct educational system."""
        self.client.force_login(self.admin_user)

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            form_data = self._get_valid_adult_student_data()
            response = self.client.post(self.people_url, form_data)

        self.assertEqual(response.status_code, 200)

        student_profile = StudentProfile.objects.get(user__email="adult.student@school.com")

        # Should be assigned the default educational system (Portugal)
        self.assertEqual(student_profile.educational_system, self.default_educational_system)
        self.assertEqual(student_profile.educational_system.code, "pt")
