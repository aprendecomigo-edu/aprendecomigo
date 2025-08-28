"""
Enhanced Email Service for Teacher Communications (Issues #99 & #100)

This service builds on the existing email infrastructure to provide enhanced
email sending capabilities with template rendering, branding, and tracking.
"""

from datetime import timedelta
import logging
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import models, transaction
from django.utils import timezone

from accounts.models import CustomUser, School, TeacherInvitation

from ..models import (
    EmailCommunication,
    EmailCommunicationType,
    EmailDeliveryStatus,
    EmailTemplateType,
    SchoolEmailTemplate,
)
from .email_template_service import EmailTemplateRenderingService, SchoolEmailTemplateManager

logger = logging.getLogger(__name__)


class EnhancedEmailService:
    """
    Enhanced email service with template rendering, branding, and comprehensive tracking.
    """

    @classmethod
    def send_template_email(
        cls,
        school: School,
        template_type: EmailTemplateType,
        recipient_email: str,
        context_variables: dict[str, Any],
        communication_type: EmailCommunicationType = EmailCommunicationType.MANUAL,
        created_by: CustomUser | None = None,
        teacher_invitation: TeacherInvitation | None = None,
        sequence=None,
        sequence_step=None,
    ) -> dict[str, Any]:
        """
        Send an email using a school's template with comprehensive tracking.

        Args:
            school: School instance
            template_type: Type of email template to use
            recipient_email: Email address of recipient
            context_variables: Variables for template rendering
            communication_type: Type of communication (manual, automated, sequence)
            created_by: User who initiated the email
            teacher_invitation: Related teacher invitation (if applicable)
            sequence: Related email sequence (if applicable)
            sequence_step: Related sequence step (if applicable)

        Returns:
            Dictionary with send results and tracking information
        """
        try:
            # Get the appropriate template for this school and type
            template = SchoolEmailTemplateManager.get_template_for_school(
                school=school, template_type=template_type, fallback_to_default=True
            )

            if not template:
                raise ValueError(f"No template found for {template_type} at school {school.name}")

            # Create email communication record for tracking
            with transaction.atomic():
                email_communication = EmailCommunication.objects.create(
                    recipient_email=recipient_email,
                    school=school,
                    template=template,
                    template_type=template_type,
                    communication_type=communication_type,
                    sequence=sequence,
                    sequence_step=sequence_step,
                    teacher_invitation=teacher_invitation,
                    created_by=created_by,
                    delivery_status=EmailDeliveryStatus.QUEUED,
                )

                # Try to link to existing user if they exist
                try:
                    user = CustomUser.objects.get(email=recipient_email)
                    email_communication.recipient = user
                    email_communication.save(update_fields=["recipient"])
                except CustomUser.DoesNotExist:
                    pass  # User doesn't exist yet, that's fine

                # Render the template
                try:
                    subject, html_content, text_content = EmailTemplateRenderingService.render_template(
                        template=template, context_variables=context_variables
                    )

                    # Update the communication record with rendered subject
                    email_communication.subject = subject
                    email_communication.save(update_fields=["subject"])

                except Exception as template_error:
                    email_communication.mark_failed(f"Template rendering failed: {template_error!s}")
                    raise

                # Send the email
                try:
                    success = cls._send_email_with_alternatives(
                        subject=subject,
                        text_content=text_content,
                        html_content=html_content,
                        recipient_email=recipient_email,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                    )

                    if success:
                        email_communication.mark_sent()
                        logger.info(f"Successfully sent {template_type} email to {recipient_email}")

                        return {
                            "success": True,
                            "email_communication_id": email_communication.id,
                            "subject": subject,
                            "recipient_email": recipient_email,
                            "template_type": template_type,
                            "delivery_status": email_communication.delivery_status,
                        }
                    else:
                        email_communication.mark_failed("Email sending failed")
                        return {
                            "success": False,
                            "error": "Email sending failed",
                            "email_communication_id": email_communication.id,
                            "recipient_email": recipient_email,
                        }

                except Exception as send_error:
                    email_communication.mark_failed(f"Email sending error: {send_error!s}")
                    raise

        except Exception as e:
            logger.error(f"Error sending template email to {recipient_email}: {e!s}")
            return {
                "success": False,
                "error": str(e),
                "recipient_email": recipient_email,
                "template_type": template_type,
            }

    @classmethod
    def send_bulk_template_emails(
        cls,
        school: School,
        template_type: EmailTemplateType,
        recipients: list[dict[str, Any]],
        communication_type: EmailCommunicationType = EmailCommunicationType.AUTOMATED,
        created_by: CustomUser | None = None,
    ) -> dict[str, Any]:
        """
        Send template emails to multiple recipients with batch processing.

        Args:
            school: School instance
            template_type: Type of email template to use
            recipients: List of recipient dictionaries with 'email' and 'context' keys
            communication_type: Type of communication
            created_by: User who initiated the emails

        Returns:
            Dictionary with batch results and statistics
        """
        results = {
            "total_recipients": len(recipients),
            "successful_emails": 0,
            "failed_emails": 0,
            "errors": [],
            "successful_emails_list": [],
            "failed_emails_list": [],
            "email_communication_ids": [],
        }

        for recipient_data in recipients:
            recipient_email = recipient_data.get("email")
            context_variables = recipient_data.get("context", {})
            teacher_invitation = recipient_data.get("teacher_invitation")

            try:
                result = cls.send_template_email(
                    school=school,
                    template_type=template_type,
                    recipient_email=recipient_email,  # type: ignore[arg-type]
                    context_variables=context_variables,
                    communication_type=communication_type,
                    created_by=created_by,
                    teacher_invitation=teacher_invitation,
                )

                if result["success"]:
                    results["successful_emails"] += 1  # type: ignore[operator]
                    results["successful_emails_list"].append(recipient_email)  # type: ignore[attr-defined]
                    results["email_communication_ids"].append(result["email_communication_id"])  # type: ignore[attr-defined]
                else:
                    results["failed_emails"] += 1  # type: ignore[operator]
                    results["failed_emails_list"].append(recipient_email)  # type: ignore[attr-defined]
                    results["errors"].append({"email": recipient_email, "error": result.get("error", "Unknown error")})  # type: ignore[attr-defined]

            except Exception as e:
                results["failed_emails"] += 1  # type: ignore[operator]
                results["failed_emails_list"].append(recipient_email)  # type: ignore[attr-defined]
                results["errors"].append({"email": recipient_email, "error": str(e)})  # type: ignore[attr-defined]
                logger.exception(f"Unexpected error sending email to {recipient_email}: {e}")

        logger.info(
            f"Bulk email batch completed: {results['successful_emails']} successful, "
            f"{results['failed_emails']} failed out of {results['total_recipients']} total"
        )

        return results

    @classmethod
    def retry_failed_email(cls, email_communication_id: int) -> dict[str, Any]:
        """
        Retry sending a failed email communication.

        Args:
            email_communication_id: ID of the EmailCommunication to retry

        Returns:
            Dictionary with retry results
        """
        try:
            email_communication = EmailCommunication.objects.get(id=email_communication_id)

            if not email_communication.can_retry():
                return {
                    "success": False,
                    "error": f"Cannot retry: max retries ({email_communication.max_retries}) exceeded",
                    "email_communication_id": email_communication_id,
                    "retry_count": email_communication.retry_count,
                }

            logger.info(
                f"Retrying email communication {email_communication_id} (attempt {email_communication.retry_count + 1})"
            )

            # Get the original context (this might need to be stored in the future)
            # For now, we'll use basic context
            context_variables = {
                "recipient_email": email_communication.recipient_email,
                "subject": email_communication.subject,
            }

            # Re-render and send
            if email_communication.template:
                try:
                    subject, html_content, text_content = EmailTemplateRenderingService.render_template(
                        template=email_communication.template, context_variables=context_variables
                    )

                    success = cls._send_email_with_alternatives(
                        subject=subject,
                        text_content=text_content,
                        html_content=html_content,
                        recipient_email=email_communication.recipient_email,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                    )

                    if success:
                        email_communication.delivery_status = EmailDeliveryStatus.SENT
                        email_communication.sent_at = timezone.now()
                        email_communication.failure_reason = None
                        email_communication.save(update_fields=["delivery_status", "sent_at", "failure_reason"])

                        return {
                            "success": True,
                            "email_communication_id": email_communication_id,
                            "retry_count": email_communication.retry_count,
                        }
                    else:
                        email_communication.mark_failed("Retry: Email sending failed")
                        return {
                            "success": False,
                            "error": "Retry: Email sending failed",
                            "email_communication_id": email_communication_id,
                            "retry_count": email_communication.retry_count,
                        }

                except Exception as retry_error:
                    email_communication.mark_failed(f"Retry error: {retry_error!s}")
                    return {
                        "success": False,
                        "error": f"Retry error: {retry_error!s}",
                        "email_communication_id": email_communication_id,
                        "retry_count": email_communication.retry_count,
                    }
            else:
                return {
                    "success": False,
                    "error": "No template available for retry",
                    "email_communication_id": email_communication_id,
                }

        except EmailCommunication.DoesNotExist:
            return {
                "success": False,
                "error": "Email communication not found",
                "email_communication_id": email_communication_id,
            }
        except Exception as e:
            logger.error(f"Error retrying email communication {email_communication_id}: {e!s}")
            return {"success": False, "error": str(e), "email_communication_id": email_communication_id}

    @classmethod
    def get_failed_emails_for_retry(cls, hours_since_failure: int = 1) -> list[EmailCommunication]:
        """
        Get failed emails that are eligible for retry.

        Args:
            hours_since_failure: Minimum hours since failure before retry

        Returns:
            List of EmailCommunication instances ready for retry
        """
        cutoff_time = timezone.now() - timedelta(hours=hours_since_failure)

        return EmailCommunication.objects.filter(  # type: ignore[return-value]
            delivery_status=EmailDeliveryStatus.FAILED,
            failed_at__lte=cutoff_time,
            retry_count__lt=models.F("max_retries"),
        ).order_by("failed_at")

    @classmethod
    def _send_email_with_alternatives(
        cls, subject: str, text_content: str, html_content: str, recipient_email: str, from_email: str
    ) -> bool:
        """
        Send email with both HTML and text alternatives.

        Args:
            subject: Email subject
            text_content: Plain text content
            html_content: HTML content
            recipient_email: Recipient email address
            from_email: Sender email address

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create email with alternatives
            email = EmailMultiAlternatives(
                subject=subject, body=text_content, from_email=from_email, to=[recipient_email]
            )

            # Attach HTML alternative
            email.attach_alternative(html_content, "text/html")

            # Send email
            result = email.send(fail_silently=False)

            return result == 1  # send() returns number of successfully sent emails

        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {e!s}")
            return False


class EmailAnalyticsService:
    """
    Service for email analytics and reporting.
    """

    @classmethod
    def get_school_email_stats(cls, school: School, days: int = 30) -> dict[str, Any]:
        """
        Get email statistics for a school over the specified period.

        Args:
            school: School instance
            days: Number of days to look back

        Returns:
            Dictionary with email statistics
        """
        from django.db.models import Count, Q
        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=days)

        base_queryset = EmailCommunication.objects.filter(school=school, queued_at__gte=cutoff_date)

        # Get counts by status
        status_counts = base_queryset.aggregate(
            total_emails=Count("id"),
            sent_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.SENT)),
            delivered_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.DELIVERED)),
            opened_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.OPENED)),
            clicked_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.CLICKED)),
            failed_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.FAILED)),
            bounced_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.BOUNCED)),
        )

        # Get counts by template type
        template_type_counts = base_queryset.values("template_type").annotate(count=Count("id")).order_by("-count")

        # Calculate rates
        total = status_counts["total_emails"] or 1
        delivery_rate = (status_counts["delivered_emails"] / total) * 100 if total > 0 else 0
        open_rate = (status_counts["opened_emails"] / total) * 100 if total > 0 else 0
        click_rate = (status_counts["clicked_emails"] / total) * 100 if total > 0 else 0
        failure_rate = (status_counts["failed_emails"] / total) * 100 if total > 0 else 0

        return {
            "period_days": days,
            "total_emails": status_counts["total_emails"],
            "sent_emails": status_counts["sent_emails"],
            "delivered_emails": status_counts["delivered_emails"],
            "opened_emails": status_counts["opened_emails"],
            "clicked_emails": status_counts["clicked_emails"],
            "failed_emails": status_counts["failed_emails"],
            "bounced_emails": status_counts["bounced_emails"],
            "delivery_rate": round(delivery_rate, 2),
            "open_rate": round(open_rate, 2),
            "click_rate": round(click_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "template_type_breakdown": list(template_type_counts),
        }

    @classmethod
    def get_template_performance(cls, template: SchoolEmailTemplate, days: int = 30) -> dict[str, Any]:
        """
        Get performance statistics for a specific template.

        Args:
            template: SchoolEmailTemplate instance
            days: Number of days to look back

        Returns:
            Dictionary with template performance statistics
        """
        from django.db.models import Avg, Count, Q
        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=days)

        emails = EmailCommunication.objects.filter(template=template, queued_at__gte=cutoff_date)

        stats = emails.aggregate(
            total_sent=Count("id"),
            delivered=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.DELIVERED)),
            opened=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.OPENED)),
            clicked=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.CLICKED)),
            failed=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.FAILED)),
            avg_retry_count=Avg("retry_count"),
        )

        total = stats["total_sent"] or 1

        return {
            "template_id": template.id,
            "template_name": template.name,
            "template_type": template.template_type,
            "period_days": days,
            "total_sent": stats["total_sent"],
            "delivered": stats["delivered"],
            "opened": stats["opened"],
            "clicked": stats["clicked"],
            "failed": stats["failed"],
            "delivery_rate": round((stats["delivered"] / total) * 100, 2) if total > 0 else 0,
            "open_rate": round((stats["opened"] / total) * 100, 2) if total > 0 else 0,
            "click_rate": round((stats["clicked"] / total) * 100, 2) if total > 0 else 0,
            "failure_rate": round((stats["failed"] / total) * 100, 2) if total > 0 else 0,
            "avg_retry_count": round(stats["avg_retry_count"] or 0, 2),
        }
