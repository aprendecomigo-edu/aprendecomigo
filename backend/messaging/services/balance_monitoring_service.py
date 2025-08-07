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

from accounts.models import CustomUser, SchoolMembership, SchoolRole
from messaging.models import EmailTemplateType, EmailCommunicationType
from messaging.services.enhanced_email_service import EnhancedEmailService

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
            
            # Get all accounts and filter by computed remaining hours
            # Since remaining_hours is a property, we need to filter in Python
            all_accounts = StudentAccountBalance.objects.select_related('student').all()
            
            result = []
            for account in all_accounts:
                remaining_hours = account.remaining_hours
                if 0 < remaining_hours < threshold:  # Still has some balance but below threshold
                    result.append({
                        'student_id': account.student.id,
                        'student_email': account.student.email,
                        'balance_hours': remaining_hours,
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
            
            # Import the enum to use the correct value
            from finances.models import TransactionPaymentStatus
            
            expiring_packages = PurchaseTransaction.objects.filter(
                expires_at__lte=cutoff_date,
                expires_at__gte=timezone.now(),
                payment_status=TransactionPaymentStatus.COMPLETED
            ).select_related('student')
            
            result = []
            for package in expiring_packages:
                result.append({
                    'student_id': package.student.id,
                    'student_email': package.student.email,
                    'package_id': package.id,
                    'expiry_date': package.expires_at,
                    'days_until_expiry': (package.expires_at - timezone.now()).days
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
                user_id=student_id,
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
            Created notification object or None if recent notification exists or creation failed
        """
        try:
            # Check for recent notification to prevent spam
            from messaging.models import NotificationType
            if cls.has_recent_notification(student_id, NotificationType.LOW_BALANCE):
                logger.info(f"Skipping low balance notification for student {student_id} - recent notification exists")
                return None
            
            # Use lazy loading to avoid cross-app import issues
            Notification = apps.get_model('messaging', 'Notification')
            
            notification = Notification.objects.create(
                user_id=student_id,
                notification_type=NotificationType.LOW_BALANCE,
                title="Low Balance Alert",
                message=f"Your account balance is low ({balance_hours} hours remaining). Please purchase more hours to continue scheduling classes.",
                metadata={
                    'remaining_hours': float(balance_hours),
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
    def create_package_expiring_notification(cls, student: Any, transaction: Any, days_until_expiry: int) -> Optional[Any]:
        """
        Create a package expiring notification for a student.
        
        Args:
            student: Student user object
            transaction: Transaction that's expiring
            days_until_expiry: Days until expiry
            
        Returns:
            Created notification object or None if failed
        """
        try:
            # Use lazy loading to avoid cross-app import issues
            Notification = apps.get_model('messaging', 'Notification')
            from messaging.models import NotificationType
            
            student_id = student.id if hasattr(student, 'id') else student
            package_id = transaction.id if hasattr(transaction, 'id') else transaction
            expiry_date = transaction.expires_at if hasattr(transaction, 'expires_at') else timezone.now() + timedelta(days=days_until_expiry)
            
            notification = Notification.objects.create(
                user_id=student_id,
                notification_type=NotificationType.PACKAGE_EXPIRING,
                title="Package Expiring Soon",
                message=f"Your class package will expire in {days_until_expiry} days. Please renew your package to continue scheduling classes.",
                related_transaction_id=package_id,
                metadata={
                    'package_id': package_id,
                    'transaction_id': package_id,
                    'expiry_date': expiry_date.isoformat() if hasattr(expiry_date, 'isoformat') else str(expiry_date),
                    'days_until_expiry': days_until_expiry,
                    'alert_type': 'package_expiring'
                }
            )
            
            logger.info(f"Created package expiring notification {notification.id} for student {student_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating package expiring notification: {e}")
            return None
    
    @classmethod
    def create_balance_depleted_notification(cls, student_id: int) -> Optional[Any]:
        """
        Create a balance depleted notification for a student.
        
        Args:
            student_id: Student ID to notify
            
        Returns:
            Created notification object or None if failed
        """
        try:
            # Use lazy loading to avoid cross-app import issues
            Notification = apps.get_model('messaging', 'Notification')
            from messaging.models import NotificationType
            
            notification = Notification.objects.create(
                user_id=student_id,
                notification_type=NotificationType.BALANCE_DEPLETED,
                title="Balance Depleted",
                message="Your account balance has been depleted and you cannot attend more lessons until you purchase additional hours.",
                metadata={
                    'remaining_hours': 0.0,
                    'alert_type': 'balance_depleted'
                }
            )
            
            logger.info(f"Created balance depleted notification {notification.id} for student {student_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating balance depleted notification for student {student_id}: {e}")
            return None
    
    @classmethod
    def monitor_all_balances(cls) -> Dict[str, Any]:
        """
        Monitor all student balances and trigger notifications as needed.
        
        Returns:
            Summary of monitoring results
        """
        logger.info("Starting balance monitoring process")
        
        try:
            # Process low balance alerts
            balance_results = cls.process_low_balance_alerts()
            
            # Process package expiring alerts
            package_results = cls.process_package_expiring_alerts()
            
            # Combine results
            combined_result = {
                'timestamp': timezone.now().isoformat(),
                'low_balance_alerts': balance_results['low_balance_alerts'],
                'balance_depleted_alerts': balance_results.get('balance_depleted_alerts', 0),
                'package_expiring_alerts': package_results['package_expiring_alerts'],
                'total_notifications': (
                    balance_results['low_balance_alerts'] + 
                    balance_results.get('balance_depleted_alerts', 0) + 
                    package_results['package_expiring_alerts']
                ),
                'total_emails_sent': balance_results['emails_sent'] + package_results['emails_sent'],
                'errors': balance_results['errors'] + package_results['errors']
            }
            
            logger.info(f"Balance monitoring completed: {combined_result}")
            return combined_result
            
        except Exception as e:
            logger.error(f"Error in monitor_all_balances: {e}", exc_info=True)
            return {
                'timestamp': timezone.now().isoformat(),
                'low_balance_alerts': 0,
                'balance_depleted_alerts': 0,
                'package_expiring_alerts': 0,
                'total_notifications': 0,
                'total_emails_sent': 0,
                'errors': [str(e)]
            }
    
    @classmethod
    def send_low_balance_email(cls, student: CustomUser, remaining_hours: Decimal) -> Dict[str, Any]:
        """
        Send low balance email notification to student.
        
        Args:
            student: Student user
            remaining_hours: Remaining hours in balance
            
        Returns:
            Email sending result
        """
        try:
            # Get student's school for email template
            membership = SchoolMembership.objects.filter(
                user=student,
                role=SchoolRole.STUDENT,
                is_active=True
            ).select_related('school').first()
            
            if not membership:
                logger.warning(f"No active school membership found for student {student.email}")
                return {'success': False, 'error': 'No active school membership'}
            
            school = membership.school
            
            # Get balance information
            try:
                StudentAccountBalance = apps.get_model('finances', 'StudentAccountBalance')
                balance = StudentAccountBalance.objects.get(student=student)
                balance_amount = balance.balance_amount
            except Exception:
                balance_amount = Decimal('0.00')
            
            # Prepare email context
            context_variables = {
                'student_name': student.name,
                'remaining_hours': float(remaining_hours),
                'balance_amount': str(balance_amount),
                'school_name': school.name,
                'support_email': school.contact_email or 'support@aprendecomigo.com'
            }
            
            # Send email using enhanced email service
            result = EnhancedEmailService.send_template_email(
                school=school,
                template_type=EmailTemplateType.LOW_BALANCE_ALERT,
                recipient_email=student.email,
                context_variables=context_variables,
                communication_type=EmailCommunicationType.AUTOMATED
            )
            
            logger.info(f"Sent low balance email to {student.email}: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending low balance email to {student.email}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def send_package_expiring_email(cls, student: CustomUser, transaction: Any, days_until_expiry: int) -> Dict[str, Any]:
        """
        Send package expiring email notification to student.
        
        Args:
            student: Student user
            transaction: Expiring transaction
            days_until_expiry: Days until expiry
            
        Returns:
            Email sending result
        """
        try:
            # Get student's school for email template
            membership = SchoolMembership.objects.filter(
                user=student,
                role=SchoolRole.STUDENT,
                is_active=True
            ).select_related('school').first()
            
            if not membership:
                logger.warning(f"No active school membership found for student {student.email}")
                return {'success': False, 'error': 'No active school membership'}
            
            school = membership.school
            
            # Prepare email context
            context_variables = {
                'student_name': student.name,
                'package_type': 'Class Package',
                'days_until_expiry': days_until_expiry,
                'expiry_date': transaction.expires_at.strftime('%Y-%m-%d') if hasattr(transaction, 'expires_at') else 'Unknown',
                'school_name': school.name,
                'support_email': school.contact_email or 'support@aprendecomigo.com'
            }
            
            # Send email using enhanced email service
            result = EnhancedEmailService.send_template_email(
                school=school,
                template_type=EmailTemplateType.PACKAGE_EXPIRING_ALERT,
                recipient_email=student.email,
                context_variables=context_variables,
                communication_type=EmailCommunicationType.AUTOMATED
            )
            
            logger.info(f"Sent package expiring email to {student.email}: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending package expiring email to {student.email}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def process_low_balance_alerts(cls) -> Dict[str, Any]:
        """
        Process low balance alerts for all students.
        
        Returns:
            Processing results summary
        """
        try:
            low_balance_students = cls.check_low_balance_students()
            notifications_sent = 0
            emails_sent = 0
            errors = []
            
            for student_data in low_balance_students:
                try:
                    student_id = student_data['student_id']
                    balance_hours = student_data['balance_hours']
                    threshold = student_data['threshold']
                    
                    # Get student object
                    User = apps.get_model('accounts', 'CustomUser')
                    student = User.objects.get(id=student_id)
                    
                    # Create notification if not recent
                    from messaging.models import NotificationType
                    if not cls.has_recent_notification(student_id, NotificationType.LOW_BALANCE):
                        notification = cls.create_low_balance_notification(
                            student_id, balance_hours, threshold
                        )
                        if notification:
                            notifications_sent += 1
                    
                    # Send email alert
                    email_result = cls.send_low_balance_email(student, balance_hours)
                    if email_result.get('success'):
                        emails_sent += 1
                    else:
                        errors.append(f"Failed to send email to {student.email}: {email_result.get('error')}")
                        
                except Exception as e:
                    errors.append(f"Error processing student {student_data.get('student_id', 'unknown')}: {str(e)}")
            
            result = {
                'low_balance_alerts': notifications_sent,
                'emails_sent': emails_sent,
                'errors': errors,
                'total_students_processed': len(low_balance_students)
            }
            
            logger.info(f"Low balance alert processing completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in process_low_balance_alerts: {e}", exc_info=True)
            return {
                'low_balance_alerts': 0,
                'emails_sent': 0,
                'errors': [str(e)],
                'total_students_processed': 0
            }
    
    @classmethod
    def process_package_expiring_alerts(cls) -> Dict[str, Any]:
        """
        Process all package expiring alerts.
        
        Creates notifications and sends emails for packages expiring soon.
        
        Returns:
            Summary of processing results
        """
        result = {
            'package_expiring_alerts': 0,
            'emails_sent': 0,
            'errors': []
        }
        
        try:
            # Get packages expiring soon
            expiring_packages = cls.check_expiring_packages()
            
            for package_data in expiring_packages:
                try:
                    # Get student and transaction info
                    student_id = package_data['student_id']
                    package_id = package_data['package_id'] 
                    days_until_expiry = package_data['days_until_expiry']
                    
                    # Get student object
                    User = apps.get_model('accounts', 'CustomUser')
                    student = User.objects.get(id=student_id)
                    
                    # Get transaction object
                    PurchaseTransaction = apps.get_model('finances', 'PurchaseTransaction')
                    transaction = PurchaseTransaction.objects.get(id=package_id)
                    
                    # Create notification
                    notification = cls.create_package_expiring_notification(
                        student, transaction, days_until_expiry
                    )
                    if notification:
                        result['package_expiring_alerts'] += 1
                    
                    # Send email notification
                    email_result = cls.send_package_expiring_email(
                        student, transaction, days_until_expiry
                    )
                    if email_result.get('success'):
                        result['emails_sent'] += 1
                    else:
                        result['errors'].append(f"Email failed for {student.email}: {email_result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Error processing package expiring alert for package {package_data.get('package_id', 'unknown')}: {str(e)}")
                    result['errors'].append(f"Error processing package {package_data.get('package_id', 'unknown')}: {str(e)}")
            
            logger.info(f"Processed package expiring alerts: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing package expiring alerts: {str(e)}")
            return {
                'package_expiring_alerts': 0,
                'emails_sent': 0,
                'errors': [str(e)]
            }
