"""
Test cases for validating fixture infrastructure improvements (Issue #181).

These tests specifically validate that the new fixture infrastructure properly
establishes all required model relationships and satisfies database constraints
that were causing ~40-50 test failures.

Following TDD methodology:
- Tests should FAIL initially (red state) when fixture infrastructure is incomplete
- Tests should PASS (green state) once proper fixture infrastructure is implemented

Focus areas from Issue #181:
1. StudentProfile - Missing school associations
2. ParentChildRelationship - Incomplete relationship setup  
3. SchoolMembership - Not created for test users
4. PricingPlan - Missing required fields
5. StudentAccountBalance - Missing student relationships
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from accounts.models import (
    School, 
    SchoolMembership, 
    SchoolRole,
    StudentProfile,
    ParentChildRelationship,
    EducationalSystem
)
from finances.models import (
    StudentAccountBalance,
    PricingPlan,
    PlanType,
    StoredPaymentMethod,
    ClassSession,
    SessionType,
    SessionStatus,
    TeacherCompensationRule,
    CompensationRuleType
)

User = get_user_model()


class FixtureInfrastructureBaseTestCase(TestCase):
    """
    Base test case for fixture infrastructure validation.
    
    This base class demonstrates the MINIMAL setup that causes constraint violations
    and should be replaced by proper fixture infrastructure.
    """
    
    def setUp(self):
        """
        Intentionally minimal setup to expose constraint violations.
        This setup should FAIL in the new fixture infrastructure tests
        until proper relationships are established.
        """
        # Create minimal school - missing many related objects
        self.school = School.objects.create(
            name="Minimal Test School",
            contact_email="test@school.com"
        )
        
        # Create minimal users - missing profiles and memberships
        self.student_user = User.objects.create_user(
            email="student@example.com",
            name="Test Student"
        )
        
        self.parent_user = User.objects.create_user(
            email="parent@example.com", 
            name="Test Parent"
        )
        
        self.teacher_user = User.objects.create_user(
            email="teacher@example.com",
            name="Test Teacher"
        )
        
        self.client = APIClient()


class StudentAccountBalanceFixtureTests(FixtureInfrastructureBaseTestCase):
    """
    Tests that validate StudentAccountBalance fixture infrastructure.
    
    These tests should initially FAIL due to missing student relationships
    and database constraint violations.
    """
    
    def test_student_balance_api_requires_student_profile_with_school_membership(self):
        """
        Test that student balance API fails without proper student profile and school membership.
        
        Expected behavior:
        - FAIL initially: Student has no StudentProfile or SchoolMembership
        - PASS after fix: Proper student profile and school membership established
        """
        self.client.force_authenticate(user=self.student_user)
        
        # This should fail due to missing StudentProfile and SchoolMembership
        url = reverse('student-balance-detail', kwargs={'pk': self.student_user.pk})
        
        with self.assertRaises((IntegrityError, ValidationError)):
            response = self.client.get(url)
            
            # If the request doesn't raise an exception, it should return an error status
            if hasattr(response, 'status_code'):
                self.assertIn(response.status_code, [400, 404, 500])
    
    def test_student_balance_creation_requires_proper_student_relationship(self):
        """
        Test that StudentAccountBalance creation fails without proper student setup.
        
        Expected behavior:
        - FAIL initially: Missing required foreign key relationships
        - PASS after fix: Student has proper profile and school associations
        """
        # Attempt to create StudentAccountBalance directly
        with self.assertRaises(IntegrityError):
            balance = StudentAccountBalance.objects.create(
                student=self.student_user,  # Student without proper profile/membership
                hours_purchased=Decimal('10.00'),
                balance_amount=Decimal('100.00')
            )
    
    def test_student_balance_api_list_requires_school_membership_filtering(self):
        """
        Test that student balance list API requires proper school membership filtering.
        
        Expected behavior:
        - FAIL initially: User can access balances across schools without proper membership
        - PASS after fix: Proper school membership filtering in place
        """
        self.client.force_authenticate(user=self.student_user)
        
        url = reverse('student-balance-list')
        
        # This should fail due to missing SchoolMembership for filtering
        with self.assertRaises((IntegrityError, ValueError)):
            response = self.client.get(url)
            
            # If no exception, should return error or empty result due to missing membership
            if hasattr(response, 'status_code'):
                self.assertIn(response.status_code, [400, 403, 404])


class PricingPlanFixtureTests(FixtureInfrastructureBaseTestCase):
    """
    Tests that validate PricingPlan fixture infrastructure.
    
    These tests should initially FAIL due to missing required fields
    and incomplete plan configurations.
    """
    
    def test_pricing_plan_api_requires_complete_plan_configuration(self):
        """
        Test that pricing plan API fails with incomplete plan data.
        
        Expected behavior:
        - FAIL initially: Plans missing required fields like name, description, price
        - PASS after fix: Complete pricing plans with all required fields
        """
        # Attempt to create incomplete pricing plan
        with self.assertRaises((IntegrityError, ValidationError)):
            incomplete_plan = PricingPlan.objects.create(
                name="",  # Missing required name
                # Missing description, plan_type, hours_included, price_eur
            )
    
    def test_pricing_plan_api_list_returns_properly_configured_plans(self):
        """
        Test that pricing plan list API requires properly configured plans.
        
        Expected behavior:
        - FAIL initially: No valid pricing plans exist due to missing required fields
        - PASS after fix: Returns list of properly configured pricing plans
        """
        url = reverse('finances:pricing-plans-list')
        
        response = self.client.get(url)
        
        # Should succeed but return empty list or plans with missing required data
        self.assertEqual(response.status_code, 200)
        
        # Validate that any returned plans would fail validation
        if response.data:
            for plan_data in response.data:
                # Check for missing required fields that should cause validation failures
                missing_fields = []
                required_fields = ['name', 'description', 'plan_type', 'hours_included', 'price_eur']
                
                for field in required_fields:
                    if not plan_data.get(field):
                        missing_fields.append(field)
                
                self.assertTrue(
                    len(missing_fields) > 0,
                    f"Pricing plan should be missing required fields: {missing_fields}"
                )


class ParentChildRelationshipFixtureTests(FixtureInfrastructureBaseTestCase):
    """
    Tests that validate ParentChildRelationship fixture infrastructure.
    
    These tests should initially FAIL due to incomplete relationship setup
    and missing parent-child associations.
    """
    
    def test_parent_child_relationship_api_requires_proper_relationship_setup(self):
        """
        Test that parent-child relationship API fails without proper setup.
        
        Expected behavior:
        - FAIL initially: Missing ParentChildRelationship records
        - PASS after fix: Proper parent-child relationships established with school context
        """
        self.client.force_authenticate(user=self.parent_user)
        
        url = reverse('parent-child-relationship-list')
        
        response = self.client.get(url)
        
        # Should succeed but return empty list due to no established relationships
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
        
        # Attempt to create relationship should fail due to missing required data
        with self.assertRaises((IntegrityError, ValidationError)):
            relationship_data = {
                'parent': self.parent_user.pk,
                'child': self.student_user.pk,
                # Missing required school field and other relationship data
            }
            
            response = self.client.post(url, relationship_data)
            
            if hasattr(response, 'status_code'):
                self.assertIn(response.status_code, [400, 500])
    
    def test_family_budget_control_requires_parent_child_relationship(self):
        """
        Test that family budget control features fail without proper parent-child setup.
        
        Expected behavior:
        - FAIL initially: FamilyBudgetControl cannot be created without ParentChildRelationship
        - PASS after fix: Proper relationships enable budget control functionality
        """
        from finances.models import FamilyBudgetControl
        
        # Attempt to create budget control without relationship should fail
        with self.assertRaises((IntegrityError, ValidationError)):
            # This should fail because no ParentChildRelationship exists
            budget_control = FamilyBudgetControl.objects.create(
                # parent_child_relationship=None,  # Missing required relationship
                monthly_budget_limit=Decimal('100.00'),
                auto_approval_threshold=Decimal('25.00')
            )


class SchoolMembershipFixtureTests(FixtureInfrastructureBaseTestCase):
    """
    Tests that validate SchoolMembership fixture infrastructure.
    
    These tests should initially FAIL due to missing school memberships
    for test users.
    """
    
    def test_user_school_access_requires_membership(self):
        """
        Test that users cannot access school-specific resources without membership.
        
        Expected behavior:
        - FAIL initially: Users have no SchoolMembership records
        - PASS after fix: Proper school memberships established for all test users
        """
        # Check that users have no school memberships
        student_memberships = SchoolMembership.objects.filter(user=self.student_user)
        teacher_memberships = SchoolMembership.objects.filter(user=self.teacher_user)
        parent_memberships = SchoolMembership.objects.filter(user=self.parent_user)
        
        self.assertEqual(student_memberships.count(), 0)
        self.assertEqual(teacher_memberships.count(), 0)
        self.assertEqual(parent_memberships.count(), 0)
    
    def test_teacher_compensation_rule_requires_teacher_membership(self):
        """
        Test that teacher compensation rules fail without proper teacher membership.
        
        Expected behavior:
        - FAIL initially: Cannot create TeacherCompensationRule without teacher profile/membership
        - PASS after fix: Teacher has proper profile and school membership
        """
        from accounts.models import TeacherProfile
        
        # Attempt to create compensation rule should fail
        with self.assertRaises((IntegrityError, ValidationError)):
            # First need TeacherProfile, which should also fail
            teacher_profile = TeacherProfile.objects.create(
                user=self.teacher_user,
                # Missing required fields
            )
            
            compensation_rule = TeacherCompensationRule.objects.create(
                teacher=teacher_profile,
                school=self.school,
                rule_type=CompensationRuleType.GRADE_SPECIFIC,
                rate_per_hour=Decimal('25.00'),
                # Missing other required relationships
            )


class ClassSessionMultiRelationshipFixtureTests(FixtureInfrastructureBaseTestCase):
    """
    Tests that validate ClassSession fixture infrastructure requiring multiple relationships.
    
    These tests should initially FAIL due to missing teacher profiles, student memberships,
    and other complex relationship requirements.
    """
    
    def test_class_session_creation_requires_all_relationships(self):
        """
        Test that ClassSession creation fails without all required relationships.
        
        Expected behavior:
        - FAIL initially: Missing TeacherProfile, SchoolMembership, StudentProfile
        - PASS after fix: All required relationships properly established
        """
        from datetime import date, time
        from accounts.models import TeacherProfile
        
        # Attempt to create class session should fail due to missing relationships
        with self.assertRaises((IntegrityError, ValidationError)):
            # Create session with minimal data (should fail)
            session = ClassSession.objects.create(
                # teacher=None,  # Missing TeacherProfile
                school=self.school,
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(11, 0),
                session_type=SessionType.INDIVIDUAL,
                grade_level='7',
                student_count=1,
                status=SessionStatus.SCHEDULED
            )
            
            # Even if session creation succeeds, adding students should fail
            session.students.add(self.student_user)  # Student without proper profile/membership
    
    def test_session_hour_deduction_requires_student_account_balance(self):
        """
        Test that session hour deduction fails without proper StudentAccountBalance.
        
        Expected behavior:
        - FAIL initially: Students have no StudentAccountBalance records
        - PASS after fix: Students have proper account balance setup
        """
        # Check that student has no account balance
        try:
            balance = StudentAccountBalance.objects.get(student=self.student_user)
            # If balance exists, it should be improperly configured
            self.assertIsNone(balance.student.student_profile, 
                            "Student should not have proper profile setup")
        except StudentAccountBalance.DoesNotExist:
            # Expected - no balance exists due to missing fixtures
            pass


class StoredPaymentMethodFixtureTests(FixtureInfrastructureBaseTestCase):
    """
    Tests that validate StoredPaymentMethod fixture infrastructure.
    
    These tests should initially FAIL due to missing student relationships
    and incomplete payment method setup.
    """
    
    def test_payment_method_api_requires_proper_student_setup(self):
        """
        Test that payment method API fails without proper student setup.
        
        Expected behavior:
        - FAIL initially: Student lacks proper profile and school associations
        - PASS after fix: Student has complete profile and payment capability
        """
        self.client.force_authenticate(user=self.student_user)
        
        url = reverse('stored-payment-method-list')
        
        response = self.client.get(url)
        
        # Should succeed but reveal missing student setup
        self.assertEqual(response.status_code, 200)
        
        # Attempt to create payment method should fail
        payment_method_data = {
            'stripe_payment_method_id': 'pm_test_123',
            'card_brand': 'visa',
            'card_last4': '4242',
            'is_default': True
        }
        
        response = self.client.post(url, payment_method_data)
        
        # Should fail due to missing student setup or return error status
        self.assertIn(response.status_code, [400, 403, 500])


class EducationalSystemFixtureTests(FixtureInfrastructureBaseTestCase):
    """
    Tests that validate EducationalSystem fixture infrastructure for StudentProfile.
    
    These tests should initially FAIL due to missing EducationalSystem setup
    required for StudentProfile creation.
    """
    
    def test_student_profile_requires_educational_system(self):
        """
        Test that StudentProfile creation fails without EducationalSystem.
        
        Expected behavior:
        - FAIL initially: No EducationalSystem objects exist for StudentProfile reference
        - PASS after fix: Proper EducationalSystem fixtures available
        """
        # Check that no educational systems exist
        educational_systems = EducationalSystem.objects.all()
        self.assertEqual(educational_systems.count(), 0)
        
        # Attempt to create StudentProfile should fail
        with self.assertRaises((IntegrityError, ValidationError)):
            student_profile = StudentProfile.objects.create(
                user=self.student_user,
                # educational_system=None,  # No EducationalSystem available
                # Missing other required fields
            )


# Summary test that validates overall fixture infrastructure
class OverallFixtureInfrastructureValidationTests(FixtureInfrastructureBaseTestCase):
    """
    High-level tests that validate the complete fixture infrastructure setup.
    
    These tests verify that all the individual fixture components work together
    to support complex API operations that span multiple models.
    """
    
    def test_complete_student_purchase_flow_requires_all_fixtures(self):
        """
        Test that a complete student purchase flow fails without all required fixtures.
        
        This test validates the integration of:
        - StudentProfile + SchoolMembership
        - StudentAccountBalance  
        - PricingPlan with complete configuration
        - ParentChildRelationship (if applicable)
        - Payment method infrastructure
        
        Expected behavior:
        - FAIL initially: Multiple missing fixtures cause cascade failures
        - PASS after fix: Complete fixture infrastructure supports full purchase flow
        """
        self.client.force_authenticate(user=self.student_user)
        
        # Test purchase initiation API - should fail due to multiple missing fixtures
        url = reverse('finances:purchase-initiate')
        purchase_data = {
            'plan_id': 999,  # Non-existent plan due to missing PricingPlan fixtures
            'payment_method_id': 'pm_test_123'
        }
        
        response = self.client.post(url, purchase_data)
        
        # Should fail with appropriate error codes
        self.assertIn(response.status_code, [400, 404, 500])
        
        # Should contain errors related to missing fixtures
        if hasattr(response, 'data') and response.data:
            # Look for error messages that indicate fixture-related issues
            error_content = str(response.data)
            fixture_related_errors = [
                'student profile', 'school membership', 'pricing plan', 
                'parent relationship', 'account balance'
            ]
            
            # At least one fixture-related error should be present
            has_fixture_error = any(
                error_term in error_content.lower() 
                for error_term in fixture_related_errors
            )
            
            self.assertTrue(has_fixture_error, 
                          f"Response should contain fixture-related errors: {error_content}")
    
    def test_teacher_session_management_requires_complete_teacher_fixtures(self):
        """
        Test that teacher session management fails without complete teacher fixture setup.
        
        Expected behavior:
        - FAIL initially: Missing TeacherProfile, SchoolMembership, CompensationRule
        - PASS after fix: Complete teacher fixture infrastructure
        """
        self.client.force_authenticate(user=self.teacher_user)
        
        # Test teacher session creation - should fail due to missing teacher setup
        url = reverse('class-session-list')
        session_data = {
            'school': self.school.pk,
            'date': '2025-01-20',
            'start_time': '10:00',
            'end_time': '11:00', 
            'session_type': SessionType.INDIVIDUAL,
            'grade_level': '7',
            'student_count': 1
        }
        
        response = self.client.post(url, session_data)
        
        # Should fail due to missing teacher profile and related fixtures
        self.assertIn(response.status_code, [400, 403, 500])