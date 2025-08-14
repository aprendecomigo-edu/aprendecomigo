"""
Balance Monitoring Service - Issue #107: Student Balance Monitoring & Notification System

Service for automated checking of student balances and creating notifications/emails.
Handles:
- Checking students with < 2 hours remaining
- Detecting packages expiring within 7 days
- Creating in-app notifications
- Sending email alerts using existing template system
- Duplicate prevention (no spam alerts)
"""

from datetime import timedelta
from decimal import Decimal
import logging
from typing import Any

from django.utils import timezone

from accounts.models import CustomUser, SchoolMembership, SchoolRole
from finances.models import PurchaseTransaction, StudentAccountBalance, TransactionPaymentStatus, TransactionType
from messaging.models import EmailCommunicationType, EmailTemplateType

from .models import Notification, NotificationType
from .services.enhanced_email_service import EnhancedEmailService

logger = logging.getLogger(__name__)


class BalanceMonitoringService:
    """
    Service for monitoring student balances and sending notifications.

    This service handles automated checking for low balances and expiring packages,
    creating in-app notifications, and sending email alerts to students.
    """

    # Default thresholds
    DEFAULT_LOW_BALANCE_THRESHOLD = Decimal("2.0")  # 2 hours
    DEFAULT_PACKAGE_EXPIRY_DAYS = 7  # 7 days ahead
    DEFAULT_NOTIFICATION_COOLDOWN = 24  # 24 hours between duplicate notifications

    @classmethod
    def check_low_balance_students(cls, threshold_hours: Decimal | None = None) -> list[CustomUser]:
        """
        Get students with low balance (remaining hours below threshold).

        Args:
            threshold_hours: Hours threshold for low balance (default: 2.0)

        Returns:
            List of CustomUser instances with low balance
        """
        if threshold_hours is None:
            threshold_hours = cls.DEFAULT_LOW_BALANCE_THRESHOLD

        try:
            # Get all student account balances where remaining hours < threshold
            low_balance_students = []

            for balance in StudentAccountBalance.objects.select_related("student").all():
                remaining_hours = balance.remaining_hours
                if remaining_hours < threshold_hours:
                    low_balance_students.append(balance.student)

            logger.info(f"Found {len(low_balance_students)} students with balance below {threshold_hours} hours")
            return low_balance_students

        except Exception as e:
            logger.error(f"Error checking low balance students: {e!s}")
            return []

    @classmethod
    def check_expiring_packages(cls, days_ahead: int | None = None) -> list[PurchaseTransaction]:
        """
        Get packages expiring within specified days.

        Args:
            days_ahead: Number of days ahead to check (default: 7)

        Returns:
            List of PurchaseTransaction instances expiring soon
        """
        if days_ahead is None:
            days_ahead = cls.DEFAULT_PACKAGE_EXPIRY_DAYS

        try:
            cutoff_date = timezone.now() + timedelta(days=days_ahead)

            expiring_transactions = PurchaseTransaction.objects.filter(
                transaction_type=TransactionType.PACKAGE,
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at__isnull=False,
                expires_at__gt=timezone.now(),  # Not already expired
                expires_at__lte=cutoff_date,  # Expires within days_ahead
            ).select_related("student")

            logger.info(f"Found {expiring_transactions.count()} packages expiring within {days_ahead} days")
            return list(expiring_transactions)

        except Exception as e:
            logger.error(f"Error checking expiring packages: {e!s}")
            return []

    @classmethod
    def has_recent_notification(
        cls, user: CustomUser, notification_type: NotificationType, cooldown_hours: int | None = None
    ) -> bool:
        """
        Check if user has received a recent notification of the same type.

        Args:
            user: User to check
            notification_type: Type of notification
            cooldown_hours: Hours to check back (default: 24)

        Returns:
            True if recent notification exists, False otherwise
        """
        if cooldown_hours is None:
            cooldown_hours = cls.DEFAULT_NOTIFICATION_COOLDOWN

        cutoff_time = timezone.now() - timedelta(hours=cooldown_hours)

        return Notification.objects.filter(
            user=user, notification_type=notification_type, created_at__gt=cutoff_time
        ).exists()

    @classmethod
    def create_low_balance_notification(cls, student: CustomUser, remaining_hours: Decimal) -> Notification | None:
        """
        Create low balance notification for a student.

        Args:
            student: Student user
            remaining_hours: Remaining hours in their balance

        Returns:
            Created Notification instance or None if duplicate/error
        """
        try:
            if not student:
                logger.warning("Cannot create notification: student is None")
                return None

            # Check for recent notifications to prevent spam
            if cls.has_recent_notification(student, NotificationType.LOW_BALANCE):
                logger.info(f"Skipping duplicate low balance notification for {student.email}")
                return None

            # Get student's balance information
            try:
                balance = StudentAccountBalance.objects.get(student=student)
                balance_amount = balance.balance_amount
            except StudentAccountBalance.DoesNotExist:
                balance_amount = Decimal("0.00")

            # Create notification
            notification = Notification.objects.create(
                user=student,
                notification_type=NotificationType.LOW_BALANCE,
                title="Low Balance Alert",
                message=f"Your account balance is running low. You have {remaining_hours} hours remaining. "
                f"Please purchase more hours to continue your lessons.",
                metadata={
                    "remaining_hours": float(remaining_hours),
                    "balance_amount": str(balance_amount),
                    "threshold_hours": float(cls.DEFAULT_LOW_BALANCE_THRESHOLD),
                    "alert_type": "low_balance",
                },
            )

            logger.info(f"Created low balance notification for {student.email} ({remaining_hours} hours remaining)")
            return notification

        except Exception as e:
            logger.error(f"Error creating low balance notification for {student.email if student else 'None'}: {e!s}")
            return None

    @classmethod
    def create_package_expiring_notification(
        cls, student: CustomUser, transaction: PurchaseTransaction, days_until_expiry: int
    ) -> Notification | None:
        """
        Create package expiring notification for a student.

        Args:
            student: Student user
            transaction: Expiring transaction
            days_until_expiry: Days until the package expires

        Returns:
            Created Notification instance or None if duplicate/error
        """
        try:
            if not student or not transaction:
                logger.warning("Cannot create notification: student or transaction is None")
                return None

            # Check for recent notifications to prevent spam
            if cls.has_recent_notification(student, NotificationType.PACKAGE_EXPIRING):
                logger.info(f"Skipping duplicate package expiring notification for {student.email}")
                return None

            # Create notification
            notification = Notification.objects.create(
                user=student,
                notification_type=NotificationType.PACKAGE_EXPIRING,
                title="Package Expiring Soon",
                message=f"Your learning package will expire in {days_until_expiry} days. "
                f"Please renew your package to continue accessing your lessons.",
                related_transaction=transaction,
                metadata={
                    "days_until_expiry": days_until_expiry,
                    "package_amount": str(transaction.amount),
                    "expiry_date": transaction.expires_at.isoformat() if transaction.expires_at else None,
                    "transaction_id": transaction.id,
                    "alert_type": "package_expiring",
                },
            )

            logger.info(
                f"Created package expiring notification for {student.email} (expires in {days_until_expiry} days)"
            )
            return notification

        except Exception as e:
            logger.error(
                f"Error creating package expiring notification for {student.email if student else 'None'}: {e!s}"
            )
            return None

    @classmethod
    def create_balance_depleted_notification(cls, student: CustomUser) -> Notification | None:
        """
        Create balance depleted notification for a student.

        Args:
            student: Student user with depleted balance

        Returns:
            Created Notification instance or None if duplicate/error
        """
        try:
            if not student:
                logger.warning("Cannot create notification: student is None")
                return None

            # Check for recent notifications to prevent spam
            if cls.has_recent_notification(student, NotificationType.BALANCE_DEPLETED):
                logger.info(f"Skipping duplicate balance depleted notification for {student.email}")
                return None

            # Create notification
            notification = Notification.objects.create(
                user=student,
                notification_type=NotificationType.BALANCE_DEPLETED,
                title="Balance Depleted",
                message="Your account balance has been depleted. You cannot attend more lessons until you "
                "purchase additional hours. Please contact your school or purchase more hours to continue.",
                metadata={"remaining_hours": 0.0, "alert_type": "balance_depleted"},
            )

            logger.info(f"Created balance depleted notification for {student.email}")
            return notification

        except Exception as e:
            logger.error(
                f"Error creating balance depleted notification for {student.email if student else 'None'}: {e!s}"
            )
            return None

    @classmethod
    def send_low_balance_email(cls, student: CustomUser, remaining_hours: Decimal) -> dict[str, Any]:
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
            membership = (
                SchoolMembership.objects.filter(user=student, role=SchoolRole.STUDENT, is_active=True)
                .select_related("school")
                .first()
            )

            if not membership:
                logger.warning(f"No active school membership found for student {student.email}")
                return {"success": False, "error": "No active school membership"}

            school = membership.school

            # Get balance information
            try:
                balance = StudentAccountBalance.objects.get(student=student)
                balance_amount = balance.balance_amount
            except StudentAccountBalance.DoesNotExist:
                balance_amount = Decimal("0.00")

            # Prepare email context
            context_variables = {
                "student_name": student.name,
                "remaining_hours": float(remaining_hours),
                "balance_amount": str(balance_amount),
                "school_name": school.name,
                "support_email": school.contact_email or "support@aprendecomigo.com",
            }

            # Send email using enhanced email service
            result = EnhancedEmailService.send_template_email(
                school=school,
                template_type=EmailTemplateType.LOW_BALANCE_ALERT,
                recipient_email=student.email,
                context_variables=context_variables,
                communication_type=EmailCommunicationType.AUTOMATED,
            )

            logger.info(f"Sent low balance email to {student.email}: {result.get('success', False)}")
            return result

        except Exception as e:
            logger.error(f"Error sending low balance email to {student.email}: {e!s}")
            return {"success": False, "error": str(e)}

    @classmethod
    def send_package_expiring_email(
        cls, student: CustomUser, transaction: PurchaseTransaction, days_until_expiry: int
    ) -> dict[str, Any]:
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
            membership = (
                SchoolMembership.objects.filter(user=student, role=SchoolRole.STUDENT, is_active=True)
                .select_related("school")
                .first()
            )

            if not membership:
                logger.warning(f"No active school membership found for student {student.email}")
                return {"success": False, "error": "No active school membership"}

            school = membership.school

            # Prepare email context
            context_variables = {
                "student_name": student.name,
                "days_until_expiry": days_until_expiry,
                "package_amount": transaction.amount,
                "expiry_date": transaction.expires_at.strftime("%B %d, %Y") if transaction.expires_at else "Unknown",
                "school_name": school.name,
                "support_email": school.contact_email or "support@aprendecomigo.com",
            }

            # Send email using enhanced email service
            result = EnhancedEmailService.send_template_email(
                school=school,
                template_type=EmailTemplateType.PACKAGE_EXPIRING_ALERT,
                recipient_email=student.email,
                context_variables=context_variables,
                communication_type=EmailCommunicationType.AUTOMATED,
            )

            logger.info(f"Sent package expiring email to {student.email}: {result.get('success', False)}")
            return result

        except Exception as e:
            logger.error(f"Error sending package expiring email to {student.email}: {e!s}")
            return {"success": False, "error": str(e)}

    @classmethod
    def process_low_balance_alerts(cls) -> dict[str, Any]:
        """
        Process all low balance alerts.

        Creates notifications and sends emails for students with low balances.

        Returns:
            Summary of processing results
        """
        result = {"low_balance_alerts": 0, "balance_depleted_alerts": 0, "emails_sent": 0, "errors": []}

        try:
            # Get students with low balance
            low_balance_students = cls.check_low_balance_students()

            for student in low_balance_students:
                try:
                    # Get remaining hours
                    balance = StudentAccountBalance.objects.get(student=student)
                    remaining_hours = balance.remaining_hours

                    # Create appropriate notification
                    if remaining_hours <= 0:
                        # Balance is completely depleted
                        notification = cls.create_balance_depleted_notification(student)
                        if notification:
                            result["balance_depleted_alerts"] += 1
                    else:
                        # Low balance but not depleted
                        notification = cls.create_low_balance_notification(student, remaining_hours)
                        if notification:
                            result["low_balance_alerts"] += 1

                    # Send email notification
                    email_result = cls.send_low_balance_email(student, remaining_hours)
                    if email_result.get("success"):
                        result["emails_sent"] += 1
                    else:
                        result["errors"].append(f"Email failed for {student.email}: {email_result.get('error')}")

                except StudentAccountBalance.DoesNotExist:
                    logger.warning(f"No balance found for student {student.email}")
                    result["errors"].append(f"No balance found for {student.email}")
                except Exception as e:
                    logger.error(f"Error processing low balance alert for {student.email}: {e!s}")
                    result["errors"].append(f"Error processing {student.email}: {e!s}")

            logger.info(f"Processed low balance alerts: {result}")
            return result

        except Exception as e:
            logger.error(f"Error processing low balance alerts: {e!s}")
            result["errors"].append(str(e))
            return result

    @classmethod
    def process_package_expiring_alerts(cls) -> dict[str, Any]:
        """
        Process all package expiring alerts.

        Creates notifications and sends emails for packages expiring soon.

        Returns:
            Summary of processing results
        """
        result = {"package_expiring_alerts": 0, "emails_sent": 0, "errors": []}

        try:
            # Get packages expiring soon
            expiring_transactions = cls.check_expiring_packages()

            for transaction in expiring_transactions:
                try:
                    student = transaction.student

                    # Calculate days until expiry
                    days_until_expiry = (transaction.expires_at - timezone.now()).days

                    # Create notification
                    notification = cls.create_package_expiring_notification(student, transaction, days_until_expiry)
                    if notification:
                        result["package_expiring_alerts"] += 1

                    # Send email notification
                    email_result = cls.send_package_expiring_email(student, transaction, days_until_expiry)
                    if email_result.get("success"):
                        result["emails_sent"] += 1
                    else:
                        result["errors"].append(f"Email failed for {student.email}: {email_result.get('error')}")

                except Exception as e:
                    logger.error(f"Error processing package expiring alert for transaction {transaction.id}: {e!s}")
                    result["errors"].append(f"Error processing transaction {transaction.id}: {e!s}")

            logger.info(f"Processed package expiring alerts: {result}")
            return result

        except Exception as e:
            logger.error(f"Error processing package expiring alerts: {e!s}")
            result["errors"].append(str(e))
            return result

    @classmethod
    def monitor_all_balances(cls) -> dict[str, Any]:
        """
        Main entry point for balance monitoring.

        Processes all types of balance-related alerts.

        Returns:
            Combined summary of all processing results
        """
        logger.info("Starting balance monitoring process")

        # Process low balance alerts
        balance_results = cls.process_low_balance_alerts()

        # Process package expiring alerts
        package_results = cls.process_package_expiring_alerts()

        # Combine results
        combined_result = {
            "timestamp": timezone.now().isoformat(),
            "low_balance_alerts": balance_results["low_balance_alerts"],
            "balance_depleted_alerts": balance_results["balance_depleted_alerts"],
            "package_expiring_alerts": package_results["package_expiring_alerts"],
            "total_notifications": (
                balance_results["low_balance_alerts"]
                + balance_results["balance_depleted_alerts"]
                + package_results["package_expiring_alerts"]
            ),
            "total_emails_sent": balance_results["emails_sent"] + package_results["emails_sent"],
            "errors": balance_results["errors"] + package_results["errors"],
        }

        logger.info(f"Balance monitoring completed: {combined_result}")
        return combined_result
