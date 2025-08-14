from rest_framework import permissions

from .models import School, SchoolMembership


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
        # Allow superusers and staff for admin purposes
        if request.user and request.user.is_authenticated:
            if request.user.is_superuser or request.user.is_staff:
                return True
            
            # Check school membership roles
            return SchoolMembership.objects.filter(
                user=request.user,
                role__in=["school_owner", "school_admin"],
                is_active=True,
            ).exists()
        
        return False

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


class SchoolPermissionMixin:
    """
    Mixin to provide school-related permission methods for ViewSets.

    This mixin provides helper methods to get schools that a user has access to
    based on their memberships and roles.
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
            user=self.request.user, is_active=True
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

        user_memberships = SchoolMembership.objects.filter(**query_filter).values_list(
            "school_id", flat=True
        )

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


class IsParentInAnySchool(permissions.BasePermission):
    """
    Custom permission to check if user is a parent in any school.
    """

    message = "You must be a parent to perform this action."

    def has_permission(self, request, _view):
        return (
            request.user
            and request.user.is_authenticated
            and SchoolMembership.objects.filter(
                user=request.user, role="parent", is_active=True
            ).exists()
        )

    def has_object_permission(self, request, _view, obj):
        # First check if user is a parent in any school
        if not SchoolMembership.objects.filter(
            user=request.user, role="parent", is_active=True
        ).exists():
            return False

        # If object has a school attribute, check if user is a parent in that school
        if hasattr(obj, "school"):
            return SchoolMembership.objects.filter(
                user=request.user, school=obj.school, role="parent", is_active=True
            ).exists()
        # If object is linked to a user, check if that user is the requester
        elif hasattr(obj, "user"):
            return obj.user == request.user
        return False


class IsParentOfStudent(permissions.BasePermission):
    """
    Custom permission to check if user is a parent of the student in question.
    Used for parent-child relationship access control.
    """

    message = "You must be the parent of this student to perform this action."

    def has_permission(self, request, _view):
        # Allow authentication check at view level
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        from .models import ParentChildRelationship
        
        # If the object has a student attribute, check parent-child relationship
        if hasattr(obj, "student"):
            return ParentChildRelationship.objects.filter(
                parent=request.user,
                child=obj.student,
                is_active=True
            ).exists()
        
        # If the object has a child attribute, check parent-child relationship
        if hasattr(obj, "child"):
            return ParentChildRelationship.objects.filter(
                parent=request.user,
                child=obj.child,
                is_active=True
            ).exists()
        
        # If the object IS a parent-child relationship, check if user is the parent
        if hasattr(obj, "parent") and hasattr(obj, "child"):
            return obj.parent == request.user
        
        # If object is linked to a user, check if that user is the requester
        if hasattr(obj, "user"):
            return obj.user == request.user
        
        return False


class IsStudentOrParent(permissions.BasePermission):
    """
    Permission that allows access to students themselves or their parents.
    Used for purchase-related endpoints where both student and parent need access.
    """

    message = "You must be this student or their parent to perform this action."

    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        from .models import ParentChildRelationship
        
        # If the object has a student attribute
        if hasattr(obj, "student"):
            # Allow if user is the student
            if obj.student == request.user:
                return True
            
            # Allow if user is a parent of the student
            return ParentChildRelationship.objects.filter(
                parent=request.user,
                child=obj.student,
                is_active=True
            ).exists()
        
        # If object is linked to a user, check if that user is the requester
        if hasattr(obj, "user"):
            if obj.user == request.user:
                return True
            
            # Check if user is a parent of the user
            return ParentChildRelationship.objects.filter(
                parent=request.user,
                child=obj.user,
                is_active=True
            ).exists()
        
        return False


class CanManageChildPurchases(permissions.BasePermission):
    """
    Permission for parents to manage their children's purchases and approval requests.
    """

    message = "You must be authorized to manage this child's purchases."

    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        from .models import ParentChildRelationship
        
        # For purchase approval requests
        if hasattr(obj, "parent") and hasattr(obj, "student"):
            return obj.parent == request.user
        
        # For budget controls
        if hasattr(obj, "parent_child_relationship"):
            return obj.parent_child_relationship.parent == request.user
        
        # For purchase transactions involving children
        if hasattr(obj, "student"):
            return ParentChildRelationship.objects.filter(
                parent=request.user,
                child=obj.student,
                is_active=True
            ).exists()
        
        return False


class IsParentWithChildren(permissions.BasePermission):
    """
    Custom permission to check if user is a parent with active children relationships.
    Used for parent dashboard and child management features.
    """

    message = "You must be a parent with active children to perform this action."

    def has_permission(self, request, _view):
        if not (request.user and request.user.is_authenticated):
            return False
            
        from .models import ParentChildRelationship
        
        # Check if user has any active parent-child relationships
        return ParentChildRelationship.objects.filter(
            parent=request.user,
            is_active=True
        ).exists()

    def has_object_permission(self, request, _view, obj):
        from .models import ParentChildRelationship
        
        # First check if user is a parent with children
        if not ParentChildRelationship.objects.filter(
            parent=request.user,
            is_active=True
        ).exists():
            return False
        
        # If object relates to a specific child, verify parent-child relationship
        if hasattr(obj, "child"):
            return ParentChildRelationship.objects.filter(
                parent=request.user,
                child=obj.child,
                is_active=True
            ).exists()
        
        # If object relates to a student, verify parent-child relationship
        if hasattr(obj, "student"):
            return ParentChildRelationship.objects.filter(
                parent=request.user,
                child=obj.student,
                is_active=True
            ).exists()
        
        # If object is linked to a user, check if that user is the requester
        if hasattr(obj, "user"):
            return obj.user == request.user
        
        return True  # User is a parent with children, allow general access
