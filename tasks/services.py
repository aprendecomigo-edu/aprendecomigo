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
    def create_teacher_onboarding_tasks(cls, user: CustomUser) -> list[Task]:
        """
        Create teacher-specific onboarding tasks as defined in workflow requirements.
        
        Tasks align with the Teacher Onboarding via Admin Invitation workflow:
        1. Confirm email address
        2. Complete teacher profile (subjects, cycles, personal data, photo)
        3. Add financial details (NIF, IBAN)
        4. Define availability schedule
        
        Args:
            user: The teacher user to create tasks for
            
        Returns:
            List of created Task objects
        """
        teacher_tasks = [
            {
                "title": "Confirmar E-mail",
                "description": "Verifique o seu e-mail e clique no link de confirmação que lhe enviámos.",
                "priority": "high",
                "task_type": "onboarding",
                "is_system_generated": True,
                "is_urgent": True,
                "due_date": timezone.now() + timedelta(days=7)
            },
            {
                "title": "Completar Perfil de Professor",
                "description": "Adicione as suas disciplinas, ciclos de ensino, dados pessoais e fotografia de perfil.",
                "priority": "high", 
                "task_type": "onboarding",
                "is_system_generated": True,
                "due_date": timezone.now() + timedelta(days=14)
            },
            {
                "title": "Adicionar Dados Fiscais",
                "description": "Introduza o seu NIF e dados bancários (IBAN) para pagamentos.",
                "priority": "medium",
                "task_type": "onboarding", 
                "is_system_generated": True,
                "due_date": timezone.now() + timedelta(days=14)
            },
            {
                "title": "Definir Disponibilidade Horária",
                "description": "Configure os horários em que está disponível para dar aulas.",
                "priority": "medium",
                "task_type": "onboarding",
                "is_system_generated": True,
                "due_date": timezone.now() + timedelta(days=14)
            },
        ]
        
        created_tasks = []
        try:
            for task_data in teacher_tasks:
                task = Task.objects.create(user=user, **task_data)
                created_tasks.append(task)
                logger.info(f"Created teacher onboarding task '{task.title}' for user {user.email}")
                
        except Exception as e:
            logger.error(f"Failed to create teacher onboarding tasks for user {user.email}: {e}")
            
        return created_tasks
    
    @classmethod
    def get_teacher_onboarding_progress(cls, user: CustomUser) -> dict:
        """
        Get teacher onboarding progress including completion percentage.
        
        Args:
            user: The teacher user to check progress for
            
        Returns:
            Dictionary with progress information and completion status
        """
        onboarding_tasks = Task.objects.filter(
            user=user,
            task_type="onboarding",
            is_system_generated=True
        )
        
        total_tasks = onboarding_tasks.count()
        completed_tasks = onboarding_tasks.filter(status="completed").count()
        
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        task_details = []
        for task in onboarding_tasks:
            task_details.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "is_completed": task.status == "completed",
                "is_overdue": task.is_overdue,
                "due_date": task.due_date
            })
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_percentage": round(progress_percentage, 1),
            "is_complete": progress_percentage == 100,
            "tasks": task_details
        }
    
    @classmethod
    def complete_teacher_onboarding_task(cls, user: CustomUser, task_title: str) -> bool:
        """
        Mark a specific teacher onboarding task as completed.
        
        Args:
            user: The teacher user
            task_title: Title of the task to complete
            
        Returns:
            True if task was found and completed, False otherwise
        """
        try:
            task = Task.objects.filter(
                user=user,
                title=task_title,
                task_type="onboarding",
                status__in=["pending", "in_progress"]
            ).first()
            
            if task:
                task.status = "completed"
                task.save()
                logger.info(f"Completed teacher onboarding task '{task_title}' for user {user.email}")
                
                # Check if all teacher onboarding tasks are complete
                cls._check_and_activate_teacher_account(user)
                return True
            else:
                logger.warning(f"No pending teacher onboarding task '{task_title}' found for user {user.email}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to complete teacher onboarding task '{task_title}' for user {user.email}: {e}")
            return False
    
    @classmethod
    def _check_and_activate_teacher_account(cls, user: CustomUser) -> bool:
        """
        Check if all teacher onboarding tasks are complete and activate account if so.
        
        Args:
            user: The teacher user to check
            
        Returns:
            True if account was activated, False otherwise
        """
        try:
            from accounts.models import TeacherProfile
            
            # Get onboarding progress
            progress = cls.get_teacher_onboarding_progress(user)
            
            # Check if teacher profile exists and is complete
            teacher_profile = None
            try:
                teacher_profile = user.teacher_profile
                profile_complete = teacher_profile.is_profile_complete()
                has_financial_details = teacher_profile.has_financial_details()
            except TeacherProfile.DoesNotExist:
                profile_complete = False
                has_financial_details = False
            
            # Check if all conditions are met for activation
            all_complete = (
                progress["is_complete"] and 
                user.email_verified and 
                profile_complete and 
                has_financial_details
            )
            
            if all_complete and not user.onboarding_completed:
                user.onboarding_completed = True
                user.save(update_fields=["onboarding_completed"])
                logger.info(f"Activated teacher account for user {user.email} - all onboarding requirements completed")
                
                # TODO: Send welcome email here
                # from messaging.services import send_teacher_welcome_email
                # send_teacher_welcome_email(user)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to check/activate teacher account for user {user.email}: {e}")
            
        return False
    
    @classmethod
    def update_teacher_profile_completion_tasks(cls, user: CustomUser) -> None:
        """
        Update teacher profile completion tasks based on current profile status.
        
        This method checks the teacher profile completion status and updates
        the corresponding onboarding tasks accordingly.
        
        Args:
            user: The teacher user to update tasks for
        """
        try:
            from accounts.models import TeacherProfile
            
            # Get teacher profile
            try:
                teacher_profile = user.teacher_profile
                completion_requirements = teacher_profile.get_completion_requirements()
            except TeacherProfile.DoesNotExist:
                logger.warning(f"No teacher profile found for user {user.email}")
                return
            
            # Update profile completion task
            if all(req["completed"] for req in completion_requirements.values()):
                cls.complete_teacher_onboarding_task(user, "Completar Perfil de Professor")
            
            # Update financial details task if applicable
            if teacher_profile.has_financial_details():
                cls.complete_teacher_onboarding_task(user, "Adicionar Dados Fiscais")
                
            # Update availability task
            if completion_requirements["availability"]["completed"]:
                cls.complete_teacher_onboarding_task(user, "Definir Disponibilidade Horária")
                
        except Exception as e:
            logger.error(f"Failed to update teacher profile completion tasks for user {user.email}: {e}")
    
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