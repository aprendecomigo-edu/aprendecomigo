"""
Standardized error handling for Aprende Comigo API.

This module provides consistent error response formats and error codes
across all API endpoints, especially for the teacher invitation system.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response


class APIErrorCode(str, Enum):
    """
    Standardized error codes for API responses.

    Format: {DOMAIN}_{SPECIFIC_ERROR}
    Example: INVITATION_NOT_FOUND, VALIDATION_FAILED
    """

    def __str__(self):
        return self.value

    # Generic errors
    VALIDATION_FAILED = "VALIDATION_FAILED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    RATE_LIMITED = "RATE_LIMITED"

    # Invitation-specific errors
    INVITATION_NOT_FOUND = "INVITATION_NOT_FOUND"
    INVITATION_EXPIRED = "INVITATION_EXPIRED"
    INVITATION_ALREADY_ACCEPTED = "INVITATION_ALREADY_ACCEPTED"
    INVITATION_ALREADY_DECLINED = "INVITATION_ALREADY_DECLINED"
    INVITATION_INVALID_RECIPIENT = "INVITATION_INVALID_RECIPIENT"
    INVITATION_INVALID_TOKEN = "INVITATION_INVALID_TOKEN"
    INVITATION_SCHOOL_NOT_FOUND = "INVITATION_SCHOOL_NOT_FOUND"
    INVITATION_DUPLICATE_MEMBERSHIP = "INVITATION_DUPLICATE_MEMBERSHIP"
    INVITATION_EMAIL_SEND_FAILED = "INVITATION_EMAIL_SEND_FAILED"

    # Profile creation errors
    PROFILE_CREATION_FAILED = "PROFILE_CREATION_FAILED"
    PROFILE_VALIDATION_FAILED = "PROFILE_VALIDATION_FAILED"
    PROFILE_FILE_UPLOAD_FAILED = "PROFILE_FILE_UPLOAD_FAILED"
    PROFILE_ALREADY_EXISTS = "PROFILE_ALREADY_EXISTS"

    # School management errors
    SCHOOL_NOT_FOUND = "SCHOOL_NOT_FOUND"
    SCHOOL_ACCESS_DENIED = "SCHOOL_ACCESS_DENIED"
    SCHOOL_MEMBERSHIP_EXISTS = "SCHOOL_MEMBERSHIP_EXISTS"

    # Bulk operation errors
    BULK_OPERATION_FAILED = "BULK_OPERATION_FAILED"
    BULK_OPERATION_PARTIAL_SUCCESS = "BULK_OPERATION_PARTIAL_SUCCESS"


class StandardErrorResponseSerializer(serializers.Serializer):
    """
    Serializer for standardized API error responses.

    Provides consistent error format across all endpoints:
    {
        "error": {
            "code": "INVITATION_NOT_FOUND",
            "message": "The invitation token is invalid or has expired",
            "details": {...}  // Optional additional context
        },
        "timestamp": "2025-08-01T10:30:00Z",
        "path": "/api/accounts/teacher-invitations/abc123/accept/"
    }
    """

    class ErrorDetailSerializer(serializers.Serializer):
        code = serializers.CharField(help_text="Error code for programmatic handling")
        message = serializers.CharField(help_text="Human-readable error message")
        details = serializers.JSONField(required=False, help_text="Additional context or validation errors")

    error = ErrorDetailSerializer()
    timestamp = serializers.DateTimeField(help_text="ISO 8601 timestamp of the error")
    path = serializers.CharField(help_text="API endpoint path where error occurred")


class ValidationErrorResponseSerializer(serializers.Serializer):
    """
    Serializer for validation error responses with field-specific errors.

    Extends StandardErrorResponseSerializer with field validation details:
    {
        "error": {
            "code": "VALIDATION_FAILED",
            "message": "Validation failed for the provided data",
            "details": {
                "field_errors": {
                    "email": ["Enter a valid email address."],
                    "hourly_rate": ["Ensure this value is less than or equal to 200."]
                },
                "non_field_errors": ["Custom message and phone number cannot be empty."]
            }
        },
        "timestamp": "2025-08-01T10:30:00Z",
        "path": "/api/accounts/teacher-invitations/abc123/accept/"
    }
    """

    class ValidationErrorDetailSerializer(serializers.Serializer):
        code = serializers.CharField(default=APIErrorCode.VALIDATION_FAILED.value)
        message = serializers.CharField(default="Validation failed for the provided data")
        details = serializers.JSONField(help_text="Field-specific validation errors")

    error = ValidationErrorDetailSerializer()
    timestamp = serializers.DateTimeField()
    path = serializers.CharField()


def create_error_response(
    error_code: APIErrorCode | str,
    message: str,
    details: dict[str, Any] | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    request_path: str | None = None,
) -> Response:
    """
    Create a standardized error response.

    Args:
        error_code: APIErrorCode enum or string error code
        message: Human-readable error message
        details: Optional additional context
        status_code: HTTP status code (default: 400)
        request_path: API endpoint path

    Returns:
        DRF Response object with standardized error format

    Example:
        return create_error_response(
            error_code=APIErrorCode.INVITATION_NOT_FOUND,
            message="The invitation token is invalid or has expired",
            status_code=status.HTTP_404_NOT_FOUND,
            request_path="/api/accounts/teacher-invitations/abc123/accept/"
        )
    """

    error_data = {
        "error": {
            "code": error_code.value if isinstance(error_code, APIErrorCode) else error_code,
            "message": message,
        },
        "timestamp": timezone.now().isoformat(),
        "path": request_path or "",
    }

    if details:
        error_data["error"]["details"] = details

    return Response(error_data, status=status_code)


def create_validation_error_response(
    serializer_errors: dict[str, Any],
    message: str = "Validation failed for the provided data",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    request_path: str | None = None,
) -> Response:
    """
    Create a standardized validation error response from serializer errors.

    Args:
        serializer_errors: Django REST Framework serializer errors dict
        message: Custom error message (optional)
        status_code: HTTP status code (default: 400)
        request_path: API endpoint path

    Returns:
        DRF Response object with standardized validation error format

    Example:
        if not serializer.is_valid():
            return create_validation_error_response(
                serializer.errors,
                request_path=request.path
            )
    """

    # Separate field errors from non-field errors
    field_errors = {}
    non_field_errors = []

    for field_name, field_errors_list in serializer_errors.items():
        if field_name == "non_field_errors":
            non_field_errors.extend(field_errors_list)
        else:
            field_errors[field_name] = field_errors_list

    details = {}
    if field_errors:
        details["field_errors"] = field_errors
    if non_field_errors:
        details["non_field_errors"] = non_field_errors

    return create_error_response(
        error_code=APIErrorCode.VALIDATION_FAILED,
        message=message,
        details=details,
        status_code=status_code,
        request_path=request_path,
    )


def create_authentication_error_response(
    message: str = "Authentication credentials were not provided",
    request_path: str | None = None,
    details: dict[str, Any] | None = None,
) -> Response:
    """
    Create a standardized authentication error response.

    Args:
        message: Custom authentication error message
        request_path: API endpoint path
        details: Optional additional context (e.g., invitation details)

    Returns:
        DRF Response object with standardized authentication error format
    """

    return create_error_response(
        error_code=APIErrorCode.AUTHENTICATION_REQUIRED,
        message=message,
        details=details,
        status_code=status.HTTP_401_UNAUTHORIZED,
        request_path=request_path,
    )


def create_permission_error_response(
    message: str = "You do not have permission to perform this action",
    request_path: str | None = None,
    details: dict[str, Any] | None = None,
) -> Response:
    """
    Create a standardized permission denied error response.

    Args:
        message: Custom permission error message
        request_path: API endpoint path
        details: Optional additional context

    Returns:
        DRF Response object with standardized permission error format
    """

    return create_error_response(
        error_code=APIErrorCode.PERMISSION_DENIED,
        message=message,
        details=details,
        status_code=status.HTTP_403_FORBIDDEN,
        request_path=request_path,
    )


def create_not_found_error_response(
    resource_name: str = "Resource", request_path: str | None = None, details: dict[str, Any] | None = None
) -> Response:
    """
    Create a standardized not found error response.

    Args:
        resource_name: Name of the resource that wasn't found
        request_path: API endpoint path
        details: Optional additional context

    Returns:
        DRF Response object with standardized not found error format
    """

    return create_error_response(
        error_code=APIErrorCode.NOT_FOUND,
        message=f"{resource_name} not found",
        details=details,
        status_code=status.HTTP_404_NOT_FOUND,
        request_path=request_path,
    )


# Invitation-specific error response helpers


def create_invitation_not_found_response(request_path: str | None = None) -> Response:
    """Create standardized response for invalid invitation tokens."""
    return create_error_response(
        error_code=APIErrorCode.INVITATION_NOT_FOUND,
        message="The invitation token is invalid or does not exist",
        status_code=status.HTTP_404_NOT_FOUND,
        request_path=request_path,
    )


def create_invitation_expired_response(request_path: str | None = None, expires_at: datetime | None = None) -> Response:
    """Create standardized response for expired invitations."""
    details = {}
    if expires_at:
        details["expired_at"] = expires_at.isoformat()

    return create_error_response(
        error_code=APIErrorCode.INVITATION_EXPIRED,
        message="This invitation has expired and is no longer valid",
        details=details,
        status_code=status.HTTP_400_BAD_REQUEST,
        request_path=request_path,
    )


def create_invitation_already_accepted_response(
    request_path: str | None = None, accepted_at: datetime | None = None
) -> Response:
    """Create standardized response for already accepted invitations."""
    details = {}
    if accepted_at:
        details["accepted_at"] = accepted_at.isoformat()

    return create_error_response(
        error_code=APIErrorCode.INVITATION_ALREADY_ACCEPTED,
        message="This invitation has already been accepted",
        details=details,
        status_code=status.HTTP_400_BAD_REQUEST,
        request_path=request_path,
    )


def create_invitation_already_declined_response(
    request_path: str | None = None, declined_at: datetime | None = None
) -> Response:
    """Create standardized response for already declined invitations."""
    details = {}
    if declined_at:
        details["declined_at"] = declined_at.isoformat()

    return create_error_response(
        error_code=APIErrorCode.INVITATION_ALREADY_DECLINED,
        message="This invitation has already been declined",
        details=details,
        status_code=status.HTTP_400_BAD_REQUEST,
        request_path=request_path,
    )


def create_invitation_invalid_recipient_response(expected_email: str, request_path: str | None = None) -> Response:
    """Create standardized response for invitation recipient mismatch."""
    return create_error_response(
        error_code=APIErrorCode.INVITATION_INVALID_RECIPIENT,
        message="This invitation is not intended for your account",
        details={"expected_email": expected_email},
        status_code=status.HTTP_403_FORBIDDEN,
        request_path=request_path,
    )


def create_school_membership_exists_response(school_name: str, request_path: str | None = None) -> Response:
    """Create standardized response for duplicate school memberships."""
    return create_error_response(
        error_code=APIErrorCode.SCHOOL_MEMBERSHIP_EXISTS,
        message=f"You are already a member of {school_name}",
        details={"school_name": school_name},
        status_code=status.HTTP_400_BAD_REQUEST,
        request_path=request_path,
    )
