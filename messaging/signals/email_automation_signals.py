"""
Email Automation Signals for Teacher Communications (Issue #100)

This module implements Django signals to trigger automated email communications
based on teacher invitation status changes and profile updates.
"""

from datetime import timedelta
import logging

from django.apps import apps
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from messaging.models import EmailCommunicationType, EmailTemplateType
from messaging.services.email_sequence_service import EmailSequenceOrchestrationService
from messaging.services.enhanced_email_service import EnhancedEmailService

logger = logging.getLogger(__name__)


# @receiver(post_save, sender="accounts.TeacherInvitation")  # TEMPORARILY DISABLED - Conflicts with legacy email service
def handle_teacher_invitation_created(sender, instance, created, **kwargs):
    """
    Handle automated emails when a teacher invitation is created.

    This signal triggers:
    1. Immediate invitation email
    2. Sets up reminder sequence
    """
    if created:
        logger.info(f"New teacher invitation created: {instance.id} for {instance.email}")

        try:
            # Prepare context for invitation email
            context = _prepare_invitation_context(instance)

            # Send initial invitation email
            result = EnhancedEmailService.send_template_email(
                school=instance.school,
                template_type=EmailTemplateType.INVITATION,
                recipient_email=instance.email,
                context_variables=context,
                communication_type=EmailCommunicationType.AUTOMATED,
                created_by=instance.invited_by,
                teacher_invitation=instance,
            )

            if result["success"]:
                logger.info(f"Invitation email sent successfully to {instance.email}")

                # Mark invitation as sent
                from accounts.models import InvitationStatus

                instance.status = InvitationStatus.SENT
                instance.email_sent_at = timezone.now()
                instance.save(update_fields=["status", "email_sent_at"])

                # Trigger reminder sequence
                EmailSequenceOrchestrationService.trigger_sequence(
                    school=instance.school,
                    trigger_event="invitation_sent",
                    context=context,
                    teacher_invitation=instance,
                )

            else:
                logger.error(f"Failed to send invitation email to {instance.email}: {result.get('error')}")
                instance.mark_email_failed(result.get("error", "Email sending failed"))

        except Exception as e:
            logger.exception(f"Error handling invitation creation for {instance.email}: {e}")
            instance.mark_email_failed(f"Signal processing error: {e!s}")


# @receiver(post_save, sender="accounts.TeacherInvitation")  # TEMPORARILY DISABLED - Conflicts with legacy email service
def handle_teacher_invitation_accepted(sender, instance, **kwargs):
    """
    Handle automated emails when a teacher invitation is accepted.

    This signal triggers:
    1. Welcome email to new teacher
    2. Profile completion sequence
    """
    # Check if invitation was just accepted (not created)
    if instance.is_accepted and instance.accepted_at:
        # Get the previous state to check if this is a new acceptance
        try:
            # This is a bit tricky with post_save, so we'll check if accepted_at is recent
            recent_acceptance = instance.accepted_at >= timezone.now() - timedelta(minutes=5)

            if recent_acceptance:
                logger.info(f"Teacher invitation accepted: {instance.id} by {instance.email}")

                try:
                    # Find the teacher user (should exist after acceptance)
                    CustomUser = apps.get_model("accounts", "CustomUser")
                    teacher_user = CustomUser.objects.filter(email=instance.email).first()

                    if teacher_user:
                        # Prepare context for welcome email
                        context = _prepare_welcome_context(instance, teacher_user)

                        # Send welcome email
                        result = EnhancedEmailService.send_template_email(
                            school=instance.school,
                            template_type=EmailTemplateType.WELCOME,
                            recipient_email=instance.email,
                            context_variables=context,
                            communication_type=EmailCommunicationType.AUTOMATED,
                            teacher_invitation=instance,
                        )

                        if result["success"]:
                            logger.info(f"Welcome email sent successfully to {instance.email}")

                            # Trigger profile completion sequence
                            EmailSequenceOrchestrationService.trigger_sequence(
                                school=instance.school,
                                trigger_event="invitation_accepted",
                                context=context,
                                teacher_invitation=instance,
                            )

                        else:
                            logger.error(f"Failed to send welcome email to {instance.email}: {result.get('error')}")

                    else:
                        logger.warning(f"No user found for accepted invitation {instance.id}")

                except Exception as e:
                    logger.exception(f"Error handling invitation acceptance for {instance.email}: {e}")

        except Exception as e:
            logger.exception(f"Error checking invitation acceptance status for {instance.id}: {e}")


@receiver(post_save, sender="accounts.CustomUser")
def handle_teacher_profile_updates(sender, instance, created, **kwargs):
    """
    Handle automated emails when teacher profiles are updated.

    This signal triggers:
    1. Profile completion celebration emails
    2. Profile reminder emails for incomplete profiles
    """
    # Only handle teachers, not other user types
    if not hasattr(instance, "teacher_profiles") or not instance.teacher_profiles.exists():
        return

    try:
        # Check profile completion status for each school
        for teacher_profile in instance.teacher_profiles.all():
            school = teacher_profile.school

            # Calculate profile completion
            completion_data = _calculate_profile_completion(instance, teacher_profile)

            if completion_data["is_complete"] and not completion_data["was_complete_before"]:
                # Profile just became complete - send celebration email
                logger.info(f"Teacher profile completed for {instance.email} at {school.name}")

                context = _prepare_completion_context(instance, teacher_profile, completion_data)

                result = EnhancedEmailService.send_template_email(
                    school=school,
                    template_type=EmailTemplateType.COMPLETION_CELEBRATION,
                    recipient_email=instance.email,
                    context_variables=context,
                    communication_type=EmailCommunicationType.AUTOMATED,
                )

                if result["success"]:
                    logger.info(f"Profile completion celebration email sent to {instance.email}")

                    # Trigger completion sequence
                    EmailSequenceOrchestrationService.trigger_sequence(
                        school=school, trigger_event="profile_completed", context=context
                    )

            elif not completion_data["is_complete"] and completion_data["needs_reminder"]:
                # Profile is incomplete and needs reminder
                logger.info(f"Profile incomplete reminder needed for {instance.email} at {school.name}")

                context = _prepare_profile_reminder_context(instance, teacher_profile, completion_data)

                # Trigger profile reminder sequence
                EmailSequenceOrchestrationService.trigger_sequence(
                    school=school, trigger_event="profile_incomplete", context=context
                )

    except Exception as e:
        logger.exception(f"Error handling teacher profile updates for {instance.email}: {e}")


def _prepare_invitation_context(invitation) -> dict:
    """Prepare context variables for invitation emails."""
    return {
        "teacher_name": invitation.email.split("@")[0].title(),  # Fallback name
        "recipient_email": invitation.email,
        "school_name": invitation.school.name,
        "school_description": invitation.school.description or "",
        "role_display": invitation.get_role_display(),
        "custom_message": invitation.custom_message or "",
        "invited_by_name": invitation.invited_by.name,
        "invited_by_email": invitation.invited_by.email,
        "invitation_link": f"https://aprendecomigo.com/accept-invitation/{invitation.token}",
        "expires_at": invitation.expires_at,
        "invitation_id": invitation.id,
    }


def _prepare_welcome_context(invitation, teacher_user) -> dict:
    """Prepare context variables for welcome emails."""
    return {
        "teacher_name": teacher_user.name or teacher_user.email.split("@")[0].title(),
        "recipient_email": teacher_user.email,
        "school_name": invitation.school.name,
        "school_description": invitation.school.description or "",
        "role_display": invitation.get_role_display(),
        "invited_by_name": invitation.invited_by.name,
        "invited_by_email": invitation.invited_by.email,
        "dashboard_link": "https://aprendecomigo.com/dashboard",
        "teacher_id": teacher_user.id,
        "invitation_id": invitation.id,
    }


def _prepare_completion_context(user, teacher_profile, completion_data: dict) -> dict:
    """Prepare context variables for profile completion emails."""
    return {
        "teacher_name": user.name or user.email.split("@")[0].title(),
        "recipient_email": user.email,
        "school_name": teacher_profile.school.name,
        "dashboard_link": "https://aprendecomigo.com/dashboard",
        "profile_completion_percentage": completion_data["completion_percentage"],
        "completed_fields": completion_data["completed_fields"],
        "teacher_id": user.id,
    }


def _prepare_profile_reminder_context(user, teacher_profile, completion_data: dict) -> dict:
    """Prepare context variables for profile reminder emails."""
    return {
        "teacher_name": user.name or user.email.split("@")[0].title(),
        "recipient_email": user.email,
        "school_name": teacher_profile.school.name,
        "profile_completion_percentage": completion_data["completion_percentage"],
        "missing_profile_fields": completion_data["missing_fields"],
        "profile_completion_link": "https://aprendecomigo.com/profile/complete",
        "teacher_id": user.id,
    }


def _calculate_profile_completion(user, teacher_profile) -> dict:
    """
    Calculate basic profile completion status using critical fields.

    Returns:
        Dictionary with simple completion information
    """
    # Use the teacher profile's critical fields check
    is_complete = teacher_profile.has_critical_fields()
    missing_fields = teacher_profile.get_missing_critical_fields()

    # Simple completion percentage: 100% if complete, 50% otherwise
    completion_percentage = 100 if is_complete else 50

    # Determine if reminder is needed (profile incomplete and no recent reminder)
    needs_reminder = not is_complete and not _has_recent_profile_reminder(user, teacher_profile.school)

    return {
        "is_complete": is_complete,
        "was_complete_before": is_complete,  # Simplified - no tracking of previous state
        "completion_percentage": completion_percentage,
        "completed_fields": [],  # Not tracking individual fields anymore
        "missing_fields": missing_fields,
        "needs_reminder": needs_reminder,
        "total_fields": 3,  # Just our 3 critical fields
    }


def _has_recent_profile_reminder(user, school, hours: int = 24) -> bool:
    """
    Check if user has received a profile reminder email recently.

    Args:
        user: CustomUser instance
        school: School instance
        hours: Hours to look back for recent reminders

    Returns:
        True if user has received a recent profile reminder
    """
    from messaging.models import EmailCommunication

    cutoff_time = timezone.now() - timedelta(hours=hours)

    recent_reminders = EmailCommunication.objects.filter(
        recipient=user, school=school, template_type=EmailTemplateType.PROFILE_REMINDER, queued_at__gte=cutoff_time
    ).exists()

    return recent_reminders


# Signal to prevent duplicate email sends during rapid updates
_processing_invitations = set()


@receiver(pre_save, sender="accounts.TeacherInvitation")
def handle_teacher_invitation_pre_save(sender, instance, **kwargs):
    """
    Handle pre-save logic to prevent duplicate email processing.
    """
    # Add invitation to processing set to prevent duplicate signals
    if instance.id:
        _processing_invitations.add(instance.id)


@receiver(post_save, sender="accounts.TeacherInvitation")
def handle_teacher_invitation_post_save_cleanup(sender, instance, **kwargs):
    """
    Clean up processing set after invitation processing.
    """
    # Remove from processing set
    _processing_invitations.discard(instance.id)
