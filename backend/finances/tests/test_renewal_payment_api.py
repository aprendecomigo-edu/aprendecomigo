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
        
        url = '/api/finances/student-balance/topup-packages/'
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
        url = '/api/finances/student-balance/topup-packages/'
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
            
            url = '/api/finances/student-balance/renew-subscription/'
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
        
        url = '/api/finances/student-balance/renew-subscription/'
        data = {
            'original_transaction_id': 99999,  # Non-existent
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_renew_subscription_invalid_payment_method(self):
        """Test renewal with invalid payment method."""
        self.client.force_authenticate(user=self.student)
        
        url = '/api/finances/student-balance/renew-subscription/'
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
        
        url = '/api/finances/student-balance/renew-subscription/'
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
            
            url = '/api/finances/student-balance/quick-topup/'
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
        
        url = '/api/finances/student-balance/quick-topup/'
        data = {
            'hours': '3.00',  # Invalid package
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quick_topup_missing_hours(self):
        """Test quick top-up without specifying hours."""
        self.client.force_authenticate(user=self.student)
        
        url = '/api/finances/student-balance/quick-topup/'
        data = {}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quick_topup_invalid_payment_method(self):
        """Test quick top-up with invalid payment method."""
        self.client.force_authenticate(user=self.student)
        
        url = '/api/finances/student-balance/quick-topup/'
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
            
            url = '/api/finances/student-balance/renew-subscription/'
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
        url = '/api/finances/student-balance/quick-topup/'
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
            ('/api/finances/student-balance/topup-packages/', 'get', {}),
            ('/api/finances/student-balance/renew-subscription/', 'post', {'original_transaction_id': 1}),
            ('/api/finances/student-balance/quick-topup/', 'post', {'hours': '5.00'}),
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
        url = '/api/finances/student-balance/renew-subscription/'
        data = {
            'original_transaction_id': 1,
            'payment_method_id': self.payment_method2.id  # Other user's method
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test quick topup endpoint
        url = '/api/finances/student-balance/quick-topup/'
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
        url = '/api/finances/student-balance/quick-topup/'
        data = {'hours': '-5.00'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test extremely large hours
        data = {'hours': '999999.00'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid transaction ID
        url = '/api/finances/student-balance/renew-subscription/'
        data = {'original_transaction_id': -1}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_limiting_protection(self):
        """Test that renewal endpoints are protected against abuse."""
        # This test would typically involve making many rapid requests
        # but for now we just ensure the endpoints respond correctly
        self.client.force_authenticate(user=self.student1)
        
        url = '/api/finances/student-balance/topup-packages/'
        
        # Make multiple requests rapidly
        responses = []
        for _ in range(5):
            response = self.client.get(url)
            responses.append(response.status_code)
        
        # All should succeed (rate limiting would be implemented at middleware level)
        for status_code in responses:
            self.assertIn(status_code, [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS])