"""
Tests for the Authorization system (AccountPermissions and SchoolPermissions).

This module tests the centralized permission logic for guardian-student relationships
and school-level operations, ensuring proper access control across all use cases.
"""

import datetime
from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.authorization import AccountPermissions, SchoolPermissions
from accounts.models import (
    EducationalSystem,
    GuardianProfile, 
    School,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
)
from accounts.models.enums import FinancialResponsibility
from accounts.tests.test_base import BaseTestCase

User = get_user_model()


class AccountPermissionsTestCase(BaseTestCase):
    """Test cases for AccountPermissions class."""

    def setUp(self):
        """Set up test data for permission tests."""
        # Create users
        self.student_user = User.objects.create_user(
            email="student@example.com", 
            name="Student User"
        )
        self.guardian_user = User.objects.create_user(
            email="guardian@example.com", 
            name="Guardian User"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", 
            name="Other User"
        )
        self.superuser = User.objects.create_user(
            email="admin@example.com", 
            name="Admin User",
            is_superuser=True
        )

        # Create guardian profile
        self.guardian_profile = GuardianProfile.objects.create(
            user=self.guardian_user
        )

        # Create student profile with guardian financial responsibility (default)
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            guardian=self.guardian_profile,
            financial_responsibility=FinancialResponsibility.GUARDIAN
        )

    def test_superuser_has_all_permissions(self):
        """Test that superusers can perform all actions."""
        all_actions = AccountPermissions.PERMISSION_MATRIX.keys()
        
        for action in all_actions:
            with self.subTest(action=action):
                self.assertTrue(
                    AccountPermissions.can_perform_action(
                        self.superuser, self.student_profile, action
                    ),
                    f"Superuser should have permission for {action}"
                )

    def test_guardian_financial_responsibility_permissions(self):
        """Test permissions when guardian has financial responsibility."""
        # Guardian should be able to make payments, not student
        self.assertTrue(
            AccountPermissions.can_make_purchases(self.guardian_user, self.student_profile)
        )
        self.assertFalse(
            AccountPermissions.can_make_purchases(self.student_user, self.student_profile)
        )

        # Guardian should be able to book sessions, not student
        self.assertTrue(
            AccountPermissions.can_book_sessions(self.guardian_user, self.student_profile)
        )
        self.assertFalse(
            AccountPermissions.can_book_sessions(self.student_user, self.student_profile)
        )

        # Both should be able to view profile/grades/attendance
        for action in ['view_profile', 'view_grades', 'view_attendance']:
            self.assertTrue(
                AccountPermissions.can_perform_action(
                    self.guardian_user, self.student_profile, action
                ),
                f"Guardian should be able to {action}"
            )
            self.assertTrue(
                AccountPermissions.can_perform_action(
                    self.student_user, self.student_profile, action
                ),
                f"Student should be able to {action}"
            )

    def test_self_financial_responsibility_permissions(self):
        """Test permissions when student has self financial responsibility."""
        # Change to self responsibility
        self.student_profile.financial_responsibility = FinancialResponsibility.SELF
        self.student_profile.save()

        # Student should be able to make payments, not guardian
        self.assertTrue(
            AccountPermissions.can_make_purchases(self.student_user, self.student_profile)
        )
        self.assertFalse(
            AccountPermissions.can_make_purchases(self.guardian_user, self.student_profile)
        )

        # Student should be able to book sessions, not guardian
        self.assertTrue(
            AccountPermissions.can_book_sessions(self.student_user, self.student_profile)
        )
        self.assertFalse(
            AccountPermissions.can_book_sessions(self.guardian_user, self.student_profile)
        )

        # Only student should be able to view profile in self mode
        self.assertTrue(
            AccountPermissions.can_perform_action(
                self.student_user, self.student_profile, 'view_profile'
            )
        )
        self.assertFalse(
            AccountPermissions.can_perform_action(
                self.guardian_user, self.student_profile, 'view_profile'
            )
        )

    def test_shared_financial_responsibility_permissions(self):
        """Test permissions when responsibility is shared."""
        # Change to shared responsibility
        self.student_profile.financial_responsibility = FinancialResponsibility.SHARED
        self.student_profile.save()

        # Both should be able to make payments
        self.assertTrue(
            AccountPermissions.can_make_purchases(self.student_user, self.student_profile)
        )
        self.assertTrue(
            AccountPermissions.can_make_purchases(self.guardian_user, self.student_profile)
        )

        # Both should be able to book sessions
        self.assertTrue(
            AccountPermissions.can_book_sessions(self.student_user, self.student_profile)
        )
        self.assertTrue(
            AccountPermissions.can_book_sessions(self.guardian_user, self.student_profile)
        )

        # Only guardian can manage budget in shared mode
        self.assertTrue(
            AccountPermissions.can_perform_action(
                self.guardian_user, self.student_profile, 'manage_budget'
            )
        )
        self.assertFalse(
            AccountPermissions.can_perform_action(
                self.student_user, self.student_profile, 'manage_budget'
            )
        )

    def test_unauthorized_user_has_no_permissions(self):
        """Test that unauthorized users have no permissions."""
        all_actions = AccountPermissions.PERMISSION_MATRIX.keys()
        
        for action in all_actions:
            with self.subTest(action=action):
                self.assertFalse(
                    AccountPermissions.can_perform_action(
                        self.other_user, self.student_profile, action
                    ),
                    f"Unauthorized user should not have permission for {action}"
                )

    def test_get_financial_responsible_user(self):
        """Test getting the financially responsible user."""
        # Guardian responsibility
        responsible_user = AccountPermissions.get_financial_responsible_user(
            self.student_profile
        )
        self.assertEqual(responsible_user, self.guardian_user)

        # Self responsibility
        self.student_profile.financial_responsibility = FinancialResponsibility.SELF
        responsible_user = AccountPermissions.get_financial_responsible_user(
            self.student_profile
        )
        self.assertEqual(responsible_user, self.student_user)

        # Shared responsibility (returns student as primary)
        self.student_profile.financial_responsibility = FinancialResponsibility.SHARED
        responsible_user = AccountPermissions.get_financial_responsible_user(
            self.student_profile
        )
        self.assertEqual(responsible_user, self.student_user)

    def test_get_authorized_users(self):
        """Test getting all authorized users."""
        # Guardian responsibility - both users authorized
        authorized = AccountPermissions.get_authorized_users(self.student_profile)
        self.assertIn(self.student_user, authorized)
        self.assertIn(self.guardian_user, authorized)
        self.assertEqual(len(authorized), 2)

        # Self responsibility - only student authorized
        self.student_profile.financial_responsibility = FinancialResponsibility.SELF
        authorized = AccountPermissions.get_authorized_users(self.student_profile)
        self.assertIn(self.student_user, authorized)
        self.assertNotIn(self.guardian_user, authorized)
        self.assertEqual(len(authorized), 1)

        # Shared responsibility - both users authorized  
        self.student_profile.financial_responsibility = FinancialResponsibility.SHARED
        authorized = AccountPermissions.get_authorized_users(self.student_profile)
        self.assertIn(self.student_user, authorized)
        self.assertIn(self.guardian_user, authorized)
        self.assertEqual(len(authorized), 2)

    def test_get_students_for_guardian(self):
        """Test getting students that a guardian is responsible for."""
        students = AccountPermissions.get_students_for_guardian(self.guardian_user)
        self.assertIn(self.student_profile, students)
        self.assertEqual(len(students), 1)

        # Test with user who is not a guardian
        students = AccountPermissions.get_students_for_guardian(self.other_user)
        self.assertEqual(len(students), 0)

        # Test with self-responsible student (should not appear in guardian's list)
        self.student_profile.financial_responsibility = FinancialResponsibility.SELF
        self.student_profile.save()
        students = AccountPermissions.get_students_for_guardian(self.guardian_user)
        self.assertEqual(len(students), 0)

    def test_requires_guardian_approval(self):
        """Test guardian approval requirements."""
        # Guardian responsibility - approval required for financial actions
        self.assertTrue(
            AccountPermissions.requires_guardian_approval(
                self.student_profile, 'make_payment'
            )
        )
        self.assertTrue(
            AccountPermissions.requires_guardian_approval(
                self.student_profile, 'book_session'
            )
        )

        # Self responsibility - no approval required
        self.student_profile.financial_responsibility = FinancialResponsibility.SELF
        self.assertFalse(
            AccountPermissions.requires_guardian_approval(
                self.student_profile, 'make_payment'
            )
        )

        # Shared responsibility - approval required for payments only
        self.student_profile.financial_responsibility = FinancialResponsibility.SHARED
        self.assertTrue(
            AccountPermissions.requires_guardian_approval(
                self.student_profile, 'make_payment'
            )
        )
        self.assertFalse(
            AccountPermissions.requires_guardian_approval(
                self.student_profile, 'book_session'
            )
        )

    def test_is_self_managed(self):
        """Test checking if student is self-managed."""
        # Guardian responsibility - not self-managed
        self.assertFalse(AccountPermissions.is_self_managed(self.student_profile))

        # Self responsibility - self-managed
        self.student_profile.financial_responsibility = FinancialResponsibility.SELF
        self.assertTrue(AccountPermissions.is_self_managed(self.student_profile))

        # Shared responsibility - not self-managed
        self.student_profile.financial_responsibility = FinancialResponsibility.SHARED
        self.assertFalse(AccountPermissions.is_self_managed(self.student_profile))

    def test_get_permission_summary(self):
        """Test getting complete permission summary."""
        # Test for guardian user
        summary = AccountPermissions.get_permission_summary(
            self.guardian_user, self.student_profile
        )
        
        # Guardian should have financial permissions
        self.assertTrue(summary['make_payment'])
        self.assertTrue(summary['book_session'])
        self.assertTrue(summary['view_profile'])
        
        # Test for student user
        summary = AccountPermissions.get_permission_summary(
            self.student_user, self.student_profile
        )
        
        # Student should have view permissions but not financial
        self.assertFalse(summary['make_payment'])
        self.assertFalse(summary['book_session'])
        self.assertTrue(summary['view_profile'])

    def test_null_user_and_profile_handling(self):
        """Test handling of null users and profiles."""
        # Null user
        self.assertFalse(
            AccountPermissions.can_perform_action(
                None, self.student_profile, 'view_profile'
            )
        )

        # Null profile
        self.assertFalse(
            AccountPermissions.can_perform_action(
                self.student_user, None, 'view_profile'
            )
        )

    def test_student_without_guardian_permissions(self):
        """Test permissions for student without guardian."""
        # Create student without guardian
        student_no_guardian = StudentProfile.objects.create(
            user=self.other_user,
            educational_system=self.default_educational_system,
            birth_date=datetime.date(2008, 1, 1),
            school_year="10",
            guardian=None,
            financial_responsibility=FinancialResponsibility.SELF
        )

        # Student should be able to perform self actions
        self.assertTrue(
            AccountPermissions.can_perform_action(
                self.other_user, student_no_guardian, 'view_profile'
            )
        )
        self.assertTrue(
            AccountPermissions.can_make_purchases(self.other_user, student_no_guardian)
        )


class SchoolPermissionsTestCase(BaseTestCase):
    """Test cases for SchoolPermissions class."""

    def setUp(self):
        """Set up test data for school permission tests."""
        # Create users
        self.admin_user = User.objects.create_user(
            email="admin@example.com", 
            name="Admin User"
        )
        self.teacher_user = User.objects.create_user(
            email="teacher@example.com", 
            name="Teacher User"
        )
        self.student_user = User.objects.create_user(
            email="student@example.com", 
            name="Student User"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", 
            name="Other User"
        )
        self.superuser = User.objects.create_user(
            email="super@example.com", 
            name="Super User",
            is_superuser=True
        )

        # Create school
        self.school = School.objects.create(
            name="Test School",
            description="A test school"
        )

        # Create memberships
        SchoolMembership.objects.create(
            user=self.admin_user,
            school=self.school,
            role=SchoolRole.SCHOOL_ADMIN,
            is_active=True
        )
        SchoolMembership.objects.create(
            user=self.teacher_user,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        SchoolMembership.objects.create(
            user=self.student_user,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )

    def test_can_manage_school(self):
        """Test school management permissions."""
        # Admin should be able to manage school
        self.assertTrue(
            SchoolPermissions.can_manage_school(self.admin_user, self.school)
        )

        # Teacher should not be able to manage school
        self.assertFalse(
            SchoolPermissions.can_manage_school(self.teacher_user, self.school)
        )

        # Student should not be able to manage school
        self.assertFalse(
            SchoolPermissions.can_manage_school(self.student_user, self.school)
        )

        # Other user should not be able to manage school
        self.assertFalse(
            SchoolPermissions.can_manage_school(self.other_user, self.school)
        )

        # Superuser should be able to manage school
        self.assertTrue(
            SchoolPermissions.can_manage_school(self.superuser, self.school)
        )

    def test_can_manage_students(self):
        """Test student management permissions."""
        # Admin should be able to manage students
        self.assertTrue(
            SchoolPermissions.can_manage_students(self.admin_user, self.school)
        )

        # Teacher should be able to manage students
        self.assertTrue(
            SchoolPermissions.can_manage_students(self.teacher_user, self.school)
        )

        # Student should not be able to manage students
        self.assertFalse(
            SchoolPermissions.can_manage_students(self.student_user, self.school)
        )

        # Other user should not be able to manage students
        self.assertFalse(
            SchoolPermissions.can_manage_students(self.other_user, self.school)
        )

        # Superuser should be able to manage students
        self.assertTrue(
            SchoolPermissions.can_manage_students(self.superuser, self.school)
        )

    def test_can_view_financial_reports(self):
        """Test financial report viewing permissions."""
        # Admin should be able to view financial reports
        self.assertTrue(
            SchoolPermissions.can_view_financial_reports(self.admin_user, self.school)
        )

        # Teacher should not be able to view financial reports
        self.assertFalse(
            SchoolPermissions.can_view_financial_reports(self.teacher_user, self.school)
        )

        # Student should not be able to view financial reports
        self.assertFalse(
            SchoolPermissions.can_view_financial_reports(self.student_user, self.school)
        )

        # Other user should not be able to view financial reports
        self.assertFalse(
            SchoolPermissions.can_view_financial_reports(self.other_user, self.school)
        )

        # Superuser should be able to view financial reports
        self.assertTrue(
            SchoolPermissions.can_view_financial_reports(self.superuser, self.school)
        )

    def test_get_user_schools(self):
        """Test getting schools for user."""
        # Admin should see their school
        admin_schools = SchoolPermissions.get_user_schools(self.admin_user)
        self.assertEqual(admin_schools.count(), 1)
        self.assertEqual(admin_schools.first().school, self.school)

        # Filter by role - admin role
        admin_schools = SchoolPermissions.get_user_schools(
            self.admin_user, SchoolRole.SCHOOL_ADMIN
        )
        self.assertEqual(admin_schools.count(), 1)

        # Filter by role - teacher role (should return 0 for admin user)
        admin_teacher_schools = SchoolPermissions.get_user_schools(
            self.admin_user, SchoolRole.TEACHER
        )
        self.assertEqual(admin_teacher_schools.count(), 0)

        # Teacher should see their school when filtering by teacher role
        teacher_schools = SchoolPermissions.get_user_schools(
            self.teacher_user, SchoolRole.TEACHER
        )
        self.assertEqual(teacher_schools.count(), 1)
        self.assertEqual(teacher_schools.first().school, self.school)

        # Other user should see no schools
        other_schools = SchoolPermissions.get_user_schools(self.other_user)
        self.assertEqual(other_schools.count(), 0)

    def test_inactive_membership_no_permissions(self):
        """Test that inactive memberships don't grant permissions."""
        # Deactivate admin membership
        membership = SchoolMembership.objects.get(
            user=self.admin_user, school=self.school
        )
        membership.is_active = False
        membership.save()

        # Admin should no longer have permissions
        self.assertFalse(
            SchoolPermissions.can_manage_school(self.admin_user, self.school)
        )
        self.assertFalse(
            SchoolPermissions.can_view_financial_reports(self.admin_user, self.school)
        )

        # Should not appear in user schools
        admin_schools = SchoolPermissions.get_user_schools(self.admin_user)
        self.assertEqual(admin_schools.count(), 0)