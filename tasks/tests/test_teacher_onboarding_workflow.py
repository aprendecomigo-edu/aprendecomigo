"""
Tests for enhanced teacher onboarding functionality.

Tests the complete teacher onboarding workflow including:
- Teacher-specific onboarding tasks creation
- Profile completion tracking
- Account activation logic
- Integration with teacher invitation system
"""

from datetime import timedelta
import uuid

from django.test import TestCase
from django.utils import timezone

from accounts.models import (
    CustomUser,
    School,
    SchoolMembership,
    SchoolRole,
    TeacherInvitation,
    TeacherProfile,
)
from tasks.models import Task
from tasks.services import TaskService


class TeacherOnboardingWorkflowTest(TestCase):
    """Test suite for the enhanced teacher onboarding workflow."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(
            name="Test School", 
            description="School for testing teacher onboarding"
        )

        self.school_owner = CustomUser.objects.create_user(
            email="owner@testschool.com", 
            name="School Owner", 
            phone_number="+351912000001"
        )

        SchoolMembership.objects.create(
            user=self.school_owner, 
            school=self.school, 
            role=SchoolRole.SCHOOL_OWNER, 
            is_active=True
        )

        # Create a teacher user for testing
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            name="New Teacher",
            phone_number="+351912000002"
        )

        SchoolMembership.objects.create(
            user=self.teacher,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )

    def test_create_teacher_onboarding_tasks(self):
        """Test creating teacher-specific onboarding tasks."""
        tasks = TaskService.create_teacher_onboarding_tasks(self.teacher)
        
        # Should create 4 teacher-specific tasks
        self.assertEqual(len(tasks), 4)
        
        expected_titles = [
            "Confirmar E-mail",
            "Completar Perfil de Professor",
            "Adicionar Dados Fiscais",
            "Definir Disponibilidade Horária"
        ]
        
        created_titles = [task.title for task in tasks]
        for title in expected_titles:
            self.assertIn(title, created_titles)
        
        # All tasks should be onboarding type and system generated
        for task in tasks:
            self.assertEqual(task.task_type, "onboarding")
            self.assertTrue(task.is_system_generated)
            self.assertEqual(task.user, self.teacher)

    def test_teacher_onboarding_progress_tracking(self):
        """Test tracking teacher onboarding progress."""
        # Create onboarding tasks
        TaskService.create_teacher_onboarding_tasks(self.teacher)
        
        # Initially no tasks completed
        progress = TaskService.get_teacher_onboarding_progress(self.teacher)
        self.assertEqual(progress["completed_tasks"], 0)
        self.assertEqual(progress["progress_percentage"], 0)
        self.assertFalse(progress["is_complete"])
        
        # Complete one task
        TaskService.complete_teacher_onboarding_task(self.teacher, "Confirmar E-mail")
        
        progress = TaskService.get_teacher_onboarding_progress(self.teacher)
        self.assertEqual(progress["completed_tasks"], 1)
        self.assertEqual(progress["progress_percentage"], 25.0)
        self.assertFalse(progress["is_complete"])
        
        # Complete all tasks
        TaskService.complete_teacher_onboarding_task(self.teacher, "Completar Perfil de Professor")
        TaskService.complete_teacher_onboarding_task(self.teacher, "Adicionar Dados Fiscais")
        TaskService.complete_teacher_onboarding_task(self.teacher, "Definir Disponibilidade Horária")
        
        progress = TaskService.get_teacher_onboarding_progress(self.teacher)
        self.assertEqual(progress["completed_tasks"], 4)
        self.assertEqual(progress["progress_percentage"], 100.0)
        self.assertTrue(progress["is_complete"])

    def test_teacher_profile_completion_tracking(self):
        """Test teacher profile completion requirements."""
        # Create teacher profile
        teacher_profile = TeacherProfile.objects.create(user=self.teacher)
        
        # Initially profile is not complete
        self.assertFalse(teacher_profile.is_profile_complete())
        
        # Get completion requirements
        requirements = teacher_profile.get_completion_requirements()
        self.assertIn("basic_info", requirements)
        self.assertIn("teaching_subjects", requirements)
        self.assertIn("grade_levels", requirements)
        self.assertIn("availability", requirements)
        self.assertIn("profile_photo", requirements)
        
        # All should be incomplete initially
        for req in requirements.values():
            self.assertFalse(req["completed"])
        
        # Fill in basic info
        teacher_profile.bio = "Experienced math teacher"
        teacher_profile.specialty = "Mathematics"
        teacher_profile.save()
        
        requirements = teacher_profile.get_completion_requirements()
        self.assertTrue(requirements["basic_info"]["completed"])
        self.assertFalse(teacher_profile.is_profile_complete())  # Still missing other fields

    def test_teacher_profile_complete_scenario(self):
        """Test complete teacher profile scenario."""
        # Create teacher profile with all required fields
        teacher_profile = TeacherProfile.objects.create(
            user=self.teacher,
            bio="Experienced mathematics teacher with 10 years of experience",
            specialty="Mathematics",
            teaching_subjects=["Mathematics", "Physics"],
            grade_level_preferences=["high_school", "university"],
            availability_schedule={"monday": {"09:00": "17:00"}, "tuesday": {"09:00": "17:00"}},
            rate_structure={"standard": 25.0, "advanced": 30.0}
        )
        
        # Add profile photo to user
        self.teacher.profile_photo = "profile_photos/test.jpg"
        self.teacher.save()
        
        # Profile should now be complete
        self.assertTrue(teacher_profile.is_profile_complete())
        self.assertTrue(teacher_profile.has_financial_details())
        
        # All requirements should be met
        requirements = teacher_profile.get_completion_requirements()
        for req in requirements.values():
            self.assertTrue(req["completed"])

    def test_account_activation_logic(self):
        """Test automatic account activation when all requirements are met."""
        # Create onboarding tasks
        TaskService.create_teacher_onboarding_tasks(self.teacher)
        
        # Create complete teacher profile
        teacher_profile = TeacherProfile.objects.create(
            user=self.teacher,
            bio="Experienced teacher",
            specialty="Mathematics",
            teaching_subjects=["Mathematics"],
            grade_level_preferences=["high_school"],
            availability_schedule={"monday": {"09:00": "17:00"}},
            rate_structure={"standard": 25.0}
        )
        
        # Add profile photo and verify email
        self.teacher.profile_photo = "profile_photos/test.jpg"
        self.teacher.email_verified = True
        self.teacher.save()
        
        # Complete all onboarding tasks
        TaskService.complete_teacher_onboarding_task(self.teacher, "Confirmar E-mail")
        TaskService.complete_teacher_onboarding_task(self.teacher, "Completar Perfil de Professor")
        TaskService.complete_teacher_onboarding_task(self.teacher, "Adicionar Dados Fiscais")
        TaskService.complete_teacher_onboarding_task(self.teacher, "Definir Disponibilidade Horária")
        
        # Refresh user from database
        self.teacher.refresh_from_db()
        
        # Account should now be activated
        self.assertTrue(self.teacher.onboarding_completed)

    def test_teacher_invitation_with_onboarding_tasks(self):
        """Test that teacher invitation creates appropriate onboarding tasks."""
        # Create teacher invitation
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="newteacher@example.com",
            invited_by=self.school_owner,
            custom_message="Welcome to our school!",
            batch_id=uuid.uuid4(),
        )
        
        # Simulate invitation acceptance (this would normally create the user)
        invited_teacher = CustomUser.objects.create_user(
            email="newteacher@example.com",
            name="Invited Teacher",
            phone_number="+351912000003"
        )
        
        # Create school membership
        SchoolMembership.objects.create(
            user=invited_teacher,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Create onboarding tasks for the new teacher
        tasks = TaskService.create_teacher_onboarding_tasks(invited_teacher)
        
        # Verify tasks were created correctly
        self.assertEqual(len(tasks), 4)
        self.assertEqual(
            Task.objects.filter(user=invited_teacher, task_type="onboarding").count(),
            4
        )
        
        # User should not be onboarding complete initially
        self.assertFalse(invited_teacher.onboarding_completed)

    def test_update_teacher_profile_completion_tasks(self):
        """Test updating tasks based on teacher profile completion status."""
        # Create teacher profile and onboarding tasks
        teacher_profile = TeacherProfile.objects.create(user=self.teacher)
        TaskService.create_teacher_onboarding_tasks(self.teacher)
        
        # Initially no tasks should be completed
        progress = TaskService.get_teacher_onboarding_progress(self.teacher)
        self.assertEqual(progress["completed_tasks"], 0)
        
        # Complete teacher profile
        teacher_profile.bio = "Experienced teacher"
        teacher_profile.specialty = "Mathematics"
        teacher_profile.teaching_subjects = ["Mathematics"]
        teacher_profile.grade_level_preferences = ["high_school"]
        teacher_profile.availability_schedule = {"monday": {"09:00": "17:00"}}
        teacher_profile.rate_structure = {"standard": 25.0}
        teacher_profile.save()
        
        # Add profile photo
        self.teacher.profile_photo = "profile_photos/test.jpg"
        self.teacher.save()
        
        # Update tasks based on profile completion
        TaskService.update_teacher_profile_completion_tasks(self.teacher)
        
        # Profile completion task should now be completed
        profile_task = Task.objects.filter(
            user=self.teacher,
            title="Completar Perfil de Professor",
            status="completed"
        ).first()
        self.assertIsNotNone(profile_task)
        
        # Financial and availability tasks should also be completed
        financial_task = Task.objects.filter(
            user=self.teacher,
            title="Adicionar Dados Fiscais",
            status="completed"
        ).first()
        self.assertIsNotNone(financial_task)
        
        availability_task = Task.objects.filter(
            user=self.teacher,
            title="Definir Disponibilidade Horária", 
            status="completed"
        ).first()
        self.assertIsNotNone(availability_task)