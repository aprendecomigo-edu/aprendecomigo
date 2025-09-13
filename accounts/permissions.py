"""
Simple permission service to replace the complex authorization system.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import get_object_or_404

from .models import School, SchoolRole
from .models.permissions import StudentPermission

User = get_user_model()


class PermissionService:
    """
    Dead simple permission checker.
    """

    @classmethod
    def can(cls, user, student_profile, action):
        """
        Check if user can perform action on student.

        Args:
            user: User attempting action
            student_profile: StudentProfile being accessed
            action: String like 'can_view_profile', 'can_make_payment'

        Returns:
            bool: True if allowed
        """
        if not user or not student_profile:
            return False

        # Superusers can do everything
        if user.is_superuser:
            return True

        try:
            # Get permission record
            permission = StudentPermission.objects.filter(student=student_profile, user=user).first()

            if not permission:
                return False

            # Check if expired
            if permission.is_expired():
                return False

            # Check the specific permission
            return getattr(permission, action, False)
        except Exception:
            # On any error, deny access for security
            return False

    @classmethod
    def can_make_payment(cls, user, student_profile):
        """Convenience method"""
        return cls.can(user, student_profile, "can_make_payment")

    @classmethod
    def can_book_session(cls, user, student_profile):
        """Convenience method"""
        return cls.can(user, student_profile, "can_book_session")

    @classmethod
    def can_view_financial(cls, user, student_profile):
        """Convenience method"""
        return cls.can(user, student_profile, "can_view_financial")

    @classmethod
    def get_authorized_users(cls, student_profile):
        """Get all users who have any permissions for this student (non-expired)"""
        from django.utils import timezone

        return (
            User.objects.filter(student_permissions__student=student_profile)
            .filter(
                models.Q(student_permissions__expires_at__isnull=True)
                | models.Q(student_permissions__expires_at__gt=timezone.now())
            )
            .distinct()
        )

    @classmethod
    def setup_permissions_for_student(cls, student_profile):
        """
        Auto-setup permissions based on student configuration.
        Call this when student/guardian relationships change.
        """
        # Clear existing permissions
        StudentPermission.objects.filter(student=student_profile).delete()

        if student_profile.account_type == "ADULT_STUDENT":
            # Adult student - full control, no guardian
            StudentPermission.create_for_adult_student(student_profile)

        elif student_profile.account_type == "GUARDIAN_ONLY":
            # Guardian manages everything, student has no account
            StudentPermission.create_for_guardian(student_profile)

        elif student_profile.account_type == "STUDENT_GUARDIAN":
            # Both have accounts: Guardian handles money, student views only
            StudentPermission.create_for_guardian(student_profile)
            StudentPermission.create_for_student_with_guardian(student_profile)


class SchoolPermissionMixin:
    """
    Mixin for views that require school-level permissions.
    Provides basic school access validation.
    Must be used with LoginRequiredMixin.
    """

    def get_school(self):
        """Get school from URL kwargs."""
        if hasattr(self, "_school"):
            return self._school

        # This will work because this mixin is used with Django class-based views
        school_pk = getattr(self, "kwargs", {}).get("school_pk") or getattr(self, "kwargs", {}).get("pk")
        if school_pk:
            self._school = get_object_or_404(School, pk=school_pk)
            return self._school
        return None

    def dispatch(self, request, *args, **kwargs):
        """Check if user has access to the school before dispatching."""
        school = self.get_school()
        if school and not self.has_school_access(request.user, school):
            raise PermissionDenied("You don't have access to this school.")
        return super().dispatch(request, *args, **kwargs)

    def has_school_access(self, user, school):
        """Check if user has access to the school."""
        if user.is_superuser:
            return True
        return user.school_memberships.filter(school=school, is_active=True).exists()


class IsSchoolOwnerOrAdminMixin(SchoolPermissionMixin):
    """
    Mixin for views that require school owner or admin permissions.
    """

    def has_school_access(self, user, school):
        """Check if user is school owner or admin."""
        if user.is_superuser:
            return True
        return user.school_memberships.filter(
            school=school, is_active=True, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN]
        ).exists()
