"""
Unit tests for Package Expiration Management business logic.

Tests core business rules for package expiration without API endpoints:
- Expiration date calculations and grace periods
- Hour calculation business rules
- Package filtering and status validation
- Notification decision logic
- Extension and renewal business rules
- Bulk processing algorithms

These tests focus on the business logic that needs fixes for GitHub Issue #173.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock

from django.test import TestCase as DjangoTestCase, override_settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from finances.models import (
    PurchaseTransaction, 
    StudentAccountBalance, 
    HourConsumption,
    TransactionPaymentStatus,
    TransactionType
)
from finances.services.package_expiration_service import (
    PackageExpirationService,
    ExpirationResult,
    NotificationResult,
    ExtensionResult,
    RenewalResult
)
from accounts.models import CustomUser


class PackageExpirationCalculationTest(DjangoTestCase):
    """Test package expiration calculation business rules."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        # Create a mock package with metadata
        self.package = Mock(spec=PurchaseTransaction)
        self.package.id = 1
        self.package.student = self.student
        self.package.metadata = {'hours_included': 10.0}
        self.package.amount = Decimal('150.00')
        self.package.expires_at = timezone.now() + timedelta(days=30)

    def test_calculate_hours_to_expire_with_no_consumption(self):
        """Test calculating hours to expire when no hours consumed."""
        with patch('finances.services.package_expiration_service.HourConsumption.objects.filter') as mock_filter:
            mock_filter.return_value.aggregate.return_value = {'total': None}
            
            result = PackageExpirationService.calculate_hours_to_expire(self.package)
            
            self.assertEqual(result, Decimal('10.00'))

    def test_calculate_hours_to_expire_with_partial_consumption(self):
        """Test calculating hours to expire with partial consumption."""
        with patch('finances.services.package_expiration_service.HourConsumption.objects.filter') as mock_filter:
            mock_filter.return_value.aggregate.return_value = {'total': Decimal('3.5')}
            
            result = PackageExpirationService.calculate_hours_to_expire(self.package)
            
            self.assertEqual(result, Decimal('6.5'))

    def test_calculate_hours_to_expire_fully_consumed(self):
        """Test calculating hours to expire when fully consumed."""
        with patch('finances.services.package_expiration_service.HourConsumption.objects.filter') as mock_filter:
            mock_filter.return_value.aggregate.return_value = {'total': Decimal('10.0')}
            
            result = PackageExpirationService.calculate_hours_to_expire(self.package)
            
            self.assertEqual(result, Decimal('0.00'))

    def test_calculate_hours_to_expire_over_consumed(self):
        """Test calculating hours to expire when over-consumed (should return 0)."""
        with patch('finances.services.package_expiration_service.HourConsumption.objects.filter') as mock_filter:
            mock_filter.return_value.aggregate.return_value = {'total': Decimal('12.0')}
            
            result = PackageExpirationService.calculate_hours_to_expire(self.package)
            
            self.assertEqual(result, Decimal('0.00'))

    def test_calculate_hours_to_expire_invalid_metadata(self):
        """Test calculating hours to expire with invalid metadata."""
        self.package.metadata = {}
        
        with patch('finances.services.package_expiration_service.HourConsumption.objects.filter') as mock_filter:
            mock_filter.return_value.aggregate.return_value = {'total': None}
            
            result = PackageExpirationService.calculate_hours_to_expire(self.package)
            
            self.assertEqual(result, Decimal('0.00'))


class PackageExpirationFiltersTest(DjangoTestCase):
    """Test package expiration filtering business logic."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    def test_get_expired_packages_filters_correctly(self):
        """Test that expired package filter uses correct criteria."""
        now = timezone.now()
        
        with patch('finances.services.package_expiration_service.PurchaseTransaction.objects.filter') as mock_filter:
            mock_queryset = Mock()
            mock_queryset.select_related.return_value = []
            mock_filter.return_value = mock_queryset
            
            PackageExpirationService.get_expired_packages()
            
            # Verify filter criteria
            mock_filter.assert_called_once()
            call_args = mock_filter.call_args[1]
            self.assertEqual(call_args['transaction_type'], TransactionType.PACKAGE)
            self.assertEqual(call_args['payment_status'], TransactionPaymentStatus.COMPLETED)
            self.assertIn('expires_at__lt', call_args)

    def test_get_packages_expiring_soon_default_days(self):
        """Test packages expiring soon filter with default 7 days."""
        with patch('finances.services.package_expiration_service.PurchaseTransaction.objects.filter') as mock_filter:
            mock_queryset = Mock()
            mock_queryset.select_related.return_value = []
            mock_filter.return_value = mock_queryset
            
            PackageExpirationService.get_packages_expiring_soon()
            
            # Should use 7 days by default
            call_args = mock_filter.call_args[1]
            self.assertIn('expires_at__lte', call_args)

    def test_get_packages_expiring_soon_custom_days(self):
        """Test packages expiring soon filter with custom days."""
        with patch('finances.services.package_expiration_service.PurchaseTransaction.objects.filter') as mock_filter:
            mock_queryset = Mock()
            mock_queryset.select_related.return_value = []
            mock_filter.return_value = mock_queryset
            
            PackageExpirationService.get_packages_expiring_soon(days_ahead=14)
            
            # Should filter with custom days
            call_args = mock_filter.call_args[1]
            self.assertIn('expires_at__lte', call_args)

    def test_get_expired_packages_outside_grace_period(self):
        """Test filtering packages outside grace period."""
        with patch('finances.services.package_expiration_service.PurchaseTransaction.objects.filter') as mock_filter:
            mock_queryset = Mock()
            mock_queryset.select_related.return_value = []
            mock_filter.return_value = mock_queryset
            
            PackageExpirationService.get_expired_packages_outside_grace_period(grace_hours=48)
            
            # Should filter correctly based on grace period
            call_args = mock_filter.call_args[1]
            self.assertIn('expires_at__lt', call_args)


class PackageExpirationProcessingTest(DjangoTestCase):
    """Test package expiration processing business logic."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        self.balance = Mock()
        self.balance.hours_purchased = Decimal('20.00')

    @patch('finances.services.package_expiration_service.StudentAccountBalance.objects.get')
    @patch('finances.services.package_expiration_service.PackageExpirationService.calculate_hours_to_expire')
    def test_process_expired_package_success(self, mock_calculate, mock_balance_get):
        """Test successful processing of expired package."""
        mock_calculate.return_value = Decimal('5.00')
        mock_balance_get.return_value = self.balance
        
        package = Mock(spec=PurchaseTransaction)
        package.id = 1
        package.student = self.student
        package.student.id = 1
        package.student.name = "Test Student"
        
        result = PackageExpirationService.process_expired_package(package)
        
        self.assertTrue(result.success)
        self.assertEqual(result.package_id, 1)
        self.assertEqual(result.student_id, 1)
        self.assertEqual(result.hours_expired, Decimal('5.00'))
        self.assertIsNotNone(result.processed_at)
        self.assertIn("Package 1 expired", result.audit_log)
        
        # Verify balance was updated
        self.balance.save.assert_called_once()
        self.assertEqual(self.balance.hours_purchased, Decimal('15.00'))

    @patch('finances.services.package_expiration_service.StudentAccountBalance.objects.get')
    def test_process_expired_package_no_hours_to_expire(self, mock_balance_get):
        """Test processing when no hours need to be expired."""
        package = Mock(spec=PurchaseTransaction)
        package.id = 1
        package.student = self.student
        package.student.id = 1
        package.student.name = "Test Student"
        
        with patch('finances.services.package_expiration_service.PackageExpirationService.calculate_hours_to_expire', return_value=Decimal('0.00')):
            result = PackageExpirationService.process_expired_package(package)
            
            self.assertTrue(result.success)
            self.assertEqual(result.hours_expired, Decimal('0.00'))
            
            # Balance should not be fetched when no hours to expire
            mock_balance_get.assert_not_called()

    @patch('finances.services.package_expiration_service.StudentAccountBalance.objects.get')
    def test_process_expired_package_exception_handling(self, mock_balance_get):
        """Test error handling in package processing."""
        mock_balance_get.side_effect = Exception("Database error")
        
        package = Mock(spec=PurchaseTransaction)
        package.id = 1
        package.student = self.student
        package.student.id = 1
        
        with patch('finances.services.package_expiration_service.PackageExpirationService.calculate_hours_to_expire', return_value=Decimal('5.00')):
            result = PackageExpirationService.process_expired_package(package)
            
            self.assertFalse(result.success)
            self.assertEqual(result.hours_expired, Decimal('0.00'))
            self.assertIn("Error processing expired package", result.error_message)


class PackageNotificationLogicTest(DjangoTestCase):
    """Test notification decision logic for package expiration."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        self.package = Mock(spec=PurchaseTransaction)
        self.package.student = self.student
        self.package.amount = Decimal('100.00')
        self.package.expires_at = timezone.now() + timedelta(days=7)

    @patch('finances.services.package_expiration_service.send_mail')
    def test_send_expiration_warning_respect_preferences_enabled(self, mock_send_mail):
        """Test notification respects student preferences when enabled."""
        self.student.metadata = {'email_notifications': False}
        
        result = PackageExpirationService.send_expiration_warning(
            self.package, 7, respect_preferences=True
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.notification_type, 'email')
        self.assertIn("Notifications disabled", result.message)
        mock_send_mail.assert_not_called()

    @patch('finances.services.package_expiration_service.send_mail')
    def test_send_expiration_warning_respect_preferences_disabled(self, mock_send_mail):
        """Test notification ignores preferences when disabled."""
        self.student.metadata = {'email_notifications': False}
        
        result = PackageExpirationService.send_expiration_warning(
            self.package, 7, respect_preferences=False
        )
        
        self.assertTrue(result.success)
        mock_send_mail.assert_called_once()

    @patch('finances.services.package_expiration_service.send_mail')
    def test_send_expiration_warning_no_metadata(self, mock_send_mail):
        """Test notification when student has no metadata."""
        # student has no metadata attribute
        
        result = PackageExpirationService.send_expiration_warning(
            self.package, 7, respect_preferences=True
        )
        
        self.assertTrue(result.success)
        mock_send_mail.assert_called_once()

    @patch('finances.services.package_expiration_service.send_mail')
    def test_send_expiration_warning_email_content(self, mock_send_mail):
        """Test email content generation for expiration warning."""
        result = PackageExpirationService.send_expiration_warning(self.package, 5)
        
        self.assertTrue(result.success)
        mock_send_mail.assert_called_once()
        
        # Check email content
        call_args = mock_send_mail.call_args[1]
        self.assertIn("5 Days Remaining", call_args['subject'])
        self.assertIn("Test Student", call_args['message'])
        self.assertIn("€100.00", call_args['message'])


class PackageExtensionLogicTest(DjangoTestCase):
    """Test package extension business logic."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com", 
            name="Test Student"
        )
        
        self.package = Mock(spec=PurchaseTransaction)
        self.package.id = 1
        self.package.expires_at = timezone.now() + timedelta(days=7)

    def test_extend_package_expiration_from_original_date(self):
        """Test extending package from original expiration date."""
        original_expiry = self.package.expires_at
        
        result = PackageExpirationService.extend_package_expiration(
            self.package, 14, "Customer request", extend_from_now=False
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.package_id, 1)
        self.assertEqual(result.original_expiry, original_expiry)
        self.assertEqual(result.extension_days, 14)
        
        # New expiry should be original + 14 days
        expected_new_expiry = original_expiry + timedelta(days=14)
        self.assertEqual(result.new_expiry, expected_new_expiry)

    def test_extend_package_expiration_from_now(self):
        """Test extending package from current time."""
        with patch('finances.services.package_expiration_service.timezone.now') as mock_now:
            mock_now.return_value = timezone.now()
            
            result = PackageExpirationService.extend_package_expiration(
                self.package, 14, "Customer request", extend_from_now=True
            )
            
            self.assertTrue(result.success)
            self.assertEqual(result.extension_days, 14)
            
            # Verify package.save was called
            self.package.save.assert_called_once()

    def test_extend_package_expiration_exception_handling(self):
        """Test error handling in package extension."""
        self.package.save.side_effect = Exception("Database error")
        
        result = PackageExpirationService.extend_package_expiration(
            self.package, 14, "Customer request"
        )
        
        self.assertFalse(result.success)
        self.assertIn("Error extending package", result.error_message)


class PackageBulkProcessingTest(DjangoTestCase):
    """Test bulk processing algorithms for package expiration."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    @patch('finances.services.package_expiration_service.PackageExpirationService.get_expired_packages_outside_grace_period')
    @patch('finances.services.package_expiration_service.PackageExpirationService.process_expired_package')
    def test_process_bulk_expiration_success(self, mock_process_package, mock_get_packages):
        """Test successful bulk expiration processing."""
        # Mock packages to process
        package1 = Mock()
        package1.id = 1
        package2 = Mock() 
        package2.id = 2
        mock_get_packages.return_value = [package1, package2]
        
        # Mock processing results
        result1 = ExpirationResult(True, 1, 1, Decimal('5.0'), timezone.now(), "audit1")
        result2 = ExpirationResult(True, 2, 2, Decimal('3.0'), timezone.now(), "audit2")
        mock_process_package.side_effect = [result1, result2]
        
        results = PackageExpirationService.process_bulk_expiration(grace_hours=24)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))
        mock_get_packages.assert_called_once_with(grace_hours=24)
        self.assertEqual(mock_process_package.call_count, 2)

    @patch('finances.services.package_expiration_service.PackageExpirationService.extend_package_expiration')
    def test_bulk_extend_packages_processing(self, mock_extend):
        """Test bulk package extension processing."""
        package1 = Mock()
        package1.id = 1
        package2 = Mock()
        package2.id = 2
        packages = [package1, package2]
        
        # Mock extension results
        result1 = ExtensionResult(True, 1, timezone.now(), timezone.now(), 7, "audit1")
        result2 = ExtensionResult(True, 2, timezone.now(), timezone.now(), 7, "audit2")
        mock_extend.side_effect = [result1, result2]
        
        results = PackageExpirationService.bulk_extend_packages(packages, 7, "Bulk extension")
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))
        self.assertEqual(mock_extend.call_count, 2)
        
        # Verify each call had correct parameters
        for call in mock_extend.call_args_list:
            self.assertEqual(call[0][1], 7)  # extension_days
            self.assertEqual(call[0][2], "Bulk extension")  # reason


class PackageRenewalLogicTest(DjangoTestCase):
    """Test package renewal business logic."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        self.expired_package = Mock(spec=PurchaseTransaction)
        self.expired_package.id = 1
        self.expired_package.student = self.student

    @patch('finances.services.package_expiration_service.PurchaseTransaction.objects.create')
    @patch('finances.services.package_expiration_service.StudentAccountBalance.objects.get')
    def test_create_package_renewal_success(self, mock_balance_get, mock_transaction_create):
        """Test successful package renewal creation."""
        # Mock new package creation
        new_package = Mock()
        new_package.id = 2
        mock_transaction_create.return_value = new_package
        
        # Mock balance update
        balance = Mock()
        balance.hours_purchased = Decimal('10.00')
        balance.balance_amount = Decimal('100.00')
        mock_balance_get.return_value = balance
        
        result = PackageExpirationService.create_package_renewal(
            self.expired_package,
            new_amount=Decimal('200.00'),
            new_hours=Decimal('15.00'),
            new_validity_days=60
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.original_package_id, 1)
        self.assertEqual(result.new_package_id, 2)
        
        # Verify new package creation parameters
        mock_transaction_create.assert_called_once()
        create_args = mock_transaction_create.call_args[1]
        self.assertEqual(create_args['student'], self.student)
        self.assertEqual(create_args['amount'], Decimal('200.00'))
        self.assertEqual(create_args['metadata']['hours_included'], 15.0)
        self.assertEqual(create_args['metadata']['renewed_from'], 1)
        
        # Verify balance update
        self.assertEqual(balance.hours_purchased, Decimal('25.00'))
        self.assertEqual(balance.balance_amount, Decimal('300.00'))
        balance.save.assert_called_once()

    @patch('finances.services.package_expiration_service.PurchaseTransaction.objects.create')
    def test_create_package_renewal_exception_handling(self, mock_transaction_create):
        """Test error handling in package renewal."""
        mock_transaction_create.side_effect = Exception("Database error")
        
        result = PackageExpirationService.create_package_renewal(
            self.expired_package,
            new_amount=Decimal('200.00'),
            new_hours=Decimal('15.00'),
            new_validity_days=60
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.original_package_id, 1)
        self.assertIsNone(result.new_package_id)
        self.assertIn("Error creating package renewal", result.error_message)


class PackageExpirationMetricsTest(DjangoTestCase):
    """Test package expiration metrics calculation business logic."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    @patch('finances.services.package_expiration_service.PurchaseTransaction.objects.filter')
    def test_calculate_expiration_metrics_calculation(self, mock_filter):
        """Test expiration metrics calculation algorithm."""
        # Mock packages with different expiration states
        now = timezone.now()
        
        package1 = Mock()
        package1.created_at = now - timedelta(days=20)
        package1.expires_at = now - timedelta(days=5)  # Expired
        
        package2 = Mock()  
        package2.created_at = now - timedelta(days=10)
        package2.expires_at = now + timedelta(days=10)  # Not expired
        
        # Mock queryset behavior
        mock_queryset = Mock()
        mock_queryset.count.return_value = 2  # Total packages
        
        # Mock expired packages count
        expired_queryset = Mock()
        expired_queryset.count.return_value = 1  # One expired
        mock_queryset.filter.return_value = expired_queryset
        
        mock_filter.return_value = mock_queryset
        
        with patch('finances.services.package_expiration_service.PackageExpirationService.calculate_hours_to_expire', return_value=Decimal('2.5')):
            result = PackageExpirationService.calculate_expiration_metrics(period_days=30)
            
            self.assertEqual(result['expiration_rate'], 0.5)  # 1 expired / 2 total
            self.assertEqual(result['hours_lost_to_expiration'], Decimal('2.5'))
            self.assertEqual(result['revenue_impact'], Decimal('37.50'))  # 2.5 * 15

    def test_identify_at_risk_students_algorithm(self):
        """Test at-risk student identification algorithm."""
        with patch('finances.services.package_expiration_service.PurchaseTransaction.objects.filter') as mock_filter:
            # Mock student with multiple expired packages
            mock_values = Mock()
            mock_annotate = Mock()
            mock_filter_final = Mock()
            
            mock_filter.return_value = mock_values
            mock_values.values.return_value = mock_annotate  
            mock_annotate.annotate.return_value = mock_filter_final
            mock_filter_final.filter.return_value = [
                {'student': 1, 'expired_count': 3},
                {'student': 2, 'expired_count': 5}
            ]
            
            result = PackageExpirationService.identify_at_risk_students(
                min_expired_packages=2, timeframe_days=90
            )
            
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['student_id'], 1)
            self.assertEqual(result[0]['expired_packages_count'], 3)
            self.assertEqual(result[0]['risk_score'], 0.6)  # 3/5 = 0.6
            
            self.assertEqual(result[1]['student_id'], 2)
            self.assertEqual(result[1]['expired_packages_count'], 5)
            self.assertEqual(result[1]['risk_score'], 1.0)  # 5/5 = 1.0 (max)