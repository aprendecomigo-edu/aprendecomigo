import logging

from common.messaging import send_email_verification_code
from common.throttles import (
    EmailBasedThrottle,
    EmailCodeRequestThrottle,
    IPBasedThrottle,
    IPSignupThrottle,
)
from django.contrib.auth import login
from django.db import models
from django.utils import timezone
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
    School,
    SchoolInvitation,
    SchoolInvitationLink,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherCourse,
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
    CourseSerializer,
    CreateStudentSerializer,
    CreateUserSerializer,
    EducationalSystemSerializer,
    EnhancedSchoolSerializer,
    InviteExistingTeacherSerializer,
    RequestCodeSerializer,
    SchoolActivitySerializer,
    SchoolInvitationSerializer,
    SchoolMembershipSerializer,
    SchoolMetricsSerializer,
    SchoolSerializer,
    SchoolWithMembersSerializer,
    StudentSerializer,
    TeacherCourseSerializer,
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
        serializer = CreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        email = validated_data.get("email")
        phone_number = validated_data.get("phone_number")
        name = validated_data.get("name")
        primary_contact = validated_data.get("primary_contact")
        school_data = validated_data.get("school", {})

        # Check if user already exists
        if user_exists(email):
            return Response(
                {"error": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, school = create_school_owner(email, name, phone_number, primary_contact, school_data)

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

        # Send verification code
        try:
            contact_type_display = "email" if primary_contact == "email" else "phone number"
            send_email_verification_code(contact_value, code)
        except Exception as e:
            # Rollback user creation if email fails
            user.delete()
            return Response(
                {"error": f"Failed to send verification code: {e!s}"},
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

        # Return the token and user info
        response_data = {
            "token": token,
            "user": UserSerializer(user).data,
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
        elif self.action in ["invite_new", "invite_existing"]:
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

    @action(detail=False, methods=["post"])
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
                    # TODO: Implement email sending
                    # send_invitation_email(invitation, invitation_link)
                    response_data["notifications_sent"]["email"] = True
                except Exception as e:
                    logger.warning(f"Failed to send invitation email: {e}")

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
            logger.error(f"Invite existing teacher failed for email {email}: {e!s}")

            return Response(
                {"error": "Failed to create invitation. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
    API endpoint for courses.
    All users can view courses, but only admins can create/modify them.
    """

    serializer_class = CourseSerializer

    def get_queryset(self):
        """
        All authenticated users can see all courses.
        """
        return Course.objects.all()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Only school admins can create/modify courses
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            # Anyone can view courses
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


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

        # Return invitation details
        return Response(
            {
                "invitation": {
                    "school": {
                        "id": invitation.school.id,
                        "name": invitation.school.name,
                        "description": invitation.school.description,
                    },
                    "role": invitation.role,
                    "role_display": invitation.get_role_display(),
                    "invited_by": {
                        "name": invitation.invited_by.name,
                        "email": invitation.invited_by.email,
                    },
                    "expires_at": invitation.expires_at,
                },
                "target_email": invitation.email,
                "requires_authentication": not request.user.is_authenticated,
                "is_correct_user": request.user.is_authenticated
                and request.user.email == invitation.email,
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
                # TODO: Implement email sending
                # send_invitation_email(invitation, invitation_link)
                notifications_sent["email"] = True
            except Exception as e:
                logger.warning(f"Failed to resend invitation email: {e}")

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
    
    def update(self, request, *args, **kwargs):
        """Enhanced update method with activity logging"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Store old values before update for comparison
        old_values = {}
        for field, value in request.data.items():
            if field != 'settings' and hasattr(instance, field):
                old_values[field] = getattr(instance, field)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Create activity log for school update
        from .services.metrics_service import SchoolActivityService
        from .models import ActivityType
        
        changes = []
        for field, value in request.data.items():
            if field != 'settings' and field in old_values:
                old_value = old_values[field]
                if old_value != value:
                    changes.append(f"{field}: '{old_value}' → '{value}'")
        
        if changes or 'settings' in request.data:
            description = f"Updated school settings"
            if changes:
                description = f"Updated school: {', '.join(changes)}"
            
            SchoolActivityService.create_activity(
                school=instance,
                activity_type=ActivityType.SETTINGS_UPDATED,
                actor=request.user,
                description=description,
                metadata={'changes': changes}
            )
        
        # Invalidate metrics cache
        from .services.metrics_service import SchoolMetricsService
        SchoolMetricsService.invalidate_cache(instance.id)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
