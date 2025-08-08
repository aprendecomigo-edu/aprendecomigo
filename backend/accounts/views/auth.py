"""
Authentication related views for the accounts app.

This module contains views for user authentication, including code request,
code verification, and base classes for authenticated views.
"""

import logging

from common.messaging import send_email_verification_code
from common.throttles import EmailBasedThrottle, EmailCodeRequestThrottle, IPBasedThrottle
from django.contrib.auth import login
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..db_queries import get_user_by_email, user_exists
from ..models import VerificationCode
from ..serializers import (
    AuthenticationResponseSerializer,
    RequestCodeSerializer,
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