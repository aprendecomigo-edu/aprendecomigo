"""
Django signals for managing system verification tasks.

This module contains signals that automatically complete system verification tasks
when certain conditions are met, such as email verification, phone verification,
and adding the first student.
"""

import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import StudentProfile
from tasks.models import Task
from tasks.services import TaskService

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_system_tasks_for_new_user(sender, instance, created, **kwargs):
    """
    Create system verification tasks for new users.

    Args:
        sender: User model class
        instance: The User instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        try:
            logger.info(f"Creating system tasks for new user: {instance.email}")
            TaskService.initialize_system_tasks(instance)
        except Exception as e:
            # Don't let signal errors break user creation
            logger.error(f"Failed to create system tasks for user {instance.email}: {e}")


@receiver(post_save, sender=User)
def complete_email_verification_task(sender, instance, **kwargs):
    """
    Complete email verification task when user's email is verified.

    Args:
        sender: User model class
        instance: The User instance being saved
        **kwargs: Additional keyword arguments
    """
    if instance.email_verified:
        TaskService.complete_system_task(instance, Task.EMAIL_VERIFICATION)


@receiver(post_save, sender=User)
def complete_phone_verification_task(sender, instance, **kwargs):
    """
    Complete phone verification task when user's phone is verified.

    Args:
        sender: User model class
        instance: The User instance being saved
        **kwargs: Additional keyword arguments
    """
    if instance.phone_verified:
        TaskService.complete_system_task(instance, Task.PHONE_VERIFICATION)


@receiver(post_save, sender=StudentProfile)
def complete_first_student_task(sender, instance, created, **kwargs):
    """
    Complete first student task for admin users in the same school when a student is created.

    This verification task is considered completed for all admin users in a school
    once ANY student exists in that school, since it validates the school account setup.

    Args:
        sender: StudentProfile model class
        instance: The StudentProfile instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        from accounts.models import GuardianStudentRelationship, SchoolMembership
        from accounts.models.schools import SchoolRole

        logger.info(f"Student profile created: {instance}.")

        # Only complete FIRST_STUDENT_ADDED task for actual school admins when they add students
        # Different behavior based on account type:

        if instance.account_type == "ADULT_STUDENT":
            # Adult students manage themselves - no admin task completion needed
            logger.info(f"Adult student {instance} created - no admin task completion needed")
            return

        elif instance.account_type == "GUARDIAN_ONLY":
            # Guardian-only students: complete task for the guardian if they're a school admin
            if instance.guardian and instance.guardian.user:
                guardian_user = instance.guardian.user
                if TaskService._is_school_admin_or_owner(guardian_user):
                    TaskService.complete_system_task(guardian_user, Task.FIRST_STUDENT_ADDED)
                    logger.info(f"Completed FIRST_STUDENT_ADDED task for guardian {guardian_user.email}")
            return

        elif instance.account_type == "STUDENT_GUARDIAN":
            # Student+Guardian accounts: Find schools through guardian relationships
            if not instance.user:
                logger.warning(f"Student+Guardian account {instance} has no user - cannot find relationships")
                return

            guardian_relationships = GuardianStudentRelationship.objects.filter(
                student=instance.user,
                is_active=True,
            ).select_related("school", "guardian")

            if not guardian_relationships.exists():
                logger.info(f"No guardian relationships found for student {instance} - no admin task completion")
                return

            # Complete task for school admins in the schools where this student has relationships
            schools = {rel.school for rel in guardian_relationships}

            for school in schools:
                # Only complete for actual school admins/owners, not personal school owners
                admin_memberships = SchoolMembership.objects.filter(
                    school=school, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
                ).select_related("user")

                # Filter out personal schools using the same logic as TaskService._is_school_admin_or_owner
                school_name = school.name
                if school_name.startswith("Personal School -") or school_name.endswith("'s School"):
                    logger.info(f"Skipping personal school {school_name} for task completion")
                    continue

                admin_users = [membership.user for membership in admin_memberships]
                for user in admin_users:
                    TaskService.complete_system_task(user, Task.FIRST_STUDENT_ADDED)
                    logger.info(f"Completed FIRST_STUDENT_ADDED task for admin {user.email} in school {school.name}")

                if admin_users:
                    logger.info(
                        f"Completed FIRST_STUDENT_ADDED task for {len(admin_users)} admin users in school {school.name}"
                    )
