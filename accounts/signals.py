"""
Django signals for automatic school activity tracking and data integrity.
Creates activity records when certain events occur and ensures users have schools.
"""

import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import ActivityType, School, SchoolActivity, SchoolInvitation, SchoolMembership, SchoolRole
from accounts.models.profiles import StudentProfile
from accounts.permissions import PermissionService
from finances.models import ClassSession

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def ensure_user_has_school_membership(sender, instance, created, **kwargs):
    """
    Ensure every non-superuser has at least one school membership.

    This is a safety net to prevent orphaned users without schools.
    If a user is created without a school membership, automatically
    create a personal school for them.

    This should rarely be triggered in normal operation as the signup
    flow handles school creation, but it prevents data integrity issues.
    """
    # Skip for superusers - they don't need schools
    if instance.is_superuser:
        return

    # Skip if this is being called during the initial migration or fixture loading
    if kwargs.get("raw", False):
        return

    # Only check on user creation, not every save
    if not created:
        return

    # Use a small delay to allow the transaction to complete
    # This is because the signup flow creates the user and school in a transaction
    from django.db import connection

    if connection.in_atomic_block:
        # We're in a transaction, don't interfere
        return

    # Check if user already has a school membership
    if instance.school_memberships.filter(is_active=True).exists():
        return

    # User has no active school membership - create one
    logger.warning(
        f"User {instance.id} ({instance.email}) was created without a school membership. "
        f"Creating personal school automatically."
    )

    try:
        with transaction.atomic():
            # Create a personal school for the user
            school_name = f"Personal School - {instance.email}"
            if instance.first_name:
                school_name = f"{instance.first_name}'s School"

            school = School.objects.create(
                name=school_name,
                description=f"Automatically created personal school for {instance.email}",
                contact_email=instance.email,
                phone_number=instance.phone_number or "",
            )
            logger.info(f"Created personal school '{school_name}' for user {instance.id}")

            # Create school membership as owner
            SchoolMembership.objects.create(user=instance, school=school, role=SchoolRole.SCHOOL_OWNER, is_active=True)

            logger.info(
                f"Created school membership for user {instance.id} as {SchoolRole.SCHOOL_OWNER} of school {school.id}"
            )

    except Exception as e:
        logger.error(
            f"Failed to create school membership for user {instance.id}: {e}. "
            f"User will not be able to access the system until this is resolved."
        )
        # Don't re-raise in post_save to avoid breaking user creation
        # The user.clean() method will catch this on next validation


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


@receiver(post_save, sender=StudentProfile)
def setup_student_permissions(sender, instance, created, **kwargs):
    """Auto-create permissions when student profile is created or updated"""
    if kwargs.get("raw", False):
        return

    try:
        PermissionService.setup_permissions_for_student(instance)
        logger.info(f"Set up permissions for student {instance}")
    except Exception as e:
        logger.error(f"Failed to setup permissions for student {instance}: {e}")
