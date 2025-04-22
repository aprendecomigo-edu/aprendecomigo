from common.permissions import (
    IsManagerOrAdmin,
    IsOwnerOrManager,
    IsStudent,
    IsTeacher,
)
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.mail import send_mail
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import EmailVerificationCode, Student, Teacher
from .serializers import (
    BiometricVerifySerializer,
    EmailRequestSerializer,
    EmailVerifySerializer,
    StudentSerializer,
    TeacherSerializer,
    UserSerializer,
)

User = get_user_model()


# Base class for authenticated views
class KnoxAuthenticatedAPIView(APIView):
    """
    Base class for views that require Knox token authentication.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


# Base class for authenticated viewsets
class KnoxAuthenticatedViewSet(viewsets.ModelViewSet):
    """
    Base class for viewsets that require Knox token authentication.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class UserViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for users.
    """

    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        # Managers and superusers can see all users
        if user.is_staff or user.is_superuser or user.user_type == "manager":
            return User.objects.all()
        # Teachers can see their own profile and assigned students
        elif user.user_type == "teacher" and hasattr(user, "teacher_profile"):
            # TODO: Implement proper student-teacher relationship
            # For now, teachers can only see themselves
            return User.objects.filter(id=user.id)
        # Parents can see their profile and linked students
        elif user.user_type == "parent" and hasattr(user, "parent_profile"):
            # TODO: Implement proper parent-student relationship
            # For now, parents can only see themselves
            return User.objects.filter(id=user.id)
        # Students and others can only see themselves
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        if self.action == "create":
            # Only managers and admins can create users
            permission_classes = [IsAuthenticated, IsManagerOrAdmin]
        elif self.action == "list":
            # Any authenticated user can list, but queryset is filtered appropriately
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only owner or manager can modify user records
            permission_classes = [IsAuthenticated, IsOwnerOrManager]
        elif self.action in ["retrieve", "school_profile", "dashboard_info"]:
            # Any authenticated user can retrieve, but queryset is filtered appropriately
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsOwnerOrManager]
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
            "user_type": user.user_type,
        }

        # Stats based on user type
        stats = {}

        if user.user_type == "manager" or user.is_superuser:
            # Admin stats
            stats = {
                "student_count": User.objects.filter(user_type="student").count(),
                "teacher_count": User.objects.filter(user_type="teacher").count(),
            }
        elif user.user_type == "teacher":
            # Teacher stats
            stats = {
                "today_classes": 0,  # Would need to calculate from scheduling models
                "week_classes": 0,
                "student_count": 0,
                "monthly_earnings": 0,
            }
        elif user.user_type == "student":
            # Student stats
            stats = {
                "upcoming_classes": 0,
                "completed_classes": 0,
                "balance": "$0",
            }

            # Check if student needs onboarding
            needs_onboarding = (
                not hasattr(user, "student_profile") or user.student_profile is None
            )
            user_info["needs_onboarding"] = needs_onboarding

            # Include calendar if available
            if hasattr(user, "student_profile") and user.student_profile:
                user_info["calendar_iframe"] = user.student_profile.calendar_iframe

        return Response({"user_info": user_info, "stats": stats})

    @action(detail=False, methods=["get"])
    def school_profile(self, request):  # noqa: ARG001
        """
        Get school profile information
        """
        # School statistics
        stats = {
            "students": User.objects.filter(user_type="student").count(),
            "teachers": User.objects.filter(user_type="teacher").count(),
            "classes": 0,  # Would need to calculate from scheduling models
            "class_types": 0,
        }

        # School information (placeholders)
        school_info = {
            "founded": "2023",
            "location": "Portugal",
            "website": "www.aprendecomigo.com",
            "email": "contact@aprendecomigo.com",
            "phone": "+351 123 456 789",
            "address": "Lisbon, Portugal",
        }

        return Response({"stats": stats, "school_info": school_info})


class TeacherViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for teacher profiles.
    """

    serializer_class = TeacherSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_type == "manager" or user.is_superuser:
            return Teacher.objects.all()
        if user.user_type == "teacher":
            return Teacher.objects.filter(user=user)
        return Teacher.objects.none()

    def get_permissions(self):
        if self.action in ["list", "retrieve", "update", "partial_update"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsTeacher]
        return [permission() for permission in permission_classes]


class StudentViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for student profiles.
    """

    serializer_class = StudentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_type == "manager" or user.is_superuser:
            return Student.objects.all()
        if user.user_type == "student":
            return Student.objects.filter(user=user)
        return Student.objects.none()

    def get_permissions(self):
        if self.action in [
            "list",
            "retrieve",
            "update",
            "partial_update",
            "onboarding",
        ]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsStudent]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def onboarding(self, request):
        """
        Handle student onboarding to complete their profile
        """
        user = request.user

        # Check if student profile already exists
        try:
            student = Student.objects.get(user=user)
            return Response(
                {"message": "Your profile is already complete."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Student.DoesNotExist:
            # Create new profile
            serializer = StudentSerializer(data=request.data)
            if serializer.is_valid():
                # Set the user and save
                serializer.save(user=user)
                # Refresh to get the full profile data for response
                student = Student.objects.get(user=user)
                return Response(
                    StudentSerializer(student).data, status=status.HTTP_201_CREATED
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Custom throttle classes for authentication
class EmailCodeRequestThrottle(AnonRateThrottle):
    rate = "5/hour"
    scope = "auth_code_request"


class EmailBasedThrottle(AnonRateThrottle):
    """Rate limit based on email address"""

    rate = "10/hour"
    scope = "auth_code_verify_email"

    def get_cache_key(self, request, view):  # noqa: ARG001
        # Get the email from the request data
        email = request.data.get("email", "")
        if not email:
            return None  # No email, no rate limiting

        # Use email for rate limiting
        return f"throttle_{self.scope}_{email}"


class IPBasedThrottle(AnonRateThrottle):
    """Rate limit based on IP address"""

    rate = "30/hour"  # Higher limit for IP since it could be shared (e.g., corporate network)
    scope = "auth_code_verify_ip"


class RequestEmailCodeView(APIView):
    """
    API endpoint for requesting a TOTP verification code.
    Rate limited to prevent abuse.
    """

    authentication_classes: list = []  # No authentication required
    permission_classes = [AllowAny]
    throttle_classes = [EmailCodeRequestThrottle]

    def post(self, request):
        serializer = EmailRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # Generate a verification secret and get the current TOTP code
            verification = EmailVerificationCode.generate_code(email)
            current_code = verification.get_current_code()

            # Send email with current TOTP code
            try:
                send_mail(
                    subject="Your Aprende Comigo Verification Code",
                    message=f"Your verification code is {current_code}. This code will expire in 30 seconds. "
                    f"If it expires, simply request a new code or wait for the next code to be generated.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                return Response(
                    {
                        "message": "Verification code sent to your email",
                        "provisioning_uri": verification.get_provisioning_uri(),  # For TOTP apps like Google Authenticator
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response(
                    {"error": f"Failed to send email: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailCodeView(APIView):
    """
    API endpoint for verifying a TOTP code and authenticating the user.
    Uses Knox tokens for authentication.
    Rate limited by both email and IP to prevent brute force attacks.
    """

    authentication_classes: list = []  # No authentication required
    permission_classes = [AllowAny]
    throttle_classes = [EmailBasedThrottle, IPBasedThrottle]  # Apply both throttles

    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            code = serializer.validated_data["code"]

            # Try to find the verification record
            try:
                verification = EmailVerificationCode.objects.filter(
                    email=email, is_used=False
                ).latest("created_at")

                # Verify the TOTP code
                if not verification.is_valid(code):
                    # Record the failed attempt
                    max_attempts_reached = verification.record_failed_attempt()

                    if max_attempts_reached:
                        return Response(
                            {
                                "error": "Too many failed attempts. Please request a new code."
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    return Response(
                        {"error": "Invalid or expired verification code"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Mark code as used
                verification.use()

                # Get or create user
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "name": email.split("@")[0],  # Simple default name
                    },
                )

                # Log the user in (for session-based auth)
                login(request, user)

                # Generate Knox token with explicit TTL
                token_ttl = getattr(settings, "KNOX", {}).get("TOKEN_TTL", None)
                token_instance, token = AuthToken.objects.create(user, token_ttl)

                # Return user data and token
                return Response(
                    {
                        "user": UserSerializer(user).data,
                        "token": token,
                        "expiry": token_instance.expiry,
                    },
                    status=status.HTTP_200_OK,
                )

            except EmailVerificationCode.DoesNotExist:
                return Response(
                    {
                        "error": "No verification request found. Please request a new code."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BiometricVerifyView(APIView):
    """
    API endpoint for biometric authentication.
    Accepts an email address and issues an authentication token without requiring a verification code.
    Rate limited to prevent abuse.
    """

    authentication_classes: list = []  # No authentication required
    permission_classes = [AllowAny]
    throttle_classes = [EmailBasedThrottle, IPBasedThrottle]  # Apply both throttles

    def post(self, request):
        serializer = BiometricVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        # Find the user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Use a generic error message for security
            return Response(
                {"error": "User not found or biometric authentication not allowed"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check if the user has completed email verification before
        # We can check if the user has at least one used verification code
        has_verified_email = EmailVerificationCode.objects.filter(
            email=email, is_used=True
        ).exists()

        if not has_verified_email:
            return Response(
                {"error": "Email verification required before using biometric login"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Create an authentication token for the user
        token_instance, token = AuthToken.objects.create(user)

        # Log the successful biometric authentication
        # You might want to create a separate function for this
        # For now, just print to console
        print(f"Biometric authentication successful for user {user.id}")

        # Return user data and token
        return Response(
            {
                "token": token,
                "expiry": token_instance.expiry,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class UserProfileView(KnoxAuthenticatedAPIView):
    """
    API endpoint for retrieving and updating the user's profile.
    """

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
