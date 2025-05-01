import re
from typing import ClassVar

from common.serializers import BaseNestedModelSerializer, BaseSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    School,
    SchoolInvitation,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherProfile,
)

User = get_user_model()

MAX_PHONE_LENGTH = 20
MAX_SCHOOL_NAME_LENGTH = 150


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """

    is_student = serializers.SerializerMethodField()
    is_teacher = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields: ClassVar[list[str]] = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_student",
            "is_teacher",
        ]
        read_only_fields: ClassVar[list[str]] = ["id", "is_student", "is_teacher"]

    def get_is_student(self, obj):
        """Check if user has any active school membership as a student."""
        return obj.school_memberships.filter(role=SchoolRole.STUDENT, is_active=True).exists()

    def get_is_teacher(self, obj):
        """Check if user has any active school membership as a teacher."""
        return obj.school_memberships.filter(role=SchoolRole.TEACHER, is_active=True).exists()


class SchoolSerializer(BaseSerializer):
    """
    Serializer for the School model.
    """

    class Meta:
        model = School
        fields: ClassVar[list[str]] = [
            "id",
            "name",
            "description",
            "address",
            "contact_email",
            "phone_number",
            "website",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = ["id", "created_at", "updated_at"]


class SchoolMembershipSerializer(BaseNestedModelSerializer):
    """
    Serializer for the SchoolMembership model.
    """

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=User.objects.all(), source="user"
    )

    school = SchoolSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=School.objects.all(), source="school"
    )

    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = SchoolMembership
        fields: ClassVar[list[str]] = [
            "id",
            "user",
            "user_id",
            "school",
            "school_id",
            "role",
            "role_display",
            "is_active",
            "joined_at",
        ]
        read_only_fields: ClassVar[list[str]] = ["id", "joined_at"]


class SchoolInvitationSerializer(BaseNestedModelSerializer):
    """
    Serializer for the SchoolInvitation model.
    """

    school = SchoolSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=School.objects.all(), source="school"
    )

    invited_by = UserSerializer(read_only=True)

    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = SchoolInvitation
        fields: ClassVar[list[str]] = [
            "id",
            "school",
            "school_id",
            "email",
            "invited_by",
            "role",
            "role_display",
            "token",
            "created_at",
            "expires_at",
            "is_accepted",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "invited_by",
            "token",
            "created_at",
            "expires_at",
            "is_accepted",
        ]


class SchoolWithMembersSerializer(SchoolSerializer):
    """
    Extended School serializer that includes member information.
    """

    members = serializers.SerializerMethodField()

    class Meta(SchoolSerializer.Meta):
        fields: ClassVar[list[str]] = [*list(SchoolSerializer.Meta.fields), "members"]

    def get_members(self, obj):
        memberships = obj.memberships.filter(is_active=True)
        return SchoolMembershipSerializer(memberships, many=True).data


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for the StudentProfile model.
    """

    user = UserSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields: ClassVar[list[str]] = ["id", "user", "school_year", "birth_date", "address"]
        read_only_fields: ClassVar[list[str]] = ["id"]


class TeacherSerializer(serializers.ModelSerializer):
    """
    Serializer for the TeacherProfile model.
    """

    user = UserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields: ClassVar[list[str]] = ["id", "user", "bio", "specialty", "education"]
        read_only_fields: ClassVar[list[str]] = ["id"]


class UserWithRolesSerializer(UserSerializer):
    """
    Extended User serializer that includes role information.
    """

    roles = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields: ClassVar[list[str]] = [*list(UserSerializer.Meta.fields), "roles"]

    def get_roles(self, obj):
        memberships = obj.school_memberships.filter(is_active=True)
        roles_data = []

        for membership in memberships:
            roles_data.append(
                {
                    "school": {
                        "id": membership.school.id,
                        "name": membership.school.name,
                    },
                    "role": membership.role,
                    "role_display": membership.get_role_display(),
                }
            )

        return roles_data


class EmailRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting an email verification code.
    """

    email = serializers.EmailField()


class EmailVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying an email code.
    """

    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)


class BiometricVerifySerializer(serializers.Serializer):
    """
    Serializer for biometric verification.
    """

    email = serializers.EmailField()


class InvitationRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a school invitation.
    """

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=SchoolRole.choices)
    school_id = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True)


class InvitationAcceptSerializer(serializers.Serializer):
    """
    Serializer for accepting a school invitation.
    """

    token = serializers.CharField()


class CreateUserSerializer(serializers.Serializer):
    """
    Serializer for creating a new user during signup.

    Requires both email and name, with phone number optional.
    Allows selection of primary contact method.
    """

    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20, required=True)
    primary_contact = serializers.ChoiceField(
        choices=[("email", "Email"), ("phone", "Phone")], default="email"
    )

    # School information is optional
    school = serializers.DictField(
        child=serializers.CharField(), required=False, help_text="School information"
    )

    def validate_phone_number(self, value):
        """Validate phone number format"""
        if not re.match(r"^\+?[0-9\s\-\(\)]{5,20}$", value):
            raise serializers.ValidationError("Invalid phone number format")

        if len(value) > MAX_PHONE_LENGTH:
            raise serializers.ValidationError("Phone number must be less than 20 characters")

        return value

    def validate(self, data):
        """
        Ensure that primary_contact is valid based on provided contact methods
        """
        primary_contact = data.get("primary_contact")

        if primary_contact == "phone" and not data.get("phone_number"):
            raise serializers.ValidationError(
                {
                    "primary_contact": "Phone number is required when phone is selected as primary contact"
                }
            )

        return data

    def validate_school(self, value):
        """Validate school data if provided"""
        if not value:
            return value

        # Extract only fields that are allowed
        allowed_fields = [
            "name",
            "description",
            "address",
            "contact_email",
            "phone_number",
            "website",
        ]
        school_data = {k: v for k, v in value.items() if k in allowed_fields}

        # Validate name field (required)
        if "name" not in school_data or not school_data["name"]:
            raise serializers.ValidationError({"name": "School name is required"})
        elif len(school_data["name"]) > MAX_SCHOOL_NAME_LENGTH:
            raise serializers.ValidationError(
                {"name": "School name must be less than 150 characters"}
            )

        # Validate contact email format (optional)
        if school_data.get("contact_email"):
            from django.core.exceptions import ValidationError
            from django.core.validators import validate_email

            try:
                validate_email(school_data["contact_email"])
            except ValidationError as err:
                raise serializers.ValidationError(
                    {"contact_email": "Invalid email format"}
                ) from err

        # Validate phone number format (optional)
        if school_data.get("phone_number"):
            if not re.match(r"^\+?[0-9\s\-\(\)]{5,20}$", school_data["phone_number"]):
                raise serializers.ValidationError({"phone_number": "Invalid phone number format"})

            if len(school_data["phone_number"]) > MAX_PHONE_LENGTH:
                raise serializers.ValidationError(
                    {"phone_number": "Phone number must be less than 20 characters"}
                )

        # Validate website URL format (optional)
        if school_data.get("website"):
            from django.core.exceptions import ValidationError
            from django.core.validators import URLValidator

            validate_url = URLValidator()
            try:
                validate_url(school_data["website"])
            except ValidationError as err:
                raise serializers.ValidationError({"website": "Invalid URL format"}) from err

        return school_data


class PhoneNumberField(serializers.CharField):
    def __init__(self, **kwargs):
        super().__init__(max_length=MAX_PHONE_LENGTH, **kwargs)

    def to_internal_value(self, value):
        value = super().to_internal_value(value)

        # Validate phone number format
        if not re.match(r"^\+?[\d\s-]+$", value):
            raise serializers.ValidationError("Invalid phone number format")

        if len(value) > MAX_PHONE_LENGTH:
            raise serializers.ValidationError("Phone number must be less than 20 characters")

        return value
