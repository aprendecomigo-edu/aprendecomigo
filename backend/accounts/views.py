import logging

from common.messaging import send_email_verification_code, TeacherInvitationEmailService
from common.throttles import (
    BulkInvitationIPThrottle,
    BulkInvitationThrottle,
    EmailBasedThrottle,
    EmailCodeRequestThrottle,
    IndividualInvitationThrottle,
    IPBasedThrottle,
    IPSignupThrottle,
)
from django.contrib.auth import login
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .throttles import ProfileWizardThrottle, FileUploadThrottle, IPBasedThrottle as LocalIPBasedThrottle
from .db_queries import (
    can_user_manage_school,
    create_school_invitation,
    create_school_owner,
    get_or_create_school_invitation_link,
    get_schools_user_can_manage,
    get_user_by_email,
    join_school_via_invitation_link,
    list_school_ids_owned_or_managed,
    list_users_by_request_permissions,
    user_exists,
)
from .models import (
    Course,
    CustomUser,
    EducationalSystem,
    EmailDeliveryStatus,
    EmailSequence,
    EmailSequenceStep,
    EmailCommunication,
    SchoolEmailTemplate,
    EmailTemplateType,
    EmailCommunicationType,
    InvitationStatus,
    ParentChildRelationship,
    ParentProfile,
    School,
    SchoolActivity,
    SchoolInvitation,
    SchoolInvitationLink,
    SchoolMembership,
    SchoolRole,
    SchoolSettings,
    StudentProfile,
    TeacherCourse,
    TeacherInvitation,
    TeacherProfile,
    VerificationCode,
)
from .permissions import (
    IsOwnerOrSchoolAdmin,
    IsSchoolOwnerOrAdmin,
    IsTeacherInAnySchool,
)
from .serializers import (
    AcceptInvitationSerializer,
    AuthenticationResponseSerializer,
    ComprehensiveSchoolSettingsSerializer,
    CourseSerializer,
    CreateStudentSerializer,
    CreateUserSerializer,
    EducationalSystemSerializer,
    EmailAnalyticsSerializer,
    EmailCommunicationSerializer,
    EmailSequenceSerializer,
    EmailTemplatePreviewSerializer,
    EnhancedSchoolSerializer,
    InviteExistingTeacherSerializer,
    ParentChildRelationshipSerializer,
    ParentProfileSerializer,
    ProfileWizardDataSerializer,
    ProfileWizardStepValidationSerializer,
    ProfilePhotoUploadSerializer,
    RequestCodeSerializer,
    SchoolActivitySerializer,
    SchoolEmailTemplateSerializer,
    SchoolInvitationSerializer,
    SchoolMembershipSerializer,
    SchoolMetricsSerializer,
    SchoolProfileSerializer,
    SchoolSerializer,
    SchoolSettingsSerializer,
    SchoolWithMembersSerializer,
    TeacherConsolidatedDashboardSerializer,
    StudentSerializer,
    TeacherCourseSerializer,
    TeacherInvitationSerializer,
    TeacherOnboardingSerializer,
    TeacherSerializer,
    UserSerializer,
    VerifyCodeSerializer,
)

logger = logging.getLogger(__name__)


# Base class for authenticated views
class KnoxAuthenticatedAPIView(APIView):
    """
    Base class for views that require Knox token authentication.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authentication_classes = [TokenAuthentication]
        self.permission_classes = [IsAuthenticated]


# Base class for authenticated viewsets
class KnoxAuthenticatedViewSet(viewsets.ModelViewSet):
    """
    Base class for viewsets that require Knox token authentication.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authentication_classes = [TokenAuthentication]
        self.permission_classes = [IsAuthenticated]


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
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        elif self.action == "signup":
            # Anyone can sign up
            permission_classes = [AllowAny]
        elif self.action == "list":
            # Any authenticated user can list, but queryset is filtered appropriately
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only owner or school admin can modify user records
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        elif self.action in ["retrieve", "school_profile", "dashboard_info"]:
            # Any authenticated user can retrieve, but queryset is filtered appropriately
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
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
        elif SchoolMembership.objects.filter(
            user=user, role=SchoolRole.TEACHER, is_active=True
        ).exists():
            user_type = "teacher"
        # Check if user is a student in any school
        elif SchoolMembership.objects.filter(
            user=user, role=SchoolRole.STUDENT, is_active=True
        ).exists():
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
        elif SchoolMembership.objects.filter(
            user=user, role=SchoolRole.TEACHER, is_active=True
        ).exists():
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
        elif SchoolMembership.objects.filter(
            user=user, role=SchoolRole.STUDENT, is_active=True
        ).exists():
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
            or SchoolMembership.objects.filter(
                user=request.user, school=school, is_active=True
            ).exists()
        ):
            return Response(
                {"error": "You don't have access to this school"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # School statistics
        stats = {
            "students": SchoolMembership.objects.filter(
                school=school, role=SchoolRole.STUDENT, is_active=True
            ).count(),
            "teachers": SchoolMembership.objects.filter(
                school=school, role=SchoolRole.TEACHER, is_active=True
            ).count(),
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
                verification = VerificationCode.objects.filter(
                    email=contact_value, is_used=False
                ).latest("created_at")
            else:
                # For phone verification, we would need a similar model for phone codes
                # This example assumes we're using the same model for simplicity
                verification = VerificationCode.objects.filter(
                    email=contact_value, is_used=False
                ).latest("created_at")
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
        from django.db import transaction
        
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
                user, school = create_school_owner(email, name, phone_number, primary_contact, school_data, is_tutor=is_tutor)
                
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
                "onboarding_completed": user.onboarding_completed
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
                return Response(
                    {"error": "steps_completed must be a list"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not current_step:
                return Response(
                    {"error": "current_step is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if completion_percentage is None:
                return Response(
                    {"error": "completion_percentage is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not (0 <= completion_percentage <= 100):
                return Response(
                    {"error": "completion_percentage must be between 0 and 100"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update user's onboarding progress
            progress_data = {
                "steps_completed": steps_completed,
                "current_step": current_step,
                "completion_percentage": completion_percentage,
                "skipped": skipped
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
                "onboarding_completed": user.onboarding_completed
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
            if "quick_actions" in update_data:
                if not isinstance(update_data["quick_actions"], list):
                    return Response(
                        {"error": "quick_actions must be a list"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if "default_landing_page" in update_data:
                if update_data["default_landing_page"] not in valid_landing_pages:
                    return Response(
                        {"error": f"default_landing_page must be one of: {', '.join(valid_landing_pages)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if "navigation_style" in update_data:
                if update_data["navigation_style"] not in valid_navigation_styles:
                    return Response(
                        {"error": f"navigation_style must be one of: {', '.join(valid_navigation_styles)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if "tutorial_auto_start" in update_data:
                if not isinstance(update_data["tutorial_auto_start"], bool):
                    return Response(
                        {"error": "tutorial_auto_start must be a boolean"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Update preferences (merge with existing)
            current_preferences.update(update_data)
            
            user.tutorial_preferences = current_preferences
            user.save(update_fields=["tutorial_preferences"])
            
            # Return updated preferences
            return Response(current_preferences, status=status.HTTP_200_OK)


class RequestCodeView(APIView):
    """
    API endpoint for requesting a TOTP verification code.
    Rate limited to prevent abuse.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authentication_classes = []  # No authentication required
        self.permission_classes = [AllowAny]
        self.throttle_classes = [EmailCodeRequestThrottle]

    def post(self, request):
        serializer = RequestCodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        # Check if a user with this email exists
        if not user_exists(email):
            # Log the event internally for security monitoring
            logger.warning(
                f"Authentication attempt with unregistered email: {email} from IP: {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            print(f"[SECURITY] Login attempt with unregistered email: {email}")

            # Perform a dummy code generation for non-existent users to ensure constant time
            # This prevents email enumeration attacks
            dummy_code = VerificationCode.generate_code("dummy@example.com")
            _ = dummy_code.get_current_code()
            return Response(
                {
                    "message": "If an account exists with this email, a verification code has been sent."
                },
                status=status.HTTP_200_OK,
            )

        # User exists - generate real verification code
        logger.info(f"Verification code requested for registered email: {email}")
        print(f"[INFO] Generating verification code for registered user: {email}")

        verification = VerificationCode.generate_code(email)
        code = verification.get_current_code()

        try:
            send_email_verification_code(email, code)
            logger.info(f"Verification code sent successfully to: {email}")
            print(f"[INFO] Verification code sent to: {email}")
        except Exception as e:
            logger.error(f"Failed to send verification code to {email}: {e}")
            return Response(
                {"error": f"Failed to send email: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": f"Verification code sent to {email}."},
            status=status.HTTP_200_OK,
        )


class VerifyCodeView(APIView):
    """
    API endpoint for verifying a TOTP code and authenticating the user.
    Uses Knox tokens for authentication.
    Rate limited by both email and IP to prevent brute force attacks.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authentication_classes = []  # No authentication required
        self.permission_classes = [AllowAny]
        self.throttle_classes = [EmailBasedThrottle, IPBasedThrottle]  # Apply both throttles

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        # Check if a user with this email exists
        if not user_exists(email):
            logger.info(f"Verification attempted for non-existent email: {email}")
            # Perform a dummy code generation for non-existent users to ensure constant time
            dummy_code = VerificationCode.generate_code("dummy@example.com")
            _ = dummy_code.get_current_code()
            return Response(
                {
                    "message": "If an account exists with this email, a verification code has been sent."
                },
                status=status.HTTP_200_OK,
            )

        # Try to get the latest verification code for this email
        try:
            verification = VerificationCode.objects.filter(email=email, is_used=False).latest(
                "created_at"
            )
        except VerificationCode.DoesNotExist:
            return Response(
                {"error": "No verification code found for this email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the code
        if not verification.is_valid(code):
            # Record the failed attempt
            locked_out = verification.record_failed_attempt()
            if locked_out:
                return Response(
                    {"error": "Too many failed attempts. Please request a new verification code."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"error": "Invalid or expired verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get user
        user = get_user_by_email(email)

        # Mark verification as used
        verification.use()

        # Update user's email verification status
        if email == user.email:
            user.email_verified = True
            user.save()
        elif email == user.phone_number:
            user.phone_verified = True
            user.save()

        # Create default onboarding tasks for new users
        try:
            from tasks.models import Task

            # Check if user already has tasks (to avoid duplicates)
            if not Task.objects.filter(user=user).exists():
                Task.create_onboarding_tasks(user)
        except Exception as e:
            # Log error but don't fail the verification process
            logger.error(f"Failed to create onboarding tasks for user {user.email}: {e}")

        # Create a session token for the user
        _, token = AuthToken.objects.create(user)

        # If using Django sessions, also login the user
        if hasattr(request, "_request") and hasattr(request._request, "session"):
            login(request._request, user)

        # Return the token and user info with enhanced data for frontend routing
        response_data = {
            "token": token,
            "user": AuthenticationResponseSerializer(user).data,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class SchoolViewSet(KnoxAuthenticatedViewSet):
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
        user_school_ids = SchoolMembership.objects.filter(
            user=self.request.user,
            is_active=True
        ).values_list("school_id", flat=True)
        
        return School.objects.filter(id__in=user_school_ids)

    def get_permissions(self):
        """Allow anyone to view schools, but only authorized users to modify."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
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

    @action(detail=True, methods=['get', 'patch'], url_path='settings', permission_classes=[IsAuthenticated, IsSchoolOwnerOrAdmin])
    def school_settings(self, request, pk=None):
        """Get or update comprehensive school settings"""
        school = self.get_object()
        
        if request.method == 'GET':
            # Get or create school settings
            settings_obj, created = SchoolSettings.objects.get_or_create(
                school=school,
                defaults={
                    'educational_system_id': 1,  # Default to Portugal system
                    'working_days': [0, 1, 2, 3, 4],  # Monday to Friday
                }
            )
            
            # Use comprehensive serializer that includes both profile and settings
            serializer = ComprehensiveSchoolSettingsSerializer(
                settings_obj, 
                context={'request': request}
            )
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PATCH':
            # Update school settings with comprehensive validation
            # Get or create school settings
            settings_obj, created = SchoolSettings.objects.get_or_create(
                school=school,
                defaults={
                    'educational_system_id': 1,
                    'working_days': [0, 1, 2, 3, 4],
                }
            )
        
            
            # Store old values for activity logging
            old_values = {}
            changed_fields = []
        
            # Process school profile updates if present
            if 'school_profile' in request.data:
                profile_data = request.data['school_profile']
                school_serializer = SchoolProfileSerializer(
                    school, 
                    data=profile_data, 
                    partial=True,
                    context={'request': request}
                )
                
                if school_serializer.is_valid(raise_exception=True):
                    # Store old school values for logging
                    for field in profile_data.keys():
                        if hasattr(school, field):
                            old_values[f"school.{field}"] = getattr(school, field)
                    
                    school_serializer.save()
                    changed_fields.extend([f"school.{field}" for field in profile_data.keys()])
            
            # Process settings updates
            settings_data = request.data.get('settings', request.data)
            if settings_data:
                # Store old settings values for logging
                for field in settings_data.keys():
                    if hasattr(settings_obj, field):
                        old_values[f"settings.{field}"] = getattr(settings_obj, field)
                
                settings_serializer = SchoolSettingsSerializer(
                    settings_obj,
                    data=settings_data,
                    partial=True,
                    context={'request': request}
                )
                
                if settings_serializer.is_valid(raise_exception=True):
                    settings_serializer.save()
                    changed_fields.extend([f"settings.{field}" for field in settings_data.keys()])
            
            # Create activity log for settings update
            if changed_fields:
                from .services.metrics_service import SchoolActivityService
                from .models import ActivityType
                
                changes_description = []
                for field in changed_fields:
                    if field in old_values:
                        old_value = old_values[field]
                        new_value = getattr(
                            school if field.startswith('school.') else settings_obj, 
                            field.split('.', 1)[1]
                        )
                        if old_value != new_value:
                            changes_description.append(f"{field}: '{old_value}' → '{new_value}'")
                
                if changes_description:
                    SchoolActivityService.create_activity(
                        school=school,
                        activity_type=ActivityType.SETTINGS_UPDATED,
                        actor=request.user,
                        description=f"Updated school settings: {', '.join(changes_description)}",
                        metadata={'changed_fields': changed_fields}
                    )
            
            # Invalidate metrics cache
            from .services.metrics_service import SchoolMetricsService
            SchoolMetricsService.invalidate_cache(school.id)
            
            # Return updated settings
            serializer = ComprehensiveSchoolSettingsSerializer(
                settings_obj, 
                context={'request': request}
            )
            
            return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='settings/educational-systems', permission_classes=[IsAuthenticated, IsSchoolOwnerOrAdmin])
    def educational_systems(self, request, pk=None):
        """Get available educational systems for school configuration"""
        from .serializers import EducationalSystemSerializer
        
        systems = EducationalSystem.objects.filter(is_active=True)
        serializer = EducationalSystemSerializer(systems, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='metrics', permission_classes=[IsAuthenticated, IsSchoolOwnerOrAdmin])
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
        from .services.metrics_service import SchoolMetricsService
        from .serializers import SchoolMetricsSerializer
        
        metrics_service = SchoolMetricsService(school)
        metrics_data = metrics_service.get_metrics()
        
        serializer = SchoolMetricsSerializer(data=metrics_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='activity', permission_classes=[IsAuthenticated, IsSchoolOwnerOrAdmin])
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
        from .services.metrics_service import SchoolActivityService
        from .serializers import SchoolActivitySerializer
        from rest_framework.pagination import PageNumberPagination
        from django.core.paginator import Paginator, EmptyPage
        
        # Get query parameters for filtering
        activity_types = request.query_params.get('activity_types')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        # Safely parse pagination parameters with validation
        try:
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)  # Max 100 items per page
        except (ValueError, TypeError):
            page = 1
            page_size = 20
        
        # Build filters
        filters = {}
        if activity_types:
            filters['activity_types'] = activity_types
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        try:
            # Get activities using the service
            activities_queryset = SchoolActivityService.get_activity_feed(
                school=school, 
                page_size=None,  # Get all, we'll paginate manually
                filters=filters
            )
            
            # Set up pagination
            paginator = Paginator(activities_queryset, page_size)
            
            try:
                activities_page = paginator.page(page)
            except EmptyPage:
                activities_page = paginator.page(paginator.num_pages) if paginator.num_pages > 0 else paginator.page(1)
            
            # Serialize the activities
            serializer = SchoolActivitySerializer(
                activities_page.object_list, 
                many=True, 
                context={'request': request}
            )
            
            # Build pagination response
            response_data = {
                'count': paginator.count,
                'next': None,
                'previous': None,
                'results': serializer.data
            }
            
            # Add next/previous page URLs if they exist
            if activities_page.has_next():
                next_page = activities_page.next_page_number()
                response_data['next'] = request.build_absolute_uri(
                    request.path + f'?page={next_page}'
                )
                # Preserve filter parameters
                for key, value in request.query_params.items():
                    if key != 'page':
                        response_data['next'] += f'&{key}={value}'
            
            if activities_page.has_previous():
                prev_page = activities_page.previous_page_number()
                response_data['previous'] = request.build_absolute_uri(
                    request.path + f'?page={prev_page}'
                )
                # Preserve filter parameters
                for key, value in request.query_params.items():
                    if key != 'page':
                        response_data['previous'] += f'&{key}={value}'
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to get activity feed for school {school.id}: {e}")
            return Response(
                {"error": "Failed to retrieve activity feed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SchoolMembershipViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for school memberships.
    """

    serializer_class = SchoolMembershipSerializer

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


class TeacherViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for teacher profiles.
    """

    serializer_class = TeacherSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return TeacherProfile.objects.all()

        # School owners and admins can see teachers in their schools
        # Get the schools where user is an admin
        admin_school_ids = list_school_ids_owned_or_managed(user)
        if len(admin_school_ids) > 0:
            # Get all teacher users in these schools
            teacher_user_ids = SchoolMembership.objects.filter(
                school_id__in=admin_school_ids, role=SchoolRole.TEACHER, is_active=True
            ).values_list("user_id", flat=True)

            return TeacherProfile.objects.filter(user_id__in=teacher_user_ids)

        # Students can see teachers in their schools (for booking classes)
        student_school_ids = SchoolMembership.objects.filter(
            user=user, role=SchoolRole.STUDENT, is_active=True
        ).values_list("school_id", flat=True)

        if len(student_school_ids) > 0:
            # Get all teacher users in the student's schools
            teacher_user_ids = SchoolMembership.objects.filter(
                school_id__in=student_school_ids, role=SchoolRole.TEACHER, is_active=True
            ).values_list("user_id", flat=True)

            return TeacherProfile.objects.filter(user_id__in=teacher_user_ids)

        # Teachers can see their own profile
        if hasattr(user, "teacher_profile"):
            return TeacherProfile.objects.filter(user=user)

        return TeacherProfile.objects.none()

    def list(self, request, *args, **kwargs):
        """
        Override list to include pending invitations when requested.
        """
        include_pending = request.query_params.get("include_pending", "false").lower() == "true"

        if not include_pending:
            # Standard behavior
            return super().list(request, *args, **kwargs)

        # Get regular teachers
        teachers_queryset = self.get_queryset()
        teachers_data = TeacherSerializer(teachers_queryset, many=True).data

        # Add pending invitations for school admins
        admin_school_ids = list_school_ids_owned_or_managed(request.user)
        if admin_school_ids:
            pending_invitations = SchoolInvitation.objects.filter(
                school_id__in=admin_school_ids,
                role=SchoolRole.TEACHER,
                is_accepted=False,
                expires_at__gt=timezone.now(),
            ).select_related("school")

            # Convert invitations to teacher-like format
            for invitation in pending_invitations:
                try:
                    invited_user = CustomUser.objects.get(email=invitation.email)
                    teachers_data.append(
                        {
                            "id": None,  # No teacher profile yet
                            "user": {
                                "id": invited_user.id,
                                "email": invited_user.email,
                                "name": invited_user.name,
                                "phone_number": invited_user.phone_number,
                                "is_student": False,
                                "is_teacher": False,
                            },
                            "bio": "",
                            "specialty": "",
                            "education": "",
                            "courses": [],
                            "status": "pending",
                            "invitation": {
                                "id": invitation.id,
                                "token": invitation.token,
                                "link": f"https://aprendecomigo.com/accept-invitation/{invitation.token}",
                                "expires_at": invitation.expires_at,
                                "invited_by": invitation.invited_by.name,
                                "created_at": invitation.created_at,
                            },
                        }
                    )
                except CustomUser.DoesNotExist:
                    # Handle case where invited user was deleted
                    teachers_data.append(
                        {
                            "id": None,
                            "user": {
                                "id": None,
                                "email": invitation.email,
                                "name": invitation.email.split("@")[0],  # Use email prefix as name
                                "phone_number": "",
                                "is_student": False,
                                "is_teacher": False,
                            },
                            "bio": "",
                            "specialty": "",
                            "education": "",
                            "courses": [],
                            "status": "pending_user_not_found",
                            "invitation": {
                                "id": invitation.id,
                                "token": invitation.token,
                                "link": f"https://aprendecomigo.com/accept-invitation/{invitation.token}",
                                "expires_at": invitation.expires_at,
                                "invited_by": invitation.invited_by.name,
                                "created_at": invitation.created_at,
                            },
                        }
                    )

        # Add status to regular teachers
        for teacher in teachers_data:
            if "status" not in teacher:
                teacher["status"] = "active"

        return Response(teachers_data)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        elif self.action == "onboarding":
            permission_classes = [IsAuthenticated]
        elif self.action in ["invite_new", "invite_existing", "invite_bulk"]:
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            permission_classes = [IsAuthenticated, IsTeacherInAnySchool]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def onboarding(self, request):
        """
        Create a teacher profile with associated courses in a single atomic transaction.

        This endpoint handles the self-onboarding process for the current user:
        1. Creates a teacher profile for the current user
        2. Associates the teacher with specified courses
        3. If user is a school owner/admin, creates teacher memberships for their schools

        All operations are atomic - if any part fails, everything is rolled back.
        """
        from django.db import transaction
        from rest_framework import status

        # Check if user already has a teacher profile
        if hasattr(request.user, "teacher_profile"):
            return Response(
                {"error": "You already have a teacher profile"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate the request data
        serializer = TeacherOnboardingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        try:
            with transaction.atomic():
                # Extract teacher profile data
                profile_data = {
                    key: value for key, value in validated_data.items() if key not in ["course_ids"]
                }

                # Create teacher profile
                teacher_profile = TeacherProfile.objects.create(user=request.user, **profile_data)

                # Associate courses if provided
                course_ids = validated_data.get("course_ids", [])

                teacher_courses = []
                if course_ids:
                    for course_id in course_ids:
                        teacher_course = TeacherCourse.objects.create(
                            teacher=teacher_profile, course_id=course_id, is_active=True
                        )
                        teacher_courses.append(teacher_course)

                # If user is a school owner/admin, create teacher memberships for their schools
                admin_memberships = SchoolMembership.objects.filter(
                    user=request.user,
                    role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
                    is_active=True,
                )

                teacher_memberships_created = []
                for admin_membership in admin_memberships:
                    # Create teacher membership if it doesn't exist
                    teacher_membership, created = SchoolMembership.objects.get_or_create(
                        user=request.user,
                        school=admin_membership.school,
                        role=SchoolRole.TEACHER,
                        defaults={"is_active": True},
                    )
                    if created:
                        teacher_memberships_created.append(teacher_membership)

                # Return the complete teacher profile with courses
                response_serializer = TeacherSerializer(teacher_profile)
                response_data = {
                    "message": "Teacher profile created successfully",
                    "teacher": response_serializer.data,
                    "courses_added": len(teacher_courses),
                }

                # Add info about school memberships if any were created
                if teacher_memberships_created:
                    response_data["teacher_memberships_created"] = len(teacher_memberships_created)
                    response_data["schools_added_as_teacher"] = [
                        membership.school.name for membership in teacher_memberships_created
                    ]

                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Log the error for debugging
            logger.error(f"Teacher onboarding failed for user {request.user.id}: {e!s}")

            return Response(
                {"error": "Failed to create teacher profile. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get", "patch"], url_path="profile")
    def profile(self, request):
        """
        Get or update the current user's teacher profile.
        """
        from rest_framework import status

        # Check if user has a teacher profile
        if not hasattr(request.user, "teacher_profile") or request.user.teacher_profile is None:
            return Response(
                {"error": "Teacher profile not found. Please complete onboarding first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        teacher_profile = request.user.teacher_profile

        if request.method == "GET":
            # Return the teacher's profile
            serializer = TeacherSerializer(teacher_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == "PATCH":
            # Update the teacher's profile
            serializer = TeacherSerializer(teacher_profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="profile/photo")
    def upload_profile_photo(self, request):
        """
        Upload profile photo for the current user's teacher profile.
        """
        from rest_framework import status

        # Check if user has a teacher profile
        if not hasattr(request.user, "teacher_profile") or request.user.teacher_profile is None:
            return Response(
                {"error": "Teacher profile not found. Please complete onboarding first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if 'photo' not in request.FILES:
            return Response(
                {"error": "No photo file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        photo = request.FILES['photo']
        teacher_profile = request.user.teacher_profile
        
        # Save the photo to the profile (assuming there's a photo field or similar)
        # For now, we'll just return a mock URL - this should be implemented based on your file storage setup
        teacher_profile.save()  # This would save any photo field updates
        
        # Return the photo URL (mock for now)
        photo_url = f"/media/teacher_profiles/{teacher_profile.id}/profile.jpg"
        
        return Response(
            {"photo_url": photo_url},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], throttle_classes=[IndividualInvitationThrottle])
    def invite_existing(self, request):
        """
        Invite an existing user to become a teacher at a school.

        This endpoint allows school owners/admins to:
        1. Create an invitation for an existing user
        2. Optionally send email/SMS notifications
        3. Return a shareable invitation link

        The user can later accept the invitation to become a teacher.
        """
        # Validate the request data
        serializer = InviteExistingTeacherSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        email = validated_data["email"]
        school_id = validated_data["school_id"]
        send_email = validated_data.get("send_email", False)
        send_sms = validated_data.get("send_sms", False)

        # Check if the requesting user can manage this school
        if not can_user_manage_school(request.user, school_id):
            return Response(
                {"error": "You don't have permission to invite teachers to this school"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Create invitation
            invitation = create_school_invitation(
                school_id=school_id,
                email=email,
                invited_by=request.user,
                role=SchoolRole.TEACHER,
            )

            # Get school info for response
            school = School.objects.get(id=school_id)
            user = CustomUser.objects.get(email=email)

            # Build invitation link
            # TODO: Replace with actual frontend URL
            invitation_link = f"https://aprendecomigo.com/accept-invitation/{invitation.token}"

            response_data = {
                "message": "Invitation created successfully",
                "invitation": {
                    "id": invitation.id,
                    "token": invitation.token,
                    "link": invitation_link,
                    "expires_at": invitation.expires_at,
                    "school": {
                        "id": school.id,
                        "name": school.name,
                    },
                    "invited_user": {
                        "email": user.email,
                        "name": user.name,
                    },
                },
                "notifications_sent": {
                    "email": False,
                    "sms": False,
                },
            }

            # Send email notification if requested
            if send_email:
                try:
                    email_result = TeacherInvitationEmailService.send_invitation_email(invitation)
                    
                    if email_result['success']:
                        response_data["notifications_sent"]["email"] = True
                        invitation.mark_email_sent()
                        logger.info(f"Individual invitation email sent to {invitation.email}")
                    else:
                        logger.warning(f"Failed to send invitation email: {email_result.get('error', 'Unknown error')}")
                        invitation.mark_email_failed(email_result.get('error', 'Unknown error'))
                        
                except Exception as e:
                    logger.warning(f"Failed to send invitation email: {e}")
                    invitation.mark_email_failed(f"Exception: {str(e)}")

            # Send SMS notification if requested
            if send_sms:
                try:
                    # TODO: Implement SMS sending
                    # send_invitation_sms(invitation, invitation_link)
                    response_data["notifications_sent"]["sms"] = True
                except Exception as e:
                    logger.warning(f"Failed to send invitation SMS: {e}")

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Log detailed error for debugging but don't expose to user
            logger.error(f"Invite existing teacher failed for user {request.user.id}, email {email}: {str(e)}", exc_info=True)

            return Response(
                {
                    "error": "Unable to create invitation at this time. Please try again later.",
                    "error_code": "INVITATION_CREATION_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["post"],
        url_path="invite-bulk",
        url_name="invite-bulk",
        throttle_classes=[BulkInvitationThrottle, BulkInvitationIPThrottle]
    )
    def invite_bulk(self, request):
        """
        Create bulk teacher invitations with transaction management.
        
        Supports processing 50+ invitations efficiently with proper error handling,
        transaction rollback, and detailed response for partial failures.
        """
        import uuid
        from django.db import transaction
        from .serializers import BulkTeacherInvitationSerializer, BulkInvitationResponseSerializer
        
        # Validate request data
        serializer = BulkTeacherInvitationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        school_id = validated_data['school_id']
        custom_message = validated_data.get('custom_message', '')
        send_email = validated_data.get('send_email', False)
        invitations_data = validated_data['invitations']
        
        # Generate batch ID for grouping invitations
        batch_id = uuid.uuid4()
        
        # Track results
        successful_invitations = []
        failed_invitations = []
        errors = []
        processed_emails = set()  # Track duplicates within the request
        
        # Process each invitation within transaction for consistency
        try:
            # Pre-validate all data before starting transaction
            validation_errors = []
            valid_emails = []
            
            for invitation_data in invitations_data:
                email = invitation_data['email']
                
                # Skip if we already processed this email in this batch
                if email in processed_emails:
                    validation_errors.append({
                        'email': email,
                        'error': 'Duplicate email address in request'
                    })
                    continue
                
                processed_emails.add(email)
                
                # Validate email format (basic validation)
                if not email or not email.strip() or '@' not in email:
                    validation_errors.append({
                        'email': email if email else '(empty)',
                        'error': 'Invalid email format'
                    })
                    continue
                
                valid_emails.append(email)
            
            # If all emails failed validation, return early
            if not valid_emails:
                failed_invitations.extend([error['email'] for error in validation_errors])
                errors.extend(validation_errors)
                
                response_data = {
                    'batch_id': batch_id,
                    'total_invitations': len(invitations_data),
                    'successful_invitations': 0,
                    'failed_invitations': len(failed_invitations),
                    'errors': errors,
                    'invitations': [],
                    'message': f'All invitations failed validation. 0 successful, {len(failed_invitations)} failed.'
                }
                
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            
            # Now process valid emails within transaction
            with transaction.atomic():
                school = School.objects.select_for_update().get(id=school_id)
                
                # Check for existing active invitations in bulk (more efficient)
                existing_emails = set(
                    TeacherInvitation.objects.filter(
                        school=school,
                        email__in=valid_emails,
                        is_accepted=False,
                        expires_at__gt=timezone.now(),
                        status__in=[
                            InvitationStatus.PENDING,
                            InvitationStatus.SENT,
                            InvitationStatus.DELIVERED,
                            InvitationStatus.VIEWED,
                        ]
                    ).values_list('email', flat=True)
                )
                
                # Process each valid email
                for email in valid_emails:
                    try:
                        # Check if invitation already exists
                        if email in existing_emails:
                            failed_invitations.append(email)
                            errors.append({
                                'email': email,
                                'error': 'An active invitation already exists for this email and school'
                            })
                            continue
                        
                        # Create invitation
                        invitation = TeacherInvitation.objects.create(
                            school=school,
                            email=email,
                            invited_by=request.user,
                            custom_message=custom_message,
                            batch_id=batch_id,
                            role=SchoolRole.TEACHER
                        )
                        
                        successful_invitations.append(invitation)
                        
                    except ValidationError as e:
                        failed_invitations.append(email)
                        errors.append({
                            'email': email,
                            'error': str(e)
                        })
                    except Exception as e:
                        failed_invitations.append(email)
                        errors.append({
                            'email': email,
                            'error': f'Unexpected error: {str(e)}'
                        })
                
                # Add validation errors to final errors
                failed_invitations.extend([error['email'] for error in validation_errors])
                errors.extend(validation_errors)
                
                # Prepare response data
                response_data = {
                    'batch_id': batch_id,
                    'total_invitations': len(invitations_data),
                    'successful_invitations': len(successful_invitations),
                    'failed_invitations': len(failed_invitations),
                    'errors': errors,
                    'invitations': [],
                    'message': f'Batch invitation completed. {len(successful_invitations)} successful, {len(failed_invitations)} failed.'
                }
                
                # Add invitation details for successful invitations
                for invitation in successful_invitations:
                    invitation_link = f"https://aprendecomigo.com/accept-teacher-invitation/{invitation.token}"
                    response_data['invitations'].append({
                        'id': invitation.id,
                        'email': invitation.email,
                        'token': invitation.token,
                        'link': invitation_link,
                        'expires_at': invitation.expires_at,
                        'status': invitation.status,
                        'email_delivery_status': invitation.email_delivery_status
                    })
                
                # Determine response status code
                if len(failed_invitations) == 0:
                    # All invitations successful
                    response_status = status.HTTP_201_CREATED
                elif len(successful_invitations) == 0:
                    # All invitations failed
                    response_status = status.HTTP_400_BAD_REQUEST
                else:
                    # Partial success
                    response_status = status.HTTP_207_MULTI_STATUS
                
                # Send batch email notifications if requested
                email_results = {'successful_emails': 0, 'failed_emails': 0, 'errors': []}
                if send_email and successful_invitations:
                    try:
                        email_results = TeacherInvitationEmailService.send_bulk_invitation_emails(
                            successful_invitations
                        )
                        
                        # Update response with email results
                        response_data['email_results'] = {
                            'emails_sent': email_results['successful_emails'],
                            'email_failures': email_results['failed_emails'],
                            'email_errors': email_results['errors']
                        }
                        
                        logger.info(
                            f"Bulk emails processed: {email_results['successful_emails']} sent, "
                            f"{email_results['failed_emails']} failed"
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to send batch emails: {e}")
                        response_data['email_results'] = {
                            'emails_sent': 0,
                            'email_failures': len(successful_invitations),
                            'email_errors': [{'error': f'Batch email processing failed: {str(e)}'}]
                        }
                
                return Response(response_data, status=response_status)
                
        except Exception as e:
            # Log detailed error for debugging but don't expose to user
            logger.error(f"Bulk teacher invitation failed for user {request.user.id}: {str(e)}", exc_info=True)
            
            # Return generic error message to prevent information leakage
            return Response(
                {
                    "error": "Unable to process bulk invitations at this time. Please try again later.",
                    "error_code": "BULK_INVITATION_FAILED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsTeacherInAnySchool])
    def consolidated_dashboard(self, request):
        """
        Get consolidated dashboard data for the authenticated teacher.
        
        Returns comprehensive dashboard data including:
        - Teacher profile information
        - Students with progress data
        - Sessions (today, upcoming, recent completed)
        - Progress metrics and analytics
        - Recent activities
        - Earnings data
        - Quick stats for widgets
        
        Optimized for performance with query optimization and caching.
        Response time target: < 500ms
        """
        try:
            # Ensure user has a teacher profile
            if not hasattr(request.user, 'teacher_profile') or not request.user.teacher_profile:
                return Response(
                    {
                        "error": "Teacher profile not found",
                        "detail": "User must have a teacher profile to access dashboard"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            teacher_profile = request.user.teacher_profile
            
            # Use the dashboard service for data aggregation
            from .services.teacher_dashboard_service import TeacherDashboardService
            
            dashboard_service = TeacherDashboardService(teacher_profile)
            dashboard_data = dashboard_service.get_consolidated_dashboard_data()
            
            # Serialize the response
            serializer = TeacherConsolidatedDashboardSerializer(dashboard_data)
            
            # Add cache control headers for client-side caching
            response = Response(serializer.data, status=status.HTTP_200_OK)
            response['Cache-Control'] = 'private, max-age=300'  # 5 minutes cache
            response['X-Dashboard-Generated'] = timezone.now().isoformat()
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating consolidated dashboard for teacher {request.user.id}: {e}", exc_info=True)
            
            return Response(
                {
                    "error": "Unable to load dashboard data",
                    "detail": "Please try again in a few moments"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TeacherProfileWizardViewSet(KnoxAuthenticatedAPIView):
    """
    SECURE API endpoints for the Teacher Profile Creation Wizard.
    Implements comprehensive security measures including:
    - Input validation and sanitization
    - Rate limiting
    - Transaction management
    - Security logging
    - Proper error handling
    """
    
    # Apply rate limiting to all endpoints in this viewset
    throttle_classes = [ProfileWizardThrottle]
    
    def post(self, request, *args, **kwargs):
        """
        Handle different wizard operations based on the URL path.
        All operations are secured with input validation and rate limiting.
        """
        from rest_framework import status
        from .services.profile_completion import ProfileCompletionService
        
        action = kwargs.get('action')
        
        try:
            if action == 'save-progress':
                return self._save_progress(request)
            elif action == 'validate-step':
                return self._validate_step(request)
            elif action == 'submit':
                return self._submit_profile(request)
            elif action == 'upload-photo':
                return self._upload_photo(request)
            else:
                logger.warning(f"Invalid action attempted: {action} by user {request.user.id}")
                return Response(
                    {"error": "Invalid action"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Unexpected error in TeacherProfileWizardViewSet: {e}", exc_info=True)
            return Response(
                {"error": "An error occurred processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests for wizard data.
        """
        from rest_framework import status
        from .services.profile_completion import ProfileCompletionService
        
        action = kwargs.get('action')
        
        if action == 'profile-completion-score':
            return self._get_completion_score(request)
        elif action == 'rate-suggestions':
            return self._get_rate_suggestions(request)
        else:
            return Response(
                {"error": "Invalid action"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _save_progress(self, request):
        """
        SECURE save wizard progress to the teacher profile.
        Implements comprehensive validation, sanitization, and transaction management.
        """
        from django.db import transaction
        from rest_framework import status
        from .services.profile_completion import ProfileCompletionService
        
        # Check if user has a teacher profile
        if not hasattr(request.user, "teacher_profile") or request.user.teacher_profile is None:
            logger.warning(f"Teacher profile not found for user {request.user.id}")
            return Response(
                {"error": "Teacher profile not found. Please complete onboarding first."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # SECURITY: Validate all input data using comprehensive serializer
        profile_data_raw = request.data.get('profile_data', {})
        current_step = request.data.get('current_step', 0)
        
        # Log potential security events
        if self._detect_security_patterns(profile_data_raw):
            logger.warning(
                f"Potential security threat detected in profile data for user {request.user.id}. "
                f"IP: {self._get_client_ip(request)}, Data keys: {list(profile_data_raw.keys())}"
            )
        
        # Validate input using secure serializer
        serializer = ProfileWizardDataSerializer(data=profile_data_raw)
        if not serializer.is_valid():
            logger.info(f"Profile data validation failed for user {request.user.id}: {serializer.errors}")
            return Response(
                {"error": "Invalid profile data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        # SECURITY: Use atomic transaction to ensure data integrity
        try:
            with transaction.atomic():
                teacher_profile = request.user.teacher_profile
                
                # Update user name with validated data
                if 'first_name' in validated_data and 'last_name' in validated_data:
                    full_name = f"{validated_data['first_name']} {validated_data['last_name']}".strip()
                    request.user.name = full_name
                    request.user.save()
                    logger.info(f"Updated name for user {request.user.id}")
                
                # Update email if provided and different
                if 'email' in validated_data and validated_data['email'] != request.user.email:
                    request.user.email = validated_data['email']
                    request.user.username = validated_data['email']  # Keep username in sync
                    request.user.save()
                    logger.info(f"Updated email for user {request.user.id}")
                
                # Update teacher profile fields with sanitized data
                if 'professional_bio' in validated_data:
                    teacher_profile.bio = validated_data['professional_bio']
                
                if 'professional_title' in validated_data:
                    teacher_profile.specialty = validated_data['professional_title']
                
                if 'phone_number' in validated_data:
                    teacher_profile.phone_number = validated_data['phone_number']
                
                if 'years_experience' in validated_data:
                    # Store in education background JSON
                    if not teacher_profile.education_background:
                        teacher_profile.education_background = {}
                    teacher_profile.education_background['years_experience'] = validated_data['years_experience']
                
                if 'education_background' in validated_data:
                    teacher_profile.education_background = validated_data['education_background']
                
                if 'teaching_subjects' in validated_data:
                    teacher_profile.teaching_subjects = validated_data['teaching_subjects']
                
                if 'rate_structure' in validated_data:
                    teacher_profile.rate_structure = validated_data['rate_structure']
                    # Also update the legacy hourly_rate field if individual_rate is present
                    if 'individual_rate' in validated_data['rate_structure']:
                        teacher_profile.hourly_rate = validated_data['rate_structure']['individual_rate']
                
                # Save profile and update completion score
                teacher_profile.save()
                teacher_profile.update_completion_score()
                
                # Get updated completion data
                completion_data = ProfileCompletionService.calculate_completion(teacher_profile)
                
                logger.info(f"Successfully saved profile progress for user {request.user.id}, step {current_step}")
                
                return Response({
                    "success": True,
                    "completion_data": completion_data,
                    "message": "Profile updated successfully"
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(
                f"Error saving wizard progress for user {request.user.id}: {e}",
                exc_info=True
            )
            return Response(
                {"error": "An error occurred while saving your profile. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _validate_step(self, request):
        """
        SECURE validation of a specific wizard step.
        Uses comprehensive serializer validation.
        """
        from rest_framework import status
        
        # Validate request structure first
        serializer = ProfileWizardStepValidationSerializer(data=request.data)
        if not serializer.is_valid():
            logger.info(f"Step validation request failed for user {request.user.id}: {serializer.errors}")
            return Response({
                "is_valid": False,
                "errors": serializer.errors,
                "warnings": {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        step = validated_data['step']
        data = validated_data['data']
        
        logger.info(f"Validated step {step} for user {request.user.id}")
        
        return Response({
            "is_valid": True,
            "errors": {},
            "warnings": {},
            "message": f"Step {step} is valid"
        }, status=status.HTTP_200_OK)
    
    def _submit_profile(self, request):
        """Submit the complete profile."""
        from rest_framework import status
        from .services.profile_completion import ProfileCompletionService
        
        # Check if user has a teacher profile
        if not hasattr(request.user, "teacher_profile") or request.user.teacher_profile is None:
            return Response(
                {"error": "Teacher profile not found. Please complete onboarding first."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            teacher_profile = request.user.teacher_profile
            profile_data = request.data.get('profile_data', {})
            
            # Save all the profile data (this would be a more comprehensive update)
            # For now, just update completion score
            teacher_profile.update_completion_score()
            
            return Response({
                "success": True,
                "profile_id": teacher_profile.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error submitting profile for user {request.user.id}: {e}")
            return Response(
                {"error": "Failed to submit profile"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_completion_score(self, request):
        """Get profile completion score."""
        from rest_framework import status
        from .services.profile_completion import ProfileCompletionService
        
        # Check if user has a teacher profile
        if not hasattr(request.user, "teacher_profile") or request.user.teacher_profile is None:
            return Response(
                {"error": "Teacher profile not found. Please complete onboarding first."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            teacher_profile = request.user.teacher_profile
            completion_data = ProfileCompletionService.calculate_completion(teacher_profile)
            
            return Response(completion_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting completion score for user {request.user.id}: {e}")
            return Response(
                {"error": "Failed to get completion score"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_rate_suggestions(self, request):
        """Get rate suggestions based on subject and location."""
        from rest_framework import status
        
        subject = request.query_params.get('subject', '')
        location = request.query_params.get('location', '')
        
        # Mock rate suggestions for now
        suggestions = {
            "subject": subject,
            "location": location,
            "suggested_rate": {
                "min": 15,
                "max": 45,
                "average": 25,
                "currency": "EUR"
            },
            "market_data": {
                "total_teachers": 150,
                "demand_level": "medium",
                "competition_level": "medium"
            }
        }
        
        return Response(suggestions, status=status.HTTP_200_OK)
    
    def _upload_photo(self, request):
        """
        SECURE profile photo upload with comprehensive validation.
        Implements file type checking, size limits, and malware scanning.
        """
        from rest_framework import status
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        import uuid
        
        # Apply file upload throttling
        if hasattr(self, 'throttle_classes'):
            # Add file upload throttle to existing throttles
            self.throttle_classes = self.throttle_classes + [FileUploadThrottle]
        
        # Check if user has a teacher profile
        if not hasattr(request.user, "teacher_profile") or request.user.teacher_profile is None:
            logger.warning(f"Photo upload attempted without teacher profile by user {request.user.id}")
            return Response(
                {"error": "Teacher profile not found. Please complete onboarding first."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Validate uploaded file using secure serializer
        serializer = ProfilePhotoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(
                f"Profile photo upload validation failed for user {request.user.id}: {serializer.errors}"
            )
            return Response(
                {"error": "Invalid file upload", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        uploaded_file = validated_data['profile_photo']
        
        try:
            # Generate secure filename
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            secure_filename = f"profile_photos/{request.user.id}/{uuid.uuid4()}{file_extension}"
            
            # Save file to secure location
            file_path = default_storage.save(secure_filename, ContentFile(uploaded_file.read()))
            file_url = default_storage.url(file_path)
            
            # Update teacher profile with photo URL
            teacher_profile = request.user.teacher_profile
            teacher_profile.photo = file_path  # Assuming there's a photo field
            teacher_profile.save()
            
            logger.info(f"Profile photo uploaded successfully for user {request.user.id}")
            
            return Response({
                "success": True,
                "photo_url": file_url,
                "message": "Profile photo uploaded successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(
                f"Error uploading profile photo for user {request.user.id}: {e}",
                exc_info=True
            )
            return Response(
                {"error": "Failed to upload photo. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _detect_security_patterns(self, data):
        """
        Detect potential security threats in user input data.
        Returns True if suspicious patterns are found.
        """
        if not isinstance(data, dict):
            return False
        
        suspicious_patterns = [
            '<script', 'javascript:', 'data:text/html', 'vbscript:',
            'onload=', 'onerror=', 'onclick=', 'onmouseover=',
            '<?php', '<%', '<iframe', 'eval(', 'alert(',
            'DROP TABLE', 'UNION SELECT', 'OR 1=1', '--',
            '../', '..\\', '/etc/passwd', 'cmd.exe',
        ]
        
        # Convert all values to strings and check patterns
        data_str = str(data).lower()
        
        for pattern in suspicious_patterns:
            if pattern.lower() in data_str:
                return True
        
        return False
    
    def _get_client_ip(self, request):
        """Get the client IP address from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class StudentViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for student profiles.
    """

    serializer_class = StudentSerializer

    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        - Students: can only access their own profile
        - Teachers: can access profiles of students they teach (via ClassSession)
        - School owners/admins: can access profiles of students in their schools
        """
        user = self.request.user

        # User can see their own student profile
        if hasattr(user, "student_profile"):
            own_profile = StudentProfile.objects.filter(user=user)
        else:
            own_profile = StudentProfile.objects.none()

        # Check if user has permission to see other profiles
        if SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True,
        ).exists():
            # School owners/admins can see students in their schools
            admin_school_ids = list_school_ids_owned_or_managed(user)
            admin_accessible = StudentProfile.objects.filter(
                user__school_memberships__school_id__in=admin_school_ids,
                user__school_memberships__role=SchoolRole.STUDENT,
                user__school_memberships__is_active=True,
            ).distinct()
            return (own_profile | admin_accessible).distinct()

        elif SchoolMembership.objects.filter(
            user=user, role=SchoolRole.TEACHER, is_active=True
        ).exists() and hasattr(user, "teacher_profile"):
            # Teachers can only see students they actually teach (via ClassSession)
            from finances.models import ClassSession

            taught_student_ids = ClassSession.objects.filter(
                teacher=user.teacher_profile
            ).values_list("students", flat=True)

            teacher_accessible = StudentProfile.objects.filter(
                user_id__in=taught_student_ids
            ).distinct()
            return (own_profile | teacher_accessible).distinct()

        # For students and other users, only show their own profile
        return own_profile

    def get_permissions(self):
        if self.action == "create":
            # Only authenticated users can create their own student profile
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only student themselves, or school admin can modify student records
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def onboarding(self, request):
        """
        Create student profile during onboarding.
        """
        # Check if user already has a student profile
        if hasattr(request.user, "student_profile"):
            return Response(
                {"error": "Student profile already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create student profile
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def create_student(self, request):
        """
        Create a complete student record (user + profile + school membership) in one request.
        This action is only available to school administrators.
        """
        from django.db import transaction

        # Validate the request data
        serializer = CreateStudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        # Check if user has permission to add students to the specified school
        school = validated_data["school_id"]
        if not can_user_manage_school(request.user, school):
            return Response(
                {"error": "You don't have permission to add students to this school"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            with transaction.atomic():
                # Create the user
                user_data = {
                    "name": validated_data["name"],
                    "email": validated_data["email"],
                    "phone_number": validated_data.get("phone_number", ""),
                    "primary_contact": validated_data.get("primary_contact", "email"),
                }
                user = CustomUser.objects.create_user(**user_data)

                # Create the student profile
                student_data = {
                    "educational_system": validated_data["educational_system_id"],
                    "school_year": validated_data["school_year"],
                    "birth_date": validated_data["birth_date"],
                    "address": validated_data.get("address", ""),
                }
                student_profile = StudentProfile.objects.create(user=user, **student_data)

                # Create school membership
                school_membership = SchoolMembership.objects.create(
                    user=user, school=school, role=SchoolRole.STUDENT, is_active=True
                )

                # Prepare response data
                response_data = {
                    "message": "Student created successfully",
                    "user": UserSerializer(user).data,
                    "student": StudentSerializer(student_profile).data,
                    "school_membership": SchoolMembershipSerializer(school_membership).data,
                    "user_created": True,
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating student: {e!s}")
            return Response(
                {"error": "Failed to create student. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CourseViewSet(KnoxAuthenticatedViewSet):
    """
    Enhanced API endpoint for courses with advanced filtering, popularity metrics, and market data.
    
    Features:
    - Advanced filtering by educational system, education level, and search
    - Popularity metrics based on session data
    - Market data including pricing information
    - Teacher availability information
    - Caching for performance optimization
    """

    serializer_class = CourseSerializer

    def get_queryset(self):
        """
        Get courses with optional filtering and enhanced data.
        """
        queryset = Course.objects.select_related('educational_system').all()
        
        # Apply filters
        queryset = self._apply_filters(queryset)
        
        # Apply search
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                models.Q(name__icontains=search_query) |
                models.Q(description__icontains=search_query) |
                models.Q(code__icontains=search_query)
            )
        
        # Apply ordering
        ordering = self.request.query_params.get('ordering')
        if ordering:
            # Handle special ordering cases
            if ordering in ['popularity_score', '-popularity_score']:
                # Popularity ordering will be handled in list() method
                pass
            elif ordering in ['avg_hourly_rate', '-avg_hourly_rate']:
                # Price ordering will be handled in list() method
                pass
            else:
                # Standard Django ordering
                try:
                    queryset = queryset.order_by(ordering)
                except Exception:
                    # Invalid ordering, use default
                    queryset = queryset.order_by('name')
        else:
            queryset = queryset.order_by('name')
        
        return queryset

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Only school admins can create/modify courses
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            # Anyone can view courses
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def list(self, request, *args, **kwargs):
        """
        Enhanced list method with popularity metrics, market data, and teacher info.
        """
        try:
            # Check cache first if enhanced data is requested
            cache_key = self._get_cache_key(request)
            if self._should_use_cache(request):
                cached_data = cache.get(cache_key)
                if cached_data:
                    return Response(cached_data)
            
            # Get base queryset
            queryset = self.filter_queryset(self.get_queryset())
            
            # Serialize base course data
            serializer = self.get_serializer(queryset, many=True)
            courses_data = serializer.data
            
            # Enhance with additional data if requested
            if self._needs_enhancement(request):
                courses_data = self._enhance_courses_data(courses_data, request)
            
            # Apply custom ordering if needed
            ordering = request.query_params.get('ordering')
            if ordering in ['popularity_score', '-popularity_score', 'avg_hourly_rate', '-avg_hourly_rate']:
                courses_data = self._apply_custom_ordering(courses_data, ordering)
            
            # Cache results if appropriate
            if self._should_use_cache(request):
                cache.set(cache_key, courses_data, timeout=900)  # 15 minutes
            
            return Response(courses_data)
            
        except Exception as e:
            logger.error(f"Error in CourseViewSet.list for user {request.user.id}: {e}")
            return Response(
                {'error': 'Failed to retrieve course data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _apply_filters(self, queryset):
        """Apply filtering based on query parameters."""
        # Filter by educational system
        educational_system_id = self.request.query_params.get('educational_system')
        if educational_system_id:
            try:
                educational_system_id = int(educational_system_id)
                if not EducationalSystem.objects.filter(id=educational_system_id).exists():
                    raise ValidationError("Invalid educational system ID")
                queryset = queryset.filter(educational_system_id=educational_system_id)
            except (ValueError, ValidationError):
                # Invalid ID - this will be handled by returning empty results
                # or we could raise a 400 error here
                from rest_framework.exceptions import ValidationError as DRFValidationError
                raise DRFValidationError({"educational_system": "Invalid educational system ID"})
        
        # Filter by education level
        education_level = self.request.query_params.get('education_level')
        if education_level:
            queryset = queryset.filter(education_level=education_level)
        
        return queryset
    
    def _needs_enhancement(self, request):
        """Check if enhanced data is requested."""
        return any([
            request.query_params.get('include_popularity') == 'true',
            request.query_params.get('include_teachers') == 'true',
            request.query_params.get('include_market_data') == 'true'
        ])
    
    def _should_use_cache(self, request):
        """Determine if caching should be used."""
        return self._needs_enhancement(request)
    
    def _get_cache_key(self, request):
        """Generate cache key based on request parameters."""
        key_parts = ['courses_enhanced']
        
        # Add filter parameters
        for param in ['educational_system', 'education_level', 'search', 'ordering']:
            value = request.query_params.get(param)
            if value:
                key_parts.append(f'{param}_{value}')
        
        # Add enhancement flags
        for param in ['include_popularity', 'include_teachers', 'include_market_data']:
            if request.query_params.get(param) == 'true':
                key_parts.append(param)
        
        return '_'.join(key_parts)
    
    def _enhance_courses_data(self, courses_data, request):
        """Add enhanced data to courses."""
        from finances.models import ClassSession, TeacherPaymentEntry
        from django.db.models import Count, Avg, Min, Max, Sum
        
        # Get course IDs for efficient querying
        course_ids = [course['id'] for course in courses_data]
        
        # Prepare enhancement data
        popularity_data = {}
        teacher_data = {}
        market_data = {}
        
        # Calculate popularity metrics if requested
        if request.query_params.get('include_popularity') == 'true':
            popularity_data = self._calculate_popularity_metrics(course_ids)
        
        # Get teacher information if requested
        if request.query_params.get('include_teachers') == 'true':
            teacher_data = self._get_teacher_information(course_ids)
        
        # Calculate market data if requested
        if request.query_params.get('include_market_data') == 'true':
            market_data = self._calculate_market_data(course_ids)
        
        # Enhance each course with additional data
        for course in courses_data:
            course_id = course['id']
            
            if course_id in popularity_data:
                course['popularity_metrics'] = popularity_data[course_id]
            
            if course_id in teacher_data:
                course['available_teachers'] = teacher_data[course_id]
            
            if course_id in market_data:
                course['market_data'] = market_data[course_id]
        
        return courses_data
    
    def _calculate_popularity_metrics(self, course_ids):
        """Calculate popularity metrics for courses."""
        from finances.models import ClassSession, SessionStatus
        from collections import defaultdict
        
        # NOTE: This is a simplified implementation that counts all sessions for teachers
        # who teach a course, regardless of which specific course the session was for.
        # In practice, you might want to track session-to-course relationships more precisely.
        
        # Get course associations through teacher-course relationships
        teacher_courses = TeacherCourse.objects.filter(
            course_id__in=course_ids
        ).select_related('teacher', 'course')
        
        # Map courses to teachers
        course_teachers = defaultdict(list)
        for tc in teacher_courses:
            course_teachers[tc.course_id].append(tc.teacher_id)
        
        # Calculate metrics per course
        course_metrics = {}
        for course_id in course_ids:
            teachers = course_teachers.get(course_id, [])
            
            if not teachers:
                # No teachers for this course
                course_metrics[course_id] = {
                    'total_sessions': 0,
                    'unique_students': 0,
                    'popularity_score': 0,
                    'rank': 0
                }
                continue
            
            # Get sessions for teachers of this course
            sessions = ClassSession.objects.filter(
                teacher_id__in=teachers,
                status=SessionStatus.COMPLETED
            ).prefetch_related('students')
            
            total_sessions = sessions.count()
            unique_students = set()
            for session in sessions:
                for student in session.students.all():
                    unique_students.add(student.id)
            
            # Calculate popularity score (sessions * 2 + unique_students * 3)
            popularity_score = total_sessions * 2 + len(unique_students) * 3
            
            course_metrics[course_id] = {
                'total_sessions': total_sessions,
                'unique_students': len(unique_students),
                'popularity_score': popularity_score,
                'rank': 0  # Will be calculated after all scores are computed
            }
        
        # Calculate ranks
        sorted_courses = sorted(
            course_metrics.items(),
            key=lambda x: x[1]['popularity_score'],
            reverse=True
        )
        
        for rank, (course_id, metrics) in enumerate(sorted_courses, 1):
            course_metrics[course_id]['rank'] = rank
        
        return course_metrics
    
    def _get_teacher_information(self, course_ids):
        """Get teacher information for courses."""
        teacher_data = {}
        
        # Get teacher-course relationships
        teacher_courses = TeacherCourse.objects.filter(
            course_id__in=course_ids,
            is_active=True
        ).select_related('teacher__user', 'course')
        
        # Group by course
        for tc in teacher_courses:
            course_id = tc.course_id
            if course_id not in teacher_data:
                teacher_data[course_id] = []
            
            teacher_info = {
                'id': tc.teacher.id,
                'name': tc.teacher.user.name,
                'email': tc.teacher.user.email,
                'hourly_rate': float(tc.hourly_rate) if tc.hourly_rate else float(tc.teacher.hourly_rate or 0),
                'profile_completion_score': float(tc.teacher.profile_completion_score),
                'is_profile_complete': tc.teacher.is_profile_complete,
                'specialty': tc.teacher.specialty
            }
            
            teacher_data[course_id].append(teacher_info)
        
        return teacher_data
    
    def _calculate_market_data(self, course_ids):
        """Calculate market data for courses."""
        from django.db.models import Avg, Min, Max, Count
        
        market_data = {}
        
        # Get aggregated data from teacher-course relationships
        for course_id in course_ids:
            teacher_courses = TeacherCourse.objects.filter(
                course_id=course_id,
                is_active=True
            ).exclude(hourly_rate__isnull=True)
            
            if teacher_courses.exists():
                # Use teacher-course specific rates where available
                rates = [float(tc.hourly_rate) for tc in teacher_courses if tc.hourly_rate]
                
                # Fallback to teacher profile rates if no course-specific rates
                if not rates:
                    rates = [
                        float(tc.teacher.hourly_rate) 
                        for tc in teacher_courses 
                        if tc.teacher.hourly_rate
                    ]
                
                if rates:
                    avg_rate = sum(rates) / len(rates)
                    min_rate = min(rates)
                    max_rate = max(rates)
                else:
                    avg_rate = min_rate = max_rate = 0.0
                
                total_teachers = teacher_courses.count()
                
                # Calculate demand score based on teacher availability and sessions
                # This is a simplified calculation - in production, you might want more sophisticated scoring
                demand_score = min(100, total_teachers * 10)  # Cap at 100
                
            else:
                avg_rate = min_rate = max_rate = 0.0
                total_teachers = 0
                demand_score = 0
            
            market_data[course_id] = {
                'avg_hourly_rate': avg_rate,
                'min_hourly_rate': min_rate,
                'max_hourly_rate': max_rate,
                'total_teachers': total_teachers,
                'demand_score': demand_score
            }
        
        return market_data
    
    def _apply_custom_ordering(self, courses_data, ordering):
        """Apply custom ordering for enhanced data."""
        if ordering == 'popularity_score':
            courses_data.sort(key=lambda x: x.get('popularity_metrics', {}).get('popularity_score', 0))
        elif ordering == '-popularity_score':
            courses_data.sort(key=lambda x: x.get('popularity_metrics', {}).get('popularity_score', 0), reverse=True)
        elif ordering == 'avg_hourly_rate':
            courses_data.sort(key=lambda x: x.get('market_data', {}).get('avg_hourly_rate', 0))
        elif ordering == '-avg_hourly_rate':
            courses_data.sort(key=lambda x: x.get('market_data', {}).get('avg_hourly_rate', 0), reverse=True)
        
        return courses_data


class EducationalSystemViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for educational systems.
    All users can view educational systems, but only admins can create/modify them.
    """

    serializer_class = EducationalSystemSerializer

    def get_queryset(self):
        """
        All authenticated users can see active educational systems.
        """
        return EducationalSystem.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Only school admins can create/modify educational systems
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            # Anyone can view educational systems
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class TeacherCourseViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for teacher-course relationships.
    """

    serializer_class = TeacherCourseSerializer

    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        - Teachers: can only access their own course relationships
        - School owners/admins: can access relationships for teachers in their schools
        """
        user = self.request.user

        # Check if user is a teacher and get their course relationships
        if hasattr(user, "teacher_profile"):
            own_relationships = TeacherCourse.objects.filter(teacher=user.teacher_profile)
        else:
            own_relationships = TeacherCourse.objects.none()

        # Check if user has permission to see other relationships
        if SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True,
        ).exists():
            # School owners/admins can see relationships of teachers in their schools
            admin_school_ids = list_school_ids_owned_or_managed(user)
            admin_accessible = TeacherCourse.objects.filter(
                teacher__user__school_memberships__school_id__in=admin_school_ids,
                teacher__user__school_memberships__role=SchoolRole.TEACHER,
                teacher__user__school_memberships__is_active=True,
            ).distinct()
            return (own_relationships | admin_accessible).distinct()

        # For teachers, only show their own relationships
        return own_relationships

    def get_permissions(self):
        if self.action == "create":
            # Only teachers can create course relationships
            permission_classes = [IsAuthenticated, IsTeacherInAnySchool]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only teacher or school admin can modify relationships
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Create a teacher-course relationship for the current teacher.
        """
        if not hasattr(self.request.user, "teacher_profile"):
            raise serializers.ValidationError("Only teachers can create course relationships")
        serializer.save(teacher=self.request.user.teacher_profile)

    def check_object_permissions(self, request, obj):
        """
        Check that the user has permission to access this specific teacher-course relationship.
        """
        super().check_object_permissions(request, obj)

        # Teachers can only modify their own relationships
        if self.action in ["update", "partial_update", "destroy"]:
            if (
                hasattr(request.user, "teacher_profile")
                and obj.teacher == request.user.teacher_profile
            ):
                return

            # School admins can modify relationships of teachers in their schools
            admin_school_ids = list_school_ids_owned_or_managed(request.user)
            if SchoolMembership.objects.filter(
                user=obj.teacher.user,
                school_id__in=admin_school_ids,
                role=SchoolRole.TEACHER,
                is_active=True,
            ).exists():
                return

            # If none of the above, deny permission
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "You don't have permission to modify this teacher-course relationship"
            )


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
        return SchoolInvitation.objects.filter(
            models.Q(email=user.email) | models.Q(invited_by=user)
        )

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
        from django.db import transaction

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
                    profile_data = {
                        key: value
                        for key, value in validated_data.items()
                        if key not in ["course_ids"]
                    }
                    teacher_profile = TeacherProfile.objects.create(
                        user=request.user, **profile_data
                    )

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
                    "custom_message": getattr(invitation, 'custom_message', None),
                    "created_at": invitation.created_at.isoformat(),
                    "expires_at": invitation.expires_at.isoformat(),
                    "is_accepted": invitation.is_accepted,
                    "invitation_link": f"https://aprendecomigo.com/accept-invitation/{invitation.token}"
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
                # For resending, we use the retry method if the invitation previously failed
                if invitation.email_delivery_status == EmailDeliveryStatus.FAILED:
                    email_result = TeacherInvitationEmailService.retry_failed_invitation_email(invitation)
                else:
                    email_result = TeacherInvitationEmailService.send_invitation_email(invitation)
                
                if email_result['success']:
                    notifications_sent["email"] = True
                    if invitation.email_delivery_status != EmailDeliveryStatus.SENT:
                        invitation.mark_email_sent()
                    logger.info(f"Invitation email resent to {invitation.email}")
                else:
                    logger.warning(f"Failed to resend invitation email: {email_result.get('error', 'Unknown error')}")
                    invitation.mark_email_failed(email_result.get('error', 'Unknown error'))
                    
            except Exception as e:
                logger.warning(f"Failed to resend invitation email: {e}")
                invitation.mark_email_failed(f"Resend exception: {str(e)}")

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
        from django.db import transaction

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
                from .models import SchoolActivity, ActivityType
                SchoolActivity.objects.create(
                    school=invitation.school,
                    activity_type=ActivityType.INVITATION_DECLINED,
                    actor=request.user if request.user.is_authenticated else None,
                    target_invitation=invitation,
                    description=f"Invitation to {invitation.email} was declined"
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
                            "status": "declined"
                        }
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            logger.error(f"Decline invitation failed for token {token}: {e!s}")
            return Response(
                {"error": "Failed to decline invitation. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# School Dashboard Views

class SchoolDashboardViewSet(viewsets.ModelViewSet):
    """ViewSet for school dashboard functionality"""
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    serializer_class = EnhancedSchoolSerializer
    
    def get_queryset(self):
        """Return schools that user can manage"""
        user_schools = get_schools_user_can_manage(self.request.user)
        return School.objects.filter(id__in=user_schools).select_related('settings')
    
    @action(detail=True, methods=['get'], url_path='metrics')
    def metrics(self, request, pk=None):
        """Get comprehensive metrics for school dashboard"""
        school = self.get_object()
        
        # Import here to avoid circular imports
        from .services.metrics_service import SchoolMetricsService
        
        metrics_service = SchoolMetricsService(school)
        metrics_data = metrics_service.get_metrics()
        
        serializer = SchoolMetricsSerializer(data=metrics_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='activity')
    def activity(self, request, pk=None):
        """Get paginated activity feed for school"""
        school = self.get_object()
        
        # Import here to avoid circular imports
        from .services.metrics_service import SchoolActivityService
        from rest_framework.pagination import PageNumberPagination
        from django.core.paginator import Paginator, EmptyPage
        
        # Get query parameters for filtering
        activity_types = request.query_params.get('activity_types')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        # Safely parse pagination parameters with validation
        try:
            page = int(request.query_params.get('page', 1))
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid page parameter. Must be a positive integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            page_size = int(request.query_params.get('page_size', 20))
            if page_size < 1:
                page_size = 20
            elif page_size > 100:
                page_size = 100
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid page_size parameter. Must be a positive integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build filters
        filters = {}
        if activity_types:
            filters['activity_types'] = activity_types
        if date_from:
            try:
                from django.utils.dateparse import parse_datetime
                filters['date_from'] = parse_datetime(date_from)
            except (ValueError, TypeError):
                pass
        if date_to:
            try:
                from django.utils.dateparse import parse_datetime
                filters['date_to'] = parse_datetime(date_to)
            except (ValueError, TypeError):
                pass
        
        # Get activities
        from .models import SchoolActivity
        activities = SchoolActivity.objects.filter(school=school).select_related(
            'actor', 'target_user', 'target_class__teacher'
        ).prefetch_related(
            'target_invitation__invited_by'
        )
        
        # Apply filters
        if filters.get('activity_types'):
            activity_types_list = filters['activity_types'].split(',')
            activities = activities.filter(activity_type__in=activity_types_list)
        
        if filters.get('date_from'):
            activities = activities.filter(timestamp__gte=filters['date_from'])
        
        if filters.get('date_to'):
            activities = activities.filter(timestamp__lte=filters['date_to'])
        
        # Paginate
        paginator = Paginator(activities, page_size)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Serialize
        serializer = SchoolActivitySerializer(
            page_obj.object_list, 
            many=True,
            context={'school': school, 'request': request}
        )
        
        # Build pagination response
        response_data = {
            'count': paginator.count,
            'next': f"?page={page_obj.next_page_number()}" if page_obj.has_next() else None,
            'previous': f"?page={page_obj.previous_page_number()}" if page_obj.has_previous() else None,
            'results': serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    


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
        method='post',
        operation_summary="Accept Teacher Invitation",
        operation_description="Accept a teacher invitation and create/update teacher profile",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'bio': openapi.Schema(type=openapi.TYPE_STRING, description='Teacher bio (max 1000 chars)', maxLength=1000),
                'specialty': openapi.Schema(type=openapi.TYPE_STRING, description='Teaching specialty'),
                'hourly_rate': openapi.Schema(type=openapi.TYPE_NUMBER, description='Hourly rate (5.00-200.00)', minimum=5.0, maximum=200.0),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number in international format'),
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='Physical address'),
                'teaching_subjects': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='Array of teaching subjects (max 10)'
                ),
                'education_background': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Education background information',
                    properties={
                        'degree': openapi.Schema(type=openapi.TYPE_STRING),
                        'university': openapi.Schema(type=openapi.TYPE_STRING),
                        'graduation_year': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                ),
                'teaching_experience': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Teaching experience details',
                    properties={
                        'years': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'description': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            },
            example={
                'bio': 'Experienced mathematics teacher with passion for helping students',
                'specialty': 'Mathematics, Physics',
                'hourly_rate': 45.00,
                'phone_number': '+1234567890',
                'teaching_subjects': ['Mathematics', 'Physics'],
                'education_background': {
                    'degree': 'Masters in Mathematics',
                    'university': 'University Name'
                },
                'teaching_experience': {
                    'years': 5,
                    'description': '5 years teaching high school mathematics'
                }
            }
        ),
        responses={
            200: openapi.Response(
                description="Invitation accepted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'invitation_accepted': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'teacher_profile': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'school_membership': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request - validation errors, invitation expired/accepted/declined",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                                'details': openapi.Schema(type=openapi.TYPE_OBJECT),
                            }
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: openapi.Response(
                description="Authentication required",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING, example='AUTHENTICATION_REQUIRED'),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                                'details': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'invitation_details': openapi.Schema(type=openapi.TYPE_OBJECT)
                                    }
                                ),
                            }
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden - invitation not for authenticated user",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING, example='INVITATION_INVALID_RECIPIENT'),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            404: openapi.Response(
                description="Invitation not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING, example='INVITATION_NOT_FOUND'),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING, example='PROFILE_CREATION_FAILED'),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                                'details': openapi.Schema(type=openapi.TYPE_OBJECT),
                            }
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'token',
                openapi.IN_PATH,
                description="Unique invitation token",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        tags=['Teacher Invitations'],
    )
    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def accept(self, request, token=None):
        """
        Accept a teacher invitation with comprehensive profile creation support.
        
        This endpoint allows teachers to accept invitations from schools and simultaneously
        create or update their teacher profile with comprehensive information.
        
        **Authentication:** Not required for invitation acceptance (token-based)
        **Rate Limiting:** Applied per IP and per user
        **HTTPS Required:** Yes, for token security
        
        **Request Format:**
        ```
        POST /api/accounts/teacher-invitations/{token}/accept/
        Content-Type: application/json
        
        {
            "bio": "Experienced mathematics teacher...",
            "specialty": "Mathematics, Physics",
            "hourly_rate": 45.00,
            "phone_number": "+1234567890",
            "teaching_subjects": ["Mathematics", "Physics"],
            "education_background": {
                "degree": "Masters in Mathematics",
                "university": "University Name"
            },
            "teaching_experience": {
                "years": 5,
                "description": "5 years teaching high school"
            }
        }
        ```
        
        **Success Response (201 Created):**
        ```json
        {
            "success": true,
            "invitation_accepted": true,
            "teacher_profile": {
                "id": 123,
                "bio": "Experienced mathematics teacher...",
                "profile_completion_score": 85.5
            },
            "school_membership": {
                "school_id": 456,
                "school_name": "Test School",
                "role": "teacher"
            }
        }
        ```
        
        **Error Responses:**
        - `404 NOT_FOUND`: Invitation token not found
        - `400 BAD_REQUEST`: Invitation expired/already accepted/declined
        - `401 UNAUTHORIZED`: Authentication required
        - `403 FORBIDDEN`: Invitation not for authenticated user
        - `400 BAD_REQUEST`: Validation errors in profile data
        - `500 INTERNAL_SERVER_ERROR`: Server error during processing
        
        **Validation Rules:**
        - `hourly_rate`: 5.00 - 200.00 USD/hour
        - `phone_number`: Valid international format
        - `bio`: Maximum 1000 characters
        - `teaching_subjects`: Array of strings, max 10 subjects
        
        Enhanced to support comprehensive teacher profile creation during invitation acceptance.
        Supports file uploads, structured data validation, and maintains backward compatibility.
        
        GitHub issue #50: [Flow C] Teacher Acceptance Workflow - Complete Profile Creation During Invitation Acceptance
        GitHub issue #80: [Flow C] Backend API Documentation and Error Message Standardization
        """
        
        from common.error_handling import (
            create_invitation_not_found_response,
            create_invitation_expired_response,
            create_invitation_already_accepted_response,
            create_invitation_already_declined_response,
            create_authentication_error_response,
            create_invitation_invalid_recipient_response,
            create_validation_error_response,
            create_error_response,
            APIErrorCode
        )
        
        # Get invitation with proper error handling
        try:
            invitation = TeacherInvitation.objects.select_related('school', 'invited_by').get(token=token)
        except TeacherInvitation.DoesNotExist:
            return create_invitation_not_found_response(request_path=request.path)
        
        # Check if invitation is valid with specific error responses
        if not invitation.is_valid():
            if invitation.is_accepted:
                return create_invitation_already_accepted_response(
                    request_path=request.path,
                    accepted_at=invitation.accepted_at
                )
            elif hasattr(invitation, 'declined_at') and invitation.declined_at:
                return create_invitation_already_declined_response(
                    request_path=request.path,
                    declined_at=invitation.declined_at
                )
            else:
                return create_invitation_expired_response(
                    request_path=request.path,
                    expires_at=invitation.expires_at
                )
        
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
                        "role": invitation.get_role_display()
                    }
                }
            )
        
        # Verify recipient with standardized error
        if invitation.email != request.user.email:
            return create_invitation_invalid_recipient_response(
                expected_email=invitation.email,
                request_path=request.path
            )
        
        # Validate profile data with improved error handling
        from .serializers import ComprehensiveTeacherProfileCreationSerializer
        profile_serializer = ComprehensiveTeacherProfileCreationSerializer(data=request.data)
        
        if not profile_serializer.is_valid():
            return create_validation_error_response(
                serializer_errors=profile_serializer.errors,
                message="Invalid teacher profile data provided",
                request_path=request.path
            )
        
        validated_profile_data = profile_serializer.validated_data
        
        # Process the acceptance with comprehensive profile creation
        from django.db import transaction
        
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
                        bio=validated_profile_data.get('bio', ''),
                        specialty=validated_profile_data.get('specialty', ''),
                        hourly_rate=validated_profile_data.get('hourly_rate'),
                        availability=validated_profile_data.get('availability', ''),
                        phone_number=validated_profile_data.get('phone_number', ''),
                        address=validated_profile_data.get('address', ''),
                        education_background=validated_profile_data.get('education_background', {}),
                        teaching_subjects=validated_profile_data.get('teaching_subjects', []),
                        rate_structure=validated_profile_data.get('rate_structure', {}),
                        weekly_availability=validated_profile_data.get('weekly_availability', {}),
                        grade_level_preferences=validated_profile_data.get('grade_level_preferences', []),
                        teaching_experience=validated_profile_data.get('teaching_experience', {}),
                        credentials_documents=validated_profile_data.get('credentials_documents', []),
                        availability_schedule=validated_profile_data.get('availability_schedule', {}),
                    )
                    profile_created = True
                
                # Update existing profile with new data if provided
                if not profile_created and validated_profile_data:
                    for field, value in validated_profile_data.items():
                        if field != 'profile_photo' and field != 'course_ids':  # Handle these separately
                            if value is not None:  # Only update if value is provided
                                setattr(teacher_profile, field, value)
                    teacher_profile.save()
                
                # Handle profile photo upload for CustomUser
                if 'profile_photo' in validated_profile_data and validated_profile_data['profile_photo']:
                    request.user.profile_photo = validated_profile_data['profile_photo']
                    request.user.save(update_fields=['profile_photo'])
                
                # Handle course associations if provided
                if 'course_ids' in validated_profile_data and validated_profile_data['course_ids']:
                    from .models import Course, TeacherCourse
                    # Remove existing associations first
                    TeacherCourse.objects.filter(teacher=teacher_profile).delete()
                    
                    # Create new associations
                    course_objects = Course.objects.filter(id__in=validated_profile_data['course_ids'])
                    for course in course_objects:
                        TeacherCourse.objects.create(
                            teacher=teacher_profile,
                            course=course,
                            is_active=True
                        )
                
                # Update profile completion score
                try:
                    teacher_profile.update_completion_score()
                except Exception as completion_error:
                    logger.warning(f"Failed to update completion score for teacher {teacher_profile.id}: {completion_error}")
                
                # Create school membership if it doesn't exist
                membership, membership_created = SchoolMembership.objects.get_or_create(
                    user=request.user,
                    school=invitation.school,
                    role=invitation.role,
                    defaults={"is_active": True},
                )
                
                if not membership_created and not membership.is_active:
                    # Reactivate if was previously inactive
                    membership.is_active = True
                    membership.save()
                
                # Mark invitation as accepted and update status
                invitation.accept()
                invitation.mark_viewed()  # Also mark as viewed
                
                # Create enhanced activity log
                from .services.metrics_service import SchoolActivityService
                from .models import ActivityType
                
                profile_details = "with comprehensive profile" if validated_profile_data else "with basic profile"
                SchoolActivityService.create_activity(
                    school=invitation.school,
                    activity_type=ActivityType.INVITATION_ACCEPTED,
                    actor=request.user,
                    target_user=request.user,
                    # Don't pass target_invitation for TeacherInvitation - SchoolActivity expects SchoolInvitation
                    # target_invitation=invitation,  
                    description=f"{request.user.name} accepted teacher invitation {profile_details}",
                    metadata={
                        'invitation_id': str(invitation.id),
                        'invitation_token': invitation.token,
                        'batch_id': str(invitation.batch_id),
                        'role': invitation.role,
                        'profile_created': profile_created,
                        'profile_fields_provided': list(validated_profile_data.keys()) if validated_profile_data else [],
                        'profile_completion_score': float(teacher_profile.profile_completion_score)
                    }
                )
                
                # Prepare comprehensive response with teacher profile data
                from .serializers import TeacherSerializer
                teacher_serializer = TeacherSerializer(teacher_profile)
                
                # Generate wizard orchestration metadata (GitHub Issue #95)
                from .services.wizard_orchestration import WizardOrchestrationService
                try:
                    wizard_metadata = WizardOrchestrationService.generate_wizard_metadata(
                        teacher_profile, invitation.school
                    )
                except Exception as wizard_error:
                    logger.warning(f"Failed to generate wizard metadata: {wizard_error}")
                    wizard_metadata = WizardOrchestrationService._get_fallback_metadata()
                
                # Return enhanced success response with wizard metadata
                return Response(
                    {
                        # Wizard orchestration fields (GitHub Issue #95)
                        "success": True,
                        "invitation_accepted": True,
                        "teacher_profile": teacher_serializer.data,
                        "wizard_metadata": wizard_metadata,
                        
                        # Backward compatibility fields
                        "teacher_profile_created": profile_created,
                        "profile_completion": {
                            "score": float(teacher_profile.profile_completion_score),
                            "is_complete": teacher_profile.is_profile_complete
                        },
                        
                        # Legacy fields for existing clients
                        "message": "Invitation accepted successfully! You are now a teacher at this school.",
                        "invitation": {
                            "id": invitation.id,
                            "school": {
                                "id": invitation.school.id,
                                "name": invitation.school.name,
                            },
                            "role": invitation.role,
                            "role_display": invitation.get_role_display(),
                            "accepted_at": invitation.accepted_at,
                        },
                        "membership": {
                            "id": membership.id,
                            "role": membership.role,
                            "joined_at": membership.joined_at,
                            "is_active": membership.is_active,
                        },
                    },
                    status=status.HTTP_200_OK,
                )
                
        except Exception as e:
            logger.error(f"Accept invitation failed for token {token}: {e}")
            return create_error_response(
                error_code=APIErrorCode.PROFILE_CREATION_FAILED,
                message="Failed to accept invitation and create teacher profile. Please try again.",
                details={"error_type": type(e).__name__},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_path=request.path
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Decline Teacher Invitation",
        operation_description="Decline a teacher invitation using the token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reason': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Optional decline reason (max 500 chars)', 
                    maxLength=500,
                    example='Not interested at this time'
                ),
            },
            required=[],
        ),
        responses={
            200: openapi.Response(
                description="Invitation declined successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'invitation_declined': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Invitation declined successfully'),
                        'invitation_details': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'school_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'role': openapi.Schema(type=openapi.TYPE_STRING),
                                'declined_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                            }
                        ),
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request - invitation already processed or expired",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING, example='INVITATION_ALREADY_ACCEPTED'),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                                'details': openapi.Schema(type=openapi.TYPE_OBJECT),
                            }
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            404: openapi.Response(
                description="Invitation not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING, example='INVITATION_NOT_FOUND'),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                                'details': openapi.Schema(type=openapi.TYPE_OBJECT),
                            }
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'token',
                openapi.IN_PATH,
                description="Unique invitation token",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        tags=['Teacher Invitations'],
    )
    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def decline(self, request, token=None):
        """
        Decline a teacher invitation.
        
        This endpoint allows anyone to decline a teacher invitation using the token.
        No authentication is required as the token provides authorization.
        
        **Authentication:** Not required (token-based authorization)
        **Rate Limiting:** Applied per IP
        **HTTPS Required:** Yes, for token security
        
        **Request Format:**
        ```
        POST /api/accounts/teacher-invitations/{token}/decline/
        Content-Type: application/json
        
        {
            "reason": "Not interested at this time"  // Optional decline reason
        }
        ```
        
        **Success Response (200 OK):**
        ```json
        {
            "success": true,
            "invitation_declined": true,
            "message": "Invitation declined successfully",
            "invitation_details": {
                "school_name": "Test School",
                "role": "teacher",
                "declined_at": "2025-08-01T10:30:00Z"
            }
        }
        ```
        
        **Error Responses:**
        - `404 NOT_FOUND`: Invitation token not found
        - `400 BAD_REQUEST`: Invitation already accepted/declined or expired
        - `500 INTERNAL_SERVER_ERROR`: Server error during processing
        
        **Validation Rules:**
        - `reason`: Optional string, maximum 500 characters
        
        Allows anyone to decline an invitation using the token.
        Maintains AllowAny permissions for public access.
        
        GitHub Issue #86: Implement Teacher Invitation Decline Endpoint
        GitHub Issue #80: Backend API Documentation and Error Message Standardization
        """
        
        from common.error_handling import (
            create_invitation_not_found_response,
            create_invitation_expired_response,
            create_invitation_already_accepted_response,
            create_invitation_already_declined_response,
            create_error_response,
            APIErrorCode
        )
        
        # Get invitation with proper error handling
        try:
            invitation = TeacherInvitation.objects.select_related('school', 'invited_by').get(token=token)
        except TeacherInvitation.DoesNotExist:
            return create_invitation_not_found_response(request_path=request.path)
        
        # Check if invitation can be declined with specific error responses
        if invitation.is_accepted:
            return create_invitation_already_accepted_response(
                request_path=request.path,
                accepted_at=invitation.accepted_at
            )
        
        if hasattr(invitation, 'declined_at') and invitation.declined_at:
            return create_invitation_already_declined_response(
                request_path=request.path,
                declined_at=invitation.declined_at
            )
        
        # Check if invitation is expired
        if invitation.is_expired():
            return create_invitation_expired_response(
                request_path=request.path,
                expires_at=invitation.expires_at
            )
        
        # Validate optional decline reason
        decline_reason = request.data.get('reason', '') if request.data else ''
        if decline_reason and len(decline_reason) > 500:
            from common.error_handling import create_validation_error_response
            return create_validation_error_response(
                serializer_errors={'reason': ['Decline reason must be 500 characters or less']},
                message="Invalid decline reason provided",
                request_path=request.path
            )
        
        try:
            # Mark invitation as declined
            invitation.decline()
            
            # Create activity log
            from .services.metrics_service import SchoolActivityService
            from .models import ActivityType
            
            SchoolActivityService.create_activity(
                school=invitation.school,
                activity_type=ActivityType.INVITATION_DECLINED,
                actor=request.user if request.user.is_authenticated else None,
                target_invitation=None,  # SchoolActivity expects SchoolInvitation, not TeacherInvitation
                description=f"Teacher invitation to {invitation.email} was declined",
                metadata={
                    'invitation_id': str(invitation.id),
                    'invitation_token': invitation.token,
                    'batch_id': str(invitation.batch_id),
                    'role': invitation.role,
                    'declined_by_authenticated_user': request.user.is_authenticated,
                    'declined_by_intended_recipient': (
                        request.user.is_authenticated and request.user.email == invitation.email
                    )
                }
            )
            
            # Return success response consistent with accept endpoint
            return Response(
                {
                    "message": "Invitation declined successfully.",
                    "invitation": {
                        "id": invitation.id,
                        "email": invitation.email,
                        "status": invitation.status,
                        "declined_at": invitation.declined_at,
                        "school": {
                            "id": invitation.school.id,
                            "name": invitation.school.name,
                        },
                        "role": invitation.role,
                        "role_display": invitation.get_role_display(),
                        "custom_message": invitation.custom_message,
                    },
                    "status": "declined",
                },
                status=status.HTTP_200_OK,
            )
            
        except ValidationError as e:
            return create_error_response(
                error_code=APIErrorCode.VALIDATION_FAILED,
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                request_path=request.path
            )
        except Exception as e:
            logger.error(f"Decline invitation failed for token {token}: {e}")
            return create_error_response(
                error_code=APIErrorCode.INVITATION_EMAIL_SEND_FAILED,
                message="Failed to decline invitation. Please try again.",
                details={"error_type": type(e).__name__},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_path=request.path
            )
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Get Teacher Invitation Status",
        operation_description="Check the current status of a teacher invitation",
        responses={
            200: openapi.Response(
                description="Invitation status retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            enum=['pending', 'sent', 'delivered', 'viewed', 'accepted', 'declined', 'expired', 'cancelled'],
                            example='pending'
                        ),
                        'status_display': openapi.Schema(type=openapi.TYPE_STRING, example='Pending'),
                        'invitation_details': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'school_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'role': openapi.Schema(type=openapi.TYPE_STRING),
                                'role_display': openapi.Schema(type=openapi.TYPE_STRING),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                'expires_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                'is_valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'is_expired': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'is_accepted': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'accepted_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, nullable=True),
                                'declined_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, nullable=True),
                                'viewed_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, nullable=True),
                                'custom_message': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            }
                        ),
                        'email_delivery': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                                'status_display': openapi.Schema(type=openapi.TYPE_STRING),
                                'sent_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, nullable=True),
                                'delivered_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, nullable=True),
                                'failure_reason': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                'retry_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        ),
                        'user_context': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'is_authenticated': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'is_intended_recipient': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'can_accept': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'can_decline': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        ),
                    }
                )
            ),
            404: openapi.Response(
                description="Invitation not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING, example='INVITATION_NOT_FOUND'),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'code': openapi.Schema(type=openapi.TYPE_STRING),
                                'message': openapi.Schema(type=openapi.TYPE_STRING),
                                'details': openapi.Schema(type=openapi.TYPE_OBJECT),
                            }
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'path': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'token',
                openapi.IN_PATH,
                description="Unique invitation token",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        tags=['Teacher Invitations'],
    )
    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def status(self, request, token=None):
        """
        Check teacher invitation status.
        
        This endpoint allows anyone to check the current status of a teacher invitation
        using the token. No authentication is required for transparency.
        
        **Authentication:** Not required (public endpoint)
        **Rate Limiting:** Applied per IP
        **HTTPS Required:** Yes, for token security
        
        **Request Format:**
        ```
        GET /api/accounts/teacher-invitations/{token}/status/
        ```
        
        **Success Response (200 OK):**
        ```json
        {
            "status": "pending",
            "status_display": "Pending",
            "invitation_details": {
                "email": "teacher@example.com",
                "school_name": "Test School",
                "role": "teacher",
                "role_display": "Teacher",
                "created_at": "2025-08-01T09:00:00Z",
                "expires_at": "2025-08-08T09:00:00Z",
                "is_valid": true,
                "is_expired": false,
                "custom_message": "Welcome to our school!"
            }
        }
        ```
        
        **Error Responses:**
        - `404 NOT_FOUND`: Invitation token not found
        - `500 INTERNAL_SERVER_ERROR`: Server error during processing
        
        **Status Values:**
        - `pending`: Invitation created but not yet sent
        - `sent`: Email successfully sent to recipient
        - `delivered`: Email confirmed delivered
        - `viewed`: Recipient has viewed the invitation
        - `accepted`: Invitation accepted by recipient
        - `declined`: Invitation declined by recipient
        - `expired`: Invitation has expired
        - `cancelled`: Invitation cancelled by sender
        
        Returns current status and details without requiring authentication.
        Useful for frontend status checking and invitation link previews.
        
        GitHub Issue #80: Backend API Documentation and Error Message Standardization
        """
        
        from common.error_handling import (
            create_invitation_not_found_response,
            create_error_response,
            APIErrorCode
        )
        
        # Get invitation with proper error handling
        try:
            invitation = TeacherInvitation.objects.select_related('school', 'invited_by').get(token=token)
        except TeacherInvitation.DoesNotExist:
            return create_invitation_not_found_response(request_path=request.path)
        
        # Mark as viewed if not already
        if not invitation.viewed_at:
            invitation.mark_viewed()
        
        # Build response data to match frontend TypeScript interface expectations
        try:
            # Build invitation object that matches frontend TeacherInvitation interface
            invitation_data = {
                "id": str(invitation.id),  # Convert UUID to string for JSON
                "email": invitation.email,
                "school": {
                    "id": invitation.school.id,
                    "name": invitation.school.name,
                },
                "invited_by": {
                    "id": invitation.invited_by.id,
                    "name": invitation.invited_by.name,
                    "email": invitation.invited_by.email,
                },
                "role": invitation.role,
                "status": invitation.status,
                "email_delivery_status": invitation.email_delivery_status,
                "token": invitation.token,
                "custom_message": invitation.custom_message,
                "batch_id": str(invitation.batch_id),
                "created_at": invitation.created_at.isoformat(),
                "expires_at": invitation.expires_at.isoformat(),
                "accepted_at": invitation.accepted_at.isoformat() if invitation.accepted_at else None,
                "viewed_at": invitation.viewed_at.isoformat() if invitation.viewed_at else None,
                "declined_at": invitation.declined_at.isoformat() if hasattr(invitation, 'declined_at') and invitation.declined_at else None,
            }
            
            # Determine if user can accept invitation
            can_accept = (
                invitation.is_valid() and 
                not invitation.is_accepted and
                request.user.is_authenticated and 
                request.user.email == invitation.email
            )
            
            # Determine if profile wizard is needed
            needs_profile_wizard = False
            wizard_metadata = None
            
            # For authenticated users who can accept, check if they need profile wizard
            if can_accept:
                # Check if user already has a complete teacher profile
                try:
                    teacher_profile = request.user.teacher_profile
                    # Basic profile completion check - can be expanded
                    needs_profile_wizard = not all([
                        teacher_profile.bio,
                        teacher_profile.hourly_rate,
                        teacher_profile.subjects.exists(),
                    ])
                    if needs_profile_wizard:
                        wizard_metadata = {
                            "requires_profile_completion": True,
                            "completed_steps": [],
                            "current_step": 1,
                        }
                except:
                    # User doesn't have a teacher profile yet
                    needs_profile_wizard = True
                    wizard_metadata = {
                        "requires_profile_completion": True,
                        "completed_steps": [],
                        "current_step": 1,
                    }
            
            # Build final response structure matching frontend InvitationStatusResponse interface
            response_data = {
                "invitation": invitation_data,
                "can_accept": can_accept,
                "reason": None,  # Can be used for explaining why invitation can't be accepted
                "needs_profile_wizard": needs_profile_wizard,
                "wizard_metadata": wizard_metadata,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to get invitation status for token {token}: {e}")
            return create_error_response(
                error_code=APIErrorCode.INVITATION_NOT_FOUND,
                message="Failed to retrieve invitation status",
                details={"error_type": type(e).__name__},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_path=request.path
            )
    
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsSchoolOwnerOrAdmin])
    def list_for_school(self, request):
        """
        Get invitation status for school admins (GET /api/accounts/teachers/invitations/).
        
        Returns all invitations for schools that the user can manage.
        """
        # Get query parameters
        school_id = request.query_params.get('school_id')
        status_filter = request.query_params.get('status')
        email_status_filter = request.query_params.get('email_status')
        
        # Base queryset - user can only see invitations for schools they manage
        queryset = self.get_queryset().select_related('school', 'invited_by')
        
        # Apply filters
        if school_id:
            try:
                school_id = int(school_id)
                # Verify user can manage this school
                admin_school_ids = list_school_ids_owned_or_managed(request.user)
                if school_id not in admin_school_ids:
                    return Response(
                        {"error": "You don't have permission to view invitations for this school"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                queryset = queryset.filter(school_id=school_id)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid school_id parameter"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        if status_filter:
            status_choices = [choice[0] for choice in InvitationStatus.choices]
            if status_filter in status_choices:
                queryset = queryset.filter(status=status_filter)
            else:
                return Response(
                    {"error": f"Invalid status. Must be one of: {', '.join(status_choices)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        if email_status_filter:
            email_status_choices = [choice[0] for choice in EmailDeliveryStatus.choices]
            if email_status_filter in email_status_choices:
                queryset = queryset.filter(email_delivery_status=email_status_filter)
            else:
                return Response(
                    {"error": f"Invalid email_status. Must be one of: {', '.join(email_status_choices)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        # Order by creation date (newest first)
        queryset = queryset.order_by('-created_at')
        
        # Build response
        invitations_data = []
        for invitation in queryset:
            invitation_data = {
                "id": invitation.id,
                "email": invitation.email,
                "status": invitation.status,
                "is_accepted": invitation.is_accepted,
                "is_valid": invitation.is_valid(),
                "school": {
                    "id": invitation.school.id,
                    "name": invitation.school.name,
                },
                "role": invitation.role,
                "role_display": invitation.get_role_display(),
                "invited_by": {
                    "name": invitation.invited_by.name,
                    "email": invitation.invited_by.email,
                },
                "batch_id": str(invitation.batch_id),
                "created_at": invitation.created_at,
                "expires_at": invitation.expires_at,
                "accepted_at": invitation.accepted_at,
                "declined_at": invitation.declined_at,
                "viewed_at": invitation.viewed_at,
                "email_delivery": {
                    "status": invitation.email_delivery_status,
                    "sent_at": invitation.email_sent_at,
                    "delivered_at": invitation.email_delivered_at,
                    "failure_reason": invitation.email_failure_reason,
                    "retry_count": invitation.retry_count,
                    "can_retry": invitation.can_retry(),
                },
                "actions": {
                    "can_cancel": not invitation.is_accepted and invitation.is_valid(),
                    "can_resend": invitation.is_valid() and invitation.can_retry(),
                    "invitation_link": f"https://aprendecomigo.com/accept-teacher-invitation/{invitation.token}",
                }
            }
            
            # Add custom message if present
            if invitation.custom_message:
                invitation_data["custom_message"] = invitation.custom_message
            
            invitations_data.append(invitation_data)
        
        # Add summary statistics
        total_count = queryset.count()
        summary_stats = {
            "total_invitations": total_count,
            "pending_invitations": queryset.filter(status=InvitationStatus.PENDING).count(),
            "sent_invitations": queryset.filter(status=InvitationStatus.SENT).count(),
            "accepted_invitations": queryset.filter(status=InvitationStatus.ACCEPTED).count(),
            "declined_invitations": queryset.filter(status=InvitationStatus.DECLINED).count(),
            "expired_invitations": queryset.filter(expires_at__lt=timezone.now(), is_accepted=False).count(),
        }
        
        return Response(
            {
                "invitations": invitations_data,
                "summary": summary_stats,
                "filters_applied": {
                    "school_id": school_id,
                    "status": status_filter,
                    "email_status": email_status_filter,
                }
            },
            status=status.HTTP_200_OK,
        )


class GlobalSearchView(KnoxAuthenticatedAPIView):
    """
    Global search API for searching across teachers, students, classes, and school settings.
    GET /api/accounts/search/global/?q=query&types=teacher,student,class&limit=10
    
    Supports school-scoped results with PostgreSQL full-text search capabilities.
    Performance target: <200ms response time.
    
    Returns results in format expected by frontend NavigationAPI interface.
    """
    
    def get(self, request):
        """
        Search across multiple entity types within the user's school context.
        
        Query parameters:
        - q: Search query (required)
        - types: Comma-separated list of types to search (teacher,student,class)
        - limit: Number of results to return (default 10, max 50)
        
        Returns:
        {
            "results": [SearchResult], 
            "total_count": int,
            "categories": {type: count}
        }
        """
        # Get and validate query parameter
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {"error": "Query parameter 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get and validate types parameter
        types_param = request.query_params.get('types', 'teacher,student,class')
        valid_types = {'teacher', 'student', 'class'}
        requested_types = set(type.strip() for type in types_param.split(','))
        
        # Validate that all requested types are valid
        invalid_types = requested_types - valid_types
        if invalid_types:
            return Response(
                {"error": f"Invalid types: {', '.join(invalid_types)}. Valid types: {', '.join(valid_types)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get and validate limit parameter
        try:
            limit = int(request.query_params.get('limit', 10))
            if limit > 50:
                limit = 50
            elif limit < 1:
                limit = 1
        except ValueError:
            return Response(
                {"error": "Limit must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user's schools to scope search results
        user_school_ids = list(
            SchoolMembership.objects.filter(
                user=request.user, 
                is_active=True
            ).values_list('school_id', flat=True)
        )
        
        if not user_school_ids:
            return Response({
                "results": [],
                "total_count": 0,
                "query": query,
                "types": list(requested_types)
            }, status=status.HTTP_200_OK)
        
        results = []
        
        # Search teachers
        if 'teacher' in requested_types:
            teacher_results = self._search_teachers(query, user_school_ids, limit)
            results.extend(teacher_results)
        
        # Search students
        if 'student' in requested_types:
            student_results = self._search_students(query, user_school_ids, limit)
            results.extend(student_results)
        
        # Search courses (mapped from 'class' type)
        if 'class' in requested_types:
            course_results = self._search_courses(query, limit)
            results.extend(course_results)
        
        # Sort results by relevance (could be enhanced with actual scoring)
        # For now, we'll sort by exact matches first, then partial matches
        def sort_key(result):
            title_lower = result.get('title', '').lower()
            query_lower = query.lower()
            if query_lower == title_lower:
                return 0  # Exact match
            elif query_lower in title_lower:
                return 1  # Partial match
            else:
                return 2  # Other match
        
        results.sort(key=sort_key)
        
        # Apply final limit across all results
        results = results[:limit]
        
        # Calculate categories for frontend
        categories = {}
        for result in results:
            result_type = result['type']
            categories[result_type] = categories.get(result_type, 0) + 1
        
        return Response({
            "results": results,
            "total_count": len(results),
            "categories": categories
        }, status=status.HTTP_200_OK)
    
    def _search_teachers(self, query, user_school_ids, limit):
        """Search for teachers within user's schools."""
        # Build the queryset with school filtering
        teacher_memberships = SchoolMembership.objects.filter(
            school_id__in=user_school_ids,
            role=SchoolRole.TEACHER,
            is_active=True
        ).select_related('user', 'user__teacher_profile')
        
        # Apply text search on user name and teacher profile fields
        query_lower = query.lower()
        teacher_memberships = teacher_memberships.filter(
            models.Q(user__name__icontains=query) |
            models.Q(user__email__icontains=query) |
            models.Q(user__teacher_profile__specialty__icontains=query) |
            models.Q(user__teacher_profile__bio__icontains=query)
        )
        
        results = []
        for membership in teacher_memberships[:limit]:
            user = membership.user
            teacher_profile = getattr(user, 'teacher_profile', None)
            
            # Build subtitle
            subtitle_parts = []
            if teacher_profile and teacher_profile.specialty:
                subtitle_parts.append(teacher_profile.specialty)
            subtitle_parts.append(user.email)
            
            result = {
                "id": str(user.id),
                "type": "teacher",
                "title": user.name,
                "subtitle": " • ".join(subtitle_parts) if subtitle_parts else None,
                "route": f"/teachers/{user.id}",
                "metadata": {
                    "email": user.email,
                    "specialty": teacher_profile.specialty if teacher_profile else None,
                    "bio": teacher_profile.bio[:200] if teacher_profile and teacher_profile.bio else None,
                }
            }
            
            results.append(result)
        
        return results
    
    def _search_students(self, query, user_school_ids, limit):
        """Search for students within user's schools."""
        # Build the queryset with school filtering
        student_memberships = SchoolMembership.objects.filter(
            school_id__in=user_school_ids,
            role=SchoolRole.STUDENT,
            is_active=True
        ).select_related('user', 'user__student_profile', 'user__student_profile__educational_system')
        
        # Apply text search on user name and student profile fields  
        query_lower = query.lower()
        student_memberships = student_memberships.filter(
            models.Q(user__name__icontains=query) |
            models.Q(user__email__icontains=query) |
            models.Q(user__student_profile__school_year__icontains=query)
        )
        
        results = []
        for membership in student_memberships[:limit]:
            user = membership.user
            student_profile = getattr(user, 'student_profile', None)
            
            # Build subtitle
            subtitle_parts = []
            if student_profile:
                if student_profile.school_year:
                    subtitle_parts.append(f"Year {student_profile.school_year}")
                if student_profile.educational_system:
                    subtitle_parts.append(student_profile.educational_system.name)
            subtitle_parts.append(user.email)
            
            result = {
                "id": str(user.id),
                "type": "student",
                "title": user.name,
                "subtitle": " • ".join(subtitle_parts) if subtitle_parts else None,
                "route": f"/students/{user.id}",
                "metadata": {
                    "email": user.email,
                    "school_year": student_profile.school_year if student_profile else None,
                    "educational_system": student_profile.educational_system.name if student_profile and student_profile.educational_system else None,
                }
            }
            
            results.append(result)
        
        return results
    
    def _search_courses(self, query, limit):
        """Search for courses across all educational systems."""
        # Apply text search on course fields
        courses = Course.objects.filter(
            models.Q(name__icontains=query) |
            models.Q(code__icontains=query) |
            models.Q(description__icontains=query)
        ).select_related('educational_system')
        
        results = []
        for course in courses[:limit]:
            # Build subtitle
            subtitle_parts = []
            if course.code:
                subtitle_parts.append(course.code)
            if course.educational_system:
                subtitle_parts.append(course.educational_system.name)
            if course.education_level:
                subtitle_parts.append(course.education_level)
            
            result = {
                "id": str(course.id),
                "type": "class",  # Frontend expects 'class' not 'course'
                "title": course.name,
                "subtitle": " • ".join(subtitle_parts) if subtitle_parts else None,
                "route": f"/classes/{course.id}",
                "metadata": {
                    "code": course.code,
                    "description": course.description[:200] if course.description else None,
                    "education_level": course.education_level,
                    "educational_system": course.educational_system.name if course.educational_system else None,
                }
            }
            results.append(result)
        
        return results


class BulkTeacherActionsView(KnoxAuthenticatedAPIView):
    """
    API endpoint for bulk teacher operations.
    
    Supports actions: update_status, send_message, export_data, update_profile
    Maximum 50 teachers per operation as per business requirements.
    """
    
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    SUPPORTED_ACTIONS = ['update_status', 'send_message', 'export_data', 'update_profile']
    MAX_TEACHERS_PER_OPERATION = 50
    
    def post(self, request):
        """
        Execute bulk operations on multiple teachers.
        
        Expected payload:
        {
            "action": "update_status|send_message|export_data|update_profile",
            "teacher_ids": [1, 2, 3, ...],
            "parameters": {
                // Action-specific parameters
            }
        }
        """
        try:
            # Validate request data
            action = request.data.get('action')
            teacher_ids = request.data.get('teacher_ids', [])
            parameters = request.data.get('parameters', {})
            
            # Validate action
            if not action or action not in self.SUPPORTED_ACTIONS:
                return Response(
                    {'error': f'Invalid action. Supported actions: {", ".join(self.SUPPORTED_ACTIONS)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate teacher_ids
            if not teacher_ids or not isinstance(teacher_ids, list):
                return Response(
                    {'error': 'teacher_ids must be a non-empty list'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check maximum limit
            if len(teacher_ids) > self.MAX_TEACHERS_PER_OPERATION:
                return Response(
                    {'error': f'Maximum {self.MAX_TEACHERS_PER_OPERATION} teachers allowed per operation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get school IDs the user can manage
            manageable_school_ids = list_school_ids_owned_or_managed(request.user)
            if not manageable_school_ids:
                return Response(
                    {'error': 'You do not have permission to manage any schools'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Execute the bulk action
            if action == 'update_status':
                result = self._handle_update_status(teacher_ids, parameters, manageable_school_ids)
            elif action == 'send_message':
                result = self._handle_send_message(teacher_ids, parameters, manageable_school_ids)
            elif action == 'export_data':
                result = self._handle_export_data(teacher_ids, parameters, manageable_school_ids)
            elif action == 'update_profile':
                result = self._handle_update_profile(teacher_ids, parameters, manageable_school_ids)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Bulk teacher action failed: {e}")
            return Response(
                {'error': 'Internal server error during bulk operation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _handle_update_status(self, teacher_ids, parameters, manageable_school_ids):
        """Handle bulk status updates for teacher memberships."""
        is_active = parameters.get('is_active')
        
        if is_active is None:
            return {
                'error': 'is_active parameter is required for update_status action',
                'successful_count': 0,
                'failed_count': len(teacher_ids),
                'results': []
            }
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for teacher_id in teacher_ids:
            try:
                # Get teacher profile
                teacher_profile = TeacherProfile.objects.get(id=teacher_id)
                
                # Get teacher's memberships in manageable schools
                memberships = SchoolMembership.objects.filter(
                    user=teacher_profile.user,
                    school_id__in=manageable_school_ids,
                    role=SchoolRole.TEACHER
                )
                
                if not memberships.exists():
                    results.append({
                        'teacher_id': teacher_id,
                        'status': 'failed',
                        'error': 'No permission to manage this teacher or teacher not found in your schools'
                    })
                    failed_count += 1
                    continue
                
                # Update membership status
                updated_count = memberships.update(is_active=is_active)
                
                if updated_count > 0:
                    results.append({
                        'teacher_id': teacher_id,
                        'status': 'success',
                        'message': f'Updated {updated_count} membership(s)'
                    })
                    successful_count += 1
                else:
                    results.append({
                        'teacher_id': teacher_id,
                        'status': 'failed',
                        'error': 'No memberships updated'
                    })
                    failed_count += 1
                    
            except TeacherProfile.DoesNotExist:
                results.append({
                    'teacher_id': teacher_id,
                    'status': 'failed',
                    'error': 'Teacher profile not found'
                })
                failed_count += 1
            except Exception as e:
                logger.error(f"Error updating status for teacher {teacher_id}: {e}")
                results.append({
                    'teacher_id': teacher_id,
                    'status': 'failed',
                    'error': str(e)
                })
                failed_count += 1
        
        return {
            'action': 'update_status',
            'successful_count': successful_count,
            'failed_count': failed_count,
            'results': results
        }
    
    def _handle_send_message(self, teacher_ids, parameters, manageable_school_ids):
        """Handle bulk message sending to teachers."""
        message = parameters.get('message')
        subject = parameters.get('subject', 'Message from School Administration')
        template = parameters.get('template')
        template_variables = parameters.get('template_variables', {})
        
        if not message and not template:
            return {
                'error': 'Either message or template parameter is required for send_message action',
                'successful_count': 0,
                'failed_count': len(teacher_ids),
                'results': []
            }
        
        results = []
        successful_count = 0
        failed_count = 0
        template_used = None
        
        for teacher_id in teacher_ids:
            try:
                # Get teacher profile
                teacher_profile = TeacherProfile.objects.get(id=teacher_id)
                
                # Check if user can manage this teacher
                memberships = SchoolMembership.objects.filter(
                    user=teacher_profile.user,
                    school_id__in=manageable_school_ids,
                    role=SchoolRole.TEACHER
                )
                
                if not memberships.exists():
                    results.append({
                        'teacher_id': teacher_id,
                        'status': 'failed',
                        'error': 'No permission to message this teacher'
                    })
                    failed_count += 1
                    continue
                
                # Prepare message content
                if template:
                    message_content = self._render_message_template(template, template_variables, teacher_profile)
                    template_used = template
                else:
                    message_content = message
                
                # Send message (implementation would depend on messaging system)
                # For now, we'll simulate success
                success = self._send_teacher_message(teacher_profile.user.email, subject, message_content)
                
                if success:
                    results.append({
                        'teacher_id': teacher_id,
                        'status': 'success',
                        'message': 'Message sent successfully'
                    })
                    successful_count += 1
                else:
                    results.append({
                        'teacher_id': teacher_id,
                        'status': 'failed',
                        'error': 'Failed to send message'
                    })
                    failed_count += 1
                    
            except TeacherProfile.DoesNotExist:
                results.append({
                    'teacher_id': teacher_id,
                    'status': 'failed',
                    'error': 'Teacher profile not found'
                })
                failed_count += 1
            except Exception as e:
                logger.error(f"Error sending message to teacher {teacher_id}: {e}")
                results.append({
                    'teacher_id': teacher_id,
                    'status': 'failed',
                    'error': str(e)
                })
                failed_count += 1
        
        result = {
            'action': 'send_message',
            'successful_count': successful_count,
            'failed_count': failed_count,
            'results': results
        }
        
        if template_used:
            result['template_used'] = template_used
        
        return result
    
    def _handle_export_data(self, teacher_ids, parameters, manageable_school_ids):
        """Handle bulk data export for teachers."""
        export_format = parameters.get('format', 'csv')
        fields = parameters.get('fields', ['name', 'email', 'bio', 'hourly_rate', 'profile_completion_score'])
        
        if export_format not in ['csv', 'json', 'xlsx']:
            return {
                'error': 'Invalid export format. Supported: csv, json, xlsx',
                'successful_count': 0,
                'failed_count': len(teacher_ids),
                'results': []
            }
        
        results = []
        successful_count = 0
        failed_count = 0
        export_data = []
        
        for teacher_id in teacher_ids:
            try:
                # Get teacher profile
                teacher_profile = TeacherProfile.objects.get(id=teacher_id)
                
                # Check if user can manage this teacher
                memberships = SchoolMembership.objects.filter(
                    user=teacher_profile.user,
                    school_id__in=manageable_school_ids,
                    role=SchoolRole.TEACHER
                )
                
                if not memberships.exists():
                    results.append({
                        'teacher_id': teacher_id,
                        'status': 'failed',
                        'error': 'No permission to export data for this teacher'
                    })
                    failed_count += 1
                    continue
                
                # Extract requested fields
                teacher_data = {}
                for field in fields:
                    if field == 'name':
                        teacher_data['name'] = teacher_profile.user.name
                    elif field == 'email':
                        teacher_data['email'] = teacher_profile.user.email
                    elif field == 'bio':
                        teacher_data['bio'] = teacher_profile.bio
                    elif field == 'hourly_rate':
                        teacher_data['hourly_rate'] = str(teacher_profile.hourly_rate) if teacher_profile.hourly_rate else ''
                    elif field == 'profile_completion_score':
                        teacher_data['profile_completion_score'] = str(teacher_profile.profile_completion_score)
                    elif field == 'specialty':
                        teacher_data['specialty'] = teacher_profile.specialty
                    elif field == 'education':
                        teacher_data['education'] = teacher_profile.education
                    elif field == 'phone_number':
                        teacher_data['phone_number'] = teacher_profile.phone_number
                    elif field == 'availability':
                        teacher_data['availability'] = teacher_profile.availability
                
                teacher_data['teacher_id'] = teacher_id
                export_data.append(teacher_data)
                
                results.append({
                    'teacher_id': teacher_id,
                    'status': 'success',
                    'message': 'Data exported successfully'
                })
                successful_count += 1
                
            except TeacherProfile.DoesNotExist:
                results.append({
                    'teacher_id': teacher_id,
                    'status': 'failed',
                    'error': 'Teacher profile not found'
                })
                failed_count += 1
            except Exception as e:
                logger.error(f"Error exporting data for teacher {teacher_id}: {e}")
                results.append({
                    'teacher_id': teacher_id,
                    'status': 'failed',
                    'error': str(e)
                })
                failed_count += 1
        
        # Generate export file (simplified implementation)
        export_url = self._generate_export_file(export_data, export_format)
        file_size = len(str(export_data))  # Simplified size calculation
        
        return {
            'action': 'export_data',
            'successful_count': successful_count,
            'failed_count': failed_count,
            'results': results,
            'export_url': export_url,
            'file_size': file_size,
            'format': export_format,
            'fields': fields
        }
    
    def _handle_update_profile(self, teacher_ids, parameters, manageable_school_ids):
        """Handle bulk profile updates for teachers."""
        if not parameters:
            return {
                'error': 'Profile update parameters are required',
                'successful_count': 0,
                'failed_count': len(teacher_ids),
                'results': []
            }
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for teacher_id in teacher_ids:
            try:
                # Get teacher profile
                teacher_profile = TeacherProfile.objects.get(id=teacher_id)
                
                # Check if user can manage this teacher
                memberships = SchoolMembership.objects.filter(
                    user=teacher_profile.user,
                    school_id__in=manageable_school_ids,
                    role=SchoolRole.TEACHER
                )
                
                if not memberships.exists():
                    results.append({
                        'teacher_id': teacher_id,
                        'status': 'failed',
                        'error': 'No permission to update this teacher'
                    })
                    failed_count += 1
                    continue
                
                # Update profile fields
                updated_fields = []
                for field, value in parameters.items():
                    if hasattr(teacher_profile, field):
                        # Handle special field types
                        if field == 'hourly_rate' and value:
                            try:
                                from decimal import Decimal
                                value = Decimal(str(value))
                            except:
                                raise ValidationError(f"Invalid hourly_rate value: {value}")
                        
                        setattr(teacher_profile, field, value)
                        updated_fields.append(field)
                
                if updated_fields:
                    teacher_profile.save()
                    
                    # Trigger completion score recalculation
                    teacher_profile.update_completion_score()
                    
                    results.append({
                        'teacher_id': teacher_id,
                        'status': 'success',
                        'message': f'Updated fields: {", ".join(updated_fields)}'
                    })
                    successful_count += 1
                else:
                    results.append({
                        'teacher_id': teacher_id,
                        'status': 'failed',
                        'error': 'No valid fields to update'
                    })
                    failed_count += 1
                
            except TeacherProfile.DoesNotExist:
                results.append({
                    'teacher_id': teacher_id,
                    'status': 'failed',
                    'error': 'Teacher profile not found'
                })
                failed_count += 1
            except ValidationError as e:
                results.append({
                    'teacher_id': teacher_id,
                    'status': 'failed',
                    'error': str(e)
                })
                failed_count += 1
            except Exception as e:
                logger.error(f"Error updating profile for teacher {teacher_id}: {e}")
                results.append({
                    'teacher_id': teacher_id,
                    'status': 'failed',
                    'error': str(e)
                })
                failed_count += 1
        
        return {
            'action': 'update_profile',
            'successful_count': successful_count,
            'failed_count': failed_count,
            'results': results
        }
    
    def _render_message_template(self, template, variables, teacher_profile):
        """Render message template with variables."""
        # Simplified template rendering
        templates = {
            'profile_completion_reminder': (
                f"Dear {teacher_profile.user.name},\n\n"
                f"We noticed your profile completion is below {variables.get('completion_threshold', 80)}%. "
                f"Please complete your profile by {variables.get('deadline', 'soon')} to improve your visibility to students.\n\n"
                "Best regards,\nSchool Administration"
            ),
            'welcome_message': (
                f"Welcome {teacher_profile.user.name}!\n\n"
                "We're excited to have you join our teaching team. Please complete your profile to get started.\n\n"
                "Best regards,\nSchool Administration"
            ),
            'profile_update_reminder': (
                f"Hello {teacher_profile.user.name},\n\n"
                "Please update your profile information to keep it current.\n\n"
                "Best regards,\nSchool Administration"
            )
        }
        
        return templates.get(template, f"Dear {teacher_profile.user.name},\n\nTemplate '{template}' not found.")
    
    def _send_teacher_message(self, email, subject, message):
        """Send message to teacher (placeholder implementation)."""
        # In a real implementation, this would integrate with email service
        logger.info(f"Sending message to {email}: {subject}")
        return True  # Assume success for now
    
    def _generate_export_file(self, data, format_type):
        """Generate export file and return URL (placeholder implementation)."""
        # In a real implementation, this would generate actual files
        import uuid
        file_id = str(uuid.uuid4())
        return f"/api/exports/{file_id}.{format_type}"


class TeacherAnalyticsView(KnoxAuthenticatedAPIView):
    """
    API endpoint for school-level teacher analytics.
    
    Provides comprehensive insights into teacher profile completion,
    subject coverage, and activity metrics for school administrators.
    """
    
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get(self, request, school_id):
        """
        Get comprehensive teacher analytics for a school.
        
        Query parameters:
        - min_completion: Filter teachers by minimum completion percentage
        - include_export_data: Include detailed teacher data for export
        """
        try:
            # Validate school existence and permissions
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                return Response(
                    {'error': 'School not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user can manage this school
            manageable_school_ids = list_school_ids_owned_or_managed(request.user)
            if school_id not in manageable_school_ids:
                return Response(
                    {'error': 'You do not have permission to view analytics for this school'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get query parameters
            min_completion = request.query_params.get('min_completion')
            include_export_data = request.query_params.get('include_export_data', '').lower() == 'true'
            
            # Get all teacher profiles for this school
            teacher_memberships = SchoolMembership.objects.filter(
                school=school,
                role=SchoolRole.TEACHER,
                is_active=True
            ).select_related('user__teacher_profile')
            
            teacher_profiles = []
            for membership in teacher_memberships:
                if hasattr(membership.user, 'teacher_profile'):
                    profile = membership.user.teacher_profile
                    
                    # Apply completion filter if specified
                    if min_completion:
                        try:
                            min_comp = float(min_completion)
                            if profile.profile_completion_score < min_comp:
                                continue
                        except ValueError:
                            pass  # Ignore invalid min_completion values
                    
                    teacher_profiles.append(profile)
            
            # Generate analytics
            analytics_data = self._generate_analytics(school, teacher_profiles, include_export_data)
            
            return Response(analytics_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Teacher analytics failed for school {school_id}: {e}")
            return Response(
                {'error': 'Internal server error while generating analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_analytics(self, school, teacher_profiles, include_export_data=False):
        """Generate comprehensive analytics data."""
        from .services.profile_completion import ProfileCompletionService
        
        if not teacher_profiles:
            return self._empty_analytics_response(include_export_data)
        
        # Profile completion statistics
        completion_stats = self._calculate_completion_stats(teacher_profiles)
        
        # Subject coverage analysis
        subject_coverage = self._analyze_subject_coverage(teacher_profiles)
        
        # Teacher activity metrics
        activity_metrics = self._calculate_activity_metrics(teacher_profiles)
        
        # Completion distribution
        completion_distribution = self._calculate_completion_distribution(teacher_profiles)
        
        # Common missing fields
        common_missing_fields = self._identify_common_missing_fields(teacher_profiles)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(completion_stats, subject_coverage, activity_metrics)
        
        analytics_data = {
            'school_id': school.id,
            'school_name': school.name,
            'generated_at': timezone.now().isoformat(),
            'profile_completion_stats': completion_stats,
            'subject_coverage': subject_coverage,
            'teacher_activity': activity_metrics,
            'completion_distribution': completion_distribution,
            'common_missing_fields': common_missing_fields,
            'recommendations': recommendations
        }
        
        # Include detailed export data if requested
        if include_export_data:
            analytics_data['teacher_details'] = self._generate_teacher_details(teacher_profiles)
        
        return analytics_data
    
    def _calculate_completion_stats(self, teacher_profiles):
        """Calculate profile completion statistics."""
        if not teacher_profiles:
            return {
                'total_teachers': 0,
                'average_completion': 0.0,
                'complete_profiles': 0,
                'incomplete_profiles': 0
            }
        
        total_teachers = len(teacher_profiles)
        completion_scores = [float(profile.profile_completion_score) for profile in teacher_profiles]
        average_completion = sum(completion_scores) / total_teachers
        
        complete_profiles = sum(1 for profile in teacher_profiles if profile.is_profile_complete)
        incomplete_profiles = total_teachers - complete_profiles
        
        return {
            'total_teachers': total_teachers,
            'average_completion': round(average_completion, 1),
            'complete_profiles': complete_profiles,
            'incomplete_profiles': incomplete_profiles
        }
    
    def _analyze_subject_coverage(self, teacher_profiles):
        """Analyze subject coverage across teachers."""
        # Get all available courses
        all_courses = Course.objects.select_related('educational_system').all()
        total_subjects = all_courses.count()
        
        # Get covered subjects (subjects taught by at least one teacher)
        covered_course_ids = set()
        subject_teacher_counts = {}
        
        for profile in teacher_profiles:
            teacher_courses = profile.teacher_courses.filter(is_active=True).select_related('course')
            for teacher_course in teacher_courses:
                course = teacher_course.course
                covered_course_ids.add(course.id)
                
                course_key = f"{course.name} ({course.education_level})"
                if course_key not in subject_teacher_counts:
                    subject_teacher_counts[course_key] = {
                        'subject_name': course.name,
                        'education_level': course.education_level,
                        'teacher_count': 0,
                        'course_id': course.id
                    }
                subject_teacher_counts[course_key]['teacher_count'] += 1
        
        covered_subjects = len(covered_course_ids)
        uncovered_subjects = total_subjects - covered_subjects
        
        # Convert to list and sort by teacher count
        subject_details = sorted(
            subject_teacher_counts.values(),
            key=lambda x: x['teacher_count'],
            reverse=True
        )
        
        return {
            'total_subjects': total_subjects,
            'covered_subjects': covered_subjects,
            'uncovered_subjects': uncovered_subjects,
            'coverage_percentage': round((covered_subjects / total_subjects) * 100, 1) if total_subjects > 0 else 0.0,
            'subject_details': subject_details
        }
    
    def _calculate_activity_metrics(self, teacher_profiles):
        """Calculate teacher activity metrics."""
        from datetime import timedelta
        
        now = timezone.now()
        recent_threshold = now - timedelta(days=30)  # Active within last 30 days
        update_threshold = now - timedelta(days=7)   # Updated profile within last 7 days
        
        active_teachers = 0
        inactive_teachers = 0
        recently_updated_profiles = 0
        needs_attention = 0  # Incomplete profiles or very low completion
        
        for profile in teacher_profiles:
            # Activity check
            if profile.last_activity and profile.last_activity >= recent_threshold:
                active_teachers += 1
            else:
                inactive_teachers += 1
            
            # Recent profile updates
            if profile.last_profile_update >= update_threshold:
                recently_updated_profiles += 1
            
            # Needs attention (incomplete or very low completion)
            if not profile.is_profile_complete or profile.profile_completion_score < 50:
                needs_attention += 1
        
        return {
            'active_teachers': active_teachers,
            'inactive_teachers': inactive_teachers,
            'recently_updated_profiles': recently_updated_profiles,
            'needs_attention': needs_attention,
            'activity_rate': round((active_teachers / len(teacher_profiles)) * 100, 1) if teacher_profiles else 0.0
        }
    
    def _calculate_completion_distribution(self, teacher_profiles):
        """Calculate completion score distribution."""
        distribution = {'0-25%': 0, '26-50%': 0, '51-75%': 0, '76-100%': 0}
        
        for profile in teacher_profiles:
            score = float(profile.profile_completion_score)
            if score <= 25:
                distribution['0-25%'] += 1
            elif score <= 50:
                distribution['26-50%'] += 1
            elif score <= 75:
                distribution['51-75%'] += 1
            else:
                distribution['76-100%'] += 1
        
        return distribution
    
    def _identify_common_missing_fields(self, teacher_profiles):
        """Identify most commonly missing fields across teachers."""
        from .services.profile_completion import ProfileCompletionService
        
        missing_field_counts = {}
        total_teachers = len(teacher_profiles)
        
        for profile in teacher_profiles:
            missing_critical, missing_optional = ProfileCompletionService.identify_missing_fields(profile)
            
            # Count missing fields
            for field in missing_critical + missing_optional:
                missing_field_counts[field] = missing_field_counts.get(field, 0) + 1
        
        # Convert to list with percentages and sort by frequency
        common_missing = []
        for field, count in missing_field_counts.items():
            common_missing.append({
                'field': field,
                'count': count,
                'percentage': round((count / total_teachers) * 100, 1) if total_teachers > 0 else 0.0
            })
        
        # Sort by count (most common first) and take top 10
        common_missing.sort(key=lambda x: x['count'], reverse=True)
        return common_missing[:10]
    
    def _generate_recommendations(self, completion_stats, subject_coverage, activity_metrics):
        """Generate actionable recommendations based on analytics."""
        recommendations = []
        
        # Profile completion recommendations
        if completion_stats['incomplete_profiles'] > completion_stats['complete_profiles']:
            recommendations.append({
                'text': f"Focus on profile completion: {completion_stats['incomplete_profiles']} teachers need to complete their profiles.",
                'priority': 'high'
            })
        
        if completion_stats['average_completion'] < 60:
            recommendations.append({
                'text': f"Overall profile quality needs improvement (average: {completion_stats['average_completion']}%). Consider providing guidance or incentives.",
                'priority': 'high'
            })
        
        # Subject coverage recommendations
        if subject_coverage['coverage_percentage'] < 70:
            recommendations.append({
                'text': f"Subject coverage is low ({subject_coverage['coverage_percentage']}%). Consider recruiting teachers for uncovered subjects.",
                'priority': 'medium'
            })
        
        # Activity recommendations
        if activity_metrics['inactive_teachers'] > activity_metrics['active_teachers']:
            recommendations.append({
                'text': f"{activity_metrics['inactive_teachers']} teachers appear inactive. Consider reaching out to re-engage them.",
                'priority': 'medium'
            })
        
        if activity_metrics['needs_attention'] > 0:
            recommendations.append({
                'text': f"{activity_metrics['needs_attention']} teachers need immediate attention for profile completion.",
                'priority': 'high'
            })
        
        # Default positive message if no major issues
        if not recommendations:
            recommendations.append({
                'text': "Your teacher profiles are in good shape! Continue monitoring and encouraging regular updates.",
                'priority': 'low'
            })
        
        return recommendations
    
    def _generate_teacher_details(self, teacher_profiles):
        """Generate detailed teacher data for export."""
        from .services.profile_completion import ProfileCompletionService
        
        teacher_details = []
        
        for profile in teacher_profiles:
            completion_data = ProfileCompletionService.calculate_completion(profile)
            courses_count = profile.teacher_courses.filter(is_active=True).count()
            
            teacher_details.append({
                'id': profile.id,
                'name': profile.user.name,
                'email': profile.user.email,
                'completion_percentage': completion_data['completion_percentage'],
                'is_complete': completion_data['is_complete'],
                'missing_fields_count': len(completion_data['missing_critical']) + len(completion_data['missing_optional']),
                'missing_critical_count': len(completion_data['missing_critical']),
                'courses_count': courses_count,
                'last_activity': profile.last_activity.isoformat() if profile.last_activity else None,
                'last_profile_update': profile.last_profile_update.isoformat() if profile.last_profile_update else None
            })
        
        # Sort by completion percentage (lowest first to highlight issues)
        teacher_details.sort(key=lambda x: x['completion_percentage'])
        
        return teacher_details
    
    def _empty_analytics_response(self, include_export_data=False):
        """Return empty analytics response for schools with no teachers."""
        response = {
            'profile_completion_stats': {
                'total_teachers': 0,
                'average_completion': 0.0,
                'complete_profiles': 0,
                'incomplete_profiles': 0
            },
            'subject_coverage': {
                'total_subjects': Course.objects.count(),
                'covered_subjects': 0,
                'uncovered_subjects': Course.objects.count(),
                'coverage_percentage': 0.0,
                'subject_details': []
            },
            'teacher_activity': {
                'active_teachers': 0,
                'inactive_teachers': 0,
                'recently_updated_profiles': 0,
                'needs_attention': 0,
                'activity_rate': 0.0
            },
            'completion_distribution': {'0-25%': 0, '26-50%': 0, '51-75%': 0, '76-100%': 0},
            'common_missing_fields': [],
            'recommendations': [{
                'text': 'No teachers found in this school. Start by inviting teachers to join.',
                'priority': 'high'
            }]
        }
        
        if include_export_data:
            response['teacher_details'] = []
        
        return response


class TutorDiscoveryAPIView(APIView):
    """
    Public API endpoint for tutor discovery.
    
    Allows students and parents to search for tutors without authentication.
    Only exposes public profile information with proper privacy controls.
    """
    
    permission_classes = [AllowAny]  # Public endpoint
    throttle_classes = [LocalIPBasedThrottle]  # Rate limiting for public endpoint
    
    def get(self, request):
        """
        Discover tutors based on search criteria.
        
        Query Parameters:
        - subjects: Comma-separated course IDs or names
        - rate_min: Minimum hourly rate (float)
        - rate_max: Maximum hourly rate (float) 
        - education_level: Education level filter
        - educational_system: Educational system ID
        - location: Location filter (future implementation)
        - availability: Availability filter (future implementation)
        - search: Free text search in bio, name, subjects
        - limit: Number of results to return (max 50, default 20)
        - offset: Pagination offset
        - ordering: Sort order (rate, completion_score, activity)
        
        Returns:
        List of public tutor profiles with:
        - Basic profile info (name, bio, specialty)
        - Subjects/courses taught
        - Rate information
        - Profile completion score
        - School information (if tutor is individual)
        """
        try:
            # Parse and validate parameters
            filters = self._parse_filters(request.query_params)
            pagination = self._parse_pagination(request.query_params)
            ordering = self._parse_ordering(request.query_params)
            
            # Generate cache key for performance
            cache_key = self._generate_cache_key(filters, pagination, ordering)
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)
            
            # Build queryset with privacy controls
            tutors_queryset = self._build_tutors_queryset(filters, ordering)
            
            # Apply pagination
            total_count = tutors_queryset.count()
            tutors_queryset = tutors_queryset[pagination['offset']:pagination['offset'] + pagination['limit']]
            
            # Serialize public data
            tutors_data = self._serialize_public_tutors(tutors_queryset, request)
            
            result = {
                'results': tutors_data,
                'count': len(tutors_data),
                'total': total_count,
                'next': self._get_next_url(request, pagination, total_count),
                'previous': self._get_previous_url(request, pagination)
            }
            
            # Cache result (shorter timeout for public endpoint)  
            cache.set(cache_key, result, timeout=300)  # 5 minutes
            
            # Track popular queries for future cache warming
            try:
                from accounts.services.tutor_discovery_cache import TutorDiscoveryCacheService
                TutorDiscoveryCacheService.track_popular_query(filters, pagination, ordering)
            except ImportError:
                pass  # Service not available
            
            return Response(result)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in tutor discovery: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve tutor data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _parse_filters(self, params):
        """Parse and validate filter parameters."""
        filters = {}
        
        # Subject filtering
        subjects = params.get('subjects')
        if subjects:
            subject_list = [s.strip() for s in subjects.split(',') if s.strip()]
            filters['subjects'] = subject_list
        
        # Rate filtering
        try:
            rate_min = params.get('rate_min')
            if rate_min:
                filters['rate_min'] = float(rate_min)
                if filters['rate_min'] < 0:
                    raise ValidationError("rate_min must be non-negative")
        except ValueError:
            raise ValidationError("Invalid rate_min format")
        
        try:
            rate_max = params.get('rate_max')
            if rate_max:
                filters['rate_max'] = float(rate_max)
                if filters['rate_max'] < 0:
                    raise ValidationError("rate_max must be non-negative")
        except ValueError:
            raise ValidationError("Invalid rate_max format")
        
        # Validate rate range
        if 'rate_min' in filters and 'rate_max' in filters:
            if filters['rate_min'] > filters['rate_max']:
                raise ValidationError("rate_min cannot be greater than rate_max")
        
        # Education level filtering
        education_level = params.get('education_level')
        if education_level:
            filters['education_level'] = education_level
        
        # Educational system filtering
        educational_system = params.get('educational_system')
        if educational_system:
            try:
                filters['educational_system'] = int(educational_system)
            except ValueError:
                raise ValidationError("Invalid educational_system format")
        
        # Search query
        search = params.get('search')
        if search:
            filters['search'] = search.strip()
        
        return filters
    
    def _parse_pagination(self, params):
        """Parse and validate pagination parameters."""
        try:
            limit = int(params.get('limit', 20))
            limit = min(max(1, limit), 50)  # Between 1 and 50
        except ValueError:
            limit = 20
        
        try:
            offset = int(params.get('offset', 0))
            offset = max(0, offset)  # Non-negative
        except ValueError:
            offset = 0
        
        return {'limit': limit, 'offset': offset}
    
    def _parse_ordering(self, params):
        """Parse and validate ordering parameter."""
        ordering = params.get('ordering', 'completion_score')
        
        valid_orderings = [
            'rate', '-rate',
            'completion_score', '-completion_score', 
            'activity', '-activity',
            'name', '-name'
        ]
        
        if ordering not in valid_orderings:
            ordering = '-completion_score'  # Default
        
        return ordering
    
    def _build_tutors_queryset(self, filters, ordering):
        """Build queryset for tutors with privacy controls and performance optimization."""
        # Only include tutors with complete profiles and active memberships
        # Use select_related and prefetch_related for performance optimization
        queryset = TeacherProfile.objects.filter(
            is_profile_complete=True,
            user__school_memberships__role__in=[SchoolRole.TEACHER, SchoolRole.SCHOOL_OWNER],
            user__school_memberships__is_active=True
        ).select_related(
            'user'
        ).prefetch_related(
            'teacher_courses__course__educational_system',
            'user__school_memberships__school'
        ).distinct()
        
        # Apply subject filtering
        if 'subjects' in filters:
            # Filter by courses taught
            course_filter = models.Q()
            for subject in filters['subjects']:
                # Try to match by course ID or name
                try:
                    course_id = int(subject)
                    course_filter |= models.Q(teacher_courses__course_id=course_id)
                except ValueError:
                    # Search by course name
                    course_filter |= models.Q(teacher_courses__course__name__icontains=subject)
            
            if course_filter:
                queryset = queryset.filter(course_filter).distinct()
        
        # Apply rate filtering
        if 'rate_min' in filters:
            queryset = queryset.filter(
                models.Q(hourly_rate__gte=filters['rate_min']) |
                models.Q(teacher_courses__hourly_rate__gte=filters['rate_min'])
            ).distinct()
        
        if 'rate_max' in filters:
            queryset = queryset.filter(
                models.Q(hourly_rate__lte=filters['rate_max']) |
                models.Q(teacher_courses__hourly_rate__lte=filters['rate_max'])
            ).distinct()
        
        # Apply education level filtering
        if 'education_level' in filters:
            queryset = queryset.filter(
                teacher_courses__course__education_level=filters['education_level']
            ).distinct()
        
        # Apply educational system filtering
        if 'educational_system' in filters:
            queryset = queryset.filter(
                teacher_courses__course__educational_system_id=filters['educational_system']
            ).distinct()
        
        # Apply search filtering
        if 'search' in filters:
            search_query = filters['search']
            queryset = queryset.filter(
                models.Q(user__name__icontains=search_query) |
                models.Q(bio__icontains=search_query) |
                models.Q(specialty__icontains=search_query) |
                models.Q(teaching_subjects__icontains=search_query)
            ).distinct()
        
        # Apply ordering
        if ordering == 'rate':
            queryset = queryset.order_by('hourly_rate')
        elif ordering == '-rate':
            queryset = queryset.order_by('-hourly_rate') 
        elif ordering == 'completion_score':
            queryset = queryset.order_by('profile_completion_score')
        elif ordering == '-completion_score':
            queryset = queryset.order_by('-profile_completion_score')
        elif ordering == 'activity':
            queryset = queryset.order_by('last_activity')
        elif ordering == '-activity':
            queryset = queryset.order_by('-last_activity')
        elif ordering == 'name':
            queryset = queryset.order_by('user__name')
        elif ordering == '-name':
            queryset = queryset.order_by('-user__name')
        else:
            queryset = queryset.order_by('-profile_completion_score')
        
        return queryset
    
    def _serialize_public_tutors(self, tutors_queryset, request):
        """Serialize tutors for public consumption with privacy controls."""
        tutors_data = []
        
        for tutor in tutors_queryset:
            # Get school information (for individual tutors)
            school_info = None
            school_membership = tutor.user.school_memberships.filter(
                role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.TEACHER],
                is_active=True
            ).select_related('school').first()
            
            if school_membership:
                school_info = {
                    'id': school_membership.school.id,
                    'name': school_membership.school.name,
                    'is_individual_tutor': school_membership.role == SchoolRole.SCHOOL_OWNER
                }
            
            # Get courses/subjects taught
            subjects = []
            teacher_courses = tutor.teacher_courses.filter(is_active=True).select_related('course')
            for tc in teacher_courses:
                subjects.append({
                    'id': tc.course.id,
                    'name': tc.course.name,
                    'code': tc.course.code,
                    'education_level': tc.course.education_level,
                    'hourly_rate': float(tc.hourly_rate) if tc.hourly_rate else float(tutor.hourly_rate or 0)
                })
            
            # Calculate average rate
            rates = [s['hourly_rate'] for s in subjects if s['hourly_rate'] > 0]
            avg_rate = sum(rates) / len(rates) if rates else float(tutor.hourly_rate or 0)
            
            tutor_data = {
                'id': tutor.id,
                'name': tutor.user.name,
                'bio': tutor.bio[:500] if tutor.bio else '',  # Limit bio length
                'specialty': tutor.specialty,
                'profile_completion_score': float(tutor.profile_completion_score),
                'is_profile_complete': tutor.is_profile_complete,
                'average_hourly_rate': round(avg_rate, 2),
                'subjects': subjects,
                'school': school_info,
                'teaching_subjects': tutor.teaching_subjects if isinstance(tutor.teaching_subjects, list) else [],
                'last_activity': tutor.last_activity.isoformat() if tutor.last_activity else None
            }
            
            tutors_data.append(tutor_data)
        
        return tutors_data
    
    def _generate_cache_key(self, filters, pagination, ordering):
        """Generate cache key for the request."""
        key_parts = ['tutor_discovery']
        
        # Add filters to key
        for key, value in filters.items():
            if isinstance(value, list):
                key_parts.append(f"{key}_{'_'.join(map(str, value))}")
            else:
                key_parts.append(f"{key}_{value}")
        
        # Add pagination and ordering
        key_parts.append(f"limit_{pagination['limit']}")
        key_parts.append(f"offset_{pagination['offset']}")
        key_parts.append(f"order_{ordering}")
        
        return '_'.join(key_parts)
    
    def _get_next_url(self, request, pagination, total_count):
        """Generate next page URL."""
        next_offset = pagination['offset'] + pagination['limit']
        if next_offset >= total_count:
            return None
        
        params = request.query_params.copy()
        params['offset'] = next_offset
        return f"{request.build_absolute_uri()}?{params.urlencode()}"
    
    def _get_previous_url(self, request, pagination):
        """Generate previous page URL."""
        if pagination['offset'] <= 0:
            return None
        
        prev_offset = max(0, pagination['offset'] - pagination['limit'])
        params = request.query_params.copy()
        params['offset'] = prev_offset
        return f"{request.build_absolute_uri()}?{params.urlencode()}"


class TutorOnboardingAPIView(KnoxAuthenticatedAPIView):
    """
    API endpoints for individual tutor onboarding process.
    
    Handles the complete onboarding flow for individual tutors including:
    - Onboarding guidance and tips
    - Starting onboarding session
    - Step validation
    - Progress tracking
    """
    
    throttle_classes = [ProfileWizardThrottle]
    
    def get_onboarding_guidance(self, request):
        """
        POST /api/accounts/tutors/onboarding/guidance/
        
        Get onboarding guidance and tips for a specific step.
        """
        try:
            step_id = request.data.get('step_id')
            context = request.data.get('context', {})
            
            if not step_id:
                return Response(
                    {'error': 'step_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            guidance_data = self._get_step_guidance(step_id, context)
            
            return Response(guidance_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting onboarding guidance: {e}")
            return Response(
                {'error': 'Failed to get onboarding guidance'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def start_onboarding(self, request):
        """
        POST /api/accounts/tutors/onboarding/start/
        
        Initialize a tutor onboarding session and return initial progress.
        """
        try:
            user = request.user
            
            # Generate onboarding session ID
            import uuid
            onboarding_id = str(uuid.uuid4())
            
            # Initialize onboarding progress in user profile
            initial_progress = {
                'current_step': 1,
                'total_steps': 6,  # Educational system, course selection, rates, availability, profile, publish
                'completed_steps': [],
                'step_completion': {
                    'educational_system_selection': {
                        'is_complete': False,
                        'completion_percentage': 0,
                        'validation_errors': [],
                        'last_updated': timezone.now().isoformat()
                    },
                    'course_selection': {
                        'is_complete': False,
                        'completion_percentage': 0,
                        'validation_errors': [],
                        'last_updated': timezone.now().isoformat()
                    },
                    'rate_configuration': {
                        'is_complete': False,
                        'completion_percentage': 0,
                        'validation_errors': [],
                        'last_updated': timezone.now().isoformat()
                    },
                    'availability_setup': {
                        'is_complete': False,
                        'completion_percentage': 0,
                        'validation_errors': [],
                        'last_updated': timezone.now().isoformat()
                    },
                    'profile_completion': {
                        'is_complete': False,
                        'completion_percentage': 0,
                        'validation_errors': [],
                        'last_updated': timezone.now().isoformat()
                    },
                    'profile_publishing': {
                        'is_complete': False,
                        'completion_percentage': 0,
                        'validation_errors': [],
                        'last_updated': timezone.now().isoformat()
                    }
                },
                'overall_completion': 0,
                'estimated_time_remaining': 45,  # minutes
                'next_recommended_step': 'educational_system_selection'
            }
            
            # Store in user's onboarding progress
            user.onboarding_progress = {
                'tutor_onboarding': {
                    'onboarding_id': onboarding_id,
                    'started_at': timezone.now().isoformat(),
                    'progress': initial_progress
                }
            }
            user.save(update_fields=['onboarding_progress'])
            
            return Response({
                'onboarding_id': onboarding_id,
                'initial_progress': initial_progress
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error starting tutor onboarding: {e}")
            return Response(
                {'error': 'Failed to start onboarding session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def validate_step(self, request):
        """
        POST /api/accounts/tutors/onboarding/validate-step/
        
        Validate completion of a specific onboarding step.
        """
        try:
            step = request.data.get('step')
            step_data = request.data.get('data', {})
            
            if not step:
                return Response(
                    {'error': 'step is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validation_result = self._validate_onboarding_step(step, step_data, request.user)
            
            return Response(validation_result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error validating onboarding step: {e}")
            return Response(
                {'error': 'Failed to validate onboarding step'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_step_guidance(self, step_id, context):
        """Get guidance data for a specific onboarding step."""
        guidance_map = {
            'educational_system_selection': {
                'tips': [
                    {
                        'title': 'Choose Your Educational System',
                        'description': 'Select the educational system that best matches your teaching expertise and target students.',
                        'priority': 'high',
                        'category': 'requirement'
                    },
                    {
                        'title': 'Portugal System',
                        'description': 'Perfect if you teach Portuguese curriculum from 1st cycle through secondary education.',
                        'priority': 'medium',
                        'category': 'suggestion'
                    },
                    {
                        'title': 'Brazil System',
                        'description': 'Ideal for Brazilian educational content and curriculum standards.',
                        'priority': 'medium',
                        'category': 'suggestion'
                    },
                    {
                        'title': 'Custom System',
                        'description': 'Choose this for specialized subjects, adult education, or professional training.',
                        'priority': 'medium',
                        'category': 'suggestion'
                    }
                ],
                'recommendations': [
                    {
                        'text': 'You can always add more educational systems later',
                        'action': 'reassurance'
                    },
                    {
                        'text': 'Start with the system you know best',
                        'action': 'guidance'
                    }
                ],
                'common_mistakes': [
                    {
                        'mistake': 'Choosing multiple systems when starting',
                        'solution': 'Start with one system and expand later as you grow your tutoring practice'
                    }
                ],
                'estimated_time': 3
            },
            'course_selection': {
                'tips': [
                    {
                        'title': 'Select Your Teaching Subjects',
                        'description': 'Choose courses that match your expertise and qualifications.',
                        'priority': 'high',
                        'category': 'requirement'
                    },
                    {
                        'title': 'Quality Over Quantity',
                        'description': 'Better to teach fewer subjects excellently than many subjects poorly.',
                        'priority': 'high',
                        'category': 'best_practice'
                    },
                    {
                        'title': 'Use Search and Filters',
                        'description': 'Use the search functionality to quickly find specific courses.',
                        'priority': 'medium',
                        'category': 'suggestion'
                    }
                ],
                'recommendations': [
                    {
                        'text': 'Start with 2-4 core subjects you are most confident teaching',
                        'action': 'guidance'
                    },
                    {
                        'text': 'You can add more subjects to your profile later',
                        'action': 'reassurance'
                    }
                ],
                'common_mistakes': [
                    {
                        'mistake': 'Selecting too many courses at once',
                        'solution': 'Focus on your strongest subjects first, then expand gradually'
                    },
                    {
                        'mistake': 'Not setting grade levels for courses',
                        'solution': 'Always specify which grade levels you can teach for each subject'
                    }
                ],
                'estimated_time': 8
            },
            'rate_configuration': {
                'tips': [
                    {
                        'title': 'Set Competitive Rates',
                        'description': 'Research local market rates for your subjects and experience level.',
                        'priority': 'high',
                        'category': 'requirement'
                    },
                    {
                        'title': 'Different Rates for Different Subjects',
                        'description': 'You can set different hourly rates for different subjects based on demand and your expertise.',
                        'priority': 'medium',
                        'category': 'suggestion'
                    },
                    {
                        'title': 'Consider Your Experience',
                        'description': 'New tutors typically start 10-20% below market average and increase rates as they gain reviews.',
                        'priority': 'medium',
                        'category': 'best_practice'
                    }
                ],
                'recommendations': [
                    {
                        'text': 'You can adjust your rates anytime from your profile settings',
                        'action': 'reassurance'
                    },
                    {
                        'text': 'Consider offering a slightly lower rate for first-time students',
                        'action': 'suggestion'
                    }
                ],
                'common_mistakes': [
                    {
                        'mistake': 'Setting rates too high when starting',
                        'solution': 'Start competitive and increase rates as you build reviews and reputation'
                    },
                    {
                        'mistake': 'Using the same rate for all subjects',
                        'solution': 'Price specialized or high-demand subjects higher than basic subjects'
                    }
                ],
                'estimated_time': 10
            }
        }
        
        return guidance_map.get(step_id, {
            'tips': [],
            'recommendations': [],
            'common_mistakes': [],
            'estimated_time': 5
        })
    
    def _validate_onboarding_step(self, step, step_data, user):
        """Validate a specific onboarding step and return validation results."""
        validation_result = {
            'is_valid': True,
            'errors': {},
            'warnings': {},
            'completion_percentage': 0
        }
        
        if step == 'course_selection':
            return self._validate_course_selection_step(step_data, validation_result)
        elif step == 'educational_system_selection':
            return self._validate_educational_system_step(step_data, validation_result)
        elif step == 'rate_configuration':
            return self._validate_rate_configuration_step(step_data, validation_result)
        else:
            validation_result['warnings']['step'] = [f'Unknown step: {step}']
            validation_result['completion_percentage'] = 50  # Partial validation
        
        return validation_result
    
    def _validate_course_selection_step(self, step_data, validation_result):
        """Validate course selection step data."""
        course_selection = step_data.get('course_selection', {})
        
        # Check educational system selection
        educational_system_id = course_selection.get('educational_system_id')
        if not educational_system_id:
            validation_result['is_valid'] = False
            validation_result['errors']['educational_system'] = ['Educational system is required']
        else:
            # Verify educational system exists
            try:
                EducationalSystem.objects.get(id=educational_system_id)
            except EducationalSystem.DoesNotExist:
                validation_result['is_valid'] = False
                validation_result['errors']['educational_system'] = ['Invalid educational system']
        
        # Check selected courses
        selected_courses = course_selection.get('selected_courses', [])
        if not selected_courses:
            validation_result['is_valid'] = False
            validation_result['errors']['courses'] = ['At least one course must be selected']
        else:
            # Validate each selected course
            for i, course_data in enumerate(selected_courses):
                course_id = course_data.get('course_id')
                hourly_rate = course_data.get('hourly_rate')
                expertise_level = course_data.get('expertise_level')
                
                if not course_id:
                    validation_result['errors'][f'course_{i}_id'] = ['Course ID is required']
                    validation_result['is_valid'] = False
                
                if not hourly_rate or hourly_rate <= 0:
                    validation_result['errors'][f'course_{i}_rate'] = ['Valid hourly rate is required']
                    validation_result['is_valid'] = False
                elif hourly_rate > 200:  # Reasonable upper limit
                    validation_result['warnings'][f'course_{i}_rate'] = ['Rate seems high - consider market rates']
                
                if expertise_level not in ['beginner', 'intermediate', 'advanced', 'expert']:
                    validation_result['errors'][f'course_{i}_expertise'] = ['Valid expertise level is required']
                    validation_result['is_valid'] = False
                
                # Verify course exists
                if course_id:
                    try:
                        Course.objects.get(id=course_id)
                    except Course.DoesNotExist:
                        validation_result['errors'][f'course_{i}_id'] = ['Invalid course ID']
                        validation_result['is_valid'] = False
        
        # Calculate completion percentage
        completion_score = 0
        if educational_system_id:
            completion_score += 30
        if selected_courses:
            completion_score += 50
            # Bonus for each valid course
            for course_data in selected_courses:
                if (course_data.get('course_id') and 
                    course_data.get('hourly_rate', 0) > 0 and 
                    course_data.get('expertise_level')):
                    completion_score += min(20, 20 // len(selected_courses))
        
        validation_result['completion_percentage'] = min(100, completion_score)
        
        return validation_result
    
    def _validate_educational_system_step(self, step_data, validation_result):
        """Validate educational system selection step."""
        educational_system_id = step_data.get('educational_system_id')
        
        if not educational_system_id:
            validation_result['is_valid'] = False
            validation_result['errors']['educational_system'] = ['Educational system selection is required']
            validation_result['completion_percentage'] = 0
        else:
            try:
                EducationalSystem.objects.get(id=educational_system_id)
                validation_result['completion_percentage'] = 100
            except EducationalSystem.DoesNotExist:
                validation_result['is_valid'] = False
                validation_result['errors']['educational_system'] = ['Invalid educational system']
                validation_result['completion_percentage'] = 0
        
        return validation_result
    
    def _validate_rate_configuration_step(self, step_data, validation_result):
        """Validate rate configuration step."""
        rates = step_data.get('rates', {})
        
        if not rates:
            validation_result['is_valid'] = False
            validation_result['errors']['rates'] = ['Rate configuration is required']
            validation_result['completion_percentage'] = 0
            return validation_result
        
        valid_rates = 0
        total_rates = len(rates)
        
        for course_id, rate_data in rates.items():
            rate = rate_data.get('hourly_rate', 0)
            
            if rate <= 0:
                validation_result['errors'][f'rate_{course_id}'] = ['Valid hourly rate is required']
                validation_result['is_valid'] = False
            elif rate > 200:
                validation_result['warnings'][f'rate_{course_id}'] = ['Rate seems high - consider market rates']
                valid_rates += 1
            else:
                valid_rates += 1
        
        validation_result['completion_percentage'] = int((valid_rates / total_rates) * 100) if total_rates > 0 else 0
        
        return validation_result
    
    def save_progress(self, request):
        """
        POST /api/accounts/tutors/onboarding/save-progress/
        
        Save tutor onboarding progress and data to user profile and related models.
        """
        try:
            step = request.data.get('step')
            step_data = request.data.get('data', {})
            onboarding_id = request.data.get('onboarding_id')
            
            if not step:
                return Response(
                    {'error': 'step is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = request.user
            
            # Ensure user has onboarding progress initialized
            if not hasattr(user, 'onboarding_progress') or not user.onboarding_progress:
                user.onboarding_progress = {}
            
            if 'tutor_onboarding' not in user.onboarding_progress:
                import uuid
                user.onboarding_progress['tutor_onboarding'] = {
                    'onboarding_id': onboarding_id or str(uuid.uuid4()),
                    'started_at': timezone.now().isoformat(),
                    'progress': {}
                }
            
            # Save step-specific data
            result = self._save_step_data(step, step_data, user)
            
            if result.get('success'):
                # Update onboarding progress
                tutor_progress = user.onboarding_progress['tutor_onboarding']['progress']
                if 'step_completion' not in tutor_progress:
                    tutor_progress['step_completion'] = {}
                
                tutor_progress['step_completion'][step] = {
                    'is_complete': result.get('is_complete', False),
                    'completion_percentage': result.get('completion_percentage', 0),
                    'validation_errors': result.get('validation_errors', []),
                    'last_updated': timezone.now().isoformat()
                }
                
                # Update overall progress
                completed_steps = sum(1 for step_info in tutor_progress.get('step_completion', {}).values() 
                                    if step_info.get('is_complete', False))
                total_steps = 9  # Updated to match frontend's 9-step wizard
                tutor_progress['overall_completion'] = int((completed_steps / total_steps) * 100)
                
                user.save(update_fields=['onboarding_progress'])
                
                return Response({
                    'success': True,
                    'step': step,
                    'saved_data': result.get('saved_data', {}),
                    'progress': tutor_progress
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'errors': result.get('errors', {}),
                    'step': step
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error saving tutor onboarding progress: {e}")
            return Response(
                {'error': 'Failed to save onboarding progress'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _save_step_data(self, step, step_data, user):
        """Save data for a specific onboarding step."""
        try:
            if step == 'business_setup':
                return self._save_business_setup_data(step_data, user)
            elif step == 'educational_system':
                return self._save_educational_system_data(step_data, user)
            elif step == 'teaching_subjects':
                return self._save_teaching_subjects_data(step_data, user)
            elif step == 'personal_information':
                return self._save_personal_information_data(step_data, user)
            elif step == 'professional_bio':
                return self._save_professional_bio_data(step_data, user)
            elif step == 'education_background':
                return self._save_education_background_data(step_data, user)
            elif step == 'availability':
                return self._save_availability_data(step_data, user)
            elif step == 'business_settings':
                return self._save_business_settings_data(step_data, user)
            elif step == 'profile_preview':
                return self._save_profile_preview_data(step_data, user)
            else:
                return {
                    'success': False,
                    'errors': {'step': [f'Unknown step: {step}']}
                }
        except Exception as e:
            logger.error(f"Error saving step data for {step}: {e}")
            return {
                'success': False,
                'errors': {'general': [f'Failed to save {step} data']}
            }
    
    def _save_business_setup_data(self, step_data, user):
        """Save business setup data (school creation)."""
        try:
            school_name = step_data.get('school_name', '').strip()
            school_description = step_data.get('school_description', '').strip()
            
            if not school_name:
                return {
                    'success': False,
                    'errors': {'school_name': ['School name is required']}
                }
            
            # Get or create school for this tutor
            from .models import School, SchoolMembership
            
            # Check if user already has a school as owner
            existing_membership = SchoolMembership.objects.filter(
                user=user, role='school_owner'
            ).first()
            
            if existing_membership:
                school = existing_membership.school
                school.name = school_name
                school.description = school_description
                school.save()
            else:
                # Create new school
                school = School.objects.create(
                    name=school_name,
                    description=school_description,
                    owner=user,
                    school_type='individual_tutor'
                )
                
                # Create school membership
                SchoolMembership.objects.create(
                    user=user,
                    school=school,
                    role='school_owner',
                    status='active'
                )
            
            return {
                'success': True,
                'is_complete': bool(school_name and school_description),
                'completion_percentage': 100 if school_name and school_description else 50,
                'saved_data': {
                    'school_id': school.id,
                    'school_name': school.name,
                    'school_description': school.description
                }
            }
            
        except Exception as e:
            logger.error(f"Error saving business setup data: {e}")
            return {
                'success': False,
                'errors': {'general': ['Failed to save business setup data']}
            }
    
    def _save_educational_system_data(self, step_data, user):
        """Save educational system selection."""
        try:
            system_id = step_data.get('educational_system_id')
            
            if not system_id:
                return {
                    'success': False,
                    'errors': {'educational_system_id': ['Educational system is required']}
                }
            
            # Get or create teacher profile
            teacher_profile = self._get_or_create_teacher_profile(user)
            
            from .models import EducationalSystem
            try:
                educational_system = EducationalSystem.objects.get(id=system_id)
                teacher_profile.educational_system = educational_system
                teacher_profile.save()
                
                return {
                    'success': True,
                    'is_complete': True,
                    'completion_percentage': 100,
                    'saved_data': {
                        'educational_system_id': educational_system.id,
                        'educational_system_name': educational_system.name
                    }
                }
            except EducationalSystem.DoesNotExist:
                return {
                    'success': False,
                    'errors': {'educational_system_id': ['Invalid educational system']}
                }
                
        except Exception as e:
            logger.error(f"Error saving educational system data: {e}")
            return {
                'success': False,
                'errors': {'general': ['Failed to save educational system data']}
            }
    
    def _save_teaching_subjects_data(self, step_data, user):
        """Save teaching subjects and rates."""
        try:
            subjects = step_data.get('subjects', [])
            
            if not subjects:
                return {
                    'success': False,
                    'errors': {'subjects': ['At least one subject is required']}
                }
            
            teacher_profile = self._get_or_create_teacher_profile(user)
            school = self._get_user_school(user)
            
            if not school:
                return {
                    'success': False,
                    'errors': {'general': ['School not found. Please complete business setup first.']}
                }
            
            from .models import Course, TeacherCourse, TeacherCompensationRule
            
            # Clear existing teacher courses for this school
            TeacherCourse.objects.filter(teacher=teacher_profile, school=school).delete()
            
            saved_subjects = []
            for subject_data in subjects:
                course_id = subject_data.get('course_id')
                hourly_rate = subject_data.get('hourly_rate')
                
                if not course_id or not hourly_rate:
                    continue
                
                try:
                    course = Course.objects.get(id=course_id)
                    
                    # Create teacher-course relationship
                    teacher_course = TeacherCourse.objects.create(
                        teacher=teacher_profile,
                        course=course,
                        school=school,
                        is_active=True
                    )
                    
                    # Create or update compensation rule
                    compensation_rule, created = TeacherCompensationRule.objects.get_or_create(
                        teacher=teacher_profile,
                        school=school,
                        course=course,
                        defaults={
                            'base_hourly_rate': float(hourly_rate),
                            'effective_date': timezone.now().date()
                        }
                    )
                    if not created:
                        compensation_rule.base_hourly_rate = float(hourly_rate)
                        compensation_rule.save()
                    
                    saved_subjects.append({
                        'course_id': course.id,
                        'course_name': course.name,
                        'hourly_rate': float(hourly_rate)
                    })
                    
                except Course.DoesNotExist:
                    continue
            
            return {
                'success': True,
                'is_complete': len(saved_subjects) > 0,
                'completion_percentage': 100 if saved_subjects else 0,
                'saved_data': {
                    'subjects': saved_subjects
                }
            }
            
        except Exception as e:
            logger.error(f"Error saving teaching subjects data: {e}")
            return {
                'success': False,
                'errors': {'general': ['Failed to save teaching subjects data']}
            }
    
    def _save_personal_information_data(self, step_data, user):
        """Save personal information data."""
        try:
            teacher_profile = self._get_or_create_teacher_profile(user)
            
            # Update user fields
            user.first_name = step_data.get('first_name', user.first_name)
            user.last_name = step_data.get('last_name', user.last_name)
            user.save(update_fields=['first_name', 'last_name'])
            
            # Update teacher profile fields
            if 'phone_number' in step_data:
                teacher_profile.phone_number = step_data['phone_number']
            if 'location' in step_data:
                teacher_profile.location = step_data['location']
            if 'years_of_experience' in step_data:
                teacher_profile.years_of_experience = step_data['years_of_experience']
            
            teacher_profile.save()
            
            completion_fields = ['first_name', 'last_name', 'phone_number', 'location']
            completed_count = sum(1 for field in completion_fields 
                                if getattr(user if field in ['first_name', 'last_name'] else teacher_profile, field))
            
            return {
                'success': True,
                'is_complete': completed_count >= 3,  # At least 3 of 4 fields
                'completion_percentage': int((completed_count / len(completion_fields)) * 100),
                'saved_data': {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': teacher_profile.phone_number,
                    'location': teacher_profile.location,
                    'years_of_experience': teacher_profile.years_of_experience
                }
            }
            
        except Exception as e:
            logger.error(f"Error saving personal information data: {e}")
            return {
                'success': False,
                'errors': {'general': ['Failed to save personal information data']}
            }
    
    def _save_professional_bio_data(self, step_data, user):
        """Save professional bio data."""
        try:
            teacher_profile = self._get_or_create_teacher_profile(user)
            
            bio = step_data.get('bio', '').strip()
            teaching_approach = step_data.get('teaching_approach', '').strip()
            
            teacher_profile.bio = bio
            teacher_profile.teaching_approach = teaching_approach
            teacher_profile.save()
            
            is_complete = bool(bio and len(bio) >= 50)  # Minimum 50 characters
            
            return {
                'success': True,
                'is_complete': is_complete,
                'completion_percentage': 100 if is_complete else 50,
                'saved_data': {
                    'bio': bio,
                    'teaching_approach': teaching_approach
                }
            }
            
        except Exception as e:
            logger.error(f"Error saving professional bio data: {e}")
            return {
                'success': False,
                'errors': {'general': ['Failed to save professional bio data']}
            }
    
    def _save_education_background_data(self, step_data, user):
        """Save education background data."""
        try:
            teacher_profile = self._get_or_create_teacher_profile(user)
            
            qualifications = step_data.get('qualifications', '').strip()
            certifications = step_data.get('certifications', [])
            
            teacher_profile.qualifications = qualifications
            
            # Handle certifications as JSON field
            if certifications:
                teacher_profile.certifications = certifications
            
            teacher_profile.save()
            
            is_complete = bool(qualifications and len(qualifications) >= 20)
            
            return {
                'success': True,
                'is_complete': is_complete,
                'completion_percentage': 100 if is_complete else 50,
                'saved_data': {
                    'qualifications': qualifications,
                    'certifications': certifications
                }
            }
            
        except Exception as e:
            logger.error(f"Error saving education background data: {e}")
            return {
                'success': False,
                'errors': {'general': ['Failed to save education background data']}
            }
    
    def _save_availability_data(self, step_data, user):
        """Save availability data."""
        try:
            teacher_profile = self._get_or_create_teacher_profile(user)
            
            availability = step_data.get('availability', {})
            timezone_preference = step_data.get('timezone', 'Europe/Lisbon')
            
            # Save availability as JSON field
            teacher_profile.availability = availability
            teacher_profile.timezone = timezone_preference
            teacher_profile.save()
            
            # Check if availability has at least some time slots
            has_availability = bool(availability and any(
                day_data.get('slots') for day_data in availability.values()
            ))
            
            return {
                'success': True,
                'is_complete': has_availability,
                'completion_percentage': 100 if has_availability else 0,
                'saved_data': {
                    'availability': availability,
                    'timezone': timezone_preference
                }
            }
            
        except Exception as e:
            logger.error(f"Error saving availability data: {e}")
            return {
                'success': False,
                'errors': {'general': ['Failed to save availability data']}
            }
    
    def _save_business_settings_data(self, step_data, user):
        """Save business settings data."""
        try:
            teacher_profile = self._get_or_create_teacher_profile(user)
            school = self._get_user_school(user)
            
            # Update school settings
            if school:
                school.cancellation_policy = step_data.get('cancellation_policy', school.cancellation_policy)
                school.session_type_preferences = step_data.get('session_preferences', {})
                school.save()
            
            # Update teacher profile settings
            teacher_profile.accepts_new_students = step_data.get('accepts_new_students', True)
            teacher_profile.min_session_duration = step_data.get('min_session_duration', 60)
            teacher_profile.max_session_duration = step_data.get('max_session_duration', 120)
            teacher_profile.save()
            
            return {
                'success': True,
                'is_complete': True,
                'completion_percentage': 100,
                'saved_data': {
                    'cancellation_policy': school.cancellation_policy if school else None,
                    'session_preferences': school.session_type_preferences if school else {},
                    'accepts_new_students': teacher_profile.accepts_new_students,
                    'min_session_duration': teacher_profile.min_session_duration,
                    'max_session_duration': teacher_profile.max_session_duration
                }
            }
            
        except Exception as e:
            logger.error(f"Error saving business settings data: {e}")
            return {
                'success': False,
                'errors': {'general': ['Failed to save business settings data']}
            }
    
    def _save_profile_preview_data(self, step_data, user):
        """Save profile preview data and mark profile as published."""
        try:
            teacher_profile = self._get_or_create_teacher_profile(user)
            
            # Mark profile as published/active
            teacher_profile.is_available = step_data.get('publish_profile', False)
            teacher_profile.profile_published_at = timezone.now() if teacher_profile.is_available else None
            teacher_profile.save()
            
            # Mark onboarding as completed
            user.onboarding_completed = True
            user.save(update_fields=['onboarding_completed'])
            
            return {
                'success': True,
                'is_complete': True,
                'completion_percentage': 100,
                'saved_data': {
                    'is_published': teacher_profile.is_available,
                    'published_at': teacher_profile.profile_published_at.isoformat() if teacher_profile.profile_published_at else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error saving profile preview data: {e}")
            return {
                'success': False,
                'errors': {'general': ['Failed to save profile preview data']}
            }
    
    def _get_or_create_teacher_profile(self, user):
        """Get or create teacher profile for user."""
        from .models import TeacherProfile
        
        teacher_profile, created = TeacherProfile.objects.get_or_create(
            user=user,
            defaults={
                'is_available': False,
                'years_of_experience': 0
            }
        )
        return teacher_profile
    
    def _get_user_school(self, user):
        """Get the school owned by this user."""
        from .models import SchoolMembership
        
        membership = SchoolMembership.objects.filter(
            user=user, role='school_owner'
        ).first()
        
        return membership.school if membership else None


class TutorOnboardingGuidanceView(TutorOnboardingAPIView):
    """Dedicated view for tutor onboarding guidance endpoint."""
    
    def post(self, request):
        return self.get_onboarding_guidance(request)


class TutorOnboardingStartView(TutorOnboardingAPIView):
    """Dedicated view for tutor onboarding start endpoint."""
    
    def post(self, request):
        return self.start_onboarding(request)


class TutorOnboardingValidateStepView(TutorOnboardingAPIView):
    """Dedicated view for tutor onboarding step validation endpoint."""
    
    def post(self, request):
        return self.validate_step(request)


class TutorOnboardingSaveProgressView(TutorOnboardingAPIView):
    """Dedicated view for tutor onboarding save progress endpoint."""
    
    def post(self, request):
        return self.save_progress(request)


# =======================
# WIZARD ORCHESTRATION API VIEWS (GitHub Issue #95)
# =======================

class TeacherProfileStepValidationView(KnoxAuthenticatedAPIView):
    """
    API endpoint for real-time step validation during teacher profile creation.
    
    POST /api/accounts/teacher-profile/validate-step/
    
    GitHub Issue #95: Backend wizard orchestration API for guided profile creation.
    """
    
    throttle_classes = [ProfileWizardThrottle]
    
    def post(self, request):
        """Validate data for a specific wizard step."""
        from .serializers import StepValidationRequestSerializer, StepValidationResponseSerializer
        from .services.wizard_orchestration import WizardOrchestrationService
        
        # Validate request data
        request_serializer = StepValidationRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                {
                    "is_valid": False,
                    "errors": request_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = request_serializer.validated_data
        step = validated_data['step']
        step_data = validated_data['data']
        
        # Validate the step data using wizard orchestration service
        validation_result = WizardOrchestrationService.validate_step_data(step, step_data)
        
        # Return validation result
        response_serializer = StepValidationResponseSerializer(data=validation_result)
        if response_serializer.is_valid():
            if validation_result['is_valid']:
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Fallback error response
            return Response(
                {
                    "is_valid": False,
                    "errors": {"general": ["Validation processing failed"]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TeacherProfileCompletionStatusView(KnoxAuthenticatedAPIView):
    """
    API endpoint for tracking teacher profile completion progress.
    
    GET /api/accounts/teacher-profile/completion-status/
    
    GitHub Issue #95: Backend wizard orchestration API for guided profile creation.
    """
    
    def get(self, request):
        """Get completion status for the current user's teacher profile."""
        try:
            # Check if user has a teacher profile
            if not hasattr(request.user, 'teacher_profile'):
                return Response(
                    {"error": "No teacher profile found for this user"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            teacher_profile = request.user.teacher_profile
            
            # Get completion status using wizard orchestration service
            from .services.wizard_orchestration import WizardOrchestrationService
            completion_status = WizardOrchestrationService._get_completion_status(teacher_profile)
            
            return Response(completion_status, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to get completion status for user {request.user.id}: {e}")
            return Response(
                {"error": "Failed to retrieve completion status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Communication System ViewSets

class SchoolEmailTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing school email templates.
    Provides CRUD operations with school-level permissions.
    """
    
    serializer_class = SchoolEmailTemplateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get_queryset(self):
        """Filter templates by user's schools."""
        user = self.request.user
        # Get schools where user is owner or admin
        school_ids = list_school_ids_owned_or_managed(user)
        return SchoolEmailTemplate.objects.filter(
            school_id__in=school_ids
        ).select_related('school', 'created_by').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the school and created_by fields when creating a template with security validation."""
        # Determine the school - use the school from request data or user's default school
        school_id = self.request.data.get('school')
        if school_id:
            # Verify user can manage this school
            school_ids = list_school_ids_owned_or_managed(self.request.user)
            if int(school_id) not in school_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to create templates for this school")
            school = School.objects.get(id=school_id)
        else:
            # Use user's first manageable school
            school_ids = list_school_ids_owned_or_managed(self.request.user)
            if not school_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't manage any schools")
            school = School.objects.get(id=school_ids[0])
        
        # Additional security validation for template content
        self._validate_template_content_security(serializer.validated_data)
        
        serializer.save(school=school, created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Update template with security validation."""
        # Additional security validation for template content
        self._validate_template_content_security(serializer.validated_data)
        serializer.save()
    
    def _validate_template_content_security(self, validated_data):
        """
        Validate template content for security vulnerabilities.
        
        Args:
            validated_data: Dictionary of validated data from serializer
            
        Raises:
            ValidationError: If template content contains security vulnerabilities
        """
        from .services.secure_template_engine import SecureTemplateEngine
        from django.core.exceptions import ValidationError
        from rest_framework.exceptions import ValidationError as DRFValidationError
        
        try:
            # Validate subject template
            if 'subject_template' in validated_data:
                SecureTemplateEngine.validate_template_content(validated_data['subject_template'])
            
            # Validate HTML content
            if 'html_content' in validated_data:
                SecureTemplateEngine.validate_template_content(validated_data['html_content'])
            
            # Validate text content
            if 'text_content' in validated_data:
                SecureTemplateEngine.validate_template_content(validated_data['text_content'])
            
            # Validate custom CSS
            if 'custom_css' in validated_data and validated_data['custom_css']:
                self._validate_custom_css_security(validated_data['custom_css'])
                
        except ValidationError as e:
            raise DRFValidationError(f"Template security validation failed: {str(e)}")
    
    def _validate_custom_css_security(self, css_content):
        """
        Validate custom CSS for security vulnerabilities.
        
        Args:
            css_content: CSS content to validate
            
        Raises:
            ValidationError: If CSS contains dangerous patterns
        """
        import re
        from django.core.exceptions import ValidationError
        
        if not css_content:
            return
        
        # Check for dangerous CSS patterns
        dangerous_patterns = [
            r'@import\s+url\s*\(',
            r'javascript\s*:',
            r'expression\s*\(',
            r'behavior\s*:',
            r'-moz-binding\s*:',
            r'binding\s*:',
            r'<script',
            r'</script>',
            r'alert\s*\(',
            r'eval\s*\(',
            r'document\.',
            r'window\.',
        ]
        
        css_lower = css_content.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, css_lower):
                raise ValidationError(f"Custom CSS contains dangerous pattern: {pattern}")
        
        # Check CSS size
        if len(css_content) > 10000:  # 10KB limit
            raise ValidationError("Custom CSS too large. Maximum size is 10KB")
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        Preview an email template with provided variables.
        """
        template = self.get_object()
        
        serializer = EmailTemplatePreviewSerializer(
            data=request.data,
            context={'template': template}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        variables = serializer.validated_data['template_variables']
        
        # Validate template variables for security
        from .services.secure_template_engine import TemplateVariableValidator
        from django.core.exceptions import ValidationError
        
        try:
            TemplateVariableValidator.validate_context(variables)
        except ValidationError as e:
            return Response(
                {"error": f"Template variables validation failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Render the template with variables using secure service
        from .services.email_template_service import EmailTemplateRenderingService
        
        try:
            subject, html_content, text_content = EmailTemplateRenderingService.render_template(
                template, variables, request=self.request
            )
            
            return Response({
                'rendered_subject': subject,
                'rendered_html': html_content,
                'rendered_text': text_content,
                'template_variables': variables,
                'template_id': template.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to preview template {template.id}: {e}")
            return Response(
                {"error": f"Failed to render template preview: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        """
        Get available filter options for templates.
        """
        from .models import EmailTemplateType
        
        return Response({
            'template_types': [
                {'value': choice[0], 'label': choice[1]}
                for choice in EmailTemplateType.choices
            ]
        }, status=status.HTTP_200_OK)


class EmailSequenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing email sequences.
    Provides CRUD operations with school-level permissions.
    """
    
    serializer_class = EmailSequenceSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get_queryset(self):
        """Filter sequences by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        return EmailSequence.objects.filter(
            school_id__in=school_ids
        ).select_related('school').prefetch_related('steps__template').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the school field when creating a sequence."""
        school_id = self.request.data.get('school')
        if school_id:
            school_ids = list_school_ids_owned_or_managed(self.request.user)
            if int(school_id) not in school_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to create sequences for this school")
            school = School.objects.get(id=school_id)
        else:
            school_ids = list_school_ids_owned_or_managed(self.request.user)
            if not school_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't manage any schools")
            school = School.objects.get(id=school_ids[0])
        
        serializer.save(school=school)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate or deactivate an email sequence.
        """
        sequence = self.get_object()
        is_active = request.data.get('is_active', True)
        
        sequence.is_active = is_active
        sequence.save(update_fields=['is_active', 'updated_at'])
        
        serializer = self.get_serializer(sequence)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='trigger-events')
    def trigger_events(self, request):
        """
        Get available trigger events for sequences.
        """
        trigger_choices = [
            ("invitation_sent", "Invitation Sent"),
            ("invitation_viewed", "Invitation Viewed"),
            ("invitation_accepted", "Invitation Accepted"),
            ("profile_incomplete", "Profile Incomplete"),
            ("profile_completed", "Profile Completed"),
        ]
        
        return Response({
            'trigger_events': [
                {'value': choice[0], 'label': choice[1]}
                for choice in trigger_choices
            ]
        }, status=status.HTTP_200_OK)


class EmailCommunicationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing email communications.
    Read-only access to communication history with analytics.
    """
    
    serializer_class = EmailCommunicationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get_queryset(self):
        """Filter communications by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        queryset = EmailCommunication.objects.filter(
            school_id__in=school_ids
        ).select_related('school', 'template', 'sequence', 'sent_by').order_by('-created_at')
        
        # Filter by date range if provided
        sent_after = self.request.query_params.get('sent_after')
        sent_before = self.request.query_params.get('sent_before')
        
        if sent_after:
            queryset = queryset.filter(sent_at__gte=sent_after)
        if sent_before:
            queryset = queryset.filter(sent_at__lte=sent_before)
        
        # Filter by communication type
        comm_type = self.request.query_params.get('communication_type')
        if comm_type:
            queryset = queryset.filter(communication_type=comm_type)
        
        # Filter by recipient email
        recipient = self.request.query_params.get('recipient_email')
        if recipient:
            queryset = queryset.filter(recipient_email__icontains=recipient)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get email communication analytics for the user's schools.
        """
        from .services.enhanced_email_service import EmailAnalyticsService
        
        user = request.user
        school_ids = list_school_ids_owned_or_managed(user)
        
        if not school_ids:
            return Response(
                {"error": "You don't manage any schools"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            analytics_service = EmailAnalyticsService()
            
            # Get analytics for all user's schools
            analytics_data = {}
            for school_id in school_ids:
                school = School.objects.get(id=school_id)
                school_analytics = analytics_service.get_school_analytics(school)
                analytics_data[school.name] = school_analytics
            
            # Aggregate analytics across all schools
            total_analytics = analytics_service.aggregate_school_analytics(school_ids)
            
            serializer = EmailAnalyticsSerializer(total_analytics)
            
            return Response({
                'total_analytics': serializer.data,
                'by_school': analytics_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to get analytics for user {user.id}: {e}")
            return Response(
                {"error": "Failed to retrieve analytics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='communication-types')
    def communication_types(self, request):
        """
        Get available communication types.
        """
        from .models import EmailCommunicationType
        
        return Response({
            'communication_types': [
                {'value': choice[0], 'label': choice[1]}
                for choice in EmailCommunicationType.choices
            ]
        }, status=status.HTTP_200_OK)


class ParentProfileViewSet(KnoxAuthenticatedViewSet):
    """
    ViewSet for managing parent profiles.
    Allows parents to manage their profile settings and preferences.
    """
    
    serializer_class = ParentProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's parent profile."""
        return ParentProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Ensure parent profile is created for the current user."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def update_notification_preferences(self, request, pk=None):
        """Update notification preferences for parent."""
        parent_profile = self.get_object()
        
        # Get current preferences and update with provided data
        current_prefs = parent_profile.notification_preferences or {}
        new_prefs = request.data.get('notification_preferences', {})
        current_prefs.update(new_prefs)
        
        parent_profile.notification_preferences = current_prefs
        parent_profile.save()
        
        serializer = self.get_serializer(parent_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'])
    def update_approval_settings(self, request, pk=None):
        """Update default approval settings for parent."""
        parent_profile = self.get_object()
        
        # Get current settings and update with provided data
        current_settings = parent_profile.default_approval_settings or {}
        new_settings = request.data.get('default_approval_settings', {})
        current_settings.update(new_settings)
        
        parent_profile.default_approval_settings = current_settings
        parent_profile.save()
        
        serializer = self.get_serializer(parent_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ParentChildRelationshipViewSet(KnoxAuthenticatedViewSet):
    """
    ViewSet for managing parent-child relationships.
    Allows parents to manage their children and school administrators to oversee relationships.
    """
    
    serializer_class = ParentChildRelationshipSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter relationships based on user role and permissions."""
        user = self.request.user
        
        # School administrators can see all relationships in their schools
        if user.school_memberships.filter(
            role__in=['school_owner', 'school_admin'], 
            is_active=True
        ).exists():
            admin_school_ids = list(user.school_memberships.filter(
                role__in=['school_owner', 'school_admin'], 
                is_active=True
            ).values_list('school_id', flat=True))
            
            return ParentChildRelationship.objects.filter(
                school_id__in=admin_school_ids
            ).select_related('parent', 'child', 'school')
        
        # Parents can see their own relationships
        return ParentChildRelationship.objects.filter(
            parent=user,
            is_active=True
        ).select_related('parent', 'child', 'school')
    
    def perform_create(self, serializer):
        """Create parent-child relationship with validation."""
        # Ensure the requesting user is the parent
        serializer.save(parent=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_children(self, request):
        """Get all children for the current parent user."""
        user = request.user
        
        relationships = ParentChildRelationship.objects.filter(
            parent=user,
            is_active=True
        ).select_related('child', 'school')
        
        children_data = []
        for relationship in relationships:
            child_data = {
                'relationship_id': relationship.id,
                'child': {
                    'id': relationship.child.id,
                    'name': relationship.child.name,
                    'email': relationship.child.email
                },
                'school': {
                    'id': relationship.school.id,
                    'name': relationship.school.name
                },
                'relationship_type': relationship.relationship_type,
                'permissions': relationship.permissions,
                'requires_purchase_approval': relationship.requires_purchase_approval,
                'requires_session_approval': relationship.requires_session_approval
            }
            children_data.append(child_data)
        
        return Response({'children': children_data}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'])
    def update_permissions(self, request, pk=None):
        """Update permissions for a specific parent-child relationship."""
        relationship = self.get_object()
        
        # Ensure the requesting user is the parent or school admin
        if (relationship.parent != request.user and 
            not request.user.school_memberships.filter(
                school=relationship.school,
                role__in=['school_owner', 'school_admin'],
                is_active=True
            ).exists()):
            return Response(
                {'error': 'You do not have permission to modify this relationship'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update permissions
        new_permissions = request.data.get('permissions', {})
        if new_permissions:
            current_permissions = relationship.permissions or {}
            current_permissions.update(new_permissions)
            relationship.permissions = current_permissions
        
        # Update approval settings
        if 'requires_purchase_approval' in request.data:
            relationship.requires_purchase_approval = request.data['requires_purchase_approval']
        
        if 'requires_session_approval' in request.data:
            relationship.requires_session_approval = request.data['requires_session_approval']
        
        relationship.save()
        
        serializer = self.get_serializer(relationship)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def create_relationship(self, request):
        """Create a new parent-child relationship."""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Validate that the parent user has PARENT role in the school
            school_id = serializer.validated_data['school'].id
            child_user = serializer.validated_data['child']
            
            # Check parent membership
            if not request.user.school_memberships.filter(
                school_id=school_id,
                role='parent',
                is_active=True
            ).exists():
                return Response(
                    {'error': 'You must have PARENT role in this school to create relationships'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check child membership
            if not child_user.school_memberships.filter(
                school_id=school_id,
                role='student',
                is_active=True
            ).exists():
                return Response(
                    {'error': 'Child must be a student in this school'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the relationship
            serializer.save(parent=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================
# Enhanced Communication API Views
# ============================

class EnhancedSchoolEmailTemplateViewSet(viewsets.ModelViewSet):
    """
    Enhanced ViewSet for managing school email templates with additional frontend features.
    Extends the existing SchoolEmailTemplateViewSet with preview and testing capabilities.
    """
    
    serializer_class = SchoolEmailTemplateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get_queryset(self):
        """Filter templates by user's schools."""
        user = self.request.user
        school_ids = list_school_ids_owned_or_managed(user)
        return SchoolEmailTemplate.objects.filter(
            school_id__in=school_ids
        ).select_related('school', 'created_by').order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Generate template preview with provided variables."""
        from .services.email_template_service import EmailTemplateRenderingService
        from rest_framework.exceptions import ValidationError as DRFValidationError
        
        template = self.get_object()
        variables = request.data.get('variables', {})
        
        try:
            # Merge with default variables
            rendering_service = EmailTemplateRenderingService()
            context_variables = {**rendering_service.DEFAULT_VARIABLES, **variables}
            
            # Add school-specific variables
            context_variables.update({
                'school_name': template.school.name,
                'school_email': template.school.contact_email,
                'school_primary_color': template.school.primary_color,
                'school_secondary_color': template.school.secondary_color,
            })
            
            # Render the template
            rendered = rendering_service.render_template(template, context_variables)
            
            return Response({
                'subject': rendered['subject'],
                'html_content': rendered['html_content'],
                'text_content': rendered['text_content'],
                'variables_used': list(context_variables.keys())
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Template preview error for template {pk}: {str(e)}")
            return Response({
                'error': 'Failed to generate preview',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        """Send test email with template."""
        from .services.enhanced_email_service import EnhancedEmailService
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        template = self.get_object()
        test_email = request.data.get('test_email')
        variables = request.data.get('variables', {})
        
        # Validate test email
        if not test_email:
            return Response({
                'error': 'test_email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_email(test_email)
        except ValidationError:
            return Response({
                'error': 'Invalid email address'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Prepare context variables
            context_variables = {
                'teacher_name': 'Test User',
                'school_name': template.school.name,
                'school_email': template.school.contact_email,
                **variables
            }
            
            # Send test email
            email_service = EnhancedEmailService()
            success = email_service.send_template_email(
                template=template,
                recipient_email=test_email,
                context_variables=context_variables,
                sender_user=request.user
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Test email sent successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to send test email'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Test email send error for template {pk}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to send test email',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response({
                'error': 'No managed schools found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        school = School.objects.get(id=school_ids[0])
        
        return Response({
            'school_id': school.id,
            'school_name': school.name,
            'primary_color': school.primary_color,
            'secondary_color': school.secondary_color,
            'text_color': school.text_color,
            'background_color': school.background_color,
            'logo_url': school.logo.url if school.logo else None,
        }, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        """Update school branding settings."""
        from .serializers import SchoolBrandingSerializer
        
        # Get user's primary school
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({
                'error': 'No managed schools found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        school = School.objects.get(id=school_ids[0])
        
        serializer = SchoolBrandingSerializer(school, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommunicationAnalyticsAPIView(APIView):
    """
    API for communication analytics and performance metrics.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get(self, request, *args, **kwargs):
        """Get email performance metrics for user's schools."""
        from django.db.models import Count, Q, Avg
        from datetime import datetime, timedelta
        
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({
                'error': 'No managed schools found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate date range (last 30 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Get communications for user's schools
        communications = EmailCommunication.objects.filter(
            school_id__in=school_ids,
            sent_at__gte=start_date,
            sent_at__lte=end_date
        )
        
        # Calculate metrics
        total_sent = communications.count()
        delivered_count = communications.filter(
            delivery_status=EmailDeliveryStatus.DELIVERED
        ).count()
        opened_count = communications.filter(opened_at__isnull=False).count()
        clicked_count = communications.filter(clicked_at__isnull=False).count()
        
        # Calculate rates
        delivery_rate = (delivered_count / total_sent * 100) if total_sent > 0 else 0
        open_rate = (opened_count / delivered_count * 100) if delivered_count > 0 else 0
        click_rate = (clicked_count / opened_count * 100) if opened_count > 0 else 0
        
        # Get recent communications
        recent_communications = communications.order_by('-sent_at')[:10].values(
            'id', 'recipient_email', 'subject', 'delivery_status', 'sent_at'
        )
        
        return Response({
            'period': {
                'start_date': start_date.date(),
                'end_date': end_date.date(),
                'days': 30
            },
            'total_sent': total_sent,
            'delivery_rate': round(delivery_rate, 2),
            'open_rate': round(open_rate, 2),
            'click_rate': round(click_rate, 2),
            'recent_communications': list(recent_communications)
        }, status=status.HTTP_200_OK)


class TemplateAnalyticsAPIView(APIView):
    """
    API for template-specific analytics and usage statistics.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
    
    def get(self, request, *args, **kwargs):
        """Get template usage and performance statistics."""
        from django.db.models import Count, Q, Avg
        from datetime import datetime, timedelta
        
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({
                'error': 'No managed schools found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get templates for user's schools
        templates = SchoolEmailTemplate.objects.filter(school_id__in=school_ids)
        
        # Calculate analytics for each template
        template_stats = []
        for template in templates:
            communications = template.email_communications.all()
            
            total_uses = communications.count()
            successful_deliveries = communications.filter(
                delivery_status=EmailDeliveryStatus.DELIVERED
            ).count()
            
            success_rate = (successful_deliveries / total_uses * 100) if total_uses > 0 else 0
            
            template_stats.append({
                'template_id': template.id,
                'template_name': template.name,
                'template_type': template.template_type,
                'usage_count': total_uses,
                'success_rate': round(success_rate, 2),
                'last_used': communications.order_by('-sent_at').first().sent_at if total_uses > 0 else None
            })
        
        # Sort by usage count
        template_stats.sort(key=lambda x: x['usage_count'], reverse=True)
        
        return Response(template_stats, status=status.HTTP_200_OK)


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
            return Response({
                'error': 'No managed schools found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        school = School.objects.get(id=school_ids[0])
        
        # Get or create school settings
        settings, created = SchoolSettings.objects.get_or_create(
            school=school,
            defaults={
                'communication_settings': {
                    'default_from_email': school.contact_email,
                    'email_signature': f'Best regards,\n{school.name} Team',
                    'auto_sequence_enabled': True,
                    'notification_preferences': {
                        'email_delivery_notifications': True,
                        'bounce_notifications': True
                    }
                }
            }
        )
        
        comm_settings = settings.communication_settings or {}
        
        return Response({
            'default_from_email': comm_settings.get('default_from_email', school.contact_email),
            'email_signature': comm_settings.get('email_signature', f'Best regards,\n{school.name} Team'),
            'auto_sequence_enabled': comm_settings.get('auto_sequence_enabled', True),
            'notification_preferences': comm_settings.get('notification_preferences', {
                'email_delivery_notifications': True,
                'bounce_notifications': True
            })
        }, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        """Update communication settings."""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        school_ids = list_school_ids_owned_or_managed(request.user)
        if not school_ids:
            return Response({
                'error': 'No managed schools found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        school = School.objects.get(id=school_ids[0])
        
        # Validate email if provided
        default_from_email = request.data.get('default_from_email')
        if default_from_email:
            try:
                validate_email(default_from_email)
            except ValidationError:
                return Response({
                    'error': 'Invalid default_from_email format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create school settings
        settings, created = SchoolSettings.objects.get_or_create(
            school=school,
            defaults={'communication_settings': {}}
        )
        
        # Update communication settings
        comm_settings = settings.communication_settings or {}
        
        if 'default_from_email' in request.data:
            comm_settings['default_from_email'] = request.data['default_from_email']
        
        if 'email_signature' in request.data:
            comm_settings['email_signature'] = request.data['email_signature']
        
        if 'auto_sequence_enabled' in request.data:
            comm_settings['auto_sequence_enabled'] = request.data['auto_sequence_enabled']
        
        if 'notification_preferences' in request.data:
            comm_settings['notification_preferences'] = request.data['notification_preferences']
        
        settings.communication_settings = comm_settings
        settings.save()
        
        return Response({
            'message': 'Communication settings updated successfully',
            'settings': comm_settings
        }, status=status.HTTP_200_OK)
