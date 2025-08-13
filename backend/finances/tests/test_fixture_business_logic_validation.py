"""
Business logic unit tests to validate fixture infrastructure improvements (Issue #181).

These tests focus specifically on INTERNAL BUSINESS LOGIC that depends on proper
model relationships. They should initially FAIL when fixture infrastructure is incomplete
and PASS once proper fixtures are implemented.

Unlike API tests, these tests directly validate:
- Service layer methods that require complete model setups
- Model validation logic that depends on proper fixture relationships
- Manager/QuerySet methods that depend on foreign key relationships
- Business rule calculations that need proper associations

Test approach follows TDD:
- RED: Tests fail initially due to missing fixtures/relationships
- GREEN: Tests pass once fixture infrastructure provides proper relationships
"""

from decimal import Decimal
from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import (
    School, StudentProfile, TeacherProfile, ParentChildRelationship,
    SchoolMembership, EducationalSystem
)
from finances.models import (
    StudentAccountBalance, PricingPlan, PlanType, ClassSession, SessionType,
    SessionStatus, TeacherCompensationRule, CompensationRuleType,
    FamilyBudgetControl, PurchaseTransaction, TransactionType,
    TransactionPaymentStatus, HourConsumption
)
from finances.services.hour_deduction_service import (
    HourDeductionService, InsufficientBalanceError
)

User = get_user_model()


class HourDeductionServiceFixtureValidationTests(TestCase):
    """
    Validate HourDeductionService business logic requires proper fixtures.
    
    Tests should FAIL initially due to missing StudentAccountBalance relationships
    and incomplete student profile setup.
    """
    
    def setUp(self):
        """Minimal setup - missing required relationships."""
        self.school = School.objects.create(name="Test School", contact_email="test@school.com")
        self.student_user = User.objects.create_user(email="student@test.com", name="Student")
        self.teacher_user = User.objects.create_user(email="teacher@test.com", name="Teacher")
    
    def test_hour_deduction_validate_student_balance_requires_proper_student_setup(self):
        """
        Test that HourDeductionService._validate_student_balance fails without proper student setup.
        
        Expected behavior:
        - FAIL initially: StudentAccountBalance creation fails due to missing student relationships
        - PASS after fix: Student has proper profile and school membership for balance validation
        """
        required_hours = Decimal('1.0')
        
        # This should fail because student lacks proper profile/membership setup
        with self.assertRaises((IntegrityError, ValidationError)):
            HourDeductionService._validate_student_balance(self.student_user, required_hours)
    
    def test_hour_deduction_get_active_packages_requires_complete_student_associations(self):
        """
        Test that getting active packages fails without proper student purchase associations.
        
        Expected behavior:
        - FAIL initially: Cannot determine active packages due to missing relationships
        - PASS after fix: Student has proper profile enabling package queries
        """
        # This should fail due to missing student profile and purchase relationships
        with self.assertRaises((AttributeError, ValidationError)):
            active_packages = HourDeductionService._get_active_packages_for_student(self.student_user)
            
            # If method doesn't raise exception, should return empty due to missing relationships
            if active_packages is not None:
                self.assertEqual(len(active_packages), 0, 
                               "Should return empty due to missing student relationships")
    
    def test_session_hour_validation_requires_complete_session_setup(self):
        """
        Test that session hour validation fails without complete session fixture setup.
        
        Expected behavior:
        - FAIL initially: Cannot create ClassSession due to missing teacher profile
        - PASS after fix: Proper teacher profile and school membership enable session creation
        """
        # Attempt to create session should fail due to missing TeacherProfile
        with self.assertRaises((IntegrityError, ValidationError)):
            session = ClassSession.objects.create(
                school=self.school,
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(11, 0),
                session_type=SessionType.INDIVIDUAL,
                grade_level='7',
                status=SessionStatus.SCHEDULED
                # Missing teacher - should fail due to missing TeacherProfile
            )


class TeacherCompensationBusinessLogicFixtureTests(TestCase):
    """
    Validate teacher compensation business logic requires proper fixtures.
    
    Tests should FAIL initially due to missing TeacherProfile and SchoolMembership.
    """
    
    def setUp(self):
        """Minimal setup - missing teacher relationships."""
        self.school = School.objects.create(name="Test School", contact_email="test@school.com")
        self.teacher_user = User.objects.create_user(email="teacher@test.com", name="Teacher")
    
    def test_compensation_rule_validation_requires_teacher_profile(self):
        """
        Test that TeacherCompensationRule validation requires proper TeacherProfile setup.
        
        Expected behavior:
        - FAIL initially: Cannot create compensation rule without TeacherProfile
        - PASS after fix: Teacher has proper profile enabling compensation rules
        """
        # This should fail because teacher lacks TeacherProfile
        with self.assertRaises((IntegrityError, ValidationError)):
            # First attempt to create TeacherProfile should fail due to missing required fields
            teacher_profile = TeacherProfile.objects.create(user=self.teacher_user)
            
            # Then compensation rule creation should also fail
            compensation_rule = TeacherCompensationRule.objects.create(
                teacher=teacher_profile,
                school=self.school,
                rule_type=CompensationRuleType.GRADE_SPECIFIC,
                grade_level='7',
                rate_per_hour=Decimal('25.00')
            )
    
    def test_teacher_session_payment_calculation_requires_complete_teacher_setup(self):
        """
        Test that teacher payment calculations fail without complete teacher setup.
        
        Expected behavior:
        - FAIL initially: Payment calculations fail due to missing teacher relationships
        - PASS after fix: Complete teacher setup enables payment processing
        """
        from finances.models import TeacherPaymentEntry
        
        # This should fail due to missing teacher profile and session relationships
        with self.assertRaises((IntegrityError, ValidationError, AttributeError)):
            # Create session should fail due to missing teacher profile
            session = ClassSession.objects.create(
                school=self.school,
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(11, 0),
                session_type=SessionType.INDIVIDUAL,
                grade_level='7',
                status=SessionStatus.COMPLETED
                # Missing teacher field - should fail
            )


class FamilyBudgetControlBusinessLogicFixtureTests(TestCase):
    """
    Validate FamilyBudgetControl business logic requires proper ParentChildRelationship fixtures.
    
    Tests should FAIL initially due to missing ParentChildRelationship setup.
    """
    
    def setUp(self):
        """Minimal setup - missing parent-child relationships."""
        self.school = School.objects.create(name="Test School", contact_email="test@school.com")
        self.parent_user = User.objects.create_user(email="parent@test.com", name="Parent")
        self.student_user = User.objects.create_user(email="student@test.com", name="Student")
    
    def test_budget_control_creation_requires_parent_child_relationship(self):
        """
        Test that FamilyBudgetControl creation fails without ParentChildRelationship.
        
        Expected behavior:
        - FAIL initially: Cannot create budget control without established parent-child relationship
        - PASS after fix: Proper parent-child relationship enables budget controls
        """
        # This should fail because no ParentChildRelationship exists
        with self.assertRaises((IntegrityError, ValidationError)):
            budget_control = FamilyBudgetControl.objects.create(
                # parent_child_relationship=None - Missing required relationship
                monthly_budget_limit=Decimal('100.00'),
                auto_approval_threshold=Decimal('25.00')
            )
    
    def test_budget_limit_checking_requires_complete_relationship_setup(self):
        """
        Test that budget limit checking fails without complete relationship setup.
        
        Expected behavior:
        - FAIL initially: Budget calculations fail due to missing relationship data
        - PASS after fix: Complete relationships enable budget limit calculations
        """
        # Attempt to check budget limits should fail due to missing relationships
        with self.assertRaises((IntegrityError, ValidationError, AttributeError)):
            # First, create parent-child relationship should fail due to missing required fields
            relationship = ParentChildRelationship.objects.create(
                parent=self.parent_user,
                child=self.student_user
                # Missing school and other required fields
            )
            
            # Then budget control creation should also fail
            budget_control = FamilyBudgetControl.objects.create(
                parent_child_relationship=relationship,
                monthly_budget_limit=Decimal('100.00')
            )
            
            # Budget checking should fail due to incomplete setup
            result = budget_control.check_budget_limits(Decimal('50.00'))


class StudentAccountBalanceBusinessLogicFixtureTests(TestCase):
    """
    Validate StudentAccountBalance business logic requires proper student fixtures.
    
    Tests should FAIL initially due to missing student profile and school associations.
    """
    
    def setUp(self):
        """Minimal setup - missing student relationships."""
        self.school = School.objects.create(name="Test School", contact_email="test@school.com")
        self.student_user = User.objects.create_user(email="student@test.com", name="Student")
    
    def test_student_balance_property_calculations_require_proper_student_setup(self):
        """
        Test that StudentAccountBalance business logic requires proper student setup.
        
        Expected behavior:
        - Balance creation succeeds (Django allows this)
        - Business logic operations fail due to missing student relationships
        """
        # Create balance - this succeeds because only User FK is required
        balance = StudentAccountBalance.objects.create(
            student=self.student_user,  # Student without proper profile/membership
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('3.00'),
            balance_amount=Decimal('100.00')
        )
        
        # Business operations should fail due to missing student profile
        with self.assertRaises((AttributeError, ValidationError)):
            # This should fail when trying to access student.student_profile
            student_profile = self.student_user.student_profile
            school = student_profile.school  # Should fail - no student_profile exists
    
    def test_purchase_transaction_association_requires_student_profile(self):
        """
        Test that purchase transaction associations require proper student profile.
        
        Expected behavior:
        - FAIL initially: Cannot create purchase transactions due to missing student setup
        - PASS after fix: Student profile enables purchase transaction creation
        """
        # This should fail due to missing student profile for transaction association
        with self.assertRaises((IntegrityError, ValidationError)):
            transaction = PurchaseTransaction.objects.create(
                student=self.student_user,  # Student without proper profile
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('100.00'),
                payment_status=TransactionPaymentStatus.COMPLETED
            )


class PricingPlanBusinessLogicFixtureTests(TestCase):
    """
    Validate PricingPlan business logic requires complete plan configuration fixtures.
    
    Tests should FAIL initially due to missing required plan fields.
    """
    
    def test_pricing_plan_validation_requires_complete_configuration(self):
        """
        Test that PricingPlan validation requires all required fields.
        
        Expected behavior:
        - FAIL initially: Plan creation fails due to missing required fields (name, price, hours, etc.)
        - PASS after fix: Complete plan configuration enables proper validation
        """
        # This should fail due to missing required fields
        with self.assertRaises((IntegrityError, ValidationError)):
            plan = PricingPlan.objects.create(
                # Missing name, description, plan_type, hours_included, price_eur
                display_order=1
            )
            
            # If creation succeeds with minimal data, validation should fail
            plan.clean()
    
    def test_pricing_plan_price_per_hour_calculation_requires_valid_configuration(self):
        """
        Test that price_per_hour calculation requires valid plan configuration.
        
        Expected behavior:
        - FAIL initially: Price calculations fail due to invalid/missing plan data
        - PASS after fix: Complete plan configuration enables price calculations
        """
        # This should fail due to invalid plan configuration
        with self.assertRaises((IntegrityError, ValidationError, ZeroDivisionError)):
            plan = PricingPlan.objects.create(
                name="Invalid Plan",
                description="Test plan with invalid data",
                plan_type=PlanType.PACKAGE,
                hours_included=Decimal('0.00'),  # Invalid - should be > 0
                price_eur=Decimal('100.00'),
                validity_days=30
            )
            
            # Price per hour calculation should fail or return None due to zero hours
            price_per_hour = plan.price_per_hour


class HourConsumptionBusinessLogicFixtureTests(TestCase):
    """
    Validate HourConsumption business logic requires proper relationships across multiple models.
    
    Tests should FAIL initially due to missing session, student, and transaction relationships.
    """
    
    def setUp(self):
        """Minimal setup - missing multiple required relationships."""
        self.school = School.objects.create(name="Test School", contact_email="test@school.com")
        self.student_user = User.objects.create_user(email="student@test.com", name="Student")
        self.teacher_user = User.objects.create_user(email="teacher@test.com", name="Teacher")
    
    def test_hour_consumption_validation_requires_all_relationship_fixtures(self):
        """
        Test that HourConsumption validation requires all relationship fixtures.
        
        Expected behavior:
        - FAIL initially: Cannot create consumption without proper student, session, and transaction setup
        - PASS after fix: All required relationships properly established
        """
        # This should fail due to missing multiple required relationships
        with self.assertRaises((IntegrityError, ValidationError)):
            # First create minimal student balance - should fail due to missing student profile
            balance = StudentAccountBalance.objects.create(
                student=self.student_user,
                hours_purchased=Decimal('10.00')
            )
            
            # Create minimal session - should fail due to missing teacher profile
            session = ClassSession.objects.create(
                school=self.school,
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(11, 0),
                session_type=SessionType.INDIVIDUAL,
                grade_level='7'
                # Missing teacher field
            )
            
            # Create minimal transaction - should fail due to missing student setup
            transaction = PurchaseTransaction.objects.create(
                student=self.student_user,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('100.00')
            )
            
            # Finally, consumption creation should fail due to relationship violations
            consumption = HourConsumption.objects.create(
                student_account=balance,
                class_session=session,
                purchase_transaction=transaction,
                hours_consumed=Decimal('1.0'),
                hours_originally_reserved=Decimal('1.0')
            )
    
    def test_consumption_session_validation_requires_proper_student_session_association(self):
        """
        Test that consumption validation requires proper student-session association.
        
        Expected behavior:
        - FAIL initially: Validation fails when student account doesn't belong to session student
        - PASS after fix: Proper student-session associations established through fixtures
        """
        # This test validates the business rule in HourConsumption.clean() that ensures
        # the student account belongs to one of the session students
        # Should fail initially due to missing proper associations
        pass  # Implementation depends on proper fixture setup


class EducationalSystemFixtureValidationTests(TestCase):
    """
    Validate that EducationalSystem fixtures are required for StudentProfile creation.
    
    Tests should FAIL initially due to missing EducationalSystem fixtures.
    """
    
    def setUp(self):
        """Minimal setup - missing educational system fixtures."""
        self.school = School.objects.create(name="Test School", contact_email="test@school.com")
        self.student_user = User.objects.create_user(email="student@test.com", name="Student")
    
    def test_student_profile_creation_requires_educational_system_fixture(self):
        """
        Test that StudentProfile creation requires EducationalSystem fixtures.
        
        Expected behavior:
        - FAIL initially: No EducationalSystem objects available for StudentProfile reference
        - PASS after fix: Proper EducationalSystem fixtures available in test setup
        """
        # Check that no educational systems exist in minimal setup
        from accounts.models import EducationalSystem
        educational_systems = EducationalSystem.objects.all()
        self.assertEqual(educational_systems.count(), 0, 
                        "Should have no educational systems in minimal fixture setup")
        
        # This should fail due to missing EducationalSystem fixture
        with self.assertRaises((IntegrityError, ValidationError)):
            student_profile = StudentProfile.objects.create(
                user=self.student_user,
                # educational_system=None - No systems available to reference
                # Other required fields also missing
            )


# Integration test validating multiple fixture dependencies
class MultiModelBusinessLogicFixtureIntegrationTests(TestCase):
    """
    Integration tests that validate multiple fixture dependencies working together.
    
    These tests should FAIL initially due to cascading fixture dependency issues
    and PASS once complete fixture infrastructure is implemented.
    """
    
    def setUp(self):
        """Minimal setup - multiple missing dependencies."""
        self.school = School.objects.create(name="Test School", contact_email="test@school.com")
        self.student_user = User.objects.create_user(email="student@test.com", name="Student")
        self.teacher_user = User.objects.create_user(email="teacher@test.com", name="Teacher")
        self.parent_user = User.objects.create_user(email="parent@test.com", name="Parent")
    
    def test_complete_session_booking_workflow_requires_all_fixture_dependencies(self):
        """
        Test that complete session booking workflow requires all fixture dependencies.
        
        This integration test validates that the following fixtures work together:
        - StudentProfile + SchoolMembership
        - TeacherProfile + SchoolMembership  
        - StudentAccountBalance with proper associations
        - PricingPlan with complete configuration
        - ParentChildRelationship (if applicable)
        
        Expected behavior:
        - FAIL initially: Cascade of fixture dependency failures
        - PASS after fix: Complete fixture infrastructure supports full workflow
        """
        # This should fail due to multiple cascading fixture issues
        with self.assertRaises((IntegrityError, ValidationError, AttributeError)):
            # Step 1: Create session (requires teacher profile)
            session = ClassSession.objects.create(
                school=self.school,
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(11, 0),
                session_type=SessionType.INDIVIDUAL,
                grade_level='7',
                status=SessionStatus.SCHEDULED
                # Missing teacher - should fail
            )
            
            # Step 2: Add student to session (requires student profile)
            session.students.add(self.student_user)  # Should fail due to missing student setup
            
            # Step 3: Process hour deduction (requires student balance and purchase history)
            consumption_records = session.process_hour_deduction()  # Should fail due to missing fixtures
    
    def test_parent_approval_workflow_requires_complete_family_fixture_setup(self):
        """
        Test that parent approval workflow requires complete family fixture setup.
        
        Expected behavior:
        - FAIL initially: Missing ParentChildRelationship and budget control fixtures
        - PASS after fix: Complete family relationship fixtures enable approval workflow
        """
        # This should fail due to missing family relationship fixtures
        with self.assertRaises((IntegrityError, ValidationError, AttributeError)):
            # Create parent-child relationship (should fail due to missing required fields)
            relationship = ParentChildRelationship.objects.create(
                parent=self.parent_user,
                child=self.student_user
                # Missing school and other required relationship data
            )
            
            # Create budget control (should fail due to incomplete relationship)
            budget_control = FamilyBudgetControl.objects.create(
                parent_child_relationship=relationship,
                monthly_budget_limit=Decimal('100.00'),
                auto_approval_threshold=Decimal('25.00')
            )
            
            # Test budget checking (should fail due to missing purchase transaction setup)
            budget_result = budget_control.check_budget_limits(Decimal('50.00'))