"""
Permission mixins for Django views in Aprende Comigo application.

Following Django best practices:
- Use UserPassesTestMixin for permission checks
- Clear, descriptive naming convention  
- Single responsibility principle
- Centralized location for reusability

All mixins inherit from Django's LoginRequiredMixin to ensure authentication.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import School, SchoolMembership


# =======================
# SCHOOL PERMISSION MIXINS
# =======================


class IsSchoolOwnerOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check if user is a school owner or administrator.
    
    Allows access to users with:
    - Django superuser/staff privileges (system admin)
    - School owner role in any school
    - School admin role in any school
    
    For views with get_object(), also checks object-level permissions.
    """

    permission_denied_message = "You must be a school owner or administrator to perform this action."

    def test_func(self):
        # Allow Django superusers and staff for system administration
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True

        # Check school membership roles for basic permission
        has_basic_permission = SchoolMembership.objects.filter(
            user=self.request.user,
            role__in=["school_owner", "school_admin"],
            is_active=True,
        ).exists()
        
        if not has_basic_permission:
            return False

        # Check object-level permission if we have get_object method
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            return self.check_school_admin_permission(obj)
        return True  # For list views, basic permission is sufficient

    def check_school_admin_permission(self, obj):
        """Check if user has admin permission for this specific object."""
        # Django superuser or staff can access all objects
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True

        # If object has a school attribute, check if user is an owner/admin in that school
        if hasattr(obj, "school"):
            return SchoolMembership.objects.filter(
                user=self.request.user,
                school=obj.school,
                role__in=["school_owner", "school_admin"],
                is_active=True,
            ).exists()
        # If object is a school itself
        elif hasattr(obj, "id") and obj._meta.model_name == "school":
            return SchoolMembership.objects.filter(
                user=self.request.user,
                school=obj,
                role__in=["school_owner", "school_admin"],
                is_active=True,
            ).exists()
        # If object is linked to a user, check if that user is the requester
        elif hasattr(obj, "user"):
            return obj.user == self.request.user
        # If object is a user, check if it's the requester
        elif hasattr(obj, "id") and hasattr(self.request.user, "id") and obj._meta.model_name == "customuser":
            return obj.id == self.request.user.id
        return False


# =======================
# HELPER MIXINS  
# =======================


class SchoolPermissionMixin:
    """
    Mixin providing school-related permission helper methods for Django views.

    This mixin provides utility methods to get schools that a user has access to
    based on their memberships and roles. Does not enforce permissions by itself.
    """

    def get_user_schools(self):
        """
        Get all schools that the current user has access to.

        Returns:
            QuerySet of School objects the user can access
        """
        if not self.request.user.is_authenticated:
            return School.objects.none()

        # Superusers can access all schools
        if self.request.user.is_superuser:
            return School.objects.all()

        # Get schools where user has any active membership
        user_memberships = SchoolMembership.objects.filter(
            user=self.request.user, 
            is_active=True
        ).values_list("school_id", flat=True)

        return School.objects.filter(id__in=user_memberships)

    def get_user_schools_by_role(self, role=None):
        """
        Get schools where the user has a specific role.

        Args:
            role: The role to filter by (e.g., 'school_owner', 'school_admin', 'teacher')

        Returns:
            QuerySet of School objects where user has the specified role
        """
        if not self.request.user.is_authenticated:
            return School.objects.none()

        # Superusers can access all schools regardless of role
        if self.request.user.is_superuser:
            return School.objects.all()

        query_filter = {"user": self.request.user, "is_active": True}

        if role:
            query_filter["role"] = role

        user_memberships = SchoolMembership.objects.filter(**query_filter).values_list("school_id", flat=True)

        return School.objects.filter(id__in=user_memberships)

    def has_school_permission(self, school, required_roles=None):
        """
        Check if user has permission for a specific school.

        Args:
            school: School instance or school ID
            required_roles: List of required roles (optional)

        Returns:
            Boolean indicating if user has permission
        """
        if not self.request.user.is_authenticated:
            return False

        # Superusers have permission for all schools
        if self.request.user.is_superuser:
            return True

        # Get school ID if school object is passed
        school_id = school.id if hasattr(school, "id") else school

        query_filter = {"user": self.request.user, "school_id": school_id, "is_active": True}

        if required_roles:
            query_filter["role__in"] = required_roles

        return SchoolMembership.objects.filter(**query_filter).exists()