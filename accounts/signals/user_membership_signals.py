"""
Django signals for user school membership management.
Ensures users always have at least one school membership.
"""

import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import School, SchoolMembership, SchoolRole

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
