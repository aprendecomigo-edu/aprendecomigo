"""
Balance Monitoring Service for student account balance alerts.

This service handles monitoring of student account balances and
triggers notifications when balances are low or packages are expiring.
"""

import logging
from decimal import Decimal
from datetime import timedelta, datetime
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.apps import apps


logger = logging.getLogger(__name__)


class BalanceMonitoringService:
    """
    Service for monitoring student account balances and triggering alerts.
    
    This service implements business logic for:
    - Low balance detection
    - Package expiration monitoring
    - Notification deduplication
    - Alert generation
    """
    
    DEFAULT_LOW_BALANCE_THRESHOLD = Decimal('2.0')  # 2 hours remaining
    DEFAULT_EXPIRY_WARNING_DAYS = 3  # 3 days before expiration
    
    @classmethod
    def check_low_balance_students(cls, threshold: Optional[Decimal] = None) -> List[Dict[str, Any]]:
        """
        Check for students with low account balances.
        
        Args:
            threshold: Balance threshold in hours (defaults to DEFAULT_LOW_BALANCE_THRESHOLD)
            
        Returns:
            List of student balance information for low balance accounts
        """
        if threshold is None:
            threshold = cls.DEFAULT_LOW_BALANCE_THRESHOLD
            
        try:
            # Use lazy loading to avoid cross-app import issues
            StudentAccountBalance = apps.get_model('finances', 'StudentAccountBalance')
            
            low_balance_accounts = StudentAccountBalance.objects.filter(
                balance_hours__lt=threshold,
                balance_hours__gt=0  # Still has some balance
            ).select_related('student')
            
            result = []
            for account in low_balance_accounts:
                result.append({
                    'student_id': account.student.id,
                    'student_email': account.student.email,
                    'balance_hours': account.balance_hours,
                    'threshold': threshold,
                    'account_id': account.id
                })
            
            logger.info(f"Found {len(result)} students with low balance (threshold: {threshold}h)")
            return result
            
        except Exception as e:
            logger.error(f"Error checking low balance students: {e}", exc_info=True)
            return []
    
    @classmethod
    def check_expiring_packages(cls, expiry_days: int = DEFAULT_EXPIRY_WARNING_DAYS) -> List[Dict[str, Any]]:
        """
        Check for packages that are expiring soon.
        
        Args:
            expiry_days: Number of days before expiration to trigger warning
            
        Returns:
            List of package expiration information
        """
        try:
            # Use lazy loading to avoid cross-app import issues
            PurchaseTransaction = apps.get_model('finances', 'PurchaseTransaction')
            
            cutoff_date = timezone.now() + timedelta(days=expiry_days)
            
            expiring_packages = PurchaseTransaction.objects.filter(
                package_expiry_date__lte=cutoff_date,
                package_expiry_date__gte=timezone.now(),
                payment_status='completed'
            ).select_related('student')
            
            result = []
            for package in expiring_packages:
                result.append({
                    'student_id': package.student.id,
                    'student_email': package.student.email,
                    'package_id': package.id,
                    'expiry_date': package.package_expiry_date,
                    'days_until_expiry': (package.package_expiry_date - timezone.now()).days
                })
            
            logger.info(f"Found {len(result)} packages expiring within {expiry_days} days")
            return result
            
        except Exception as e:
            logger.error(f"Error checking expiring packages: {e}", exc_info=True)
            return []
    
    @classmethod
    def has_recent_notification(cls, student_id: int, notification_type: str, 
                              hours_threshold: int = 24) -> bool:
        """
        Check if a student has received a recent notification of the given type.
        
        Args:
            student_id: Student ID to check
            notification_type: Type of notification to check for
            hours_threshold: Hours to look back for recent notifications
            
        Returns:
            True if recent notification exists, False otherwise
        """
        try:
            # Use lazy loading to avoid cross-app import issues
            Notification = apps.get_model('messaging', 'Notification')
            
            cutoff_time = timezone.now() - timedelta(hours=hours_threshold)
            
            recent_notification = Notification.objects.filter(
                student_id=student_id,
                notification_type=notification_type,
                created_at__gte=cutoff_time
            ).exists()
            
            return recent_notification
            
        except Exception as e:
            logger.error(f"Error checking recent notifications for student {student_id}: {e}")
            return False
    
    @classmethod
    def create_low_balance_notification(cls, student_id: int, balance_hours: Decimal,
                                      threshold: Decimal) -> Optional[Any]:
        """
        Create a low balance notification for a student.
        
        Args:
            student_id: Student ID to notify
            balance_hours: Current balance in hours
            threshold: Threshold that triggered the notification
            
        Returns:
            Created notification object or None if failed
        """
        try:
            # Use lazy loading to avoid cross-app import issues
            Notification = apps.get_model('messaging', 'Notification')
            NotificationType = apps.get_model('messaging', 'NotificationType')
            
            notification = Notification.objects.create(
                student_id=student_id,
                notification_type=NotificationType.BALANCE_LOW,
                title="Low Account Balance Warning",
                message=f"Your account balance is low ({balance_hours} hours remaining). Please top up to continue scheduling classes.",
                metadata={
                    'balance_hours': float(balance_hours),
                    'threshold_hours': float(threshold),
                    'alert_type': 'low_balance'
                }
            )
            
            logger.info(f"Created low balance notification {notification.id} for student {student_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating low balance notification for student {student_id}: {e}")
            return None
    
    @classmethod
    def create_package_expiring_notification(cls, student_id: int, package_id: int,
                                           expiry_date: datetime) -> Optional[Any]:
        """
        Create a package expiring notification for a student.
        
        Args:
            student_id: Student ID to notify
            package_id: Package ID that's expiring
            expiry_date: When the package expires
            
        Returns:
            Created notification object or None if failed
        """
        try:
            # Use lazy loading to avoid cross-app import issues
            Notification = apps.get_model('messaging', 'Notification')
            NotificationType = apps.get_model('messaging', 'NotificationType')
            
            days_until_expiry = (expiry_date - timezone.now()).days
            
            notification = Notification.objects.create(
                student_id=student_id,
                notification_type=NotificationType.PACKAGE_EXPIRING,
                title="Package Expiring Soon",
                message=f"Your class package will expire in {days_until_expiry} days. Please renew to continue scheduling classes.",
                metadata={
                    'package_id': package_id,
                    'expiry_date': expiry_date.isoformat(),
                    'days_until_expiry': days_until_expiry,
                    'alert_type': 'package_expiring'
                }
            )
            
            logger.info(f"Created package expiring notification {notification.id} for student {student_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating package expiring notification for student {student_id}: {e}")
            return None
    
    @classmethod
    def monitor_all_balances(cls) -> Dict[str, Any]:
        """
        Monitor all student balances and trigger notifications as needed.
        
        Returns:
            Summary of monitoring results
        """
        try:
            # Check low balances
            low_balance_students = cls.check_low_balance_students()
            low_balance_notifications = 0
            
            for student_data in low_balance_students:
                # Check if already notified recently
                if not cls.has_recent_notification(
                    student_data['student_id'], 
                    'balance_low',
                    hours_threshold=24
                ):
                    notification = cls.create_low_balance_notification(
                        student_data['student_id'],
                        student_data['balance_hours'],
                        student_data['threshold']
                    )
                    if notification:
                        low_balance_notifications += 1
            
            # Check expiring packages
            expiring_packages = cls.check_expiring_packages()
            expiring_notifications = 0
            
            for package_data in expiring_packages:
                # Check if already notified recently
                if not cls.has_recent_notification(
                    package_data['student_id'],
                    'package_expiring',
                    hours_threshold=48  # Check for notifications in last 48 hours
                ):
                    notification = cls.create_package_expiring_notification(
                        package_data['student_id'],
                        package_data['package_id'],
                        package_data['expiry_date']
                    )
                    if notification:
                        expiring_notifications += 1
            
            result = {
                'success': True,
                'low_balance_students': len(low_balance_students),
                'low_balance_notifications_sent': low_balance_notifications,
                'expiring_packages': len(expiring_packages),
                'expiring_notifications_sent': expiring_notifications,
                'total_notifications_sent': low_balance_notifications + expiring_notifications
            }
            
            logger.info(f"Balance monitoring completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in monitor_all_balances: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'low_balance_students': 0,
                'low_balance_notifications_sent': 0,
                'expiring_packages': 0,
                'expiring_notifications_sent': 0,
                'total_notifications_sent': 0
            }
