"""
Task Services

Services for managing tasks programmatically, including system verification tasks
and onboarding tasks creation using the unified task architecture.
"""

import logging

from django.utils.translation import gettext_lazy as _

from .models import Task

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing tasks programmatically with unified system task architecture."""

    @staticmethod
    def initialize_system_tasks(user):
        """
        Create all system verification tasks for a new user.

        Args:
            user: The user to create system tasks for

        Returns:
            List of created Task objects
        """
        # Basic tasks for all users
        system_tasks = [
            {
                "system_code": Task.EMAIL_VERIFICATION,
                "title": _("Verify your email address"),
                "description": _("Click the verification link sent to your email"),
                "priority": "high",
            },
            {
                "system_code": Task.PHONE_VERIFICATION,
                "title": _("Verify your phone number"),
                "description": _("Enter the SMS code to verify your phone"),
                "priority": "high",
            },
        ]

        # Only add FIRST_STUDENT_ADDED task for school admins/owners
        if TaskService._is_school_admin_or_owner(user):
            system_tasks.append(
                {
                    "system_code": Task.FIRST_STUDENT_ADDED,
                    "title": _("Add your first student"),
                    "description": _("Add a student to start using the platform"),
                    "priority": "medium",
                }
            )

        created_tasks = []
        for task_data in system_tasks:
            task, created = Task.objects.get_or_create(
                user=user,
                system_code=task_data["system_code"],
                task_type="system",
                defaults={
                    "title": task_data["title"],
                    "description": task_data["description"],
                    "priority": task_data["priority"],
                    "is_system_generated": True,
                    "status": "pending",
                },
            )
            if created:
                created_tasks.append(task)
                logger.info(f"Created system task {task_data['system_code']} for user {user.email}")

        return created_tasks

    @staticmethod
    def _is_school_admin_or_owner(user):
        """
        Check if the user is a school admin or owner of a real school.

        Excludes personal schools that are automatically created for all users.
        Only returns True for users who are admins/owners of actual schools.

        Args:
            user: The user to check

        Returns:
            Boolean indicating if user has admin/owner role in a real school
        """
        try:
            from accounts.models import SchoolMembership
            from accounts.models.schools import SchoolRole

            # Get all admin/owner memberships for this user
            admin_memberships = SchoolMembership.objects.filter(
                user=user, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
            ).select_related("school")

            # Check if any of these memberships are for real schools (not personal schools)
            for membership in admin_memberships:
                school_name = membership.school.name
                # Exclude personal schools created automatically
                if not school_name.startswith("Personal School -") and not school_name.endswith("'s School"):
                    return True

            return False
        except Exception as e:
            logger.warning(f"Could not check admin status for user {user.email}: {e}")
            return False

    @staticmethod
    def complete_system_task(user, system_code):
        """
        Mark a system task as completed and sync boolean fields for legacy compatibility.

        Args:
            user: The user whose system task to complete
            system_code: The system code of the task to complete

        Returns:
            Task object if found and updated, None otherwise
        """
        try:
            task = Task.system_tasks.by_system_code(user, system_code).first()
            if task and task.status != "completed":
                task.status = "completed"
                task.save()

                # Update boolean fields for legacy compatibility
                user_updated = False
                update_fields = []

                if system_code == Task.EMAIL_VERIFICATION and not user.email_verified:
                    user.email_verified = True
                    user_updated = True
                    update_fields.append("email_verified")
                elif system_code == Task.PHONE_VERIFICATION and not user.phone_verified:
                    user.phone_verified = True
                    user_updated = True
                    update_fields.append("phone_verified")
                elif system_code == Task.FIRST_STUDENT_ADDED:
                    # No boolean field for first_student_added - task system is primary
                    logger.info(f"Completed FIRST_STUDENT_ADDED task for user {user.email} (task system only)")

                if user_updated and update_fields:
                    user.save(update_fields=update_fields)
                    logger.info(
                        f"Updated boolean fields {update_fields} for user {user.email} after completing {system_code}"
                    )

                logger.info(f"Completed system task {system_code} for user {user.email}")
                return task
        except Task.DoesNotExist:
            logger.warning(f"System task {system_code} not found for user {user.email}")
        return None

    @staticmethod
    def get_verification_status(user):
        """
        Get verification status for dashboard display.

        Args:
            user: The user to check verification status for

        Returns:
            Dictionary with verification status for each system task
        """
        # Optimize to single query by fetching all completed system tasks at once
        completed_system_codes = set(
            Task.system_tasks.for_user(user).filter(status="completed").values_list("system_code", flat=True)
        )

        return {
            "email_verified": Task.EMAIL_VERIFICATION in completed_system_codes,
            "phone_verified": Task.PHONE_VERIFICATION in completed_system_codes,
            "first_student_added": Task.FIRST_STUDENT_ADDED in completed_system_codes,
        }
