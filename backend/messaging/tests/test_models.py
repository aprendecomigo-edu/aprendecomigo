"""
Test cases for notification models - Issue #107: Student Balance Monitoring & Notification System

Tests for:
- Notification model with all fields and validation
- NotificationType enum with proper choices
- Notification model relationships and constraints
- Notification model methods and properties
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from accounts.models import CustomUser, School, SchoolMembership, SchoolRole
from finances.models import StudentAccountBalance, PurchaseTransaction, TransactionType, TransactionPaymentStatus
from messaging.models import Notification, NotificationType


class NotificationModelTest(TestCase):
    """Test case for Notification model functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            address="123 Test Street, Test City"
        )
        
        # Create test student user
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        # Create school membership for student
        SchoolMembership.objects.create(
            user=self.student,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        # Create student account balance
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("8.00"),
            balance_amount=Decimal("50.00")
        )
        
    def test_notification_creation(self):
        """Test creating a basic notification."""
        notification = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.LOW_BALANCE,
            title="Low Balance Alert",
            message="Your balance is running low",
            is_read=False
        )
        
        self.assertEqual(notification.user, self.student)
        self.assertEqual(notification.notification_type, NotificationType.LOW_BALANCE)
        self.assertEqual(notification.title, "Low Balance Alert")
        self.assertEqual(notification.message, "Your balance is running low")
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
        self.assertIsNotNone(notification.updated_at)
        self.assertIsNone(notification.read_at)
        
    def test_notification_str_representation(self):
        """Test string representation of notification."""
        notification = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.LOW_BALANCE,
            title="Low Balance Alert",
            message="Your balance is running low"
        )
        
        expected_str = f"LOW_BALANCE notification for {self.student.name}: Low Balance Alert"
        self.assertEqual(str(notification), expected_str)
        
    def test_notification_mark_as_read(self):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.LOW_BALANCE,
            title="Low Balance Alert",
            message="Your balance is running low"
        )
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        
        # Mark as read
        notification.mark_as_read()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
        
        # Verify it was saved to database
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
        
    def test_notification_mark_as_unread(self):
        """Test marking notification as unread."""
        notification = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.LOW_BALANCE,
            title="Low Balance Alert",
            message="Your balance is running low",
            is_read=True,
            read_at=timezone.now()
        )
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
        
        # Mark as unread
        notification.mark_as_unread()
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        
        # Verify it was saved to database
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        
    def test_notification_type_choices(self):
        """Test all notification type choices work correctly."""
        test_cases = [
            (NotificationType.LOW_BALANCE, "Low Balance Alert"),
            (NotificationType.PACKAGE_EXPIRING, "Package Expiring Soon"),
            (NotificationType.BALANCE_DEPLETED, "Balance Depleted")
        ]
        
        for notification_type, title in test_cases:
            with self.subTest(notification_type=notification_type):
                notification = Notification.objects.create(
                    user=self.student,
                    notification_type=notification_type,
                    title=title,
                    message=f"Test message for {notification_type}"
                )
                
                self.assertEqual(notification.notification_type, notification_type)
                
    def test_notification_related_transaction(self):
        """Test notification with related transaction."""
        # Create a transaction
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timezone.timedelta(days=7)  # Expires in 7 days
        )
        
        notification = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.PACKAGE_EXPIRING,
            title="Package Expiring Soon",
            message="Your package expires in 7 days",
            related_transaction=transaction
        )
        
        self.assertEqual(notification.related_transaction, transaction)
        
    def test_notification_metadata(self):
        """Test notification with metadata."""
        metadata = {
            "remaining_hours": 1.5,
            "expiry_date": "2025-08-08",
            "package_type": "Premium"
        }
        
        notification = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.LOW_BALANCE,
            title="Low Balance Alert",
            message="Your balance is running low",
            metadata=metadata
        )
        
        self.assertEqual(notification.metadata, metadata)
        self.assertEqual(notification.metadata["remaining_hours"], 1.5)
        
    def test_notification_ordering(self):
        """Test notification default ordering (newest first)."""
        # Create notifications with different timestamps
        notification1 = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.LOW_BALANCE,
            title="First Notification",
            message="First message"
        )
        
        notification2 = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.PACKAGE_EXPIRING,
            title="Second Notification",
            message="Second message"
        )
        
        notifications = list(Notification.objects.all())
        
        # Should be ordered by created_at descending (newest first)
        self.assertEqual(notifications[0], notification2)
        self.assertEqual(notifications[1], notification1)
        
    def test_notification_user_required(self):
        """Test that user field is required."""
        with self.assertRaises(IntegrityError):
            Notification.objects.create(
                notification_type=NotificationType.LOW_BALANCE,
                title="Test Notification",
                message="Test message"
                # Missing user field
            )
            
    def test_notification_title_required(self):
        """Test that title field is required."""
        with self.assertRaises(ValidationError):
            notification = Notification(
                user=self.student,
                notification_type=NotificationType.LOW_BALANCE,
                message="Test message"
                # Missing title field
            )
            notification.full_clean()
            
    def test_notification_message_required(self):
        """Test that message field is required."""
        with self.assertRaises(ValidationError):
            notification = Notification(
                user=self.student,
                notification_type=NotificationType.LOW_BALANCE,
                title="Test Title"
                # Missing message field
            )
            notification.full_clean()
            
    def test_notification_title_max_length(self):
        """Test title field max length constraint."""
        long_title = "x" * 201  # Exceed max_length of 200
        
        with self.assertRaises(ValidationError):
            notification = Notification(
                user=self.student,
                notification_type=NotificationType.LOW_BALANCE,
                title=long_title,
                message="Test message"
            )
            notification.full_clean()
            
    def test_notification_indexes(self):
        """Test that proper database indexes exist."""
        # This test ensures indexes are created properly
        # Create multiple notifications to test index performance
        for i in range(10):
            Notification.objects.create(
                user=self.student,
                notification_type=NotificationType.LOW_BALANCE,
                title=f"Notification {i}",
                message=f"Message {i}",
                is_read=(i % 2 == 0)  # Alternate read/unread
            )
            
        # Query that should use user index
        user_notifications = Notification.objects.filter(user=self.student)
        self.assertEqual(user_notifications.count(), 10)
        
        # Query that should use user+is_read index
        unread_notifications = Notification.objects.filter(user=self.student, is_read=False)
        self.assertEqual(unread_notifications.count(), 5)
        
        # Query that should use created_at index (for ordering)
        recent_notifications = Notification.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        )
        self.assertEqual(recent_notifications.count(), 10)


class NotificationTypeTest(TestCase):
    """Test case for NotificationType enum."""
    
    def test_notification_type_choices(self):
        """Test that all required notification types exist."""
        expected_choices = [
            NotificationType.LOW_BALANCE,
            NotificationType.PACKAGE_EXPIRING,
            NotificationType.BALANCE_DEPLETED
        ]
        
        for choice in expected_choices:
            self.assertIn(choice, NotificationType.values)
            
    def test_notification_type_labels(self):
        """Test notification type display labels."""
        expected_labels = {
            NotificationType.LOW_BALANCE: "Low Balance",
            NotificationType.PACKAGE_EXPIRING: "Package Expiring",
            NotificationType.BALANCE_DEPLETED: "Balance Depleted"
        }
        
        for choice, expected_label in expected_labels.items():
            self.assertEqual(choice.label, expected_label)
            
    def test_notification_type_values(self):
        """Test notification type string values."""
        expected_values = {
            NotificationType.LOW_BALANCE: "low_balance",
            NotificationType.PACKAGE_EXPIRING: "package_expiring",
            NotificationType.BALANCE_DEPLETED: "balance_depleted"
        }
        
        for choice, expected_value in expected_values.items():
            self.assertEqual(choice.value, expected_value)


class NotificationQuerySetTest(TestCase):
    """Test case for notification queryset methods and filters."""
    
    def setUp(self):
        """Set up test data."""
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            address="123 Test Street, Test City"
        )
        
        # Create test users
        self.student1 = CustomUser.objects.create_user(
            email="student1@test.com",
            name="Test Student 1"
        )
        
        self.student2 = CustomUser.objects.create_user(
            email="student2@test.com",
            name="Test Student 2"
        )
        
        # Create school memberships
        for student in [self.student1, self.student2]:
            SchoolMembership.objects.create(
                user=student,
                school=self.school,
                role=SchoolRole.STUDENT
            )
            
    def test_filter_by_user(self):
        """Test filtering notifications by user."""
        # Create notifications for different users
        Notification.objects.create(
            user=self.student1,
            notification_type=NotificationType.LOW_BALANCE,
            title="Student 1 Notification",
            message="Message for student 1"
        )
        
        Notification.objects.create(
            user=self.student2,
            notification_type=NotificationType.LOW_BALANCE,
            title="Student 2 Notification",
            message="Message for student 2"
        )
        
        # Filter by student1
        student1_notifications = Notification.objects.filter(user=self.student1)
        self.assertEqual(student1_notifications.count(), 1)
        self.assertEqual(student1_notifications.first().title, "Student 1 Notification")
        
        # Filter by student2
        student2_notifications = Notification.objects.filter(user=self.student2)
        self.assertEqual(student2_notifications.count(), 1)
        self.assertEqual(student2_notifications.first().title, "Student 2 Notification")
        
    def test_filter_unread_notifications(self):
        """Test filtering unread notifications."""
        # Create read and unread notifications
        Notification.objects.create(
            user=self.student1,
            notification_type=NotificationType.LOW_BALANCE,
            title="Read Notification",
            message="This notification is read",
            is_read=True,
            read_at=timezone.now()
        )
        
        Notification.objects.create(
            user=self.student1,
            notification_type=NotificationType.PACKAGE_EXPIRING,
            title="Unread Notification",
            message="This notification is unread",
            is_read=False
        )
        
        # Filter unread notifications
        unread_notifications = Notification.objects.filter(user=self.student1, is_read=False)
        self.assertEqual(unread_notifications.count(), 1)
        self.assertEqual(unread_notifications.first().title, "Unread Notification")
        
        # Filter read notifications
        read_notifications = Notification.objects.filter(user=self.student1, is_read=True)
        self.assertEqual(read_notifications.count(), 1)
        self.assertEqual(read_notifications.first().title, "Read Notification")
        
    def test_filter_by_notification_type(self):
        """Test filtering notifications by type."""
        # Create notifications of different types
        Notification.objects.create(
            user=self.student1,
            notification_type=NotificationType.LOW_BALANCE,
            title="Low Balance Notification",
            message="Your balance is low"
        )
        
        Notification.objects.create(
            user=self.student1,
            notification_type=NotificationType.PACKAGE_EXPIRING,
            title="Package Expiring Notification",
            message="Your package is expiring"
        )
        
        # Filter by LOW_BALANCE type
        low_balance_notifications = Notification.objects.filter(
            user=self.student1, 
            notification_type=NotificationType.LOW_BALANCE
        )
        self.assertEqual(low_balance_notifications.count(), 1)
        self.assertEqual(low_balance_notifications.first().title, "Low Balance Notification")
        
        # Filter by PACKAGE_EXPIRING type
        expiring_notifications = Notification.objects.filter(
            user=self.student1, 
            notification_type=NotificationType.PACKAGE_EXPIRING
        )
        self.assertEqual(expiring_notifications.count(), 1)
        self.assertEqual(expiring_notifications.first().title, "Package Expiring Notification")