"""
Custom managers for the Task model.

This module provides specialized managers for different types of tasks,
including system-generated tasks and user-created tasks.
"""

from django.db import models


class SystemTaskManager(models.Manager):
    """
    Manager for system-generated tasks only.

    This manager filters to only show tasks that are:
    - task_type='system'
    - is_system_generated=True
    """

    def get_queryset(self):
        """Return only system-generated tasks"""
        return super().get_queryset().filter(task_type="system", is_system_generated=True)

    def for_user(self, user):
        """Get system tasks for a specific user"""
        return self.filter(user=user)

    def completed_for_user(self, user):
        """Get completed system tasks for a specific user"""
        return self.for_user(user).filter(status="completed")

    def pending_for_user(self, user):
        """Get pending system tasks for a specific user"""
        return self.for_user(user).filter(status="pending")

    def by_system_code(self, user, system_code):
        """Get a system task by user and system code"""
        return self.for_user(user).filter(system_code=system_code)


class UserTaskManager(models.Manager):
    """
    Manager for user-created tasks only.

    This manager filters to only show tasks that are:
    - task_type in ['personal', 'assignment', 'onboarding']
    - is_system_generated=False
    """

    def get_queryset(self):
        """Return only user-created tasks"""
        return (
            super()
            .get_queryset()
            .filter(task_type__in=["personal", "assignment", "onboarding"], is_system_generated=False)
        )

    def for_user(self, user):
        """Get user tasks for a specific user"""
        return self.filter(user=user)

    def completed_for_user(self, user):
        """Get completed user tasks for a specific user"""
        return self.for_user(user).filter(status="completed")

    def pending_for_user(self, user):
        """Get pending user tasks for a specific user"""
        return self.for_user(user).filter(status="pending")


class OnboardingTaskManager(models.Manager):
    """
    Manager for onboarding tasks specifically.

    This manager filters to only show onboarding tasks.
    """

    def get_queryset(self):
        """Return only onboarding tasks"""
        return super().get_queryset().filter(task_type="onboarding")

    def for_user(self, user):
        """Get onboarding tasks for a specific user"""
        return self.filter(user=user)

    def completed_for_user(self, user):
        """Get completed onboarding tasks for a specific user"""
        return self.for_user(user).filter(status="completed")
