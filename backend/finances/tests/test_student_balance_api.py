"""
Test cases for Student Account Balance API endpoints.

Following TDD methodology, these tests define all expected behavior
for the student balance API before any implementation.
"""

import json
from decimal import Decimal
from unittest.mock import patch

from accounts.models import CustomUser, School, TeacherProfile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from ..models import (
    ClassSession,
    HourConsumption,
    PlanType,
    PricingPlan,
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)


class StudentBalanceAPITestCase(TestCase):
    """Base test case with common setup for student balance API tests."""

    def setUp(self):
        """Set up test data common to all student balance API tests."""
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            contact_email="test@school.com",
            address="123 Test St"
        )

        # Create test users
        self.student_user = CustomUser.objects.create_user(
            email="student@example.com",
            name="Test Student",
            password="testpass123"
        )

        self.other_student = CustomUser.objects.create_user(
            email="other@example.com",
            name="Other Student",
            password="testpass123"
        )

        self.admin_user = CustomUser.objects.create_user(
            email="admin@example.com",
            name="Admin User",
            password="testpass123",
            is_staff=True
        )

        # Create teacher user and profile
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher@example.com",
            name="Test Teacher",
            password="testpass123"
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user
        )

        # Create student account balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student_user,
            hours_purchased=Decimal("50.00"),
            hours_consumed=Decimal("0.00"),  # Will be updated by HourConsumption
            balance_amount=Decimal("300.00")
        )

        # Create test pricing plans
        self.package_plan = PricingPlan.objects.create(
            name="10 Hour Package",
            description="10 tutoring hours valid for 30 days",
            plan_type=PlanType.PACKAGE,
            hours_included=Decimal("10.00"),
            price_eur=Decimal("150.00"),
            validity_days=30,
            is_active=True
        )

        self.subscription_plan = PricingPlan.objects.create(
            name="Monthly Subscription",
            description="Unlimited hours per month",
            plan_type=PlanType.SUBSCRIPTION,
            hours_included=Decimal("20.00"),
            price_eur=Decimal("200.00"),
            validity_days=None,
            is_active=True
        )

        # Create test transactions
        self.completed_transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("150.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_123",
            expires_at=timezone.now() + timezone.timedelta(days=30),
            metadata={"plan_id": self.package_plan.id}
        )

        self.pending_transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("150.00"),
            payment_status=TransactionPaymentStatus.PENDING,
            stripe_payment_intent_id="pi_test_456",
            expires_at=timezone.now() + timezone.timedelta(days=30),
            metadata={"plan_id": self.package_plan.id}
        )

        # Create expired transaction
        self.expired_transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_expired",
            expires_at=timezone.now() - timezone.timedelta(days=5),
            metadata={"plan_id": self.package_plan.id}
        )

        # Create subscription transaction
        self.subscription_transaction = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal("200.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_sub",
            expires_at=None,
            metadata={"plan_id": self.subscription_plan.id}
        )

        # Create test class session for consumption
        self.class_session = ClassSession.objects.create(
            teacher=self.teacher_profile,
            school=self.school,
            date=timezone.now().date(),
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timezone.timedelta(hours=1)).time(),
            session_type="individual",
            grade_level="10",
            status="completed"
        )
        self.class_session.students.add(self.student_user)

        # Create hour consumption record
        self.hour_consumption = HourConsumption.objects.create(
            student_account=self.student_balance,
            class_session=self.class_session,
            purchase_transaction=self.completed_transaction,
            hours_consumed=Decimal("1.5"),
            hours_originally_reserved=Decimal("2.0")
        )

        self.client = APIClient()

    def authenticate_as_student(self):
        """Authenticate client as the test student."""
        self.client.force_authenticate(user=self.student_user)

    def authenticate_as_admin(self):
        """Authenticate client as admin."""
        self.client.force_authenticate(user=self.admin_user)


class StudentBalanceSummaryAPITests(StudentBalanceAPITestCase):
    """Test cases for /finances/api/student-balance/ endpoint."""

    def test_get_student_balance_authenticated_user(self):
        """Test authenticated user can view their own balance summary."""
        self.authenticate_as_student()
        url = reverse('finances:student-balance-summary')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify response structure and data
        self.assertIn('student_info', data)
        self.assertIn('balance_summary', data)
        self.assertIn('package_status', data)
        self.assertIn('upcoming_expirations', data)
        
        # Verify student info
        student_info = data['student_info']
        self.assertEqual(student_info['id'], self.student_user.id)
        self.assertEqual(student_info['name'], self.student_user.name)
        self.assertEqual(student_info['email'], self.student_user.email)
        
        # Verify balance summary
        balance_summary = data['balance_summary']
        self.assertEqual(Decimal(balance_summary['hours_purchased']), Decimal("50.00"))
        self.assertEqual(Decimal(balance_summary['hours_consumed']), Decimal("1.50"))  # From HourConsumption
        self.assertEqual(Decimal(balance_summary['remaining_hours']), Decimal("48.50"))
        self.assertEqual(Decimal(balance_summary['balance_amount']), Decimal("300.00"))
        
        # Verify package status includes active packages
        package_status = data['package_status']
        self.assertGreater(len(package_status['active_packages']), 0)
        self.assertGreater(len(package_status['expired_packages']), 0)

    def test_get_student_balance_with_email_parameter_authenticated(self):
        """Test authenticated admin can view any student's balance using email parameter."""
        self.authenticate_as_admin()
        url = reverse('finances:student-balance-summary')
        
        response = self.client.get(url, {'email': self.student_user.email})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify it returns the correct student's data
        self.assertEqual(data['student_info']['email'], self.student_user.email)

    def test_get_student_balance_with_email_parameter_unauthenticated(self):
        """Test unauthenticated user cannot access balance with email parameter."""
        url = reverse('finances:student-balance-summary')
        
        response = self.client.get(url, {'email': self.student_user.email})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_student_balance_unauthorized_access(self):
        """Test that students cannot access other students' balances."""
        # Authenticate as other student
        self.client.force_authenticate(user=self.other_student)
        url = reverse('finances:student-balance-summary')
        
        # Try to access main student's balance via email parameter
        response = self.client.get(url, {'email': self.student_user.email})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_student_balance_no_balance_record(self):
        """Test response when student has no balance record."""
        # Create user without balance record
        new_student = CustomUser.objects.create_user(
            email="newstudent@example.com",
            name="New Student",
            password="testpass123"
        )
        self.client.force_authenticate(user=new_student)
        url = reverse('finances:student-balance-summary')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return zero balance
        balance_summary = data['balance_summary']
        self.assertEqual(Decimal(balance_summary['hours_purchased']), Decimal("0.00"))
        self.assertEqual(Decimal(balance_summary['hours_consumed']), Decimal("0.00"))
        self.assertEqual(Decimal(balance_summary['remaining_hours']), Decimal("0.00"))
        self.assertEqual(Decimal(balance_summary['balance_amount']), Decimal("0.00"))

    def test_get_student_balance_nonexistent_email(self):
        """Test error response for nonexistent email parameter."""
        self.authenticate_as_admin()
        url = reverse('finances:student-balance-summary')
        
        response = self.client.get(url, {'email': 'nonexistent@example.com'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_upcoming_expirations_calculation(self):
        """Test that upcoming expirations are correctly calculated."""
        # Create package expiring soon
        soon_expiring = PurchaseTransaction.objects.create(
            student=self.student_user,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            stripe_payment_intent_id="pi_test_soon",
            expires_at=timezone.now() + timezone.timedelta(days=5),
            metadata={"plan_id": self.package_plan.id, "hours_included": "10.0"}
        )
        
        self.authenticate_as_student()
        url = reverse('finances:student-balance-summary')
        
        response = self.client.get(url)
        data = response.json()
        
        upcoming = data['upcoming_expirations']
        self.assertGreater(len(upcoming), 0)
        
        # Find our soon-expiring package
        soon_expiring_item = next(
            (item for item in upcoming if item['transaction_id'] == soon_expiring.id),
            None
        )
        self.assertIsNotNone(soon_expiring_item)
        self.assertLessEqual(soon_expiring_item['days_until_expiry'], 7)


class StudentBalanceHistoryAPITests(StudentBalanceAPITestCase):
    """Test cases for /finances/api/student-balance/history/ endpoint."""

    def test_get_transaction_history_authenticated(self):
        """Test authenticated user can view their transaction history."""
        self.authenticate_as_student()
        url = reverse('finances:student-balance-history')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify pagination structure
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('results', data)
        
        # Verify we have transactions
        self.assertGreater(len(data['results']), 0)
        
        # Verify transaction structure
        transaction = data['results'][0]
        required_fields = [
            'id', 'transaction_type', 'amount', 'payment_status',
            'expires_at', 'created_at', 'metadata', 'is_expired'
        ]
        for field in required_fields:
            self.assertIn(field, transaction)

    def test_get_transaction_history_filtering_by_status(self):
        """Test filtering transaction history by payment status."""
        self.authenticate_as_student()
        url = reverse('finances:student-balance-history')
        
        # Filter by completed status
        response = self.client.get(url, {'payment_status': 'completed'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # All returned transactions should be completed
        for transaction in data['results']:
            self.assertEqual(transaction['payment_status'], 'completed')

    def test_get_transaction_history_filtering_by_type(self):
        """Test filtering transaction history by transaction type."""
        self.authenticate_as_student()
        url = reverse('finances:student-balance-history')
        
        # Filter by package type
        response = self.client.get(url, {'transaction_type': 'package'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # All returned transactions should be packages
        for transaction in data['results']:
            self.assertEqual(transaction['transaction_type'], 'package')

    def test_get_transaction_history_with_email_parameter(self):
        """Test admin can view any student's transaction history."""
        self.authenticate_as_admin()
        url = reverse('finances:student-balance-history')
        
        response = self.client.get(url, {'email': self.student_user.email})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return student's transactions
        self.assertGreater(len(data['results']), 0)

    def test_get_transaction_history_pagination(self):
        """Test transaction history pagination works correctly."""
        # Create additional transactions for pagination testing
        for i in range(25):
            PurchaseTransaction.objects.create(
                student=self.student_user,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal("50.00"),
                payment_status=TransactionPaymentStatus.COMPLETED,
                stripe_payment_intent_id=f"pi_test_pagination_{i}",
                expires_at=timezone.now() + timezone.timedelta(days=30)
            )
        
        self.authenticate_as_student()
        url = reverse('finances:student-balance-history')
        
        response = self.client.get(url, {'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should have exactly 10 results per page
        self.assertEqual(len(data['results']), 10)
        self.assertIsNotNone(data['next'])  # Should have next page


class StudentBalancePurchasesAPITests(StudentBalanceAPITestCase):
    """Test cases for /finances/api/student-balance/purchases/ endpoint."""

    def test_get_purchase_history_authenticated(self):
        """Test authenticated user can view their purchase history."""
        self.authenticate_as_student()
        url = reverse('finances:student-balance-purchases')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify pagination structure
        self.assertIn('count', data)
        self.assertIn('results', data)
        
        # Verify we have purchases
        self.assertGreater(len(data['results']), 0)
        
        # Verify purchase structure includes plan details
        purchase = data['results'][0]
        required_fields = [
            'id', 'transaction_type', 'amount', 'payment_status',
            'expires_at', 'created_at', 'plan_details', 'hours_remaining'
        ]
        for field in required_fields:
            self.assertIn(field, purchase)
        
        # Verify plan details are populated
        plan_details = purchase['plan_details']
        if plan_details:  # Some transactions might not have plan details
            self.assertIn('name', plan_details)
            self.assertIn('hours_included', plan_details)

    def test_get_purchase_history_with_consumption_details(self):
        """Test that purchase history includes consumption details."""
        self.authenticate_as_student()
        url = reverse('finances:student-balance-purchases')
        
        response = self.client.get(url, {'include_consumption': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Find purchase with consumption
        purchase_with_consumption = next(
            (p for p in data['results'] 
             if p['id'] == self.completed_transaction.id),
            None
        )
        
        self.assertIsNotNone(purchase_with_consumption)
        self.assertIn('consumption_details', purchase_with_consumption)
        
        consumption = purchase_with_consumption['consumption_details']
        self.assertGreater(len(consumption), 0)
        
        # Verify consumption record structure
        consumption_record = consumption[0]
        consumption_fields = [
            'id', 'hours_consumed', 'hours_originally_reserved',
            'consumed_at', 'class_session_id', 'is_refunded'
        ]
        for field in consumption_fields:
            self.assertIn(field, consumption_record)

    def test_get_purchase_history_filtering_by_active_status(self):
        """Test filtering purchases by active/expired status."""
        self.authenticate_as_student()
        url = reverse('finances:student-balance-purchases')
        
        # Filter active packages only
        response = self.client.get(url, {'active_only': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # All returned purchases should be active (not expired)
        for purchase in data['results']:
            self.assertFalse(purchase.get('is_expired', False))

    def test_get_purchase_history_hours_remaining_calculation(self):
        """Test that hours remaining is correctly calculated per purchase."""
        self.authenticate_as_student()
        url = reverse('finances:student-balance-purchases')
        
        response = self.client.get(url, {'include_consumption': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Find our transaction with consumption
        purchase = next(
            (p for p in data['results'] 
             if p['id'] == self.completed_transaction.id),
            None
        )
        
        self.assertIsNotNone(purchase)
        
        # Verify hours_remaining calculation
        if purchase['plan_details']:
            plan_hours = Decimal(purchase['plan_details']['hours_included'])
            consumed_hours = sum(
                Decimal(c['hours_consumed']) 
                for c in purchase['consumption_details']
            )
            expected_remaining = plan_hours - consumed_hours
            self.assertEqual(
                Decimal(purchase['hours_remaining']), 
                expected_remaining
            )


class StudentBalanceSecurityTests(StudentBalanceAPITestCase):
    """Security and permission tests for student balance API."""

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        endpoints = [
            reverse('finances:student-balance-summary'),
            reverse('finances:student-balance-history'),
            reverse('finances:student-balance-purchases'),
        ]
        
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_access_other_student_data(self):
        """Test that students cannot access other students' data."""
        # Authenticate as other student
        self.client.force_authenticate(user=self.other_student)
        
        endpoints_with_email = [
            reverse('finances:student-balance-summary'),
            reverse('finances:student-balance-history'),
            reverse('finances:student-balance-purchases'),
        ]
        
        for url in endpoints_with_email:
            response = self.client.get(url, {'email': self.student_user.email})
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_any_student_data(self):
        """Test that admin users can access any student's data."""
        self.authenticate_as_admin()
        
        endpoints_with_email = [
            reverse('finances:student-balance-summary'),
            reverse('finances:student-balance-history'),
            reverse('finances:student-balance-purchases'),
        ]
        
        for url in endpoints_with_email:
            response = self.client.get(url, {'email': self.student_user.email})
            self.assertIn(response.status_code, [status.HTTP_200_OK])




class StudentBalancePerformanceTests(StudentBalanceAPITestCase):
    """Performance-related tests for student balance API."""




class StudentBalanceDataIntegrityTests(StudentBalanceAPITestCase):
    """Data integrity and edge case tests."""

    def test_balance_with_negative_hours(self):
        """Test balance display when student has negative hours (overdraft)."""
        # Create student with negative balance
        self.student_balance.hours_consumed = Decimal("60.00")  # More than purchased
        self.student_balance.save()
        
        self.authenticate_as_student()
        url = reverse('finances:student-balance-summary')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        balance_summary = data['balance_summary']
        remaining_hours = Decimal(balance_summary['remaining_hours'])
        self.assertLess(remaining_hours, Decimal("0.00"))  # Should be negative

    def test_expired_packages_not_counted_in_active_hours(self):
        """Test that expired packages are not counted in available hours."""
        self.authenticate_as_student()
        url = reverse('finances:student-balance-summary')
        
        response = self.client.get(url)
        data = response.json()
        
        # Expired packages should be listed separately
        package_status = data['package_status']
        self.assertIn('expired_packages', package_status)
        self.assertGreater(len(package_status['expired_packages']), 0)
        
        # Find our expired package
        expired_package = next(
            (p for p in package_status['expired_packages'] 
             if p['transaction_id'] == self.expired_transaction.id),
            None
        )
        self.assertIsNotNone(expired_package)
        self.assertTrue(expired_package['is_expired'])

    def test_subscription_without_expiry_date(self):
        """Test handling of subscription transactions without expiry dates."""
        self.authenticate_as_student()
        url = reverse('finances:student-balance-purchases')
        
        response = self.client.get(url)
        data = response.json()
        
        # Find subscription transaction
        subscription = next(
            (p for p in data['results'] 
             if p['id'] == self.subscription_transaction.id),
            None
        )
        
        self.assertIsNotNone(subscription)
        self.assertIsNone(subscription['expires_at'])
        self.assertFalse(subscription.get('is_expired', True))

    def test_empty_consumption_history(self):
        """Test handling when student has no consumption history."""
        # Create new student with purchases but no consumption
        new_student = CustomUser.objects.create_user(
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
            stripe_payment_intent_id="pi_test_no_consumption",
            expires_at=timezone.now() + timezone.timedelta(days=30)
        )
        
        self.client.force_authenticate(user=new_student)
        url = reverse('finances:student-balance-purchases')
        
        response = self.client.get(url, {'include_consumption': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should handle empty consumption gracefully
        self.assertGreater(len(data['results']), 0)
        purchase = data['results'][0]
        self.assertEqual(len(purchase['consumption_details']), 0)
        
        # Hours remaining should equal hours included (converted to strings for comparison)
        if purchase['plan_details'] and purchase['plan_details']['hours_included']:
            self.assertEqual(
                str(purchase['hours_remaining']),
                str(purchase['plan_details']['hours_included'])
            )