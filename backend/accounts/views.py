import logging

from common.messaging import send_email_verification_code
from common.throttles import (
    EmailBasedThrottle,
    EmailCodeRequestThrottle,
    IPBasedThrottle,
    IPSignupThrottle,
)
from django.contrib.auth import login
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .db_queries import (
    create_school_owner,
    get_user_by_email,
    list_school_ids_owned_or_managed,
    list_users_by_request_permissions,
    user_exists,
)
from .models import (
    School,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherProfile,
    VerificationCode,
)
from .permissions import (
    IsOwnerOrSchoolAdmin,
    IsSchoolOwnerOrAdmin,
    IsStudentInAnySchool,
    IsTeacherInAnySchool,
)
from .serializers import (
    CreateUserSerializer,
    RequestCodeSerializer,
    SchoolMembershipSerializer,
    SchoolSerializer,
    SchoolWithMembersSerializer,
    StudentSerializer,
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

        # Stats based on primary role
        stats = {}

        # If user is a school owner or admin in any school
        admin_school_ids = list_school_ids_owned_or_managed(user)
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
            # Log the event internally
            logger.info(f"Code requested for non-existent email: {email}")
            # Perform a dummy code generation for non-existent users to ensure constant time
            dummy_code = VerificationCode.generate_code("dummy@example.com")
            _ = dummy_code.get_current_code()
            return Response(
                {
                    "message": "If an account exists with this email, a verification code has been sent."
                },
                status=status.HTTP_200_OK,
            )

        verification = VerificationCode.generate_code(email)
        code = verification.get_current_code()
        try:
            send_email_verification_code(email, code)
        except Exception as e:
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

    def get_queryset(self):
        user = self.request.user
        # System admins can see all schools
        if user.is_staff or user.is_superuser:
            return School.objects.all()

        # Users can see schools they're members of
        school_ids = SchoolMembership.objects.filter(user=user, is_active=True).values_list(
            "school_id", flat=True
        )

        return School.objects.filter(id__in=school_ids)

    def get_permissions(self):
        if self.action == "create":
            # Any authenticated user can create a school (becoming its owner)
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only school owner/admin can modify school
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            # For list, retrieve, etc.
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        # Create the school
        school = serializer.save()

        # Create a membership for the creator as school owner
        SchoolMembership.objects.create(
            user=self.request.user,
            school=school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True,
        )

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """
        Get detailed information about the school including its members
        """
        school = self.get_object()
        serializer = SchoolWithMembersSerializer(school)
        return Response(serializer.data)


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

        # Teachers can see their own profile
        if hasattr(user, "teacher_profile"):
            return TeacherProfile.objects.filter(user=user)

        return TeacherProfile.objects.none()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        else:
            permission_classes = [IsAuthenticated, IsTeacherInAnySchool]
        return [permission() for permission in permission_classes]


class StudentViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for student profiles.
    """

    serializer_class = StudentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return StudentProfile.objects.all()

        # School owners and admins can see students in their schools
        admin_school_ids = list_school_ids_owned_or_managed(user)
        if len(admin_school_ids) > 0:
            # Get the schools where user is an admin

            # Get all student users in these schools
            student_user_ids = SchoolMembership.objects.filter(
                school_id__in=admin_school_ids, role=SchoolRole.STUDENT, is_active=True
            ).values_list("user_id", flat=True)

            return StudentProfile.objects.filter(user_id__in=student_user_ids)

        # Teachers can see students in schools where they teach
        if SchoolMembership.objects.filter(
            user=user, role=SchoolRole.TEACHER, is_active=True
        ).exists():
            # Get the schools where user is a teacher
            teacher_school_ids = SchoolMembership.objects.filter(
                user=user, role=SchoolRole.TEACHER, is_active=True
            ).values_list("school_id", flat=True)

            # Get all student users in these schools
            student_user_ids = SchoolMembership.objects.filter(
                school_id__in=teacher_school_ids,
                role=SchoolRole.STUDENT,
                is_active=True,
            ).values_list("user_id", flat=True)

            return StudentProfile.objects.filter(user_id__in=student_user_ids)

        # Students can see their own profile
        if hasattr(user, "student_profile"):
            return StudentProfile.objects.filter(user=user)

        return StudentProfile.objects.none()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "onboarding"]:
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        else:
            permission_classes = [IsAuthenticated, IsStudentInAnySchool]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def onboarding(self, request):
        """
        Handle student onboarding to complete their profile
        """
        user = request.user

        # Check if student profile already exists
        try:
            # Just check if profile exists, no need to store in variable
            StudentProfile.objects.get(user=user)
            return Response(
                {"message": "Your profile is already complete."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except StudentProfile.DoesNotExist:
            # Create new profile
            serializer = StudentSerializer(data=request.data)
            if serializer.is_valid():
                # Set the user and save
                serializer.save(user=user)
                return Response(
                    {"message": "Student profile created successfully."},
                    status=status.HTTP_201_CREATED,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
