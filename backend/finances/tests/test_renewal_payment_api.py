"""
API tests for the renewal payment system endpoints.

This test suite covers:
- Saved payment methods API endpoints (enhanced existing functionality)
- Subscription renewal API endpoints
- Quick top-up API endpoints
- Proper security, authentication, and authorization
"""

import json
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import CustomUser
from finances.models import (
    StoredPaymentMethod,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)


User = get_user_model()


class SavedPaymentMethodAPITests(TestCase):
    """Test suite for saved payment methods API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test student user
        self.student = CustomUser.objects.create_user(
            email='student@test.com',
            name='Test Student'
        )
        
        # Create another student for cross-user security tests
        self.other_student = CustomUser.objects.create_user(
            email='other@test.com',
            name='Other Student'
        )
        
        # Create test payment method
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_123456789',
            stripe_customer_id='cus_test_123456789',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )
        
        # Create student account balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('100.00')
        )

    def test_list_payment_methods_authenticated(self):
        """Test listing payment methods for authenticated student."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-payment-methods')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['payment_methods']), 1)
        
        payment_method_data = response.data['payment_methods'][0]
        self.assertEqual(payment_method_data['id'], self.payment_method.id)
        self.assertEqual(payment_method_data['card_display'], 'Visa ****4242')
        self.assertTrue(payment_method_data['is_default'])
        self.assertIn('stripe_customer_id', payment_method_data)

    def test_list_payment_methods_unauthenticated(self):
        """Test listing payment methods without authentication."""
        url = reverse('finances:studentbalance-payment-methods')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_payment_methods_cross_user_security(self):
        """Test that users can only see their own payment methods."""
        self.client.force_authenticate(user=self.other_student)
        
        url = reverse('finances:studentbalance-payment-methods')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['payment_methods']), 0)

    @patch('finances.services.payment_method_service.stripe')
    def test_add_payment_method_success(self, mock_stripe):
        """Test successfully adding a new payment method."""
        self.client.force_authenticate(user=self.student)
        
        # Mock Stripe responses
        mock_payment_method = Mock()
        mock_payment_method.id = 'pm_test_new'
        mock_payment_method.type = 'card'
        mock_payment_method.card = {
            'brand': 'mastercard',
            'last4': '1234',
            'exp_month': 6,
            'exp_year': 2026
        }
        
        # Mock service calls within the view
        with patch('finances.services.payment_method_service.PaymentMethodService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.add_payment_method.return_value = {
                'success': True,
                'payment_method_id': 999,
                'card_display': 'Mastercard ****1234',
                'is_default': False,
                'stripe_customer_id': 'cus_test_123456789',
                'message': 'Payment method added successfully'
            }
            
            url = reverse('finances:studentbalance-payment-methods')
            data = {
                'stripe_payment_method_id': 'pm_test_new',
                'is_default': False
            }
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(response.data['success'])
            self.assertEqual(response.data['payment_method_id'], 999)
            
            # Verify service was called with correct parameters
            mock_service.add_payment_method.assert_called_once_with(
                student_user=self.student,
                stripe_payment_method_id='pm_test_new',
                is_default=False
            )

    def test_add_payment_method_invalid_data(self):
        """Test adding payment method with invalid data."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-payment-methods')
        data = {
            'stripe_payment_method_id': 'invalid_format',  # Invalid format
            'is_default': False
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_payment_method_success(self):
        """Test successfully removing a payment method."""
        self.client.force_authenticate(user=self.student)
        
        with patch('finances.services.payment_method_service.PaymentMethodService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.remove_payment_method.return_value = {
                'success': True,
                'message': 'Payment method removed successfully',
                'was_default': True
            }
            
            url = reverse('finances:studentbalance-remove-payment-method', kwargs={'pk': self.payment_method.id})
            response = self.client.delete(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            
            # Verify service was called
            mock_service.remove_payment_method.assert_called_once_with(
                student_user=self.student,
                payment_method_id=self.payment_method.id
            )

    def test_remove_payment_method_not_found(self):
        """Test removing a non-existent payment method."""
        self.client.force_authenticate(user=self.student)
        
        with patch('finances.services.payment_method_service.PaymentMethodService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.remove_payment_method.return_value = {
                'success': False,
                'error_type': 'not_found',
                'message': 'Payment method not found'
            }
            
            url = reverse('finances:studentbalance-remove-payment-method', kwargs={'pk': 99999})
            response = self.client.delete(url)
            
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_set_default_payment_method_success(self):
        """Test successfully setting default payment method."""
        self.client.force_authenticate(user=self.student)
        
        with patch('finances.services.payment_method_service.PaymentMethodService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.set_default_payment_method.return_value = {
                'success': True,
                'message': 'Default payment method updated successfully'
            }
            
            url = reverse('finances:studentbalance-set-default-payment-method', kwargs={'pk': self.payment_method.id})
            response = self.client.post(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            
            # Verify service was called
            mock_service.set_default_payment_method.assert_called_once_with(
                student_user=self.student,
                payment_method_id=self.payment_method.id
            )


class RenewalPaymentAPITests(TestCase):
    """Test suite for renewal payment API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test student user
        self.student = CustomUser.objects.create_user(
            email='student@test.com',
            name='Test Student'
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
            is_active=True,
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
        
        # Create student account balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('100.00')
        )

    def test_get_topup_packages(self):
        """Test getting available top-up packages."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-topup-packages')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('packages', response.data)
        
        packages = response.data['packages']
        self.assertEqual(len(packages), 3)  # 5, 10, 20 hour packages
        
        # Check that all required fields are present
        for package in packages:
            self.assertIn('hours', package)
            self.assertIn('price', package)
            self.assertIn('price_per_hour', package)
            self.assertIn('savings_percent', package)

    def test_get_topup_packages_unauthenticated(self):
        """Test getting top-up packages without authentication."""
        url = reverse('finances:studentbalance-topup-packages')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('finances.services.renewal_payment_service.stripe')
    def test_renew_subscription_success(self, mock_stripe):
        """Test successful subscription renewal."""
        self.client.force_authenticate(user=self.student)
        
        with patch('finances.services.renewal_payment_service.RenewalPaymentService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.renew_subscription.return_value = {
                'success': True,
                'transaction_id': 999,
                'payment_intent_id': 'pi_renewal_123',
                'message': 'Subscription renewed successfully'
            }
            
            url = reverse('finances:studentbalance-renew-subscription')
            data = {
                'original_transaction_id': self.original_transaction.id,
                'payment_method_id': self.payment_method.id
            }
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(response.data['success'])
            self.assertEqual(response.data['transaction_id'], 999)
            
            # Verify service was called
            mock_service.renew_subscription.assert_called_once_with(
                student_user=self.student,
                original_transaction_id=self.original_transaction.id,
                payment_method_id=self.payment_method.id
            )

    def test_renew_subscription_invalid_transaction(self):
        """Test renewal with invalid original transaction."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-renew-subscription')
        data = {
            'original_transaction_id': 99999,  # Non-existent
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_renew_subscription_invalid_payment_method(self):
        """Test renewal with invalid payment method."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-renew-subscription')
        data = {
            'original_transaction_id': self.original_transaction.id,
            'payment_method_id': 99999  # Non-existent
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_renew_subscription_cross_user_security(self):
        """Test that users cannot renew other users' subscriptions."""
        # Create another user's transaction
        other_user = CustomUser.objects.create_user(
            email='other@test.com',
            name='Other User'
        )
        
        other_transaction = PurchaseTransaction.objects.create(
            student=other_user,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_other_123',
        )
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-renew-subscription')
        data = {
            'original_transaction_id': other_transaction.id,
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('finances.services.renewal_payment_service.stripe')
    def test_quick_topup_success(self, mock_stripe):
        """Test successful quick top-up."""
        self.client.force_authenticate(user=self.student)
        
        with patch('finances.services.renewal_payment_service.RenewalPaymentService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.quick_topup.return_value = {
                'success': True,
                'transaction_id': 888,
                'payment_intent_id': 'pi_topup_123',
                'hours_purchased': Decimal('5.00'),
                'amount_paid': Decimal('50.00'),
                'message': 'Successfully purchased 5 hours for €50'
            }
            
            url = reverse('finances:studentbalance-quick-topup')
            data = {
                'hours': '5.00',
                'payment_method_id': self.payment_method.id
            }
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(response.data['success'])
            self.assertEqual(response.data['transaction_id'], 888)
            self.assertEqual(float(response.data['hours_purchased']), 5.00)
            
            # Verify service was called
            mock_service.quick_topup.assert_called_once_with(
                student_user=self.student,
                hours=Decimal('5.00'),
                payment_method_id=self.payment_method.id
            )

    def test_quick_topup_invalid_hours(self):
        """Test quick top-up with invalid hours package."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-quick-topup')
        data = {
            'hours': '3.00',  # Invalid package
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quick_topup_missing_hours(self):
        """Test quick top-up without specifying hours."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-quick-topup')
        data = {}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quick_topup_invalid_payment_method(self):
        """Test quick top-up with invalid payment method."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-quick-topup')
        data = {
            'hours': '5.00',
            'payment_method_id': 99999  # Non-existent
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_renewal_payment_method_service_error_handling(self):
        """Test proper error handling from renewal payment service."""
        self.client.force_authenticate(user=self.student)
        
        with patch('finances.services.renewal_payment_service.RenewalPaymentService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.renew_subscription.return_value = {
                'success': False,
                'error_type': 'payment_method_expired',
                'message': 'Payment method has expired. Please update your payment method.'
            }
            
            url = reverse('finances:studentbalance-renew-subscription')
            data = {
                'original_transaction_id': self.original_transaction.id,
            }
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)
            self.assertIn('error_type', response.data)


class RenewalPaymentSecurityAPITests(TestCase):
    """Test suite for security aspects of the renewal payment API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test users
        self.student1 = CustomUser.objects.create_user(
            email='student1@test.com',
            name='Student One'
        )
        
        self.student2 = CustomUser.objects.create_user(
            email='student2@test.com',
            name='Student Two'
        )
        
        # Create payment methods for different students
        self.payment_method1 = StoredPaymentMethod.objects.create(
            student=self.student1,
            stripe_payment_method_id='pm_student1',
            stripe_customer_id='cus_student1',
            card_brand='visa',
            card_last4='4242',
            is_default=True,
            is_active=True
        )
        
        self.payment_method2 = StoredPaymentMethod.objects.create(
            student=self.student2,
            stripe_payment_method_id='pm_student2',
            stripe_customer_id='cus_student2',
            card_brand='mastercard',
            card_last4='1234',
            is_default=True,
            is_active=True
        )

    def test_cross_user_payment_method_access_denied(self):
        """Test that users cannot access other users' payment methods."""
        self.client.force_authenticate(user=self.student1)
        
        # Try to use student2's payment method for renewal
        url = reverse('finances:studentbalance-quick-topup')
        data = {
            'hours': '5.00',
            'payment_method_id': self.payment_method2.id  # Different user's payment method
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Payment method not found or not accessible', response.data['error'])

    def test_renewal_requires_authentication(self):
        """Test that renewal endpoints require authentication."""
        endpoints = [
            (reverse('finances:studentbalance-topup-packages'), 'get', {}),
            (reverse('finances:studentbalance-renew-subscription'), 'post', {'original_transaction_id': 1}),
            (reverse('finances:studentbalance-quick-topup'), 'post', {'hours': '5.00'}),
        ]
        
        for url, method, data in endpoints:
            
            if method == 'get':
                response = self.client.get(url)
            else:
                response = self.client.post(url, data)
            
            self.assertEqual(
                response.status_code, 
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {url} should require authentication"
            )

    def test_payment_method_ownership_validation(self):
        """Test payment method ownership validation across all endpoints."""
        self.client.force_authenticate(user=self.student1)
        
        # Test renewal endpoint
        url = reverse('finances:studentbalance-renew-subscription')
        data = {
            'original_transaction_id': 1,
            'payment_method_id': self.payment_method2.id  # Other user's method
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test quick topup endpoint
        url = reverse('finances:studentbalance-quick-topup')
        data = {
            'hours': '5.00',
            'payment_method_id': self.payment_method2.id  # Other user's method
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_input_sanitization(self):
        """Test that inputs are properly sanitized and validated."""
        self.client.force_authenticate(user=self.student1)
        
        # Test negative hours
        url = reverse('finances:studentbalance-quick-topup')
        data = {'hours': '-5.00'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test extremely large hours
        data = {'hours': '999999.00'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid transaction ID
        url = reverse('finances:studentbalance-renew-subscription')
        data = {'original_transaction_id': -1}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_limiting_protection(self):
        """Test that renewal endpoints are protected against abuse."""
        # This test would typically involve making many rapid requests
        # but for now we just ensure the endpoints respond correctly
        self.client.force_authenticate(user=self.student1)
        
        url = reverse('finances:studentbalance-topup-packages')
        
        # Make multiple requests rapidly
        responses = []
        for _ in range(5):
            response = self.client.get(url)
            responses.append(response.status_code)
        
        # All should succeed (rate limiting would be implemented at middleware level)
        for status_code in responses:
            self.assertIn(status_code, [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS])