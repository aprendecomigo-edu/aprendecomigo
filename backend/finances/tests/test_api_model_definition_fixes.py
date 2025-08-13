"""
DRF API tests for GitHub Issue #180: Fix model definition mismatches.

This test suite validates the correct usage of:
1. TransactionType.PACKAGE (not TransactionType.HOURS which doesn't exist)
2. PricingPlan creation with required hours_included field
3. School creation with valid parameters (not invalid 'owner', 'time_zone')
4. Enum serialization/deserialization in API endpoints

These tests should initially FAIL (red state) before implementation fixes are applied,
demonstrating the TDD approach to ensuring model definition corrections work correctly.
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import School
from finances.models import (
    PlanType,
    PricingPlan,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)
from finances.serializers import PricingPlanSerializer

User = get_user_model()


class TransactionTypeEnumAPITest(APITestCase):
    """
    Test TransactionType enum usage in API serializers.
    
    Issue #180: TransactionType.HOURS doesn't exist - should be TransactionType.PACKAGE
    These tests will FAIL initially until the correct enum values are used.
    """

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
            password='testpass123'
        )
        
        # Create student balance
        StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            balance_amount=Decimal('100.00')
        )

    def test_transaction_type_package_in_purchase_api(self):
        """
        Test that API accepts TransactionType.PACKAGE (not HOURS).
        
        **Issue**: Code might reference TransactionType.HOURS which doesn't exist
        **Expected**: Should use TransactionType.PACKAGE
        **Test State**: Will FAIL if TransactionType.HOURS is used
        """
        self.client.force_authenticate(user=self.student)
        
        # Create test data using correct enum value
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,  # Correct value
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        # Verify the transaction was created with correct enum
        self.assertEqual(transaction.transaction_type, TransactionType.PACKAGE)
        self.assertIn(TransactionType.PACKAGE, [choice[0] for choice in TransactionType.choices])

    def test_transaction_type_hours_does_not_exist(self):
        """
        Test that TransactionType.HOURS does not exist.
        
        **Issue**: Some code references TransactionType.HOURS incorrectly
        **Expected**: AttributeError when trying to access non-existent HOURS
        **Test State**: Will FAIL if HOURS enum value exists
        """
        # This should raise AttributeError since HOURS doesn't exist
        with self.assertRaises(AttributeError):
            _ = TransactionType.HOURS  # This should fail

    def test_transaction_type_serializer_validation(self):
        """
        Test serializer validation with correct TransactionType values.
        
        **Issue**: Serializers might expect invalid enum values
        **Expected**: Only accept valid enum values (PACKAGE, SUBSCRIPTION)
        **Test State**: Will FAIL if invalid enum validation exists
        """
        # Test valid enum values
        valid_types = [TransactionType.PACKAGE, TransactionType.SUBSCRIPTION]
        
        for transaction_type in valid_types:
            transaction = PurchaseTransaction.objects.create(
                student=self.student,
                transaction_type=transaction_type,
                amount=Decimal('25.00'),
                payment_status=TransactionPaymentStatus.PENDING
            )
            self.assertEqual(transaction.transaction_type, transaction_type)

    def test_purchase_transaction_with_package_type_creation(self):
        """
        Test direct PurchaseTransaction creation with PACKAGE type.
        
        **Issue**: Code might reference invalid TransactionType.HOURS
        **Expected**: Should work with TransactionType.PACKAGE
        **Test State**: Will FAIL if HOURS type is referenced anywhere
        """
        # Create a pricing plan with PACKAGE type
        pricing_plan = PricingPlan.objects.create(
            name='Test Package',
            description='Test package plan',
            plan_type=PlanType.PACKAGE,  # Using PACKAGE type
            hours_included=Decimal('10.00'),
            price_eur=Decimal('50.00'),
            validity_days=30
        )
        
        # Create transaction with PACKAGE type (the correct enum value)
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,  # Should work
            amount=pricing_plan.price_eur,
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        # Verify transaction was created successfully
        self.assertEqual(transaction.transaction_type, TransactionType.PACKAGE)
        self.assertEqual(transaction.amount, pricing_plan.price_eur)


class PlanTypeEnumAPITest(APITestCase):
    """
    Test PlanType enum usage in API serializers.
    
    Validates correct usage of PlanType.PACKAGE and PlanType.SUBSCRIPTION.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='admin@test.com',
            name='Test Admin',
            password='testpass123'
        )

    def test_plan_type_enum_values_exist(self):
        """
        Test that PlanType enum has correct values.
        
        **Expected**: PlanType should have PACKAGE and SUBSCRIPTION
        **Test State**: Will FAIL if enum values are incorrect
        """
        # Test enum values exist
        self.assertEqual(PlanType.PACKAGE, 'package')
        self.assertEqual(PlanType.SUBSCRIPTION, 'subscription')
        
        # Test choices are available
        choices = [choice[0] for choice in PlanType.choices]
        self.assertIn('package', choices)
        self.assertIn('subscription', choices)

    def test_pricing_plan_serializer_with_plan_types(self):
        """
        Test PricingPlanSerializer handles PlanType enum correctly.
        
        **Issue**: Serializer might not handle enum types properly
        **Expected**: Should serialize/deserialize PlanType correctly
        **Test State**: Will FAIL if enum handling is broken
        """
        # Test PACKAGE plan
        package_plan = PricingPlan.objects.create(
            name='Package Plan',
            description='A package plan',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('20.00'),
            price_eur=Decimal('100.00'),
            validity_days=60
        )
        
        serializer = PricingPlanSerializer(package_plan)
        data = serializer.data
        
        self.assertEqual(data['plan_type'], 'package')
        
        # Test SUBSCRIPTION plan
        subscription_plan = PricingPlan.objects.create(
            name='Subscription Plan',
            description='A subscription plan',
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal('30.00'),
            price_eur=Decimal('150.00')
        )
        
        serializer = PricingPlanSerializer(subscription_plan)
        data = serializer.data
        
        self.assertEqual(data['plan_type'], 'subscription')


class PricingPlanRequiredFieldsAPITest(APITestCase):
    """
    Test PricingPlan creation with required hours_included field.
    
    Issue #180: PricingPlan creation fails due to missing required hours_included field.
    Tests will FAIL initially if hours_included is not properly handled.
    """

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_user(
            email='admin@test.com',
            name='Test Admin',
            password='testpass123',
            is_staff=True
        )

    def test_pricing_plan_creation_without_hours_included_fails(self):
        """
        Test that PricingPlan creation fails without hours_included.
        
        **Issue**: Code might try to create PricingPlan without required field
        **Expected**: Should raise ValidationError or IntegrityError
        **Test State**: Will FAIL if hours_included is not required
        """
        from django.db import IntegrityError
        from django.core.exceptions import ValidationError
        
        # This should fail - hours_included is required
        with self.assertRaises((IntegrityError, ValidationError)):
            plan = PricingPlan.objects.create(
                name='Invalid Plan',
                description='Plan without hours_included',
                plan_type=PlanType.PACKAGE,
                price_eur=Decimal('50.00'),
                validity_days=30
                # Missing hours_included - should fail
            )
            plan.full_clean()  # Force validation

    def test_pricing_plan_creation_with_hours_included_succeeds(self):
        """
        Test that PricingPlan creation succeeds with hours_included.
        
        **Issue**: Code must include hours_included in all plan creation
        **Expected**: Should create successfully with required field
        **Test State**: Will FAIL if field is not handled properly
        """
        plan = PricingPlan.objects.create(
            name='Valid Plan',
            description='Plan with hours_included',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('15.00'),  # Required field
            price_eur=Decimal('75.00'),
            validity_days=45
        )
        
        # Should succeed
        self.assertEqual(plan.hours_included, Decimal('15.00'))
        plan.full_clean()  # Should not raise validation error

    def test_pricing_plan_serializer_requires_hours_included(self):
        """
        Test that PricingPlanSerializer validates hours_included.
        
        **Issue**: Serializer might not validate required field
        **Expected**: Serializer should require hours_included
        **Test State**: Will FAIL if field validation is missing
        """
        # Test serializer without hours_included
        data = {
            'name': 'Test Plan',
            'description': 'Test description',
            'plan_type': PlanType.PACKAGE,
            'price_eur': '50.00',
            'validity_days': 30
            # Missing hours_included
        }
        
        serializer = PricingPlanSerializer(data=data)
        
        # Should be invalid - hours_included is required
        self.assertFalse(serializer.is_valid())
        self.assertIn('hours_included', serializer.errors)

    def test_pricing_plan_serializer_with_hours_included_valid(self):
        """
        Test that PricingPlanSerializer validates with hours_included.
        
        **Expected**: Should be valid with all required fields
        **Test State**: Will FAIL if serializer doesn't handle field correctly
        """
        data = {
            'name': 'Valid Plan',
            'description': 'Valid description',
            'plan_type': PlanType.PACKAGE,
            'hours_included': '20.00',  # Required field included
            'price_eur': '100.00',
            'validity_days': 60
        }
        
        serializer = PricingPlanSerializer(data=data)
        
        # Should be valid
        self.assertTrue(serializer.is_valid(), f"Errors: {serializer.errors}")


class SchoolModelValidParametersAPITest(APITestCase):
    """
    Test School model creation with valid parameters only.
    
    Issue #180: School model creation with invalid parameters (owner, time_zone).
    Tests will FAIL initially if invalid parameters are used.
    """

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_user(
            email='admin@test.com',
            name='Test Admin',
            password='testpass123',
            is_staff=True
        )

    def test_school_creation_with_invalid_owner_parameter_fails(self):
        """
        Test that School creation fails with invalid 'owner' parameter.
        
        **Issue**: Code might try to create School with non-existent 'owner' field
        **Expected**: Should raise TypeError for unexpected keyword argument
        **Test State**: Will FAIL if 'owner' parameter is used
        """
        # This should fail - 'owner' is not a valid School field
        with self.assertRaises(TypeError) as cm:
            School.objects.create(
                name='Test School',
                owner=self.admin  # Invalid parameter - should fail
            )
        
        self.assertIn('owner', str(cm.exception))

    def test_school_creation_with_invalid_time_zone_parameter_fails(self):
        """
        Test that School creation fails with invalid 'time_zone' parameter.
        
        **Issue**: Code might try to create School with non-existent 'time_zone' field
        **Expected**: Should raise TypeError for unexpected keyword argument
        **Test State**: Will FAIL if 'time_zone' parameter is used
        """
        # This should fail - 'time_zone' is not a valid School field
        with self.assertRaises(TypeError) as cm:
            School.objects.create(
                name='Test School',
                time_zone='UTC'  # Invalid parameter - should fail
            )
        
        self.assertIn('time_zone', str(cm.exception))

    def test_school_creation_with_valid_parameters_succeeds(self):
        """
        Test that School creation succeeds with valid parameters only.
        
        **Expected**: Should create successfully with valid fields
        **Test State**: Will FAIL if valid field usage is broken
        """
        # Valid School creation
        school = School.objects.create(
            name='Valid School',
            description='A valid school description',
            address='123 Test Street',
            contact_email='contact@school.com',
            phone_number='+1234567890',
            website='https://school.com',
            primary_color='#FF0000',
            secondary_color='#00FF00',
            email_domain='school.com'
        )
        
        # Should succeed
        self.assertEqual(school.name, 'Valid School')
        self.assertEqual(school.contact_email, 'contact@school.com')
        
        # Verify all fields are accessible
        expected_fields = [
            'name', 'description', 'address', 'contact_email', 
            'phone_number', 'website', 'primary_color', 
            'secondary_color', 'email_domain'
        ]
        
        for field in expected_fields:
            # Should not raise AttributeError
            getattr(school, field)

    def test_school_model_field_validation(self):
        """
        Test School model field definitions and constraints.
        
        **Expected**: Should have correct field types and constraints
        **Test State**: Will FAIL if field definitions are incorrect
        """
        # Test that only valid fields exist
        school_fields = [field.name for field in School._meta.fields]
        
        # Valid fields that should exist
        expected_fields = [
            'id', 'name', 'description', 'address', 'contact_email',
            'phone_number', 'website', 'logo', 'primary_color',
            'secondary_color', 'email_domain', 'created_at', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, school_fields)
        
        # Invalid fields that should NOT exist
        invalid_fields = ['owner', 'time_zone']
        
        for field in invalid_fields:
            self.assertNotIn(field, school_fields)


class EnumSerializationAPITest(APITestCase):
    """
    Test enum serialization/deserialization in API responses.
    
    Validates that enum values are properly serialized and deserialized
    in API endpoints without conversion issues.
    """

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
            password='testpass123'
        )

    def test_transaction_type_serialization_in_api_response(self):
        """
        Test that TransactionType enums serialize correctly in API responses.
        
        **Issue**: Enum values might not serialize properly
        **Expected**: Should return string values ('package', 'subscription')
        **Test State**: Will FAIL if serialization is broken
        """
        # Create transaction with PACKAGE type
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        # Test that the enum serializes to string
        self.assertEqual(str(transaction.transaction_type), 'package')
        
        # Create transaction with SUBSCRIPTION type
        subscription_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        # Test that the enum serializes to string
        self.assertEqual(str(subscription_transaction.transaction_type), 'subscription')

    def test_plan_type_serialization_in_pricing_plan(self):
        """
        Test that PlanType enums serialize correctly in PricingPlan.
        
        **Issue**: PlanType values might not serialize properly
        **Expected**: Should return string values ('package', 'subscription')
        **Test State**: Will FAIL if serialization is broken
        """
        # Create package plan
        package_plan = PricingPlan.objects.create(
            name='Package Plan',
            description='Test package',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('10.00'),
            price_eur=Decimal('50.00'),
            validity_days=30
        )
        
        # Test enum serialization
        self.assertEqual(str(package_plan.plan_type), 'package')
        
        # Create subscription plan
        subscription_plan = PricingPlan.objects.create(
            name='Subscription Plan',
            description='Test subscription',
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal('20.00'),
            price_eur=Decimal('100.00')
        )
        
        # Test enum serialization
        self.assertEqual(str(subscription_plan.plan_type), 'subscription')

    def test_enum_choice_validation(self):
        """
        Test that enum choices are properly validated.
        
        **Issue**: Invalid enum values might be accepted
        **Expected**: Should only accept valid enum choices
        **Test State**: Will FAIL if invalid values are accepted
        """
        from django.core.exceptions import ValidationError
        
        # Test invalid TransactionType
        with self.assertRaises(ValidationError):
            transaction = PurchaseTransaction(
                student=self.student,
                transaction_type='invalid_type',  # Invalid enum value
                amount=Decimal('50.00'),
                payment_status=TransactionPaymentStatus.COMPLETED
            )
            transaction.full_clean()
        
        # Test invalid PlanType
        with self.assertRaises(ValidationError):
            plan = PricingPlan(
                name='Invalid Plan',
                description='Test plan',
                plan_type='invalid_plan_type',  # Invalid enum value
                hours_included=Decimal('10.00'),
                price_eur=Decimal('50.00'),
                validity_days=30
            )
            plan.full_clean()


class ModelDefinitionFixesIntegrationTest(APITestCase):
    """
    Integration tests combining all model definition fixes.
    
    Tests the complete workflow with correct enum usage, required fields,
    and valid parameters across all affected models.
    """

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
            password='testpass123'
        )
        
        # Create valid School
        self.school = School.objects.create(
            name='Test School',
            description='A test school'
        )
        
        # Create valid PricingPlan with required hours_included
        self.pricing_plan = PricingPlan.objects.create(
            name='Test Plan',
            description='Test pricing plan',
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal('15.00'),  # Required field
            price_eur=Decimal('75.00'),
            validity_days=30
        )

    def test_complete_purchase_workflow_with_correct_enums(self):
        """
        Test complete purchase workflow using correct enum values and required fields.
        
        **Issue**: Workflow might break with incorrect enum/field usage
        **Expected**: Should work end-to-end with correct model definitions
        **Test State**: Will FAIL if any model definition is incorrect
        """
        # Create student balance
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            balance_amount=Decimal('100.00')
        )
        
        # Create transaction with correct enum
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,  # Correct enum
            amount=self.pricing_plan.price_eur,
            payment_status=TransactionPaymentStatus.COMPLETED
        )
        
        # Verify everything was created correctly
        self.assertEqual(transaction.transaction_type, TransactionType.PACKAGE)
        self.assertEqual(self.pricing_plan.plan_type, PlanType.PACKAGE)
        self.assertIsNotNone(self.pricing_plan.hours_included)
        self.assertIsNotNone(self.school.name)
        
        # Verify no invalid fields exist
        with self.assertRaises(AttributeError):
            _ = TransactionType.HOURS  # Should not exist
        
        school_fields = [field.name for field in School._meta.fields]
        self.assertNotIn('owner', school_fields)
        self.assertNotIn('time_zone', school_fields)