import re
from typing import ClassVar

from common.serializers import BaseNestedModelSerializer, BaseSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Course,
    EducationalSystem,
    School,
    SchoolInvitation,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherCourse,
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
            "name",
            "phone_number",
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


class EducationalSystemSerializer(serializers.ModelSerializer):
    """
    Serializer for the EducationalSystem model.
    """

    class Meta:
        model = EducationalSystem
        fields: ClassVar[list[str]] = [
            "id",
            "name",
            "code",
            "description",
            "school_years",
            "education_levels",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = ["id", "created_at", "updated_at"]


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for the StudentProfile model.
    """

    user = UserSerializer(read_only=True)
    educational_system = EducationalSystemSerializer(read_only=True)
    educational_system_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=EducationalSystem.objects.filter(is_active=True),
        source="educational_system",
    )

    class Meta:
        model = StudentProfile
        fields: ClassVar[list[str]] = [
            "id",
            "user",
            "educational_system",
            "educational_system_id",
            "school_year",
            "birth_date",
            "address",
        ]
        read_only_fields: ClassVar[list[str]] = ["id"]


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for the Course model.
    """

    class Meta:
        model = Course
        fields: ClassVar[list[str]] = [
            "id",
            "name",
            "code",
            "educational_system",
            "education_level",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = ["id", "created_at", "updated_at"]


class TeacherCourseSerializer(serializers.ModelSerializer):
    """
    Serializer for the TeacherCourse many-to-many relationship.
    """

    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Course.objects.all(), source="course"
    )

    class Meta:
        model = TeacherCourse
        fields: ClassVar[list[str]] = [
            "id",
            "course",
            "course_id",
            "hourly_rate",
            "is_active",
            "started_teaching",
        ]
        read_only_fields: ClassVar[list[str]] = ["id", "started_teaching"]


class TeacherSerializer(serializers.ModelSerializer):
    """
    Serializer for the TeacherProfile model.
    """

    user = UserSerializer(read_only=True)
    courses = serializers.SerializerMethodField()

    class Meta:
        model = TeacherProfile
        fields: ClassVar[list[str]] = ["id", "user", "bio", "specialty", "education", "courses"]
        read_only_fields: ClassVar[list[str]] = ["id"]

    def get_courses(self, obj):
        """Get active courses taught by this teacher."""
        teacher_courses = obj.teacher_courses.filter(is_active=True)
        return TeacherCourseSerializer(teacher_courses, many=True).data


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


class RequestCodeSerializer(serializers.Serializer):
    """
    Serializer for requesting a verification code.
    """

    email = serializers.EmailField()


class VerifyCodeSerializer(serializers.Serializer):
    """
    Serializer for verifying a verification code.
    """

    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)


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

    # School information is required
    school = serializers.DictField(
        child=serializers.CharField(), required=True, help_text="School information"
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


class TeacherOnboardingSerializer(serializers.Serializer):
    """
    Serializer for creating a teacher profile with associated courses in one request.
    """

    # Teacher profile fields (all optional)
    bio = serializers.CharField(required=False, allow_blank=True)
    specialty = serializers.CharField(max_length=100, required=False, allow_blank=True)

    # Course associations
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of course IDs the teacher wants to teach",
    )

    def validate_course_ids(self, value):
        """Validate that all course IDs exist."""
        if not value:
            return value

        existing_ids = set(Course.objects.filter(id__in=value).values_list("id", flat=True))
        invalid_ids = set(value) - existing_ids

        if invalid_ids:
            raise serializers.ValidationError(f"Invalid course IDs: {list(invalid_ids)}")

        return value


class AddExistingTeacherSerializer(serializers.Serializer):
    """
    ⚠️ DEPRECATED: This serializer is deprecated as of [DATE].

    Use InviteExistingTeacherSerializer instead to ensure proper user consent.
    This serializer was for adding teachers without their explicit acceptance.

    MIGRATION: Replace with InviteExistingTeacherSerializer
    """

    email = serializers.EmailField()
    school_id = serializers.IntegerField()

    # Teacher profile fields (all optional)
    bio = serializers.CharField(required=False, allow_blank=True)
    specialty = serializers.CharField(max_length=100, required=False, allow_blank=True)

    # Course associations
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of course IDs the teacher wants to teach",
    )

    def validate_email(self, value):
        """Validate that the user exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"User with email '{value}' does not exist")
        return value

    def validate_school_id(self, value):
        """Validate that the school exists."""
        if not School.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"School with ID {value} does not exist")
        return value

    def validate_course_ids(self, value):
        """Validate that all course IDs exist."""
        if not value:
            return value

        existing_ids = set(Course.objects.filter(id__in=value).values_list("id", flat=True))
        invalid_ids = set(value) - existing_ids

        if invalid_ids:
            raise serializers.ValidationError(f"Invalid course IDs: {list(invalid_ids)}")

        return value


class InviteNewTeacherSerializer(serializers.Serializer):
    """
    Serializer for creating a new user and inviting them as a teacher to a school.
    """

    email = serializers.EmailField()
    name = serializers.CharField(max_length=150)
    school_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # Teacher profile fields (all optional)
    bio = serializers.CharField(required=False, allow_blank=True)
    specialty = serializers.CharField(max_length=100, required=False, allow_blank=True)

    # Course associations
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of course IDs the teacher wants to teach",
    )

    def validate_email(self, value):
        """Validate that the user doesn't already exist."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"User with email '{value}' already exists")
        return value

    def validate_school_id(self, value):
        """Validate that the school exists."""
        if not School.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"School with ID {value} does not exist")
        return value

    def validate_phone_number(self, value):
        """Validate phone number format if provided."""
        if not value:
            return value

        if not re.match(r"^\+?[0-9\s\-\(\)]{5,20}$", value):
            raise serializers.ValidationError("Invalid phone number format")

        if len(value) > 20:
            raise serializers.ValidationError("Phone number must be less than 20 characters")

        return value

    def validate_course_ids(self, value):
        """Validate that all course IDs exist."""
        if not value:
            return value

        existing_ids = set(Course.objects.filter(id__in=value).values_list("id", flat=True))
        invalid_ids = set(value) - existing_ids

        if invalid_ids:
            raise serializers.ValidationError(f"Invalid course IDs: {list(invalid_ids)}")

        return value


class TeacherOnboardingResponseSerializer(serializers.Serializer):
    """
    Serializer for teacher onboarding response data.
    """

    message = serializers.CharField()
    courses_added = serializers.IntegerField()
    teacher = TeacherSerializer()
    school_membership = SchoolMembershipSerializer(required=False)
    user_created = serializers.BooleanField(required=False)
    invitation_sent = serializers.BooleanField(required=False)
    invitation = SchoolInvitationSerializer(required=False)


class InviteExistingTeacherSerializer(serializers.Serializer):
    """
    Serializer for inviting an existing user to become a teacher at a school.
    Creates an invitation that the user can accept later.
    """

    email = serializers.EmailField()
    school_id = serializers.IntegerField()
    send_email = serializers.BooleanField(default=False)
    send_sms = serializers.BooleanField(default=False)

    def validate_email(self, value):
        """Validate that the user exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"User with email '{value}' does not exist")
        return value

    def validate_school_id(self, value):
        """Validate that the school exists."""
        if not School.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"School with ID {value} does not exist")
        return value

    def validate(self, data):
        """Cross-field validation."""
        user = User.objects.get(email=data["email"])
        school_id = data["school_id"]

        # Check if user is already a teacher at this school
        if SchoolMembership.objects.filter(
            user=user, school_id=school_id, role=SchoolRole.TEACHER, is_active=True
        ).exists():
            raise serializers.ValidationError("User is already a teacher at this school")

        # Check if there's already a pending invitation
        if SchoolInvitation.objects.filter(
            email=data["email"],
            school_id=school_id,
            role=SchoolRole.TEACHER,
            is_accepted=False,
            expires_at__gt=timezone.now(),
        ).exists():
            raise serializers.ValidationError(
                "There is already a pending invitation for this user to this school"
            )

        return data


class AcceptInvitationSerializer(serializers.Serializer):
    """
    Serializer for accepting a school invitation.
    """

    # Teacher profile fields (optional - user can customize when accepting)
    bio = serializers.CharField(required=False, allow_blank=True)
    specialty = serializers.CharField(max_length=100, required=False, allow_blank=True)

    # Course associations
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of course IDs the teacher wants to teach",
    )

    def validate_course_ids(self, value):
        """Validate that all course IDs exist."""
        if not value:
            return value

        existing_ids = set(Course.objects.filter(id__in=value).values_list("id", flat=True))
        invalid_ids = set(value) - existing_ids

        if invalid_ids:
            raise serializers.ValidationError(f"Invalid course IDs: {list(invalid_ids)}")

        return value


class CreateStudentSerializer(serializers.Serializer):
    """
    Serializer for creating a complete student record (user + profile + school membership) in one request.
    """

    # User fields
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    primary_contact = serializers.ChoiceField(
        choices=[("email", "Email"), ("phone", "Phone")], default="email"
    )

    # Student profile fields
    educational_system_id = serializers.PrimaryKeyRelatedField(
        queryset=EducationalSystem.objects.filter(is_active=True), help_text="Educational system ID"
    )
    school_year = serializers.CharField(
        max_length=50, help_text="School year within the educational system"
    )
    birth_date = serializers.DateField(help_text="Student's birth date (YYYY-MM-DD)")
    address = serializers.CharField(
        required=False, allow_blank=True, help_text="Student's address (optional)"
    )

    # School membership
    school_id = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.all(), help_text="School ID to add the student to"
    )

    def validate_email(self, value):
        """Validate that email doesn't already exist"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        return value

    def validate_phone_number(self, value):
        """Validate phone number format if provided"""
        if value and not re.match(r"^\+?[0-9\s\-\(\)]{5,20}$", value):
            raise serializers.ValidationError("Invalid phone number format")
        return value

    def validate_school_year(self, value):
        """Validate that school year exists in the educational system"""
        educational_system_id = self.initial_data.get("educational_system_id")
        if educational_system_id:
            try:
                educational_system = EducationalSystem.objects.get(id=educational_system_id)
                # Extract valid keys from the school_years tuples/lists
                valid_keys = [year[0] for year in educational_system.school_years]
                if value not in valid_keys:
                    # Format error message with key: display pairs
                    valid_options = [
                        f"'{year[0]}': '{year[1]}'" for year in educational_system.school_years
                    ]
                    raise serializers.ValidationError(
                        f"School year '{value}' is not valid for educational system '{educational_system.name}'. "
                        f"Valid options: {{{', '.join(valid_options)}}}"
                    )
            except EducationalSystem.DoesNotExist:
                pass  # Will be caught by educational_system_id validation
        return value

    def validate(self, data):
        """Cross-field validation"""
        primary_contact = data.get("primary_contact")
        phone_number = data.get("phone_number")

        if primary_contact == "phone" and not phone_number:
            raise serializers.ValidationError(
                {
                    "primary_contact": "Phone number is required when phone is selected as primary contact"
                }
            )

        return data


class CreateStudentResponseSerializer(serializers.Serializer):
    """
    Serializer for create student response data.
    """

    message = serializers.CharField()
    user = UserSerializer()
    student = StudentSerializer()
    school_membership = SchoolMembershipSerializer()
    user_created = serializers.BooleanField(default=True)
