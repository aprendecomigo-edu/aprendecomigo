"""
Email Sequence Orchestration Service (Issue #100)

This service handles automated email sequences with configurable delays,
trigger conditions, and comprehensive tracking.
"""

from datetime import datetime, timedelta
import logging
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import CustomUser, School, TeacherInvitation

from ..models import (
    EmailCommunication,
    EmailCommunicationType,
    EmailDeliveryStatus,
    EmailSequence,
)
from .enhanced_email_service import EnhancedEmailService

logger = logging.getLogger(__name__)


class EmailSequenceOrchestrationService:
    """
    Service for orchestrating automated email sequences with timing and conditions.
    """

    @classmethod
    def trigger_sequence(
        cls,
        school: School,
        trigger_event: str,
        context: dict[str, Any],
        teacher_invitation: TeacherInvitation | None = None,
        user: CustomUser | None = None,
    ) -> dict[str, Any]:
        """
        Trigger email sequences based on an event.

        Args:
            school: School instance
            trigger_event: Event that triggered the sequence
            context: Context variables for email rendering
            teacher_invitation: Related teacher invitation (if applicable)
            user: Related user (if applicable)

        Returns:
            Dictionary with trigger results
        """
        try:
            # Find active sequences for this trigger event
            sequences = EmailSequence.objects.filter(
                school=school, trigger_event=trigger_event, is_active=True
            ).prefetch_related("steps__template")

            if not sequences.exists():
                logger.info(f"No active sequences found for trigger '{trigger_event}' at school {school.name}")
                return {"success": True, "message": "No sequences to trigger", "triggered_sequences": 0}

            triggered_sequences = []

            for sequence in sequences:
                try:
                    result = cls._schedule_sequence_steps(
                        sequence=sequence, context=context, teacher_invitation=teacher_invitation, user=user
                    )

                    if result["success"]:
                        triggered_sequences.append(
                            {
                                "sequence_id": sequence.id,
                                "sequence_name": sequence.name,
                                "scheduled_steps": result["scheduled_steps"],
                            }
                        )
                        logger.info(f"Triggered sequence '{sequence.name}' with {result['scheduled_steps']} steps")
                    else:
                        logger.error(f"Failed to trigger sequence '{sequence.name}': {result.get('error')}")

                except Exception as e:
                    logger.exception(f"Error triggering sequence {sequence.id}: {e}")

            return {"success": True, "triggered_sequences": len(triggered_sequences), "sequences": triggered_sequences}

        except Exception as e:
            logger.exception(f"Error triggering sequences for event '{trigger_event}': {e}")
            return {"success": False, "error": str(e), "triggered_sequences": 0}

    @classmethod
    def _schedule_sequence_steps(
        cls,
        sequence: EmailSequence,
        context: dict[str, Any],
        teacher_invitation: TeacherInvitation | None = None,
        user: CustomUser | None = None,
    ) -> dict[str, Any]:
        """
        Schedule all steps in an email sequence.

        Args:
            sequence: EmailSequence instance
            context: Context variables for email rendering
            teacher_invitation: Related teacher invitation (if applicable)
            user: Related user (if applicable)

        Returns:
            Dictionary with scheduling results
        """
        try:
            steps = sequence.steps.filter(is_active=True).order_by("step_number")

            if not steps.exists():
                return {"success": False, "error": "No active steps in sequence", "scheduled_steps": 0}

            scheduled_steps = 0
            recipient_email = context.get("recipient_email")

            if not recipient_email:
                return {"success": False, "error": "No recipient email in context", "scheduled_steps": 0}

            # Check if we should prevent duplicate sequences for the same recipient
            if cls._should_prevent_duplicate_sequence(sequence, recipient_email):
                logger.info(f"Preventing duplicate sequence {sequence.id} for {recipient_email}")
                return {"success": True, "message": "Sequence already active for recipient", "scheduled_steps": 0}

            # Schedule each step
            base_time = timezone.now()

            for step in steps:
                try:
                    # Calculate when this step should be sent
                    send_time = base_time + timedelta(hours=step.delay_hours)

                    # Create email communication record for this step (queued for future sending)
                    with transaction.atomic():
                        email_communication = EmailCommunication.objects.create(
                            recipient_email=recipient_email,
                            school=sequence.school,
                            template=step.template,
                            template_type=step.template.template_type,
                            subject=f"Scheduled: {step.template.subject_template}",  # Will be rendered later
                            communication_type=EmailCommunicationType.SEQUENCE,
                            sequence=sequence,
                            sequence_step=step,
                            teacher_invitation=teacher_invitation,
                            delivery_status=EmailDeliveryStatus.QUEUED,
                            queued_at=send_time,  # Schedule for future
                        )

                        # Try to link to existing user
                        if user:
                            email_communication.recipient = user
                            email_communication.save(update_fields=["recipient"])
                        else:
                            try:
                                existing_user = CustomUser.objects.get(email=recipient_email)
                                email_communication.recipient = existing_user
                                email_communication.save(update_fields=["recipient"])
                            except CustomUser.DoesNotExist:
                                pass

                        scheduled_steps += 1
                        logger.debug(f"Scheduled step {step.step_number} of sequence {sequence.id} for {send_time}")

                except Exception as e:
                    logger.exception(f"Error scheduling step {step.id}: {e}")

            return {"success": True, "scheduled_steps": scheduled_steps, "sequence_id": sequence.id}

        except Exception as e:
            logger.exception(f"Error scheduling sequence steps for {sequence.id}: {e}")
            return {"success": False, "error": str(e), "scheduled_steps": 0}

    @classmethod
    def process_due_sequence_emails(cls) -> dict[str, Any]:
        """
        Process email communications that are due to be sent from sequences.
        This method should be called periodically (e.g., via a cron job or Celery task).

        Returns:
            Dictionary with processing results
        """
        try:
            # Find emails that are queued and due to be sent
            due_emails = (
                EmailCommunication.objects.filter(
                    delivery_status=EmailDeliveryStatus.QUEUED,
                    communication_type=EmailCommunicationType.SEQUENCE,
                    queued_at__lte=timezone.now(),
                )
                .select_related("template", "school", "sequence", "sequence_step", "teacher_invitation")
                .order_by("queued_at")
            )

            if not due_emails.exists():
                return {"success": True, "message": "No due sequence emails to process", "processed_emails": 0}

            processed_count = 0
            successful_count = 0
            failed_count = 0
            errors = []

            for email_comm in due_emails:
                try:
                    # Check if conditions are still met for sending this email
                    should_send = cls._evaluate_send_conditions(email_comm)

                    if not should_send["should_send"]:
                        # Mark as cancelled rather than failed
                        email_comm.delivery_status = EmailDeliveryStatus.FAILED
                        email_comm.failure_reason = f"Condition not met: {should_send['reason']}"
                        email_comm.save(update_fields=["delivery_status", "failure_reason"])

                        logger.info(f"Skipped sequence email {email_comm.id}: {should_send['reason']}")
                        processed_count += 1
                        continue

                    # Prepare context for this specific email
                    context = cls._prepare_sequence_email_context(email_comm)

                    # Send the email
                    result = cls._send_sequence_email(email_comm, context)

                    if result["success"]:
                        successful_count += 1
                        logger.info(f"Successfully sent sequence email {email_comm.id}")
                    else:
                        failed_count += 1
                        errors.append(
                            {"email_communication_id": email_comm.id, "error": result.get("error", "Unknown error")}
                        )
                        logger.error(f"Failed to send sequence email {email_comm.id}: {result.get('error')}")

                    processed_count += 1

                except Exception as e:
                    failed_count += 1
                    errors.append({"email_communication_id": email_comm.id, "error": str(e)})
                    logger.exception(f"Error processing sequence email {email_comm.id}: {e}")
                    processed_count += 1

            logger.info(
                f"Processed {processed_count} sequence emails: {successful_count} successful, {failed_count} failed"
            )

            return {
                "success": True,
                "processed_emails": processed_count,
                "successful_emails": successful_count,
                "failed_emails": failed_count,
                "errors": errors,
            }

        except Exception as e:
            logger.exception(f"Error processing due sequence emails: {e}")
            return {"success": False, "error": str(e), "processed_emails": 0}

    @classmethod
    def _should_prevent_duplicate_sequence(cls, sequence: EmailSequence, recipient_email: str) -> bool:
        """
        Check if we should prevent duplicate sequences for the same recipient.

        Args:
            sequence: EmailSequence instance
            recipient_email: Recipient email address

        Returns:
            True if duplicate should be prevented
        """
        # Check if there are already active sequence emails for this recipient
        active_sequence_emails = EmailCommunication.objects.filter(
            sequence=sequence,
            recipient_email=recipient_email,
            delivery_status__in=[EmailDeliveryStatus.QUEUED, EmailDeliveryStatus.SENDING, EmailDeliveryStatus.SENT],
        ).exists()

        return active_sequence_emails

    @classmethod
    def _evaluate_send_conditions(cls, email_comm: EmailCommunication) -> dict[str, Any]:
        """
        Evaluate whether an email should be sent based on its conditions.

        Args:
            email_comm: EmailCommunication instance

        Returns:
            Dictionary with evaluation results
        """
        if not email_comm.sequence_step:
            return {"should_send": True, "reason": "No conditions to evaluate"}

        step = email_comm.sequence_step
        condition = step.send_condition

        try:
            if condition == "always":
                return {"should_send": True, "reason": "Always send condition"}

            elif condition == "if_no_response":
                # Check if recipient has responded/clicked recent emails
                has_response = EmailCommunication.objects.filter(
                    recipient_email=email_comm.recipient_email,
                    school=email_comm.school,
                    delivery_status__in=[EmailDeliveryStatus.CLICKED, EmailDeliveryStatus.OPENED],
                    sent_at__gte=timezone.now() - timedelta(days=7),
                ).exists()

                return {
                    "should_send": not has_response,
                    "reason": "Recipient has responded" if has_response else "No response from recipient",
                }

            elif condition == "if_not_accepted":
                # Check if related invitation is still not accepted
                if email_comm.teacher_invitation:
                    is_accepted = email_comm.teacher_invitation.is_accepted
                    return {
                        "should_send": not is_accepted,
                        "reason": "Invitation already accepted" if is_accepted else "Invitation not yet accepted",
                    }
                else:
                    return {"should_send": False, "reason": "No teacher invitation to check"}

            elif condition == "if_profile_incomplete":
                # Check if user profile is still incomplete
                if email_comm.recipient:
                    # This would need to be implemented based on your profile completion logic
                    # For now, we'll assume it should send
                    return {"should_send": True, "reason": "Profile completion check not implemented"}
                else:
                    return {"should_send": True, "reason": "User not found, assuming profile incomplete"}

            else:
                return {"should_send": False, "reason": f"Unknown condition: {condition}"}

        except Exception as e:
            logger.exception(f"Error evaluating send conditions for email {email_comm.id}: {e}")
            return {"should_send": False, "reason": f"Condition evaluation error: {e!s}"}

    @classmethod
    def _prepare_sequence_email_context(cls, email_comm: EmailCommunication) -> dict[str, Any]:
        """
        Prepare context variables for a sequence email.

        Args:
            email_comm: EmailCommunication instance

        Returns:
            Dictionary with context variables
        """
        context = {
            "recipient_email": email_comm.recipient_email,
            "school_name": email_comm.school.name,
            "platform_name": "Aprende Comigo",
            "platform_url": "https://aprendecomigo.com",
            "support_email": "support@aprendecomigo.com",
            "current_year": datetime.now().year,
        }

        # Add recipient-specific context
        if email_comm.recipient:
            context.update(
                {
                    "teacher_name": email_comm.recipient.name or email_comm.recipient.email.split("@")[0].title(),
                    "teacher_id": email_comm.recipient.id,
                }
            )
        else:
            context.update(
                {
                    "teacher_name": email_comm.recipient_email.split("@")[0].title(),
                }
            )

        # Add invitation-specific context
        if email_comm.teacher_invitation:
            invitation = email_comm.teacher_invitation
            context.update(
                {
                    "invitation_link": f"https://aprendecomigo.com/accept-invitation/{invitation.token}",
                    "invited_by_name": invitation.invited_by.name,
                    "invited_by_email": invitation.invited_by.email,
                    "expires_at": invitation.expires_at,
                    "role_display": invitation.get_role_display(),
                    "custom_message": invitation.custom_message or "",
                }
            )

        # Add sequence-specific context
        if email_comm.sequence:
            context.update(
                {
                    "sequence_name": email_comm.sequence.name,
                }
            )

        # Add common links
        context.update(
            {
                "dashboard_link": "https://aprendecomigo.com/dashboard",
                "profile_completion_link": "https://aprendecomigo.com/profile/complete",
                "resources_link": "https://aprendecomigo.com/resources",
                "help_center_link": "https://aprendecomigo.com/help",
            }
        )

        return context

    @classmethod
    def _send_sequence_email(cls, email_comm: EmailCommunication, context: dict[str, Any]) -> dict[str, Any]:
        """
        Send a sequence email using the enhanced email service.

        Args:
            email_comm: EmailCommunication instance
            context: Context variables for rendering

        Returns:
            Dictionary with send results
        """
        try:
            from .email_template_service import EmailTemplateRenderingService

            if not email_comm.template:
                email_comm.mark_failed("No template available")
                return {"success": False, "error": "No template available for sequence email"}

            # Render the template
            subject, html_content, text_content = EmailTemplateRenderingService.render_template(
                template=email_comm.template, context_variables=context
            )

            # Update the email communication with rendered subject
            email_comm.subject = subject
            email_comm.delivery_status = EmailDeliveryStatus.SENDING
            email_comm.save(update_fields=["subject", "delivery_status"])

            # Send the email
            success = EnhancedEmailService._send_email_with_alternatives(
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                recipient_email=email_comm.recipient_email,
                from_email=settings.DEFAULT_FROM_EMAIL,
            )

            if success:
                email_comm.mark_sent()
                return {"success": True, "email_communication_id": email_comm.id}
            else:
                email_comm.mark_failed("Email sending failed")
                return {"success": False, "error": "Email sending failed", "email_communication_id": email_comm.id}

        except Exception as e:
            email_comm.mark_failed(f"Sequence email error: {e!s}")
            return {"success": False, "error": str(e), "email_communication_id": email_comm.id}

    @classmethod
    def cancel_sequence_for_recipient(
        cls, sequence: EmailSequence, recipient_email: str, reason: str = "Sequence cancelled"
    ) -> dict[str, Any]:
        """
        Cancel all pending sequence emails for a specific recipient.

        Args:
            sequence: EmailSequence instance
            recipient_email: Recipient email address
            reason: Reason for cancellation

        Returns:
            Dictionary with cancellation results
        """
        try:
            # Find all queued emails for this sequence and recipient
            queued_emails = EmailCommunication.objects.filter(
                sequence=sequence, recipient_email=recipient_email, delivery_status=EmailDeliveryStatus.QUEUED
            )

            cancelled_count = 0

            for email_comm in queued_emails:
                email_comm.delivery_status = EmailDeliveryStatus.FAILED
                email_comm.failure_reason = reason
                email_comm.save(update_fields=["delivery_status", "failure_reason"])
                cancelled_count += 1

            logger.info(f"Cancelled {cancelled_count} sequence emails for {recipient_email}")

            return {
                "success": True,
                "cancelled_emails": cancelled_count,
                "sequence_id": sequence.id,
                "recipient_email": recipient_email,
            }

        except Exception as e:
            logger.exception(f"Error cancelling sequence for {recipient_email}: {e}")
            return {"success": False, "error": str(e), "cancelled_emails": 0}

    @classmethod
    def get_sequence_status(cls, sequence: EmailSequence) -> dict[str, Any]:
        """
        Get status and statistics for an email sequence.

        Args:
            sequence: EmailSequence instance

        Returns:
            Dictionary with sequence status and statistics
        """
        from django.db.models import Count

        try:
            # Get email statistics for this sequence
            email_stats = EmailCommunication.objects.filter(sequence=sequence).aggregate(
                total_emails=Count("id"),
                queued_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.QUEUED)),
                sent_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.SENT)),
                delivered_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.DELIVERED)),
                opened_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.OPENED)),
                clicked_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.CLICKED)),
                failed_emails=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.FAILED)),
            )

            # Get step breakdown
            step_stats = []
            for step in sequence.steps.filter(is_active=True).order_by("step_number"):
                step_emails = EmailCommunication.objects.filter(sequence_step=step).aggregate(
                    total=Count("id"),
                    sent=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.SENT)),
                    failed=Count("id", filter=Q(delivery_status=EmailDeliveryStatus.FAILED)),
                )

                step_stats.append(
                    {
                        "step_number": step.step_number,
                        "template_name": step.template.name,
                        "delay_hours": step.delay_hours,
                        "total_emails": step_emails["total"],
                        "sent_emails": step_emails["sent"],
                        "failed_emails": step_emails["failed"],
                    }
                )

            return {
                "sequence_id": sequence.id,
                "sequence_name": sequence.name,
                "is_active": sequence.is_active,
                "trigger_event": sequence.trigger_event,
                "total_steps": sequence.steps.filter(is_active=True).count(),
                "email_statistics": email_stats,
                "step_breakdown": step_stats,
            }

        except Exception as e:
            logger.exception(f"Error getting sequence status for {sequence.id}: {e}")
            return {"sequence_id": sequence.id, "error": str(e)}
