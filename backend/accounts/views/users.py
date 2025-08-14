"""
User management views for the accounts app.

This module contains views for user management, including user CRUD operations,
parent profiles, parent-child relationships, and user onboarding.
"""

import logging
from typing import ClassVar

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.messaging import send_email_verification_code
from common.throttles import EmailCodeRequestThrottle, IPSignupThrottle

from ..db_queries import (
    create_school_owner,
    list_school_ids_owned_or_managed,
    list_users_by_request_permissions,
    user_exists,
)
from ..models import (
    ParentChildRelationship,
    ParentProfile,
    School,
    SchoolMembership,
    SchoolRole,
    VerificationCode,
)
from ..permissions import IsOwnerOrSchoolAdmin, IsSchoolOwnerOrAdmin
from ..serializers import (
    CreateUserSerializer,
    ParentChildRelationshipSerializer,
    ParentProfileSerializer,
    UserSerializer,
)
from .auth import KnoxAuthenticatedViewSet

logger = logging.getLogger(__name__)


class UserViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for users.
    """

    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        return list_users_by_request_permissions(user)

    def get_permissions(self):
        if self.action == "create":
            # Only school owners/admins and system admins can create users
            permission_classes: ClassVar = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        elif self.action == "signup":
            # Anyone can sign up
            permission_classes: ClassVar = [AllowAny]
        elif self.action == "list":
            # Any authenticated user can list, but queryset is filtered appropriately
            permission_classes: ClassVar = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only owner or school admin can modify user records
            permission_classes: ClassVar = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        elif self.action in ["retrieve", "school_profile", "dashboard_info"]:
            # Any authenticated user can retrieve, but queryset is filtered appropriately
            permission_classes: ClassVar = [IsAuthenticated]
        else:
            permission_classes: ClassVar = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def dashboard_info(self, request):
        """
        Get dashboard information for the current user
        """
        user = request.user

        # This method should only be called for authenticated users
        # If this is reached with AnonymousUser, it's a misconfiguration
        if not user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Basic user info
        user_info = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "date_joined": user.date_joined,
            "first_login_completed": user.first_login_completed,
        }

        # Get user's roles in schools
        memberships = SchoolMembership.objects.filter(user=user, is_active=True)

        user_info["roles"] = [
            {
                "school": {"id": m.school.id, "name": m.school.name},
                "role": m.role,
                "role_display": m.get_role_display(),
            }
            for m in memberships
        ]

        # Determine primary user_type based on roles
        user_type = None
        is_admin = False

        # Check if user is a school owner or admin in any school
        admin_school_ids = list_school_ids_owned_or_managed(user)
        if len(admin_school_ids) > 0:
            user_type = "admin"
            is_admin = True
        # Check if user is a teacher in any school
        elif SchoolMembership.objects.filter(user=user, role=SchoolRole.TEACHER, is_active=True).exists():
            user_type = "teacher"
        # Check if user is a student in any school
        elif SchoolMembership.objects.filter(user=user, role=SchoolRole.STUDENT, is_active=True).exists():
            user_type = "student"
        else:
            user_type = "student"  # Default fallback

        user_info["user_type"] = user_type
        user_info["is_admin"] = is_admin

        # Stats based on primary role
        stats = {}

        # If user is a school owner or admin in any school
        if len(admin_school_ids) > 0:
            # Admin stats
            stats = {
                "schools_count": len(admin_school_ids),
                "student_count": SchoolMembership.objects.filter(
                    school_id__in=admin_school_ids,
                    role=SchoolRole.STUDENT,
                    is_active=True,
                ).count(),
                "teacher_count": SchoolMembership.objects.filter(
                    school_id__in=admin_school_ids,
                    role=SchoolRole.TEACHER,
                    is_active=True,
                ).count(),
            }

        # If user is a teacher in any school
        elif SchoolMembership.objects.filter(user=user, role=SchoolRole.TEACHER, is_active=True).exists():
            # Teacher stats
            stats = {
                "today_classes": 0,  # Would need to calculate from scheduling models
                "week_classes": 0,
                "student_count": 0,
                "monthly_earnings": 0,
            }

            # Check if teacher needs profile
            needs_onboarding = not hasattr(user, "teacher_profile") or user.teacher_profile is None
            user_info["needs_onboarding"] = needs_onboarding

            # Include calendar if available
            if hasattr(user, "teacher_profile") and user.teacher_profile:
                user_info["calendar_iframe"] = user.teacher_profile.calendar_iframe

        # If user is a student in any school
        elif SchoolMembership.objects.filter(user=user, role=SchoolRole.STUDENT, is_active=True).exists():
            # Student stats
            stats = {
                "upcoming_classes": 0,
                "completed_classes": 0,
                "balance": "$0",
            }

            # Check if student needs onboarding
            needs_onboarding = not hasattr(user, "student_profile") or user.student_profile is None
            user_info["needs_onboarding"] = needs_onboarding

            # Include calendar if available
            if hasattr(user, "student_profile") and user.student_profile:
                user_info["calendar_iframe"] = user.student_profile.calendar_iframe

        return Response({"user_info": user_info, "stats": stats})

    @action(detail=False, methods=["post"])
    def complete_first_login(self, request):
        """
        Mark the user's first login as completed
        """
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user.first_login_completed = True
        user.save()

        return Response({"message": "First login marked as completed"})

    @action(detail=False, methods=["get"])
    def school_profile(self, request):
        """
        Get school profile information for a specific school
        """
        school_id = request.query_params.get("school_id")

        if not school_id:
            return Response({"error": "School ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            school = School.objects.get(id=school_id)
        except School.DoesNotExist:
            return Response({"error": "School not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if user has access to this school
        if not (
            request.user.is_superuser
            or request.user.is_staff
            or SchoolMembership.objects.filter(user=request.user, school=school, is_active=True).exists()
        ):
            return Response(
                {"error": "You don't have access to this school"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # School statistics
        stats = {
            "students": SchoolMembership.objects.filter(school=school, role=SchoolRole.STUDENT, is_active=True).count(),
            "teachers": SchoolMembership.objects.filter(school=school, role=SchoolRole.TEACHER, is_active=True).count(),
            "classes": 0,  # Would need to calculate from scheduling models
            "class_types": 0,
        }

        # School information
        school_info = {
            "id": school.id,
            "name": school.name,
            "description": school.description,
            "address": school.address,
            "contact_email": school.contact_email,
            "phone_number": school.phone_number,
            "website": school.website,
            "created_at": school.created_at,
        }

        return Response({"stats": stats, "school_info": school_info})

    @action(detail=False, methods=["post"])
    def verify_contact(self, request):
        """
        Verify a contact method (email or phone) using a verification code
        """
        contact_type = request.data.get("contact_type")
        code = request.data.get("code")

        if not contact_type or contact_type not in ["email", "phone"]:
            return Response(
                {"error": "Invalid contact type. Must be 'email' or 'phone'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not code:
            return Response(
                {"error": "Verification code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        contact_value = getattr(user, "email" if contact_type == "email" else "phone_number")

        # Check for verification code
        try:
            if contact_type == "email":
                verification = VerificationCode.objects.filter(email=contact_value, is_used=False).latest("created_at")
            else:
                # For phone verification, we would need a similar model for phone codes
                # This example assumes we're using the same model for simplicity
                verification = VerificationCode.objects.filter(email=contact_value, is_used=False).latest("created_at")
        except VerificationCode.DoesNotExist:
            return Response(
                {"error": f"No verification code found for this {contact_type}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the code
        if not verification.is_valid(code):
            return Response(
                {"error": "Invalid or expired verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark verification as used
        verification.use()

        # Update user's verification status
        setattr(user, f"{contact_type}_verified", True)
        user.save()

        return Response(
            {
                "message": f"Your {contact_type} has been verified successfully.",
                "user": UserSerializer(user).data,
            }
        )

    @action(detail=False, methods=["post"])
    def set_primary_contact(self, request):
        """
        Update the user's primary contact method
        """
        primary_contact = request.data.get("primary_contact")

        if not primary_contact or primary_contact not in ["email", "phone"]:
            return Response(
                {"error": "Invalid contact type. Must be 'email' or 'phone'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        # Ensure the selected contact is verified
        if primary_contact == "email" and not user.email_verified:
            return Response(
                {"error": "Email must be verified before setting it as primary contact."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif primary_contact == "phone" and not user.phone_verified:
            return Response(
                {"error": "Phone number must be verified before setting it as primary contact."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update primary contact
        user.primary_contact = primary_contact
        user.save()

        return Response(
            {
                "message": f"Your primary contact has been updated to {primary_contact}.",
                "user": UserSerializer(user).data,
            }
        )

    @action(
        detail=False,
        methods=["post"],
        throttle_classes=[EmailCodeRequestThrottle, IPSignupThrottle],
    )
    def signup(self, request):
        """
        Sign up as a new user without requiring authentication.

        This handles the first step of the onboarding process where a user
        fills out the form with their information and selects a primary contact.
        """
        serializer = CreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        email = validated_data.get("email")
        phone_number = validated_data.get("phone_number")
        name = validated_data.get("name")
        primary_contact = validated_data.get("primary_contact")
        user_type = validated_data.get("user_type")  # Explicit user type from frontend
        school_data = validated_data.get("school", {})

        # Check if user already exists
        if user_exists(email):
            return Response(
                {"error": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use explicit user type instead of vulnerable pattern matching
        is_tutor = user_type == "tutor"

        # Wrap all database operations in a transaction for rollback protection
        try:
            with transaction.atomic():
                user, school = create_school_owner(
                    email, name, phone_number, primary_contact, school_data, is_tutor=is_tutor
                )

                # Generate verification code for primary contact
                if primary_contact == "email":
                    verification = VerificationCode.generate_code(email)
                    contact_value = email
                else:
                    # For phone verification, in a real system we'd use a different
                    # mechanism like SMS, but for this example we'll use email
                    verification = VerificationCode.generate_code(phone_number)
                    contact_value = phone_number

                code = verification.get_current_code()

                # Send verification code (if this fails, transaction will rollback)
                contact_type_display = "email" if primary_contact == "email" else "phone number"
                try:
                    send_email_verification_code(contact_value, code)
                except Exception as e:
                    # This will cause the transaction to rollback automatically
                    raise Exception(f"Failed to send verification code: {e!s}")

        except Exception as e:
            # Transaction automatically rolled back, return error
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": f"User created successfully. Verification code sent to your {contact_type_display}.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "phone_number": user.phone_number,
                    "primary_contact": user.primary_contact,
                },
                "school": {"id": school.id, "name": school.name},
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get", "post"])
    def onboarding_progress(self, request):
        """
        GET/POST /api/accounts/onboarding-progress/

        GET: Returns current user's onboarding progress
        POST: Updates user's onboarding progress
        """
        user = request.user

        if request.method == "GET":
            # Return current onboarding progress
            progress_data = user.onboarding_progress or {}

            response_data = {
                "steps_completed": progress_data.get("steps_completed", []),
                "current_step": progress_data.get("current_step", "profile"),
                "completion_percentage": progress_data.get("completion_percentage", 0),
                "skipped": progress_data.get("skipped", False),
                "completed_at": progress_data.get("completed_at"),
                "onboarding_completed": user.onboarding_completed,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        elif request.method == "POST":
            # Validate input data
            steps_completed = request.data.get("steps_completed")
            current_step = request.data.get("current_step")
            completion_percentage = request.data.get("completion_percentage")
            skipped = request.data.get("skipped", False)

            # Validation
            if not isinstance(steps_completed, list):
                return Response({"error": "steps_completed must be a list"}, status=status.HTTP_400_BAD_REQUEST)

            if not current_step:
                return Response({"error": "current_step is required"}, status=status.HTTP_400_BAD_REQUEST)

            if completion_percentage is None:
                return Response({"error": "completion_percentage is required"}, status=status.HTTP_400_BAD_REQUEST)

            if not (0 <= completion_percentage <= 100):
                return Response(
                    {"error": "completion_percentage must be between 0 and 100"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Update user's onboarding progress
            progress_data = {
                "steps_completed": steps_completed,
                "current_step": current_step,
                "completion_percentage": completion_percentage,
                "skipped": skipped,
            }

            # Mark as completed if percentage is 100 or current_step is "completed"
            if completion_percentage == 100 or current_step == "completed":
                user.onboarding_completed = True
                progress_data["completed_at"] = timezone.now().isoformat()

            user.onboarding_progress = progress_data
            user.save(update_fields=["onboarding_progress", "onboarding_completed"])

            # Return updated progress
            response_data = {
                "steps_completed": steps_completed,
                "current_step": current_step,
                "completion_percentage": completion_percentage,
                "skipped": skipped,
                "completed_at": progress_data.get("completed_at"),
                "onboarding_completed": user.onboarding_completed,
            }

            return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get", "post"])
    def navigation_preferences(self, request):
        """
        GET/POST /api/accounts/navigation-preferences/

        GET: Returns current user's navigation preferences
        POST: Updates user's navigation preferences
        """
        user = request.user

        if request.method == "GET":
            # Return current navigation preferences
            preferences = user.tutorial_preferences or {}

            return Response(preferences, status=status.HTTP_200_OK)

        elif request.method == "POST":
            # Validate and update navigation preferences
            current_preferences = user.tutorial_preferences or {}

            # Define valid values for specific fields
            valid_landing_pages = ["dashboard", "students", "teachers", "reports", "billing"]
            valid_navigation_styles = ["sidebar", "top_nav", "compact"]

            update_data = request.data

            # Validation
            if "quick_actions" in update_data and not isinstance(update_data["quick_actions"], list):
                return Response({"error": "quick_actions must be a list"}, status=status.HTTP_400_BAD_REQUEST)

            if "default_landing_page" in update_data and update_data["default_landing_page"] not in valid_landing_pages:
                return Response(
                    {"error": f"default_landing_page must be one of: {', '.join(valid_landing_pages)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "navigation_style" in update_data and update_data["navigation_style"] not in valid_navigation_styles:
                return Response(
                    {"error": f"navigation_style must be one of: {', '.join(valid_navigation_styles)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "tutorial_auto_start" in update_data and not isinstance(update_data["tutorial_auto_start"], bool):
                return Response({"error": "tutorial_auto_start must be a boolean"}, status=status.HTTP_400_BAD_REQUEST)

            # Update preferences (merge with existing)
            current_preferences.update(update_data)

            user.tutorial_preferences = current_preferences
            user.save(update_fields=["tutorial_preferences"])

            # Return updated preferences
            return Response(current_preferences, status=status.HTTP_200_OK)


class ParentProfileViewSet(KnoxAuthenticatedViewSet):
    """
    ViewSet for managing parent profiles.
    Allows parents to manage their profile settings and preferences.
    """

    serializer_class = ParentProfileSerializer
    permission_classes: ClassVar = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's parent profile."""
        return ParentProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Ensure parent profile is created for the current user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["patch"])
    def update_notification_preferences(self, request, pk=None):
        """Update notification preferences for parent."""
        parent_profile = self.get_object()

        # Validate and update notification preferences
        notification_data = request.data.get("notification_preferences", {})

        # Update the preferences
        current_preferences = parent_profile.notification_preferences or {}
        current_preferences.update(notification_data)
        parent_profile.notification_preferences = current_preferences
        parent_profile.save(update_fields=["notification_preferences", "updated_at"])

        serializer = self.get_serializer(parent_profile)
        return Response(serializer.data)


class ParentChildRelationshipViewSet(KnoxAuthenticatedViewSet):
    """
    ViewSet for managing parent-child relationships.
    Allows parents to manage their children and school administrators to oversee relationships.
    """

    serializer_class = ParentChildRelationshipSerializer
    permission_classes: ClassVar = [IsAuthenticated]

    def get_queryset(self):
        """Filter relationships based on user role and permissions."""
        user = self.request.user

        # School administrators can see all relationships in their schools
        if user.school_memberships.filter(role__in=["school_owner", "school_admin"], is_active=True).exists():
            admin_school_ids = list(
                user.school_memberships.filter(role__in=["school_owner", "school_admin"], is_active=True).values_list(
                    "school_id", flat=True
                )
            )
            return ParentChildRelationship.objects.filter(school_id__in=admin_school_ids, is_active=True)

        # Parents can see their own relationships
        return ParentChildRelationship.objects.filter(parent=user, is_active=True)

    def perform_create(self, serializer):
        """Ensure relationships are created with proper validation."""
        # Additional validation could be added here
        serializer.save()

    @action(detail=True, methods=["patch"])
    def update_permissions(self, request, pk=None):
        """Update permissions for a specific parent-child relationship."""
        relationship = self.get_object()

        # Validate user can modify this relationship
        user = request.user
        if not (
            relationship.parent == user
            or user.school_memberships.filter(
                school=relationship.school, role__in=["school_owner", "school_admin"], is_active=True
            ).exists()
        ):
            return Response(
                {"error": "You don't have permission to modify this relationship"}, status=status.HTTP_403_FORBIDDEN
            )

        # Update permissions
        permissions_data = request.data.get("permissions", {})
        relationship.permissions = permissions_data

        # Update approval settings if provided
        if "requires_purchase_approval" in request.data:
            relationship.requires_purchase_approval = request.data["requires_purchase_approval"]

        if "requires_session_approval" in request.data:
            relationship.requires_session_approval = request.data["requires_session_approval"]

        relationship.save()

        serializer = self.get_serializer(relationship)
        return Response(serializer.data)
