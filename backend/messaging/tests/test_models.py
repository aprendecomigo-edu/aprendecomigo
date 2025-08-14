"""
Business logic tests for messaging models.

Tests core business rules for:
- Notification lifecycle and state management
- Business domain methods and constraints
- NotificationType enum business behavior
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from messaging.models import Notification, NotificationType
from messaging.tests.test_base import MessagingTestBase


class NotificationModelTest(MessagingTestBase):
    """Test case for Notification model functionality."""

    def setUp(self):
        """Set up test data."""
        super().setUp()

    def test_create_notification_with_required_fields(self):
        """Test business rule: notification can be created with required fields."""
        notification = self.create_notification(title="Low Balance Alert", message="Your balance is running low")

        # Business requirement: new notifications are unread by default
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

        # Business requirement: notifications have audit timestamps
        self.assertIsNotNone(notification.created_at)
        self.assertIsNotNone(notification.updated_at)

    def test_notification_display_includes_business_context(self):
        """Test business requirement: notification display includes user and type context."""
        notification = self.create_notification(title="Low Balance Alert", message="Your balance is running low")

        display = str(notification)
        # Business context must be clear from display
        self.assertIn("LOW_BALANCE", display)
        self.assertIn(self.student.name, display)
        self.assertIn("Low Balance Alert", display)

    def test_mark_as_read_business_rule(self):
        """Test business rule: marking notification as read sets timestamp and persists."""
        notification = self.create_notification()

        # Business rule: new notifications are unread
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

        # Business rule: mark_as_read updates both status and timestamp
        notification.mark_as_read()

        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

        # Business rule: changes are persisted automatically
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_mark_as_unread_business_rule(self):
        """Test business rule: marking notification as unread clears timestamp and persists."""
        notification = self.create_notification(is_read=True)
        notification.read_at = timezone.now()
        notification.save()

        # Business rule: mark_as_unread clears both status and timestamp
        notification.mark_as_unread()

        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

        # Business rule: changes are persisted automatically
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

    def test_all_notification_types_supported(self):
        """Test business requirement: all balance monitoring notification types are supported."""
        # Business domain: student balance monitoring notification types
        balance_monitoring_types = [
            (NotificationType.LOW_BALANCE, "Low Balance Alert"),
            (NotificationType.PACKAGE_EXPIRING, "Package Expiring Soon"),
            (NotificationType.BALANCE_DEPLETED, "Balance Depleted"),
        ]

        for notification_type, title in balance_monitoring_types:
            with self.subTest(notification_type=notification_type):
                notification = self.create_notification(
                    notification_type=notification_type, title=title, message=f"Business alert: {notification_type}"
                )

                self.assertEqual(notification.notification_type, notification_type)

    def test_link_notification_to_expiring_package(self):
        """Test business rule: package expiring notifications link to specific transaction."""
        # Business scenario: student has a package expiring in 7 days
        transaction = self.create_purchase_transaction(expires_at_days=7)

        notification = self.create_notification(
            notification_type=NotificationType.PACKAGE_EXPIRING,
            title="Package Expiring Soon",
            message="Your package expires in 7 days",
        )
        notification.related_transaction = transaction
        notification.save()

        # Business rule: notification must reference the expiring transaction
        self.assertEqual(notification.related_transaction, transaction)

    def test_store_business_context_in_metadata(self):
        """Test business rule: notifications store relevant business context in metadata."""
        business_context = {
            "remaining_hours": 1.5,
            "balance_amount": "25.50",
            "threshold_hours": 2.0,
            "alert_type": "low_balance",
        }

        notification = self.create_notification(
            title="Low Balance Alert", message="Your balance is running low", metadata=business_context
        )

        # Business rule: metadata preserves business context
        self.assertEqual(notification.metadata["remaining_hours"], 1.5)
        self.assertEqual(notification.metadata["alert_type"], "low_balance")
        self.assertEqual(notification.metadata["threshold_hours"], 2.0)

    def test_notification_display_order_business_rule(self):
        """Test business rule: notifications appear newest first for user experience."""
        notification1 = self.create_notification(title="First Notification")
        notification2 = self.create_notification(
            notification_type=NotificationType.PACKAGE_EXPIRING, title="Second Notification"
        )

        notifications = list(Notification.objects.all())

        # Business rule: newest notifications appear first
        self.assertEqual(notifications[0], notification2)
        self.assertEqual(notifications[1], notification1)

    def test_notification_requires_recipient_user(self):
        """Test business constraint: every notification must have a recipient user."""
        with self.assertRaises(IntegrityError):
            Notification.objects.create(
                notification_type=NotificationType.LOW_BALANCE,
                title="Test Notification",
                message="Test message",
                # Missing user - violates business constraint
            )

    def test_notification_content_validation(self):
        """Test business rules: notifications must have clear, actionable content."""
        # Business rule: title is required for clarity
        with self.assertRaises(ValidationError):
            notification = Notification(
                user=self.student, notification_type=NotificationType.LOW_BALANCE, message="Test message"
            )
            notification.full_clean()

        # Business rule: message is required for actionable information
        with self.assertRaises(ValidationError):
            notification = Notification(
                user=self.student, notification_type=NotificationType.LOW_BALANCE, title="Test Title"
            )
            notification.full_clean()

        # Business rule: title must be concise for user experience
        excessively_long_title = "x" * 201  # Exceeds business limit
        with self.assertRaises(ValidationError):
            notification = Notification(
                user=self.student,
                notification_type=NotificationType.LOW_BALANCE,
                title=excessively_long_title,
                message="Test message",
            )
            notification.full_clean()

    def test_notification_cascade_deletion_when_user_removed(self):
        """Test business rule: notifications are cleaned up when user account is deleted."""
        notification = self.create_notification()
        notification_id = notification.id

        # Business action: remove user account
        self.student.delete()

        # Business rule: associated notifications are automatically deleted
        with self.assertRaises(Notification.DoesNotExist):
            Notification.objects.get(id=notification_id)

    def test_notification_transaction_relationship_handles_transaction_deletion(self):
        """Test business rule: notification handles related transaction deletion gracefully."""
        transaction = self.create_purchase_transaction()
        notification = self.create_notification(
            notification_type=NotificationType.PACKAGE_EXPIRING, title="Package Expiring"
        )
        notification.related_transaction = transaction
        notification.save()

        # Business action: delete the related transaction
        transaction.delete()

        # Business rule: notification is also deleted (cascade delete)
        with self.assertRaises(Notification.DoesNotExist):
            Notification.objects.get(id=notification.id)


class NotificationTypeTest(TestCase):
    """Test business behavior of NotificationType enum."""

    def test_balance_monitoring_notification_types_completeness(self):
        """Test business requirement: all essential balance monitoring notification types are available."""
        # Business domain: student balance monitoring notification types
        required_types = [
            NotificationType.LOW_BALANCE,
            NotificationType.PACKAGE_EXPIRING,
            NotificationType.BALANCE_DEPLETED,
        ]

        # Business rule: all balance monitoring types must be available
        for notification_type in required_types:
            self.assertIn(notification_type, NotificationType.values)

    def test_notification_type_display_labels_are_user_friendly(self):
        """Test business requirement: notification types have clear, actionable display labels."""
        business_labels = {
            NotificationType.LOW_BALANCE: "Low Balance",
            NotificationType.PACKAGE_EXPIRING: "Package Expiring",
            NotificationType.BALANCE_DEPLETED: "Balance Depleted",
        }

        # Business rule: labels must be user-friendly and immediately understandable
        for notification_type, expected_label in business_labels.items():
            self.assertEqual(notification_type.label, expected_label)

    def test_notification_type_values_are_database_safe(self):
        """Test business rule: notification type values are suitable for database storage."""
        # Business rule: enum values should be concise and database-friendly
        for notification_type in NotificationType:
            value = notification_type.value

            # Should be lowercase with underscores (database convention)
            self.assertEqual(value, value.lower())
            self.assertNotIn(" ", value)  # No spaces
            self.assertNotIn("-", value)  # No hyphens, use underscores

            # Should not be excessively long
            self.assertLessEqual(len(value), 30)
