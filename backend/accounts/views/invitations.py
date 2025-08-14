"""
Invitation management views for the accounts app.

This module contains all views related to invitation management,
including school invitations, teacher invitations, and invitation links.
"""

import logging

from django.db import models, transaction
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from knox.auth import TokenAuthentication
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..db_queries import (
    can_user_manage_school,
    list_school_ids_owned_or_managed,
)
from ..models import (
    EmailDeliveryStatus,
    InvitationStatus,
    SchoolInvitation,
    SchoolInvitationLink,
    SchoolMembership,
    TeacherInvitation,
    TeacherProfile,
)
from ..permissions import (
    IsSchoolOwnerOrAdmin,
)
from ..serializers import (
    AcceptInvitationSerializer,
    ComprehensiveTeacherProfileCreationSerializer,
    SchoolInvitationSerializer,
    SchoolMembershipSerializer,
    TeacherInvitationSerializer,
    TeacherSerializer,
)

logger = logging.getLogger(__name__)


class InvitationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing school invitations.
    """

    queryset = SchoolInvitation.objects.all()
    serializer_class = SchoolInvitationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "token"  # Use token instead of id for lookups

    def get_permissions(self):
        """
        Different permissions for different actions.
        """
        if self.action == "details":
            # Anyone can view invitation details (for sharing links)
            permission_classes = [AllowAny]
        else:
            # All other actions require authentication
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter invitations based on user permissions."""
        user = self.request.user

        # System admins can see all invitations
        if user.is_staff or user.is_superuser:
            return SchoolInvitation.objects.all()

        # Users can see invitations sent to them or sent by them
        return SchoolInvitation.objects.filter(models.Q(email=user.email) | models.Q(invited_by=user))

    @action(detail=True, methods=["post"])
    def accept(self, request, token=None):
        """
        Accept a school invitation and become a teacher.

        This endpoint allows a user to:
        1. Accept an invitation using the token
        2. Create their teacher profile with custom data
        3. Join the school as a teacher
        4. Associate with courses
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

        # Verify the current user is the intended recipient
        if invitation.email != request.user.email:
            return Response(
                {"error": "This invitation is not for your account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate the acceptance data
        serializer = AcceptInvitationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        try:
            with transaction.atomic():
                # Check if user already has a teacher profile
                if hasattr(request.user, "teacher_profile"):
                    teacher_profile = request.user.teacher_profile
                else:
                    # Create teacher profile with provided data
                    from ..models import TeacherCourse

                    profile_data = {key: value for key, value in validated_data.items() if key not in ["course_ids"]}
                    teacher_profile = TeacherProfile.objects.create(user=request.user, **profile_data)

                # Create school membership if it doesn't exist
                membership, created = SchoolMembership.objects.get_or_create(
                    user=request.user,
                    school=invitation.school,
                    role=invitation.role,
                    defaults={"is_active": True},
                )

                if not created and not membership.is_active:
                    # Reactivate if was previously inactive
                    membership.is_active = True
                    membership.save()

                # Associate courses if provided
                from ..models import TeacherCourse

                course_ids = validated_data.get("course_ids", [])
                teacher_courses = []
                if course_ids:
                    for course_id in course_ids:
                        teacher_course, course_created = TeacherCourse.objects.get_or_create(
                            teacher=teacher_profile,
                            course_id=course_id,
                            defaults={"is_active": True},
                        )
                        if course_created:
                            teacher_courses.append(teacher_course)

                # Mark invitation as accepted
                invitation.is_accepted = True
                invitation.save()

                # Return success response
                teacher_serializer = TeacherSerializer(teacher_profile)
                membership_serializer = SchoolMembershipSerializer(membership)

                return Response(
                    {
                        "message": "Invitation accepted successfully! You are now a teacher at this school.",
                        "teacher": teacher_serializer.data,
                        "school_membership": membership_serializer.data,
                        "courses_added": len(teacher_courses),
                        "school": {
                            "id": invitation.school.id,
                            "name": invitation.school.name,
                        },
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            logger.error(f"Accept invitation failed for token {token}: {e!s}")

            return Response(
                {"error": "Failed to accept invitation. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def details(self, request, token=None):
        """
        Get invitation details without accepting it.
        Useful for showing invitation info on the frontend before acceptance.
        """
        try:
            invitation = SchoolInvitation.objects.get(token=token)
        except SchoolInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid invitation token"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if invitation is valid
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

        # Check if user can accept this invitation
        can_accept = True
        reason = None

        if not request.user.is_authenticated:
            can_accept = False
            reason = "Authentication required"
        elif request.user.email != invitation.email:
            can_accept = False
            reason = "This invitation is not for your account"

        # Return invitation details in the format expected by frontend
        return Response(
            {
                "invitation": {
                    "id": str(invitation.id),
                    "email": invitation.email,
                    "school": {
                        "id": invitation.school.id,
                        "name": invitation.school.name,
                        "description": invitation.school.description,
                    },
                    "invited_by": {
                        "id": invitation.invited_by.id,
                        "name": invitation.invited_by.name,
                        "email": invitation.invited_by.email,
                    },
                    "role": invitation.role,
                    "status": "pending",  # SchoolInvitation doesn't have status field
                    "token": invitation.token,
                    "custom_message": getattr(invitation, "custom_message", None),
                    "created_at": invitation.created_at.isoformat(),
                    "expires_at": invitation.expires_at.isoformat(),
                    "is_accepted": invitation.is_accepted,
                    "invitation_link": f"https://aprendecomigo.com/accept-invitation/{invitation.token}",
                },
                "can_accept": can_accept,
                "reason": reason,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def resend(self, request, token=None):
        """
        Resend invitation notifications (email/SMS).
        """
        try:
            invitation = SchoolInvitation.objects.get(token=token)
        except SchoolInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid invitation token"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if user can manage this invitation
        if not can_user_manage_school(request.user, invitation.school.id):
            return Response(
                {"error": "You don't have permission to manage this invitation"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if invitation is still valid
        if not invitation.is_valid():
            return Response(
                {"error": "This invitation is no longer valid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        send_email = request.data.get("send_email", False)
        send_sms = request.data.get("send_sms", False)

        notifications_sent = {
            "email": False,
            "sms": False,
        }

        invitation_link = f"https://aprendecomigo.com/accept-invitation/{invitation.token}"

        # Send email if requested
        if send_email:
            try:
                from ..services.teacher_invitation_email_service import TeacherInvitationEmailService

                # For resending, we use the retry method if the invitation previously failed
                if invitation.email_delivery_status == EmailDeliveryStatus.FAILED:
                    email_result = TeacherInvitationEmailService.retry_failed_invitation_email(invitation)
                else:
                    email_result = TeacherInvitationEmailService.send_invitation_email(invitation)

                if email_result["success"]:
                    notifications_sent["email"] = True
                    if invitation.email_delivery_status != EmailDeliveryStatus.SENT:
                        invitation.mark_email_sent()
                    logger.info(f"Invitation email resent to {invitation.email}")
                else:
                    logger.warning(f"Failed to resend invitation email: {email_result.get('error', 'Unknown error')}")
                    invitation.mark_email_failed(email_result.get("error", "Unknown error"))

            except Exception as e:
                logger.warning(f"Failed to resend invitation email: {e}")
                invitation.mark_email_failed(f"Resend exception: {e!s}")

        # Send SMS if requested
        if send_sms:
            try:
                # TODO: Implement SMS sending
                # send_invitation_sms(invitation, invitation_link)
                notifications_sent["sms"] = True
            except Exception as e:
                logger.warning(f"Failed to resend invitation SMS: {e}")

        return Response(
            {
                "message": "Invitation notifications sent",
                "notifications_sent": notifications_sent,
                "invitation_link": invitation_link,
            }
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, token=None):
        """
        Cancel a pending invitation.
        """
        try:
            invitation = SchoolInvitation.objects.get(token=token)
        except SchoolInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid invitation token"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if user can manage this invitation
        if not can_user_manage_school(request.user, invitation.school.id):
            return Response(
                {"error": "You don't have permission to manage this invitation"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if invitation is already accepted
        if invitation.is_accepted:
            return Response(
                {"error": "Cannot cancel an already accepted invitation"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete the invitation
        invitation.delete()

        return Response({"message": "Invitation cancelled successfully"})

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

        # Check if the user is authenticated (optional for decline)
        if request.user.is_authenticated:
            # Verify the current user is the intended recipient
            if invitation.email != request.user.email:
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
                from ..models import ActivityType, SchoolActivity

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


class TeacherInvitationViewSet(viewsets.ModelViewSet):
    """
    Simplified API endpoints for teacher invitation management.
    Provides clean REST endpoints without WebSocket complexity.
    """

    queryset = TeacherInvitation.objects.all()
    serializer_class = TeacherInvitationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "token"  # Use token instead of id for lookups

    def get_queryset(self):
        """Filter invitations based on user permissions."""
        user = self.request.user

        # System admins can see all invitations
        if user.is_staff or user.is_superuser:
            return TeacherInvitation.objects.all()

        # Get schools where user is admin
        admin_school_ids = list_school_ids_owned_or_managed(user)

        if admin_school_ids:
            # School admins can see invitations for their schools
            return TeacherInvitation.objects.filter(school_id__in=admin_school_ids)

        # Users can see invitations sent to them
        return TeacherInvitation.objects.filter(email=user.email)

    def get_permissions(self):
        """Different permissions for different actions."""
        if self.action in ["accept", "decline", "status"]:
            # Anyone can check status, accept, or decline (with token validation)
            permission_classes = [AllowAny]
        elif self.action == "list":
            # Only admins can list invitations
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            # All other actions require authentication
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        method="post",
        operation_summary="Accept Teacher Invitation",
        operation_description="Accept a teacher invitation and create/update teacher profile",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "bio": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Teacher bio (max 1000 chars)", maxLength=1000
                ),
                "specialty": openapi.Schema(type=openapi.TYPE_STRING, description="Teaching specialty"),
                "hourly_rate": openapi.Schema(
                    type=openapi.TYPE_NUMBER, description="Hourly rate (5.00-200.00)", minimum=5.0, maximum=200.0
                ),
                "phone_number": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Phone number in international format"
                ),
                "address": openapi.Schema(type=openapi.TYPE_STRING, description="Physical address"),
                "teaching_subjects": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Array of teaching subjects (max 10)",
                ),
                "education_background": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Education background information",
                    properties={
                        "degree": openapi.Schema(type=openapi.TYPE_STRING),
                        "university": openapi.Schema(type=openapi.TYPE_STRING),
                        "graduation_year": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
                "teaching_experience": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Teaching experience details",
                    properties={
                        "years": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "description": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            },
            example={
                "bio": "Experienced mathematics teacher with passion for helping students",
                "specialty": "Mathematics, Physics",
                "hourly_rate": 45.00,
                "phone_number": "+1234567890",
                "teaching_subjects": ["Mathematics", "Physics"],
                "education_background": {"degree": "Masters in Mathematics", "university": "University Name"},
                "teaching_experience": {"years": 5, "description": "5 years teaching high school mathematics"},
            },
        ),
        responses={
            200: openapi.Response(
                description="Invitation accepted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "invitation_accepted": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "teacher_profile": openapi.Schema(type=openapi.TYPE_OBJECT),
                        "school_membership": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
            400: openapi.Response(
                description="Bad request - validation errors, invitation expired/accepted/declined",
            ),
            401: openapi.Response(
                description="Authentication required",
            ),
            403: openapi.Response(
                description="Forbidden - invitation not for authenticated user",
            ),
            404: openapi.Response(
                description="Invitation not found",
            ),
            500: openapi.Response(
                description="Internal server error",
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                "token", openapi.IN_PATH, description="Unique invitation token", type=openapi.TYPE_STRING, required=True
            )
        ],
        tags=["Teacher Invitations"],
    )
    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def accept(self, request, token=None):
        """
        Accept a teacher invitation with comprehensive profile creation support.
        """

        from common.error_handling import (
            APIErrorCode,
            create_authentication_error_response,
            create_invitation_already_accepted_response,
            create_invitation_already_declined_response,
            create_invitation_expired_response,
            create_invitation_invalid_recipient_response,
            create_invitation_not_found_response,
            create_validation_error_response,
        )

        # Get invitation with proper error handling
        try:
            invitation = TeacherInvitation.objects.select_related("school", "invited_by").get(token=token)
        except TeacherInvitation.DoesNotExist:
            return create_invitation_not_found_response(request_path=request.path)

        # Check if invitation is valid with specific error responses
        if not invitation.is_valid():
            if invitation.is_accepted:
                return create_invitation_already_accepted_response(
                    request_path=request.path, accepted_at=invitation.accepted_at
                )
            elif hasattr(invitation, "declined_at") and invitation.declined_at:
                return create_invitation_already_declined_response(
                    request_path=request.path, declined_at=invitation.declined_at
                )
            else:
                return create_invitation_expired_response(request_path=request.path, expires_at=invitation.expires_at)

        # Check authentication with invitation context
        if not request.user.is_authenticated:
            return create_authentication_error_response(
                message="Authentication required to accept invitation",
                request_path=request.path,
                details={
                    "invitation_details": {
                        "school_name": invitation.school.name,
                        "email": invitation.email,
                        "expires_at": invitation.expires_at.isoformat(),
                        "role": invitation.get_role_display(),
                    }
                },
            )

        # Verify recipient with standardized error
        if invitation.email != request.user.email:
            return create_invitation_invalid_recipient_response(
                expected_email=invitation.email, request_path=request.path
            )

        # Validate profile data with improved error handling
        profile_serializer = ComprehensiveTeacherProfileCreationSerializer(data=request.data)

        if not profile_serializer.is_valid():
            return create_validation_error_response(
                serializer_errors=profile_serializer.errors,
                message="Invalid teacher profile data provided",
                request_path=request.path,
            )

        validated_profile_data = profile_serializer.validated_data

        # Process the acceptance with comprehensive profile creation
        try:
            with transaction.atomic():
                profile_created = False

                # Check if user already has a teacher profile
                if hasattr(request.user, "teacher_profile"):
                    teacher_profile = request.user.teacher_profile
                else:
                    # Create teacher profile with comprehensive data or minimal defaults
                    teacher_profile = TeacherProfile.objects.create(
                        user=request.user,
                        bio=validated_profile_data.get("bio", ""),
                        specialty=validated_profile_data.get("specialty", ""),
                        hourly_rate=validated_profile_data.get("hourly_rate"),
                        availability=validated_profile_data.get("availability", ""),
                        phone_number=validated_profile_data.get("phone_number", ""),
                        address=validated_profile_data.get("address", ""),
                        education_background=validated_profile_data.get("education_background", {}),
                        teaching_subjects=validated_profile_data.get("teaching_subjects", []),
                        rate_structure=validated_profile_data.get("rate_structure", {}),
                        weekly_availability=validated_profile_data.get("weekly_availability", {}),
                        grade_level_preferences=validated_profile_data.get("grade_level_preferences", []),
                        teaching_experience=validated_profile_data.get("teaching_experience", {}),
                        credentials_documents=validated_profile_data.get("credentials_documents", []),
                        availability_schedule=validated_profile_data.get("availability_schedule", {}),
                    )
                    profile_created = True

                # Update existing profile with new data if provided
                if not profile_created and validated_profile_data:
                    for field, value in validated_profile_data.items():
                        if field != "profile_photo" and field != "course_ids":  # Handle these separately
                            if value is not None:  # Only update if value is provided
                                setattr(teacher_profile, field, value)
                    teacher_profile.save()

                # Handle profile photo upload for CustomUser
                if validated_profile_data.get("profile_photo"):
                    request.user.profile_photo = validated_profile_data["profile_photo"]
                    request.user.save(update_fields=["profile_photo"])

                # Create or activate school membership
                membership, membership_created = SchoolMembership.objects.get_or_create(
                    user=request.user,
                    school=invitation.school,
                    role=invitation.role,
                    defaults={"is_active": True},
                )

                if not membership_created and not membership.is_active:
                    membership.is_active = True
                    membership.save()

                # Mark invitation as accepted
                invitation.is_accepted = True
                invitation.accepted_at = timezone.now()
                invitation.save()

                # Return comprehensive success response
                from ..serializers import UserSerializer

                response_data = {
                    "success": True,
                    "invitation_accepted": True,
                    "teacher_profile": TeacherSerializer(teacher_profile).data,
                    "school_membership": SchoolMembershipSerializer(membership).data,
                    "user": UserSerializer(request.user).data,
                    "profile_created": profile_created,
                    "school": {
                        "id": invitation.school.id,
                        "name": invitation.school.name,
                        "description": invitation.school.description,
                    },
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Teacher invitation acceptance failed for token {token}: {e}")
            from common.error_handling import create_error_response

            return create_error_response(
                error_code=APIErrorCode.PROFILE_CREATION_FAILED,
                message="Failed to accept invitation and create profile",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_path=request.path,
                details={"error": str(e)},
            )
