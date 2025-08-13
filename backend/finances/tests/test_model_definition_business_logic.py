"""
Unit tests for GitHub Issue #180: Fix model definition mismatches - Business Logic Validation.

This test suite focuses on validating the business logic around model definition corrections:
1. TransactionType.PACKAGE (not TransactionType.HOURS which doesn't exist)
2. PricingPlan creation with required hours_included field
3. School model creation with valid parameters (not invalid 'owner', 'time_zone')
4. Model validation constraints and business rules

These are pure unit tests that test business logic, model validation, and internal
functionality - NOT API endpoints. They focus on ensuring models work correctly
for internal business operations.
"""

from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from accounts.models import School
from finances.models import (
    PlanType,
    PricingPlan,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
    ClassSession,
    SessionStatus,
    SessionType,
    HourConsumption,
    TeacherCompensationRule,
    CompensationRuleType,
    Receipt,
    StoredPaymentMethod,
    FamilyBudgetControl,
    PurchaseApprovalRequest,
    PurchaseRequestType,
    PurchaseApprovalStatus,
    WebhookEventLog,
    WebhookEventStatus,
)

User = get_user_model()


class TransactionTypeEnumBusinessLogicTest(TestCase):
    """
    Unit tests for TransactionType enum business logic validation.
    
    Issue #180: TransactionType.HOURS doesn't exist - should be TransactionType.PACKAGE
    These tests validate correct enum usage in business logic operations.
    """

    def setUp(self):
        """Set up test data for business logic tests."""
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
            password='testpass123'
        )
        
        # Create student account balance for business logic tests
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('2.00'),
            balance_amount=Decimal('80.00')
        )

    def test_transaction_type_enum_contains_package_not_hours(self):
        """
        Test that TransactionType enum contains PACKAGE but not HOURS.
        
        Business Logic: Ensures business operations use correct enum values.
        Expected: PACKAGE should exist, HOURS should not exist.
        """
        # Verify PACKAGE exists and has correct value
        self.assertTrue(hasattr(TransactionType, 'PACKAGE'))
        self.assertEqual(TransactionType.PACKAGE, 'package')
        
        # Verify HOURS does not exist
        self.assertFalse(hasattr(TransactionType, 'HOURS'))
        
        # Verify choices contain correct values
        valid_choices = [choice[0] for choice in TransactionType.choices]
        self.assertIn('package', valid_choices)
        self.assertIn('subscription', valid_choices)
        self.assertNotIn('hours', valid_choices)

    def test_transaction_type_package_business_logic_operations(self):
        """
        Test business logic operations using TransactionType.PACKAGE.
        
        Business Logic: Validates that PACKAGE type works in core business operations.
        """
        # Create transaction with PACKAGE type
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        # Verify business logic operations work
        self.assertEqual(transaction.transaction_type, TransactionType.PACKAGE)
        self.assertFalse(transaction.is_expired)  # Should not be expired without expires_at
        
        # Test business method functionality
        transaction.mark_completed()
        self.assertEqual(transaction.payment_status, TransactionPaymentStatus.COMPLETED)

    def test_transaction_type_subscription_business_logic_operations(self):
        """
        Test business logic operations using TransactionType.SUBSCRIPTION.
        
        Business Logic: Validates that SUBSCRIPTION type works in core business operations.
        """
        # Create transaction with SUBSCRIPTION type
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.PENDING
        )
        
        # Verify business logic operations work
        self.assertEqual(transaction.transaction_type, TransactionType.SUBSCRIPTION)
        self.assertFalse(transaction.is_expired)  # Subscriptions don't expire
        
        # Test validation logic for subscriptions
        transaction.clean()  # Should not raise validation error

    def test_transaction_type_invalid_value_validation(self):
        """
        Test that invalid TransactionType values are rejected by business logic.
        
        Business Logic: Ensures model validation prevents invalid enum values.
        """
        # Create transaction with invalid type
        transaction = PurchaseTransaction(
            student=self.student,
            transaction_type='invalid_type',  # Invalid enum value
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.PENDING
        )
        
        # Should fail validation
        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_transaction_type_business_rule_validation(self):
        """
        Test business rules specific to TransactionType values.
        
        Business Logic: Validates that business rules work correctly with enum values.
        """
        # Test SUBSCRIPTION business rule: should not have expires_at
        subscription_transaction = PurchaseTransaction(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('75.00'),
            payment_status=TransactionPaymentStatus.PENDING,
            expires_at='2025-12-31 23:59:59'  # Should cause validation error
        )
        
        # Should fail business rule validation
        with self.assertRaises(ValidationError) as cm:
            subscription_transaction.clean()
        
        self.assertIn('Subscription transactions should not have an expiration date', str(cm.exception))
        
        # Test PACKAGE business rule: can have expires_at
        package_transaction = PurchaseTransaction(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.PENDING,
            expires_at='2025-12-31 23:59:59'
        )
        
        # Should pass validation
        package_transaction.clean()  # Should not raise


class PricingPlanRequiredFieldsBusinessLogicTest(TestCase):
    """
    Unit tests for PricingPlan required hours_included field business logic.
    
    Issue #180: PricingPlan creation fails due to missing required hours_included field.
    Tests validate that business logic properly handles required field constraints.
    """

    def test_pricing_plan_hours_included_field_is_required(self):
        """
        Test that hours_included field is required for PricingPlan creation.
        
        Business Logic: Ensures core pricing model requires hours specification.
        """
        # Attempt to create PricingPlan without hours_included
        with self.assertRaises((IntegrityError, ValidationError)):
            plan = PricingPlan.objects.create(
                name='Invalid Plan',
                description='Plan without hours_included',
                plan_type=PlanType.PACKAGE,
                price_eur=Decimal('50.00'),
                validity_days=30
                # Missing hours_included - should fail
            )
            plan.full_clean()

    def test_pricing_plan_hours_included_business_logic_validation(self):
        """
        Test business logic validation rules for hours_included field.
        
        Business Logic: Ensures hours_included meets business requirements.
        """
        # Test with zero hours (should fail)
        with self.assertRaises(ValidationError):
            plan = PricingPlan(
                name='Zero Hours Plan',
                description='Invalid plan with zero hours',
                plan_type=PlanType.PACKAGE,
                hours_included=Decimal('0.00'),  # Invalid - must be > 0
                price_eur=Decimal('50.00'),
                validity_days=30
            )
            plan.full_clean()
        
        # Test with negative hours (should fail)
        with self.assertRaises(ValidationError):
            plan = PricingPlan(
                name='Negative Hours Plan',
                description='Invalid plan with negative hours',
                plan_type=PlanType.PACKAGE,
                hours_included=Decimal('-5.00'),  # Invalid - must be > 0
                price_eur=Decimal('50.00'),
                validity_days=30
            )
            plan.full_clean()

    def test_pricing_plan_hours_included_business_calculations(self):
        """
        Test business calculations that depend on hours_included field.
        
        Business Logic: Validates price-per-hour calculations and business metrics.
        """
        # Create valid plan with hours_included
        plan = PricingPlan.objects.create(
            name='Valid Plan',
            description='Plan with proper hours_included',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('20.00'),
            price_eur=Decimal('100.00'),
            validity_days=60
        )
        
        # Test business calculation methods
        price_per_hour = plan.price_per_hour
        self.assertEqual(price_per_hour, Decimal('5.00'))  # 100.00 / 20.00
        
        # Test string representation includes hours
        plan_str = str(plan)
        self.assertIn('20.00', plan_str)  # Hours should be in string representation

    def test_pricing_plan_package_vs_subscription_hours_logic(self):
        """
        Test hours_included business logic differences between PACKAGE and SUBSCRIPTION.
        
        Business Logic: Both plan types require hours_included for business operations.
        """
        # Test PACKAGE plan with hours_included
        package_plan = PricingPlan.objects.create(
            name='Package Plan',
            description='Package with hours',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('15.00'),
            price_eur=Decimal('75.00'),
            validity_days=30
        )
        
        # Test SUBSCRIPTION plan with hours_included
        subscription_plan = PricingPlan.objects.create(
            name='Subscription Plan',
            description='Subscription with hours',
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal('25.00'),
            price_eur=Decimal('150.00')
            # No validity_days for subscription
        )
        
        # Both should have valid hours_included
        self.assertEqual(package_plan.hours_included, Decimal('15.00'))
        self.assertEqual(subscription_plan.hours_included, Decimal('25.00'))
        
        # Both should calculate price_per_hour correctly
        self.assertEqual(package_plan.price_per_hour, Decimal('5.00'))
        self.assertEqual(subscription_plan.price_per_hour, Decimal('6.00'))

    def test_pricing_plan_business_rule_constraints(self):
        """
        Test PricingPlan business rule constraints with hours_included.
        
        Business Logic: Validates plan type specific business rules.
        """
        # Test PACKAGE plan business rules
        package_plan = PricingPlan(
            name='Package Plan',
            description='Package plan',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('10.00'),
            price_eur=Decimal('50.00')
            # Missing validity_days - should fail for PACKAGE
        )
        
        with self.assertRaises(ValidationError) as cm:
            package_plan.clean()
        
        self.assertIn('Package plans must have validity_days specified', str(cm.exception))
        
        # Test SUBSCRIPTION plan business rules
        subscription_plan = PricingPlan(
            name='Subscription Plan',
            description='Subscription plan',
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal('20.00'),
            price_eur=Decimal('100.00'),
            validity_days=30  # Should fail for SUBSCRIPTION
        )
        
        with self.assertRaises(ValidationError) as cm:
            subscription_plan.clean()
        
        self.assertIn('Subscription plans should not have validity_days', str(cm.exception))


class SchoolModelValidParametersBusinessLogicTest(TestCase):
    """
    Unit tests for School model parameter validation business logic.
    
    Issue #180: School model creation with invalid parameters (owner, time_zone).
    Tests validate that business logic rejects invalid parameters.
    """

    def setUp(self):
        """Set up test data for School model tests."""
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            name='Test Admin',
            password='testpass123'
        )

    def test_school_creation_rejects_invalid_owner_parameter(self):
        """
        Test that School model rejects invalid 'owner' parameter.
        
        Business Logic: Ensures model creation fails with non-existent fields.
        """
        # Should raise TypeError for invalid 'owner' parameter
        with self.assertRaises(TypeError) as cm:
            School.objects.create(
                name='Test School',
                owner=self.admin_user  # Invalid field - doesn't exist in School model
            )
        
        self.assertIn('owner', str(cm.exception))

    def test_school_creation_rejects_invalid_time_zone_parameter(self):
        """
        Test that School model rejects invalid 'time_zone' parameter.
        
        Business Logic: Ensures model creation fails with non-existent fields.
        """
        # Should raise TypeError for invalid 'time_zone' parameter
        with self.assertRaises(TypeError) as cm:
            School.objects.create(
                name='Test School',
                time_zone='UTC'  # Invalid field - doesn't exist in School model
            )
        
        self.assertIn('time_zone', str(cm.exception))

    def test_school_model_valid_field_business_operations(self):
        """
        Test School model business operations with valid fields only.
        
        Business Logic: Validates that all valid fields work in business operations.
        """
        # Create school with valid fields
        school = School.objects.create(
            name='Valid School',
            description='A valid school for testing',
            address='123 Test Street, Test City',
            contact_email='contact@school.com',
            phone_number='+1234567890',
            website='https://www.school.com',
            primary_color='#FF0000',
            secondary_color='#00FF00',
            email_domain='school.com'
        )
        
        # Test business operations
        self.assertEqual(school.name, 'Valid School')
        self.assertEqual(school.contact_email, 'contact@school.com')
        self.assertEqual(school.primary_color, '#FF0000')
        
        # Test string representation
        school_str = str(school)
        self.assertEqual(school_str, 'Valid School')

    def test_school_model_field_existence_validation(self):
        """
        Test that School model has expected fields and not invalid ones.
        
        Business Logic: Validates model schema matches business requirements.
        """
        # Get all field names from School model
        school_fields = [field.name for field in School._meta.fields]
        
        # Valid fields that should exist
        expected_fields = [
            'id', 'name', 'description', 'address', 'contact_email',
            'phone_number', 'website', 'logo', 'primary_color',
            'secondary_color', 'email_domain', 'created_at', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, school_fields, f"Expected field '{field}' not found in School model")
        
        # Invalid fields that should NOT exist
        invalid_fields = ['owner', 'time_zone']
        
        for field in invalid_fields:
            self.assertNotIn(field, school_fields, f"Invalid field '{field}' found in School model")

    def test_school_business_logic_constraints(self):
        """
        Test School model business logic constraints and validation.
        
        Business Logic: Validates that school creation follows business rules.
        """
        # Test minimal valid school creation
        minimal_school = School.objects.create(name='Minimal School')
        self.assertEqual(minimal_school.name, 'Minimal School')
        self.assertEqual(minimal_school.description, '')  # Default blank
        
        # Test school with all valid optional fields
        complete_school = School.objects.create(
            name='Complete School',
            description='Complete school with all fields',
            address='456 Complete Street',
            contact_email='complete@school.com',
            phone_number='+9876543210',
            website='https://complete.school.com',
            primary_color='#0000FF',
            secondary_color='#FFFF00',
            email_domain='complete.school.com'
        )
        
        # All fields should be accessible for business operations
        self.assertIsNotNone(complete_school.primary_color)
        self.assertIsNotNone(complete_school.secondary_color)
        self.assertIsNotNone(complete_school.email_domain)


class ModelFactoryValidationBusinessLogicTest(TestCase):
    """
    Unit tests for model factory and fixture validation business logic.
    
    Tests validate that test data creation uses correct model patterns
    and doesn't rely on non-existent fields or enum values.
    """

    def setUp(self):
        """Set up users for factory validation tests."""
        self.student = User.objects.create_user(
            email='student@factory.com',
            name='Factory Student',
            password='testpass123'
        )
        
        self.teacher_user = User.objects.create_user(
            email='teacher@factory.com',
            name='Factory Teacher',
            password='testpass123'
        )

    def test_purchase_transaction_factory_with_correct_enum(self):
        """
        Test PurchaseTransaction factory/creation with correct TransactionType enum.
        
        Business Logic: Ensures test data creation uses valid enum values.
        """
        # Test factory pattern with PACKAGE type
        package_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,  # Correct enum
            amount=Decimal('75.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        self.assertEqual(package_transaction.transaction_type, TransactionType.PACKAGE)
        
        # Test factory pattern with SUBSCRIPTION type
        subscription_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,  # Correct enum
            amount=Decimal('125.00'),
            payment_status=TransactionPaymentStatus.PENDING
        )
        
        self.assertEqual(subscription_transaction.transaction_type, TransactionType.SUBSCRIPTION)

    def test_pricing_plan_factory_with_required_hours_included(self):
        """
        Test PricingPlan factory/creation with required hours_included field.
        
        Business Logic: Ensures test data includes all required fields.
        """
        # Test complete PricingPlan factory
        plan = PricingPlan.objects.create(
            name='Factory Plan',
            description='Plan created by factory',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('30.00'),  # Required field
            price_eur=Decimal('150.00'),
            validity_days=90
        )
        
        self.assertEqual(plan.hours_included, Decimal('30.00'))
        self.assertIsNotNone(plan.price_per_hour)  # Business calculation should work

    def test_school_factory_with_valid_parameters_only(self):
        """
        Test School factory/creation with valid parameters only.
        
        Business Logic: Ensures test data creation doesn't use invalid parameters.
        """
        # Test School factory with valid fields
        school = School.objects.create(
            name='Factory School',
            description='School created by factory',
            contact_email='factory@school.com',
            primary_color='#FF6600',
            secondary_color='#0066FF'
        )
        
        self.assertEqual(school.name, 'Factory School')
        self.assertEqual(school.contact_email, 'factory@school.com')

    def test_complex_business_scenario_factory_validation(self):
        """
        Test complex business scenario with multiple model factories.
        
        Business Logic: Validates that related model creation works correctly.
        """
        # Create school with valid parameters
        school = School.objects.create(
            name='Business School',
            description='School for business scenario testing'
        )
        
        # Create pricing plan with required fields
        pricing_plan = PricingPlan.objects.create(
            name='Business Plan',
            description='Plan for business testing',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('25.00'),
            price_eur=Decimal('200.00'),
            validity_days=60
        )
        
        # Create purchase transaction with correct enum
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=pricing_plan.price_eur,
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        # Create student balance
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=pricing_plan.hours_included,
            balance_amount=pricing_plan.price_eur
        )
        
        # Verify business relationships work
        self.assertEqual(transaction.amount, pricing_plan.price_eur)
        self.assertEqual(balance.hours_purchased, pricing_plan.hours_included)


class ModelConstraintValidationBusinessLogicTest(TestCase):
    """
    Unit tests for model constraint validation business logic.
    
    Tests validate that model constraints work correctly with
    corrected model definitions and enum values.
    """

    def setUp(self):
        """Set up test data for constraint validation."""
        self.student = User.objects.create_user(
            email='constraint@test.com',
            name='Constraint Student',
            password='testpass123'
        )
        
        self.teacher_user = User.objects.create_user(
            email='teacher@constraint.com',
            name='Constraint Teacher',
            password='testpass123'
        )

    def test_transaction_type_enum_constraint_validation(self):
        """
        Test that TransactionType enum constraints work correctly.
        
        Business Logic: Validates enum field constraints prevent invalid values.
        """
        # Valid enum values should pass constraint validation
        valid_transaction = PurchaseTransaction(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.PENDING
        )
        
        # Should pass validation
        valid_transaction.full_clean()
        
        # Invalid enum value should fail constraint validation
        invalid_transaction = PurchaseTransaction(
            student=self.student,
            transaction_type='invalid_enum',  # Not in enum choices
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.PENDING
        )
        
        with self.assertRaises(ValidationError):
            invalid_transaction.full_clean()

    def test_pricing_plan_decimal_field_constraints(self):
        """
        Test PricingPlan decimal field constraints business logic.
        
        Business Logic: Validates decimal constraints for business calculations.
        """
        # Test hours_included decimal constraint
        plan = PricingPlan(
            name='Decimal Test Plan',
            description='Testing decimal constraints',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('15.50'),  # Valid decimal
            price_eur=Decimal('77.25'),       # Valid decimal
            validity_days=45
        )
        
        # Should pass validation
        plan.full_clean()
        
        # Test business calculation with decimal values
        price_per_hour = plan.price_per_hour
        expected_price_per_hour = Decimal('77.25') / Decimal('15.50')
        self.assertEqual(price_per_hour, expected_price_per_hour)

    def test_student_account_balance_constraint_validation(self):
        """
        Test StudentAccountBalance model constraints business logic.
        
        Business Logic: Validates balance constraints for business operations.
        """
        # Create valid balance
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('150.00')
        )
        
        # Test business logic property
        remaining_hours = balance.remaining_hours
        self.assertEqual(remaining_hours, Decimal('15.00'))  # 20.00 - 5.00

    def test_unique_constraint_validation_business_logic(self):
        """
        Test unique constraint validation in business logic scenarios.
        
        Business Logic: Validates that unique constraints prevent duplicate business data.
        """
        # Create first student balance
        balance1 = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            balance_amount=Decimal('100.00')
        )
        
        # Attempt to create duplicate balance for same student
        # Should fail due to OneToOneField constraint
        with self.assertRaises(IntegrityError):
            balance2 = StudentAccountBalance.objects.create(
                student=self.student,  # Same student - should fail
                hours_purchased=Decimal('20.00'),
                balance_amount=Decimal('200.00')
            )

    def test_foreign_key_constraint_business_logic(self):
        """
        Test foreign key constraints in business logic operations.
        
        Business Logic: Validates that foreign key relationships work correctly.
        """
        # Create related models with proper foreign key relationships
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('30.00'),
            balance_amount=Decimal('300.00')
        )
        
        transaction = PurchaseTransaction.objects.create(
            student=self.student,  # Same student as balance
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        # Verify foreign key relationships work for business operations
        self.assertEqual(balance.student, transaction.student)
        self.assertEqual(balance.student.email, 'constraint@test.com')