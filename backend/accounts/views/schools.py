"""
School management views for the accounts app.

This module contains all views related to school management,
including school CRUD operations, settings, dashboard, memberships,
branding, and invitation links.
"""

import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from knox.auth import TokenAuthentication
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..db_queries import (
    can_user_manage_school,
    get_or_create_school_invitation_link,
    get_schools_user_can_manage,
    join_school_via_invitation_link,
    list_school_ids_owned_or_managed,
)
from ..models import (
    ActivityType,
    EducationalSystem,
    InvitationStatus,
    School,
    SchoolActivity,
    SchoolInvitation,
    SchoolInvitationLink,
    SchoolMembership,
    SchoolRole,
    SchoolSettings,
    TeacherInvitation,
)
from ..permissions import (
    IsSchoolOwnerOrAdmin,
)
from ..serializers import (
    ComprehensiveSchoolSettingsSerializer,
    EducationalSystemSerializer,
    EnhancedSchoolSerializer,
    SchoolActivitySerializer,
    SchoolMembershipSerializer,
    SchoolMetricsSerializer,
    SchoolProfileSerializer,
    SchoolSerializer,
    SchoolSettingsSerializer,
    SchoolWithMembersSerializer,
    TeacherSerializer,
)

logger = logging.getLogger(__name__)


class SchoolViewSet(viewsets.ModelViewSet):
    """
    API endpoint for schools.
    """

    serializer_class = SchoolSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter schools based on user permissions."""
        # System admins can see all schools
        if self.request.user.is_staff or self.request.user.is_superuser:
            return School.objects.all()

        # If user is not authenticated (since list/retrieve are AllowAny), show all schools
        if not self.request.user.is_authenticated:
            return School.objects.all()

        # Authenticated users see schools they're members of (any role)
        user_school_ids = SchoolMembership.objects.filter(user=self.request.user, is_active=True).values_list(
            "school_id", flat=True
        )

        return School.objects.filter(id__in=user_school_ids)

    def get_permissions(self):
        """Allow anyone to view schools, but only authorized users to modify."""
        permission_classes = [AllowAny] if self.action in ["list", "retrieve"] else [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        # Create the school
        school = serializer.save()

        # Create school membership for the creator as owner
        SchoolMembership.objects.create(
            user=self.request.user, school=school, role=SchoolRole.SCHOOL_OWNER, is_active=True
        )

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """Get all members of a school with their roles."""
        school = self.get_object()
        serializer = SchoolWithMembersSerializer(school)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def invitation_link(self, request, pk=None):
        """
        Get or create a generic invitation link for the school.
        This link can be shared to invite teachers without knowing their email.
        """
        school = self.get_object()

        # Check if user can manage this school
        if not can_user_manage_school(request.user, school.id):
            return Response(
                {"error": "You don't have permission to manage invitations for this school"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Get or create invitation link for teacher role
            invitation_link = get_or_create_school_invitation_link(
                school_id=school.id,
                role=SchoolRole.TEACHER,
                created_by=request.user,
                expires_days=365,  # Long-lived link (1 year)
            )

            # Build the full URL
            link_url = f"https://aprendecomigo.com/join-school/{invitation_link.token}"

            return Response(
                {
                    "invitation_link": {
                        "token": invitation_link.token,
                        "url": link_url,
                        "expires_at": invitation_link.expires_at,
                        "usage_count": invitation_link.usage_count,
                        "max_uses": invitation_link.max_uses,
                        "school": {
                            "id": school.id,
                            "name": school.name,
                        },
                        "role": invitation_link.role,
                        "role_display": invitation_link.get_role_display(),
                    }
                }
            )

        except Exception as e:
            logger.error(f"Failed to get invitation link for school {school.id}: {e}")
            return Response(
                {"error": "Failed to generate invitation link. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def join_via_link(self, request):
        """
        Join a school using a generic invitation link.
        This endpoint allows any authenticated user to join a school if they have the link.
        """
        token = request.data.get("token")
        if not token:
            return Response(
                {"error": "Invitation token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Extract teacher profile data from request
            teacher_data = {
                "bio": request.data.get("bio", ""),
                "specialty": request.data.get("specialty", ""),
                "course_ids": request.data.get("course_ids", []),
            }

            # Join the school
            teacher_profile, membership = join_school_via_invitation_link(
                token=token, user=request.user, teacher_data=teacher_data
            )

            # Serialize the response
            teacher_serializer = TeacherSerializer(teacher_profile)
            membership_serializer = SchoolMembershipSerializer(membership)

            return Response(
                {
                    "message": "Successfully joined the school as a teacher!",
                    "teacher": teacher_serializer.data,
                    "school_membership": membership_serializer.data,
                    "courses_added": len(teacher_data.get("course_ids", [])),
                    "school": {
                        "id": membership.school.id,
                        "name": membership.school.name,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Failed to join school via link {token}: {e}")
            return Response(
                {"error": "Failed to join school. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["get", "patch"],
        url_path="settings",
        permission_classes=[IsAuthenticated, IsSchoolOwnerOrAdmin],
    )
    def school_settings(self, request, pk=None):
        """Get or update comprehensive school settings"""
        school = self.get_object()

        if request.method == "GET":
            # Get or create school settings
            settings_obj, created = SchoolSettings.objects.get_or_create(
                school=school,
                defaults={
                    "educational_system_id": 1,  # Default to Portugal system
                    "working_days": [0, 1, 2, 3, 4],  # Monday to Friday
                },
            )

            # Use comprehensive serializer that includes both profile and settings
            serializer = ComprehensiveSchoolSettingsSerializer(settings_obj, context={"request": request})

            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == "PATCH":
            # Update school settings with comprehensive validation
            # Get or create school settings
            settings_obj, created = SchoolSettings.objects.get_or_create(
                school=school,
                defaults={
                    "educational_system_id": 1,
                    "working_days": [0, 1, 2, 3, 4],
                },
            )

            # Store old values for activity logging
            old_values = {}
            changed_fields = []

            # Process school profile updates if present
            if "school_profile" in request.data:
                profile_data = request.data["school_profile"]
                school_serializer = SchoolProfileSerializer(
                    school, data=profile_data, partial=True, context={"request": request}
                )

                if school_serializer.is_valid(raise_exception=True):
                    # Store old school values for logging
                    for field in profile_data:
                        if hasattr(school, field):
                            old_values[f"school.{field}"] = getattr(school, field)

                    school_serializer.save()
                    changed_fields.extend([f"school.{field}" for field in profile_data])

            # Process settings updates
            settings_data = request.data.get("settings", request.data)
            if settings_data:
                # Store old settings values for logging
                for field in settings_data:
                    if hasattr(settings_obj, field):
                        old_values[f"settings.{field}"] = getattr(settings_obj, field)

                settings_serializer = SchoolSettingsSerializer(
                    settings_obj, data=settings_data, partial=True, context={"request": request}
                )

                if settings_serializer.is_valid(raise_exception=True):
                    settings_serializer.save()
                    changed_fields.extend([f"settings.{field}" for field in settings_data])

            # Create activity log for settings update
            if changed_fields:
                from ..services.metrics_service import SchoolActivityService

                changes_description = []
                for field in changed_fields:
                    if field in old_values:
                        old_value = old_values[field]
                        new_value = getattr(
                            school if field.startswith("school.") else settings_obj, field.split(".", 1)[1]
                        )
                        if old_value != new_value:
                            changes_description.append(f"{field}: '{old_value}' → '{new_value}'")

                if changes_description:
                    SchoolActivityService.create_activity(
                        school=school,
                        activity_type=ActivityType.SETTINGS_UPDATED,
                        actor=request.user,
                        description=f"Updated school settings: {', '.join(changes_description)}",
                        metadata={"changed_fields": changed_fields},
                    )

            # Invalidate metrics cache
            from ..services.metrics_service import SchoolMetricsService

            SchoolMetricsService.invalidate_cache(school.id)

            # Return updated settings
            serializer = ComprehensiveSchoolSettingsSerializer(settings_obj, context={"request": request})

            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path="settings/educational-systems",
        permission_classes=[IsAuthenticated, IsSchoolOwnerOrAdmin],
    )
    def educational_systems(self, request, pk=None):
        """Get available educational systems for school configuration"""
        systems = EducationalSystem.objects.filter(is_active=True)
        serializer = EducationalSystemSerializer(systems, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=["get"], url_path="metrics", permission_classes=[IsAuthenticated, IsSchoolOwnerOrAdmin]
    )
    def metrics(self, request, pk=None):
        """Get comprehensive metrics for school dashboard"""
        school = self.get_object()

        # Check if user can manage this school
        if not can_user_manage_school(request.user, school.id):
            return Response(
                {"error": "You don't have permission to view metrics for this school"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Import here to avoid circular imports
        from ..services.metrics_service import SchoolMetricsService

        metrics_service = SchoolMetricsService(school)
        metrics_data = metrics_service.get_metrics()

        serializer = SchoolMetricsSerializer(data=metrics_data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=["get"], url_path="activity", permission_classes=[IsAuthenticated, IsSchoolOwnerOrAdmin]
    )
    def activity(self, request, pk=None):
        """Get paginated activity feed for school"""
        school = self.get_object()

        # Check if user can manage this school
        if not can_user_manage_school(request.user, school.id):
            return Response(
                {"error": "You don't have permission to view activity for this school"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Import here to avoid circular imports
        from django.core.paginator import EmptyPage, Paginator

        from ..services.metrics_service import SchoolActivityService

        # Get query parameters for filtering
        activity_types = request.query_params.get("activity_types")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        # Safely parse pagination parameters with validation
        try:
            page = int(request.query_params.get("page", 1))
            page_size = min(int(request.query_params.get("page_size", 20)), 100)  # Max 100 items per page
        except (ValueError, TypeError):
            page = 1
            page_size = 20

        # Build filters
        filters = {}
        if activity_types:
            filters["activity_types"] = activity_types
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to

        try:
            # Get activities using the service
            activities_queryset = SchoolActivityService.get_activity_feed(
                school=school,
                page_size=None,  # Get all, we'll paginate manually
                filters=filters,
            )

            # Set up pagination
            paginator = Paginator(activities_queryset, page_size)

            try:
                activities_page = paginator.page(page)
            except EmptyPage:
                activities_page = paginator.page(paginator.num_pages) if paginator.num_pages > 0 else paginator.page(1)

            # Serialize the activities
            serializer = SchoolActivitySerializer(activities_page.object_list, many=True, context={"request": request})

            # Build pagination response
            response_data = {"count": paginator.count, "next": None, "previous": None, "results": serializer.data}

            # Add next/previous page URLs if they exist
            if activities_page.has_next():
                next_page = activities_page.next_page_number()
                response_data["next"] = request.build_absolute_uri(request.path + f"?page={next_page}")
                # Preserve filter parameters
                for key, value in request.query_params.items():
                    if key != "page":
                        response_data["next"] += f"&{key}={value}"

            if activities_page.has_previous():
                prev_page = activities_page.previous_page_number()
                response_data["previous"] = request.build_absolute_uri(request.path + f"?page={prev_page}")
                # Preserve filter parameters
                for key, value in request.query_params.items():
                    if key != "page":
                        response_data["previous"] += f"&{key}={value}"

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to get activity feed for school {school.id}: {e}")
            return Response(
                {"error": "Failed to retrieve activity feed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SchoolMembershipViewSet(viewsets.ModelViewSet):
    """
    API endpoint for school memberships.
    """

    serializer_class = SchoolMembershipSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # System admins can see all memberships
        if user.is_staff or user.is_superuser:
            return SchoolMembership.objects.all()

        # School owners and admins can see memberships in their schools
        admin_school_ids = list_school_ids_owned_or_managed(user)

        if admin_school_ids:
            return SchoolMembership.objects.filter(school_id__in=admin_school_ids)

        # Other users can only see their own memberships
        return SchoolMembership.objects.filter(user=user)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Only school owner/admin can manage memberships
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            # For list, retrieve, etc.
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class SchoolDashboardViewSet(viewsets.ModelViewSet):
    """ViewSet for school dashboard functionality"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    serializer_class = EnhancedSchoolSerializer

    def get_queryset(self):
        """Return schools that user can manage"""
        user_schools = get_schools_user_can_manage(self.request.user)
        return School.objects.filter(id__in=user_schools).select_related("settings")

    @action(detail=True, methods=["get"], url_path="metrics")
    def metrics(self, request, pk=None):
        """Get comprehensive metrics for school dashboard"""
        school = self.get_object()

        # Import here to avoid circular imports
        from ..services.metrics_service import SchoolMetricsService

        metrics_service = SchoolMetricsService(school)
        metrics_data = metrics_service.get_metrics()

        serializer = SchoolMetricsSerializer(data=metrics_data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="activity")
    def activity(self, request, pk=None):
        """Get paginated activity feed for school"""
        school = self.get_object()

        # Import here to avoid circular imports
        from django.core.paginator import EmptyPage, Paginator

        # Get query parameters for filtering
        activity_types = request.query_params.get("activity_types")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        # Safely parse pagination parameters with validation
        try:
            page = int(request.query_params.get("page", 1))
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid page parameter. Must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            page_size = int(request.query_params.get("page_size", 20))
            if page_size < 1:
                page_size = 20
            elif page_size > 100:
                page_size = 100
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid page_size parameter. Must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build filters
        filters = {}
        if activity_types:
            filters["activity_types"] = activity_types
        if date_from:
            try:
                from django.utils.dateparse import parse_datetime

                filters["date_from"] = parse_datetime(date_from)
            except (ValueError, TypeError):
                pass
        if date_to:
            try:
                from django.utils.dateparse import parse_datetime

                filters["date_to"] = parse_datetime(date_to)
            except (ValueError, TypeError):
                pass

        # Get activities
        activities = (
            SchoolActivity.objects.filter(school=school)
            .select_related("actor", "target_user", "target_class__teacher")
            .prefetch_related("target_invitation__invited_by")
        )

        # Apply filters
        if filters.get("activity_types"):
            activity_types_list = filters["activity_types"].split(",")
            activities = activities.filter(activity_type__in=activity_types_list)

        if filters.get("date_from"):
            activities = activities.filter(timestamp__gte=filters["date_from"])

        if filters.get("date_to"):
            activities = activities.filter(timestamp__lte=filters["date_to"])

        # Paginate
        paginator = Paginator(activities, page_size)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # Serialize
        serializer = SchoolActivitySerializer(
            page_obj.object_list, many=True, context={"school": school, "request": request}
        )

        # Build pagination response
        response_data = {
            "count": paginator.count,
            "next": f"?page={page_obj.next_page_number()}" if page_obj.has_next() else None,
            "previous": f"?page={page_obj.previous_page_number()}" if page_obj.has_previous() else None,
            "results": serializer.data,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class SchoolInvitationLinkView(APIView):
    """
    API endpoint for viewing generic school invitation link details.
    This is a public endpoint (no auth required) for sharing links.
    """

    permission_classes = [AllowAny]

    def get(self, request, token):
        """
        Get invitation link details without joining.
        Useful for showing invitation info on the frontend before the user decides to join.
        """
        try:
            invitation_link = SchoolInvitationLink.objects.select_related("school").get(token=token)
        except SchoolInvitationLink.DoesNotExist:
            return Response(
                {"error": "Invalid invitation link"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if invitation link is valid
        if not invitation_link.is_valid():
            return Response(
                {"error": "This invitation link has expired or is no longer active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Return invitation link details
        return Response(
            {
                "invitation": {
                    "school": {
                        "id": invitation_link.school.id,
                        "name": invitation_link.school.name,
                        "description": invitation_link.school.description,
                    },
                    "role": invitation_link.role,
                    "role_display": invitation_link.get_role_display(),
                    "expires_at": invitation_link.expires_at,
                    "usage_count": invitation_link.usage_count,
                    "max_uses": invitation_link.max_uses,
                },
                "requires_authentication": not request.user.is_authenticated,
                "user_already_member": False,  # Will be updated below if user is authenticated
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def decline(self, request, token=None):
        """
        Decline a school invitation
        """

        # Get the invitation
        try:
            invitation = SchoolInvitation.objects.get(token=token)
        except SchoolInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid invitation token"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate invitation
        if not invitation.is_valid():
            if invitation.is_accepted:
                return Response(
                    {"error": "This invitation has already been accepted"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {"error": "This invitation has expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Check if the user is authenticated and verify they are the intended recipient
        if request.user.is_authenticated and invitation.email != request.user.email:
            return Response(
                {"error": "This invitation is not for your account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            with transaction.atomic():
                # Mark invitation as declined (for both SchoolInvitation models)
                invitation.is_accepted = False  # Keep as False but we'll track status differently
                invitation.save()

                # If this is actually a TeacherInvitation, update its status too
                try:
                    teacher_invitation = TeacherInvitation.objects.get(token=token)
                    teacher_invitation.status = InvitationStatus.DECLINED
                    teacher_invitation.save()
                except TeacherInvitation.DoesNotExist:
                    pass  # Not a teacher invitation

                # Log the activity
                SchoolActivity.objects.create(
                    school=invitation.school,
                    activity_type=ActivityType.INVITATION_DECLINED,
                    actor=request.user if request.user.is_authenticated else None,
                    target_invitation=invitation,
                    description=f"Invitation to {invitation.email} was declined",
                )

                return Response(
                    {
                        "message": "Invitation declined successfully",
                        "invitation": {
                            "token": invitation.token,
                            "email": invitation.email,
                            "school": {
                                "id": invitation.school.id,
                                "name": invitation.school.name,
                            },
                            "status": "declined",
                        },
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            logger.error(f"Decline invitation failed for token {token}: {e!s}")
            return Response(
                {"error": "Failed to decline invitation. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SchoolBrandingAPIView(APIView):
    """
    API for managing school branding settings for email templates.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]

    def get(self, request, *args, **kwargs):
        """Get school branding settings."""
        # Get user's primary school
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({"error": "No managed schools found"}, status=status.HTTP_404_NOT_FOUND)

        school = School.objects.get(id=school_ids[0])

        return Response(
            {
                "school_id": school.id,
                "school_name": school.name,
                "primary_color": school.primary_color,
                "secondary_color": school.secondary_color,
                "logo_url": school.logo.url if school.logo else None,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, *args, **kwargs):
        """Update school branding settings."""
        from ..serializers import SchoolBrandingSerializer

        # Get user's primary school
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({"error": "No managed schools found"}, status=status.HTTP_404_NOT_FOUND)

        school = School.objects.get(id=school_ids[0])

        serializer = SchoolBrandingSerializer(school, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommunicationSettingsAPIView(APIView):
    """
    API for managing communication settings and preferences.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]

    def get(self, request, *args, **kwargs):
        """Get communication settings for user's school."""
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({"error": "No managed schools found"}, status=status.HTTP_404_NOT_FOUND)

        school = School.objects.get(id=school_ids[0])

        # Get or create school settings
        settings, created = SchoolSettings.objects.get_or_create(
            school=school,
            defaults={
                "communication_settings": {
                    "default_from_email": school.contact_email,
                    "email_signature": f"Best regards,\n{school.name} Team",
                    "auto_sequence_enabled": True,
                    "notification_preferences": {"email_delivery_notifications": True, "bounce_notifications": True},
                }
            },
        )

        comm_settings = getattr(settings, "communication_settings", {}) or {}

        return Response(
            {
                "default_from_email": comm_settings.get("default_from_email", school.contact_email),
                "email_signature": comm_settings.get("email_signature", f"Best regards,\n{school.name} Team"),
                "auto_sequence_enabled": comm_settings.get("auto_sequence_enabled", True),
                "notification_preferences": comm_settings.get(
                    "notification_preferences", {"email_delivery_notifications": True, "bounce_notifications": True}
                ),
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, *args, **kwargs):
        """Update communication settings."""
        from django.core.validators import validate_email

        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({"error": "No managed schools found"}, status=status.HTTP_404_NOT_FOUND)

        school = School.objects.get(id=school_ids[0])

        # Validate email if provided
        default_from_email = request.data.get("default_from_email")
        if default_from_email:
            try:
                validate_email(default_from_email)
            except ValidationError:
                return Response({"error": "Invalid default_from_email format"}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create school settings
        settings, created = SchoolSettings.objects.get_or_create(school=school, defaults={"communication_settings": {}})

        # Update communication settings
        comm_settings = getattr(settings, "communication_settings", {}) or {}

        if "default_from_email" in request.data:
            comm_settings["default_from_email"] = request.data["default_from_email"]

        if "email_signature" in request.data:
            comm_settings["email_signature"] = request.data["email_signature"]

        if "auto_sequence_enabled" in request.data:
            comm_settings["auto_sequence_enabled"] = request.data["auto_sequence_enabled"]

        if "notification_preferences" in request.data:
            comm_settings["notification_preferences"] = request.data["notification_preferences"]

        settings.communication_settings = comm_settings
        settings.save()

        return Response(
            {"message": "Communication settings updated successfully", "settings": comm_settings},
            status=status.HTTP_200_OK,
        )
