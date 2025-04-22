from rest_framework import permissions


class IsTeacher(permissions.BasePermission):
    """
    Custom permission to only allow teachers to access the view.
    """

    def has_permission(self, request, view):  # noqa: U100
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

    def has_permission(self, request, view):  # noqa: U100
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

    def has_permission(self, request, view):  # noqa: U100
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

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_staff
                or request.user.is_superuser
                or (
                    hasattr(request.user, "user_type")
                    and request.user.user_type == "manager"
                )
            )
        )


class IsOwnerOrManager(permissions.BasePermission):
    """
    Object-level permission to allow both owners and managers/admins access.
    """

    def has_permission(self, request, view):
        # Always allow managers and admins
        if (
            request.user.is_staff
            or request.user.is_superuser
            or (
                hasattr(request.user, "user_type")
                and request.user.user_type == "manager"
            )
        ):
            return True
        return (
            True  # For object-level permissions, we'll check in has_object_permission
        )

    def has_object_permission(self, request, view, obj):
        # Managers and admins can access all objects
        if (
            request.user.is_staff
            or request.user.is_superuser
            or (
                hasattr(request.user, "user_type")
                and request.user.user_type == "manager"
            )
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

    def has_object_permission(self, request, view, obj):  # noqa: U100
        # Instance must have an attribute named `owner` or `user`
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        elif hasattr(obj, "user"):
            return obj.user == request.user
        return False
