"""
DRF Test Utilities for Finances App API Testing.

This module provides reusable utilities and helpers for testing DRF APIs
in the finances app, promoting consistency and reducing code duplication
across test files.

**Key Features:**
- Response structure validation helpers
- Common test data factories
- Authentication helper mixins
- Standard assertion patterns

**Usage Example:**
    from finances.tests.test_api_utils import APITestMixin
    
    class MyAPITest(APITestCase, APITestMixin):
        def test_my_endpoint(self):
            response = self.get_authenticated_response('/api/endpoint/')
            self.assert_successful_response(response)
            self.assert_required_fields(response.data, ['id', 'name', 'amount'])
"""

from decimal import Decimal
from typing import Dict, List, Any

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import School, TeacherProfile
from finances.models import (
    PricingPlan, PlanType, PurchaseTransaction,
    StudentAccountBalance, TransactionPaymentStatus,
    TransactionType
)

User = get_user_model()


class APITestMixin:
    """
    Mixin providing common API testing utilities.
    
    This mixin should be used with APITestCase to provide standardized
    methods for API testing across the finances app.
    """
    
    def assert_successful_response(self, response, expected_status=status.HTTP_200_OK):
        """
        Assert that a response is successful with expected status.
        
        Args:
            response: DRF Response object
            expected_status: Expected HTTP status code (default: 200)
        """
        self.assertEqual(response.status_code, expected_status)
        self.assertIsNotNone(response.data)
    
    def assert_error_response(self, response, expected_status, error_field=None):
        """
        Assert that a response contains an error with expected status.
        
        Args:
            response: DRF Response object
            expected_status: Expected HTTP status code
            error_field: Optional field name that should contain error
        """
        self.assertEqual(response.status_code, expected_status)
        
        if error_field:
            error_data = response.json()
            self.assertIn(error_field, error_data)
    
    def assert_required_fields(self, data: Dict[str, Any], required_fields: List[str]):
        """
        Assert that response data contains all required fields.
        
        Args:
            data: Response data dictionary
            required_fields: List of field names that must be present
        """
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
    
    def assert_pagination_structure(self, data: Dict[str, Any]):
        """
        Assert that response data has proper DRF pagination structure.
        
        Args:
            data: Response data dictionary
            
        Expected Structure:
            {
                "count": 10,
                "next": "http://example.com/api/?page=2",
                "previous": null,
                "results": [...]
            }
        """
        pagination_fields = ['count', 'next', 'previous', 'results']
        for field in pagination_fields:
            self.assertIn(field, data, f"Missing pagination field: {field}")
        
        self.assertIsInstance(data['count'], int)
        self.assertIsInstance(data['results'], list)
    
    def assert_timestamp_format(self, timestamp_str: str):
        """
        Assert that a timestamp string is in valid ISO format.
        
        Args:
            timestamp_str: Timestamp string to validate
        """
        from django.utils.dateparse import parse_datetime
        
        self.assertIsInstance(timestamp_str, str)
        parsed_datetime = parse_datetime(timestamp_str)
        self.assertIsNotNone(parsed_datetime, f"Invalid timestamp format: {timestamp_str}")
    
    def assert_decimal_field(self, value, expected_precision=2):
        """
        Assert that a decimal field is properly formatted.
        
        Args:
            value: Value to check (should be string representation of decimal)
            expected_precision: Expected decimal places (default: 2)
        """
        # DRF typically serializes decimals as strings for precision
        if isinstance(value, str):
            try:
                decimal_value = Decimal(value)
                # Check precision by counting decimal places
                decimal_places = abs(decimal_value.as_tuple().exponent)
                self.assertLessEqual(decimal_places, expected_precision)
            except (ValueError, TypeError):
                self.fail(f"Invalid decimal format: {value}")
        else:
            # Accept numeric types but convert to check precision
            self.assertIsInstance(value, (int, float, Decimal))


class FinancesAPITestDataFactory:
    """
    Factory class for creating consistent test data across finance API tests.
    
    This factory provides methods to create common test objects with
    realistic data, reducing setup code duplication and ensuring consistency.
    """
    
    @staticmethod
    def create_test_student(email="student@test.com", name="Test Student"):
        """Create a test student user."""
        return User.objects.create_user(
            email=email,
            name=name,
            password="testpass123"
        )
    
    @staticmethod
    def create_test_admin(email="admin@test.com", name="Admin User"):
        """Create a test admin user."""
        return User.objects.create_user(
            email=email,
            name=name,
            password="testpass123",
            is_staff=True,
            is_superuser=True
        )
    
    @staticmethod
    def create_test_school(name="Test School"):
        """Create a test school."""
        return School.objects.create(
            name=name,
            contact_email="contact@testschool.com",
            address="123 Test Street"
        )
    
    @staticmethod
    def create_test_teacher(email="teacher@test.com", name="Test Teacher"):
        """Create a test teacher with profile."""
        user = User.objects.create_user(
            email=email,
            name=name,
            password="testpass123"
        )
        
        profile = TeacherProfile.objects.create(
            user=user,
            bio="Experienced test teacher",
            specialty="Mathematics",
            hourly_rate=Decimal("25.00")
        )
        
        return user, profile
    
    @staticmethod
    def create_test_pricing_plan(
        plan_type=PlanType.PACKAGE,
        name="Test Package",
        price=Decimal("100.00"),
        hours=Decimal("10.00")
    ):
        """Create a test pricing plan."""
        return PricingPlan.objects.create(
            name=name,
            description=f"Test {plan_type} plan",
            plan_type=plan_type,
            hours_included=hours,
            price_eur=price,
            validity_days=30 if plan_type == PlanType.PACKAGE else None,
            is_active=True,
            display_order=1
        )
    
    @staticmethod
    def create_test_transaction(
        student,
        transaction_type=TransactionType.PACKAGE,
        amount=Decimal("100.00"),
        status=TransactionPaymentStatus.COMPLETED
    ):
        """Create a test purchase transaction."""
        return PurchaseTransaction.objects.create(
            student=student,
            transaction_type=transaction_type,
            amount=amount,
            payment_status=status,
            stripe_payment_intent_id=f"pi_test_{student.id}_{transaction_type}",
            metadata={
                "plan_name": f"Test {transaction_type}",
                "hours_included": "10.00" if transaction_type == TransactionType.PACKAGE else "20.00"
            }
        )
    
    @staticmethod
    def create_test_student_balance(student, hours_purchased=Decimal("20.00")):
        """Create a test student account balance."""
        return StudentAccountBalance.objects.create(
            student=student,
            hours_purchased=hours_purchased,
            hours_consumed=Decimal("0.00"),
            balance_amount=hours_purchased * Decimal("10.00")  # Assuming 10 EUR per hour
        )


class FinancesAPITestCase(APITestCase, APITestMixin):
    """
    Base test case for finances API tests.
    
    Provides common setup and utilities for testing finance-related APIs.
    Inherits from both APITestCase and APITestMixin for full functionality.
    
    **Usage:**
        class MyFinanceAPITest(FinancesAPITestCase):
            def test_my_endpoint(self):
                response = self.client.get('/api/finances/endpoint/')
                self.assert_successful_response(response)
    """
    
    def setUp(self):
        """Set up common test data."""
        super().setUp()
        
        # Create common test users
        self.student = FinancesAPITestDataFactory.create_test_student()
        self.admin_user = FinancesAPITestDataFactory.create_test_admin()
        self.school = FinancesAPITestDataFactory.create_test_school()
        
        # Create common test data
        self.pricing_plan = FinancesAPITestDataFactory.create_test_pricing_plan()
        self.student_balance = FinancesAPITestDataFactory.create_test_student_balance(
            self.student
        )
    
    def authenticate_as_student(self):
        """Authenticate client as test student."""
        self.client.force_authenticate(user=self.student)
    
    def authenticate_as_admin(self):
        """Authenticate client as admin user."""
        self.client.force_authenticate(user=self.admin_user)
    
    def get_authenticated_response(self, url, user=None, method='GET', data=None):
        """
        Get authenticated API response.
        
        Args:
            url: API endpoint URL
            user: User to authenticate as (default: self.student)
            method: HTTP method (default: GET)
            data: Request data for POST/PUT/PATCH
            
        Returns:
            DRF Response object
        """
        if user is None:
            user = self.student
        
        self.client.force_authenticate(user=user)
        
        if method.upper() == 'GET':
            return self.client.get(url)
        elif method.upper() == 'POST':
            return self.client.post(url, data, format='json')
        elif method.upper() == 'PUT':
            return self.client.put(url, data, format='json')
        elif method.upper() == 'PATCH':
            return self.client.patch(url, data, format='json')
        elif method.upper() == 'DELETE':
            return self.client.delete(url)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")