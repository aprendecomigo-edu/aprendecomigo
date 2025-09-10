"""
Centralized authorization logic for guardian-student relationships.

This module provides a unified permission system for managing access control
between students, guardians, and other user roles in the educational platform.
"""

from typing import List, Optional
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models.enums import FinancialResponsibility, SchoolRole
from .models.profiles import StudentProfile, GuardianProfile


User = get_user_model()


class AccountPermissions:
    """
    Centralized permission logic for guardian-student relationships.
    
    This class provides a single source of truth for authorization decisions
    across the application, handling various permission scenarios based on
    financial responsibility settings.
    """
    
    # Permission matrix defining who can perform which actions based on financial responsibility
    PERMISSION_MATRIX = {
        'view_profile': {
            FinancialResponsibility.SELF: ['student'],
            FinancialResponsibility.GUARDIAN: ['student', 'guardian'],
            FinancialResponsibility.SHARED: ['student', 'guardian'],
        },
        'view_grades': {
            FinancialResponsibility.SELF: ['student'],
            FinancialResponsibility.GUARDIAN: ['student', 'guardian'],
            FinancialResponsibility.SHARED: ['student', 'guardian'],
        },
        'view_attendance': {
            FinancialResponsibility.SELF: ['student'],
            FinancialResponsibility.GUARDIAN: ['student', 'guardian'],
            FinancialResponsibility.SHARED: ['student', 'guardian'],
        },
        'make_payment': {
            FinancialResponsibility.SELF: ['student'],
            FinancialResponsibility.GUARDIAN: ['guardian'],
            FinancialResponsibility.SHARED: ['student', 'guardian'],
        },
        'book_session': {
            FinancialResponsibility.SELF: ['student'],
            FinancialResponsibility.GUARDIAN: ['guardian'],
            FinancialResponsibility.SHARED: ['student', 'guardian'],
        },
        'cancel_session': {
            FinancialResponsibility.SELF: ['student'],
            FinancialResponsibility.GUARDIAN: ['guardian'],
            FinancialResponsibility.SHARED: ['student', 'guardian'],
        },
        'update_profile': {
            FinancialResponsibility.SELF: ['student'],
            FinancialResponsibility.GUARDIAN: ['guardian'],
            FinancialResponsibility.SHARED: ['student', 'guardian'],
        },
        'manage_budget': {
            FinancialResponsibility.SELF: ['student'],
            FinancialResponsibility.GUARDIAN: ['guardian'],
            FinancialResponsibility.SHARED: ['guardian'],  # Only guardian can set budgets
        },
        'approve_purchase': {
            FinancialResponsibility.SELF: [],  # Student doesn't need to approve their own
            FinancialResponsibility.GUARDIAN: ['guardian'],
            FinancialResponsibility.SHARED: ['guardian'],
        },
        'view_financial_history': {
            FinancialResponsibility.SELF: ['student'],
            FinancialResponsibility.GUARDIAN: ['guardian'],
            FinancialResponsibility.SHARED: ['student', 'guardian'],
        },
    }
    
    @classmethod
    def can_perform_action(cls, user: User, student_profile: StudentProfile, action: str) -> bool:
        """
        Check if a user can perform a specific action for a student.
        
        Args:
            user: The user attempting the action
            student_profile: The student profile being acted upon
            action: The action being attempted (from PERMISSION_MATRIX keys)
        
        Returns:
            bool: True if the user can perform the action, False otherwise
        """
        if not user or not student_profile:
            return False
        
        # Superusers can do everything
        if user.is_superuser:
            return True
        
        # Get the financial responsibility setting
        responsibility = student_profile.financial_responsibility
        
        # Get allowed roles for this action and responsibility combination
        allowed_roles = cls.PERMISSION_MATRIX.get(action, {}).get(responsibility, [])
        
        # Check if user is the student
        if 'student' in allowed_roles and user == student_profile.user:
            return True
        
        # Check if user is the guardian
        if 'guardian' in allowed_roles and student_profile.guardian:
            if user == student_profile.guardian.user:
                return True
        
        return False
    
    @classmethod
    def can_make_purchases(cls, user: User, student_profile: StudentProfile) -> bool:
        """
        Check if a user can make purchases for a student.
        
        This is a convenience method that wraps can_perform_action for purchases.
        """
        return cls.can_perform_action(user, student_profile, 'make_payment')
    
    @classmethod
    def can_book_sessions(cls, user: User, student_profile: StudentProfile) -> bool:
        """
        Check if a user can book sessions for a student.
        
        This is a convenience method that wraps can_perform_action for session booking.
        """
        return cls.can_perform_action(user, student_profile, 'book_session')
    
    @classmethod
    def get_financial_responsible_user(cls, student_profile: StudentProfile) -> Optional[User]:
        """
        Get the primary user responsible for financial decisions.
        
        Args:
            student_profile: The student profile
        
        Returns:
            User: The user responsible for financial decisions
        """
        if student_profile.financial_responsibility == FinancialResponsibility.SELF:
            return student_profile.user
        elif student_profile.financial_responsibility == FinancialResponsibility.GUARDIAN:
            return student_profile.guardian.user if student_profile.guardian else None
        elif student_profile.financial_responsibility == FinancialResponsibility.SHARED:
            # For shared responsibility, return the student as primary
            # but both should be checked using get_authorized_users()
            return student_profile.user
        return student_profile.user  # Fallback to student
    
    @classmethod
    def get_authorized_users(cls, student_profile: StudentProfile) -> List[User]:
        """
        Get all users who can act on behalf of this student.
        
        Args:
            student_profile: The student profile
        
        Returns:
            List[User]: List of authorized users
        """
        authorized = [student_profile.user]
        
        if student_profile.guardian and student_profile.financial_responsibility in [
            FinancialResponsibility.GUARDIAN, 
            FinancialResponsibility.SHARED
        ]:
            authorized.append(student_profile.guardian.user)
        
        return authorized
    
    @classmethod
    def get_students_for_guardian(cls, guardian_user: User) -> List[StudentProfile]:
        """
        Get all students that a guardian is responsible for.
        
        Args:
            guardian_user: The guardian user
        
        Returns:
            List[StudentProfile]: List of student profiles
        """
        if not hasattr(guardian_user, 'guardian_profile'):
            return []
        
        # Get all students where this guardian is responsible
        return StudentProfile.objects.filter(
            guardian=guardian_user.guardian_profile,
            financial_responsibility__in=[
                FinancialResponsibility.GUARDIAN,
                FinancialResponsibility.SHARED
            ]
        ).select_related('user', 'educational_system')
    
    @classmethod
    def requires_guardian_approval(cls, student_profile: StudentProfile, action: str) -> bool:
        """
        Check if an action requires guardian approval.
        
        Args:
            student_profile: The student profile
            action: The action being attempted
        
        Returns:
            bool: True if guardian approval is required
        """
        if student_profile.financial_responsibility == FinancialResponsibility.SELF:
            return False
        
        # For guardian and shared responsibility, check if action needs approval
        approval_required_actions = ['make_payment', 'book_session', 'cancel_session']
        
        if action in approval_required_actions:
            if student_profile.financial_responsibility == FinancialResponsibility.GUARDIAN:
                return True
            elif student_profile.financial_responsibility == FinancialResponsibility.SHARED:
                # In shared mode, could implement threshold-based approval
                # For now, return True for significant actions
                return action in ['make_payment']
        
        return False
    
    @classmethod
    def is_self_managed(cls, student_profile: StudentProfile) -> bool:
        """
        Check if a student manages their own account.
        
        Args:
            student_profile: The student profile
        
        Returns:
            bool: True if student is self-managed
        """
        return (
            student_profile.financial_responsibility == FinancialResponsibility.SELF or
            (student_profile.guardian and student_profile.guardian.user == student_profile.user)
        )
    
    @classmethod
    def get_permission_summary(cls, user: User, student_profile: StudentProfile) -> dict:
        """
        Get a summary of all permissions a user has for a student.
        
        Args:
            user: The user to check permissions for
            student_profile: The student profile
        
        Returns:
            dict: Dictionary of action -> bool for all permissions
        """
        return {
            action: cls.can_perform_action(user, student_profile, action)
            for action in cls.PERMISSION_MATRIX.keys()
        }


class SchoolPermissions:
    """
    Permission logic for school-level operations.
    
    Handles authorization for school administrators, teachers, and staff.
    """
    
    @classmethod
    def can_manage_school(cls, user: User, school) -> bool:
        """Check if user can manage school settings and users."""
        from .models.schools import SchoolMembership
        
        membership = SchoolMembership.objects.filter(
            user=user,
            school=school,
            is_active=True,
            role=SchoolRole.SCHOOL_ADMIN
        ).exists()
        
        return membership or user.is_superuser
    
    @classmethod
    def can_manage_students(cls, user: User, school) -> bool:
        """Check if user can manage student records."""
        from .models.schools import SchoolMembership
        
        membership = SchoolMembership.objects.filter(
            user=user,
            school=school,
            is_active=True,
            role__in=[SchoolRole.SCHOOL_ADMIN, SchoolRole.TEACHER]
        ).exists()
        
        return membership or user.is_superuser
    
    @classmethod
    def can_view_financial_reports(cls, user: User, school) -> bool:
        """Check if user can view financial reports."""
        from .models.schools import SchoolMembership
        
        membership = SchoolMembership.objects.filter(
            user=user,
            school=school,
            is_active=True,
            role=SchoolRole.SCHOOL_ADMIN
        ).exists()
        
        return membership or user.is_superuser
    
    @classmethod
    def get_user_schools(cls, user: User, role: Optional[SchoolRole] = None):
        """Get all schools where user has a specific role (or any role)."""
        from .models.schools import SchoolMembership
        
        query = SchoolMembership.objects.filter(
            user=user,
            is_active=True
        )
        
        if role:
            query = query.filter(role=role)
        
        return query.select_related('school')