"""
Comprehensive serializer tests for the finances app.

These tests verify serializer validation, field exposure, data transformation,
PCI compliance, and business logic enforcement for all financial API serializers.
Critical areas covered:
- PCI compliance for payment methods
- Financial data validation and sanitization  
- Budget control and approval workflows
- Purchase transaction processing
- Receipt generation and management
- Cross-field validation logic
"""

import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import serializers as drf_serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from accounts.models import CustomUser, School, StudentProfile, TeacherProfile
from common.test_base import BaseAPITestCase, mock_external_services
from finances.models import (
    ClassSession, FamilyBudgetControl, PricingPlan, PurchaseApprovalRequest,
    PurchaseTransaction, Receipt, SchoolBillingSettings, StoredPaymentMethod,
    StudentAccountBalance, TeacherCompensationRule, TeacherPaymentEntry,
    TransactionPaymentStatus, TransactionType
)
from finances.serializers import (
    ClassSessionSerializer, FamilyBudgetControlSerializer, MonthlyPaymentSummarySerializer,
    PricingPlanSerializer, PurchaseApprovalActionSerializer, PurchaseApprovalRequestSerializer,
    PurchaseInitiationRequestSerializer, PurchaseInitiationResponseSerializer,
    QuickTopupRequestSerializer, ReceiptSerializer, StoredPaymentMethodSerializer,
    StudentInfoSerializer, StudentBalanceSummarySerializer, TeacherCompensationRuleSerializer
)

User = get_user_model()


class TestStudentInfoSerializer(BaseAPITestCase):
    """Test suite for StudentInfoSerializer - Issue #107: PCI compliance and data validation."""

    def test_valid_student_info_serialization(self):
        """Test serializing valid student information."""
        data = {
            'name': 'João Silva',
            'email': 'joao.silva@example.com'
        }
        serializer = StudentInfoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], 'João Silva')
        self.assertEqual(serializer.validated_data['email'], 'joao.silva@example.com')

    def test_student_name_validation_valid_names(self):
        """Test name validation accepts valid Portuguese names."""
        valid_names = [
            'João da Silva',
            'Maria José Santos',
            'Pedro O\'Neill',  # apostrophe
            'Ana-Lucia Costa',  # hyphen
            'José Antônio',     # accented characters
            'Dr. Carlos Silva', # dot
            'Santos Jr.',       # abbreviation
        ]
        
        for name in valid_names:
            with self.subTest(name=name):
                data = {'name': name, 'email': 'test@example.com'}
                serializer = StudentInfoSerializer(data=data)
                self.assertTrue(serializer.is_valid(), 
                               f"Should accept valid name: {name}. Errors: {serializer.errors}")

    def test_student_name_validation_invalid_names(self):
        """Test name validation rejects invalid names."""
        invalid_names = [
            '',                    # empty
            '   ',                 # whitespace only
            'João123Silva',        # numbers
            'Maria@Silva',         # @ symbol
            'Pedro#Silva',         # hash symbol
            '<script>alert()</script>', # XSS attempt
            'João\nSilva',         # newline
            'A' * 200,             # too long
        ]
        
        for name in invalid_names:
            with self.subTest(name=name):
                data = {'name': name, 'email': 'test@example.com'}
                serializer = StudentInfoSerializer(data=data)
                self.assertFalse(serializer.is_valid(),
                                f"Should reject invalid name: {name}")
                self.assertIn('name', serializer.errors)

    def test_student_name_sanitization(self):
        """Test name field sanitization and length limiting."""
        # Test whitespace trimming
        data = {'name': '  João Silva  ', 'email': 'test@example.com'}
        serializer = StudentInfoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], 'João Silva')
        
        # Test length limiting (150 chars)
        long_name = 'A' * 160
        data = {'name': long_name, 'email': 'test@example.com'}
        serializer = StudentInfoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data['name']), 150)

    def test_student_email_validation_valid_emails(self):
        """Test email validation accepts valid email formats."""
        valid_emails = [
            'simple@example.com',
            'user+tag@domain.org',
            'test.email@subdomain.example.co.uk',
            'numbers123@test456.com',
            'hyphen-test@example.com',
            'underscore_test@example.com',
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                data = {'name': 'Test User', 'email': email}
                serializer = StudentInfoSerializer(data=data)
                self.assertTrue(serializer.is_valid(),
                               f"Should accept valid email: {email}. Errors: {serializer.errors}")

    def test_student_email_validation_invalid_emails(self):
        """Test email validation rejects invalid email formats."""
        invalid_emails = [
            '',                        # empty
            'invalid-email',          # no @ symbol
            '@domain.com',            # missing user part
            'user@',                  # missing domain
            'user..double@domain.com', # double dots
            'user@domain',            # missing TLD
            'user name@domain.com',   # space in user part
            '<script>@domain.com',    # XSS attempt
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                data = {'name': 'Test User', 'email': email}
                serializer = StudentInfoSerializer(data=data)
                self.assertFalse(serializer.is_valid(),
                                f"Should reject invalid email: {email}")
                self.assertIn('email', serializer.errors)

    def test_student_email_normalization(self):
        """Test email normalization to lowercase."""
        data = {'name': 'Test User', 'email': '  TEST@EXAMPLE.COM  '}
        serializer = StudentInfoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['email'], 'test@example.com')

    def test_required_fields_validation(self):
        """Test that both name and email are required."""
        # Missing name
        data = {'email': 'test@example.com'}
        serializer = StudentInfoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        
        # Missing email
        data = {'name': 'Test User'}
        serializer = StudentInfoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        # Both missing
        serializer = StudentInfoSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        self.assertIn('email', serializer.errors)


class TestPricingPlanSerializer(BaseAPITestCase):
    """Test suite for PricingPlanSerializer."""

    def setUp(self):
        super().setUp()
        self.pricing_plan = PricingPlan.objects.create(
            name='Basic Plan',
            description='Basic tutoring plan',
            plan_type='hours',
            hours_included=Decimal('10.00'),
            price_eur=Decimal('50.00'),
            validity_days=30,
            display_order=1,
            is_featured=True,
            is_active=True
        )

    def test_pricing_plan_serialization(self):
        """Test serializing pricing plan data."""
        serializer = PricingPlanSerializer(self.pricing_plan)
        data = serializer.data
        
        # Verify all expected fields are present
        expected_fields = [
            'id', 'name', 'description', 'plan_type', 'plan_type_display',
            'hours_included', 'price_eur', 'validity_days', 'display_order',
            'is_featured', 'price_per_hour'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Verify field values
        self.assertEqual(data['name'], 'Basic Plan')
        self.assertEqual(data['plan_type'], 'hours')
        self.assertEqual(float(data['hours_included']), 10.00)
        self.assertEqual(float(data['price_eur']), 50.00)
        self.assertTrue(data['is_featured'])

    def test_price_per_hour_calculation(self):
        """Test price per hour calculation."""
        serializer = PricingPlanSerializer(self.pricing_plan)
        data = serializer.data
        
        # Should calculate 50.00 / 10.00 = 5.00
        self.assertEqual(data['price_per_hour'], '5.00')

    def test_price_per_hour_zero_hours(self):
        """Test price per hour calculation with zero hours."""
        plan = PricingPlan.objects.create(
            name='Unlimited Plan',
            plan_type='subscription',
            hours_included=Decimal('0.00'),
            price_eur=Decimal('100.00'),
            validity_days=30,
            is_active=True
        )
        
        serializer = PricingPlanSerializer(plan)
        data = serializer.data
        
        # Should return None for zero hours
        self.assertIsNone(data['price_per_hour'])

    def test_read_only_fields(self):
        """Test that read-only fields cannot be updated."""
        data = {
            'name': 'Updated Plan',
            'price_per_hour': '999.99',  # read-only field
            'plan_type_display': 'Custom Display'  # read-only field
        }
        
        serializer = PricingPlanSerializer(self.pricing_plan, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_plan = serializer.save()
        self.assertEqual(updated_plan.name, 'Updated Plan')
        # Read-only fields should not change
        self.assertEqual(updated_plan.price_per_hour, Decimal('5.00'))


class TestPurchaseInitiationRequestSerializer(BaseAPITestCase):
    """Test suite for PurchaseInitiationRequestSerializer - Critical for payment security."""

    def setUp(self):
        super().setUp()
        self.pricing_plan = PricingPlan.objects.create(
            name='Test Plan',
            plan_type='hours',
            hours_included=Decimal('5.00'),
            price_eur=Decimal('25.00'),
            validity_days=30,
            is_active=True
        )

    def test_valid_purchase_initiation_request(self):
        """Test valid purchase initiation request."""
        data = {
            'plan_id': self.pricing_plan.id,
            'student_info': {
                'name': 'Test Student',
                'email': 'student@example.com'
            }
        }
        
        serializer = PurchaseInitiationRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['plan_id'], self.pricing_plan.id)
        self.assertEqual(serializer.validated_data['student_info']['name'], 'Test Student')

    def test_plan_id_validation_nonexistent_plan(self):
        """Test validation fails for non-existent plan ID."""
        data = {
            'plan_id': 99999,  # Non-existent
            'student_info': {'name': 'Test', 'email': 'test@example.com'}
        }
        
        serializer = PurchaseInitiationRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('plan_id', serializer.errors)
        self.assertIn('not found', str(serializer.errors['plan_id'][0]))

    def test_plan_id_validation_inactive_plan(self):
        """Test validation fails for inactive plan."""
        inactive_plan = PricingPlan.objects.create(
            name='Inactive Plan',
            plan_type='hours',
            hours_included=Decimal('5.00'),
            price_eur=Decimal('25.00'),
            validity_days=30,
            is_active=False
        )
        
        data = {
            'plan_id': inactive_plan.id,
            'student_info': {'name': 'Test', 'email': 'test@example.com'}
        }
        
        serializer = PurchaseInitiationRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('plan_id', serializer.errors)
        self.assertIn('not currently active', str(serializer.errors['plan_id'][0]))

    def test_plan_id_validation_invalid_format(self):
        """Test validation fails for invalid plan ID format."""
        invalid_plan_ids = [0, -1, 'abc', None]
        
        for plan_id in invalid_plan_ids:
            with self.subTest(plan_id=plan_id):
                data = {
                    'plan_id': plan_id,
                    'student_info': {'name': 'Test', 'email': 'test@example.com'}
                }
                
                serializer = PurchaseInitiationRequestSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('plan_id', serializer.errors)

    def test_nested_student_info_validation(self):
        """Test nested student_info validation."""
        data = {
            'plan_id': self.pricing_plan.id,
            'student_info': {
                'name': '',  # Invalid
                'email': 'invalid-email'  # Invalid
            }
        }
        
        serializer = PurchaseInitiationRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('student_info', serializer.errors)

    def test_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        # Missing plan_id
        data = {'student_info': {'name': 'Test', 'email': 'test@example.com'}}
        serializer = PurchaseInitiationRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('plan_id', serializer.errors)
        
        # Missing student_info
        data = {'plan_id': self.pricing_plan.id}
        serializer = PurchaseInitiationRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('student_info', serializer.errors)


class TestStoredPaymentMethodSerializer(BaseAPITestCase):
    """Test suite for StoredPaymentMethodSerializer - Critical PCI compliance tests."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            name='Test User'
        )
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.user,
            stripe_payment_method_id='pm_test_12345',
            stripe_customer_id='cus_test_12345',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True
        )

    def test_pci_compliant_serialization(self):
        """Test serialization follows PCI compliance - no raw card data exposure."""
        serializer = StoredPaymentMethodSerializer(self.payment_method)
        data = serializer.data
        
        # Verify card data is not directly exposed
        self.assertNotIn('card_last4', data)
        self.assertNotIn('stripe_payment_method_id', data)
        
        # Verify secure fields are present
        self.assertIn('card_brand', data)
        self.assertIn('card_exp_month', data)
        self.assertIn('card_exp_year', data)
        self.assertIn('card_display', data)
        self.assertIn('is_expired', data)

    def test_card_display_format(self):
        """Test card_display field provides secure formatted display."""
        serializer = StoredPaymentMethodSerializer(self.payment_method)
        data = serializer.data
        
        card_display = data['card_display']
        self.assertIsInstance(card_display, str)
        # Should contain brand and last4 but in secure format
        self.assertIn('visa', card_display.lower())
        self.assertIn('4242', card_display)

    def test_expiration_validation(self):
        """Test is_expired field calculation."""
        # Current payment method should not be expired (expires 2025)
        serializer = StoredPaymentMethodSerializer(self.payment_method)
        data = serializer.data
        self.assertFalse(data['is_expired'])
        
        # Create expired payment method
        expired_method = StoredPaymentMethod.objects.create(
            student=self.user,
            stripe_payment_method_id='pm_test_expired',
            stripe_customer_id='cus_test_12345',
            card_brand='mastercard',
            card_last4='1234',
            card_exp_month=1,
            card_exp_year=2020,  # Expired
            is_active=True
        )
        
        serializer = StoredPaymentMethodSerializer(expired_method)
        data = serializer.data
        self.assertTrue(data['is_expired'])

    def test_read_only_fields_protection(self):
        """Test that sensitive fields are read-only."""
        read_only_fields = [
            'id', 'student_name', 'card_display', 'is_expired',
            'stripe_customer_id', 'created_at', 'updated_at'
        ]
        
        serializer = StoredPaymentMethodSerializer()
        meta_read_only = serializer.Meta.read_only_fields
        
        for field in read_only_fields:
            self.assertIn(field, meta_read_only,
                         f"Field '{field}' should be read-only for PCI compliance")

    def test_no_sensitive_data_in_representation(self):
        """Test to_representation doesn't expose sensitive PCI data."""
        serializer = StoredPaymentMethodSerializer(self.payment_method)
        representation = serializer.to_representation(self.payment_method)
        
        # Critical PCI fields that should NOT be in API responses
        sensitive_fields = ['card_last4', 'stripe_payment_method_id']
        for field in sensitive_fields:
            self.assertNotIn(field, representation,
                           f"Sensitive field '{field}' should not be in API response")

    def test_student_name_display(self):
        """Test student name is properly displayed."""
        serializer = StoredPaymentMethodSerializer(self.payment_method)
        data = serializer.data
        
        self.assertEqual(data['student_name'], 'Test User')


class TestTeacherCompensationRuleSerializer(BaseAPITestCase):
    """Test suite for TeacherCompensationRuleSerializer."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School')
        self.user = CustomUser.objects.create_user(
            email='teacher@example.com',
            name='Test Teacher'
        )
        self.teacher = TeacherProfile.objects.create(user=self.user)
        
        self.rule = TeacherCompensationRule.objects.create(
            teacher=self.teacher,
            school=self.school,
            rule_type='grade_specific',
            grade_level='5th',
            rate_per_hour=Decimal('25.00'),
            is_active=True
        )

    def test_teacher_compensation_rule_serialization(self):
        """Test serializing teacher compensation rule."""
        serializer = TeacherCompensationRuleSerializer(self.rule)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'teacher', 'teacher_name', 'teacher_email', 'school',
            'school_name', 'rule_type', 'rule_type_display', 'grade_level',
            'rate_per_hour', 'fixed_amount', 'conditions', 'is_active',
            'effective_from', 'effective_until'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['teacher_name'], 'Test Teacher')
        self.assertEqual(data['teacher_email'], 'teacher@example.com')
        self.assertEqual(data['school_name'], 'Test School')

    def test_grade_specific_rule_validation(self):
        """Test validation for grade-specific rules requires grade_level and rate_per_hour."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'rule_type': 'grade_specific',
            # Missing grade_level and rate_per_hour
        }
        
        serializer = TeacherCompensationRuleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('grade_level', serializer.errors)
        self.assertIn('rate_per_hour', serializer.errors)

    def test_group_class_rule_validation(self):
        """Test validation for group class rules requires rate_per_hour."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'rule_type': 'group_class',
            # Missing rate_per_hour
        }
        
        serializer = TeacherCompensationRuleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('rate_per_hour', serializer.errors)

    def test_fixed_salary_rule_validation(self):
        """Test validation for fixed salary rules requires fixed_amount."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'rule_type': 'fixed_salary',
            # Missing fixed_amount
        }
        
        serializer = TeacherCompensationRuleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('fixed_amount', serializer.errors)

    def test_valid_grade_specific_rule(self):
        """Test valid grade-specific rule creation."""
        data = {
            'teacher': self.teacher.id,
            'school': self.school.id,
            'rule_type': 'grade_specific',
            'grade_level': '6th',
            'rate_per_hour': '30.00',
            'is_active': True
        }
        
        serializer = TeacherCompensationRuleSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class TestFamilyBudgetControlSerializer(BaseAPITestCase):
    """Test suite for FamilyBudgetControlSerializer - Parent-child budget control."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School')
        self.parent = CustomUser.objects.create_user(
            email='parent@example.com',
            name='Test Parent'
        )
        self.child = CustomUser.objects.create_user(
            email='child@example.com',
            name='Test Child'
        )
        
        # Create parent-child relationship (assuming it exists in the system)
        from accounts.models import ParentChildRelationship
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            school=self.school,
            relationship_type='parent'
        )
        
        self.budget_control = FamilyBudgetControl.objects.create(
            parent_child_relationship=self.relationship,
            monthly_budget_limit=Decimal('200.00'),
            weekly_budget_limit=Decimal('50.00'),
            auto_approval_threshold=Decimal('20.00'),
            require_approval_for_sessions=True,
            require_approval_for_packages=False,
            is_active=True
        )

    def test_family_budget_control_serialization(self):
        """Test serializing family budget control data."""
        serializer = FamilyBudgetControlSerializer(self.budget_control)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'parent_child_relationship', 'parent_name', 'child_name',
            'school_name', 'monthly_budget_limit', 'weekly_budget_limit',
            'auto_approval_threshold', 'require_approval_for_sessions',
            'require_approval_for_packages', 'current_monthly_spending',
            'current_weekly_spending', 'is_active'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['parent_name'], 'Test Parent')
        self.assertEqual(data['child_name'], 'Test Child')
        self.assertEqual(data['school_name'], 'Test School')
        self.assertEqual(float(data['monthly_budget_limit']), 200.00)

    def test_budget_limits_check(self):
        """Test budget limits checking functionality."""
        serializer = FamilyBudgetControlSerializer(self.budget_control)
        
        # Test amount within auto-approval threshold
        result = serializer.check_budget_limits(Decimal('15.00'))
        self.assertTrue(result['allowed'])
        self.assertTrue(result['can_auto_approve'])
        
        # Test amount above auto-approval threshold but within budget
        result = serializer.check_budget_limits(Decimal('35.00'))
        self.assertTrue(result['allowed'])
        self.assertFalse(result['can_auto_approve'])

    def test_read_only_fields(self):
        """Test read-only fields are properly protected."""
        read_only_fields = [
            'id', 'parent_name', 'child_name', 'school_name',
            'current_monthly_spending', 'current_weekly_spending',
            'created_at', 'updated_at'
        ]
        
        serializer = FamilyBudgetControlSerializer()
        meta_read_only = serializer.Meta.read_only_fields
        
        for field in read_only_fields:
            self.assertIn(field, meta_read_only)


class TestPurchaseApprovalRequestSerializer(BaseAPITestCase):
    """Test suite for PurchaseApprovalRequestSerializer - Parent approval workflow."""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School')
        self.parent = CustomUser.objects.create_user(
            email='parent@example.com',
            name='Test Parent'
        )
        self.student = CustomUser.objects.create_user(
            email='student@example.com',
            name='Test Student'
        )
        self.pricing_plan = PricingPlan.objects.create(
            name='Test Plan',
            plan_type='hours',
            price_eur=Decimal('50.00'),
            is_active=True
        )
        
        from accounts.models import ParentChildRelationship
        self.relationship = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.student,
            school=self.school,
            relationship_type='parent'
        )
        
        self.approval_request = PurchaseApprovalRequest.objects.create(
            student=self.student,
            parent=self.parent,
            parent_child_relationship=self.relationship,
            amount=Decimal('50.00'),
            description='5 hours tutoring package',
            request_type='hours',
            pricing_plan=self.pricing_plan,
            status='pending'
        )

    def test_purchase_approval_request_serialization(self):
        """Test serializing purchase approval request."""
        serializer = PurchaseApprovalRequestSerializer(self.approval_request)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'student', 'student_name', 'parent', 'parent_name',
            'parent_child_relationship', 'amount', 'description', 'request_type',
            'status', 'pricing_plan', 'pricing_plan_name', 'class_session',
            'class_session_info', 'time_remaining_hours', 'is_expired',
            'parent_notes'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['student_name'], 'Test Student')
        self.assertEqual(data['parent_name'], 'Test Parent')
        self.assertEqual(data['pricing_plan_name'], 'Test Plan')

    def test_validation_prevents_same_user_parent_student(self):
        """Test validation prevents student and parent being the same user."""
        data = {
            'student': self.parent.id,  # Same as parent
            'parent': self.parent.id,
            'parent_child_relationship': self.relationship.id,
            'amount': '50.00',
            'description': 'Test purchase',
            'request_type': 'hours'
        }
        
        serializer = PurchaseApprovalRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Student and parent cannot be the same user', str(serializer.errors))

    def test_validation_parent_child_relationship_match(self):
        """Test validation ensures parent matches relationship."""
        # Create different parent
        other_parent = CustomUser.objects.create_user(
            email='other@example.com',
            name='Other Parent'
        )
        
        data = {
            'student': self.student.id,
            'parent': other_parent.id,  # Doesn't match relationship
            'parent_child_relationship': self.relationship.id,
            'amount': '50.00',
            'description': 'Test purchase',
            'request_type': 'hours'
        }
        
        serializer = PurchaseApprovalRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Parent must match the parent-child relationship', str(serializer.errors))

    def test_time_remaining_calculation(self):
        """Test time remaining hours calculation."""
        serializer = PurchaseApprovalRequestSerializer(self.approval_request)
        data = serializer.data
        
        # Should calculate time remaining based on expires_at
        if not self.approval_request.is_expired:
            self.assertIsInstance(data['time_remaining_hours'], float)
            self.assertGreaterEqual(data['time_remaining_hours'], 0)
        else:
            self.assertEqual(data['time_remaining_hours'], 0)


class TestPurchaseApprovalActionSerializer(BaseAPITestCase):
    """Test suite for PurchaseApprovalActionSerializer - Parent approval actions."""

    def test_valid_approval_actions(self):
        """Test valid approval actions."""
        valid_actions = ['approve', 'deny']
        
        for action in valid_actions:
            with self.subTest(action=action):
                data = {
                    'action': action,
                    'parent_notes': 'Test notes'
                }
                serializer = PurchaseApprovalActionSerializer(data=data)
                self.assertTrue(serializer.is_valid())

    def test_invalid_approval_action(self):
        """Test invalid approval actions are rejected."""
        invalid_actions = ['maybe', 'pending', 'cancel', '']
        
        for action in invalid_actions:
            with self.subTest(action=action):
                data = {'action': action}
                serializer = PurchaseApprovalActionSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('action', serializer.errors)

    def test_parent_notes_sanitization(self):
        """Test parent notes are properly sanitized."""
        # Test HTML sanitization
        data = {
            'action': 'approve',
            'parent_notes': '<script>alert("xss")</script>Approved for good grades'
        }
        serializer = PurchaseApprovalActionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent_notes', serializer.errors)

    def test_parent_notes_suspicious_content(self):
        """Test parent notes reject suspicious content."""
        suspicious_content = [
            'javascript:alert()',
            'data:text/html,<script>',
            'vbscript:msgbox',
            '<script>evil()</script>'
        ]
        
        for content in suspicious_content:
            with self.subTest(content=content):
                data = {
                    'action': 'approve',
                    'parent_notes': content
                }
                serializer = PurchaseApprovalActionSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('parent_notes', serializer.errors)

    def test_parent_notes_optional(self):
        """Test parent notes are optional."""
        data = {'action': 'approve'}
        serializer = PurchaseApprovalActionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_parent_notes_length_limit(self):
        """Test parent notes respect length limit."""
        long_notes = 'A' * 1001  # Over 1000 character limit
        data = {
            'action': 'approve',
            'parent_notes': long_notes
        }
        serializer = PurchaseApprovalActionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent_notes', serializer.errors)


class TestQuickTopupRequestSerializer(BaseAPITestCase):
    """Test suite for QuickTopupRequestSerializer - Quick hour purchases."""

    @mock_external_services
    def test_valid_quick_topup_request(self):
        """Test valid quick top-up request validation."""
        # Mock the service to return valid packages
        with patch('finances.services.renewal_payment_service.RenewalPaymentService') as mock_service:
            mock_service.return_value.QUICK_TOPUP_PACKAGES = {
                Decimal('1.00'): Decimal('8.00'),
                Decimal('3.00'): Decimal('20.00'),
                Decimal('5.00'): Decimal('30.00')
            }
            
            data = {
                'hours': '3.00',
                'payment_method_id': 1
            }
            serializer = QuickTopupRequestSerializer(data=data)
            self.assertTrue(serializer.is_valid())

    @mock_external_services  
    def test_invalid_hours_package(self):
        """Test validation rejects invalid hours packages."""
        with patch('finances.services.renewal_payment_service.RenewalPaymentService') as mock_service:
            mock_service.return_value.QUICK_TOPUP_PACKAGES = {
                Decimal('1.00'): Decimal('8.00'),
                Decimal('3.00'): Decimal('20.00'),
                Decimal('5.00'): Decimal('30.00')
            }
            
            data = {
                'hours': '2.50',  # Not in available packages
                'payment_method_id': 1
            }
            serializer = QuickTopupRequestSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('hours', serializer.errors)
            self.assertIn('Invalid hours package', str(serializer.errors['hours'][0]))

    def test_hours_validation_minimum_value(self):
        """Test hours validation requires positive value."""
        invalid_hours = [0, -1, -0.5]
        
        for hours in invalid_hours:
            with self.subTest(hours=hours):
                data = {
                    'hours': str(hours),
                    'payment_method_id': 1
                }
                serializer = QuickTopupRequestSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('hours', serializer.errors)

    def test_payment_method_id_optional(self):
        """Test payment_method_id is optional."""
        with patch('finances.services.renewal_payment_service.RenewalPaymentService') as mock_service:
            mock_service.return_value.QUICK_TOPUP_PACKAGES = {
                Decimal('1.00'): Decimal('8.00')
            }
            
            data = {'hours': '1.00'}
            serializer = QuickTopupRequestSerializer(data=data)
            self.assertTrue(serializer.is_valid())


class TestReceiptSerializer(BaseAPITestCase):
    """Test suite for ReceiptSerializer - Receipt management and PCI compliance."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            name='Test User'
        )
        self.transaction = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            metadata={'plan_name': 'Basic Plan'}
        )
        self.receipt = Receipt.objects.create(
            student=self.user,
            transaction=self.transaction,
            receipt_number='RCP-2024-001',
            amount=Decimal('50.00'),
            generated_at=datetime.datetime.now(),
            is_valid=True
        )

    def test_receipt_serialization(self):
        """Test serializing receipt data."""
        serializer = ReceiptSerializer(self.receipt)
        data = serializer.data
        
        # Verify all expected fields
        expected_fields = [
            'id', 'receipt_number', 'amount', 'generated_at', 'is_valid',
            'student_name', 'transaction_amount', 'transaction_type',
            'plan_name', 'pdf_file', 'metadata'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['student_name'], 'Test User')
        self.assertEqual(float(data['amount']), 50.00)
        self.assertEqual(data['plan_name'], 'Basic Plan')

    def test_plan_name_from_metadata(self):
        """Test plan name extraction from transaction metadata."""
        serializer = ReceiptSerializer(self.receipt)
        data = serializer.data
        
        self.assertEqual(data['plan_name'], 'Basic Plan')

    def test_plan_name_fallback(self):
        """Test plan name fallback for missing metadata."""
        transaction_no_metadata = PurchaseTransaction.objects.create(
            student=self.user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            metadata=None
        )
        receipt_no_metadata = Receipt.objects.create(
            student=self.user,
            transaction=transaction_no_metadata,
            receipt_number='RCP-2024-002',
            amount=Decimal('25.00'),
            generated_at=datetime.datetime.now(),
            is_valid=True
        )
        
        serializer = ReceiptSerializer(receipt_no_metadata)
        data = serializer.data
        
        self.assertEqual(data['plan_name'], 'Unknown Plan')

    def test_read_only_fields_protection(self):
        """Test read-only fields are properly protected."""
        read_only_fields = [
            'id', 'receipt_number', 'generated_at', 'student_name',
            'transaction_amount', 'transaction_type', 'plan_name',
            'created_at', 'updated_at'
        ]
        
        serializer = ReceiptSerializer()
        meta_read_only = serializer.Meta.read_only_fields
        
        for field in read_only_fields:
            self.assertIn(field, meta_read_only)


class TestMonthlyPaymentSummarySerializer(BaseAPITestCase):
    """Test suite for MonthlyPaymentSummarySerializer - Payment reporting."""

    def test_monthly_payment_summary_fields(self):
        """Test all required fields are present in summary."""
        data = {
            'billing_period': '2024-01',
            'teacher_id': 1,
            'teacher_name': 'Test Teacher',
            'teacher_email': 'teacher@example.com',
            'school_id': 1,
            'school_name': 'Test School',
            'total_hours': Decimal('40.00'),
            'total_amount': Decimal('1000.00'),
            'session_count': 20,
            'individual_sessions': {'count': 15, 'hours': 30.0},
            'group_sessions': {'count': 5, 'hours': 10.0},
            'trial_sessions': {'count': 2, 'hours': 2.0},
            'pending_amount': Decimal('200.00'),
            'calculated_amount': Decimal('600.00'),
            'paid_amount': Decimal('200.00')
        }
        
        serializer = MonthlyPaymentSummarySerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_decimal_field_precision(self):
        """Test decimal fields maintain proper precision."""
        data = {
            'billing_period': '2024-01',
            'teacher_id': 1,
            'teacher_name': 'Test Teacher',
            'teacher_email': 'teacher@example.com',
            'school_id': 1,
            'school_name': 'Test School',
            'total_hours': '40.50',  # 2 decimal places
            'total_amount': '1234.56',  # 2 decimal places
            'session_count': 20,
            'individual_sessions': {},
            'group_sessions': {},
            'trial_sessions': {},
            'pending_amount': '0.00',
            'calculated_amount': '1234.56',
            'paid_amount': '0.00'
        }
        
        serializer = MonthlyPaymentSummarySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['total_hours'], Decimal('40.50'))
        self.assertEqual(serializer.validated_data['total_amount'], Decimal('1234.56'))


# Mark first todo as completed
class TestSerializersComprehensiveFinances(BaseAPITestCase):
    """Integration test suite for finances serializers working together."""

    def test_purchase_workflow_serializers_integration(self):
        """Test serializers work together in purchase workflow."""
        # This is a placeholder for integration testing
        # Would test the full flow from purchase initiation to receipt generation
        pass

    def test_budget_control_workflow_integration(self):
        """Test budget control serializers work together in approval workflow."""
        # This is a placeholder for integration testing
        # Would test parent-child approval workflow end-to-end
        pass