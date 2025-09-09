"""
Task Services

Services for managing tasks programmatically, including verification tasks
and onboarding tasks creation.
"""

from datetime import timedelta
import logging
from typing import Optional

from django.utils import timezone

from accounts.models import CustomUser
from .models import Task

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing tasks programmatically."""
    
    @classmethod
    def create_verification_tasks(cls, user: CustomUser, email: str, phone_number: Optional[str] = None) -> list[Task]:
        """
        Create verification tasks for a new user during signup.
        
        Args:
            user: The user to create tasks for
            email: Email address to verify
            phone_number: Phone number to verify (optional)
            
        Returns:
            List of created Task objects
        """
        tasks_created = []
        
        try:
            # Create email verification task
            email_task = Task.objects.create(
                user=user,
                title="Verify your email address",
                description=f"Please check {email} for a verification link. You have 24 hours to complete this.",
                priority="high",
                task_type="onboarding",
                is_system_generated=True,
                is_urgent=True,
                due_date=timezone.now() + timedelta(hours=24)
            )
            tasks_created.append(email_task)
            logger.info(f"Created email verification task for user {user.email}")
            
            # Create phone verification task if phone number provided
            if phone_number:
                phone_task = Task.objects.create(
                    user=user,
                    title="Verify your phone number",
                    description=f"Check SMS sent to {phone_number} for verification code. You have 24 hours to complete this.",
                    priority="high",
                    task_type="onboarding",
                    is_system_generated=True,
                    is_urgent=True,
                    due_date=timezone.now() + timedelta(hours=24)
                )
                tasks_created.append(phone_task)
                logger.info(f"Created phone verification task for user {user.email}")
                
        except Exception as e:
            logger.error(f"Failed to create verification tasks for user {user.email}: {e}")
            
        return tasks_created
    
    @classmethod
    def complete_email_verification_task(cls, user: CustomUser) -> bool:
        """
        Mark the email verification task as completed for a user.
        
        Args:
            user: The user whose email verification task to complete
            
        Returns:
            True if task was found and completed, False otherwise
        """
        try:
            email_task = Task.objects.filter(
                user=user,
                title="Verify your email address",
                status__in=["pending", "in_progress"]
            ).first()
            
            if email_task:
                email_task.status = "completed"
                email_task.save()
                logger.info(f"Completed email verification task for user {user.email}")
                return True
            else:
                logger.warning(f"No pending email verification task found for user {user.email}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to complete email verification task for user {user.email}: {e}")
            return False
    
    @classmethod
    def complete_phone_verification_task(cls, user: CustomUser) -> bool:
        """
        Mark the phone verification task as completed for a user.
        
        Args:
            user: The user whose phone verification task to complete
            
        Returns:
            True if task was found and completed, False otherwise
        """
        try:
            phone_task = Task.objects.filter(
                user=user,
                title="Verify your phone number",
                status__in=["pending", "in_progress"]
            ).first()
            
            if phone_task:
                phone_task.status = "completed"
                phone_task.save()
                logger.info(f"Completed phone verification task for user {user.email}")
                return True
            else:
                logger.warning(f"No pending phone verification task found for user {user.email}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to complete phone verification task for user {user.email}: {e}")
            return False
    
    @classmethod
    def get_verification_tasks(cls, user: CustomUser) -> dict:
        """
        Get the status of verification tasks for a user.
        
        Args:
            user: The user to check verification tasks for
            
        Returns:
            Dictionary with email and phone verification task status
        """
        email_task = Task.objects.filter(
            user=user,
            title="Verify your email address"
        ).first()
        
        phone_task = Task.objects.filter(
            user=user,
            title="Verify your phone number"
        ).first()
        
        return {
            "email_verification": {
                "exists": bool(email_task),
                "status": email_task.status if email_task else None,
                "is_overdue": email_task.is_overdue if email_task else False,
                "completed": email_task.status == "completed" if email_task else False
            },
            "phone_verification": {
                "exists": bool(phone_task),
                "status": phone_task.status if phone_task else None,
                "is_overdue": phone_task.is_overdue if phone_task else False,
                "completed": phone_task.status == "completed" if phone_task else False
            }
        }