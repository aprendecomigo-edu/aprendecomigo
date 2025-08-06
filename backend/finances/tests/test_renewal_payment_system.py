"""
Tests for the renewal payment system including saved payment methods and renewal/quick-topup services.

This test suite covers:
- StoredPaymentMethod model with stripe_customer_id integration
- PaymentMethodService with Stripe Customer support
- RenewalPaymentService for one-click renewals and quick top-ups
- Security validations and error handling
"""

import json
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from accounts.models import CustomUser
from finances.models import (
    StoredPaymentMethod,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)
from finances.services.payment_method_service import PaymentMethodService
from finances.services.renewal_payment_service import RenewalPaymentService


class StoredPaymentMethodModelTests(TestCase):
    """Test suite for StoredPaymentMethod model enhancements."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        
        self.payment_method_data = {
            'student': self.student,
            'stripe_payment_method_id': 'pm_test_123456789',
            'stripe_customer_id': 'cus_test_123456789',
            'card_brand': 'visa',
            'card_last4': '4242',
            'card_exp_month': 12,
            'card_exp_year': 2025,
            'is_default': True,
            'is_active': True,
        }

    def test_stored_payment_method_creation_with_customer_id(self):
        """Test creating a StoredPaymentMethod with stripe_customer_id."""
        payment_method = StoredPaymentMethod.objects.create(**self.payment_method_data)
        
        self.assertEqual(payment_method.student, self.student)
        self.assertEqual(payment_method.stripe_payment_method_id, 'pm_test_123456789')
        self.assertEqual(payment_method.stripe_customer_id, 'cus_test_123456789')
        self.assertEqual(payment_method.card_brand, 'visa')
        self.assertEqual(payment_method.card_last4, '4242')
        self.assertEqual(payment_method.card_exp_month, 12)
        self.assertEqual(payment_method.card_exp_year, 2025)
        self.assertTrue(payment_method.is_default)
        self.assertTrue(payment_method.is_active)

    def test_stored_payment_method_creation_without_customer_id(self):
        """Test creating a StoredPaymentMethod without stripe_customer_id (backward compatibility)."""
        payment_method_data = self.payment_method_data.copy()
        del payment_method_data['stripe_customer_id']
        
        payment_method = StoredPaymentMethod.objects.create(**payment_method_data)
        
        self.assertEqual(payment_method.student, self.student)
        self.assertIsNone(payment_method.stripe_customer_id)
        self.assertEqual(payment_method.stripe_payment_method_id, 'pm_test_123456789')

    def test_card_display_property(self):
        """Test the card_display property."""
        payment_method = StoredPaymentMethod.objects.create(**self.payment_method_data)
        
        self.assertEqual(payment_method.card_display, 'Visa ****4242')

    def test_card_display_property_no_data(self):
        """Test card_display property when card data is missing."""
        payment_method_data = self.payment_method_data.copy()
        payment_method_data['card_brand'] = ''
        payment_method_data['card_last4'] = ''
        
        payment_method = StoredPaymentMethod.objects.create(**payment_method_data)
        
        self.assertEqual(payment_method.card_display, 'Payment Method')

    def test_is_expired_property(self):
        """Test the is_expired property."""
        # Test non-expired card
        payment_method = StoredPaymentMethod.objects.create(**self.payment_method_data)
        self.assertFalse(payment_method.is_expired)
        
        # Test expired card
        expired_data = self.payment_method_data.copy()
        expired_data['stripe_payment_method_id'] = 'pm_test_expired'
        expired_data['card_exp_year'] = 2020
        expired_data['card_exp_month'] = 1
        
        expired_payment_method = StoredPaymentMethod.objects.create(**expired_data)
        self.assertTrue(expired_payment_method.is_expired)



    def test_validation_expiration_month(self):
        """Test validation of card expiration month."""
        payment_method_data = self.payment_method_data.copy()
        payment_method_data['card_exp_month'] = 13  # Invalid month
        
        payment_method = StoredPaymentMethod(**payment_method_data)
        
        with self.assertRaises(ValidationError):
            payment_method.clean()

    def test_validation_card_last4_digits(self):
        """Test validation of card last 4 digits."""
        payment_method_data = self.payment_method_data.copy()
        payment_method_data['card_last4'] = 'abcd'  # Invalid format
        
        payment_method = StoredPaymentMethod(**payment_method_data)
        
        with self.assertRaises(ValidationError):
            payment_method.clean()

    def test_str_representation(self):
        """Test string representation of StoredPaymentMethod."""
        payment_method = StoredPaymentMethod.objects.create(**self.payment_method_data)
        
        expected = "Visa ****4242 - Test Student (Default)"
        self.assertEqual(str(payment_method), expected)
        
        # Test non-default
        payment_method.is_default = False
        payment_method.save()
        
        expected = "Visa ****4242 - Test Student"
        self.assertEqual(str(payment_method), expected)


class PaymentMethodServiceTests(TestCase):
    """Test suite for enhanced PaymentMethodService with Stripe Customer support."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        self.service = PaymentMethodService()



    def test_add_payment_method_duplicate_prevention(self):
        """Test prevention of duplicate payment method addition."""
        # Create existing payment method
        StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_duplicate',
            stripe_customer_id='cus_test_123',
            card_brand='visa',
            card_last4='4242',
            is_default=False,
            is_active=True
        )
        
        # Try to add same payment method
        result = self.service.add_payment_method(
            student_user=self.student,
            stripe_payment_method_id='pm_test_duplicate'
        )
        
        # Verify failure
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'already_exists')

    def test_get_default_payment_method(self):
        """Test getting default payment method."""
        # Create default payment method
        default_pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_default',
            stripe_customer_id='cus_test_123',
            card_brand='visa',
            card_last4='4242',
            is_default=True,
            is_active=True
        )
        
        # Create non-default payment method
        StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_non_default',
            stripe_customer_id='cus_test_123',
            card_brand='mastercard',
            card_last4='1234',
            is_default=False,
            is_active=True
        )
        
        # Get default
        result = self.service.get_default_payment_method(self.student)
        
        self.assertEqual(result.id, default_pm.id)
        self.assertTrue(result.is_default)

    def test_get_default_payment_method_none_exists(self):
        """Test getting default payment method when none exists."""
        result = self.service.get_default_payment_method(self.student)
        self.assertIsNone(result)


class RenewalPaymentServiceTests(TestCase):
    """Test suite for RenewalPaymentService."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        
        # Create student account balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('100.00')
        )
        
        # Create stored payment method
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_renewal',
            stripe_customer_id='cus_test_renewal',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True
        )
        
        # Create original subscription transaction
        self.original_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_original_123',
            stripe_customer_id='cus_test_renewal',
            metadata={
                'subscription_name': 'Premium Plan',
                'billing_cycle': 'monthly'
            }
        )
        
        self.service = RenewalPaymentService()

    def test_get_available_topup_packages(self):
        """Test getting available top-up packages."""
        packages = self.service.get_available_topup_packages()
        
        self.assertEqual(len(packages), 3)  # 5, 10, 20 hour packages
        
        # Check 5-hour package
        five_hour_package = next(p for p in packages if p['hours'] == 5.0)
        self.assertEqual(five_hour_package['price'], 50.0)
        self.assertEqual(five_hour_package['price_per_hour'], 10.0)


    def test_quick_topup_invalid_package(self):
        """Test quick top-up with invalid hours package."""
        result = self.service.quick_topup(
            student_user=self.student,
            hours=Decimal('3.00')  # Invalid package
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'invalid_package')


    def test_renew_subscription_invalid_transaction(self):
        """Test renewal with invalid original transaction."""
        result = self.service.renew_subscription(
            student_user=self.student,
            original_transaction_id=99999  # Non-existent
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'transaction_not_found')

    def test_renew_subscription_wrong_type(self):
        """Test renewal with non-subscription transaction."""
        # Create package transaction
        package_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('25.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_package_123',
            metadata={'hours': '5'}
        )
        
        result = self.service.renew_subscription(
            student_user=self.student,
            original_transaction_id=package_transaction.id
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'invalid_transaction_type')

    def test_renewal_no_default_payment_method(self):
        """Test renewal when no default payment method exists."""
        # Remove default flag
        self.payment_method.is_default = False
        self.payment_method.save()
        
        result = self.service.renew_subscription(
            student_user=self.student,
            original_transaction_id=self.original_transaction.id
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'no_default_payment_method')

    def test_renewal_expired_payment_method(self):
        """Test renewal with expired payment method."""
        # Make payment method expired
        self.payment_method.card_exp_year = 2020
        self.payment_method.card_exp_month = 1
        self.payment_method.save()
        
        result = self.service.renew_subscription(
            student_user=self.student,
            original_transaction_id=self.original_transaction.id
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'payment_method_expired')

    def test_savings_calculation(self):
        """Test savings percentage calculation."""
        # Test 5-hour package (no savings at base rate)
        savings_5h = self.service._calculate_savings_percent(Decimal('5.00'), Decimal('50.00'))
        self.assertEqual(savings_5h, 0.0)
        
        # Test 10-hour package (5% savings)
        savings_10h = self.service._calculate_savings_percent(Decimal('10.00'), Decimal('95.00'))
        self.assertEqual(savings_10h, 5.0)
        
        # Test 20-hour package (10% savings)
        savings_20h = self.service._calculate_savings_percent(Decimal('20.00'), Decimal('180.00'))
        self.assertEqual(savings_20h, 10.0)


class RenewalPaymentSecurityTests(TestCase):
    """Test suite for security aspects of the renewal payment system."""

    def setUp(self):
        """Set up test data."""
        self.student1 = CustomUser.objects.create_user(
            email='student1@test.com',
            name='Student One',
        )
        
        self.student2 = CustomUser.objects.create_user(
            email='student2@test.com',
            name='Student Two',
        )
        
        # Create payment method for student1
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student1,
            stripe_payment_method_id='pm_student1',
            stripe_customer_id='cus_student1',
            card_brand='visa',
            card_last4='4242',
            is_default=True,
            is_active=True
        )
        
        # Create transaction for student1
        self.transaction = PurchaseTransaction.objects.create(
            student=self.student1,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_student1',
            stripe_customer_id='cus_student1'
        )
        
        self.service = RenewalPaymentService()

    def test_renewal_cross_student_security(self):
        """Test that students cannot renew other students' transactions."""
        result = self.service.renew_subscription(
            student_user=self.student2,  # Different student
            original_transaction_id=self.transaction.id  # Student1's transaction
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'transaction_not_found')

    def test_payment_method_service_cross_student_security(self):
        """Test that payment method service respects student boundaries."""
        service = PaymentMethodService()
        
        # Try to get student1's default payment method as student2
        result = service.get_default_payment_method(self.student2)
        self.assertIsNone(result)
        
        # Verify student1 can get their own
        result = service.get_default_payment_method(self.student1)
        self.assertEqual(result.id, self.payment_method.id)


    def test_pci_compliance_no_raw_card_data(self):
        """Test that no raw card data is stored."""
        # Verify only safe card display data is stored
        self.assertIsNotNone(self.payment_method.card_last4)
        self.assertIsNotNone(self.payment_method.card_brand)
        self.assertEqual(len(self.payment_method.card_last4), 4)
        
        # Verify we only store Stripe references
        self.assertTrue(self.payment_method.stripe_payment_method_id.startswith('pm_'))
        self.assertTrue(self.payment_method.stripe_customer_id.startswith('cus_'))
        
        # Verify no full card numbers or sensitive data in any field
        for field in ['stripe_payment_method_id', 'stripe_customer_id', 'card_brand', 'card_last4']:
            value = getattr(self.payment_method, field)
            if value:
                # Should not contain full card numbers (16 digits)
                self.assertNotRegex(str(value), r'\d{16}')
                # Should not contain CVV patterns (3-4 digits alone)
                self.assertNotRegex(str(value), r'^\d{3,4}$')