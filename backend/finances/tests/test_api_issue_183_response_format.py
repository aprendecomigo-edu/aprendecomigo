"""
API Tests for Issue #183 - API Response Format Issues (10-15 failures expected)

These tests validate consistent API response formatting across different scenarios:
- Error response content-type mismatches (expecting application/json)
- Missing fields in edge case API responses  
- Inconsistent error message formats in API responses
- JSON vs HTML responses in error scenarios
- Standardized error response structure

These tests will FAIL initially (TDD red state) and should pass after implementing
the response format consistency improvements.
"""

import json
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock

from accounts.models import School
from finances.models import (
    StoredPaymentMethod, StudentAccountBalance, PricingPlan, PurchaseTransaction,
    TransactionType, TransactionPaymentStatus
)
from common.test_base import BaseAPITestCase

User = get_user_model()


class APIResponseFormatConsistencyTests(BaseAPITestCase):
    """
    Test API response format consistency for Issue #183.
    
    These tests validate that all API endpoints return consistent JSON responses
    with proper content-types, standardized error structures, and complete field sets.
    """
    
    def setUp(self):
        """Set up test data for response format tests."""
        super().setUp()
        self.client = APIClient()
        
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            address="123 Test St"
        )
        
        # Create student user
        self.student_user = User.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        # Create student account balance
        StudentAccountBalance.objects.create(
            student=self.student_user,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('2.00'),
            balance_amount=Decimal('50.00')
        )
        
        # Create pricing plan
        self.pricing_plan = PricingPlan.objects.create(
            school=self.school,
            name="Basic Plan",
            hours=10,
            price=Decimal('100.00'),
            is_active=True
        )

    def test_error_responses_have_json_content_type(self):
        """
        Test that error responses return proper JSON content-type.
        
        Issue: Some error responses return HTML or have mismatched content-types
        Expected: All API errors should return 'application/json'
        This test will FAIL initially.
        """
        # Test unauthenticated request - should return JSON error
        self.client.force_authenticate(user=None)
        url = "/api/student-balance/payment-methods/"
        response = self.client.get(url)
        
        # CRITICAL: This will FAIL if response is HTML instead of JSON
        self.assertEqual(
            response['Content-Type'], 
            'application/json',
            f"Error response should have JSON content-type but got '{response['Content-Type']}'"
        )
        
        # Should be valid JSON
        try:
            response_data = response.json()
        except (ValueError, json.JSONDecodeError) as e:
            self.fail(f"Error response should be valid JSON but got parse error: {e}")
        
        # Should have standardized error structure
        self.assertIn('error', response_data, "Error response should contain 'error' field")
        
    def test_validation_errors_standardized_format(self):
        """
        Test that validation errors follow standardized format.
        
        Issue: Inconsistent validation error formats across endpoints
        Expected: Consistent error structure with field-specific errors
        This test will FAIL initially.
        """
        self.client.force_authenticate(user=self.student_user)
        
        # Test invalid payment method creation
        url = "/api/student-balance/payment-methods/"
        invalid_data = {
            "stripe_payment_method_id": "invalid_format",  # Should start with 'pm_'
            "is_default": "not_a_boolean"  # Invalid boolean
        }
        
        response = self.client.post(url, invalid_data, format='json')
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Should have JSON content-type
        self.assertEqual(
            response['Content-Type'],
            'application/json',
            "Validation error should return JSON content-type"
        )
        
        response_data = response.json()
        
        # CRITICAL: This will FAIL if error structure is inconsistent
        # Expected standardized structure
        expected_fields = ['stripe_payment_method_id', 'is_default']
        for field in expected_fields:
            self.assertIn(
                field, 
                response_data,
                f"Validation error should include field '{field}' in standardized format"
            )
            
        # Each field error should be a list of strings
        for field in expected_fields:
            if field in response_data:
                self.assertIsInstance(
                    response_data[field],
                    list,
                    f"Field '{field}' errors should be a list of strings"
                )

    def test_not_found_errors_consistent_format(self):
        """
        Test that 404 Not Found errors have consistent format.
        
        Issue: Missing fields or inconsistent error messages in 404 responses
        Expected: Standardized 404 error structure
        This test will FAIL initially.
        """
        self.client.force_authenticate(user=self.student_user)
        
        # Test accessing non-existent payment method
        url = "/api/student-balance/payment-methods/99999/"
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Should have JSON content-type
        self.assertEqual(
            response['Content-Type'],
            'application/json',
            "404 error should return JSON content-type"
        )
        
        response_data = response.json()
        
        # CRITICAL: This will FAIL if 404 structure is inconsistent
        required_fields = ['error']  # At minimum should have error field
        for field in required_fields:
            self.assertIn(
                field,
                response_data,
                f"404 error should include '{field}' field in response"
            )
            
        # Error message should be string and descriptive
        if 'error' in response_data:
            self.assertIsInstance(response_data['error'], str)
            self.assertTrue(
                len(response_data['error']) > 0,
                "Error message should not be empty"
            )

    def test_permission_denied_errors_consistent_format(self):
        """
        Test that permission denied errors have consistent format.
        
        Issue: Permission errors may return HTML or inconsistent JSON
        Expected: Standardized permission error structure  
        This test will FAIL initially.
        """
        # Create another user who shouldn't have access
        other_user = User.objects.create_user(
            email="other@test.com",
            name="Other User"
        )
        
        # Create payment method for original user
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_card",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="4242", 
            card_exp_month=12,
            card_exp_year=2025,
            is_default=True,
            is_active=True
        )
        
        # Try to access as different user (should be forbidden)
        self.client.force_authenticate(user=other_user)
        url = f"/api/student-balance/payment-methods/{payment_method.id}/"
        response = self.client.delete(url)
        
        # Should return 403 or 404 (depending on implementation)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        
        # CRITICAL: Should have JSON content-type, not HTML
        self.assertEqual(
            response['Content-Type'],
            'application/json',
            f"Permission error should return JSON, not HTML. Got '{response['Content-Type']}'"
        )
        
        response_data = response.json()
        self.assertIn('error', response_data, "Permission error should contain 'error' field")

    @patch('finances.services.payment_method_service.StripeService')
    def test_stripe_error_responses_consistent_format(self, mock_stripe_service):
        """
        Test that Stripe integration errors return consistent JSON format.
        
        Issue: External service errors may return inconsistent formats
        Expected: Standardized error structure even for Stripe errors
        This test will FAIL initially.
        """
        self.client.force_authenticate(user=self.student_user)
        
        # Mock Stripe service to return error
        mock_instance = MagicMock()
        mock_stripe_service.return_value = mock_instance
        mock_instance.get_payment_method.return_value = {
            'success': False,
            'error_type': 'stripe_error',
            'message': 'Payment method not found in Stripe'
        }
        
        url = "/api/student-balance/payment-methods/"
        data = {
            "stripe_payment_method_id": "pm_test_nonexistent",
            "is_default": False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should return appropriate error status
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST, 
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ])
        
        # CRITICAL: Should have JSON content-type even for Stripe errors
        self.assertEqual(
            response['Content-Type'],
            'application/json', 
            "Stripe error responses should return JSON content-type"
        )
        
        response_data = response.json()
        
        # Should have standardized error structure
        self.assertIn('error', response_data, "Stripe error should contain 'error' field")
        
        # Error message should be string
        if 'error' in response_data:
            self.assertIsInstance(response_data['error'], str)

    def test_successful_responses_complete_field_sets(self):
        """
        Test that successful responses include all expected fields.
        
        Issue: Missing fields in edge case API responses
        Expected: Complete field sets in successful responses
        This test will FAIL initially if fields are missing.
        """
        self.client.force_authenticate(user=self.student_user)
        
        # Create payment method
        payment_method = StoredPaymentMethod.objects.create(
            student=self.student_user,
            stripe_payment_method_id="pm_test_complete",
            stripe_customer_id="cus_test_customer",
            card_brand="visa",
            card_last4="4242",
            card_exp_month=12, 
            card_exp_year=2025,
            is_default=True,
            is_active=True
        )
        
        # Test GET payment methods response
        url = "/api/student-balance/payment-methods/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # CRITICAL: Required top-level fields
        required_top_level = ['payment_methods', 'success']
        for field in required_top_level:
            self.assertIn(
                field,
                response_data,
                f"Successful payment methods response missing required field '{field}'"
            )
        
        payment_methods = response_data['payment_methods']
        self.assertIsInstance(payment_methods, list)
        self.assertGreater(len(payment_methods), 0, "Should return at least one payment method")
        
        # CRITICAL: Each payment method should have complete field set
        pm = payment_methods[0]
        required_pm_fields = [
            'id', 'card_brand', 'card_display', 'is_default', 'is_active', 
            'is_expired', 'student_name', 'created_at', 'updated_at'
        ]
        
        for field in required_pm_fields:
            self.assertIn(
                field,
                pm,
                f"Payment method response missing required field '{field}'"
            )

    def test_edge_case_empty_response_format(self):
        """
        Test that empty result responses maintain consistent format.
        
        Issue: Empty responses may return inconsistent structure
        Expected: Consistent format even when no results
        This test will FAIL initially.
        """
        # Create user with no payment methods
        empty_user = User.objects.create_user(
            email="empty@test.com",
            name="Empty User"
        )
        
        # Create balance for the user
        StudentAccountBalance.objects.create(
            student=empty_user,
            school=self.school,
            balance=Decimal('0.00')
        )
        
        self.client.force_authenticate(user=empty_user)
        
        # Test empty payment methods list
        url = "/api/student-balance/payment-methods/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        response_data = response.json()
        
        # CRITICAL: Should maintain consistent structure even when empty
        self.assertIn('payment_methods', response_data, "Should include 'payment_methods' field even when empty")
        self.assertIn('success', response_data, "Should include 'success' field")
        
        self.assertIsInstance(response_data['payment_methods'], list)
        self.assertEqual(len(response_data['payment_methods']), 0, "Should return empty list")
        self.assertTrue(response_data['success'], "Should indicate success even for empty results")

    def test_malformed_json_request_error_format(self):
        """
        Test error responses for malformed JSON requests.
        
        Issue: Malformed request errors may return HTML or inconsistent format
        Expected: Standardized JSON error response
        This test will FAIL initially.
        """
        self.client.force_authenticate(user=self.student_user)
        
        # Send malformed JSON
        url = "/api/student-balance/payment-methods/"
        malformed_json = '{"stripe_payment_method_id": "pm_test", "invalid": }'
        
        response = self.client.post(
            url,
            data=malformed_json,
            content_type='application/json'
        )
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # CRITICAL: Should return JSON, not HTML error page
        self.assertEqual(
            response['Content-Type'],
            'application/json',
            f"Malformed JSON error should return JSON content-type, got '{response['Content-Type']}'"
        )
        
        # Should be parseable JSON
        try:
            response_data = response.json()
        except (ValueError, json.JSONDecodeError) as e:
            self.fail(f"Malformed JSON error response should be valid JSON: {e}")
        
        # Should have error field
        self.assertIn('error', response_data, "Malformed JSON error should contain 'error' field")

    def test_method_not_allowed_consistent_format(self):
        """
        Test that Method Not Allowed errors return consistent JSON format.
        
        Issue: HTTP method errors may return HTML or inconsistent format  
        Expected: Standardized JSON error response
        This test will FAIL initially.
        """
        self.client.force_authenticate(user=self.student_user)
        
        # Try unsupported method on payment methods endpoint
        url = "/api/student-balance/payment-methods/"
        response = self.client.patch(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # CRITICAL: Should return JSON, not HTML
        self.assertEqual(
            response['Content-Type'],
            'application/json',
            f"Method not allowed should return JSON content-type, got '{response['Content-Type']}'"
        )
        
        response_data = response.json()
        
        # Should have consistent error structure
        self.assertIn('error', response_data, "Method not allowed should contain 'error' field")
        
        # Error should mention allowed methods
        error_msg = response_data['error'].lower()
        self.assertTrue(
            'method' in error_msg or 'allowed' in error_msg,
            f"Error message should mention method/allowed: {response_data['error']}"
        )