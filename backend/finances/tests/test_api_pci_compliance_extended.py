"""
Extended PCI Compliance API Tests - Issue #173 Priority 5

This test suite extends the existing PCI compliance tests with additional
scenarios and edge cases where raw card data might be exposed, addressing
comprehensive security validation for the renewal payment system.

These tests are designed to initially FAIL to demonstrate additional PCI
compliance vulnerabilities beyond the basic serializer and API response issues.

Extended Test Coverage:
- Error response PCI compliance (exception handling)
- Debug/logging PCI compliance validation  
- Admin endpoints PCI compliance
- Integration endpoint data exposure
- Performance endpoint data leakage
- WebSocket/real-time data exposure
- Bulk operation PCI compliance
"""

import json
import logging
from decimal import Decimal
from unittest.mock import Mock, patch
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import School
from finances.tests.stripe_test_utils import comprehensive_stripe_mocks_decorator
from finances.models import (
    StoredPaymentMethod,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)

User = get_user_model()


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class PCIComplianceErrorHandlingTests(APITestCase):
    """
    Test PCI compliance in error scenarios and exception handling.
    
    These tests validate that error responses, stack traces, and
    exception messages don't leak sensitive payment method data.
    """

    def setUp(self):
        """Set up test data for error handling tests."""
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        
        # Create payment method with sensitive data
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_test_error_123',
            stripe_customer_id='cus_test_error_123',
            card_brand='visa',
            card_last4='4242',  # PCI violation in error scenarios
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)

    @override_settings(DEBUG=True)
    def test_debug_mode_error_responses_pci_compliance_fails(self):
        """
        Test that debug mode error responses don't expose card data.
        
        When DEBUG=True, Django shows detailed error information.
        This should not include sensitive payment method data.
        
        Expected to FAIL initially if debug responses leak card data.
        """
        # Trigger an error with payment method operations
        invalid_data = {
            'payment_method_id': 'invalid-id',
            'reason': 'Testing debug mode PCI compliance'
        }
        
        url = '/api/finances/studentbalance/remove-payment-method/'
        response = self.client.post(url, invalid_data, format='json')
        
        # Get the full response content including potential debug info
        response_content = response.content.decode('utf-8')
        
        # Check for card data in debug responses
        sensitive_data_patterns = [
            self.payment_method.card_last4,
            self.payment_method.stripe_payment_method_id,
            self.payment_method.stripe_customer_id,
            'pm_test_error',
            'cus_test_error',
        ]
        
        for pattern in sensitive_data_patterns:
            self.assertNotIn(
                pattern,
                response_content,
                f"DEBUG mode error response contains sensitive data: '{pattern}'. "
                f"Check error handling to ensure payment method data is not included in tracebacks."
            )

    def test_validation_error_messages_pci_compliance_fails(self):
        """
        Test that validation error messages don't expose card data.
        
        Validation errors should provide helpful messages without
        including sensitive payment method information.
        
        Expected to FAIL initially if validation errors leak card data.
        """
        # Test various invalid scenarios that might trigger validation errors
        invalid_scenarios = [
            # Missing required fields
            {'reason': 'Missing payment method ID'},
            # Invalid payment method ID
            {'payment_method_id': 999999, 'reason': 'Non-existent payment method'},
            # Invalid data types
            {'payment_method_id': self.payment_method.id, 'reason': None},
        ]
        
        url = '/api/finances/studentbalance/remove-payment-method/'
        
        for invalid_data in invalid_scenarios:
            with self.subTest(scenario=invalid_data):
                response = self.client.post(url, invalid_data, format='json')
                
                if response.status_code == status.HTTP_400_BAD_REQUEST:
                    error_data = response.json()
                    error_json = json.dumps(error_data)
                    
                    # Validation errors should not include card data
                    sensitive_patterns = [
                        r'\d{4}',  # Any 4-digit sequence (potential card digits)
                        'pm_test_',  # Stripe payment method IDs
                        'cus_test_',  # Stripe customer IDs
                        '4242',  # Specific card digits
                    ]
                    
                    import re
                    for pattern in sensitive_patterns:
                        matches = re.findall(pattern, error_json)
                        if pattern == r'\d{4}':
                            # Filter out non-sensitive 4-digit sequences (years, etc.)
                            card_like_matches = [m for m in matches if not m.startswith('20')]
                            self.assertEqual(
                                len(card_like_matches), 0,
                                f"Validation error contains potential card digits: {card_like_matches}. "
                                f"Error response: {error_data}"
                            )
                        else:
                            self.assertEqual(
                                len(matches), 0,
                                f"Validation error contains sensitive pattern '{pattern}': {matches}. "
                                f"Error response: {error_data}"
                            )

    @patch('finances.services.payment_method_service.logger')
    def test_service_layer_logging_pci_compliance_fails(self, mock_logger):
        """
        Test that service layer logging doesn't expose card data.
        
        Service layer operations may log information for debugging.
        These logs should not contain sensitive payment method data.
        
        Expected to FAIL initially if logging exposes card data.
        """
        # Trigger a payment method operation that would generate logs
        remove_data = {
            'payment_method_id': self.payment_method.id,
            'reason': 'Testing logging PCI compliance'
        }
        
        url = '/api/finances/studentbalance/remove-payment-method/'
        response = self.client.post(url, remove_data, format='json')
        
        # Check all logger calls for sensitive data
        for call in mock_logger.info.call_args_list + mock_logger.error.call_args_list + mock_logger.debug.call_args_list:
            if call:
                log_message = str(call[0][0]) if call[0] else ''
                
                # Log messages should not contain card data
                self.assertNotIn(
                    '4242',
                    log_message,
                    f"Service layer logging exposes card digits: '{log_message}'. "
                    f"Check payment method service logging to mask sensitive data."
                )
                
                self.assertNotIn(
                    'pm_test_error',
                    log_message,
                    f"Service layer logging exposes Stripe payment method ID: '{log_message}'. "
                    f"Check logging to mask Stripe IDs."
                )

    def test_exception_handling_pci_compliance_fails(self):
        """
        Test that exception handling doesn't expose card data.
        
        When exceptions occur during payment operations, the exception
        messages and handling should not leak sensitive information.
        
        Expected to FAIL initially if exceptions expose card data.
        """
        # Mock a service exception that might include payment method data
        with patch('finances.services.payment_method_service.StripeService') as mock_stripe:
            # Configure mock to raise exception with potentially sensitive data
            mock_stripe.return_value.detach_payment_method.side_effect = Exception(
                f"Stripe error for payment method pm_test_error_123 card ****4242"
            )
            
            remove_data = {
                'payment_method_id': self.payment_method.id,
                'reason': 'Testing exception PCI compliance'
            }
            
            url = '/api/finances/studentbalance/remove-payment-method/'
            response = self.client.post(url, remove_data, format='json')
            
            # Exception handling should sanitize error messages
            if response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
                error_data = response.json()
                error_message = str(error_data).lower()
                
                # Should not expose Stripe IDs or card data from exception
                self.assertNotIn(
                    'pm_test_error',
                    error_message,
                    f"Exception handling exposes Stripe payment method ID: {error_data}. "
                    f"Check exception sanitization in error handling."
                )
                
                self.assertNotIn(
                    '4242',
                    error_message,
                    f"Exception handling exposes card digits: {error_data}. "
                    f"Check exception message sanitization."
                )


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class PCIComplianceAdminEndpointTests(APITestCase):
    """
    Test PCI compliance in admin/management endpoints.
    
    These tests validate that administrative endpoints don't
    expose sensitive payment method data inappropriately.
    """

    def setUp(self):
        """Set up test data for admin endpoint tests."""
        self.admin_user = User.objects.create_user(
            email='admin@school.com',
            name='Admin User',
        )
        
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        
        self.payment_method = StoredPaymentMethod.objects.create(
            student=self.student,
            stripe_payment_method_id='pm_admin_test_123',
            stripe_customer_id='cus_admin_test_123',
            card_brand='visa',
            card_last4='4242',  # Should be masked in admin views
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True,
        )
        
        self.client = APIClient()

    def test_admin_transaction_history_pci_compliance_fails(self):
        """
        Test that admin transaction history doesn't expose card data.
        
        Admin transaction history endpoints should show transaction
        information without exposing sensitive payment method details.
        
        Expected to FAIL initially if admin endpoints expose card data.
        """
        # Create transaction with payment method
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('50.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id='pi_admin_test_123',
            metadata={
                'payment_method_id': self.payment_method.stripe_payment_method_id,
                'card_brand': self.payment_method.card_brand,
                'card_last4': self.payment_method.card_last4  # PCI violation in metadata
            }
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Test admin transaction history endpoint
        url = '/api/finances/admin/payments/transactions/'
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            response_json = json.dumps(data)
            
            # Admin endpoints should not expose raw card data
            self.assertNotRegex(
                response_json,
                r'"card_last4":\s*"?\d{4}"?',
                f"Admin transaction history exposes raw card_last4: {response_json}. "
                f"Check admin serializers for proper data masking."
            )
            
            # Check metadata for card data exposure
            self.assertNotIn(
                '4242',
                response_json,
                f"Admin transaction history exposes card digits in metadata: {response_json}. "
                f"Check metadata sanitization in admin endpoints."
            )

    def test_admin_student_analytics_pci_compliance_fails(self):
        """
        Test that admin student analytics don't expose card data.
        
        Student analytics might include payment method information
        but should not expose sensitive card details.
        
        Expected to FAIL initially if analytics expose card data.
        """
        self.client.force_authenticate(user=self.admin_user)
        
        # Test admin student analytics endpoint
        url = f'/api/finances/admin/students/{self.student.id}/analytics/'
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            response_json = json.dumps(data)
            
            # Analytics should not include raw payment method data
            sensitive_fields = [
                'card_last4', 'stripe_payment_method_id', 'stripe_customer_id'
            ]
            
            for field in sensitive_fields:
                self.assertNotIn(
                    field,
                    response_json,
                    f"Admin student analytics exposes sensitive field '{field}': {response_json}. "
                    f"Check analytics data sanitization."
                )
            
            # Check for card digit patterns
            import re
            card_patterns = re.findall(r'\b\d{4}\b', response_json)
            potential_card_digits = [p for p in card_patterns if p.startswith(('4', '5', '6'))]
            
            self.assertEqual(
                len(potential_card_digits), 0,
                f"Admin analytics contains potential card digits: {potential_card_digits}. "
                f"Check analytics data for card data leakage."
            )

    def test_admin_system_health_pci_compliance_fails(self):
        """
        Test that admin system health endpoints don't expose card data.
        
        System health checks might include database samples or
        debugging information that could leak payment data.
        
        Expected to FAIL initially if health checks expose card data.
        """
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api/finances/admin/system/health/'
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            response_json = json.dumps(data)
            
            # Health check should not include payment method samples
            health_violations = [
                'pm_test_',  # Stripe payment method IDs
                'cus_test_', # Stripe customer IDs  
                '4242',      # Card digits
                'card_last4', # Field names
                'stripe_payment_method_id'
            ]
            
            for violation in health_violations:
                self.assertNotIn(
                    violation,
                    response_json,
                    f"System health check exposes payment data: '{violation}'. "
                    f"Response: {response_json}. Check health check data sanitization."
                )


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class PCIComplianceBulkOperationTests(APITestCase):
    """
    Test PCI compliance in bulk operations and batch processing.
    
    These tests validate that bulk operations don't inadvertently
    expose payment method data in batch responses.
    """

    def setUp(self):
        """Set up test data for bulk operation tests."""
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        
        # Create multiple payment methods
        self.payment_methods = []
        for i in range(3):
            pm = StoredPaymentMethod.objects.create(
                student=self.student,
                stripe_payment_method_id=f'pm_bulk_test_{i}',
                stripe_customer_id=f'cus_bulk_test_{i}',
                card_brand='visa' if i % 2 == 0 else 'mastercard',
                card_last4=f'424{i}',  # Different last4 for each
                card_exp_month=12,
                card_exp_year=2025 + i,
                is_default=(i == 0),
                is_active=True,
            )
            self.payment_methods.append(pm)
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)

    def test_bulk_payment_method_operations_pci_compliance_fails(self):
        """
        Test that bulk payment method operations don't expose card data.
        
        Bulk operations might return summary information that
        inadvertently includes sensitive payment method details.
        
        Expected to FAIL initially if bulk operations expose card data.
        """
        # Test bulk deactivation (if supported)
        bulk_data = {
            'payment_method_ids': [pm.id for pm in self.payment_methods],
            'operation': 'deactivate',
            'reason': 'Bulk PCI compliance test'
        }
        
        url = '/api/finances/studentbalance/bulk-payment-methods/'
        response = self.client.post(url, bulk_data, format='json')
        
        # Check response for card data exposure
        if response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]:
            data = response.json()
            response_json = json.dumps(data)
            
            # Bulk response should not contain card data
            for pm in self.payment_methods:
                self.assertNotIn(
                    pm.card_last4,
                    response_json,
                    f"Bulk operation response contains card_last4 '{pm.card_last4}': {response_json}. "
                    f"Check bulk operation response sanitization."
                )
                
                self.assertNotIn(
                    pm.stripe_payment_method_id,
                    response_json,
                    f"Bulk operation response contains Stripe PM ID '{pm.stripe_payment_method_id}': {response_json}. "
                    f"Check bulk response for Stripe ID exposure."
                )

    def test_payment_method_list_pagination_pci_compliance_fails(self):
        """
        Test that paginated payment method lists don't expose card data.
        
        Paginated responses might include metadata or debugging
        information that could leak sensitive data.
        
        Expected to FAIL initially if pagination exposes card data.
        """
        url = '/api/finances/studentbalance/payment-methods/?limit=2'
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            response_json = json.dumps(data)
            
            # Check pagination metadata for data leakage
            pagination_fields = ['count', 'next', 'previous', 'results']
            
            for field in pagination_fields:
                if field in data:
                    field_content = json.dumps(data[field])
                    
                    # Should not contain raw card digits
                    import re
                    card_digits = re.findall(r'\b\d{4}\b', field_content)
                    card_like_digits = [d for d in card_digits if d.startswith(('4', '5', '6'))]
                    
                    self.assertEqual(
                        len(card_like_digits), 0,
                        f"Pagination field '{field}' contains potential card digits: {card_like_digits}. "
                        f"Field content: {field_content}"
                    )

    def test_concurrent_payment_operations_pci_compliance_fails(self):
        """
        Test that concurrent payment operations don't expose card data.
        
        Race conditions or concurrent operations might lead to
        data exposure through error messages or logging.
        
        Expected to FAIL initially if concurrent operations expose card data.
        """
        # Simulate concurrent removal operations
        remove_data = {
            'payment_method_id': self.payment_methods[0].id,
            'reason': 'Concurrent operation test'
        }
        
        url = '/api/finances/studentbalance/remove-payment-method/'
        
        # Make multiple concurrent requests
        responses = []
        for _ in range(3):
            response = self.client.post(url, remove_data, format='json')
            responses.append(response)
        
        # Check all responses for card data exposure
        for i, response in enumerate(responses):
            with self.subTest(request_number=i):
                response_content = response.content.decode('utf-8')
                
                # Concurrent responses should not expose card data
                self.assertNotIn(
                    '4240',  # card_last4 from first payment method
                    response_content,
                    f"Concurrent request {i} exposes card data: {response_content}. "
                    f"Check concurrent operation handling for data leakage."
                )
                
                # Should not expose Stripe IDs in error handling
                self.assertNotIn(
                    'pm_bulk_test_0',
                    response_content,
                    f"Concurrent request {i} exposes Stripe PM ID: {response_content}. "
                    f"Check concurrent error handling sanitization."
                )