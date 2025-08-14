"""
Tests for standardized error handling system.

This module tests the error response format consistency and error code standardization
across all API endpoints, with focus on the teacher invitation system.
"""

from datetime import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from ..error_handling import (
    APIErrorCode,
    create_authentication_error_response,
    create_error_response,
    create_invitation_already_accepted_response,
    create_invitation_already_declined_response,
    create_invitation_expired_response,
    create_invitation_invalid_recipient_response,
    create_invitation_not_found_response,
    create_not_found_error_response,
    create_permission_error_response,
    create_school_membership_exists_response,
    create_validation_error_response,
)


class TestStandardizedErrorResponses(TestCase):
    """Test cases for standardized error response formats."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_path = "/api/accounts/teacher-invitations/abc123/accept/"

    def test_create_basic_error_response(self):
        """Test creating a basic error response with minimal data."""
        response = create_error_response(
            error_code=APIErrorCode.INVITATION_NOT_FOUND, message="Test error message", request_path=self.test_path
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "INVITATION_NOT_FOUND")
        self.assertEqual(response.data["error"]["message"], "Test error message")
        self.assertEqual(response.data["path"], self.test_path)
        self.assertIn("timestamp", response.data)

    def test_create_error_response_with_details(self):
        """Test creating an error response with additional details."""
        details = {"expected_email": "test@example.com", "provided_email": "wrong@example.com"}

        response = create_error_response(
            error_code=APIErrorCode.INVITATION_INVALID_RECIPIENT,
            message="Invalid recipient",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN,
            request_path=self.test_path,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["details"], details)

    def test_create_validation_error_response(self):
        """Test creating a validation error response from serializer errors."""
        serializer_errors = {
            "email": ["Enter a valid email address."],
            "hourly_rate": ["Ensure this value is less than or equal to 200."],
            "non_field_errors": ["Custom message is required."],
        }

        response = create_validation_error_response(serializer_errors=serializer_errors, request_path=self.test_path)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_FAILED")
        self.assertIn("field_errors", response.data["error"]["details"])
        self.assertIn("non_field_errors", response.data["error"]["details"])

        # Check field errors are properly mapped
        field_errors = response.data["error"]["details"]["field_errors"]
        self.assertEqual(field_errors["email"], ["Enter a valid email address."])
        self.assertEqual(field_errors["hourly_rate"], ["Ensure this value is less than or equal to 200."])

        # Check non-field errors are properly mapped
        non_field_errors = response.data["error"]["details"]["non_field_errors"]
        self.assertEqual(non_field_errors, ["Custom message is required."])

    def test_create_authentication_error_response(self):
        """Test creating an authentication error response."""
        response = create_authentication_error_response(
            message="Please log in to accept this invitation", request_path=self.test_path
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"]["code"], "AUTHENTICATION_REQUIRED")
        self.assertEqual(response.data["error"]["message"], "Please log in to accept this invitation")

    def test_create_permission_error_response(self):
        """Test creating a permission denied error response."""
        response = create_permission_error_response(
            message="You cannot accept invitations for other users", request_path=self.test_path
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual(response.data["error"]["message"], "You cannot accept invitations for other users")

    def test_create_not_found_error_response(self):
        """Test creating a not found error response."""
        response = create_not_found_error_response(resource_name="Teacher Invitation", request_path=self.test_path)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"]["code"], "NOT_FOUND")
        self.assertEqual(response.data["error"]["message"], "Teacher Invitation not found")


class TestInvitationSpecificErrorResponses(TestCase):
    """Test cases for invitation-specific error response helpers."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_path = "/api/accounts/teacher-invitations/abc123/accept/"

    def test_invitation_not_found_response(self):
        """Test invitation not found error response."""
        response = create_invitation_not_found_response(request_path=self.test_path)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"]["code"], "INVITATION_NOT_FOUND")
        self.assertEqual(response.data["error"]["message"], "The invitation token is invalid or does not exist")

    def test_invitation_expired_response(self):
        """Test invitation expired error response."""
        expired_time = timezone.now()

        response = create_invitation_expired_response(request_path=self.test_path, expires_at=expired_time)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "INVITATION_EXPIRED")
        self.assertEqual(response.data["error"]["message"], "This invitation has expired and is no longer valid")
        self.assertEqual(response.data["error"]["details"]["expired_at"], expired_time.isoformat())

    def test_invitation_already_accepted_response(self):
        """Test invitation already accepted error response."""
        accepted_time = timezone.now()

        response = create_invitation_already_accepted_response(request_path=self.test_path, accepted_at=accepted_time)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "INVITATION_ALREADY_ACCEPTED")
        self.assertEqual(response.data["error"]["message"], "This invitation has already been accepted")
        self.assertEqual(response.data["error"]["details"]["accepted_at"], accepted_time.isoformat())

    def test_invitation_already_declined_response(self):
        """Test invitation already declined error response."""
        declined_time = timezone.now()

        response = create_invitation_already_declined_response(request_path=self.test_path, declined_at=declined_time)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "INVITATION_ALREADY_DECLINED")
        self.assertEqual(response.data["error"]["message"], "This invitation has already been declined")
        self.assertEqual(response.data["error"]["details"]["declined_at"], declined_time.isoformat())

    def test_invitation_invalid_recipient_response(self):
        """Test invitation invalid recipient error response."""
        expected_email = "teacher@example.com"

        response = create_invitation_invalid_recipient_response(
            expected_email=expected_email, request_path=self.test_path
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "INVITATION_INVALID_RECIPIENT")
        self.assertEqual(response.data["error"]["message"], "This invitation is not intended for your account")
        self.assertEqual(response.data["error"]["details"]["expected_email"], expected_email)

    def test_school_membership_exists_response(self):
        """Test school membership already exists error response."""
        school_name = "Test School"

        response = create_school_membership_exists_response(school_name=school_name, request_path=self.test_path)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "SCHOOL_MEMBERSHIP_EXISTS")
        self.assertEqual(response.data["error"]["message"], f"You are already a member of {school_name}")
        self.assertEqual(response.data["error"]["details"]["school_name"], school_name)


class TestAPIErrorCodes(TestCase):
    """Test cases for API error code enum."""

    def test_error_code_values(self):
        """Test that error codes have expected string values."""
        self.assertEqual(APIErrorCode.INVITATION_NOT_FOUND.value, "INVITATION_NOT_FOUND")
        self.assertEqual(APIErrorCode.VALIDATION_FAILED.value, "VALIDATION_FAILED")
        self.assertEqual(APIErrorCode.AUTHENTICATION_REQUIRED.value, "AUTHENTICATION_REQUIRED")

    def test_error_code_as_string(self):
        """Test that error codes can be used as strings."""
        error_code = APIErrorCode.INVITATION_EXPIRED
        self.assertEqual(str(error_code), "INVITATION_EXPIRED")

    def test_error_code_in_response(self):
        """Test that error codes work correctly in response creation."""
        response = create_error_response(error_code=APIErrorCode.INVITATION_NOT_FOUND, message="Test message")

        self.assertEqual(response.data["error"]["code"], "INVITATION_NOT_FOUND")


class TestErrorResponseConsistency(TestCase):
    """Test cases for ensuring error response format consistency."""

    def test_all_responses_have_required_fields(self):
        """Test that all error responses have required fields."""
        test_cases = [
            create_error_response(APIErrorCode.VALIDATION_FAILED, "Test"),
            create_authentication_error_response(),
            create_permission_error_response(),
            create_not_found_error_response("Resource"),
            create_invitation_not_found_response(),
            create_invitation_expired_response(),
        ]

        for response in test_cases:
            # Check top-level structure
            self.assertIn("error", response.data)
            self.assertIn("timestamp", response.data)
            self.assertIn("path", response.data)

            # Check error object structure
            error = response.data["error"]
            self.assertIn("code", error)
            self.assertIn("message", error)

            # Validate error code format (UPPERCASE_WITH_UNDERSCORES)
            self.assertRegex(error["code"], r"^[A-Z_]+$")

            # Validate timestamp format (ISO 8601)
            self.assertRegex(response.data["timestamp"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_validation_errors_structure(self):
        """Test that validation errors have consistent structure."""
        serializer_errors = {
            "email": ["Invalid email format"],
            "phone": ["Required field"],
            "non_field_errors": ["Data conflict"],
        }

        response = create_validation_error_response(serializer_errors)

        # Check validation-specific structure
        details = response.data["error"]["details"]
        self.assertIn("field_errors", details)
        self.assertIn("non_field_errors", details)

        # Ensure field errors are properly formatted
        field_errors = details["field_errors"]
        self.assertEqual(field_errors["email"], ["Invalid email format"])
        self.assertEqual(field_errors["phone"], ["Required field"])

        # Ensure non-field errors are properly formatted
        non_field_errors = details["non_field_errors"]
        self.assertEqual(non_field_errors, ["Data conflict"])

    @patch("django.utils.timezone.now")
    def test_timestamp_consistency(self, mock_now):
        """Test that timestamps are consistently formatted."""
        from zoneinfo import ZoneInfo

        test_time = datetime(2025, 8, 1, 10, 30, 0, tzinfo=ZoneInfo("UTC"))
        mock_now.return_value = test_time

        response = create_error_response(APIErrorCode.VALIDATION_FAILED, "Test")

        self.assertEqual(response.data["timestamp"], "2025-08-01T10:30:00+00:00")

    def test_error_response_serialization(self):
        """Test that error responses can be properly serialized to JSON."""
        response = create_error_response(
            error_code=APIErrorCode.INVITATION_NOT_FOUND, message="Test message", details={"test_key": "test_value"}
        )

        # Response data should be JSON-serializable
        import json

        json_str = json.dumps(response.data)
        reconstructed = json.loads(json_str)

        self.assertEqual(reconstructed["error"]["code"], "INVITATION_NOT_FOUND")
        self.assertEqual(reconstructed["error"]["message"], "Test message")
        self.assertEqual(reconstructed["error"]["details"]["test_key"], "test_value")
