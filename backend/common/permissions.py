from accounts.models import SchoolMembership
from rest_framework import permissions


class IsTeacher(permissions.BasePermission):
    """
    Custom permission to only allow teachers to access the view.
    """

    def has_permission(self, request, _view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "user_type")
            and request.user.user_type == "teacher"
        )


class IsStudent(permissions.BasePermission):
    """
    Custom permission to only allow students to access the view.
    """

    def has_permission(self, request, _view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "user_type")
            and request.user.user_type == "student"
        )


class IsParent(permissions.BasePermission):
    """
    Custom permission to only allow parents to access the view.
    """

    def has_permission(self, request, _view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "user_type")
            and request.user.user_type == "parent"
        )


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow managers or admins to access the view.
    """

    def has_permission(self, request, _view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_staff
                or request.user.is_superuser
                or (hasattr(request.user, "user_type") and request.user.user_type == "manager")
            )
        )


class IsOwnerOrManager(permissions.BasePermission):
    """
    Object-level permission to allow both owners and managers/admins access.
    """

    def has_permission(self, request, _view):
        # Always allow managers and admins
        if (
            request.user.is_staff
            or request.user.is_superuser
            or (hasattr(request.user, "user_type") and request.user.user_type == "manager")
        ):
            return True
        return True  # For object-level permissions, we'll check in has_object_permission

    def has_object_permission(self, request, _view, obj):
        # Managers and admins can access all objects
        if (
            request.user.is_staff
            or request.user.is_superuser
            or (hasattr(request.user, "user_type") and request.user.user_type == "manager")
        ):
            return True

        # Check for ownership
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        elif hasattr(obj, "user"):
            return obj.user == request.user
        elif hasattr(obj, "id") and hasattr(request.user, "id"):
            return obj.id == request.user.id
        return False


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, _view, obj):
        # Instance must have an attribute named `owner` or `user`
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        elif hasattr(obj, "user"):
            return obj.user == request.user
        return False


class IsTeacherInAnySchool(permissions.BasePermission):
    """
    Custom permission to check if user is a teacher in any school.
    """

    message = "You must be a teacher to perform this action."

    def has_permission(self, request, _view):
        return (
            request.user
            and request.user.is_authenticated
            and SchoolMembership.objects.filter(
                user=request.user, role="teacher", is_active=True
            ).exists()
        )

    def has_object_permission(self, request, _view, obj):
        # First check if user is a teacher in any school
        if not SchoolMembership.objects.filter(
            user=request.user, role="teacher", is_active=True
        ).exists():
            return False

        # If object has a school attribute, check if user is a teacher in that school
        if hasattr(obj, "school"):
            return SchoolMembership.objects.filter(
                user=request.user, school=obj.school, role="teacher", is_active=True
            ).exists()
        # If object is linked to a user, check if that user is the requester
        elif hasattr(obj, "user"):
            return obj.user == request.user
        return False


class IsStudentInAnySchool(permissions.BasePermission):
    """
    Custom permission to check if user is a student in any school.
    """

    message = "You must be a student to perform this action."

    def has_permission(self, request, _view):
        return (
            request.user
            and request.user.is_authenticated
            and SchoolMembership.objects.filter(
                user=request.user, role="student", is_active=True
            ).exists()
        )

    def has_object_permission(self, request, _view, obj):
        # First check if user is a student in any school
        if not SchoolMembership.objects.filter(
            user=request.user, role="student", is_active=True
        ).exists():
            return False

        # If object has a school attribute, check if user is a student in that school
        if hasattr(obj, "school"):
            return SchoolMembership.objects.filter(
                user=request.user, school=obj.school, role="student", is_active=True
            ).exists()
        # If object is linked to a user, check if that user is the requester
        elif hasattr(obj, "user"):
            return obj.user == request.user
        return False


class IsSchoolOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to check if user is an owner or admin of any school.
    """

    message = "You must be a school owner or administrator to perform this action."

    def has_permission(self, request, _view):
        return (
            request.user
            and request.user.is_authenticated
            and SchoolMembership.objects.filter(
                user=request.user,
                role__in=["school_owner", "school_admin"],
                is_active=True,
            ).exists()
        )

    def has_object_permission(self, request, _view, obj):
        # If it's a Django superuser or staff, allow access for admin purposes
        if request.user.is_superuser or request.user.is_staff:
            return True

        # If object has a school attribute, check if user is an owner/admin in that school
        if hasattr(obj, "school"):
            return SchoolMembership.objects.filter(
                user=request.user,
                school=obj.school,
                role__in=["school_owner", "school_admin"],
                is_active=True,
            ).exists()
        # If object is a school itself
        elif hasattr(obj, "id") and obj._meta.model_name == "school":
            return SchoolMembership.objects.filter(
                user=request.user,
                school=obj,
                role__in=["school_owner", "school_admin"],
                is_active=True,
            ).exists()
        # If object is linked to a user, check if that user is the requester
        elif hasattr(obj, "user"):
            return obj.user == request.user
        # If object is a user, check if it's the requester
        elif (
            hasattr(obj, "id")
            and hasattr(request.user, "id")
            and obj._meta.model_name == "customuser"
        ):
            return obj.id == request.user.id
        return False


class IsOwnerOrSchoolAdmin(permissions.BasePermission):
    """
    Object-level permission to allow both owners and school admins access.
    """

    message = "You must be the owner of this resource or a school administrator."

    def has_permission(self, request, _view):
        # Always allow Django superusers and staff
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Allow school owner/admin permission to be checked at the object level
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        # Django superusers and staff can access all objects
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Check for school ownership/admin if object has a school
        if hasattr(obj, "school"):
            school_admin_access = SchoolMembership.objects.filter(
                user=request.user,
                school=obj.school,
                role__in=["school_owner", "school_admin"],
                is_active=True,
            ).exists()
            if school_admin_access:
                return True

        # Check for direct ownership
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        elif hasattr(obj, "user"):
            return obj.user == request.user
        elif (
            hasattr(obj, "id")
            and hasattr(request.user, "id")
            and obj._meta.model_name == "customuser"
        ):
            return obj.id == request.user.id
        return False


class IsSuperUserOrSystemAdmin(permissions.BasePermission):
    """
    Django system-level permission for backend administration.
    This is separate from application roles and should only be used
    for system administration endpoints.
    """

    message = "This action requires system administrator privileges."

    def has_permission(self, request, _view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.is_staff)
        )
