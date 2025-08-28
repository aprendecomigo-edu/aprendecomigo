from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import School, SchoolMembership


class IsTeacherMixin(UserPassesTestMixin):
    """
    Mixin to only allow teachers to access the view.
    """

    def test_func(self):
        return (
            self.request.user
            and self.request.user.is_authenticated
            and hasattr(self.request.user, "user_type")
            and self.request.user.user_type == "teacher"
        )


class IsStudentMixin(UserPassesTestMixin):
    """
    Mixin to only allow students to access the view.
    """

    def test_func(self):
        return (
            self.request.user
            and self.request.user.is_authenticated
            and hasattr(self.request.user, "user_type")
            and self.request.user.user_type == "student"
        )


class IsParentMixin(UserPassesTestMixin):
    """
    Mixin to only allow parents to access the view.
    """

    def test_func(self):
        return (
            self.request.user
            and self.request.user.is_authenticated
            and hasattr(self.request.user, "user_type")
            and self.request.user.user_type == "parent"
        )


class IsManagerOrAdminMixin(UserPassesTestMixin):
    """
    Mixin to only allow managers or admins to access the view.
    """

    def test_func(self):
        return (
            self.request.user
            and self.request.user.is_authenticated
            and (
                self.request.user.is_staff
                or self.request.user.is_superuser
                or (hasattr(self.request.user, "user_type") and self.request.user.user_type == "manager")
            )
        )


class IsOwnerOrManagerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to allow both owners and managers/admins access.
    """

    def test_func(self):
        # Always allow managers and admins
        if (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or (hasattr(self.request.user, "user_type") and self.request.user.user_type == "manager")
        ):
            return True
        
        # Check object-level permission if we have get_object method
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            return self.check_object_ownership(obj)
        return True  # For list views, allow general access

    def check_object_ownership(self, obj):
        """Check if user owns the object"""
        # Check for ownership
        if hasattr(obj, "owner"):
            return obj.owner == self.request.user
        elif hasattr(obj, "user"):
            return obj.user == self.request.user
        elif hasattr(obj, "id") and hasattr(self.request.user, "id"):
            return obj.id == self.request.user.id
        return False


class IsOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to only allow owners of an object to access it.
    Assumes the model instance has an `owner` attribute.
    """

    def test_func(self):
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            # Instance must have an attribute named `owner` or `user`
            if hasattr(obj, "owner"):
                return obj.owner == self.request.user
            elif hasattr(obj, "user"):
                return obj.user == self.request.user
        return False


class IsTeacherInAnySchoolMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check if user is a teacher in any school.
    """

    permission_denied_message = "You must be a teacher to perform this action."

    def test_func(self):
        if not SchoolMembership.objects.filter(
            user=self.request.user, role="teacher", is_active=True
        ).exists():
            return False

        # Check object-level permission if we have get_object method
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            # If object has a school attribute, check if user is a teacher in that school
            if hasattr(obj, "school"):
                return SchoolMembership.objects.filter(
                    user=self.request.user, school=obj.school, role="teacher", is_active=True
                ).exists()
            # If object is linked to a user, check if that user is the requester
            elif hasattr(obj, "user"):
                return obj.user == self.request.user
        return True  # For list views, basic teacher permission is sufficient


class IsStudentInAnySchoolMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check if user is a student in any school.
    """

    permission_denied_message = "You must be a student to perform this action."

    def test_func(self):
        if not SchoolMembership.objects.filter(
            user=self.request.user, role="student", is_active=True
        ).exists():
            return False

        # Check object-level permission if we have get_object method
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            # If object has a school attribute, check if user is a student in that school
            if hasattr(obj, "school"):
                return SchoolMembership.objects.filter(
                    user=self.request.user, school=obj.school, role="student", is_active=True
                ).exists()
            # If object is linked to a user, check if that user is the requester
            elif hasattr(obj, "user"):
                return obj.user == self.request.user
        return True  # For list views, basic student permission is sufficient


class IsSchoolOwnerOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check if user is an owner or admin of any school.
    """

    permission_denied_message = "You must be a school owner or administrator to perform this action."

    def test_func(self):
        # Allow superusers and staff for admin purposes
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
        """Check if user has admin permission for this specific object"""
        # If it's a Django superuser or staff, allow access for admin purposes
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


class IsOwnerOrSchoolAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to allow both owners and school admins access.
    """

    permission_denied_message = "You must be the owner of this resource or a school administrator."

    def test_func(self):
        # Always allow Django superusers and staff
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True

        # Check object-level permission if we have get_object method
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            return self.check_owner_or_school_admin_permission(obj)
        return True  # For list views, allow authenticated users

    def check_owner_or_school_admin_permission(self, obj):
        """Check if user is owner or school admin for this object"""
        # Django superusers and staff can access all objects
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True

        # Check for school ownership/admin if object has a school
        if hasattr(obj, "school"):
            school_admin_access = SchoolMembership.objects.filter(
                user=self.request.user,
                school=obj.school,
                role__in=["school_owner", "school_admin"],
                is_active=True,
            ).exists()
            if school_admin_access:
                return True

        # Check for direct ownership
        if hasattr(obj, "owner"):
            return obj.owner == self.request.user
        elif hasattr(obj, "user"):
            return obj.user == self.request.user
        elif hasattr(obj, "id") and hasattr(self.request.user, "id") and obj._meta.model_name == "customuser":
            return obj.id == self.request.user.id
        return False


class IsSuperUserOrSystemAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Django system-level permission for backend administration.
    This is separate from application roles and should only be used
    for system administration endpoints.
    """

    permission_denied_message = "This action requires system administrator privileges."

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff


class SchoolPermissionMixin:
    """
    Mixin to provide school-related permission methods for Django views.

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
        user_memberships = SchoolMembership.objects.filter(user=self.request.user, is_active=True).values_list(
            "school_id", flat=True
        )

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


class IsParentInAnySchoolMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check if user is a parent in any school.
    """

    permission_denied_message = "You must be a parent to perform this action."

    def test_func(self):
        if not SchoolMembership.objects.filter(
            user=self.request.user, role="parent", is_active=True
        ).exists():
            return False

        # Check object-level permission if we have get_object method
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            # If object has a school attribute, check if user is a parent in that school
            if hasattr(obj, "school"):
                return SchoolMembership.objects.filter(
                    user=self.request.user, school=obj.school, role="parent", is_active=True
                ).exists()
            # If object is linked to a user, check if that user is the requester
            elif hasattr(obj, "user"):
                return obj.user == self.request.user
        return True  # For list views, basic parent permission is sufficient


class IsParentOfStudentMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check if user is a parent of the student in question.
    Used for parent-child relationship access control.
    """

    permission_denied_message = "You must be the parent of this student to perform this action."

    def test_func(self):
        # Check object-level permission if we have get_object method
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            return self.check_parent_child_relationship(obj)
        return True  # For list views, allow authenticated users

    def check_parent_child_relationship(self, obj):
        """Check if user is parent of the student related to this object"""
        from .models import ParentChildRelationship

        # If the object has a student attribute, check parent-child relationship
        if hasattr(obj, "student"):
            return ParentChildRelationship.objects.filter(
                parent=self.request.user, child=obj.student, is_active=True
            ).exists()

        # If the object has a child attribute, check parent-child relationship
        if hasattr(obj, "child"):
            return ParentChildRelationship.objects.filter(
                parent=self.request.user, child=obj.child, is_active=True
            ).exists()

        # If the object IS a parent-child relationship, check if user is the parent
        if hasattr(obj, "parent") and hasattr(obj, "child"):
            return obj.parent == self.request.user

        # If object is linked to a user, check if that user is the requester
        if hasattr(obj, "user"):
            return obj.user == self.request.user

        return False


class IsStudentOrParentMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that allows access to students themselves or their parents.
    Used for purchase-related endpoints where both student and parent need access.
    """

    permission_denied_message = "You must be this student or their parent to perform this action."

    def test_func(self):
        # Check object-level permission if we have get_object method
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            return self.check_student_or_parent_permission(obj)
        return True  # For list views, allow authenticated users

    def check_student_or_parent_permission(self, obj):
        """Check if user is the student or their parent"""
        from .models import ParentChildRelationship

        # If the object has a student attribute
        if hasattr(obj, "student"):
            # Allow if user is the student
            if obj.student == self.request.user:
                return True

            # Allow if user is a parent of the student
            return ParentChildRelationship.objects.filter(
                parent=self.request.user, child=obj.student, is_active=True
            ).exists()

        # If object is linked to a user, check if that user is the requester
        if hasattr(obj, "user"):
            if obj.user == self.request.user:
                return True

            # Check if user is a parent of the user
            return ParentChildRelationship.objects.filter(
                parent=self.request.user, child=obj.user, is_active=True
            ).exists()

        return False


class CanManageChildPurchasesMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin for parents to manage their children's purchases and approval requests.
    """

    permission_denied_message = "You must be authorized to manage this child's purchases."

    def test_func(self):
        # Check object-level permission if we have get_object method
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            return self.check_child_purchase_permission(obj)
        return True  # For list views, allow authenticated users

    def check_child_purchase_permission(self, obj):
        """Check if user can manage this child's purchases"""
        from .models import ParentChildRelationship

        # For purchase approval requests
        if hasattr(obj, "parent") and hasattr(obj, "student"):
            return obj.parent == self.request.user

        # For budget controls
        if hasattr(obj, "parent_child_relationship"):
            return obj.parent_child_relationship.parent == self.request.user

        # For purchase transactions involving children
        if hasattr(obj, "student"):
            return ParentChildRelationship.objects.filter(
                parent=self.request.user, child=obj.student, is_active=True
            ).exists()

        return False


class IsParentWithChildrenMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check if user is a parent with active children relationships.
    Used for parent dashboard and child management features.
    """

    permission_denied_message = "You must be a parent with active children to perform this action."

    def test_func(self):
        from .models import ParentChildRelationship

        # Check if user has any active parent-child relationships
        if not ParentChildRelationship.objects.filter(
            parent=self.request.user, is_active=True
        ).exists():
            return False

        # Check object-level permission if we have get_object method
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            return self.check_parent_with_children_permission(obj)
        return True  # For list views, basic parent permission is sufficient

    def check_parent_with_children_permission(self, obj):
        """Check if user is parent with permission for this object"""
        from .models import ParentChildRelationship

        # If object relates to a specific child, verify parent-child relationship
        if hasattr(obj, "child"):
            return ParentChildRelationship.objects.filter(
                parent=self.request.user, child=obj.child, is_active=True
            ).exists()

        # If object relates to a student, verify parent-child relationship
        if hasattr(obj, "student"):
            return ParentChildRelationship.objects.filter(
                parent=self.request.user, child=obj.student, is_active=True
            ).exists()

        # If object is linked to a user, check if that user is the requester
        if hasattr(obj, "user"):
            return obj.user == self.request.user

        return True  # User is a parent with children, allow general access
