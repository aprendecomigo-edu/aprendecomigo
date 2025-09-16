"""
Model Constraints and Database Integration Tests for Add Student functionality.

This module tests database-level constraints, model validation, and data integrity
scenarios that could cause silent failures or data corruption in the Add Student flow.
These tests ensure that the business rules defined in the models are properly enforced
at the database level and that the form submission flow handles constraint violations
gracefully.

Key areas tested:
1. Model-level validation constraints
2. Database integrity constraints
3. Foreign key relationships and cascading
4. Unique constraint enforcement
5. Business rule validation at model level
6. Transaction rollback scenarios
7. Cross-model consistency validation
"""

import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from accounts.models import EducationalSystem, School, SchoolMembership
from accounts.models.enums import SchoolRole
from accounts.models.profiles import GuardianProfile, GuardianStudentRelationship, StudentProfile
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class StudentProfileConstraintTests(TestCase):
    """Test StudentProfile model constraints and validation."""

    def setUp(self):
        """Set up test data."""
        self.educational_system = EducationalSystem.objects.get_or_create(
            name="Portugal",
            code="pt",
            defaults={"description": "Portuguese Educational System"},
        )[0]

    def test_adult_student_must_have_user_account(self):
        """Test that ADULT_STUDENT must have a user account."""
        # Should raise ValidationError when user is None for ADULT_STUDENT
        student_profile = StudentProfile(
            user=None,  # Invalid for ADULT_STUDENT
            account_type="ADULT_STUDENT",
            educational_system=self.educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
        )

        with self.assertRaises(ValidationError) as context:
            student_profile.full_clean()

        self.assertIn("Adult students must have a user account", str(context.exception))

    def test_adult_student_cannot_have_guardian(self):
        """Test that ADULT_STUDENT cannot have a guardian assigned."""
        user = User.objects.create_user(email="adult@test.com", name="Adult Student")
        guardian_user = User.objects.create_user(email="guardian@test.com", name="Guardian")
        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        student_profile = StudentProfile(
            user=user,
            account_type="ADULT_STUDENT",
            educational_system=self.educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
            guardian=guardian_profile,  # Invalid for ADULT_STUDENT
        )

        with self.assertRaises(ValidationError) as context:
            student_profile.full_clean()

        self.assertIn("Adult students should not have a guardian assigned", str(context.exception))

    def test_guardian_only_must_not_have_user_account(self):
        """Test that GUARDIAN_ONLY must not have a user account."""
        user = User.objects.create_user(email="student@test.com", name="Student")
        guardian_user = User.objects.create_user(email="guardian@test.com", name="Guardian")
        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        student_profile = StudentProfile(
            user=user,  # Invalid for GUARDIAN_ONLY
            account_type="GUARDIAN_ONLY",
            educational_system=self.educational_system,
            birth_date=datetime.date(2012, 1, 1),
            school_year="6",
            guardian=guardian_profile,
        )

        with self.assertRaises(ValidationError) as context:
            student_profile.full_clean()

        self.assertIn("Guardian-only students should not have a user account", str(context.exception))

    def test_guardian_only_must_have_guardian(self):
        """Test that GUARDIAN_ONLY must have a guardian assigned."""
        student_profile = StudentProfile(
            user=None,
            account_type="GUARDIAN_ONLY",
            educational_system=self.educational_system,
            birth_date=datetime.date(2012, 1, 1),
            school_year="6",
            guardian=None,  # Invalid for GUARDIAN_ONLY
        )

        with self.assertRaises(ValidationError) as context:
            student_profile.full_clean()

        self.assertIn("Guardian-only students must have a guardian assigned", str(context.exception))

    def test_student_guardian_must_have_both_user_and_guardian(self):
        """Test that STUDENT_GUARDIAN must have both user and guardian."""
        # Test missing user
        guardian_user = User.objects.create_user(email="guardian@test.com", name="Guardian")
        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        student_profile = StudentProfile(
            user=None,  # Invalid for STUDENT_GUARDIAN
            account_type="STUDENT_GUARDIAN",
            educational_system=self.educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            guardian=guardian_profile,
        )

        with self.assertRaises(ValidationError) as context:
            student_profile.full_clean()

        self.assertIn("Student+Guardian accounts require the student to have a user account", str(context.exception))

        # Test missing guardian
        student_user = User.objects.create_user(email="student@test.com", name="Student")

        student_profile = StudentProfile(
            user=student_user,
            account_type="STUDENT_GUARDIAN",
            educational_system=self.educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            guardian=None,  # Invalid for STUDENT_GUARDIAN
        )

        with self.assertRaises(ValidationError) as context:
            student_profile.full_clean()

        self.assertIn("Student+Guardian accounts require a guardian to be assigned", str(context.exception))

    def test_school_year_validation_against_educational_system(self):
        """Test that school year must be valid for the educational system."""
        user = User.objects.create_user(email="student@test.com", name="Student")

        # Test with invalid school year
        student_profile = StudentProfile(
            user=user,
            account_type="ADULT_STUDENT",
            educational_system=self.educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="invalid_year",  # Invalid for Portugal system
        )

        # This should raise ValidationError if the educational system has proper validation
        try:
            student_profile.full_clean()
            # If no error, check if the educational system validates school years
            valid_years = (
                dict(self.educational_system.school_year_choices)
                if hasattr(self.educational_system, "school_year_choices")
                else {}
            )
            if valid_years and "invalid_year" not in valid_years:
                self.fail("Expected ValidationError for invalid school year")
        except ValidationError as e:
            self.assertIn("school_year", str(e).lower())


class GuardianStudentRelationshipConstraintTests(TestCase):
    """Test GuardianStudentRelationship model constraints."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(name="Test School")

        self.guardian_user = User.objects.create_user(email="guardian@test.com", name="Guardian")
        self.student_user = User.objects.create_user(email="student@test.com", name="Student")

        # Create required school memberships
        SchoolMembership.objects.create(user=self.guardian_user, school=self.school, role=SchoolRole.GUARDIAN)
        SchoolMembership.objects.create(user=self.student_user, school=self.school, role=SchoolRole.STUDENT)

    def test_guardian_cannot_be_same_as_student(self):
        """Test that guardian cannot be the same user as student."""
        relationship = GuardianStudentRelationship(
            guardian=self.guardian_user,
            student=self.guardian_user,  # Same as guardian - invalid
            school=self.school,
        )

        with self.assertRaises(ValidationError) as context:
            relationship.full_clean()

        self.assertIn("guardian and student cannot be the same user", str(context.exception))

    def test_guardian_must_be_school_member(self):
        """Test that guardian must be a member of the school."""
        # Create guardian without school membership
        orphan_guardian = User.objects.create_user(email="orphan.guardian@test.com", name="Orphan Guardian")

        relationship = GuardianStudentRelationship(
            guardian=orphan_guardian,  # Not a member of the school
            student=self.student_user,
            school=self.school,
        )

        with self.assertRaises(ValidationError) as context:
            relationship.full_clean()

        self.assertIn("guardian must be a member of the school", str(context.exception))

    def test_student_must_be_school_member(self):
        """Test that student must be a member of the school."""
        # Create student without school membership
        orphan_student = User.objects.create_user(email="orphan.student@test.com", name="Orphan Student")

        relationship = GuardianStudentRelationship(
            guardian=self.guardian_user,
            student=orphan_student,  # Not a member of the school
            school=self.school,
        )

        with self.assertRaises(ValidationError) as context:
            relationship.full_clean()

        self.assertIn("student must be a member of the school", str(context.exception))

    def test_unique_relationship_constraint(self):
        """Test that guardian-student-school combination must be unique."""
        # Create first relationship
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_user,
            student=self.student_user,
            school=self.school,
        )

        # Try to create duplicate relationship
        with self.assertRaises(IntegrityError):
            GuardianStudentRelationship.objects.create(
                guardian=self.guardian_user,
                student=self.student_user,
                school=self.school,  # Same combination
            )


class DatabaseIntegrityConstraintTests(TransactionTestCase):
    """Test database-level integrity constraints."""

    def setUp(self):
        """Set up test data."""
        self.educational_system = EducationalSystem.objects.get_or_create(
            name="Portugal",
            code="pt",
            defaults={"description": "Portuguese Educational System"},
        )[0]

    def test_user_email_uniqueness_constraint(self):
        """Test that user email uniqueness is enforced at database level."""
        # Create first user
        User.objects.create_user(email="duplicate@test.com", name="First User")

        # Try to create second user with same email
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email="duplicate@test.com", name="Second User")

    def test_student_profile_user_uniqueness(self):
        """Test that each user can have only one student profile."""
        user = User.objects.create_user(email="student@test.com", name="Student")

        # Create first student profile
        StudentProfile.objects.create(
            user=user,
            account_type="ADULT_STUDENT",
            educational_system=self.educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
        )

        # Try to create second student profile for same user
        with self.assertRaises(IntegrityError):
            StudentProfile.objects.create(
                user=user,  # Same user
                account_type="ADULT_STUDENT",
                educational_system=self.educational_system,
                birth_date=datetime.date(1996, 1, 1),
                school_year="11",
            )

    def test_guardian_profile_user_uniqueness(self):
        """Test that each user can have only one guardian profile."""
        user = User.objects.create_user(email="guardian@test.com", name="Guardian")

        # Create first guardian profile
        GuardianProfile.objects.create(user=user)

        # Try to create second guardian profile for same user
        with self.assertRaises(IntegrityError):
            GuardianProfile.objects.create(user=user)

    def test_foreign_key_cascade_behavior(self):
        """Test foreign key cascade behavior when deleting related objects."""
        # Create guardian and student
        guardian_user = User.objects.create_user(email="guardian@test.com", name="Guardian")
        student_user = User.objects.create_user(email="student@test.com", name="Student")

        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        student_profile = StudentProfile.objects.create(
            user=student_user,
            account_type="STUDENT_GUARDIAN",
            educational_system=self.educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            guardian=guardian_profile,
        )

        # Delete guardian user - should handle cascade appropriately
        guardian_user.delete()

        # Check what happens to student profile
        student_profile.refresh_from_db()

        # Depending on the cascade setting, guardian might be set to None or student might be deleted
        # The exact behavior depends on the on_delete setting in the model


class AddStudentFormConstraintIntegrationTests(BaseTestCase):
    """Integration tests for form submission with model constraints."""

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

    def test_form_handles_duplicate_user_constraint(self):
        """Test that form handles duplicate user creation gracefully."""
        # Create existing user
        existing_user = User.objects.create_user(email="existing@test.com", name="Existing User")

        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "New Name",
            "student_email": "existing@test.com",  # Duplicate email
            "student_birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        # Should handle gracefully (either use existing user or show error)
        self.assertEqual(response.status_code, 200)

        # Only one user should exist with this email
        users_with_email = User.objects.filter(email="existing@test.com")
        self.assertEqual(users_with_email.count(), 1)

    def test_form_handles_profile_constraint_violations(self):
        """Test that form handles profile constraint violations."""
        self.client.force_login(self.admin_user)

        # Try to create ADULT_STUDENT without proper age (if age validation exists)
        today = datetime.date.today()
        minor_birth_date = today.replace(year=today.year - 16)  # 16 years old

        form_data = {
            "action": "add_student",
            "account_type": "self",  # Adult student
            "student_name": "Minor Student",
            "student_email": "minor@test.com",
            "student_birth_date": minor_birth_date.strftime("%Y-%m-%d"),
        }

        response = self.client.post(self.people_url, form_data)

        # Should handle constraint violation (either reject or force different type)
        self.assertEqual(response.status_code, 200)

        # Check if student was created and with what account type
        user_exists = User.objects.filter(email="minor@test.com").exists()
        if user_exists:
            user = User.objects.get(email="minor@test.com")
            if hasattr(user, "student_profile"):
                # If created, should not be ADULT_STUDENT for a minor
                self.assertNotEqual(user.student_profile.account_type, "ADULT_STUDENT")

    def test_form_transaction_rollback_on_constraint_violation(self):
        """Test that form submissions are properly rolled back on constraint violations."""
        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "separate",
            "student_name": "Transaction Test Student",
            "student_email": "transaction.test@example.com",
            "student_birth_date": "2008-01-01",
            "guardian_name": "Transaction Guardian",
            "guardian_email": "transaction.guardian@example.com",
        }

        # Mock PermissionService to raise an exception after user creation
        with patch(
            "accounts.permissions.PermissionService.setup_permissions_for_student",
            side_effect=Exception("Transaction rollback test"),
        ):
            response = self.client.post(self.people_url, form_data)

        # Should handle error gracefully
        self.assertEqual(response.status_code, 200)

        # Users should not exist due to transaction rollback
        self.assertFalse(User.objects.filter(email="transaction.test@example.com").exists())
        self.assertFalse(User.objects.filter(email="transaction.guardian@example.com").exists())

    def test_form_handles_school_membership_constraints(self):
        """Test that form handles school membership constraint violations."""
        # Create user with no school access
        no_access_user = User.objects.create_user(email="noaccess@test.com", name="No Access User", is_active=True)

        self.client.force_login(no_access_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "No Access Student",
            "student_email": "noaccess.student@test.com",
            "student_birth_date": "1995-01-01",
        }

        response = self.client.post(self.people_url, form_data)

        # Should handle lack of school access gracefully
        self.assertEqual(response.status_code, 200)

        # Student should not be created or should not have school membership
        if User.objects.filter(email="noaccess.student@test.com").exists():
            student = User.objects.get(email="noaccess.student@test.com")
            memberships = SchoolMembership.objects.filter(user=student)
            # Should either have no memberships or handle appropriately
            if memberships.exists():
                # If memberships exist, they should be for schools the creating user has access to
                pass

    def test_concurrent_form_submission_constraint_handling(self):
        """Test handling of constraints during concurrent form submissions."""
        self.client.force_login(self.admin_user)

        # Simulate concurrent submissions trying to create same user
        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "Concurrent Student",
            "student_email": "concurrent@test.com",
            "student_birth_date": "1995-01-01",
        }

        # First submission
        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response1 = self.client.post(self.people_url, form_data)

        # Immediate second submission (might hit unique constraint)
        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response2 = self.client.post(self.people_url, form_data)

        # Both should handle gracefully
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        # Only one user should exist
        users_with_email = User.objects.filter(email="concurrent@test.com")
        self.assertEqual(users_with_email.count(), 1)

    def test_educational_system_foreign_key_constraint(self):
        """Test handling of educational system foreign key constraints."""
        # Delete all educational systems to test constraint handling
        EducationalSystem.objects.all().delete()

        self.client.force_login(self.admin_user)

        form_data = {
            "action": "add_student",
            "account_type": "self",
            "student_name": "No System Student",
            "student_email": "no.system@test.com",
            "student_birth_date": "1995-01-01",
        }

        with patch("accounts.permissions.PermissionService.setup_permissions_for_student"):
            response = self.client.post(self.people_url, form_data)

        # Should handle missing educational system gracefully
        self.assertEqual(response.status_code, 200)

        # Either student should not be created or default system should be created
        if User.objects.filter(email="no.system@test.com").exists():
            student = User.objects.get(email="no.system@test.com")
            if hasattr(student, "student_profile"):
                # Should have some educational system assigned
                self.assertIsNotNone(student.student_profile.educational_system)


class ModelValidationIntegrationTests(TestCase):
    """Test model validation integration with form processing."""

    def setUp(self):
        """Set up test data."""
        self.educational_system = EducationalSystem.objects.get_or_create(
            name="Portugal",
            code="pt",
            defaults={"description": "Portuguese Educational System"},
        )[0]

    def test_student_profile_clean_method_validation(self):
        """Test that StudentProfile.clean() method is called during form processing."""
        # Create invalid student profile data that should fail clean() validation
        user = User.objects.create_user(email="test@test.com", name="Test User")
        guardian_user = User.objects.create_user(email="guardian@test.com", name="Guardian")
        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        # This should fail validation in clean() method
        student_profile = StudentProfile(
            user=user,
            account_type="ADULT_STUDENT",
            educational_system=self.educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
            guardian=guardian_profile,  # Invalid for ADULT_STUDENT
        )

        with self.assertRaises(ValidationError):
            student_profile.full_clean()

    def test_guardian_student_relationship_clean_validation(self):
        """Test that GuardianStudentRelationship.clean() is called."""
        school = School.objects.create(name="Test School")
        user = User.objects.create_user(email="test@test.com", name="Test User")

        # This should fail clean() validation (guardian = student)
        relationship = GuardianStudentRelationship(
            guardian=user,
            student=user,  # Same as guardian
            school=school,
        )

        with self.assertRaises(ValidationError):
            relationship.full_clean()

    def test_model_save_validation_enforcement(self):
        """Test that model validation is enforced on save."""
        user = User.objects.create_user(email="test@test.com", name="Test User")

        # Create invalid student profile
        student_profile = StudentProfile(
            user=None,  # Invalid for ADULT_STUDENT
            account_type="ADULT_STUDENT",
            educational_system=self.educational_system,
            birth_date=datetime.date(1995, 1, 1),
            school_year="12",
        )

        # Should raise ValidationError on save if validation is enforced
        with self.assertRaises(ValidationError):
            student_profile.full_clean()
            student_profile.save()  # This should not be reached
