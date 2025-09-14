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
        logger.info(f"Creating system tasks for new user: {instance.email}")
        TaskService.initialize_system_tasks(instance)


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
    Complete first student task for all users when any student is created.

    This verification task is considered completed for the entire system
    once ANY student exists, since it indicates that the school administration
    has set up their first student account.

    Args:
        sender: StudentProfile model class
        instance: The StudentProfile instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        logger.info(f"Student profile created: {instance}. Completing FIRST_STUDENT_ADDED task for all users.")

        # Complete the FIRST_STUDENT_ADDED task for all users who have it pending
        all_users = User.objects.all()
        for user in all_users:
            TaskService.complete_system_task(user, Task.FIRST_STUDENT_ADDED)

        logger.info("Completed FIRST_STUDENT_ADDED task for all users")
