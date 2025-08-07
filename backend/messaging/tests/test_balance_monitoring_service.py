"""
Business logic tests for BalanceMonitoringService.

Tests the core business rules for student balance monitoring:
- Low balance detection and thresholds
- Package expiration monitoring
- Notification deduplication (preventing spam)
- Email alert triggering
- Balance depletion handling
- Service integration and error handling
"""

from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone

from accounts.models import CustomUser, School, SchoolMembership, SchoolRole
from finances.models import (
    StudentAccountBalance, PurchaseTransaction, 
    TransactionType, TransactionPaymentStatus
)
from messaging.models import Notification, NotificationType
from messaging.services import BalanceMonitoringService


class BalanceMonitoringServiceTest(TestCase):
    """Test business logic for balance monitoring service."""
    
    def setUp(self):
        """Set up test data."""
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school for balance monitoring",
            contact_email="support@testschool.com"
        )
        
        # Create test student
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        # Create school membership
        SchoolMembership.objects.create(
            user=self.student,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        
        # Create student balance
        self.balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("0.00"),
            balance_amount=Decimal("100.00")
        )
    
    def test_low_balance_detection_threshold(self):
        """Test business rule: detect students below configured balance threshold."""
        # Business scenario: student has 1.5 hours remaining (below 2.0 threshold)
        self.balance.hours_consumed = Decimal("8.50")  # 10.0 - 8.5 = 1.5 remaining
        self.balance.save()
        
        # Business rule: detect students below default threshold (2.0 hours)
        low_balance_students = BalanceMonitoringService.check_low_balance_students()
        
        self.assertIn(self.student, low_balance_students)
        
        # Business rule: students above threshold should not be detected
        self.balance.hours_consumed = Decimal("7.50")  # 10.0 - 7.5 = 2.5 remaining
        self.balance.save()
        
        low_balance_students = BalanceMonitoringService.check_low_balance_students()
        
        self.assertNotIn(self.student, low_balance_students)
    
    def test_custom_balance_threshold(self):
        """Test business rule: service supports custom balance thresholds."""
        # Business scenario: school wants custom threshold of 3.0 hours
        self.balance.hours_consumed = Decimal("7.50")  # 10.0 - 7.5 = 2.5 remaining
        self.balance.save()
        
        # Business rule: student should not trigger default threshold (2.0)
        low_balance_default = BalanceMonitoringService.check_low_balance_students()
        self.assertNotIn(self.student, low_balance_default)
        
        # Business rule: student should trigger custom threshold (3.0)
        low_balance_custom = BalanceMonitoringService.check_low_balance_students(
            threshold_hours=Decimal("3.0")
        )
        self.assertIn(self.student, low_balance_custom)
    
    def test_package_expiration_detection(self):
        """Test business rule: detect packages expiring within configured timeframe."""
        # Business scenario: student has package expiring in 5 days
        expiring_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(days=5)
        )
        
        # Business rule: detect packages expiring within default timeframe (7 days)
        expiring_packages = BalanceMonitoringService.check_expiring_packages()
        
        self.assertIn(expiring_transaction, expiring_packages)
        
        # Business rule: packages expiring beyond timeframe should not be detected
        future_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(days=10)  # Beyond 7 days
        )
        
        expiring_packages = BalanceMonitoringService.check_expiring_packages()
        
        self.assertNotIn(future_transaction, expiring_packages)
    
    def test_ignore_expired_packages(self):
        """Test business rule: ignore packages that have already expired."""
        # Business scenario: student has already expired package
        expired_transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() - timedelta(days=1)  # Already expired
        )
        
        # Business rule: expired packages should not trigger alerts
        expiring_packages = BalanceMonitoringService.check_expiring_packages()
        
        self.assertNotIn(expired_transaction, expiring_packages)
    
    def test_notification_deduplication_prevents_spam(self):
        """Test business rule: prevent duplicate notifications within cooldown period."""
        # Business scenario: student already received low balance notification recently
        recent_notification = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.LOW_BALANCE,
            title="Previous Low Balance Alert",
            message="Previous message",
            created_at=timezone.now() - timedelta(hours=12)  # Within 24h cooldown
        )
        
        # Business rule: service should detect recent notification
        has_recent = BalanceMonitoringService.has_recent_notification(
            self.student, NotificationType.LOW_BALANCE
        )
        self.assertTrue(has_recent)
        
        # Business rule: service should NOT create duplicate notification
        notification = BalanceMonitoringService.create_low_balance_notification(
            self.student, Decimal("1.5")
        )
        self.assertIsNone(notification)
    
    def test_notification_deduplication_allows_after_cooldown(self):
        """Test business rule: allow notifications after cooldown period expires."""
        # Business scenario: student received notification beyond cooldown period
        old_notification = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.LOW_BALANCE,
            title="Old Low Balance Alert",
            message="Old message",
            created_at=timezone.now() - timedelta(hours=25)  # Beyond 24h cooldown
        )
        
        # Business rule: service should not detect old notification as recent
        has_recent = BalanceMonitoringService.has_recent_notification(
            self.student, NotificationType.LOW_BALANCE
        )
        self.assertFalse(has_recent)
        
        # Business rule: service should create new notification
        notification = BalanceMonitoringService.create_low_balance_notification(
            self.student, Decimal("1.5")
        )
        self.assertIsNotNone(notification)
    
    def test_low_balance_notification_content(self):
        """Test business rule: low balance notifications contain actionable information."""
        # Business action: create low balance notification
        notification = BalanceMonitoringService.create_low_balance_notification(
            self.student, Decimal("1.5")
        )
        
        # Business rule: notification contains clear title
        self.assertEqual(notification.title, "Low Balance Alert")
        
        # Business rule: notification contains remaining hours
        self.assertIn("1.5 hours remaining", notification.message)
        
        # Business rule: notification contains actionable guidance
        self.assertIn("Please purchase more hours", notification.message)
        
        # Business rule: notification stores business context in metadata
        self.assertEqual(notification.metadata["remaining_hours"], 1.5)
        self.assertEqual(notification.metadata["alert_type"], "low_balance")
        self.assertEqual(notification.metadata["threshold_hours"], float(BalanceMonitoringService.DEFAULT_LOW_BALANCE_THRESHOLD))
    
    def test_package_expiring_notification_content(self):
        """Test business rule: package expiring notifications contain actionable information."""
        # Business scenario: package expiring in 5 days
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("50.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(days=5)
        )
        
        # Business action: create package expiring notification
        notification = BalanceMonitoringService.create_package_expiring_notification(
            self.student, transaction, days_until_expiry=5
        )
        
        # Business rule: notification contains clear title
        self.assertEqual(notification.title, "Package Expiring Soon")
        
        # Business rule: notification contains expiry timeframe
        self.assertIn("expire in 5 days", notification.message)
        
        # Business rule: notification contains actionable guidance
        self.assertIn("Please renew your package", notification.message)
        
        # Business rule: notification links to related transaction
        self.assertEqual(notification.related_transaction, transaction)
        
        # Business rule: notification stores business context in metadata
        self.assertEqual(notification.metadata["days_until_expiry"], 5)
        self.assertEqual(notification.metadata["transaction_id"], transaction.id)
        self.assertEqual(notification.metadata["alert_type"], "package_expiring")
    
    def test_balance_depleted_notification(self):
        """Test business rule: balance depleted notifications indicate urgent action needed."""
        # Business action: create balance depleted notification
        notification = BalanceMonitoringService.create_balance_depleted_notification(self.student)
        
        # Business rule: notification indicates urgency
        self.assertEqual(notification.title, "Balance Depleted")
        
        # Business rule: notification explains impact
        self.assertIn("cannot attend more lessons", notification.message)
        
        # Business rule: notification provides clear next steps
        self.assertIn("purchase additional hours", notification.message)
        
        # Business rule: notification stores zero balance context
        self.assertEqual(notification.metadata["remaining_hours"], 0.0)
        self.assertEqual(notification.metadata["alert_type"], "balance_depleted")
    
    @patch('messaging.services.EnhancedEmailService.send_template_email')
    def test_email_alert_integration(self, mock_send_email):
        """Test business rule: service integrates with email system for alerts."""
        # Business scenario: service should send email when balance is low
        mock_send_email.return_value = {'success': True, 'message': 'Email sent'}
        
        # Business action: send low balance email
        result = BalanceMonitoringService.send_low_balance_email(
            self.student, Decimal("1.5")
        )
        
        # Business rule: service uses email service
        self.assertTrue(mock_send_email.called)
        
        # Business rule: service passes correct template type
        call_args = mock_send_email.call_args
        self.assertEqual(call_args[1]['template_type'].value, 'low_balance_alert')
        
        # Business rule: service passes business context variables
        context_vars = call_args[1]['context_variables']
        self.assertEqual(context_vars['remaining_hours'], 1.5)
        self.assertEqual(context_vars['student_name'], 'Test Student')
        self.assertEqual(context_vars['school_name'], 'Test School')
        
        # Business rule: service returns email sending result
        self.assertTrue(result['success'])
    
    @patch('messaging.services.EnhancedEmailService.send_template_email')
    def test_email_alert_failure_handling(self, mock_send_email):
        """Test business rule: service handles email failures gracefully."""
        # Business scenario: email service fails
        mock_send_email.return_value = {'success': False, 'error': 'SMTP error'}
        
        # Business action: attempt to send email
        result = BalanceMonitoringService.send_low_balance_email(
            self.student, Decimal("1.5")
        )
        
        # Business rule: service captures failure result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'SMTP error')
    
    def test_comprehensive_balance_monitoring(self):
        """Test business rule: comprehensive monitoring processes all alert types."""
        # Business scenario: create conditions for multiple alert types
        
        # Low balance student
        low_balance_student = CustomUser.objects.create_user(
            email="lowbalance@test.com",
            name="Low Balance Student"
        )
        SchoolMembership.objects.create(
            user=low_balance_student,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        StudentAccountBalance.objects.create(
            student=low_balance_student,
            hours_purchased=Decimal("5.00"),
            hours_consumed=Decimal("4.00"),  # 1.0 hour remaining (below threshold)
            balance_amount=Decimal("25.00")
        )
        
        # Expiring package
        PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timedelta(days=3)  # Expires in 3 days
        )
        
        # Business action: run comprehensive monitoring
        with patch('messaging.services.BalanceMonitoringService.send_low_balance_email') as mock_low_email, \
             patch('messaging.services.BalanceMonitoringService.send_package_expiring_email') as mock_exp_email:
            
            mock_low_email.return_value = {'success': True}
            mock_exp_email.return_value = {'success': True}
            
            result = BalanceMonitoringService.monitor_all_balances()
        
        # Business rule: service processes all alert types
        self.assertIn('low_balance_alerts', result)
        self.assertIn('package_expiring_alerts', result)
        self.assertIn('total_notifications', result)
        self.assertIn('total_emails_sent', result)
        
        # Business rule: service creates appropriate notifications
        self.assertGreater(result['low_balance_alerts'], 0)
        self.assertGreater(result['package_expiring_alerts'], 0)
        
        # Business rule: service provides processing timestamp
        self.assertIn('timestamp', result)
    
    def test_service_error_resilience(self):
        """Test business rule: service continues processing despite individual errors."""
        # Business scenario: student record has issues but service should continue
        
        # Create student with balance but invalid email
        problem_student = CustomUser.objects.create_user(
            email="",  # Invalid email
            name="Problem Student"
        )
        SchoolMembership.objects.create(
            user=problem_student,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        StudentAccountBalance.objects.create(
            student=problem_student,
            hours_purchased=Decimal("5.00"),
            hours_consumed=Decimal("4.50"),  # Low balance
            balance_amount=Decimal("12.50")
        )
        
        # Create valid student with low balance
        valid_student = CustomUser.objects.create_user(
            email="valid@test.com",
            name="Valid Student"
        )
        SchoolMembership.objects.create(
            user=valid_student,
            school=self.school,
            role=SchoolRole.STUDENT,
            is_active=True
        )
        StudentAccountBalance.objects.create(
            student=valid_student,
            hours_purchased=Decimal("3.00"),
            hours_consumed=Decimal("2.50"),  # Low balance
            balance_amount=Decimal("12.50")
        )
        
        # Business action: run monitoring with some errors expected
        with patch('messaging.services.BalanceMonitoringService.send_low_balance_email') as mock_email:
            mock_email.side_effect = lambda student, hours: (
                {'success': False, 'error': 'Invalid email'} if student.email == "" 
                else {'success': True}
            )
            
            result = BalanceMonitoringService.process_low_balance_alerts()
        
        # Business rule: service continues despite errors
        self.assertGreater(result['low_balance_alerts'], 0)
        
        # Business rule: service tracks errors but doesn't stop processing
        self.assertIn('errors', result)
        
        # Business rule: service processes valid records despite invalid ones
        valid_notification = Notification.objects.filter(
            user=valid_student,
            notification_type=NotificationType.LOW_BALANCE
        ).first()
        self.assertIsNotNone(valid_notification)