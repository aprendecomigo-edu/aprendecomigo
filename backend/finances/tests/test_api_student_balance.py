"""
Consolidated test suite for Student Balance API endpoints.

This module contains focused tests for:
- Student account balance queries and management
- Hour consumption tracking and validation
- Purchase history and transaction queries
- Balance calculation accuracy
- Security and permission validation

Focuses on business logic validation rather than framework behavior.
"""

import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import School, TeacherProfile
from finances.models import (
    ClassSession,
    HourConsumption,
    PlanType,
    PricingPlan,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)
from finances.tests.base import FinanceBaseTestCase
from finances.tests.stripe_test_utils import comprehensive_stripe_mocks_decorator

User = get_user_model()


@comprehensive_stripe_mocks_decorator(apply_to_class=True)
class StudentBalanceAPITestCase(FinanceBaseTestCase, APITestCase):
    """Base test case with common setup for student balance API tests."""

    def setUp(self):
        """Set up test data common to all student balance API tests."""
        super().setUp()
        
        # Use existing fixtures from base class
        # Update the existing student account balance with our test values
        self.student_balance = self.student_account_balance
        self.student_balance.hours_purchased = Decimal("50.00")
        self.student_balance.hours_consumed = Decimal("0.00")
        self.student_balance.balance_amount = Decimal("300.00")
        self.student_balance.save()
        
        # Create another student for testing access controls
        self.other_student = User.objects.create_user(
            email="other@example.com",
            name="Other Student",
            password="testpass123"
        )

        # Create test transactions using existing pricing plan
        self.completed_transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("150.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_123",
            expires_at=timezone.now() + timezone.timedelta(days=30),
            metadata={"plan_id": self.pricing_plan.id}
        )

        self.expired_transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_expired",
            expires_at=timezone.now() - timezone.timedelta(days=5),
            metadata={"plan_id": self.pricing_plan.id}
        )

        # Delete existing hour consumption from base class to start fresh
        if hasattr(self, 'hour_consumption') and self.hour_consumption:
            self.hour_consumption.delete()
        
        # Create a new hour consumption record to trigger balance update
        self.hour_consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.completed_transaction,
            hours_consumed=Decimal("1.5"),
            hours_originally_reserved=Decimal("2.0")
        )

    def authenticate_as_student(self):
        """Authenticate client as the test student."""
        self.client.force_authenticate(user=self.student_user)

    def authenticate_as_admin(self):
        """Authenticate client as admin."""
        self.client.force_authenticate(user=self.admin_user)
        
    def authenticate_as_other_student(self):
        """Authenticate client as the other student."""
        self.client.force_authenticate(user=self.other_student)


class StudentBalanceSummaryAPITests(StudentBalanceAPITestCase):
    """Test cases for student balance summary endpoint."""

    def test_get_balance_summary_authenticated_user(self):
        """Test authenticated user can view their balance summary with correct calculations."""
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-summary')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify response structure and critical data
        self.assertIn('student_info', data)
        self.assertIn('balance_summary', data)
        self.assertIn('package_status', data)
        
        # Verify balance calculations include consumption
        balance_summary = data['balance_summary']
        self.assertEqual(Decimal(str(balance_summary['hours_purchased'])), Decimal("50.00"))
        self.assertEqual(Decimal(str(balance_summary['hours_consumed'])), Decimal("1.50"))
        self.assertEqual(Decimal(str(balance_summary['remaining_hours'])), Decimal("48.50"))
        
        # Verify package status distinguishes active vs expired
        package_status = data['package_status']
        self.assertIn('active_packages', package_status)
        self.assertIn('expired_packages', package_status)
        self.assertGreater(len(package_status['expired_packages']), 0)

    def test_admin_can_view_any_student_balance(self):
        """Test admin can view any student's balance using email parameter."""
        self.authenticate_as_admin()
        url = reverse('finances:studentbalance-summary')
        
        response = self.client.get(url, {'email': self.student_user.email})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['student_info']['email'], self.student_user.email)

    def test_students_cannot_access_other_balances(self):
        """Test students cannot access other students' balances."""
        self.authenticate_as_other_student()
        url = reverse('finances:studentbalance-summary')
        
        response = self.client.get(url, {'email': self.student_user.email})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_balance_with_no_account_record(self):
        """Test response when student has no balance record returns zeros."""
        new_student = User.objects.create_user(
            email="newstudent@example.com",
            name="New Student",
            password="testpass123"
        )
        self.client.force_authenticate(user=new_student)
        url = reverse('finances:studentbalance-summary')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        balance_summary = response.json()['balance_summary']
        self.assertEqual(Decimal(str(balance_summary['balance_amount'])), Decimal("0.00"))

    def test_upcoming_expirations_within_week(self):
        """Test upcoming expirations correctly identifies packages expiring soon."""
        # Create package expiring in 5 days
        PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_soon",
            expires_at=timezone.now() + timezone.timedelta(days=5),
            metadata={"plan_id": self.pricing_plan.id, "hours_included": "10.0"}
        )
        
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-summary')
        
        response = self.client.get(url)
        upcoming = response.json()['upcoming_expirations']
        
        self.assertGreater(len(upcoming), 0)
        # Find the soon-expiring package
        soon_expiring = next((item for item in upcoming if item['days_until_expiry'] <= 7), None)
        self.assertIsNotNone(soon_expiring)


class StudentBalanceHistoryAPITests(StudentBalanceAPITestCase):
    """Test cases for student balance transaction history endpoint."""

    def test_get_transaction_history_with_pagination(self):
        """Test transaction history returns paginated results with proper structure."""
        # Create multiple transactions for pagination
        for i in range(15):
            PurchaseTransaction.objects.create(
                student=self.student_user,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal("50.00"),
                payment_status=TransactionPaymentStatus.COMPLETED,
                stripe_payment_intent_id=f"pi_test_{i}",
                expires_at=timezone.now() + timezone.timedelta(days=30)
            )
        
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-history')
        
        response = self.client.get(url, {'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify pagination structure
        self.assertIn('count', data)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 10)
        self.assertIsNotNone(data.get('next'))

    def test_filter_by_payment_status(self):
        """Test filtering transaction history by payment status."""
        # Create pending transaction
        PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("150.00"),
            payment_status=TransactionPaymentStatus.PENDING,
            stripe_payment_intent_id="pi_test_pending"
        )
        
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-history')
        
        # Filter by completed status
        response = self.client.get(url, {'payment_status': 'completed'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for transaction in response.json()['results']:
            self.assertEqual(transaction['payment_status'], 'completed')

    def test_filter_by_transaction_type(self):
        """Test filtering by transaction type."""
        # Create subscription transaction
        PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal("200.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_sub"
        )
        
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-history')
        
        response = self.client.get(url, {'transaction_type': 'subscription'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for transaction in response.json()['results']:
            self.assertEqual(transaction['transaction_type'], 'subscription')


class StudentBalancePurchasesAPITests(StudentBalanceAPITestCase):
    """Test cases for student balance purchases endpoint with consumption details."""

    def test_get_purchases_with_consumption_details(self):
        """Test purchase history includes accurate consumption details and remaining hours."""
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-purchases')
        
        response = self.client.get(url, {'include_consumption': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Find purchase with consumption
        purchase = next(
            (p for p in data['results'] if p['id'] == self.completed_transaction.id),
            None
        )
        
        self.assertIsNotNone(purchase)
        self.assertIn('consumption_details', purchase)
        self.assertGreater(len(purchase['consumption_details']), 0)
        
        # Verify consumption record structure
        consumption = purchase['consumption_details'][0]
        required_fields = ['hours_consumed', 'hours_originally_reserved', 'consumed_at']
        for field in required_fields:
            self.assertIn(field, consumption)

    def test_hours_remaining_calculation_accuracy(self):
        """Test that hours remaining calculation is accurate per purchase."""
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-purchases')
        
        response = self.client.get(url, {'include_consumption': 'true'})
        purchase = next(
            (p for p in response.json()['results'] if p['id'] == self.completed_transaction.id),
            None
        )
        
        if purchase and purchase.get('plan_details'):
            plan_hours = Decimal(str(purchase['plan_details']['hours_included']))
            consumed_hours = sum(
                Decimal(str(c['hours_consumed'])) for c in purchase['consumption_details']
            )
            expected_remaining = plan_hours - consumed_hours
            self.assertEqual(Decimal(str(purchase['hours_remaining'])), expected_remaining)

    def test_filter_active_packages_only(self):
        """Test filtering to show only active (non-expired) packages."""
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-purchases')
        
        response = self.client.get(url, {'active_only': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for purchase in response.json()['results']:
            self.assertFalse(purchase.get('is_expired', False))


class StudentBalanceSecurityTests(StudentBalanceAPITestCase):
    """Security and permission tests for student balance API."""

    def test_unauthenticated_access_denied(self):
        """Test unauthenticated requests are properly denied."""
        endpoints = [
            reverse('finances:studentbalance-summary'),
            reverse('finances:studentbalance-history'),
            reverse('finances:studentbalance-purchases'),
        ]
        
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_email_parameter_validation(self):
        """Test proper validation of email parameter format."""
        self.authenticate_as_admin()
        url = reverse('finances:studentbalance-summary')
        
        response = self.client.get(url, {'email': 'invalid-email-format'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sql_injection_protection(self):
        """Test protection against SQL injection attempts."""
        self.authenticate_as_admin()
        url = reverse('finances:studentbalance-summary')
        
        malicious_emails = [
            "'; DROP TABLE accounts_customuser; --",
            "admin@test.com' OR '1'='1",
        ]
        
        for malicious_email in malicious_emails:
            response = self.client.get(url, {'email': malicious_email})
            # Should return error, not crash
            self.assertIn(response.status_code, [
                status.HTTP_404_NOT_FOUND, 
                status.HTTP_400_BAD_REQUEST
            ])


class StudentBalanceDataIntegrityTests(StudentBalanceAPITestCase):
    """Data integrity and edge case tests for balance calculations."""

    def test_balance_with_negative_hours_overdraft(self):
        """Test balance display when student has negative hours (overdraft scenario)."""
        # Update balance to show overconsumption
        self.student_balance.hours_consumed = Decimal("60.00")  # More than purchased
        self.student_balance.save()
        
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-summary')
        
        response = self.client.get(url)
        balance_summary = response.json()['balance_summary']
        
        remaining_hours = Decimal(str(balance_summary['remaining_hours']))
        self.assertLess(remaining_hours, Decimal("0.00"))  # Should show negative

    def test_expired_packages_excluded_from_active_hours(self):
        """Test expired packages don't contribute to available hours."""
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-summary')
        
        response = self.client.get(url)
        package_status = response.json()['package_status']
        
        # Should have expired packages listed separately
        self.assertIn('expired_packages', package_status)
        expired_package = next(
            (p for p in package_status['expired_packages'] 
             if p['transaction_id'] == self.expired_transaction.id),
            None
        )
        self.assertIsNotNone(expired_package)
        self.assertTrue(expired_package['is_expired'])

    def test_subscription_without_expiry_handling(self):
        """Test proper handling of subscription transactions without expiry dates."""
        # Create subscription transaction
        subscription = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal("200.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_subscription",
            expires_at=None  # Subscriptions don't expire
        )
        
        self.authenticate_as_student()
        url = reverse('finances:studentbalance-purchases')
        
        response = self.client.get(url)
        purchase = next(
            (p for p in response.json()['results'] if p['id'] == subscription.id),
            None
        )
        
        self.assertIsNotNone(purchase)
        self.assertIsNone(purchase['expires_at'])
        self.assertFalse(purchase.get('is_expired', True))

    def test_empty_consumption_history_handling(self):
        """Test graceful handling when student has purchases but no consumption."""
        # Create new student with purchases but no consumption
        new_student = User.objects.create_user(
            email="noconsumption@example.com",
            name="No Consumption Student",
            password="testpass123"
        )
        
        StudentAccountBalance.objects.create(
            student=new_student,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("0.00"),
            balance_amount=Decimal("150.00")
        )
        
        PurchaseTransaction.objects.create(
            student=new_student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("150.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_no_consumption"
        )
        
        self.client.force_authenticate(user=new_student)
        url = reverse('finances:studentbalance-purchases')
        
        response = self.client.get(url, {'include_consumption': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        purchase = response.json()['results'][0]
        self.assertEqual(len(purchase['consumption_details']), 0)
