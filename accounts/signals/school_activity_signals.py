"""
Django signals for automatic school activity tracking.
Creates activity records when certain events occur.
"""

import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import ActivityType, SchoolActivity, SchoolInvitation, SchoolMembership, SchoolRole
from finances.models import ClassSession

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=SchoolMembership)
def create_membership_activity(sender, instance, created, **kwargs):
    """Create activity when user joins a school"""
    if created and instance.is_active:
        # Determine activity type based on role
        if instance.role == SchoolRole.STUDENT:
            activity_type = ActivityType.STUDENT_JOINED
            description = f"{instance.user.name} joined as a student"
        elif instance.role == SchoolRole.TEACHER:
            activity_type = ActivityType.TEACHER_JOINED
            description = f"{instance.user.name} joined as a teacher"
        else:
            # For admins and owners, don't create activity
            return

        SchoolActivity.objects.create(
            school=instance.school,
            activity_type=activity_type,
            actor=instance.user,
            target_user=instance.user,
            description=description,
            metadata={
                "role": instance.role,
                "joined_at": instance.joined_at.isoformat() if instance.joined_at else None,
            },
        )


@receiver(post_save, sender=SchoolInvitation)
def create_invitation_activity(sender, instance, created, **kwargs):
    """Create activity when invitation is sent or accepted"""
    if created:
        # Invitation sent
        SchoolActivity.objects.create(
            school=instance.school,
            activity_type=ActivityType.INVITATION_SENT,
            actor=instance.invited_by,
            target_invitation=instance,
            description=f"{instance.invited_by.name} invited {instance.email} as a {instance.get_role_display()}",
            metadata={
                "email": instance.email,
                "role": instance.role,
                "expires_at": instance.expires_at.isoformat()
                if hasattr(instance.expires_at, "isoformat")
                else str(instance.expires_at),
            },
        )
    else:
        # Check if invitation was just accepted
        if instance.is_accepted:
            # Try to find the user who accepted
            try:
                accepting_user = User.objects.get(email=instance.email)
            except User.DoesNotExist:
                accepting_user = None

            SchoolActivity.objects.create(
                school=instance.school,
                activity_type=ActivityType.INVITATION_ACCEPTED,
                actor=accepting_user,
                target_invitation=instance,
                target_user=accepting_user,
                description=f"{instance.email} accepted invitation to join as {instance.get_role_display()}",
                metadata={"email": instance.email, "role": instance.role, "invited_by": instance.invited_by.name},
            )


@receiver(post_save, sender=ClassSession)
def create_class_session_activity(sender, instance, created, **kwargs):
    """Create activity when class session is created or completed"""
    if created:
        # Class created
        SchoolActivity.objects.create(
            school=instance.school,
            activity_type=ActivityType.CLASS_CREATED,
            actor=instance.teacher.user,
            target_class=instance,
            description=f"Grade {instance.grade_level} class scheduled",
            metadata={
                "grade_level": instance.grade_level,
                "session_type": instance.session_type,
                "date": instance.date.isoformat() if hasattr(instance.date, "isoformat") else str(instance.date),
                "duration": str(instance.duration_hours) if hasattr(instance, "duration_hours") else None,
            },
        )
    else:
        # Check if status changed to completed
        if instance.status == "completed":
            # Check if we already created a completion activity
            existing_activity = SchoolActivity.objects.filter(
                school=instance.school, activity_type=ActivityType.CLASS_COMPLETED, target_class=instance
            ).exists()

            if not existing_activity:
                SchoolActivity.objects.create(
                    school=instance.school,
                    activity_type=ActivityType.CLASS_COMPLETED,
                    actor=instance.teacher.user,
                    target_class=instance,
                    description=f"Grade {instance.grade_level} class completed",
                    metadata={
                        "grade_level": instance.grade_level,
                        "session_type": instance.session_type,
                        "date": instance.date.isoformat()
                        if hasattr(instance.date, "isoformat")
                        else str(instance.date),
                        "duration": str(instance.duration_hours) if hasattr(instance, "duration_hours") else None,
                        "student_count": instance.student_count if hasattr(instance, "student_count") else 1,
                    },
                )
        elif instance.status == "cancelled":
            # Check if we already created a cancellation activity
            existing_activity = SchoolActivity.objects.filter(
                school=instance.school, activity_type=ActivityType.CLASS_CANCELLED, target_class=instance
            ).exists()

            if not existing_activity:
                SchoolActivity.objects.create(
                    school=instance.school,
                    activity_type=ActivityType.CLASS_CANCELLED,
                    actor=instance.teacher.user,
                    target_class=instance,
                    description=f"Grade {instance.grade_level} class cancelled",
                    metadata={
                        "grade_level": instance.grade_level,
                        "session_type": instance.session_type,
                        "date": instance.date.isoformat() if instance.date else None,
                    },
                )


@receiver(post_save, sender=SchoolActivity)
def invalidate_metrics_cache_on_activity(sender, instance, created, **kwargs):
    """Invalidate school metrics cache when new activity is created"""
    if created:
        from accounts.services.metrics_service import SchoolMetricsService

        SchoolMetricsService.invalidate_cache(instance.school.id)

        # Note: WebSocket broadcasting for dashboard updates has been removed
        # as per the decision to limit WebSocket usage to chat functionality only


@receiver(post_save, sender=SchoolMembership)
def invalidate_metrics_cache_on_membership(sender, instance, created, **kwargs):
    """Invalidate school metrics cache when membership changes"""
    from accounts.services.metrics_service import SchoolMetricsService

    SchoolMetricsService.invalidate_cache(instance.school.id)


@receiver(post_save, sender=ClassSession)
def invalidate_metrics_cache_on_session(sender, instance, created, **kwargs):
    """Invalidate school metrics cache when class session changes"""
    from accounts.services.metrics_service import SchoolMetricsService

    SchoolMetricsService.invalidate_cache(instance.school.id)
