"""
Simple permission model for student access control.
Replaces the complex authorization matrix with straightforward database records.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .enums import FinancialResponsibility


class StudentPermission(models.Model):
    """
    Simple permission model - who can do what for which student.
    One record per user-student relationship.
    """
    student = models.ForeignKey(
        'StudentProfile', 
        on_delete=models.CASCADE, 
        related_name='permissions'
    )
    user = models.ForeignKey(
        'CustomUser', 
        on_delete=models.CASCADE, 
        related_name='student_permissions'
    )
    
    # Core permissions - simple boolean flags
    can_view_profile = models.BooleanField(default=False)
    can_view_grades = models.BooleanField(default=False)
    can_view_attendance = models.BooleanField(default=False)
    can_make_payment = models.BooleanField(default=False)
    can_book_session = models.BooleanField(default=False)
    can_cancel_session = models.BooleanField(default=False)
    can_update_profile = models.BooleanField(default=False)
    can_manage_budget = models.BooleanField(default=False)
    can_view_financial = models.BooleanField(default=False)
    
    # Metadata
    expires_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'user']
        indexes = [
            models.Index(fields=['student', 'user']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.name} -> {self.student}"
    
    def is_expired(self):
        """Check if permission has expired"""
        return self.expires_at and self.expires_at < timezone.now()
    
    @classmethod
    def create_for_adult_student(cls, student_profile):
        """Create full permissions for adult student"""
        return cls.objects.update_or_create(
            student=student_profile,
            user=student_profile.user,
            defaults={
                'can_view_profile': True,
                'can_view_grades': True,
                'can_view_attendance': True,
                'can_make_payment': True,
                'can_book_session': True,
                'can_cancel_session': True,
                'can_update_profile': True,
                'can_manage_budget': True,
                'can_view_financial': True,
            }
        )
    
    @classmethod
    def create_for_guardian(cls, student_profile):
        """Create guardian permissions"""
        if not student_profile.guardian:
            return None
            
        return cls.objects.update_or_create(
            student=student_profile,
            user=student_profile.guardian.user,
            defaults={
                'can_view_profile': True,
                'can_view_grades': True,
                'can_view_attendance': True,
                'can_make_payment': True,
                'can_book_session': True,
                'can_cancel_session': True,
                'can_update_profile': True,
                'can_manage_budget': True,
                'can_view_financial': True,
            }
        )
    
    @classmethod
    def create_for_student_with_guardian(cls, student_profile):
        """Create limited permissions for student who has a guardian"""
        if not student_profile.user:
            return None
            
        return cls.objects.update_or_create(
            student=student_profile,
            user=student_profile.user,
            defaults={
                'can_view_profile': True,
                'can_view_grades': True,
                'can_view_attendance': True,
                'can_make_payment': False,  # Guardian handles money
                'can_book_session': False,  # Guardian books
                'can_cancel_session': False,  # Guardian cancels
                'can_update_profile': False,  # Guardian manages
                'can_manage_budget': False,  # Guardian only
                'can_view_financial': False,  # Guardian only
            }
        )