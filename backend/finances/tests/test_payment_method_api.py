"""
Tests for payment method management APIs in the finances app.

Tests the PaymentMethodService and related API endpoints for
storing, listing, and managing payment methods with Stripe integration.
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from finances.models import StoredPaymentMethod
from finances.services.payment_method_service import PaymentMethodService


User = get_user_model()


class PaymentMethodServiceTest(TestCase):
    """Test cases for the PaymentMethodService."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
        
        self.service = PaymentMethodService()
    
    @patch('finances.services.payment_method_service.StripeService')
    def test_add_payment_method_success(self, mock_stripe_service):
        """Test successful payment method addition."""
        # Mock Stripe service
        mock_stripe_instance = MagicMock()
        mock_stripe_service.return_value = mock_stripe_instance
        
        mock_stripe_instance.retrieve_payment_method.return_value = {
            'success': True,
            'payment_method': {
                'type': 'card',
                'card': {
                    'brand': 'visa',
                    'last4': '4242',
                    'exp_month': 12,
                    'exp_year': 2025
                }
            }
        }
        
        result = self.service.add_payment_method(
            student_user=self.student,
            stripe_payment_method_id='pm_test_123',
            is_default=True
        )
        
        self.assertTrue(result['success'])
        self.assertIn('payment_method_id', result)
        self.assertTrue(result['is_default'])
        
        # Check payment method was created in database
        payment_method = StoredPaymentMethod.objects.get(id=result['payment_method_id'])
        self.assertEqual(payment_method.student, self.student)
        self.assertEqual(payment_method.stripe_payment_method_id, 'pm_test_123')
        self.assertEqual(payment_method.card_brand, 'visa')
        self.assertEqual(payment_method.card_last4, '4242')
        self.assertTrue(payment_method.is_default)
    
    @patch('finances.services.payment_method_service.StripeService')
    def test_add_payment_method_stripe_error(self, mock_stripe_service):
        """Test payment method addition with Stripe error."""
        # Mock Stripe service error
        mock_stripe_instance = MagicMock()
        mock_stripe_service.return_value = mock_stripe_instance
        
        mock_stripe_instance.retrieve_payment_method.return_value = {
            'success': False,
            'message': 'Invalid payment method'
        }
        
        result = self.service.add_payment_method(
            student_user=self.student,
            stripe_payment_method_id='pm_invalid_123',
            is_default=False
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'stripe_error')
        self.assertIn('Invalid payment method', result['message'])
    
    def test_add_payment_method_already_exists(self):
        """Test adding payment method that already exists."""
        # Create existing payment method
        StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_123',
            card_brand='visa',
            card_last4='4242'
        )
        
        with patch('finances.services.payment_method_service.StripeService'):
            result = self.service.add_payment_method(
                student_user=self.student,
                stripe_payment_method_id='pm_test_123',
                is_default=False
            )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'already_exists')
    
    def test_list_payment_methods(self):
        """Test listing payment methods."""
        # Create payment methods
        pm1 = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_1',
            card_brand='visa',
            card_last4='4242',
            is_default=True
        )
        
        pm2 = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_2',
            card_brand='mastercard',
            card_last4='5555',
            is_default=False
        )
        
        result = self.service.list_payment_methods(self.student)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 2)
        
        # Check ordering (default first)
        payment_methods = result['payment_methods']
        self.assertEqual(payment_methods[0]['id'], pm1.id)
        self.assertTrue(payment_methods[0]['is_default'])
        self.assertEqual(payment_methods[1]['id'], pm2.id)
        self.assertFalse(payment_methods[1]['is_default'])
    
    def test_list_payment_methods_exclude_expired(self):
        """Test listing payment methods excluding expired ones."""
        # Create expired payment method
        StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_expired',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=1,
            card_exp_year=2020  # Expired
        )
        
        # Create valid payment method
        StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_valid',
            card_brand='visa',
            card_last4='5555',
            card_exp_month=12,
            card_exp_year=2025
        )
        
        result = self.service.list_payment_methods(self.student, include_expired=False)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)  # Only non-expired
    
    @patch('finances.services.payment_method_service.StripeService')
    def test_remove_payment_method_success(self, mock_stripe_service):
        """Test successful payment method removal."""
        # Create payment method
        pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_123',
            card_brand='visa',
            card_last4='4242'
        )
        
        # Mock Stripe service
        mock_stripe_instance = MagicMock()
        mock_stripe_service.return_value = mock_stripe_instance
        mock_stripe_instance.detach_payment_method.return_value = {'success': True}
        
        result = self.service.remove_payment_method(self.student, pm.id)
        
        self.assertTrue(result['success'])
        self.assertFalse(result['was_default'])
        
        # Check payment method was removed
        self.assertFalse(StoredPaymentMethod.objects.filter(id=pm.id).exists())
    
    def test_remove_payment_method_not_found(self):
        """Test removing non-existent payment method."""
        result = self.service.remove_payment_method(self.student, 99999)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')
    
    def test_remove_default_payment_method(self):
        """Test removing default payment method."""
        # Create two payment methods
        pm1 = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_1',
            card_brand='visa',
            card_last4='4242',
            is_default=True
        )
        
        pm2 = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_2',
            card_brand='mastercard',
            card_last4='5555',
            is_default=False
        )
        
        with patch('finances.services.payment_method_service.StripeService') as mock_stripe_service:
            mock_stripe_instance = MagicMock()
            mock_stripe_service.return_value = mock_stripe_instance
            mock_stripe_instance.detach_payment_method.return_value = {'success': True}
            
            result = self.service.remove_payment_method(self.student, pm1.id)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['was_default'])
        
        # Check that pm2 became the new default
        pm2.refresh_from_db()
        self.assertTrue(pm2.is_default)
    
    def test_set_default_payment_method(self):
        """Test setting default payment method."""
        # Create payment methods
        pm1 = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_1',
            card_brand='visa',
            card_last4='4242',
            is_default=True
        )
        
        pm2 = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_2',
            card_brand='mastercard',
            card_last4='5555',
            is_default=False
        )
        
        result = self.service.set_default_payment_method(self.student, pm2.id)
        
        self.assertTrue(result['success'])
        
        # Check defaults were updated
        pm1.refresh_from_db()
        pm2.refresh_from_db()
        self.assertFalse(pm1.is_default)
        self.assertTrue(pm2.is_default)
    
    def test_set_default_expired_payment_method(self):
        """Test setting expired payment method as default."""
        # Create expired payment method
        pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_expired',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=1,
            card_exp_year=2020  # Expired
        )
        
        result = self.service.set_default_payment_method(self.student, pm.id)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'expired')
    
    def test_get_default_payment_method(self):
        """Test getting default payment method."""
        # Create payment methods
        pm1 = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_1',
            card_brand='visa',
            card_last4='4242',
            is_default=False
        )
        
        pm2 = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_2',
            card_brand='mastercard',
            card_last4='5555',
            is_default=True
        )
        
        default_pm = self.service.get_default_payment_method(self.student)
        
        self.assertEqual(default_pm, pm2)
    
    def test_cleanup_expired_payment_methods(self):
        """Test cleaning up expired payment methods."""
        # Create expired payment method
        expired_pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_expired',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=1,
            card_exp_year=2020,  # Expired
            is_default=True
        )
        
        # Create valid payment method
        valid_pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_valid',
            card_brand='mastercard',
            card_last4='5555',
            card_exp_month=12,
            card_exp_year=2025
        )
        
        result = self.service.cleanup_expired_payment_methods(self.student)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['expired_count'], 1)
        
        # Check expired payment method was deactivated
        expired_pm.refresh_from_db()
        self.assertFalse(expired_pm.is_active)
        self.assertFalse(expired_pm.is_default)
        
        # Check valid payment method is still active
        valid_pm.refresh_from_db()
        self.assertTrue(valid_pm.is_active)


class PaymentMethodAPITest(APITestCase):
    """Test cases for payment method API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
        
        # Create payment method
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_123',
            card_brand='visa',
            card_last4='4242',
            is_default=True
        )
    
    def test_list_payment_methods_authenticated(self):
        """Test listing payment methods as authenticated student."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-payment-methods')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
        
        payment_method_data = response.data['payment_methods'][0]
        self.assertEqual(payment_method_data['id'], self.payment_method.id)
        self.assertEqual(payment_method_data['card_brand'], 'visa')
        self.assertEqual(payment_method_data['card_last4'], '4242')
        self.assertTrue(payment_method_data['is_default'])
    
    def test_list_payment_methods_unauthenticated(self):
        """Test listing payment methods without authentication."""
        url = reverse('finances:studentbalance-payment-methods')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('finances.services.payment_method_service.PaymentMethodService.add_payment_method')
    def test_add_payment_method_success(self, mock_add_method):
        """Test successful payment method addition."""
        mock_add_method.return_value = {
            'success': True,
            'payment_method_id': 1,
            'card_display': 'Visa ****4242',
            'is_default': True,
            'message': 'Payment method added successfully'
        }
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-payment-methods')
        data = {
            'stripe_payment_method_id': 'pm_test_new',
            'is_default': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['payment_method_id'], 1)
        
        # Verify service was called with correct parameters
        mock_add_method.assert_called_once_with(
            student_user=self.student,
            stripe_payment_method_id='pm_test_new',
            is_default=True
        )
    
    def test_add_payment_method_invalid_id(self):
        """
        Test adding payment method with invalid Stripe ID format.
        
        **API Validation:** stripe_payment_method_id must start with 'pm_'
        **Expected Response:** 400 Bad Request with specific validation error
        """
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-payment-methods')
        data = {
            'stripe_payment_method_id': 'invalid_id',  # Should start with 'pm_'
            'is_default': False
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify specific validation error message
        error_data = response.json()
        self.assertIn('stripe_payment_method_id', error_data)
        error_message = str(error_data.get('stripe_payment_method_id', ''))
        self.assertIn('Invalid Stripe payment method ID format', error_message)
    
    def test_add_payment_method_missing_data(self):
        """Test adding payment method with missing data."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-payment-methods')
        data = {}  # Missing stripe_payment_method_id
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('finances.services.payment_method_service.PaymentMethodService.remove_payment_method')
    def test_remove_payment_method_success(self, mock_remove_method):
        """Test successful payment method removal."""
        mock_remove_method.return_value = {
            'success': True,
            'message': 'Payment method removed successfully',
            'was_default': True
        }
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-remove-payment-method', kwargs={'pk': self.payment_method.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['was_default'])
        
        # Verify service was called with correct parameters
        mock_remove_method.assert_called_once_with(
            student_user=self.student,
            payment_method_id=self.payment_method.id
        )
    
    def test_remove_payment_method_not_found(self):
        """Test removing non-existent payment method."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-remove-payment-method', kwargs={'pk': 99999})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('finances.services.payment_method_service.PaymentMethodService.set_default_payment_method')
    def test_set_default_payment_method_success(self, mock_set_default):
        """Test setting default payment method."""
        mock_set_default.return_value = {
            'success': True,
            'message': 'Default payment method updated successfully'
        }
        
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-set-default-payment-method', kwargs={'pk': self.payment_method.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify service was called with correct parameters
        mock_set_default.assert_called_once_with(
            student_user=self.student,
            payment_method_id=self.payment_method.id
        )
    
    def test_payment_methods_with_filters(self):
        """Test listing payment methods with query parameters."""
        self.client.force_authenticate(user=self.student)
        
        url = reverse('finances:studentbalance-payment-methods')
        response = self.client.get(url, {'include_expired': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_cross_user_payment_method_security(self):
        """Test that users cannot access other users' payment methods."""
        # Create another student with a payment method
        other_student = User.objects.create_user(
            email='other@example.com',
            name='Other Student',
            password='testpass123'
        )
        
        other_payment_method = StoredPaymentMethod.objects.create(
            student=other_student,
            stripe_payment_method_id='pm_other_123',
            card_brand='mastercard',
            card_last4='5555',
            is_default=True
        )
        
        self.client.force_authenticate(user=self.student)
        
        # Try to remove other user's payment method
        url = reverse('finances:studentbalance-remove-payment-method', kwargs={'pk': other_payment_method.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Try to set other user's payment method as default
        url = reverse('finances:studentbalance-set-default-payment-method', kwargs={'pk': other_payment_method.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_add_payment_method_with_malformed_stripe_id(self):
        """Test adding payment method with various malformed Stripe IDs."""
        self.client.force_authenticate(user=self.student)
        url = reverse('finances:studentbalance-payment-methods')
        
        malformed_ids = [
            'invalid_id',  # Wrong prefix
            'pm_',  # Too short
            'pm_' + 'x' * 100,  # Too long
            '',  # Empty
            None,  # None value would be handled by serializer
        ]
        
        for stripe_id in malformed_ids:
            if stripe_id is None:
                continue  # Skip None as it would be caught by required field validation
                
            data = {
                'stripe_payment_method_id': stripe_id,
                'is_default': False
            }
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                           f"Should reject malformed ID: {stripe_id}")


class StoredPaymentMethodModelTest(TestCase):
    """Test cases for the StoredPaymentMethod model."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            name='Test Student',
            password='testpass123'
        )
    
    def test_payment_method_creation(self):
        """Test creating a stored payment method."""
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_123',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True
        )
        
        self.assertEqual(payment_method.student, self.student)
        self.assertEqual(payment_method.stripe_payment_method_id, 'pm_test_123')
        self.assertEqual(payment_method.card_brand, 'visa')
        self.assertEqual(payment_method.card_last4, '4242')
        self.assertTrue(payment_method.is_default)
        self.assertTrue(payment_method.is_active)
    
    def test_payment_method_str_representation(self):
        """Test string representation of payment method."""
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_123',
            card_brand='visa',
            card_last4='4242',
            is_default=True
        )
        
        expected_str = f"Visa ****4242 - {self.student.name} (Default)"
        self.assertEqual(str(payment_method), expected_str)
    
    def test_payment_method_is_expired_property(self):
        """Test is_expired property."""
        # Create expired payment method
        expired_pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_expired',
            card_exp_month=1,
            card_exp_year=2020
        )
        
        # Create valid payment method
        valid_pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_valid',
            card_exp_month=12,
            card_exp_year=2025
        )
        
        self.assertTrue(expired_pm.is_expired)
        self.assertFalse(valid_pm.is_expired)
    
    def test_payment_method_default_constraint(self):
        """Test unique default constraint."""
        # Create first default payment method
        pm1 = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_1',
            is_default=True
        )
        
        # Create second payment method and set as default
        pm2 = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_2',
            is_default=True
        )
        
        # First payment method should no longer be default
        pm1.refresh_from_db()
        self.assertFalse(pm1.is_default)
        self.assertTrue(pm2.is_default)
    
    def test_payment_method_validation(self):
        """Test payment method validation."""
        # Test invalid exp_month
        with self.assertRaisesMessage(Exception, 'Card expiration month must be between 1 and 12'):
            payment_method = StoredPaymentMethod(
                student=self.student,
                stripe_payment_method_id='pm_test',
                card_exp_month=13  # Invalid
            )
            payment_method.full_clean()
        
        # Test invalid card_last4
        with self.assertRaisesMessage(Exception, 'Card last 4 digits must contain only numbers'):
            payment_method = StoredPaymentMethod(
                student=self.student,
                stripe_payment_method_id='pm_test',
                card_last4='abcd'  # Should be digits
            )
            payment_method.full_clean()