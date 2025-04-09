from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.mail import send_mail
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from common.permissions import IsOwner, IsStudent, IsTeacher

from .models import EmailVerificationCode, Student, Teacher
from .serializers import (
    EmailRequestSerializer,
    EmailVerifySerializer,
    StudentSerializer,
    TeacherSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        if self.action in [
            "create",
            "list",
            "retrieve",
            "update",
            "partial_update",
            "school_profile",
        ]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsOwner]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def dashboard_info(self, request):
        """
        Get dashboard information for the current user
        """
        user = request.user

        # Basic user info
        user_info = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "date_joined": user.date_joined,
            "is_admin": user.is_admin or user.is_staff or user.is_superuser,
            "user_type": user.user_type,
        }

        # Stats based on user type
        stats = {}

        if user.is_admin or user.is_staff or user.is_superuser:
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
    def school_profile(self):
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


class TeacherViewSet(viewsets.ModelViewSet):
    """
    API endpoint for teacher profiles.
    """

    serializer_class = TeacherSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
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


class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for student profiles.
    """

    serializer_class = StudentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
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


class RequestEmailCodeView(APIView):
    """
    API endpoint for requesting an email verification code.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # Generate a verification code
            verification = EmailVerificationCode.generate_code(email)

            # Send email with verification code
            try:
                send_mail(
                    subject="Your Aprende Comigo Verification Code",
                    message=f"Your verification code {verification.code} \
                    will expire in 10 minutes.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                return Response(
                    {"message": "Verification code sent to your email"},
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
    API endpoint for verifying an email code and authenticating the user.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            code = serializer.validated_data["code"]

            # Try to find the verification code
            try:
                verification = EmailVerificationCode.objects.get(
                    email=email, code=code, is_used=False
                )

                if not verification.is_valid():
                    return Response(
                        {"error": "Verification code has expired"},
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

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)

                # Return user data and tokens
                return Response(
                    {
                        "user": UserSerializer(user).data,
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    status=status.HTTP_200_OK,
                )

            except EmailVerificationCode.DoesNotExist:
                return Response(
                    {"error": "Invalid verification code"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    API endpoint for retrieving and updating the user's profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
