"""
Test suite for Package Expiration Management functionality.

Following TDD methodology, these tests define the expected behavior for:
- Automatic package expiration detection and processing
- Manual expiration management for admins
- Student notification system for upcoming expirations
- Package extension and renewal workflows
- Bulk expiration processing efficiency
- Grace periods and extension policies
- Comprehensive audit logging
- Integration with existing hour consumption and balance systems

Tests follow GitHub Issue #33: "Create Package Expiration Management"
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from accounts.models import CustomUser, School
from finances.models import (
    PurchaseTransaction,
    StudentAccountBalance,
    HourConsumption,
    TransactionPaymentStatus,
    TransactionType,
    ClassSession,
    SessionStatus,
)
from finances.services.package_expiration_service import (
    PackageExpirationService,
    ExpirationResult,
    NotificationResult,
)

User = get_user_model()


class PackageExpirationDetectionTests(TestCase):
    """Tests for package expiration detection logic."""

    def setUp(self):
        """Set up test data."""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St",
            contact_email="test@school.com"
        )
        
        # Create student
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            phone_number="+1234567890"
        )
        
        # Create student account balance
        self.balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('150.00')
        )
        
        # Create base datetime for testing
        self.now = timezone.now()

    def test_detect_expired_packages_basic(self):
        """Test basic expired package detection."""
        # Create expired package
        expired_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=1)
        )
        
        # Create active package
        active_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('150.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now + timedelta(days=30)
        )
        
        # Test detection
        expired_packages = PackageExpirationService.get_expired_packages()
        
        self.assertEqual(len(expired_packages), 1)
        self.assertEqual(expired_packages[0].id, expired_transaction.id)

    def test_detect_packages_expiring_soon(self):
        """Test detection of packages expiring within specified timeframe."""
        # Create package expiring in 2 days
        soon_expiring = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now + timedelta(days=2)
        )
        
        # Create package expiring in 10 days
        later_expiring = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('150.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now + timedelta(days=10)
        )
        
        # Test detection with 3-day window
        expiring_soon = PackageExpirationService.get_packages_expiring_soon(days_ahead=3)
        
        self.assertEqual(len(expiring_soon), 1)
        self.assertEqual(expiring_soon[0].id, soon_expiring.id)
        
        # Test detection with 15-day window
        expiring_soon_wide = PackageExpirationService.get_packages_expiring_soon(days_ahead=15)
        
        self.assertEqual(len(expiring_soon_wide), 2)

    def test_exclude_subscription_packages_from_expiration(self):
        """Test that subscription packages are excluded from expiration detection."""
        # Create subscription (no expiration)
        subscription = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.SUBSCRIPTION,
            amount=Decimal('199.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=None
        )
        
        # Create expired package
        expired_package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=1)
        )
        
        expired_packages = PackageExpirationService.get_expired_packages()
        expiring_soon = PackageExpirationService.get_packages_expiring_soon(days_ahead=30)
        
        # Only package should be detected, not subscription
        self.assertEqual(len(expired_packages), 1)
        self.assertEqual(expired_packages[0].id, expired_package.id)
        self.assertEqual(len(expiring_soon), 0)

    def test_exclude_incomplete_payments_from_expiration(self):
        """Test that packages with incomplete payments are excluded."""
        # Create pending payment package
        pending_package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.PENDING,
            expires_at=self.now - timedelta(days=1)
        )
        
        # Create failed payment package
        failed_package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.FAILED,
            expires_at=self.now - timedelta(days=1)
        )
        
        expired_packages = PackageExpirationService.get_expired_packages()
        
        # No packages should be detected for expiration
        self.assertEqual(len(expired_packages), 0)

    def test_get_packages_by_student(self):
        """Test filtering expired packages by specific student."""
        # Create another student
        other_student = User.objects.create_user(
            email="other@test.com",
            name="Other Student",
            phone_number="+1234567891"
        )
        
        # Create expired packages for both students
        student_expired = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=1)
        )
        
        other_expired = PurchaseTransaction.objects.create(
            student=other_student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('150.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=2)
        )
        
        # Test student-specific detection
        student_packages = PackageExpirationService.get_expired_packages_for_student(self.student)
        
        self.assertEqual(len(student_packages), 1)
        self.assertEqual(student_packages[0].id, student_expired.id)


class PackageExpirationProcessingTests(TestCase):
    """Tests for package expiration processing and effects on student balances."""

    def setUp(self):
        """Set up test data."""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            address="123 Test St", 
            contact_email="test@school.com"
        )
        
        # Create student
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            phone_number="+1234567890"
        )
        
        # Create student account balance
        self.balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('300.00')
        )
        
        self.now = timezone.now()

    def test_process_single_expired_package(self):
        """Test processing a single expired package."""
        # Create expired package with remaining hours
        expired_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('200.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=1),
            metadata={'hours_included': 10}
        )
        
        # Process expiration
        result = PackageExpirationService.process_expired_package(expired_transaction)
        
        # Verify result
        self.assertIsInstance(result, ExpirationResult)
        self.assertTrue(result.success)
        self.assertEqual(result.package_id, expired_transaction.id)
        self.assertEqual(result.student_id, self.student.id)
        self.assertGreater(result.hours_expired, Decimal('0.00'))
        self.assertIsNotNone(result.processed_at)

    def test_calculate_hours_to_expire(self):
        """Test calculation of hours to expire from package."""
        # Create teacher for class session
        from accounts.models import TeacherProfile
        teacher_user = User.objects.create_user(
            email="teacher@test.com",
            name="Test Teacher",
            phone_number="+1234567892"
        )
        teacher = TeacherProfile.objects.create(
            user=teacher_user,
            bio="Test teacher biography"
        )
        
        # Create expired package
        expired_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('150.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=1),
            metadata={'hours_included': 10}
        )
        
        # Create class sessions for consumption records
        from datetime import time
        session1 = ClassSession.objects.create(
            teacher=teacher,
            school=self.school,
            date=self.now.date(),
            start_time=time(10, 0),
            end_time=time(13, 0),
            session_type="individual",
            grade_level="10",
            status=SessionStatus.COMPLETED
        )
        session1.students.add(self.student)
        
        session2 = ClassSession.objects.create(
            teacher=teacher,
            school=self.school,
            date=self.now.date(),
            start_time=time(14, 0),
            end_time=time(16, 0),
            session_type="individual",
            grade_level="10",
            status=SessionStatus.COMPLETED
        )
        session2.students.add(self.student)
        
        # Create hour consumption records (5 hours consumed)
        HourConsumption.objects.create(
            student_account=self.balance,
            class_session=session1,
            purchase_transaction=expired_transaction,
            hours_consumed=Decimal('3.00'),
            hours_originally_reserved=Decimal('3.00')
        )
        
        HourConsumption.objects.create(
            student_account=self.balance,
            class_session=session2,
            purchase_transaction=expired_transaction,
            hours_consumed=Decimal('2.00'),
            hours_originally_reserved=Decimal('2.00')
        )
        
        # Calculate hours to expire
        hours_to_expire = PackageExpirationService.calculate_hours_to_expire(expired_transaction)
        
        # Should be 10 total - 5 consumed = 5 hours to expire
        self.assertEqual(hours_to_expire, Decimal('5.00'))

    def test_update_student_balance_on_expiration(self):
        """Test that student balance is updated correctly when package expires."""
        # Record original balance
        original_purchased = self.balance.hours_purchased
        original_consumed = self.balance.hours_consumed
        
        # Create expired package
        expired_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('150.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=1),
            metadata={'hours_included': 10}
        )
        
        # Add package hours to balance (simulating purchase)
        self.balance.hours_purchased += Decimal('10.00')
        self.balance.save()
        
        # Process expiration
        result = PackageExpirationService.process_expired_package(expired_transaction)
        
        # Refresh balance from database
        self.balance.refresh_from_db()
        
        # Verify balance was updated (purchased hours reduced by expired amount)
        self.assertEqual(
            self.balance.hours_purchased, 
            original_purchased  # Should remove the expired hours
        )

    def test_bulk_expiration_processing(self):
        """Test processing multiple expired packages efficiently."""
        # Create multiple expired packages
        expired_packages = []
        for i in range(5):
            package = PurchaseTransaction.objects.create(
                student=self.student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('100.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at=self.now - timedelta(days=i+1),
                metadata={'hours_included': 5}
            )
            expired_packages.append(package)
        
        # Process all expired packages
        results = PackageExpirationService.process_bulk_expiration()
        
        # Verify all packages were processed
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, ExpirationResult)
            self.assertTrue(result.success)

    def test_grace_period_handling(self):
        """Test handling of grace periods for package expiration."""
        # Create package that expired within grace period
        grace_period_hours = 24
        expired_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(hours=12)  # Expired 12 hours ago
        )
        
        # Should not be processed if within grace period
        expired_packages = PackageExpirationService.get_expired_packages_outside_grace_period(
            grace_hours=grace_period_hours
        )
        
        self.assertEqual(len(expired_packages), 0)
        
        # Should be processed if outside grace period
        expired_packages = PackageExpirationService.get_expired_packages_outside_grace_period(
            grace_hours=6  # 6 hour grace period
        )
        
        self.assertEqual(len(expired_packages), 1)

    def test_expiration_audit_logging(self):
        """Test that expiration processing creates audit logs."""
        # Create expired package
        expired_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=1),
            metadata={'hours_included': 5}
        )
        
        # Process expiration
        result = PackageExpirationService.process_expired_package(expired_transaction)
        
        # Verify audit information is recorded
        self.assertIsNotNone(result.audit_log)
        self.assertIn('expired', result.audit_log)
        self.assertIn(str(self.student.id), result.audit_log)
        self.assertIn(str(expired_transaction.id), result.audit_log)


class PackageNotificationTests(TestCase):
    """Tests for package expiration notification system."""

    def setUp(self):
        """Set up test data."""
        # Create student
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            phone_number="+1234567890"
        )
        
        self.now = timezone.now()






class PackageExtensionTests(TestCase):
    """Tests for package extension and renewal functionality."""

    def setUp(self):
        """Set up test data."""
        # Create student
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            phone_number="+1234567890"
        )
        
        # Create student account balance
        self.balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('150.00')
        )
        
        self.now = timezone.now()

    def test_extend_package_expiration(self):
        """Test extending a package expiration date."""
        # Create package expiring soon
        original_expiry = self.now + timedelta(days=5)
        package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=original_expiry
        )
        
        # Extend by 30 days
        extension_days = 30
        result = PackageExpirationService.extend_package_expiration(
            package, 
            extension_days=extension_days
        )
        
        # Verify extension
        self.assertTrue(result.success)
        
        # Refresh package from database
        package.refresh_from_db()
        expected_expiry = original_expiry + timedelta(days=extension_days)
        self.assertEqual(package.expires_at.date(), expected_expiry.date())

    def test_bulk_package_extension(self):
        """Test extending multiple packages at once."""
        # Create multiple packages for student
        packages = []
        for i in range(3):
            package = PurchaseTransaction.objects.create(
                student=self.student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('100.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at=self.now + timedelta(days=i+1)
            )
            packages.append(package)
        
        # Extend all packages by 14 days
        extension_days = 14
        results = PackageExpirationService.bulk_extend_packages(
            packages,
            extension_days=extension_days
        )
        
        # Verify all extensions
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.success)

    def test_extend_expired_package(self):
        """Test extending an already expired package."""
        # Create expired package
        expired_package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=5)
        )
        
        # Extend from current time (not original expiry)
        extension_days = 30
        result = PackageExpirationService.extend_package_expiration(
            expired_package,
            extension_days=extension_days,
            extend_from_now=True
        )
        
        # Verify extension
        self.assertTrue(result.success)
        
        # Refresh package from database
        expired_package.refresh_from_db()
        expected_expiry = self.now + timedelta(days=extension_days)
        self.assertEqual(
            expired_package.expires_at.date(),
            expected_expiry.date()
        )

    def test_package_renewal_with_new_purchase(self):
        """Test renewing an expired package with a new purchase."""
        # Create expired package
        expired_package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=10),
            metadata={'hours_included': 10}
        )
        
        # Create renewal
        renewal_result = PackageExpirationService.create_package_renewal(
            expired_package,
            new_amount=Decimal('120.00'),
            new_hours=Decimal('12.00'),
            new_validity_days=60
        )
        
        # Verify renewal was created
        self.assertTrue(renewal_result.success)
        self.assertIsNotNone(renewal_result.new_package_id)
        
        # Verify new package exists
        new_package = PurchaseTransaction.objects.get(id=renewal_result.new_package_id)
        self.assertEqual(new_package.student, self.student)
        self.assertEqual(new_package.amount, Decimal('120.00'))
        self.assertGreater(new_package.expires_at, self.now)

    def test_extension_audit_logging(self):
        """Test that package extensions are properly logged."""
        # Create package
        package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now + timedelta(days=5)
        )
        
        # Extend package
        result = PackageExpirationService.extend_package_expiration(
            package,
            extension_days=30,
            reason="Customer service extension"
        )
        
        # Verify audit information
        self.assertIsNotNone(result.audit_log)
        self.assertIn('extended', result.audit_log.lower())
        self.assertIn('30', result.audit_log)
        self.assertIn('customer service', result.audit_log.lower())


class ExpirationAnalyticsTests(TestCase):
    """Tests for expiration analytics and reporting functionality."""

    def setUp(self):
        """Set up test data."""
        # Create multiple students
        self.students = []
        for i in range(3):
            student = User.objects.create_user(
                email=f"student{i}@test.com",
                name=f"Test Student {i}",
                phone_number=f"+123456789{i}"
            )
            self.students.append(student)
        
        self.now = timezone.now()

    def test_generate_expiration_summary_report(self):
        """Test generating summary report of expiration activity."""
        # Create mix of expired, expiring, and active packages
        self._create_test_packages()
        
        # Generate report
        report = PackageExpirationService.generate_expiration_summary_report(
            start_date=self.now - timedelta(days=30),
            end_date=self.now + timedelta(days=30)
        )
        
        # Verify report structure
        self.assertIn('total_packages', report)
        self.assertIn('expired_packages', report)
        self.assertIn('expiring_soon', report)
        self.assertIn('hours_expired', report)
        self.assertIn('students_affected', report)
        
        # Verify data accuracy
        self.assertGreater(report['total_packages'], 0)
        self.assertGreater(report['expired_packages'], 0)

    def test_get_student_expiration_history(self):
        """Test retrieving expiration history for a specific student."""
        student = self.students[0]
        
        # Create expiration history for student
        for i in range(3):
            PurchaseTransaction.objects.create(
                student=student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('100.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at=self.now - timedelta(days=i*10)
            )
        
        # Get history
        history = PackageExpirationService.get_student_expiration_history(
            student,
            limit=10
        )
        
        # Verify history
        self.assertEqual(len(history), 3)
        for entry in history:
            self.assertEqual(entry['student_id'], student.id)
            self.assertIn('package_id', entry)
            self.assertIn('expired_at', entry)

    def test_calculate_expiration_metrics(self):
        """Test calculation of expiration metrics and KPIs."""
        # Create test data
        self._create_test_packages()
        
        # Calculate metrics
        metrics = PackageExpirationService.calculate_expiration_metrics(
            period_days=30
        )
        
        # Verify metrics structure
        self.assertIn('expiration_rate', metrics)
        self.assertIn('average_package_lifetime', metrics)
        self.assertIn('hours_lost_to_expiration', metrics)
        self.assertIn('revenue_impact', metrics)
        
        # Verify metrics are reasonable
        self.assertGreaterEqual(metrics['expiration_rate'], 0)
        self.assertLessEqual(metrics['expiration_rate'], 1)

    def test_identify_at_risk_students(self):
        """Test identification of students with patterns indicating high expiration risk."""
        # Create student with multiple expired packages
        high_risk_student = self.students[0]
        
        for i in range(4):
            PurchaseTransaction.objects.create(
                student=high_risk_student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('100.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at=self.now - timedelta(days=i*5)
            )
        
        # Identify at-risk students
        at_risk = PackageExpirationService.identify_at_risk_students(
            min_expired_packages=2,
            timeframe_days=30
        )
        
        # Verify identification
        self.assertGreater(len(at_risk), 0)
        risk_student_ids = [student['student_id'] for student in at_risk]
        self.assertIn(high_risk_student.id, risk_student_ids)

    def _create_test_packages(self):
        """Helper method to create test packages for analytics."""
        for i, student in enumerate(self.students):
            # Expired package
            PurchaseTransaction.objects.create(
                student=student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('100.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at=self.now - timedelta(days=i+1)
            )
            
            # Expiring soon package
            PurchaseTransaction.objects.create(
                student=student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('150.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at=self.now + timedelta(days=i+2)
            )
            
            # Active package
            PurchaseTransaction.objects.create(
                student=student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('200.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at=self.now + timedelta(days=30+i)
            )


class AdminAPIEndpointsTests(TestCase):
    """Tests for admin API endpoints for expiration management."""

    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            name="Admin User",
            phone_number="+1234567890",
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular student
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            phone_number="+1234567891"
        )
        
        # Create student account balance
        self.balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('150.00')
        )
        
        self.now = timezone.now()

    def test_get_expired_packages_endpoint(self):
        """Test API endpoint to get expired packages."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        # Create expired package
        expired_package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=1)
        )
        
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        
        response = client.get('/api/finances/api/admin/expired-packages/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_process_expired_packages_endpoint(self):
        """Test API endpoint to process expired packages."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        # Create expired package
        expired_package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=2),
            metadata={'hours_included': 10}
        )
        
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        
        response = client.post('/api/finances/api/admin/process-expired-packages/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('processed_count', response.data)

    def test_extend_package_endpoint(self):
        """Test API endpoint to extend package expiration."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        # Create package expiring soon
        package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now + timedelta(days=5)
        )
        
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        
        data = {
            'extension_days': 30,
            'reason': 'Customer service extension'
        }
        
        response = client.post(f'/api/finances/api/admin/packages/{package.id}/extend/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_get_expiration_analytics_endpoint(self):
        """Test API endpoint to get expiration analytics."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        # Create test packages
        for i in range(3):
            PurchaseTransaction.objects.create(
                student=self.student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('100.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at=self.now - timedelta(days=i+1)
            )
        
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        
        response = client.get('/api/finances/api/admin/expiration-analytics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('total_packages', response.data['summary'])
        self.assertIn('expired_packages', response.data['summary'])

    def test_send_expiration_notifications_endpoint(self):
        """Test API endpoint to send expiration notifications."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        # Create package expiring soon
        package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now + timedelta(days=3)
        )
        
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        
        data = {
            'days_ahead': 7
        }
        
        with patch('finances.services.package_expiration_service.send_mail') as mock_send_mail:
            mock_send_mail.return_value = True
            
            response = client.post('/api/finances/api/admin/send-expiration-notifications/', data)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('notifications_sent', response.data)

    def test_unauthorized_access_denied(self):
        """Test that unauthorized users cannot access admin endpoints."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        client = APIClient()
        # No authentication
        
        response = client.get('/api/finances/api/admin/expired-packages/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Authenticate as regular student
        client.force_authenticate(user=self.student)
        
        response = client.get('/api/finances/api/admin/expired-packages/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ManagementCommandTests(TestCase):
    """Tests for the package expiration management command."""

    def setUp(self):
        """Set up test data."""
        # Create student
        self.student = User.objects.create_user(
            email="student@test.com",
            name="Test Student",
            phone_number="+1234567890"
        )
        
        self.now = timezone.now()

    def test_management_command_basic_execution(self):
        """Test basic execution of the expiration management command."""
        # Create expired packages
        for i in range(3):
            PurchaseTransaction.objects.create(
                student=self.student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('100.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at=self.now - timedelta(days=i+1)
            )
        
        # Execute command
        with patch('sys.stdout') as mock_stdout:
            call_command('process_package_expiration', verbosity=2)
            
            # Verify command executed
            self.assertTrue(mock_stdout.write.called)

    def test_management_command_dry_run(self):
        """Test dry run mode of the management command."""
        # Create expired package
        expired_package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=1),
            metadata={'hours_included': 10}
        )
        
        # Execute command in dry run mode
        with patch('sys.stdout') as mock_stdout:
            call_command('process_package_expiration', '--dry-run', verbosity=2)
            
            # Verify command executed but didn't process
            self.assertTrue(mock_stdout.write.called)
            
            # Verify package wasn't actually processed
            expired_package.refresh_from_db()
            self.assertTrue(expired_package.is_expired)

    def test_management_command_with_grace_period(self):
        """Test management command respecting grace period."""
        # Create recently expired package (within grace period)
        recent_expired = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(hours=12)
        )
        
        # Execute command with 24-hour grace period
        with patch('sys.stdout') as mock_stdout:
            call_command(
                'process_package_expiration',
                '--grace-hours=24',
                verbosity=2
            )
            
            # Verify command executed
            self.assertTrue(mock_stdout.write.called)

    def test_management_command_student_filter(self):
        """Test management command filtering by specific student."""
        # Create another student
        other_student = User.objects.create_user(
            email="other@test.com",
            name="Other Student",
            phone_number="+1234567891"
        )
        
        # Create expired packages for both students
        student_package = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('100.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=1)
        )
        
        other_package = PurchaseTransaction.objects.create(
            student=other_student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal('150.00'),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=self.now - timedelta(days=2)
        )
        
        # Execute command for specific student
        with patch('sys.stdout') as mock_stdout:
            call_command(
                'process_package_expiration',
                f'--student-email={self.student.email}',
                verbosity=2
            )
            
            # Verify command executed
            self.assertTrue(mock_stdout.write.called)