"""
Package Expiration Management Service.

This service handles the core business logic for:
- Automatic package expiration detection and processing
- Student notification system for upcoming expirations
- Package extension and renewal workflows
- Bulk expiration processing efficiency
- Grace periods and extension policies
- Comprehensive audit logging
- Integration with existing hour consumption and balance systems

Following GitHub Issue #33: "Create Package Expiration Management"
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Sum, Count

from finances.models import (
    PurchaseTransaction,
    StudentAccountBalance,
    HourConsumption,
    TransactionPaymentStatus,
    TransactionType,
)

logger = logging.getLogger(__name__)


@dataclass
class ExpirationResult:
    """Result object for package expiration processing."""
    success: bool
    package_id: int
    student_id: int
    hours_expired: Decimal
    processed_at: datetime
    audit_log: str
    error_message: str = ""


@dataclass
class NotificationResult:
    """Result object for notification sending."""
    success: bool
    notification_type: str
    recipient: str
    message: str
    sent_at: Optional[datetime] = None


@dataclass
class ExtensionResult:
    """Result object for package extension operations."""
    success: bool
    package_id: int
    original_expiry: datetime
    new_expiry: datetime
    extension_days: int
    audit_log: str
    error_message: str = ""


@dataclass
class RenewalResult:
    """Result object for package renewal operations."""
    success: bool
    original_package_id: int
    new_package_id: Optional[int]
    audit_log: str
    error_message: str = ""


class PackageExpirationService:
    """Service for managing package expiration lifecycle."""

    @staticmethod
    def get_expired_packages() -> List[PurchaseTransaction]:
        """
        Get all packages that have expired.
        
        Returns:
            List[PurchaseTransaction]: Expired packages
        """
        now = timezone.now()
        return list(
            PurchaseTransaction.objects.filter(
                transaction_type=TransactionType.PACKAGE,
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at__lt=now
            ).select_related('student')
        )

    @staticmethod
    def get_packages_expiring_soon(days_ahead: int = 7) -> List[PurchaseTransaction]:
        """
        Get packages expiring within specified number of days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List[PurchaseTransaction]: Packages expiring soon
        """
        now = timezone.now()
        cutoff_date = now + timedelta(days=days_ahead)
        
        return list(
            PurchaseTransaction.objects.filter(
                transaction_type=TransactionType.PACKAGE,
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at__gte=now,
                expires_at__lte=cutoff_date
            ).select_related('student')
        )

    @staticmethod
    def get_expired_packages_for_student(student) -> List[PurchaseTransaction]:
        """
        Get expired packages for a specific student.
        
        Args:
            student: Student user object
            
        Returns:
            List[PurchaseTransaction]: Student's expired packages
        """
        now = timezone.now()
        return list(
            PurchaseTransaction.objects.filter(
                student=student,
                transaction_type=TransactionType.PACKAGE,
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at__lt=now
            )
        )

    @staticmethod
    def get_expired_packages_outside_grace_period(grace_hours: int = 24) -> List[PurchaseTransaction]:
        """
        Get packages that expired outside the grace period.
        
        Args:
            grace_hours: Grace period in hours
            
        Returns:
            List[PurchaseTransaction]: Packages outside grace period
        """
        now = timezone.now()
        grace_cutoff = now - timedelta(hours=grace_hours)
        
        return list(
            PurchaseTransaction.objects.filter(
                transaction_type=TransactionType.PACKAGE,
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at__lt=grace_cutoff
            ).select_related('student')
        )

    @staticmethod
    def calculate_hours_to_expire(package: PurchaseTransaction) -> Decimal:
        """
        Calculate how many hours should be expired from a package.
        
        Args:
            package: Package transaction to calculate for
            
        Returns:
            Decimal: Hours to expire (total hours - consumed hours)
        """
        # Get total hours from package metadata
        total_hours = Decimal(str(package.metadata.get('hours_included', 0)))
        
        # Get consumed hours for this package
        consumed_hours = HourConsumption.objects.filter(
            purchase_transaction=package
        ).aggregate(
            total=Sum('hours_consumed')
        )['total'] or Decimal('0.00')
        
        # Return remaining hours to expire
        return max(total_hours - consumed_hours, Decimal('0.00'))

    @staticmethod
    @transaction.atomic
    def process_expired_package(package: PurchaseTransaction) -> ExpirationResult:
        """
        Process a single expired package.
        
        Args:
            package: Expired package to process
            
        Returns:
            ExpirationResult: Processing result
        """
        try:
            # Calculate hours to expire
            hours_to_expire = PackageExpirationService.calculate_hours_to_expire(package)
            
            # Update student balance if there are hours to expire
            if hours_to_expire > Decimal('0.00'):
                balance = StudentAccountBalance.objects.get(student=package.student)
                balance.hours_purchased -= hours_to_expire
                balance.save(update_fields=['hours_purchased', 'updated_at'])
            
            # Create audit log
            audit_log = (
                f"Package {package.id} expired for student {package.student.id} "
                f"({package.student.name}). {hours_to_expire} hours expired. "
                f"Processed at {timezone.now()}"
            )
            
            # Log the expiration
            logger.info(audit_log)
            
            return ExpirationResult(
                success=True,
                package_id=package.id,
                student_id=package.student.id,
                hours_expired=hours_to_expire,
                processed_at=timezone.now(),
                audit_log=audit_log
            )
            
        except Exception as e:
            error_msg = f"Error processing expired package {package.id}: {str(e)}"
            logger.error(error_msg)
            
            return ExpirationResult(
                success=False,
                package_id=package.id,
                student_id=package.student.id,
                hours_expired=Decimal('0.00'),
                processed_at=timezone.now(),
                audit_log="",
                error_message=error_msg
            )

    @staticmethod
    def process_bulk_expiration(grace_hours: int = 24) -> List[ExpirationResult]:
        """
        Process all expired packages outside grace period.
        
        Args:
            grace_hours: Grace period in hours
            
        Returns:
            List[ExpirationResult]: Processing results for all packages
        """
        expired_packages = PackageExpirationService.get_expired_packages_outside_grace_period(
            grace_hours=grace_hours
        )
        
        results = []
        for package in expired_packages:
            result = PackageExpirationService.process_expired_package(package)
            results.append(result)
        
        logger.info(f"Processed {len(results)} expired packages")
        return results

    @staticmethod
    def send_expiration_warning(
        package: PurchaseTransaction, 
        days_until_expiry: int,
        respect_preferences: bool = True
    ) -> NotificationResult:
        """
        Send expiration warning email to student.
        
        Args:
            package: Package expiring soon
            days_until_expiry: Days until expiration
            respect_preferences: Whether to respect student notification preferences
            
        Returns:
            NotificationResult: Notification sending result
        """
        try:
            student = package.student
            
            # Check notification preferences if requested
            if respect_preferences:
                preferences = getattr(student, 'metadata', None) or {}
                if not preferences.get('email_notifications', True):
                    return NotificationResult(
                        success=False,
                        notification_type='email',
                        recipient=student.email,
                        message="Notifications disabled for this student"
                    )
            
            # Prepare email content
            subject = f"Package Expiring Soon - {days_until_expiry} Days Remaining"
            message = (
                f"Dear {student.name},\n\n"
                f"Your tutoring package (€{package.amount}) will expire in {days_until_expiry} days "
                f"on {package.expires_at.strftime('%B %d, %Y')}.\n\n"
                f"To continue your tutoring sessions, please consider extending your package "
                f"or purchasing a new one.\n\n"
                f"Best regards,\n"
                f"Aprende Comigo Team"
            )
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=False
            )
            
            return NotificationResult(
                success=True,
                notification_type='email',
                recipient=student.email,
                message="Expiration warning sent successfully",
                sent_at=timezone.now()
            )
            
        except Exception as e:
            error_msg = f"Error sending expiration warning: {str(e)}"
            logger.error(error_msg)
            
            return NotificationResult(
                success=False,
                notification_type='email',
                recipient=package.student.email,
                message=error_msg
            )

    @staticmethod
    def send_expiration_confirmation(
        package: PurchaseTransaction, 
        hours_expired: Decimal
    ) -> NotificationResult:
        """
        Send expiration confirmation email after processing.
        
        Args:
            package: Expired package
            hours_expired: Hours that were expired
            
        Returns:
            NotificationResult: Notification sending result
        """
        try:
            student = package.student
            
            # Prepare email content
            subject = "Package Expired - Hours Removed from Account"
            message = (
                f"Dear {student.name},\n\n"
                f"Your tutoring package (€{package.amount}) has expired and "
                f"{hours_expired} unused hours have been removed from your account.\n\n"
                f"To continue your tutoring sessions, please purchase a new package.\n\n"
                f"Best regards,\n"
                f"Aprende Comigo Team"
            )
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=False
            )
            
            return NotificationResult(
                success=True,
                notification_type='email',
                recipient=student.email,
                message="Expiration confirmation sent successfully",
                sent_at=timezone.now()
            )
            
        except Exception as e:
            error_msg = f"Error sending expiration confirmation: {str(e)}"
            logger.error(error_msg)
            
            return NotificationResult(
                success=False,
                notification_type='email',
                recipient=package.student.email,
                message=error_msg
            )

    @staticmethod
    def send_batch_expiration_warnings(
        packages: List[PurchaseTransaction], 
        days_until_expiry: int
    ) -> List[NotificationResult]:
        """
        Send expiration warnings to multiple students efficiently.
        
        Args:
            packages: Packages expiring soon
            days_until_expiry: Days until expiration
            
        Returns:
            List[NotificationResult]: Notification results for all packages
        """
        results = []
        for package in packages:
            result = PackageExpirationService.send_expiration_warning(
                package, days_until_expiry
            )
            results.append(result)
        
        logger.info(f"Sent {len(results)} expiration warning notifications")
        return results

    @staticmethod
    @transaction.atomic
    def extend_package_expiration(
        package: PurchaseTransaction,
        extension_days: int,
        reason: str = "",
        extend_from_now: bool = False
    ) -> ExtensionResult:
        """
        Extend a package expiration date.
        
        Args:
            package: Package to extend
            extension_days: Number of days to extend
            reason: Reason for extension
            extend_from_now: Whether to extend from now or original expiry
            
        Returns:
            ExtensionResult: Extension operation result
        """
        try:
            original_expiry = package.expires_at
            
            # Calculate new expiry date
            if extend_from_now:
                base_date = timezone.now()
            else:
                base_date = original_expiry
            
            new_expiry = base_date + timedelta(days=extension_days)
            
            # Update package
            package.expires_at = new_expiry
            package.save(update_fields=['expires_at', 'updated_at'])
            
            # Create audit log
            audit_log = (
                f"Package {package.id} extended by {extension_days} days "
                f"from {original_expiry} to {new_expiry}. "
                f"Reason: {reason or 'No reason provided'}. "
                f"Extended at {timezone.now()}"
            )
            
            logger.info(audit_log)
            
            return ExtensionResult(
                success=True,
                package_id=package.id,
                original_expiry=original_expiry,
                new_expiry=new_expiry,
                extension_days=extension_days,
                audit_log=audit_log
            )
            
        except Exception as e:
            error_msg = f"Error extending package {package.id}: {str(e)}"
            logger.error(error_msg)
            
            return ExtensionResult(
                success=False,
                package_id=package.id,
                original_expiry=package.expires_at,
                new_expiry=package.expires_at,
                extension_days=0,
                audit_log="",
                error_message=error_msg
            )

    @staticmethod
    def bulk_extend_packages(
        packages: List[PurchaseTransaction],
        extension_days: int,
        reason: str = ""
    ) -> List[ExtensionResult]:
        """
        Extend multiple packages at once.
        
        Args:
            packages: Packages to extend
            extension_days: Number of days to extend
            reason: Reason for bulk extension
            
        Returns:
            List[ExtensionResult]: Extension results for all packages
        """
        results = []
        for package in packages:
            result = PackageExpirationService.extend_package_expiration(
                package, extension_days, reason
            )
            results.append(result)
        
        logger.info(f"Bulk extended {len(results)} packages by {extension_days} days")
        return results

    @staticmethod
    @transaction.atomic
    def create_package_renewal(
        expired_package: PurchaseTransaction,
        new_amount: Decimal,
        new_hours: Decimal,
        new_validity_days: int
    ) -> RenewalResult:
        """
        Create a new package as a renewal of an expired one.
        
        Args:
            expired_package: Original expired package
            new_amount: Amount for new package
            new_hours: Hours for new package
            new_validity_days: Validity period for new package
            
        Returns:
            RenewalResult: Renewal operation result
        """
        try:
            # Create new package
            new_package = PurchaseTransaction.objects.create(
                student=expired_package.student,
                transaction_type=TransactionType.PACKAGE,
                amount=new_amount,
                payment_status=TransactionPaymentStatus.COMPLETED,
                expires_at=timezone.now() + timedelta(days=new_validity_days),
                metadata={
                    'hours_included': float(new_hours),
                    'renewed_from': expired_package.id
                }
            )
            
            # Update student balance
            balance = StudentAccountBalance.objects.get(student=expired_package.student)
            balance.hours_purchased += new_hours
            balance.balance_amount += new_amount
            balance.save(update_fields=['hours_purchased', 'balance_amount', 'updated_at'])
            
            # Create audit log
            audit_log = (
                f"Package {expired_package.id} renewed with new package {new_package.id}. "
                f"New amount: €{new_amount}, Hours: {new_hours}, "
                f"Validity: {new_validity_days} days. Created at {timezone.now()}"
            )
            
            logger.info(audit_log)
            
            return RenewalResult(
                success=True,
                original_package_id=expired_package.id,
                new_package_id=new_package.id,
                audit_log=audit_log
            )
            
        except Exception as e:
            error_msg = f"Error creating package renewal: {str(e)}"
            logger.error(error_msg)
            
            return RenewalResult(
                success=False,
                original_package_id=expired_package.id,
                new_package_id=None,
                audit_log="",
                error_message=error_msg
            )

    @staticmethod
    def generate_expiration_summary_report(
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Generate summary report of expiration activity.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dict: Expiration summary report
        """
        # Get packages in date range
        packages = PurchaseTransaction.objects.filter(
            transaction_type=TransactionType.PACKAGE,
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Calculate metrics
        total_packages = packages.count()
        expired_packages = packages.filter(expires_at__lt=timezone.now()).count()
        expiring_soon = packages.filter(
            expires_at__gte=timezone.now(),
            expires_at__lte=timezone.now() + timedelta(days=30)
        ).count()
        
        # Calculate hours expired
        hours_expired = Decimal('0.00')
        for package in packages.filter(expires_at__lt=timezone.now()):
            hours_expired += PackageExpirationService.calculate_hours_to_expire(package)
        
        # Count affected students
        students_affected = packages.filter(
            expires_at__lt=timezone.now()
        ).values('student').distinct().count()
        
        return {
            'total_packages': total_packages,
            'expired_packages': expired_packages,
            'expiring_soon': expiring_soon,
            'hours_expired': hours_expired,
            'students_affected': students_affected,
            'report_period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }

    @staticmethod
    def get_student_expiration_history(student, limit: int = 50) -> List[Dict]:
        """
        Get expiration history for a specific student.
        
        Args:
            student: Student user object
            limit: Maximum number of records to return
            
        Returns:
            List[Dict]: Student's expiration history
        """
        expired_packages = PurchaseTransaction.objects.filter(
            student=student,
            transaction_type=TransactionType.PACKAGE,
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at__lt=timezone.now()
        ).order_by('-expires_at')[:limit]
        
        history = []
        for package in expired_packages:
            history.append({
                'student_id': student.id,
                'package_id': package.id,
                'amount': package.amount,
                'expired_at': package.expires_at,
                'hours_expired': PackageExpirationService.calculate_hours_to_expire(package)
            })
        
        return history

    @staticmethod
    def calculate_expiration_metrics(period_days: int = 30) -> Dict:
        """
        Calculate expiration metrics and KPIs.
        
        Args:
            period_days: Period to analyze in days
            
        Returns:
            Dict: Expiration metrics
        """
        start_date = timezone.now() - timedelta(days=period_days)
        
        # Get packages in period
        packages = PurchaseTransaction.objects.filter(
            transaction_type=TransactionType.PACKAGE,
            payment_status=TransactionPaymentStatus.COMPLETED,
            created_at__gte=start_date
        )
        
        total_packages = packages.count()
        expired_packages = packages.filter(expires_at__lt=timezone.now()).count()
        
        # Calculate expiration rate
        expiration_rate = (
            expired_packages / total_packages if total_packages > 0 else 0
        )
        
        # Calculate average package lifetime
        lifetimes = []
        for package in packages.filter(expires_at__isnull=False):
            lifetime = (package.expires_at - package.created_at).days
            lifetimes.append(lifetime)
        
        average_lifetime = sum(lifetimes) / len(lifetimes) if lifetimes else 0
        
        # Calculate hours lost to expiration
        hours_lost = Decimal('0.00')
        for package in packages.filter(expires_at__lt=timezone.now()):
            hours_lost += PackageExpirationService.calculate_hours_to_expire(package)
        
        # Estimate revenue impact (simplified)
        revenue_impact = hours_lost * Decimal('15.00')  # Assume €15/hour average
        
        return {
            'expiration_rate': expiration_rate,
            'average_package_lifetime': average_lifetime,
            'hours_lost_to_expiration': hours_lost,
            'revenue_impact': revenue_impact
        }

    @staticmethod
    def identify_at_risk_students(
        min_expired_packages: int = 2,
        timeframe_days: int = 90
    ) -> List[Dict]:
        """
        Identify students with patterns indicating high expiration risk.
        
        Args:
            min_expired_packages: Minimum expired packages to be considered at risk
            timeframe_days: Timeframe to analyze
            
        Returns:
            List[Dict]: At-risk students with details
        """
        start_date = timezone.now() - timedelta(days=timeframe_days)
        
        # Find students with multiple expired packages
        at_risk_students = []
        
        students_with_expired = PurchaseTransaction.objects.filter(
            transaction_type=TransactionType.PACKAGE,
            payment_status=TransactionPaymentStatus.COMPLETED,
            expires_at__lt=timezone.now(),
            expires_at__gte=start_date
        ).values('student').annotate(
            expired_count=Count('id')
        ).filter(expired_count__gte=min_expired_packages)
        
        for student_data in students_with_expired:
            student_id = student_data['student']
            expired_count = student_data['expired_count']
            
            at_risk_students.append({
                'student_id': student_id,
                'expired_packages_count': expired_count,
                'risk_score': min(expired_count / 5.0, 1.0)  # Normalize to 0-1
            })
        
        return at_risk_students