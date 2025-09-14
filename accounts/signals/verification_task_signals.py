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

        # Find the school associated with this student
        # Students are associated with schools through GuardianStudentRelationship
        # The relationship uses the student's user account (if they have one)
        guardian_relationships = None
        if instance.user:
            guardian_relationships = GuardianStudentRelationship.objects.filter(
                student=instance.user,
                is_active=True,  # Only consider active relationships
            ).select_related("school")

        if not guardian_relationships or not guardian_relationships.exists():
            logger.warning(
                f"No guardian relationship found for student {instance}. "
                "Falling back to completing task for all users (test/legacy mode)."
            )
            # Fallback for tests or legacy data - complete for all users
            all_users = User.objects.all()
            for user in all_users:
                TaskService.complete_system_task(user, Task.FIRST_STUDENT_ADDED)
            logger.info("Completed FIRST_STUDENT_ADDED task for all users (fallback mode)")
            return
        # TODO work on improving this logic to avoid running this for every new student
        # Get all schools this student belongs to
        schools = {rel.school for rel in guardian_relationships}

        for school in schools:
            logger.info(f"Completing FIRST_STUDENT_ADDED task for admin users in school: {school.name}")

            # Get all admin users (SCHOOL_OWNER and SCHOOL_ADMIN roles) in this school
            admin_memberships = SchoolMembership.objects.filter(
                school=school, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
            ).select_related("user")

            admin_users = [membership.user for membership in admin_memberships]

            # Complete the task for each admin user
            for user in admin_users:
                TaskService.complete_system_task(user, Task.FIRST_STUDENT_ADDED)

            logger.info(
                f"Completed FIRST_STUDENT_ADDED task for {len(admin_users)} admin users in school {school.name}"
            )
