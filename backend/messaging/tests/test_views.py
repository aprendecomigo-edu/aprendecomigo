"""
Test cases for notification API endpoints - Issue #107: Student Balance Monitoring & Notification System

Tests for:
- GET /api/notifications/ - List user notifications with pagination
- POST /api/notifications/{id}/read/ - Mark notification as read
- GET /api/notifications/unread-count/ - Get unread count for UI badge
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from knox.models import AuthToken

from accounts.models import CustomUser, School, SchoolMembership, SchoolRole
from finances.models import StudentAccountBalance, PurchaseTransaction, TransactionType, TransactionPaymentStatus
from messaging.models import Notification, NotificationType


class NotificationAPITestCase(TestCase):
    """Base test case for notification API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create test school
        self.school = School.objects.create(
            name="Test School",
            description="A test school",
            address="123 Test Street, Test City"
        )
        
        # Create test users
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        self.other_student = CustomUser.objects.create_user(
            email="other@test.com",
            name="Other Student"
        )
        
        # Create school memberships
        SchoolMembership.objects.create(
            user=self.student,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        SchoolMembership.objects.create(
            user=self.other_student,
            school=self.school,
            role=SchoolRole.STUDENT
        )
        
        # Create student account balances
        self.student_balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal("10.00"),
            hours_consumed=Decimal("8.00"),
            balance_amount=Decimal("50.00")
        )
        
        # Set up API client
        self.client = APIClient()
        
        # Create auth token for student
        self.token = AuthToken.objects.create(self.student)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        
    def create_notification(self, user=None, notification_type=NotificationType.LOW_BALANCE, 
                          title="Test Notification", message="Test message", is_read=False):
        """Helper method to create a notification."""
        if user is None:
            user = self.student
            
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            is_read=is_read
        )


class NotificationListAPITest(NotificationAPITestCase):
    """Test case for notification list API endpoint."""
    
    def test_list_user_notifications(self):
        """Test listing notifications for authenticated user."""
        # Create notifications for the student
        notification1 = self.create_notification(
            title="Low Balance Alert", 
            message="Your balance is running low"
        )
        notification2 = self.create_notification(
            title="Package Expiring", 
            message="Your package expires soon",
            notification_type=NotificationType.PACKAGE_EXPIRING
        )
        
        # Create notification for other student (should not appear)
        self.create_notification(
            user=self.other_student,
            title="Other Student Notification",
            message="This should not appear"
        )
        
        url = reverse('messaging:notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Check that results are ordered by created_at descending (newest first)
        self.assertEqual(response.data['results'][0]['id'], notification2.id)
        self.assertEqual(response.data['results'][1]['id'], notification1.id)
        
        # Check notification content
        first_notification = response.data['results'][0]
        self.assertEqual(first_notification['title'], "Package Expiring")
        self.assertEqual(first_notification['message'], "Your package expires soon")
        self.assertEqual(first_notification['notification_type'], NotificationType.PACKAGE_EXPIRING)
        self.assertEqual(first_notification['is_read'], False)
        self.assertIsNone(first_notification['read_at'])
        
    def test_list_notifications_empty(self):
        """Test listing notifications when user has none."""
        url = reverse('messaging:notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['count'], 0)
        
    def test_list_notifications_unauthenticated(self):
        """Test that unauthenticated users cannot access notifications."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('messaging:notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_list_notifications_pagination(self):
        """Test notification list pagination."""
        # Create many notifications
        for i in range(25):
            self.create_notification(
                title=f"Notification {i}",
                message=f"Message {i}"
            )
            
        url = reverse('messaging:notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 25)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        
        # Test getting second page
        response = self.client.get(response.data['next'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])
        
    def test_list_notifications_filter_by_type(self):
        """Test filtering notifications by type."""
        # Create notifications of different types
        low_balance = self.create_notification(
            notification_type=NotificationType.LOW_BALANCE,
            title="Low Balance"
        )
        expiring = self.create_notification(
            notification_type=NotificationType.PACKAGE_EXPIRING,
            title="Package Expiring"
        )
        depleted = self.create_notification(
            notification_type=NotificationType.BALANCE_DEPLETED,
            title="Balance Depleted"
        )
        
        # Filter by LOW_BALANCE
        url = reverse('messaging:notification-list')
        response = self.client.get(url, {'notification_type': NotificationType.LOW_BALANCE})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], low_balance.id)
        
        # Filter by PACKAGE_EXPIRING
        response = self.client.get(url, {'notification_type': NotificationType.PACKAGE_EXPIRING})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], expiring.id)
        
    def test_list_notifications_filter_by_read_status(self):
        """Test filtering notifications by read status."""
        # Create read and unread notifications
        read_notification = self.create_notification(
            title="Read Notification",
            is_read=True
        )
        read_notification.read_at = timezone.now()
        read_notification.save()
        
        unread_notification = self.create_notification(
            title="Unread Notification",
            is_read=False
        )
        
        # Filter by unread
        url = reverse('messaging:notification-list')
        response = self.client.get(url, {'is_read': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], unread_notification.id)
        
        # Filter by read
        response = self.client.get(url, {'is_read': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], read_notification.id)


class NotificationMarkAsReadAPITest(NotificationAPITestCase):
    """Test case for mark notification as read API endpoint."""
    
    def test_mark_notification_as_read(self):
        """Test marking a notification as read."""
        notification = self.create_notification(
            title="Test Notification",
            message="Test message",
            is_read=False
        )
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        
        url = reverse('messaging:notification-mark-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Notification marked as read')
        
        # Verify notification was updated
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
        
    def test_mark_already_read_notification(self):
        """Test marking an already read notification as read."""
        notification = self.create_notification(
            title="Already Read",
            message="Already read message",
            is_read=True
        )
        notification.read_at = timezone.now()
        notification.save()
        
        original_read_at = notification.read_at
        
        url = reverse('messaging:notification-mark-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Notification marked as read')
        
        # Verify read_at timestamp didn't change
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertEqual(notification.read_at, original_read_at)
        
    def test_mark_notification_as_read_not_found(self):
        """Test marking non-existent notification as read."""
        url = reverse('messaging:notification-mark-read', kwargs={'pk': 99999})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_mark_notification_as_read_other_user(self):
        """Test marking another user's notification as read (should fail)."""
        other_notification = self.create_notification(
            user=self.other_student,
            title="Other User Notification",
            message="Should not be accessible"
        )
        
        url = reverse('messaging:notification-mark-read', kwargs={'pk': other_notification.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify the notification wasn't modified
        other_notification.refresh_from_db()
        self.assertFalse(other_notification.is_read)
        self.assertIsNone(other_notification.read_at)
        
    def test_mark_notification_as_read_unauthenticated(self):
        """Test that unauthenticated users cannot mark notifications as read."""
        notification = self.create_notification()
        
        self.client.credentials()  # Remove authentication
        
        url = reverse('messaging:notification-mark-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationUnreadCountAPITest(NotificationAPITestCase):
    """Test case for notification unread count API endpoint."""
    
    def test_get_unread_count_empty(self):
        """Test getting unread count when user has no notifications."""
        url = reverse('messaging:notification-unread-count')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 0)
        
    def test_get_unread_count_with_notifications(self):
        """Test getting unread count with mixed read/unread notifications."""
        # Create unread notifications
        self.create_notification(title="Unread 1", is_read=False)
        self.create_notification(title="Unread 2", is_read=False)
        self.create_notification(title="Unread 3", is_read=False)
        
        # Create read notifications
        read_notification = self.create_notification(title="Read 1", is_read=True)
        read_notification.read_at = timezone.now()
        read_notification.save()
        
        # Create notification for other user (should not count)
        self.create_notification(
            user=self.other_student,
            title="Other User Unread",
            is_read=False
        )
        
        url = reverse('messaging:notification-unread-count')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 3)
        
    def test_get_unread_count_all_read(self):
        """Test getting unread count when all notifications are read."""
        # Create read notifications
        for i in range(5):
            notification = self.create_notification(
                title=f"Read Notification {i}",
                is_read=True
            )
            notification.read_at = timezone.now()
            notification.save()
            
        url = reverse('messaging:notification-unread-count')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 0)
        
    def test_get_unread_count_unauthenticated(self):
        """Test that unauthenticated users cannot get unread count."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('messaging:notification-unread-count')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_unread_count_updates_after_marking_read(self):
        """Test that unread count updates after marking notifications as read."""
        # Create unread notifications
        notification1 = self.create_notification(title="Unread 1", is_read=False)
        notification2 = self.create_notification(title="Unread 2", is_read=False)
        
        # Check initial count
        url = reverse('messaging:notification-unread-count')
        response = self.client.get(url)
        self.assertEqual(response.data['unread_count'], 2)
        
        # Mark one as read
        mark_read_url = reverse('messaging:notification-mark-read', kwargs={'pk': notification1.pk})
        self.client.post(mark_read_url)
        
        # Check updated count
        response = self.client.get(url)
        self.assertEqual(response.data['unread_count'], 1)
        
        # Mark the other as read
        mark_read_url = reverse('messaging:notification-mark-read', kwargs={'pk': notification2.pk})
        self.client.post(mark_read_url)
        
        # Check final count
        response = self.client.get(url)
        self.assertEqual(response.data['unread_count'], 0)


class NotificationAPIIntegrationTest(NotificationAPITestCase):
    """Integration tests for notification API endpoints."""
    
    def test_notification_api_workflow(self):
        """Test complete notification API workflow."""
        # 1. Initially no notifications
        list_url = reverse('messaging:notification-list')
        count_url = reverse('messaging:notification-unread-count')
        
        response = self.client.get(list_url)
        self.assertEqual(len(response.data['results']), 0)
        
        response = self.client.get(count_url)
        self.assertEqual(response.data['unread_count'], 0)
        
        # 2. Create notifications
        notification1 = self.create_notification(
            title="Balance Low",
            message="Your balance is running low",
            notification_type=NotificationType.LOW_BALANCE
        )
        
        notification2 = self.create_notification(
            title="Package Expiring",
            message="Your package expires in 7 days",
            notification_type=NotificationType.PACKAGE_EXPIRING
        )
        
        # 3. List notifications
        response = self.client.get(list_url)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['id'], notification2.id)  # Newest first
        self.assertEqual(response.data['results'][1]['id'], notification1.id)
        
        # 4. Check unread count
        response = self.client.get(count_url)
        self.assertEqual(response.data['unread_count'], 2)
        
        # 5. Mark one as read
        mark_read_url = reverse('messaging:notification-mark-read', kwargs={'pk': notification1.pk})
        response = self.client.post(mark_read_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 6. Check updated unread count
        response = self.client.get(count_url)
        self.assertEqual(response.data['unread_count'], 1)
        
        # 7. Filter by unread
        response = self.client.get(list_url, {'is_read': 'false'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], notification2.id)
        
        # 8. Filter by read
        response = self.client.get(list_url, {'is_read': 'true'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], notification1.id)
        
    def test_notification_with_transaction_relationship(self):
        """Test notification with related transaction."""
        # Create a transaction
        transaction = PurchaseTransaction.objects.create(
            student=self.student,
            transaction_type=TransactionType.PACKAGE,
            amount=Decimal("100.00"),
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        # Create notification with transaction
        notification = Notification.objects.create(
            user=self.student,
            notification_type=NotificationType.PACKAGE_EXPIRING,
            title="Package Expiring Soon",
            message="Your package expires in 7 days",
            related_transaction=transaction
        )
        
        # Test listing includes transaction data
        list_url = reverse('messaging:notification-list')
        response = self.client.get(list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        notification_data = response.data['results'][0]
        self.assertEqual(notification_data['id'], notification.id)
        self.assertIsNotNone(notification_data.get('related_transaction'))
        
    def test_notification_metadata_support(self):
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
        
        # Test listing includes metadata
        list_url = reverse('messaging:notification-list')
        response = self.client.get(list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification_data = response.data['results'][0]
        self.assertEqual(notification_data['metadata'], metadata)