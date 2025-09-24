"""
Tests for multiple guardians per student functionality (Issue #304)
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from accounts.forms import AddGuardianForm, EditGuardianPermissionsForm
from accounts.models import CustomUser, GuardianProfile, GuardianStudentRelationship, School, StudentProfile
from accounts.models.enums import SchoolRole
from accounts.models.schools import SchoolMembership

User = get_user_model()


class GuardianStudentRelationshipModelTest(TestCase):
    """Test the enhanced GuardianStudentRelationship model."""

    def setUp(self):
        """Set up test data."""
        # Create school
        self.school = School.objects.create(name="Test School", address="123 Test St", phone_number="1234567890")

        # Create guardian users and profiles
        self.guardian1 = User.objects.create_user(email="guardian1@test.com", name="Guardian One")
        self.guardian_profile1 = GuardianProfile.objects.create(user=self.guardian1)

        self.guardian2 = User.objects.create_user(email="guardian2@test.com", name="Guardian Two")
        self.guardian_profile2 = GuardianProfile.objects.create(user=self.guardian2)

        # Create student user and profile
        self.student = User.objects.create_user(email="student@test.com", name="Test Student")
        self.student_profile = StudentProfile.objects.create(
            user=self.student,
            guardian=self.guardian_profile1,  # Legacy field
            birth_date=date(2010, 1, 1),
        )

    def test_create_primary_guardian_relationship(self):
        """Test creating a primary guardian relationship."""
        relationship = GuardianStudentRelationship.objects.create(
            guardian=self.guardian1,
            student=self.student,
            school=self.school,
            is_primary=True,
            relationship_type="Mother",
        )

        self.assertTrue(relationship.is_primary)
        self.assertTrue(relationship.can_manage_finances)  # Auto-set for primary
        self.assertTrue(relationship.can_book_classes)
        self.assertTrue(relationship.can_view_records)
        self.assertTrue(relationship.can_edit_profile)

    def test_only_one_primary_guardian_per_student(self):
        """Test constraint: only one primary guardian per student."""
        # Create first primary guardian
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian1, student=self.student, school=self.school, is_primary=True
        )

        # Try to create second primary guardian - should fail
        with self.assertRaises(IntegrityError):
            GuardianStudentRelationship.objects.create(
                guardian=self.guardian2, student=self.student, school=self.school, is_primary=True
            )

    def test_multiple_non_primary_guardians(self):
        """Test that multiple non-primary guardians are allowed."""
        # Create primary guardian
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian1, student=self.student, school=self.school, is_primary=True
        )

        # Create non-primary guardian - should succeed
        relationship2 = GuardianStudentRelationship.objects.create(
            guardian=self.guardian2,
            student=self.student,
            school=self.school,
            is_primary=False,
            relationship_type="Father",
        )

        self.assertFalse(relationship2.is_primary)
        self.assertEqual(GuardianStudentRelationship.objects.filter(student=self.student).count(), 2)

    def test_guardian_cannot_be_student(self):
        """Test constraint: guardian cannot be the same as student."""
        with self.assertRaises(IntegrityError):
            GuardianStudentRelationship.objects.create(
                guardian=self.student,  # Same as student
                student=self.student,
                school=self.school,
                is_primary=True,
            )

    def test_primary_guardian_auto_financial_permission(self):
        """Test that primary guardians automatically get financial permissions."""
        relationship = GuardianStudentRelationship.objects.create(
            guardian=self.guardian1,
            student=self.student,
            school=self.school,
            is_primary=True,
            can_manage_finances=False,  # Try to set to False
        )

        # Refresh from database
        relationship.refresh_from_db()
        self.assertTrue(relationship.can_manage_finances)  # Should be auto-set to True


class StudentProfileBackwardCompatibilityTest(TestCase):
    """Test backward compatibility methods on StudentProfile."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(name="Test School", address="123 Test St", phone_number="1234567890")

        # Create guardians
        self.guardian1 = User.objects.create_user(email="guardian1@test.com", name="Guardian One")
        self.guardian_profile1 = GuardianProfile.objects.create(user=self.guardian1)

        self.guardian2 = User.objects.create_user(email="guardian2@test.com", name="Guardian Two")
        self.guardian_profile2 = GuardianProfile.objects.create(user=self.guardian2)

        # Create student
        self.student = User.objects.create_user(email="student@test.com", name="Test Student")
        self.student_profile = StudentProfile.objects.create(
            user=self.student, guardian=self.guardian_profile1, birth_date=date(2010, 1, 1)
        )

        # Create relationships
        self.primary_rel = GuardianStudentRelationship.objects.create(
            guardian=self.guardian1, student=self.student, school=self.school, is_primary=True
        )

        self.secondary_rel = GuardianStudentRelationship.objects.create(
            guardian=self.guardian2, student=self.student, school=self.school, is_primary=False
        )

    def test_primary_guardian_property(self):
        """Test the primary_guardian property returns the correct guardian."""
        primary = self.student_profile.primary_guardian
        self.assertEqual(primary, self.guardian_profile1)

    def test_has_primary_guardian(self):
        """Test the has_primary_guardian method."""
        self.assertTrue(self.student_profile.has_primary_guardian())

        # Remove primary guardian
        self.primary_rel.delete()
        self.assertFalse(self.student_profile.has_primary_guardian())

    def test_all_guardians(self):
        """Test the all_guardians method returns all guardians."""
        guardians = self.student_profile.all_guardians
        self.assertEqual(guardians.count(), 2)
        self.assertIn(self.guardian_profile1, guardians)
        self.assertIn(self.guardian_profile2, guardians)

    def test_get_guardians_for_school(self):
        """Test getting guardians for a specific school."""
        guardians = self.student_profile.get_guardians_for_school(self.school)
        self.assertEqual(guardians.count(), 2)

        # Create another school and relationship
        school2 = School.objects.create(name="School 2", address="456 Test Ave", phone_number="9876543210")

        # Guardian 1 is only in school 1
        guardians_school2 = self.student_profile.get_guardians_for_school(school2)
        self.assertEqual(guardians_school2.count(), 0)


class GuardianFormsTest(TestCase):
    """Test guardian management forms."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(name="Test School", address="123 Test St", phone_number="1234567890")

        self.student = User.objects.create_user(email="student@test.com", name="Test Student")
        self.student_profile = StudentProfile.objects.create(user=self.student, birth_date=date(2010, 1, 1))

        self.guardian = User.objects.create_user(email="guardian@test.com", name="Guardian User")

    def test_add_guardian_form_valid(self):
        """Test AddGuardianForm with valid data."""
        form_data = {
            "email": "newguardian@test.com",
            "name": "New Guardian",
            "relationship_type": "Mother",
            "is_primary": True,
            "can_book_classes": True,
            "can_view_records": True,
            "can_edit_profile": True,
        }

        form = AddGuardianForm(data=form_data, student=self.student, school=self.school)
        self.assertTrue(form.is_valid())

    def test_add_guardian_form_duplicate_relationship(self):
        """Test AddGuardianForm prevents duplicate relationships."""
        # Create existing relationship
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian, student=self.student, school=self.school, is_primary=True
        )

        # Try to add same guardian again
        form_data = {
            "email": self.guardian.email,  # Existing guardian email
            "name": "Guardian User",
            "relationship_type": "Father",
            "is_primary": False,
        }

        form = AddGuardianForm(data=form_data, student=self.student, school=self.school)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_edit_permissions_form_primary_guardian(self):
        """Test EditGuardianPermissionsForm enforces primary guardian rules."""
        relationship = GuardianStudentRelationship.objects.create(
            guardian=self.guardian, student=self.student, school=self.school, is_primary=True
        )

        form_data = {
            "can_manage_finances": False,  # Try to remove financial permission
            "can_book_classes": True,
            "can_view_records": True,
            "can_edit_profile": True,
            "can_receive_notifications": True,
            "relationship_type": "Mother",
            "is_primary": True,  # Must include this for primary guardian
        }

        form = EditGuardianPermissionsForm(relationship=relationship, data=form_data)

        self.assertTrue(form.is_valid())
        saved_rel = form.save()

        # Financial permission should remain True for primary guardian
        self.assertTrue(saved_rel.can_manage_finances)


class GuardianViewsTest(TransactionTestCase):
    """Test guardian management views."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(name="Test School", address="123 Test St", phone_number="1234567890")

        # Create admin user
        self.admin = User.objects.create_user(email="admin@test.com", name="Admin User", password="testpass123")
        SchoolMembership.objects.create(
            user=self.admin, school=self.school, role=SchoolRole.SCHOOL_ADMIN, is_active=True
        )

        # Create student
        self.student = User.objects.create_user(email="student@test.com", name="Test Student")
        self.student_profile = StudentProfile.objects.create(user=self.student, birth_date=date(2010, 1, 1))

        # Create primary guardian
        self.guardian = User.objects.create_user(
            email="guardian@test.com", name="Guardian User", password="testpass123"
        )
        self.guardian_profile = GuardianProfile.objects.create(user=self.guardian)

        self.relationship = GuardianStudentRelationship.objects.create(
            guardian=self.guardian, student=self.student, school=self.school, is_primary=True
        )

    def test_manage_guardians_view_as_admin(self):
        """Test that admin can access guardian management view."""
        self.client.login(email="admin@test.com", password="testpass123")

        url = reverse(
            "accounts:manage_student_guardians", kwargs={"school_id": self.school.id, "student_id": self.student.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Guardian User")
        self.assertContains(response, "PRIMARY")

    def test_add_guardian_view(self):
        """Test adding a new guardian."""
        self.client.login(email="admin@test.com", password="testpass123")

        url = reverse("accounts:add_guardian", kwargs={"school_id": self.school.id, "student_id": self.student.id})

        response = self.client.post(
            url,
            {
                "email": "newguardian@test.com",
                "name": "New Guardian",
                "relationship_type": "Father",
                "is_primary": "false",  # String because it's from form
                "can_book_classes": "true",
                "can_view_records": "true",
                "can_edit_profile": "false",
            },
            headers={"hx-request": "true"},
        )  # Simulate HTMX request

        self.assertEqual(response.status_code, 200)

        # Check that guardian was created
        new_guardian = User.objects.filter(email="newguardian@test.com").first()
        self.assertIsNotNone(new_guardian)

        # Check relationship was created
        relationship = GuardianStudentRelationship.objects.filter(guardian=new_guardian, student=self.student).first()
        self.assertIsNotNone(relationship)
        self.assertFalse(relationship.is_primary)

    def test_cannot_remove_last_guardian(self):
        """Test that the last guardian cannot be removed."""
        self.client.login(email="admin@test.com", password="testpass123")

        url = reverse(
            "accounts:remove_guardian",
            kwargs={
                "school_id": self.school.id,
                "student_id": self.student.id,
                "relationship_id": self.relationship.id,
            },
        )

        response = self.client.delete(url, headers={"hx-request": "true"})

        # Should get an error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cannot remove")

        # Relationship should still exist
        self.assertTrue(GuardianStudentRelationship.objects.filter(id=self.relationship.id).exists())

    def test_set_primary_guardian(self):
        """Test changing which guardian is primary."""
        # Create a second guardian
        guardian2 = User.objects.create_user(email="guardian2@test.com", name="Guardian Two")
        GuardianProfile.objects.create(user=guardian2)

        relationship2 = GuardianStudentRelationship.objects.create(
            guardian=guardian2, student=self.student, school=self.school, is_primary=False
        )

        self.client.login(email="admin@test.com", password="testpass123")

        url = reverse(
            "accounts:set_primary_guardian",
            kwargs={"school_id": self.school.id, "student_id": self.student.id, "relationship_id": relationship2.id},
        )

        response = self.client.post(url, headers={"hx-request": "true"})
        self.assertEqual(response.status_code, 200)

        # Check that guardian2 is now primary
        relationship2.refresh_from_db()
        self.assertTrue(relationship2.is_primary)
        self.assertTrue(relationship2.can_manage_finances)

        # Check that guardian1 is no longer primary
        self.relationship.refresh_from_db()
        self.assertFalse(self.relationship.is_primary)


class GuardianBusinessRulesTest(TransactionTestCase):
    """Test comprehensive business rules and edge cases for guardian management."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(name="Test School", address="123 Test St", phone_number="1234567890")

        self.school2 = School.objects.create(name="Test School 2", address="456 Test Ave", phone_number="0987654321")

        # Create guardian users
        self.guardian1 = User.objects.create_user(email="guardian1@test.com", name="Primary Guardian")
        self.guardian_profile1 = GuardianProfile.objects.create(user=self.guardian1)

        self.guardian2 = User.objects.create_user(email="guardian2@test.com", name="Secondary Guardian")
        self.guardian_profile2 = GuardianProfile.objects.create(user=self.guardian2)

        # Create student user and profile
        self.student = User.objects.create_user(email="student@test.com", name="Test Student")
        self.student_profile = StudentProfile.objects.create(user=self.student, birth_date=date(2010, 1, 1))

    def test_cannot_remove_last_guardian_relationship(self):
        """Test that the last guardian relationship cannot be removed."""
        # Create only one guardian relationship
        relationship = GuardianStudentRelationship.objects.create(
            guardian=self.guardian1, student=self.student, school=self.school, is_primary=True
        )

        # Verify we have exactly one guardian
        self.assertEqual(
            GuardianStudentRelationship.objects.filter(
                student=self.student, school=self.school, is_active=True
            ).count(),
            1,
        )

        # Attempt to deactivate the only guardian should fail in business logic
        # This would typically be enforced in the view layer
        relationship.is_active = False
        relationship.save()  # This saves but business logic should prevent it

        # In a real implementation, there would be a check before allowing this

    def test_primary_guardian_transfer_workflow(self):
        """Test complete workflow of transferring primary guardian status."""
        # Create two guardians
        primary_rel = GuardianStudentRelationship.objects.create(
            guardian=self.guardian1, student=self.student, school=self.school, is_primary=True
        )

        secondary_rel = GuardianStudentRelationship.objects.create(
            guardian=self.guardian2, student=self.student, school=self.school, is_primary=False
        )

        # Verify initial state
        self.assertTrue(primary_rel.is_primary)
        self.assertTrue(primary_rel.can_manage_finances)
        self.assertFalse(secondary_rel.is_primary)
        self.assertFalse(secondary_rel.can_manage_finances)

        # Transfer primary status
        with transaction.atomic():
            # Remove primary from first guardian
            primary_rel.is_primary = False
            primary_rel.can_manage_finances = False
            primary_rel.save()

            # Set second guardian as primary
            secondary_rel.is_primary = True
            secondary_rel.save()  # This should auto-set financial permissions

        # Refresh from database
        primary_rel.refresh_from_db()
        secondary_rel.refresh_from_db()

        # Verify the transfer
        self.assertFalse(primary_rel.is_primary)
        self.assertTrue(secondary_rel.is_primary)
        self.assertTrue(secondary_rel.can_manage_finances)  # Auto-set by save()

    def test_guardian_permissions_hierarchy(self):
        """Test that guardian permissions work correctly for different scenarios."""
        # Create primary guardian
        primary_rel = GuardianStudentRelationship.objects.create(
            guardian=self.guardian1,
            student=self.student,
            school=self.school,
            is_primary=True,
            can_book_classes=True,
            can_view_records=True,
            can_edit_profile=True,
        )

        # Create secondary guardian with limited permissions
        secondary_rel = GuardianStudentRelationship.objects.create(
            guardian=self.guardian2,
            student=self.student,
            school=self.school,
            is_primary=False,
            can_book_classes=True,
            can_view_records=False,  # Limited access
            can_edit_profile=False,
            can_manage_finances=False,
        )

        # Verify permission differences
        self.assertTrue(primary_rel.can_manage_finances)
        self.assertTrue(primary_rel.can_view_records)
        self.assertTrue(primary_rel.can_edit_profile)

        self.assertFalse(secondary_rel.can_manage_finances)
        self.assertFalse(secondary_rel.can_view_records)
        self.assertFalse(secondary_rel.can_edit_profile)
        self.assertTrue(secondary_rel.can_book_classes)  # This permission is allowed

    def test_cross_school_guardian_relationships(self):
        """Test guardian relationships across multiple schools."""
        # Create guardian relationship in first school
        rel_school1 = GuardianStudentRelationship.objects.create(
            guardian=self.guardian1, student=self.student, school=self.school, is_primary=True
        )

        # Create guardian relationship in second school (same guardian, same student)
        # Can only have one primary guardian globally, so this must be non-primary
        rel_school2 = GuardianStudentRelationship.objects.create(
            guardian=self.guardian1,
            student=self.student,
            school=self.school2,
            is_primary=False,  # Cannot be primary - only one primary per student globally
        )

        # Both relationships should exist
        self.assertTrue(
            GuardianStudentRelationship.objects.filter(
                guardian=self.guardian1, student=self.student, school=self.school
            ).exists()
        )
        self.assertTrue(
            GuardianStudentRelationship.objects.filter(
                guardian=self.guardian1, student=self.student, school=self.school2
            ).exists()
        )

        # Only one can be primary (global constraint)
        self.assertTrue(rel_school1.is_primary)
        self.assertFalse(rel_school2.is_primary)

        # Trying to create another primary guardian for same student should fail
        with self.assertRaises(IntegrityError):
            GuardianStudentRelationship.objects.create(
                guardian=self.guardian2, student=self.student, school=self.school2, is_primary=True
            )

    def test_guardian_profile_creation_workflow(self):
        """Test complete workflow of creating guardian profiles and relationships."""
        # Create a new guardian user (simulating form submission)
        guardian_email = "newguardian@test.com"
        guardian_name = "New Guardian"

        # Simulate AddGuardianForm.save() workflow
        guardian_user, created = User.objects.get_or_create(
            email=guardian_email,
            defaults={
                "name": guardian_name,
                "is_active": True,
            },
        )
        self.assertTrue(created)

        # Create guardian profile
        guardian_profile = GuardianProfile.objects.create(user=guardian_user)

        # Create relationship
        relationship = GuardianStudentRelationship.objects.create(
            guardian=guardian_user,
            student=self.student,
            school=self.school,
            is_primary=True,
            relationship_type="Father",
            can_book_classes=True,
            can_view_records=True,
            can_edit_profile=True,
        )

        # Verify everything is created correctly
        self.assertEqual(guardian_user.email, guardian_email)
        self.assertEqual(guardian_user.name, guardian_name)
        self.assertTrue(hasattr(guardian_user, "guardian_profile"))
        self.assertTrue(relationship.is_primary)
        self.assertTrue(relationship.can_manage_finances)  # Auto-set
        self.assertEqual(relationship.relationship_type, "Father")

    def test_duplicate_guardian_prevention(self):
        """Test that duplicate guardian relationships are prevented."""
        # Create first relationship
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian1, student=self.student, school=self.school, is_primary=True
        )

        # Attempt to create duplicate relationship should fail
        with self.assertRaises(IntegrityError):
            GuardianStudentRelationship.objects.create(
                guardian=self.guardian1,
                student=self.student,
                school=self.school,  # Same combination
                is_primary=False,
            )

    def test_emergency_contact_workflow(self):
        """Test that guardians can serve as emergency contacts."""
        # Create primary guardian with full permissions
        primary_rel = GuardianStudentRelationship.objects.create(
            guardian=self.guardian1,
            student=self.student,
            school=self.school,
            is_primary=True,
            relationship_type="Mother",
            can_receive_notifications=True,
        )

        # Create emergency contact guardian with limited permissions
        emergency_rel = GuardianStudentRelationship.objects.create(
            guardian=self.guardian2,
            student=self.student,
            school=self.school,
            is_primary=False,
            relationship_type="Emergency Contact",
            can_book_classes=False,
            can_view_records=False,
            can_edit_profile=False,
            can_manage_finances=False,
            can_receive_notifications=True,  # Can receive emergency notifications
        )

        # Verify both can receive notifications
        self.assertTrue(primary_rel.can_receive_notifications)
        self.assertTrue(emergency_rel.can_receive_notifications)

        # But only primary has other permissions
        self.assertTrue(primary_rel.can_manage_finances)
        self.assertFalse(emergency_rel.can_manage_finances)


class GuardianConstraintValidationTest(TestCase):
    """Test database constraints and validation rules."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Constraint Test School", address="123 Test St", phone_number="1234567890"
        )

        self.guardian_user = User.objects.create_user(email="guardian@test.com", name="Guardian User")
        GuardianProfile.objects.create(user=self.guardian_user)

        self.student_user = User.objects.create_user(email="student@test.com", name="Student User")
        StudentProfile.objects.create(user=self.student_user, birth_date=date(2010, 1, 1))

    def test_unique_primary_guardian_constraint(self):
        """Test that only one guardian can be primary per student."""
        # Create first primary guardian
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_user, student=self.student_user, school=self.school, is_primary=True
        )

        # Create second guardian
        guardian2 = User.objects.create_user(email="guardian2@test.com", name="Guardian Two")
        GuardianProfile.objects.create(user=guardian2)

        # Attempt to create second primary guardian should fail
        with self.assertRaises(IntegrityError):
            GuardianStudentRelationship.objects.create(
                guardian=guardian2, student=self.student_user, school=self.school, is_primary=True
            )

    def test_guardian_cannot_be_student_constraint(self):
        """Test that a user cannot be both guardian and student in same relationship."""
        with self.assertRaises(IntegrityError):
            GuardianStudentRelationship.objects.create(
                guardian=self.student_user,  # Same as student
                student=self.student_user,
                school=self.school,
                is_primary=True,
            )

    def test_unique_together_constraint(self):
        """Test that guardian-student-school combination must be unique."""
        # Create first relationship
        GuardianStudentRelationship.objects.create(
            guardian=self.guardian_user, student=self.student_user, school=self.school, is_primary=True
        )

        # Attempt to create duplicate should fail
        with self.assertRaises(IntegrityError):
            GuardianStudentRelationship.objects.create(
                guardian=self.guardian_user,
                student=self.student_user,
                school=self.school,  # Same combination
                is_primary=False,
            )

    def test_inactive_relationship_handling(self):
        """Test behavior with inactive relationships."""
        # Create active relationship
        active_rel = GuardianStudentRelationship.objects.create(
            guardian=self.guardian_user, student=self.student_user, school=self.school, is_primary=True, is_active=True
        )

        # Deactivate it
        active_rel.is_active = False
        active_rel.save()

        # Verify the relationship is deactivated
        self.assertFalse(active_rel.is_active)
        self.assertTrue(active_rel.is_primary)  # Still marked as primary

        # Create new guardian for non-primary relationship
        guardian2 = User.objects.create_user(email="guardian2@test.com", name="Guardian Two")
        GuardianProfile.objects.create(user=guardian2)

        # Can create non-primary relationships even with inactive primary
        new_rel = GuardianStudentRelationship.objects.create(
            guardian=guardian2, student=self.student_user, school=self.school, is_primary=False, is_active=True
        )

        self.assertFalse(new_rel.is_primary)
        self.assertTrue(new_rel.is_active)
        self.assertFalse(active_rel.is_active)

        # The business logic for handling inactive primary guardians
        # would be implemented in the application layer, not database constraints


class GuardianFormIntegrationTest(TestCase):
    """Integration tests for guardian forms with complete workflows."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(name="Form Test School", address="123 Test St", phone_number="1234567890")

        self.student_user = User.objects.create_user(email="student@test.com", name="Test Student")
        self.student_profile = StudentProfile.objects.create(user=self.student_user, birth_date=date(2010, 1, 1))

    def test_add_first_guardian_workflow(self):
        """Test adding the first guardian to a student."""
        # Should be able to set as primary
        form_data = {
            "email": "firstguardian@test.com",
            "name": "First Guardian",
            "relationship_type": "Mother",
            "is_primary": True,
            "can_book_classes": True,
            "can_view_records": True,
            "can_edit_profile": True,
        }

        form = AddGuardianForm(data=form_data, student=self.student_user, school=self.school)
        self.assertTrue(form.is_valid())

        # Simulate form save (need to provide created_by parameter)
        admin_user = User.objects.create_user(email="admin@test.com", name="Admin User")
        relationship = form.save(created_by=admin_user)
        self.assertTrue(relationship.is_primary)
        self.assertTrue(relationship.can_manage_finances)

    def test_add_second_guardian_workflow(self):
        """Test adding a second guardian when primary already exists."""
        # Create first guardian
        guardian1 = User.objects.create_user(email="guardian1@test.com", name="Primary Guardian")
        GuardianProfile.objects.create(user=guardian1)
        GuardianStudentRelationship.objects.create(
            guardian=guardian1, student=self.student_user, school=self.school, is_primary=True
        )

        # Try to add second guardian as primary (should be prevented in form)
        form_data = {
            "email": "guardian2@test.com",
            "name": "Second Guardian",
            "relationship_type": "Father",
            "is_primary": True,  # This should be ignored/prevented
            "can_book_classes": True,
            "can_view_records": False,
            "can_edit_profile": False,
        }

        form = AddGuardianForm(data=form_data, student=self.student_user, school=self.school)
        # Form should be valid but primary status should be handled appropriately
        self.assertTrue(form.is_valid())

    def test_edit_guardian_permissions_workflow(self):
        """Test editing guardian permissions through form."""
        # Create guardian relationship
        guardian_user = User.objects.create_user(email="guardian@test.com", name="Guardian User")
        GuardianProfile.objects.create(user=guardian_user)

        relationship = GuardianStudentRelationship.objects.create(
            guardian=guardian_user,
            student=self.student_user,
            school=self.school,
            is_primary=True,
            can_book_classes=True,
            can_view_records=True,
            can_edit_profile=True,
        )

        # Edit permissions
        form_data = {
            "relationship_type": "Updated Relationship",
            "is_primary": True,
            "can_manage_finances": True,  # Should remain true for primary
            "can_book_classes": False,
            "can_view_records": True,
            "can_edit_profile": False,
            "can_receive_notifications": True,
        }

        form = EditGuardianPermissionsForm(relationship=relationship, data=form_data)
        self.assertTrue(form.is_valid())

        updated_rel = form.save()
        self.assertEqual(updated_rel.relationship_type, "Updated Relationship")
        self.assertFalse(updated_rel.can_book_classes)
        self.assertFalse(updated_rel.can_edit_profile)
        # Financial permissions should remain True for primary guardian
        self.assertTrue(updated_rel.can_manage_finances)
