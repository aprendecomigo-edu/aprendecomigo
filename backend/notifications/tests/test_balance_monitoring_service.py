"""
Test cases for BalanceMonitoringService - Issue #107: Student Balance Monitoring & Notification System

Tests for:
- Checking students with low balance (< 2 hours remaining)
- Detecting packages expiring within 7 days
- Creating in-app notifications
- Sending email alerts using existing template system
- Duplicate prevention (no spam alerts)
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock

from accounts.models import CustomUser, School, SchoolMembership, SchoolRole
from finances.models import StudentAccountBalance, PurchaseTransaction, TransactionType, TransactionPaymentStatus
from notifications.models import Notification, NotificationType
from notifications.services import BalanceMonitoringService


class BalanceMonitoringServiceTest(TestCase):
    """Test case for BalanceMonitoringService functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            address="123 Test Street, Test City"
        )
        
        # Create test students
        self.student1 = CustomUser.objects.create_user(
            email="student1@test.com",
            name="Test Student 1"
        )
        
        self.student2 = CustomUser.objects.create_user(
            email="student2@test.com",
            name="Test Student 2"
        )
        
        self.student3 = CustomUser.objects.create_user(
            email="student3@test.com",
            name="Test Student 3"
        )
        
        # Create school memberships
        for student in [self.student1, self.student2, self.student3]:
            SchoolMembership.objects.create(
                user=student,
                school=self.school,
                role=SchoolRole.STUDENT
            )
            
        # Create student account balances
        # Student 1: Low balance (1.5 hours remaining)
        self.balance1 = StudentAccountBalance.objects.create(
            student=self.student1,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("8.50"),
            balance_amount=Decimal("30.00")
        )
        
        # Student 2: Normal balance (5 hours remaining)
        self.balance2 = StudentAccountBalance.objects.create(
            student=self.student2,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("5.00"),
            balance_amount=Decimal("100.00")
        )
        
        # Student 3: Depleted balance (0 hours remaining)
        self.balance3 = StudentAccountBalance.objects.create(
            student=self.student3,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("10.00"),
            balance_amount=Decimal("0.00")
        )
        
    def test_check_low_balance_students(self):
        """Test identifying students with low balance."""
        students = BalanceMonitoringService.check_low_balance_students()
        
        # Should include student1 (1.5 hours) and student3 (0 hours)
        student_ids = [student.id for student in students]
        self.assertIn(self.student1.id, student_ids)
        self.assertIn(self.student3.id, student_ids)
        self.assertNotIn(self.student2.id, student_ids)  # Has 5 hours, not low
        
    def test_check_low_balance_students_custom_threshold(self):
        """Test low balance check with custom threshold."""
        students = BalanceMonitoringService.check_low_balance_students(threshold_hours=6)
        
        # With threshold of 6, all students should be included
        student_ids = [student.id for student in students]
        self.assertIn(self.student1.id, student_ids)  # 1.5 hours
        self.assertIn(self.student2.id, student_ids)  # 5 hours
        self.assertIn(self.student3.id, student_ids)  # 0 hours
        
    def test_check_expiring_packages(self):
        """Test identifying packages expiring within 7 days."""
        # Create transactions with different expiry dates
        # Transaction expiring in 5 days (should be detected)
        expiring_transaction = PurchaseTransaction.objects.create(
            student=self.student1,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timezone.timedelta(days=5)
        )
        
        # Transaction expiring in 10 days (should not be detected)
        future_transaction = PurchaseTransaction.objects.create(
            student=self.student2,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timezone.timedelta(days=10)
        )
        
        # Transaction already expired (should not be detected)
        expired_transaction = PurchaseTransaction.objects.create(
            student=self.student3,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() - timezone.timedelta(days=1)
        )
        
        transactions = BalanceMonitoringService.check_expiring_packages()
        
        # Should only include the transaction expiring in 5 days
        transaction_ids = [t.id for t in transactions]
        self.assertIn(expiring_transaction.id, transaction_ids)
        self.assertNotIn(future_transaction.id, transaction_ids)
        self.assertNotIn(expired_transaction.id, transaction_ids)
        
    def test_check_expiring_packages_custom_days(self):
        """Test expiring packages check with custom days ahead."""
        # Create transaction expiring in 5 days
        expiring_transaction = PurchaseTransaction.objects.create(
            student=self.student1,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timezone.timedelta(days=5)
        )
        
        # With 3 days ahead, should not be detected
        transactions = BalanceMonitoringService.check_expiring_packages(days_ahead=3)
        self.assertEqual(len(transactions), 0)
        
        # With 10 days ahead, should be detected
        transactions = BalanceMonitoringService.check_expiring_packages(days_ahead=10)
        transaction_ids = [t.id for t in transactions]
        self.assertIn(expiring_transaction.id, transaction_ids)
        
    def test_create_low_balance_notification(self):
        """Test creating low balance notifications."""
        # Initially no notifications
        self.assertEqual(Notification.objects.count(), 0)
        
        # Create notification for student1
        notification = BalanceMonitoringService.create_low_balance_notification(
            self.student1, 
            remaining_hours=1.5
        )
        
        # Verify notification was created
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.user, self.student1)
        self.assertEqual(notification.notification_type, NotificationType.LOW_BALANCE)
        self.assertIn("1.5", notification.message)
        self.assertFalse(notification.is_read)
        
        # Check metadata
        self.assertEqual(notification.metadata['remaining_hours'], 1.5)
        self.assertIn('balance_amount', notification.metadata)
        
    def test_create_package_expiring_notification(self):
        """Test creating package expiring notifications."""
        # Create transaction
        transaction = PurchaseTransaction.objects.create(
            student=self.student1,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timezone.timedelta(days=5)
        )
        
        # Initially no notifications
        self.assertEqual(Notification.objects.count(), 0)
        
        # Create notification
        notification = BalanceMonitoringService.create_package_expiring_notification(
            self.student1,
            transaction,
            days_until_expiry=5
        )
        
        # Verify notification was created
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.user, self.student1)
        self.assertEqual(notification.notification_type, NotificationType.PACKAGE_EXPIRING)
        self.assertEqual(notification.related_transaction, transaction)
        self.assertIn("5 days", notification.message)
        self.assertFalse(notification.is_read)
        
        # Check metadata
        self.assertEqual(notification.metadata['days_until_expiry'], 5)
        self.assertEqual(notification.metadata['package_amount'], str(transaction.amount))
        
    def test_create_balance_depleted_notification(self):
        """Test creating balance depleted notifications."""
        # Initially no notifications
        self.assertEqual(Notification.objects.count(), 0)
        
        # Create notification for student3 (has 0 balance)
        notification = BalanceMonitoringService.create_balance_depleted_notification(
            self.student3
        )
        
        # Verify notification was created
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.user, self.student3)
        self.assertEqual(notification.notification_type, NotificationType.BALANCE_DEPLETED)
        self.assertIn("depleted", notification.message.lower())
        self.assertFalse(notification.is_read)
        
    def test_duplicate_prevention_recent_notification(self):
        """Test that duplicate notifications are not created for recent alerts."""
        # Create an existing recent notification (within 24 hours)
        existing_notification = Notification.objects.create(
            user=self.student1,
            notification_type=NotificationType.LOW_BALANCE,
            title="Low Balance Alert",
            message="Your balance is running low"
        )
        # Manually update created_at since auto_now_add can't be overridden
        existing_notification.created_at = timezone.now() - timezone.timedelta(hours=12)
        existing_notification.save(update_fields=['created_at'])
        
        # Try to create another low balance notification
        notification = BalanceMonitoringService.create_low_balance_notification(
            self.student1,
            remaining_hours=1.5
        )
        
        # Should return None (no duplicate created)
        self.assertIsNone(notification)
        self.assertEqual(Notification.objects.count(), 1)  # Still only the original
        
    def test_duplicate_prevention_old_notification(self):
        """Test that notifications can be created if old notification exists."""
        # Create an old notification (more than 24 hours ago)
        old_notification = Notification.objects.create(
            user=self.student1,
            notification_type=NotificationType.LOW_BALANCE,
            title="Low Balance Alert",
            message="Your balance is running low"
        )
        # Manually update created_at since auto_now_add can't be overridden
        old_notification.created_at = timezone.now() - timezone.timedelta(hours=30)
        old_notification.save(update_fields=['created_at'])
        
        # Try to create another low balance notification
        notification = BalanceMonitoringService.create_low_balance_notification(
            self.student1,
            remaining_hours=1.5
        )
        
        # Should create new notification
        self.assertIsNotNone(notification)
        self.assertEqual(Notification.objects.count(), 2)  # Original + new
        
    @patch('notifications.services.EnhancedEmailService.send_template_email')
    def test_send_low_balance_email(self, mock_send_email):
        """Test sending low balance email notification."""
        mock_send_email.return_value = {'success': True, 'email_communication_id': 123}
        
        # Send email
        result = BalanceMonitoringService.send_low_balance_email(
            self.student1,
            remaining_hours=1.5
        )
        
        # Verify email service was called
        self.assertTrue(mock_send_email.called)
        args, kwargs = mock_send_email.call_args
        
        # Check arguments
        self.assertEqual(kwargs['school'], self.school)
        self.assertEqual(kwargs['recipient_email'], self.student1.email)
        self.assertEqual(kwargs['context_variables']['student_name'], self.student1.name)
        self.assertEqual(kwargs['context_variables']['remaining_hours'], 1.5)
        
        # Check result
        self.assertTrue(result['success'])
        
    @patch('notifications.services.EnhancedEmailService.send_template_email')
    def test_send_package_expiring_email(self, mock_send_email):
        """Test sending package expiring email notification."""
        mock_send_email.return_value = {'success': True, 'email_communication_id': 123}
        
        # Create transaction
        transaction = PurchaseTransaction.objects.create(
            student=self.student1,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timezone.timedelta(days=5)
        )
        
        # Send email
        result = BalanceMonitoringService.send_package_expiring_email(
            self.student1,
            transaction,
            days_until_expiry=5
        )
        
        # Verify email service was called
        self.assertTrue(mock_send_email.called)
        args, kwargs = mock_send_email.call_args
        
        # Check arguments
        self.assertEqual(kwargs['school'], self.school)
        self.assertEqual(kwargs['recipient_email'], self.student1.email)
        self.assertEqual(kwargs['context_variables']['student_name'], self.student1.name)
        self.assertEqual(kwargs['context_variables']['days_until_expiry'], 5)
        self.assertEqual(kwargs['context_variables']['package_amount'], transaction.amount)
        
        # Check result
        self.assertTrue(result['success'])
        
    @patch('notifications.services.BalanceMonitoringService.send_low_balance_email')
    def test_process_low_balance_alerts(self, mock_send_email):
        """Test processing low balance alerts end-to-end."""
        mock_send_email.return_value = {'success': True}
        
        # Initially no notifications
        self.assertEqual(Notification.objects.count(), 0)
        
        # Process alerts
        result = BalanceMonitoringService.process_low_balance_alerts()
        
        # Should create low balance notifications for students with hours remaining but < 2
        low_balance_notifications = Notification.objects.filter(notification_type=NotificationType.LOW_BALANCE)
        
        # Only Student1 (1.5 hours) should get low balance notification
        # Student3 (0 hours) gets depleted notification instead
        student_ids = [n.user.id for n in low_balance_notifications]
        self.assertIn(self.student1.id, student_ids)
        self.assertNotIn(self.student3.id, student_ids)  # Gets depleted instead
        self.assertNotIn(self.student2.id, student_ids)  # Has 5 hours
        
        # Should also create balance depleted notification for student3
        depleted_notifications = Notification.objects.filter(
            notification_type=NotificationType.BALANCE_DEPLETED
        )
        self.assertEqual(depleted_notifications.count(), 1)
        self.assertEqual(depleted_notifications.first().user, self.student3)
        
        # Should attempt to send emails
        self.assertTrue(mock_send_email.called)
        
        # Check result summary
        self.assertEqual(result['low_balance_alerts'], 1)  # Only student1 (student3 gets depleted)
        self.assertEqual(result['balance_depleted_alerts'], 1)  # student3
        self.assertEqual(result['emails_sent'], 2)  # Both students get emails
        
    @patch('notifications.services.BalanceMonitoringService.send_package_expiring_email')
    def test_process_package_expiring_alerts(self, mock_send_email):
        """Test processing package expiring alerts end-to-end."""
        mock_send_email.return_value = {'success': True}
        
        # Create expiring transaction
        transaction = PurchaseTransaction.objects.create(
            student=self.student1,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timezone.timedelta(days=5)
        )
        
        # Initially no notifications
        self.assertEqual(Notification.objects.count(), 0)
        
        # Process alerts
        result = BalanceMonitoringService.process_package_expiring_alerts()
        
        # Should create notification for expiring package
        notifications = Notification.objects.filter(
            notification_type=NotificationType.PACKAGE_EXPIRING
        )
        self.assertEqual(notifications.count(), 1)
        
        notification = notifications.first()
        self.assertEqual(notification.user, self.student1)
        self.assertEqual(notification.related_transaction, transaction)
        
        # Should attempt to send email
        self.assertTrue(mock_send_email.called)
        
        # Check result summary
        self.assertEqual(result['package_expiring_alerts'], 1)
        self.assertEqual(result['emails_sent'], 1)
        
    @patch('notifications.services.BalanceMonitoringService.process_low_balance_alerts')
    @patch('notifications.services.BalanceMonitoringService.process_package_expiring_alerts')
    def test_monitor_all_balances(self, mock_package_alerts, mock_balance_alerts):
        """Test monitoring all balances (main entry point)."""
        mock_balance_alerts.return_value = {
            'low_balance_alerts': 2,
            'balance_depleted_alerts': 1,
            'emails_sent': 2,
            'errors': []
        }
        
        mock_package_alerts.return_value = {
            'package_expiring_alerts': 1,
            'emails_sent': 1,
            'errors': []
        }
        
        # Run monitoring
        result = BalanceMonitoringService.monitor_all_balances()
        
        # Both processing methods should be called
        self.assertTrue(mock_balance_alerts.called)
        self.assertTrue(mock_package_alerts.called)
        
        # Check combined result
        self.assertEqual(result['total_notifications'], 4)  # 2 + 1 + 1
        self.assertEqual(result['total_emails_sent'], 3)  # 2 + 1
        self.assertEqual(len(result['errors']), 0)
        
    def test_error_handling_invalid_student(self):
        """Test error handling when creating notifications for invalid data."""
        # Try to create notification with None student
        notification = BalanceMonitoringService.create_low_balance_notification(
            None,
            remaining_hours=1.5
        )
        
        # Should handle gracefully
        self.assertIsNone(notification)
        self.assertEqual(Notification.objects.count(), 0)
        
    def test_error_handling_invalid_transaction(self):
        """Test error handling when creating notifications for invalid transaction."""
        # Try to create notification with None transaction
        notification = BalanceMonitoringService.create_package_expiring_notification(
            self.student1,
            None,
            days_until_expiry=5
        )
        
        # Should handle gracefully
        self.assertIsNone(notification)
        self.assertEqual(Notification.objects.count(), 0)