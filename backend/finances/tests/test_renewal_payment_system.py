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

from django.contrib.auth import get_user_model
from accounts.models import School
from finances.models import (
    StoredPaymentMethod,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)
from finances.services.payment_method_service import PaymentMethodService
from finances.services.renewal_payment_service import RenewalPaymentService

User = get_user_model()


class StoredPaymentMethodModelTests(TestCase):
    """Test suite for StoredPaymentMethod model enhancements."""

    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
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

    def test_unique_default_constraint(self):
        """Test that only one default payment method per student is allowed."""
        # Create first default payment method
        StoredPaymentMethod.objects.create(**self.payment_method_data)
        
        # Try to create second default payment method for same student
        second_data = self.payment_method_data.copy()
        second_data['stripe_payment_method_id'] = 'pm_test_second'
        second_data['stripe_customer_id'] = 'cus_test_second'
        
        # This should not raise an error as the model's save method handles it
        second_payment_method = StoredPaymentMethod.objects.create(**second_data)
        
        # Verify only one is default
        default_methods = StoredPaymentMethod.objects.filter(
            student=self.student,
            is_default=True
        )
        self.assertEqual(default_methods.count(), 1)
        self.assertEqual(default_methods.first(), second_payment_method)

    def test_stripe_payment_method_id_uniqueness(self):
        """Test that stripe_payment_method_id is unique across all records."""
        StoredPaymentMethod.objects.create(**self.payment_method_data)
        
        # Create another student
        another_student = User.objects.create_user(
            email='another@test.com',
            name='Another Student',
        )
        
        # Try to create payment method with same stripe_payment_method_id
        duplicate_data = self.payment_method_data.copy()
        duplicate_data['student'] = another_student
        
        with self.assertRaises(IntegrityError):
            StoredPaymentMethod.objects.create(**duplicate_data)

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
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        self.service = PaymentMethodService()

    @patch('finances.services.payment_method_service.StripeService')
    def test_add_payment_method_with_customer_creation(self, mock_stripe_service):
        """Test adding payment method with automatic customer creation."""
        # Mock Stripe responses
        mock_payment_method = Mock()
        mock_payment_method.id = 'pm_test_123456789'
        mock_payment_method.type = 'card'
        mock_payment_method.card = {
            'brand': 'visa',
            'last4': '4242',
            'exp_month': 12,
            'exp_year': 2025
        }
        
        mock_customer = Mock()
        mock_customer.id = 'cus_test_123456789'
        
        # Setup method mocks
        self.service.stripe_service.retrieve_payment_method = Mock(return_value={
            'success': True,
            'payment_method': mock_payment_method
        })
        self.service.stripe_service.create_customer = Mock(return_value={
            'success': True,
            'customer_id': 'cus_test_123456789',
            'customer': mock_customer
        })
        self.service.stripe_service.attach_payment_method_to_customer = Mock(return_value={
            'success': True,
            'payment_method': mock_payment_method
        })
        
        # Call the method
        result = self.service.add_payment_method(
            student_user=self.student,
            stripe_payment_method_id='pm_test_123456789',
            is_default=True
        )
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertIn('payment_method_id', result)
        self.assertEqual(result['stripe_customer_id'], 'cus_test_123456789')
        
        # Verify database record
        payment_method = StoredPaymentMethod.objects.get(id=result['payment_method_id'])
        self.assertEqual(payment_method.stripe_customer_id, 'cus_test_123456789')
        self.assertEqual(payment_method.stripe_payment_method_id, 'pm_test_123456789')
        self.assertTrue(payment_method.is_default)

    @patch('finances.services.payment_method_service.StripeService')
    def test_add_payment_method_with_existing_customer(self, mock_stripe_service):
        """Test adding payment method with existing customer."""
        # Create existing payment method with customer
        existing_pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_existing',
            stripe_customer_id='cus_existing_123',
            card_brand='mastercard',
            card_last4='1234',
            is_default=False,
            is_active=True
        )
        
        # Mock Stripe responses
        mock_payment_method = Mock()
        mock_payment_method.id = 'pm_test_new'
        mock_payment_method.type = 'card'
        mock_payment_method.card = {
            'brand': 'visa',
            'last4': '4242',
            'exp_month': 12,
            'exp_year': 2025
        }
        
        # Setup method mocks
        self.service.stripe_service.retrieve_payment_method = Mock(return_value={
            'success': True,
            'payment_method': mock_payment_method
        })
        self.service.stripe_service.retrieve_customer = Mock(return_value={
            'success': True,
            'customer': Mock(id='cus_existing_123')
        })
        self.service.stripe_service.attach_payment_method_to_customer = Mock(return_value={
            'success': True,
            'payment_method': mock_payment_method
        })
        
        # Call the method
        result = self.service.add_payment_method(
            student_user=self.student,
            stripe_payment_method_id='pm_test_new',
            is_default=True
        )
        
        # Verify result uses existing customer
        self.assertTrue(result['success'])
        self.assertEqual(result['stripe_customer_id'], 'cus_existing_123')

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
        self.student = User.objects.create_user(
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

    @patch('finances.services.renewal_payment_service.stripe')
    def test_quick_topup_success(self, mock_stripe):
        """Test successful quick top-up purchase."""
        # Mock Stripe payment intent
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_topup_123'
        mock_payment_intent.client_secret = 'pi_topup_123_secret'
        mock_payment_intent.status = 'succeeded'
        
        mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
        mock_stripe.PaymentIntent.confirm.return_value = mock_payment_intent
        
        # Call quick top-up
        result = self.service.quick_topup(
            student_user=self.student,
            hours=Decimal('5.00')
        )
        
        # Verify success
        self.assertTrue(result['success'])
        self.assertEqual(result['hours_purchased'], Decimal('5.00'))
        self.assertEqual(result['amount_paid'], Decimal('50.00'))
        
        # Verify transaction created
        transaction = PurchaseTransaction.objects.get(id=result['transaction_id'])
        self.assertEqual(transaction.transaction_type, TransactionType.PACKAGE)
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.metadata['renewal_type'], 'quick_topup')
        self.assertEqual(transaction.metadata['hours'], '5.00')

    def test_quick_topup_invalid_package(self):
        """Test quick top-up with invalid hours package."""
        result = self.service.quick_topup(
            student_user=self.student,
            hours=Decimal('3.00')  # Invalid package
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'invalid_package')

    @patch('finances.services.renewal_payment_service.stripe')
    def test_renew_subscription_success(self, mock_stripe):
        """Test successful subscription renewal."""
        # Mock Stripe payment intent
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_renewal_123'
        mock_payment_intent.client_secret = 'pi_renewal_123_secret'
        mock_payment_intent.status = 'succeeded'
        
        mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
        mock_stripe.PaymentIntent.confirm.return_value = mock_payment_intent
        
        # Call renewal
        result = self.service.renew_subscription(
            student_user=self.student,
            original_transaction_id=self.original_transaction.id
        )
        
        # Verify success
        self.assertTrue(result['success'])
        self.assertIn('transaction_id', result)
        
        # Verify new transaction created
        new_transaction = PurchaseTransaction.objects.get(id=result['transaction_id'])
        self.assertEqual(new_transaction.transaction_type, TransactionType.SUBSCRIPTION)
        self.assertEqual(new_transaction.amount, self.original_transaction.amount)
        self.assertEqual(
            new_transaction.metadata['original_transaction_id'], 
            self.original_transaction.id
        )

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
        self.student1 = User.objects.create_user(
            email='student1@test.com',
            name='Student One',
        )
        
        self.student2 = User.objects.create_user(
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

    def test_stored_payment_method_queryset_security(self):
        """Test that queryset filtering prevents cross-student data access."""
        # Student2 should not see student1's payment methods
        student2_methods = StoredPaymentMethod.objects.filter(student=self.student2)
        self.assertEqual(student2_methods.count(), 0)
        
        # Student1 should see their own
        student1_methods = StoredPaymentMethod.objects.filter(student=self.student1)
        self.assertEqual(student1_methods.count(), 1)

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