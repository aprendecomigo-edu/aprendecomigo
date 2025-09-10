"""
Integration test demonstrating the complete teacher onboarding workflow.

This test shows the full flow from admin invitation creation to teacher account activation,
demonstrating all the components working together.
"""

import uuid

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import (
    School,
    SchoolMembership,
    SchoolRole,
    TeacherInvitation,
    TeacherProfile,
)
from tasks.models import Task
from tasks.services import TaskService

User = get_user_model()


class TeacherOnboardingIntegrationTest(TestCase):
    """Integration test for the complete teacher onboarding workflow."""

    def setUp(self):
        """Set up test data for integration testing."""
        self.client = Client()
        
        # Create school and admin
        self.school = School.objects.create(
            name="Integration Test School",
            description="School for testing complete workflow"
        )
        
        self.admin = User.objects.create_user(
            email="admin@school.com",
            name="School Admin",
            phone_number="+351912000001"
        )
        
        SchoolMembership.objects.create(
            user=self.admin,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )

    def test_complete_teacher_onboarding_workflow(self):
        """Test the complete teacher onboarding workflow from start to finish."""
        
        # Step 1: Admin creates teacher invitation
        invitation = TeacherInvitation.objects.create(
            school=self.school,
            email="newteacher@example.com",
            invited_by=self.admin,
            custom_message="Welcome to our school team!",
            batch_id=uuid.uuid4(),
        )
        
        self.assertTrue(invitation.is_valid())
        self.assertEqual(invitation.status, "pending")
        
        # Step 2: Teacher accepts invitation (simulated - normally done via POST to AcceptTeacherInvitationView)
        # Create teacher user as would happen during invitation acceptance
        teacher = User.objects.create_user(
            email="newteacher@example.com",
            name="New Teacher",
            phone_number="+351912000002"
        )
        
        # Create school membership
        SchoolMembership.objects.create(
            user=teacher,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Mark invitation as accepted
        invitation.accept()
        
        # Step 3: Create teacher onboarding tasks
        tasks = TaskService.create_teacher_onboarding_tasks(teacher)
        
        self.assertEqual(len(tasks), 4)
        self.assertFalse(teacher.onboarding_completed)
        
        # Verify all expected tasks were created
        task_titles = [task.title for task in tasks]
        expected_titles = [
            "Confirmar E-mail",
            "Completar Perfil de Professor", 
            "Adicionar Dados Fiscais",
            "Definir Disponibilidade Horária"
        ]
        
        for title in expected_titles:
            self.assertIn(title, task_titles)
        
        # Step 4: Teacher completes email verification
        teacher.email_verified = True
        teacher.save()
        
        TaskService.complete_teacher_onboarding_task(teacher, "Confirmar E-mail")
        
        # Check progress
        progress = TaskService.get_teacher_onboarding_progress(teacher)
        self.assertEqual(progress["completed_tasks"], 1)
        self.assertEqual(progress["progress_percentage"], 25.0)
        
        # Step 5: Teacher completes profile
        teacher_profile = TeacherProfile.objects.create(
            user=teacher,
            bio="Experienced mathematics teacher with passion for education",
            specialty="Mathematics",
            teaching_subjects=["Mathematics", "Statistics"],
            grade_level_preferences=["middle_school", "high_school"],
            availability_schedule={
                "monday": {"09:00": "17:00"},
                "tuesday": {"09:00": "17:00"},
                "wednesday": {"09:00": "17:00"}
            },
            rate_structure={"standard": 25.0, "premium": 30.0}
        )
        
        # Add profile photo
        teacher.profile_photo = "profile_photos/teacher.jpg"
        teacher.save()
        
        # Verify profile is complete
        self.assertTrue(teacher_profile.is_profile_complete())
        self.assertTrue(teacher_profile.has_financial_details())
        
        # Update tasks based on profile completion
        TaskService.update_teacher_profile_completion_tasks(teacher)
        
        # Check progress - should now be complete
        progress = TaskService.get_teacher_onboarding_progress(teacher)
        self.assertEqual(progress["completed_tasks"], 4)
        self.assertEqual(progress["progress_percentage"], 100.0)
        self.assertTrue(progress["is_complete"])
        
        # Step 6: Account should now be activated
        teacher.refresh_from_db()
        self.assertTrue(teacher.onboarding_completed)
        
        # Verify all tasks are completed
        completed_tasks = Task.objects.filter(
            user=teacher,
            task_type="onboarding",
            status="completed"
        )
        self.assertEqual(completed_tasks.count(), 4)
        
        # Verify invitation is properly accepted
        invitation.refresh_from_db()
        self.assertTrue(invitation.is_accepted)
        self.assertEqual(invitation.status, "accepted")
        
        print("✅ Complete teacher onboarding workflow test passed!")
        print(f"📊 Teacher completed {progress['completed_tasks']}/4 onboarding tasks")
        print(f"🎯 Progress: {progress['progress_percentage']}%")
        print(f"✨ Account activated: {teacher.onboarding_completed}")

    def test_workflow_with_partial_completion(self):
        """Test workflow when teacher only partially completes onboarding."""
        
        # Create teacher and invitation
        teacher = User.objects.create_user(
            email="partial@example.com",
            name="Partial Teacher",
            phone_number="+351912000003"
        )
        
        SchoolMembership.objects.create(
            user=teacher,
            school=self.school,
            role=SchoolRole.TEACHER,
            is_active=True
        )
        
        # Create onboarding tasks
        TaskService.create_teacher_onboarding_tasks(teacher)
        
        # Only complete email verification
        teacher.email_verified = True
        teacher.save()
        TaskService.complete_teacher_onboarding_task(teacher, "Confirmar E-mail")
        
        # Create incomplete profile (missing some required fields)
        TeacherProfile.objects.create(
            user=teacher,
            bio="Short bio",
            specialty="English"
            # Missing: teaching_subjects, grade_level_preferences, availability_schedule
        )
        
        # Check progress
        progress = TaskService.get_teacher_onboarding_progress(teacher)
        self.assertEqual(progress["completed_tasks"], 1)
        self.assertFalse(progress["is_complete"])
        
        # Account should NOT be activated
        teacher.refresh_from_db()
        self.assertFalse(teacher.onboarding_completed)
        
        print("✅ Partial completion test passed!")
        print(f"📊 Teacher completed {progress['completed_tasks']}/4 onboarding tasks")
        print(f"🎯 Progress: {progress['progress_percentage']}%")
        print(f"❌ Account activated: {teacher.onboarding_completed} (correctly not activated)")