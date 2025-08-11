"""
Unit tests for Payment Method ID Type Conversion business logic.

Tests core business rules for payment method data validation and conversion:
- Payment method ID parameter validation and sanitization
- Type conversion algorithms for different input formats
- Card data extraction and normalization business rules
- Customer ID validation and lookup logic
- Parameter format validation for Stripe integration
- Data structure conversion between internal and Stripe formats

These tests focus on the business logic that needs fixes for GitHub Issue #173.
"""

from unittest.mock import Mock, patch
from django.test import TestCase

from finances.services.payment_method_service import (
    PaymentMethodService,
    PaymentMethodValidationError
)
from accounts.models import CustomUser
from finances.models import StoredPaymentMethod


class PaymentMethodIDValidationTest(TestCase):
    """Test payment method ID validation and type conversion business rules."""

    def setUp(self):
        """Set up test data."""
        self.service = PaymentMethodService()
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    def test_validate_stripe_payment_method_valid_id_format(self):
        """Test validation accepts valid Stripe payment method ID format."""
        # Mock Stripe response
        mock_stripe_data = {
            'id': 'pm_1234567890abcdef',
            'type': 'card',
            'card': {
                'brand': 'visa',
                'last4': '4242',
                'exp_month': 12,
                'exp_year': 2025
            }
        }
        
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.return_value = {
                'success': True,
                'payment_method': mock_stripe_data
            }
            
            result = self.service._validate_stripe_payment_method('pm_1234567890abcdef')
            
            self.assertTrue(result['success'])
            self.assertEqual(result['payment_method']['brand'], 'visa')
            self.assertEqual(result['payment_method']['last4'], '4242')
            self.assertEqual(result['payment_method']['exp_month'], 12)
            self.assertEqual(result['payment_method']['exp_year'], 2025)

    def test_validate_stripe_payment_method_invalid_id_format(self):
        """Test validation rejects invalid payment method ID formats."""
        # Mock Stripe error response
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.return_value = {
                'success': False,
                'message': 'Invalid payment method ID format'
            }
            
            result = self.service._validate_stripe_payment_method('invalid_id_123')
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error_type'], 'stripe_error')
            self.assertIn('Invalid payment method', result['message'])

    def test_validate_stripe_payment_method_empty_id(self):
        """Test validation handles empty payment method ID."""
        # Empty string should trigger validation error
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.return_value = {
                'success': False,
                'message': 'Payment method ID cannot be empty'
            }
            
            result = self.service._validate_stripe_payment_method('')
            
            self.assertFalse(result['success'])
            self.assertIn('Invalid payment method', result['message'])

    def test_validate_stripe_payment_method_none_id(self):
        """Test validation handles None payment method ID."""
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.side_effect = Exception("Payment method ID cannot be None")
            
            result = self.service._validate_stripe_payment_method(None)
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error_type'], 'validation_error')

    def test_validate_stripe_payment_method_stripe_exception(self):
        """Test validation handles Stripe API exceptions gracefully."""
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.side_effect = Exception("Stripe API connection failed")
            
            result = self.service._validate_stripe_payment_method('pm_1234567890abcdef')
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error_type'], 'validation_error')
            self.assertIn('Failed to validate payment method', result['message'])


class CardDataExtractionTest(TestCase):
    """Test card data extraction and normalization business rules."""

    def setUp(self):
        """Set up test data."""
        self.service = PaymentMethodService()

    def test_card_data_extraction_complete_data(self):
        """Test extraction of complete card data from Stripe response."""
        mock_stripe_data = {
            'id': 'pm_1234567890abcdef',
            'type': 'card',
            'card': {
                'brand': 'visa',
                'last4': '4242',
                'exp_month': 12,
                'exp_year': 2025,
                'funding': 'credit',
                'country': 'US'
            }
        }
        
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.return_value = {
                'success': True,
                'payment_method': mock_stripe_data
            }
            
            result = self.service._validate_stripe_payment_method('pm_1234567890abcdef')
            
            self.assertTrue(result['success'])
            card_data = result['payment_method']
            self.assertEqual(card_data['brand'], 'visa')
            self.assertEqual(card_data['last4'], '4242')
            self.assertEqual(card_data['exp_month'], 12)
            self.assertEqual(card_data['exp_year'], 2025)

    def test_card_data_extraction_missing_fields(self):
        """Test extraction handles missing card data fields."""
        mock_stripe_data = {
            'id': 'pm_1234567890abcdef',
            'type': 'card',
            'card': {
                'brand': 'mastercard',
                # Missing last4, exp_month, exp_year
            }
        }
        
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.return_value = {
                'success': True,
                'payment_method': mock_stripe_data
            }
            
            result = self.service._validate_stripe_payment_method('pm_1234567890abcdef')
            
            self.assertTrue(result['success'])
            card_data = result['payment_method']
            self.assertEqual(card_data['brand'], 'mastercard')
            self.assertEqual(card_data['last4'], '')  # Default empty string
            self.assertIsNone(card_data['exp_month'])  # Default None
            self.assertIsNone(card_data['exp_year'])   # Default None

    def test_card_data_extraction_non_card_payment_method(self):
        """Test extraction handles non-card payment methods."""
        mock_stripe_data = {
            'id': 'pm_1234567890abcdef',
            'type': 'sepa_debit',  # Not a card
            'sepa_debit': {
                'last4': '3000'
            }
        }
        
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.return_value = {
                'success': True,
                'payment_method': mock_stripe_data
            }
            
            result = self.service._validate_stripe_payment_method('pm_1234567890abcdef')
            
            self.assertTrue(result['success'])
            card_data = result['payment_method']
            # Should return empty card data for non-card payment methods
            self.assertEqual(card_data['brand'], '')
            self.assertEqual(card_data['last4'], '')
            self.assertIsNone(card_data['exp_month'])
            self.assertIsNone(card_data['exp_year'])

    def test_card_data_extraction_malformed_response(self):
        """Test extraction handles malformed Stripe response."""
        mock_stripe_data = {
            'id': 'pm_1234567890abcdef',
            'type': 'card',
            # Missing 'card' object entirely
        }
        
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.return_value = {
                'success': True,
                'payment_method': mock_stripe_data
            }
            
            result = self.service._validate_stripe_payment_method('pm_1234567890abcdef')
            
            self.assertTrue(result['success'])
            card_data = result['payment_method']
            # Should gracefully handle missing card data
            self.assertEqual(card_data['brand'], '')
            self.assertEqual(card_data['last4'], '')


class TypeConversionAlgorithmsTest(TestCase):
    """Test type conversion algorithms for different input formats."""

    def setUp(self):
        """Set up test data."""
        self.service = PaymentMethodService()
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    def test_payment_method_id_integer_conversion(self):
        """Test conversion of integer payment method IDs."""
        # Create a stored payment method
        stored_pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test123',
            stripe_customer_id='cus_test123',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True
        )
        
        # Test with integer ID (common from API)
        result = self.service.set_default_payment_method(self.student, stored_pm.id)
        
        self.assertTrue(result['success'])
        self.assertIn('successfully', result['message'])

    def test_payment_method_id_string_conversion(self):
        """Test conversion of string payment method IDs to integers."""
        stored_pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test123',
            stripe_customer_id='cus_test123',
            card_brand='visa',
            card_last4='4242',
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True
        )
        
        # Test with string ID that can be converted to int
        result = self.service.set_default_payment_method(self.student, str(stored_pm.id))
        
        self.assertTrue(result['success'])

    def test_payment_method_id_invalid_string_conversion(self):
        """Test handling of invalid string payment method IDs."""
        # Test with non-numeric string
        result = self.service.set_default_payment_method(self.student, "invalid_id")
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')

    def test_payment_method_id_negative_integer(self):
        """Test handling of negative payment method IDs."""
        result = self.service.set_default_payment_method(self.student, -1)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')

    def test_payment_method_id_zero_value(self):
        """Test handling of zero payment method ID."""
        result = self.service.set_default_payment_method(self.student, 0)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'not_found')

    def test_payment_method_id_none_value(self):
        """Test handling of None payment method ID."""
        result = self.service.set_default_payment_method(self.student, None)
        
        self.assertFalse(result['success'])
        # Should handle gracefully, likely as not found


class CustomerIDLookupLogicTest(TestCase):
    """Test customer ID validation and lookup business logic."""

    def setUp(self):
        """Set up test data."""
        self.service = PaymentMethodService()
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    def test_get_or_create_stripe_customer_existing_payment_method(self):
        """Test customer lookup from existing payment method."""
        # Create existing payment method with customer ID
        StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_existing',
            stripe_customer_id='cus_existing123',
            card_brand='visa',
            card_last4='4242',
            is_active=True
        )
        
        # Mock Stripe customer verification
        with patch.object(self.service.stripe_service, 'retrieve_customer') as mock_retrieve:
            mock_retrieve.return_value = {'success': True, 'customer': {'id': 'cus_existing123'}}
            
            result = self.service._get_or_create_stripe_customer(self.student)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['customer_id'], 'cus_existing123')
            self.assertTrue(result['existing'])

    def test_get_or_create_stripe_customer_invalid_existing_customer(self):
        """Test handling when existing customer ID is invalid in Stripe."""
        # Create payment method with invalid customer ID
        StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_existing',
            stripe_customer_id='cus_invalid123',
            card_brand='visa',
            card_last4='4242',
            is_active=True
        )
        
        with patch.object(self.service.stripe_service, 'retrieve_customer') as mock_retrieve:
            mock_retrieve.return_value = {'success': False, 'message': 'Customer not found'}
            
            # Mock customer creation for fallback
            with patch.object(self.service.stripe_service, 'create_customer') as mock_create:
                mock_create.return_value = {
                    'success': True,
                    'customer_id': 'cus_new123'
                }
                
                result = self.service._get_or_create_stripe_customer(self.student)
                
                self.assertTrue(result['success'])
                self.assertEqual(result['customer_id'], 'cus_new123')
                self.assertFalse(result['existing'])

    def test_get_or_create_stripe_customer_from_transaction_lookup(self):
        """Test customer lookup from existing transactions."""
        # Mock transaction lookup
        mock_transaction = Mock()
        mock_transaction.stripe_customer_id = 'cus_from_transaction123'
        
        with patch('finances.services.payment_method_service.apps.get_model') as mock_get_model:
            mock_model = Mock()
            mock_model.objects.filter.return_value.first.return_value = mock_transaction
            mock_get_model.return_value = mock_model
            
            # Mock Stripe customer verification
            with patch.object(self.service.stripe_service, 'retrieve_customer') as mock_retrieve:
                mock_retrieve.return_value = {'success': True}
                
                result = self.service._get_or_create_stripe_customer(self.student)
                
                self.assertTrue(result['success'])
                self.assertEqual(result['customer_id'], 'cus_from_transaction123')
                self.assertTrue(result['existing'])

    def test_get_or_create_stripe_customer_auto_create_disabled(self):
        """Test behavior when auto-create is disabled and no customer exists."""
        result = self.service._get_or_create_stripe_customer(self.student, auto_create=False)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'no_customer')
        self.assertIn('auto-creation is disabled', result['message'])

    def test_get_or_create_stripe_customer_create_new_customer(self):
        """Test creation of new Stripe customer."""
        with patch.object(self.service.stripe_service, 'create_customer') as mock_create:
            mock_create.return_value = {
                'success': True,
                'customer_id': 'cus_newly_created123'
            }
            
            result = self.service._get_or_create_stripe_customer(self.student)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['customer_id'], 'cus_newly_created123')
            self.assertFalse(result['existing'])
            
            # Verify customer creation parameters
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            self.assertEqual(call_args['email'], self.student.email)
            self.assertEqual(call_args['name'], self.student.name)
            self.assertIn('student_id', call_args['metadata'])

    def test_get_or_create_stripe_customer_creation_failure(self):
        """Test handling of Stripe customer creation failure."""
        with patch.object(self.service.stripe_service, 'create_customer') as mock_create:
            mock_create.return_value = {
                'success': False,
                'error_type': 'stripe_error',
                'message': 'Failed to create customer'
            }
            
            result = self.service._get_or_create_stripe_customer(self.student)
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error_type'], 'stripe_error')

    def test_get_or_create_stripe_customer_model_lookup_error(self):
        """Test handling of model lookup errors during transaction search."""
        # Mock LookupError when accessing PurchaseTransaction model
        with patch('finances.services.payment_method_service.apps.get_model') as mock_get_model:
            mock_get_model.side_effect = LookupError("Model not found")
            
            # Should continue and create new customer despite lookup error
            with patch.object(self.service.stripe_service, 'create_customer') as mock_create:
                mock_create.return_value = {
                    'success': True,
                    'customer_id': 'cus_fallback123'
                }
                
                result = self.service._get_or_create_stripe_customer(self.student)
                
                self.assertTrue(result['success'])
                self.assertEqual(result['customer_id'], 'cus_fallback123')


class ParameterFormatValidationTest(TestCase):
    """Test parameter format validation for service method inputs."""

    def setUp(self):
        """Set up test data."""
        self.service = PaymentMethodService()
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    def test_add_payment_method_parameter_validation(self):
        """Test parameter validation in add_payment_method method."""
        # Mock validation to focus on parameter handling
        with patch.object(self.service, '_validate_stripe_payment_method') as mock_validate:
            mock_validate.return_value = {
                'success': True,
                'payment_method': {'brand': 'visa', 'last4': '4242', 'exp_month': 12, 'exp_year': 2025}
            }
            
            with patch.object(self.service, '_get_or_create_stripe_customer') as mock_customer:
                mock_customer.return_value = {'success': True, 'customer_id': 'cus_test123'}
                
                with patch.object(self.service.stripe_service, 'attach_payment_method_to_customer') as mock_attach:
                    mock_attach.return_value = {'success': True}
                    
                    # Test with valid parameters
                    result = self.service.add_payment_method(
                        student_user=self.student,
                        stripe_payment_method_id='pm_valid123',
                        is_default=True,
                        auto_create_customer=True
                    )
                    
                    self.assertTrue(result['success'])

    def test_remove_payment_method_invalid_id_type(self):
        """Test remove_payment_method with invalid ID types."""
        # Test with string that can't be converted to int
        result = self.service.remove_payment_method(self.student, "invalid_string")
        
        # Should handle gracefully - either convert or return not found
        self.assertFalse(result['success'])

    def test_list_payment_methods_boolean_parameter_validation(self):
        """Test list_payment_methods with boolean parameter validation."""
        # Test with valid boolean
        result = self.service.list_payment_methods(self.student, include_expired=True)
        self.assertTrue(result['success'])
        
        # Test with string that should be converted to boolean
        result = self.service.list_payment_methods(self.student, include_expired="true")
        self.assertTrue(result['success'])  # Should handle string conversion

    def test_parameter_none_handling(self):
        """Test handling of None parameters across service methods."""
        # Test set_default_payment_method with None ID
        result = self.service.set_default_payment_method(self.student, None)
        self.assertFalse(result['success'])
        
        # Test remove_payment_method with None ID  
        result = self.service.remove_payment_method(self.student, None)
        self.assertFalse(result['success'])


class DataStructureConversionTest(TestCase):
    """Test conversion between internal and external data structures."""

    def setUp(self):
        """Set up test data."""
        self.service = PaymentMethodService()
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    def test_stripe_to_internal_data_conversion(self):
        """Test conversion from Stripe data format to internal format."""
        stripe_payment_method = {
            'id': 'pm_1234567890abcdef',
            'type': 'card',
            'card': {
                'brand': 'visa',
                'last4': '4242',
                'exp_month': 12,
                'exp_year': 2025,
                'funding': 'credit',
                'country': 'US'
            }
        }
        
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.return_value = {
                'success': True,
                'payment_method': stripe_payment_method
            }
            
            result = self.service._validate_stripe_payment_method('pm_1234567890abcdef')
            
            # Should extract only relevant fields for internal storage
            internal_data = result['payment_method']
            self.assertEqual(internal_data['brand'], 'visa')
            self.assertEqual(internal_data['last4'], '4242')
            self.assertEqual(internal_data['exp_month'], 12)
            self.assertEqual(internal_data['exp_year'], 2025)
            
            # Should not include Stripe-specific fields
            self.assertNotIn('funding', internal_data)
            self.assertNotIn('country', internal_data)

    def test_internal_to_api_response_conversion(self):
        """Test conversion from internal format to API response format."""
        stored_pm = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test123',
            stripe_customer_id='cus_test123',
            card_brand='mastercard',
            card_last4='5678',
            card_exp_month=6,
            card_exp_year=2026,
            is_default=True,
            is_active=True
        )
        
        result = self.service.list_payment_methods(self.student)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['payment_methods']), 1)
        
        api_pm = result['payment_methods'][0]
        self.assertEqual(api_pm['id'], stored_pm.id)
        self.assertEqual(api_pm['card_brand'], 'mastercard')
        self.assertEqual(api_pm['card_last4'], '5678')
        self.assertEqual(api_pm['card_exp_month'], 6)
        self.assertEqual(api_pm['card_exp_year'], 2026)
        self.assertTrue(api_pm['is_default'])
        self.assertFalse(api_pm['is_expired'])
        self.assertIn('created_at', api_pm)

    def test_error_response_standardization(self):
        """Test standardization of error response formats."""
        # Test validation error format
        with patch.object(self.service.stripe_service, 'retrieve_payment_method') as mock_retrieve:
            mock_retrieve.side_effect = Exception("Network error")
            
            result = self.service._validate_stripe_payment_method('pm_test123')
            
            # Should have standardized error format
            self.assertFalse(result['success'])
            self.assertIn('error_type', result)
            self.assertIn('message', result)
            self.assertEqual(result['error_type'], 'validation_error')

    def test_metadata_structure_consistency(self):
        """Test consistency of metadata structure across operations."""
        # Test customer creation metadata
        with patch.object(self.service.stripe_service, 'create_customer') as mock_create:
            mock_create.return_value = {
                'success': True,
                'customer_id': 'cus_test123'
            }
            
            self.service._get_or_create_stripe_customer(self.student)
            
            # Verify metadata structure
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            metadata = call_args['metadata']
            
            self.assertIn('student_id', metadata)
            self.assertIn('platform', metadata)
            self.assertIn('created_via', metadata)
            self.assertEqual(metadata['student_id'], str(self.student.id))
            self.assertEqual(metadata['platform'], 'aprende_comigo')