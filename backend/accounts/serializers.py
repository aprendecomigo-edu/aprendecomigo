import re
import logging
from typing import ClassVar

from common.serializers import BaseNestedModelSerializer, BaseSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from messaging.models import (
    EmailDeliveryStatus,
    EmailSequence,
    EmailSequenceStep, 
    EmailCommunication,
    EmailTemplateType,
    EmailCommunicationType,
)
from .models import (
    Course,
    EducationalSystem,
    InvitationStatus,
    School,
    SchoolActivity,
    SchoolInvitation,
    SchoolMembership,
    SchoolRole,
    SchoolSettings,
    StudentProfile,
    StudentProgress,
    ProgressAssessment,
    TeacherCourse,
    TeacherInvitation,
    TeacherProfile,
)

User = get_user_model()
logger = logging.getLogger(__name__)

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
    Now uses Django enumeration types for better type safety.
    """

    school_years = serializers.SerializerMethodField()
    education_levels = serializers.SerializerMethodField()

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

    def get_school_years(self, obj):
        """Get school year choices as key-value pairs"""
        return obj.school_year_choices

    def get_education_levels(self, obj):
        """Get education level choices as key-value pairs"""
        return obj.education_level_choices


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
    Enhanced serializer for the TeacherProfile model.
    
    Includes all profile fields, computed properties, and completion data
    as required for GitHub issue #71.
    """

    user = UserSerializer(read_only=True)
    courses = serializers.SerializerMethodField()
    
    # Computed fields for profile completion and analytics
    profile_completion = serializers.SerializerMethodField()
    school_memberships = serializers.SerializerMethodField()
    last_activity = serializers.DateTimeField(read_only=True)
    
    # Rate and availability information
    hourly_rate = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    availability = serializers.CharField(required=False, allow_blank=True)
    
    # Contact and location information
    address = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    calendar_iframe = serializers.CharField(required=False, allow_blank=True)
    
    # New structured data fields
    education_background = serializers.JSONField(required=False)
    teaching_subjects = serializers.JSONField(required=False)
    rate_structure = serializers.JSONField(required=False)
    weekly_availability = serializers.JSONField(required=False)
    
    # Enhanced profile fields
    grade_level_preferences = serializers.JSONField(required=False)
    teaching_experience = serializers.JSONField(required=False)
    credentials_documents = serializers.JSONField(required=False)
    availability_schedule = serializers.JSONField(required=False)
    
    # Profile tracking fields
    profile_completion_score = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    is_profile_complete = serializers.BooleanField(read_only=True)
    last_profile_update = serializers.DateTimeField(read_only=True)

    class Meta:
        model = TeacherProfile
        fields: ClassVar[list[str]] = [
            "id", 
            "user", 
            "bio", 
            "specialty", 
            "education",
            "hourly_rate",
            "availability", 
            "address",
            "phone_number",
            "calendar_iframe",
            "education_background",
            "teaching_subjects",
            "rate_structure", 
            "weekly_availability",
            "grade_level_preferences",
            "teaching_experience",
            "credentials_documents",
            "availability_schedule",
            "profile_completion_score",
            "is_profile_complete",
            "last_profile_update",
            "last_activity",
            "courses",
            "profile_completion",
            "school_memberships"
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id", 
            "profile_completion_score", 
            "is_profile_complete", 
            "last_profile_update",
            "last_activity"
        ]

    def get_courses(self, obj):
        """Get active courses taught by this teacher."""
        teacher_courses = obj.teacher_courses.filter(is_active=True)
        return TeacherCourseSerializer(teacher_courses, many=True).data
    
    def get_profile_completion(self, obj):
        """Get detailed profile completion data."""
        try:
            completion_data = obj.get_completion_data()
            return {
                'completion_percentage': completion_data['completion_percentage'],
                'missing_critical': completion_data['missing_critical'],
                'missing_optional': completion_data['missing_optional'],
                'recommendations': completion_data['recommendations'],
                'is_complete': completion_data['is_complete'],
                'scores_breakdown': completion_data['scores_breakdown']
            }
        except Exception as e:
            logger.error(f"Error getting profile completion for teacher {obj.id}: {e}")
            return {
                'completion_percentage': 0.0,
                'missing_critical': [],
                'missing_optional': [],
                'recommendations': [],
                'is_complete': False,
                'scores_breakdown': {'basic_info': 0.0, 'teaching_details': 0.0, 'professional_info': 0.0}
            }
    
    def get_school_memberships(self, obj):
        """Get all school memberships for this teacher."""
        try:
            memberships = obj.get_school_memberships()
            return [
                {
                    'school_id': membership.school.id,
                    'school_name': membership.school.name,
                    'role': membership.role,
                    'is_active': membership.is_active,
                    'joined_at': membership.joined_at
                }
                for membership in memberships
            ]
        except Exception as e:
            logger.error(f"Error getting school memberships for teacher {obj.id}: {e}")
            return []
    
    def update(self, instance, validated_data):
        """Update teacher profile and recalculate completion score."""
        # Update the instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Recalculate completion score after update
        try:
            instance.update_completion_score()
        except Exception as e:
            logger.error(f"Failed to update completion score for teacher {instance.id} after update: {e}")
        
        return instance
    
    def validate_education_background(self, value):
        """Validate education background structure."""
        if not value:
            return value
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Education background must be a dictionary")
        
        # Optional validation for expected fields
        expected_fields = ['degree', 'institution', 'field', 'year']
        for field in expected_fields:
            if field in value and value[field] is not None:
                if field == 'year':
                    try:
                        year = int(value[field])
                        if year < 1900 or year > 2030:
                            raise serializers.ValidationError(f"Invalid year: {year}")
                    except (ValueError, TypeError):
                        raise serializers.ValidationError("Year must be a valid integer")
        
        return value
    
    def validate_teaching_subjects(self, value):
        """Validate teaching subjects list."""
        if not value:
            return []
        
        if not isinstance(value, list):
            raise serializers.ValidationError("Teaching subjects must be a list")
        
        # Validate each subject is a string
        for subject in value:
            if not isinstance(subject, str) or len(subject.strip()) == 0:
                raise serializers.ValidationError("Each subject must be a non-empty string")
        
        # Remove duplicates and empty strings
        cleaned_subjects = list(set(s.strip() for s in value if s.strip()))
        
        if len(cleaned_subjects) > 20:
            raise serializers.ValidationError("Maximum 20 subjects allowed")
        
        return cleaned_subjects
    
    def validate_rate_structure(self, value):
        """Validate rate structure dictionary."""
        if not value:
            return value
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Rate structure must be a dictionary")
        
        # Validate rate values are positive numbers
        for rate_type, rate_value in value.items():
            if rate_value is not None:
                try:
                    rate = float(rate_value)
                    if rate < 0:
                        raise serializers.ValidationError(f"Rate for {rate_type} must be positive")
                except (ValueError, TypeError):
                    raise serializers.ValidationError(f"Invalid rate value for {rate_type}")
        
        return value
    
    def validate_weekly_availability(self, value):
        """Validate weekly availability structure."""
        if not value:
            return value
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Weekly availability must be a dictionary")
        
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day, times in value.items():
            if day.lower() not in valid_days:
                raise serializers.ValidationError(f"Invalid day: {day}")
            
            if times and not isinstance(times, list):
                raise serializers.ValidationError(f"Times for {day} must be a list")
            
            # Validate time format (optional - could be more strict)
            if times:
                for time_slot in times:
                    if not isinstance(time_slot, str) or len(time_slot.strip()) == 0:
                        raise serializers.ValidationError(f"Invalid time slot for {day}: {time_slot}")
        
        return value


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


class AuthenticationResponseSerializer(UserWithRolesSerializer):
    """
    Enhanced User serializer for authentication responses.
    Includes user_type and primary_role for immediate frontend routing decisions.
    This prevents the need for additional API calls during authentication flow.
    """

    user_type = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    primary_role = serializers.SerializerMethodField()

    class Meta(UserWithRolesSerializer.Meta):
        fields: ClassVar[list[str]] = [*list(UserWithRolesSerializer.Meta.fields), "user_type", "is_admin", "primary_role"]

    def get_user_type(self, obj):
        """
        Determine user_type from SchoolMembership records.
        Uses the same logic as dashboard_info endpoint.
        """
        from .db_queries import list_school_ids_owned_or_managed
        
        # Check if user is a school owner or admin in any school
        admin_school_ids = list_school_ids_owned_or_managed(obj)
        if len(admin_school_ids) > 0:
            return "admin"
        
        # Check if user is a teacher in any school
        elif SchoolMembership.objects.filter(
            user=obj, role=SchoolRole.TEACHER, is_active=True
        ).exists():
            return "teacher"
        
        # Check if user is a student in any school
        elif SchoolMembership.objects.filter(
            user=obj, role=SchoolRole.STUDENT, is_active=True
        ).exists():
            return "student"
        
        # Default fallback
        return "student"

    def get_is_admin(self, obj):
        """
        Check if user has admin privileges (school owner or admin).
        """
        from .db_queries import list_school_ids_owned_or_managed
        
        admin_school_ids = list_school_ids_owned_or_managed(obj)
        return len(admin_school_ids) > 0
    
    def get_primary_role(self, obj):
        """
        Get the user's primary role for immediate frontend routing.
        Returns the highest priority role the user has.
        """
        from .db_queries import list_school_ids_owned_or_managed
        
        # Check if user is a school owner or admin in any school
        admin_school_ids = list_school_ids_owned_or_managed(obj)
        if len(admin_school_ids) > 0:
            return SchoolRole.SCHOOL_OWNER
        
        # Check if user is a teacher in any school
        teacher_membership = SchoolMembership.objects.filter(
            user=obj, role=SchoolRole.TEACHER, is_active=True
        ).first()
        if teacher_membership:
            return SchoolRole.TEACHER
        
        # Check if user is a student in any school
        student_membership = SchoolMembership.objects.filter(
            user=obj, role=SchoolRole.STUDENT, is_active=True
        ).first()
        if student_membership:
            return SchoolRole.STUDENT
        
        # Default fallback
        return SchoolRole.STUDENT


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
    Allows selection of primary contact method and explicit user type.
    """

    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20, required=True)
    primary_contact = serializers.ChoiceField(
        choices=[("email", "Email"), ("phone", "Phone")], default="email"
    )
    user_type = serializers.ChoiceField(
        choices=[("tutor", "Individual Tutor"), ("school", "School/Institution")],
        required=True,
        help_text="Explicit user type selection from frontend"
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


class ComprehensiveTeacherProfileCreationSerializer(serializers.Serializer):
    """
    Comprehensive serializer for teacher profile creation during invitation acceptance.
    
    Supports all profile fields, file uploads, and validation for GitHub issue #50.
    """
    
    # Basic Information (existing fields)
    bio = serializers.CharField(required=False, allow_blank=True, max_length=5000)
    specialty = serializers.CharField(max_length=100, required=False, allow_blank=True)
    hourly_rate = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)
    
    # Contact and Location
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    # File Uploads
    profile_photo = serializers.ImageField(required=False, allow_null=True)
    
    # Teaching Subjects with structured data
    teaching_subjects = serializers.JSONField(required=False, allow_null=True)
    
    # Grade Level Preferences
    grade_level_preferences = serializers.JSONField(required=False, allow_null=True)
    
    # Availability and Schedule
    availability = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    weekly_availability = serializers.JSONField(required=False, allow_null=True)
    availability_schedule = serializers.JSONField(required=False, allow_null=True)
    
    # Rates and Compensation
    rate_structure = serializers.JSONField(required=False, allow_null=True)
    
    # Credentials and Education
    education_background = serializers.JSONField(required=False, allow_null=True)
    teaching_experience = serializers.JSONField(required=False, allow_null=True)
    credentials_documents = serializers.JSONField(required=False, allow_null=True)
    
    # Course associations (backward compatibility)
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of course IDs the teacher wants to teach",
    )
    
    def validate_profile_photo(self, value):
        """Validate profile photo upload."""
        if not value:
            return value
        
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError("Profile photo must be less than 5MB.")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Profile photo must be a JPEG, PNG, GIF, or WebP image."
            )
        
        return value
    
    def validate_teaching_subjects(self, value):
        """Validate teaching subjects structure."""
        if not value:
            return value
        
        if not isinstance(value, list):
            raise serializers.ValidationError("Teaching subjects must be a list.")
        
        valid_levels = ['beginner', 'intermediate', 'advanced', 'expert']
        
        for subject_data in value:
            if not isinstance(subject_data, dict):
                raise serializers.ValidationError("Each teaching subject must be an object.")
            
            if 'subject' not in subject_data:
                raise serializers.ValidationError("Each teaching subject must have a 'subject' field.")
            
            if 'level' in subject_data and subject_data['level'] not in valid_levels:
                raise serializers.ValidationError(
                    f"Subject level must be one of: {', '.join(valid_levels)}"
                )
        
        return value
    
    def validate_grade_level_preferences(self, value):
        """Validate grade level preferences."""
        if not value:
            return value
        
        if not isinstance(value, list):
            raise serializers.ValidationError("Grade level preferences must be a list.")
        
        valid_levels = [
            'elementary', 'middle', 'high_school', 'university', 'university_prep',
            'professional', 'adult_education'
        ]
        
        for level in value:
            if level not in valid_levels:
                raise serializers.ValidationError(
                    f"Invalid grade level: {level}. Must be one of: {', '.join(valid_levels)}"
                )
        
        return value
    
    def validate_hourly_rate(self, value):
        """Validate hourly rate."""
        if value is None:
            return value
        
        if value < 0:
            raise serializers.ValidationError("Hourly rate cannot be negative.")
        
        if value > 500:  # Reasonable maximum
            raise serializers.ValidationError("Hourly rate seems unusually high. Please verify.")
        
        return value
    
    def validate_education_background(self, value):
        """Validate education background structure."""
        if not value:
            return value
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Education background must be an object.")
        
        # Validate degrees structure if present
        if 'degrees' in value:
            if not isinstance(value['degrees'], list):
                raise serializers.ValidationError("Degrees must be a list.")
            
            for degree in value['degrees']:
                if not isinstance(degree, dict):
                    raise serializers.ValidationError("Each degree must be an object.")
                
                required_fields = ['degree', 'institution']
                for field in required_fields:
                    if field not in degree or not degree[field]:
                        raise serializers.ValidationError(f"Each degree must have a '{field}' field.")
        
        return value
    
    def validate_teaching_experience(self, value):
        """Validate teaching experience structure."""
        if not value:
            return value
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Teaching experience must be an object.")
        
        # Validate total_years if present
        if 'total_years' in value:
            total_years = value['total_years']
            if not isinstance(total_years, (int, float)) or total_years < 0:
                raise serializers.ValidationError("Total years must be a non-negative number.")
            
            if total_years > 80:  # Reasonable maximum
                raise serializers.ValidationError("Total years seems unusually high.")
        
        # Validate positions structure if present
        if 'positions' in value:
            if not isinstance(value['positions'], list):
                raise serializers.ValidationError("Positions must be a list.")
            
            for position in value['positions']:
                if not isinstance(position, dict):
                    raise serializers.ValidationError("Each position must be an object.")
        
        return value
    
    def validate_weekly_availability(self, value):
        """Validate weekly availability structure."""
        if not value:
            return value
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Weekly availability must be an object.")
        
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day, slots in value.items():
            if day not in valid_days:
                raise serializers.ValidationError(f"Invalid day: {day}")
            
            if not isinstance(slots, list):
                raise serializers.ValidationError(f"Availability for {day} must be a list of time slots.")
            
            for slot in slots:
                if not isinstance(slot, dict) or 'start' not in slot or 'end' not in slot:
                    raise serializers.ValidationError(
                        f"Each time slot for {day} must have 'start' and 'end' times."
                    )
        
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
                # Use the enumeration-based validation
                if not educational_system.validate_school_year(value):
                    # Format error message with key: display pairs
                    valid_options = [
                        f"'{year[0]}': '{year[1]}'"
                        for year in educational_system.school_year_choices
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


# School Dashboard Serializers

class SchoolSettingsSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for school settings with all configuration options"""
    
    # Read-only fields for display
    educational_system_name = serializers.CharField(source='educational_system.name', read_only=True)
    grade_levels_display = serializers.ListField(source='get_grade_levels_display', read_only=True)
    working_days_display = serializers.ListField(source='get_working_days_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_code_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    
    class Meta:
        model = SchoolSettings
        fields = [
            # Basic operational settings
            'trial_cost_absorption',
            'default_session_duration',
            'timezone',
            
            # Educational system configuration
            'educational_system',
            'educational_system_name',
            'grade_levels',
            'grade_levels_display',
            
            # Billing configuration
            'billing_contact_name',
            'billing_contact_email',
            'billing_address',
            'tax_id',
            'currency_code',
            'currency_display',
            
            # Localization
            'language',
            'language_display',
            
            # Schedule and availability
            'working_hours_start',
            'working_hours_end',
            'working_days',
            'working_days_display',
            
            # Communication preferences
            'email_notifications_enabled',
            'sms_notifications_enabled',
            
            # User permissions and access control
            'allow_student_self_enrollment',
            'require_parent_approval',
            'auto_assign_teachers',
            'class_reminder_hours',
            
            # Integration settings
            'enable_calendar_integration',
            'calendar_integration_type',
            'enable_email_integration',
            'email_integration_provider',
            
            # Privacy and data handling
            'data_retention_policy',
            'gdpr_compliance_enabled',
            'allow_data_export',
            'require_data_processing_consent',
            
            # Dashboard preferences
            'dashboard_refresh_interval',
            'activity_retention_days',
            
            # Timestamps
            'created_at',
            'updated_at',
        ]
        
    def validate_working_days(self, value):
        """Validate working days are within valid range"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Working days must be a list.")
        
        for day in value:
            if not isinstance(day, int) or day < 0 or day > 6:
                raise serializers.ValidationError(
                    "Working days must be integers between 0 (Monday) and 6 (Sunday)."
                )
        
        return value
    
    def validate_grade_levels(self, value):
        """Validate grade levels are valid for the educational system"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Grade levels must be a list.")
        
        # Get educational system from instance or initial data
        educational_system = None
        if self.instance:
            educational_system = self.instance.educational_system
        elif 'educational_system' in self.initial_data:
            try:
                educational_system = EducationalSystem.objects.get(
                    id=self.initial_data['educational_system']
                )
            except EducationalSystem.DoesNotExist:
                pass
        
        if educational_system:
            valid_levels = dict(educational_system.school_year_choices)
            for level in value:
                if level not in valid_levels:
                    raise serializers.ValidationError(
                        f"Grade level '{level}' is not valid for educational system '{educational_system.name}'. "
                        f"Valid options: {list(valid_levels.keys())}"
                    )
        
        return value
    
    def validate_working_hours_start(self, value):
        """Validate working hours start time"""
        working_hours_end = self.initial_data.get('working_hours_end')
        if working_hours_end:
            # If working_hours_end is a string, parse it to time object
            if isinstance(working_hours_end, str):
                try:
                    from datetime import datetime
                    working_hours_end = datetime.strptime(working_hours_end, '%H:%M').time()
                except ValueError:
                    # If parsing fails, skip validation here - it will be caught by field validation
                    return value
            
            if value >= working_hours_end:
                raise serializers.ValidationError(
                    "Working hours start time must be before end time."
                )
        return value
    
    def validate(self, attrs):
        """Validate the complete settings"""
        attrs = super().validate(attrs)
        
        # Validate working hours consistency
        start_time = attrs.get('working_hours_start')
        end_time = attrs.get('working_hours_end')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'working_hours_end': "End time must be after start time."
            })
        
        # Validate integration settings consistency
        if attrs.get('enable_calendar_integration') and not attrs.get('calendar_integration_type'):
            raise serializers.ValidationError({
                'calendar_integration_type': "Calendar integration type is required when calendar integration is enabled."
            })
        
        if attrs.get('enable_email_integration') and not attrs.get('email_integration_provider'):
            raise serializers.ValidationError({
                'email_integration_provider': "Email integration provider is required when email integration is enabled."
            })
        
        return attrs


class SchoolProfileSerializer(serializers.ModelSerializer):
    """Serializer for school profile information including branding"""
    
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = School
        fields = [
            'id',
            'name',
            'description',
            'address',
            'contact_email',
            'phone_number',
            'website',
            'logo',
            'logo_url',
            'primary_color',
            'secondary_color',
            'email_domain',
            'created_at',
            'updated_at',
        ]
    
    def get_logo_url(self, obj):
        """Get the full URL for the school logo"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def validate_primary_color(self, value):
        """Validate primary color is a valid hex color"""
        if value and not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError(
                "Primary color must be a valid hex color code (e.g., #3B82F6)."
            )
        return value
    
    def validate_secondary_color(self, value):
        """Validate secondary color is a valid hex color"""
        if value and not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError(
                "Secondary color must be a valid hex color code (e.g., #1F2937)."
            )
        return value


class ComprehensiveSchoolSettingsSerializer(BaseNestedModelSerializer):
    """Complete school settings serializer including both profile and settings"""
    
    school_profile = SchoolProfileSerializer(source='school', read_only=True)
    settings = SchoolSettingsSerializer(source='*')
    
    class Meta:
        model = SchoolSettings
        fields = ['school_profile', 'settings']


class SchoolActivityActorSerializer(serializers.ModelSerializer):
    """Serializer for activity actor information"""
    
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role']
        
    def get_role(self, obj):
        """Get the user's role in the school context"""
        # Get school from context
        school = self.context.get('school')
        if school:
            membership = obj.school_memberships.filter(
                school=school, 
                is_active=True
            ).first()
            if membership:
                return membership.role
        return None


class SchoolActivityTargetSerializer(serializers.Serializer):
    """Serializer for activity target information"""
    
    type = serializers.CharField()
    id = serializers.IntegerField()
    name = serializers.CharField()


class SchoolActivitySerializer(serializers.ModelSerializer):
    """Serializer for school activities"""
    
    actor = SchoolActivityActorSerializer(read_only=True)
    target = serializers.SerializerMethodField()
    
    class Meta:
        model = SchoolActivity
        fields = [
            'id',
            'activity_type',
            'timestamp',
            'actor',
            'target',
            'metadata',
            'description'
        ]
        
    def get_target(self, obj):
        """Get target information based on activity type"""
        if obj.target_user:
            return {
                'type': 'user',
                'id': obj.target_user.id,
                'name': obj.target_user.name
            }
        elif obj.target_class:
            return {
                'type': 'class',
                'id': obj.target_class.id,
                'name': f"Grade {obj.target_class.grade_level} class"
            }
        elif obj.target_invitation:
            return {
                'type': 'invitation',
                'id': obj.target_invitation.id,
                'name': obj.target_invitation.email
            }
        return None


class TrendDataSerializer(serializers.Serializer):
    """Serializer for trend data points"""
    
    daily = serializers.ListField(child=serializers.IntegerField())
    weekly = serializers.ListField(child=serializers.IntegerField())
    monthly = serializers.ListField(child=serializers.IntegerField())


class CountMetricsSerializer(serializers.Serializer):
    """Serializer for count-based metrics with trends"""
    
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    inactive = serializers.IntegerField()
    trend = TrendDataSerializer()


class ClassMetricsSerializer(serializers.Serializer):
    """Serializer for class-related metrics"""
    
    active_classes = serializers.IntegerField()
    completed_today = serializers.IntegerField()
    scheduled_today = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    trend = serializers.DictField(
        child=serializers.ListField(child=serializers.IntegerField())
    )


class EngagementMetricsSerializer(serializers.Serializer):
    """Serializer for engagement metrics"""
    
    invitations_sent = serializers.IntegerField()
    invitations_accepted = serializers.IntegerField()
    acceptance_rate = serializers.FloatField()
    avg_time_to_accept = serializers.CharField()


class SchoolMetricsSerializer(serializers.Serializer):
    """Serializer for complete school metrics"""
    
    student_count = CountMetricsSerializer()
    teacher_count = CountMetricsSerializer()
    class_metrics = ClassMetricsSerializer()
    engagement_metrics = EngagementMetricsSerializer()


class EnhancedSchoolSerializer(serializers.ModelSerializer):
    """Enhanced school serializer with settings support"""
    
    settings = SchoolSettingsSerializer(read_only=True)
    
    class Meta:
        model = School
        fields = [
            'id',
            'name',
            'description',
            'address',
            'contact_email',
            'phone_number',
            'website',
            'created_at',
            'updated_at',
            'settings'
        ]
        
    def update(self, instance, validated_data):
        """Update school and settings together"""
        settings_data = None
        
        # Extract settings from request if present
        request = self.context.get('request')
        if request and hasattr(request, 'data') and 'settings' in request.data:
            settings_data = request.data['settings']
        
        # Update school fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update or create settings
        if settings_data:
            settings, created = SchoolSettings.objects.get_or_create(
                school=instance,
                defaults=settings_data
            )
            if not created:
                for key, value in settings_data.items():
                    setattr(settings, key, value)
                settings.save()
        
        return instance


class TeacherInvitationSerializer(BaseNestedModelSerializer):
    """
    Serializer for the TeacherInvitation model.
    """
    
    school = SchoolSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=School.objects.all(), source="school"
    )
    invited_by = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    email_delivery_status_display = serializers.CharField(
        source='get_email_delivery_status_display', read_only=True
    )
    
    class Meta:
        model = TeacherInvitation
        fields = [
            "id",
            "school",
            "school_id", 
            "email",
            "invited_by",
            "role",
            "custom_message",
            "batch_id",
            "status",
            "status_display",
            "email_delivery_status",
            "email_delivery_status_display",
            "email_sent_at",
            "email_delivered_at",
            "email_failure_reason",
            "retry_count",
            "max_retries",
            "token",
            "created_at",
            "updated_at",
            "expires_at",
            "is_accepted",
            "accepted_at",
            "declined_at",
            "viewed_at",
        ]
        read_only_fields = [
            "id",
            "invited_by",
            "status",
            "email_delivery_status",
            "email_sent_at",
            "email_delivered_at",
            "email_failure_reason",
            "retry_count",
            "token",
            "created_at",
            "updated_at",
            "is_accepted",
            "accepted_at",
            "declined_at",
            "viewed_at",
        ]


class SingleInvitationSerializer(serializers.Serializer):
    """
    Serializer for a single invitation in a bulk request.
    """
    
    email = serializers.CharField(allow_blank=True)  # Use CharField to allow invalid emails, validate in view
    
    def validate_email(self, value):
        """Allow all email formats to pass through for view-level partial success handling."""
        # All email validation moved to view level to enable 207 Multi-Status responses
        # for partial failures as per API requirements
        return value


class BulkTeacherInvitationSerializer(serializers.Serializer):
    """
    Serializer for bulk teacher invitation requests.
    Handles validation and processing of multiple invitations at once.
    """
    
    school_id = serializers.IntegerField()
    custom_message = serializers.CharField(
        max_length=1000, 
        required=False, 
        allow_blank=True,
        help_text="Personal message to include in all invitations"
    )
    send_email = serializers.BooleanField(
        default=False,
        help_text="Whether to immediately send invitation emails"
    )
    invitations = serializers.ListField(
        child=SingleInvitationSerializer(),
        min_length=1,
        max_length=100,
        help_text="List of email addresses to invite (max 100)"
    )
    
    def validate_custom_message(self, value):
        """Validate and sanitize custom message for security."""
        if not value:
            return value
        
        # Strip dangerous HTML tags and script content
        import re
        from django.utils.html import strip_tags
        
        # Remove script tags and their content
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove dangerous HTML attributes (on* event handlers)
        value = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', value, flags=re.IGNORECASE)
        
        # Strip remaining HTML tags to plain text
        value = strip_tags(value)
        
        # Limit line breaks to prevent formatting abuse
        value = re.sub(r'\n{3,}', '\n\n', value)
        
        # Ensure reasonable length after sanitization
        if len(value.strip()) > 1000:
            raise serializers.ValidationError("Custom message is too long after processing")
        
        return value.strip()
    
    def validate(self, data):
        """Custom validation for the entire serializer."""
        data = super().validate(data)
        return data
    
    def validate_school_id(self, value):
        """Validate that the school exists and user has permission."""
        try:
            school = School.objects.get(id=value)
        except School.DoesNotExist:
            raise serializers.ValidationError("School does not exist")
        
        # Check user permission
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        from .db_queries import can_user_manage_school
        if not can_user_manage_school(request.user, school.id):
            raise serializers.ValidationError(
                "You don't have permission to invite teachers to this school"
            )
        
        return value
    
    def validate_invitations(self, value):
        """Validate invitation list for limits and duplicates within request."""
        if len(value) == 0:
            raise serializers.ValidationError("At least one invitation is required")
        
        if len(value) > 100:
            raise serializers.ValidationError("Maximum 100 invitations allowed per batch")
        
        # Note: Duplicate validation within request temporarily disabled to allow
        # view-level partial success handling as per API requirements.
        # This allows the view to return 207 Multi-Status for partial failures.
        
        return value
    
    def validate(self, data):
        """Additional validation across fields."""
        school_id = data.get('school_id')
        emails = [inv['email'] for inv in data.get('invitations', [])]
        
        # Note: We don't validate existing invitations here anymore to allow partial success
        # This validation is moved to the view level for better error handling
        
        return data


class BulkInvitationResponseSerializer(serializers.Serializer):
    """
    Serializer for bulk invitation response data.
    """
    
    batch_id = serializers.UUIDField(read_only=True)
    total_invitations = serializers.IntegerField(read_only=True)
    successful_invitations = serializers.IntegerField(read_only=True)
    failed_invitations = serializers.IntegerField(read_only=True)
    errors = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    invitations = TeacherInvitationSerializer(many=True, read_only=True)
    message = serializers.CharField(read_only=True)


# =======================
# TEACHER PROFILE WIZARD SECURITY SERIALIZERS
# =======================

class ProfileWizardDataSerializer(serializers.Serializer):
    """
    Comprehensive input validation serializer for Teacher Profile Wizard.
    Implements strict validation and sanitization for all user inputs.
    """
    
    # Personal Information Fields
    first_name = serializers.CharField(
        max_length=50,
        required=True,
        help_text="Teacher's first name"
    )
    last_name = serializers.CharField(
        max_length=50,
        required=True,
        help_text="Teacher's last name"
    )
    email = serializers.EmailField(
        required=True,
        help_text="Teacher's email address"
    )
    phone_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Teacher's phone number"
    )
    
    # Professional Information Fields
    professional_bio = serializers.CharField(
        max_length=2500,  # ~500 words
        required=False,
        allow_blank=True,
        help_text="Teacher's professional biography"
    )
    professional_title = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Teacher's professional title or specialty"
    )
    years_experience = serializers.IntegerField(
        min_value=0,
        max_value=50,
        required=False,
        allow_null=True,
        help_text="Years of teaching experience"
    )
    
    # Education Background (structured data)
    education_background = serializers.JSONField(
        required=False,
        help_text="Structured educational background data"
    )
    
    # Teaching Subjects
    teaching_subjects = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text="List of subjects the teacher can teach"
    )
    
    # Rate Structure
    rate_structure = serializers.JSONField(
        required=False,
        help_text="Teaching rate structure"
    )
    
    def validate_first_name(self, value):
        """Validate and sanitize first name."""
        if not value or not value.strip():
            raise serializers.ValidationError("First name cannot be empty.")
        
        # Remove HTML tags and sanitize
        import bleach
        clean_value = bleach.clean(value, tags=[], strip=True).strip()
        
        if len(clean_value) < 1:
            raise serializers.ValidationError("First name must contain at least one character.")
        
        # Check for suspicious patterns
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:', 'onload=', 'onerror=']
        clean_lower = clean_value.lower()
        
        for pattern in suspicious_patterns:
            if pattern in clean_lower:
                raise serializers.ValidationError("First name contains invalid characters.")
        
        return clean_value
    
    def validate_last_name(self, value):
        """Validate and sanitize last name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Last name cannot be empty.")
        
        # Remove HTML tags and sanitize
        import bleach
        clean_value = bleach.clean(value, tags=[], strip=True).strip()
        
        if len(clean_value) < 1:
            raise serializers.ValidationError("Last name must contain at least one character.")
        
        # Check for suspicious patterns
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:', 'onload=', 'onerror=']
        clean_lower = clean_value.lower()
        
        for pattern in suspicious_patterns:
            if pattern in clean_lower:
                raise serializers.ValidationError("Last name contains invalid characters.")
        
        return clean_value
    
    def validate_email(self, value):
        """Validate email format and security."""
        if not value:
            raise serializers.ValidationError("Email address is required.")
        
        # Basic email format validation (Django's EmailField handles most of this)
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Please enter a valid email address.")
        
        # Check for suspicious patterns in email
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
        clean_lower = value.lower()
        
        for pattern in suspicious_patterns:
            if pattern in clean_lower:
                raise serializers.ValidationError("Email address contains invalid characters.")
        
        return value.lower().strip()
    
    def validate_phone_number(self, value):
        """Validate phone number format and security."""
        if not value:
            return value
        
        # Remove HTML tags and sanitize
        import bleach
        clean_value = bleach.clean(value, tags=[], strip=True).strip()
        
        # Check for suspicious patterns
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:', 'onload=', 'onerror=']
        clean_lower = clean_value.lower()
        
        for pattern in suspicious_patterns:
            if pattern in clean_lower:
                raise serializers.ValidationError("Phone number contains invalid characters.")
        
        # Basic phone number validation
        import re
        # Allow common phone number formats
        phone_pattern = r'^[\+]?[\d\s\(\)\-\.]{7,20}$'
        
        if not re.match(phone_pattern, clean_value):
            raise serializers.ValidationError(
                "Please enter a valid phone number (7-20 digits, may include +, spaces, (), -, .)"
            )
        
        return clean_value
    
    def validate_professional_bio(self, value):
        """Validate and sanitize professional bio."""
        if not value:
            return value
        
        # Word count validation (approximately 500 words max)
        word_count = len(value.split())
        if word_count > 500:
            raise serializers.ValidationError(
                f"Professional bio is too long ({word_count} words). Maximum 500 words allowed."
            )
        
        # HTML sanitization - allow safe HTML tags
        import bleach
        
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'a']
        allowed_attributes = {
            'a': ['href', 'title'],
        }
        
        clean_value = bleach.clean(
            value,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        ).strip()
        
        # Additional security checks
        suspicious_patterns = ['javascript:', 'data:', 'vbscript:', 'onload=', 'onerror=', 'onclick=']
        clean_lower = clean_value.lower()
        
        for pattern in suspicious_patterns:
            if pattern in clean_lower:
                raise serializers.ValidationError("Professional bio contains invalid content.")
        
        return clean_value
    
    def validate_professional_title(self, value):
        """Validate and sanitize professional title."""
        if not value:
            return value
        
        # Remove HTML tags and sanitize
        import bleach
        clean_value = bleach.clean(value, tags=[], strip=True).strip()
        
        if len(clean_value) > 100:
            raise serializers.ValidationError("Professional title is too long (maximum 100 characters).")
        
        # Check for suspicious patterns
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:', 'onload=', 'onerror=']
        clean_lower = clean_value.lower()
        
        for pattern in suspicious_patterns:
            if pattern in clean_lower:
                raise serializers.ValidationError("Professional title contains invalid characters.")
        
        return clean_value
    
    def validate_education_background(self, value):
        """Validate education background JSON structure."""
        if not value:
            return value
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Education background must be a valid object.")
        
        # Limit the size of the JSON data
        import json
        json_str = json.dumps(value)
        if len(json_str) > 5000:  # 5KB limit
            raise serializers.ValidationError("Education background data is too large.")
        
        # Validate expected fields if present
        expected_fields = ['degree', 'institution', 'field_of_study', 'graduation_year']
        
        for field, field_value in value.items():
            if field not in expected_fields:
                continue
            
            if not isinstance(field_value, str):
                raise serializers.ValidationError(f"Education background field '{field}' must be a string.")
            
            # Sanitize string values
            import bleach
            clean_value = bleach.clean(field_value, tags=[], strip=True)
            
            # Check for suspicious patterns
            suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
            if any(pattern in clean_value.lower() for pattern in suspicious_patterns):
                raise serializers.ValidationError(f"Education background field '{field}' contains invalid content.")
            
            value[field] = clean_value
        
        return value
    
    def validate_teaching_subjects(self, value):
        """Validate teaching subjects list."""
        if not value:
            return value
        
        if not isinstance(value, list):
            raise serializers.ValidationError("Teaching subjects must be a list.")
        
        if len(value) > 20:  # Reasonable limit
            raise serializers.ValidationError("Too many teaching subjects (maximum 20 allowed).")
        
        clean_subjects = []
        for subject in value:
            if not isinstance(subject, str):
                raise serializers.ValidationError("Each teaching subject must be a string.")
            
            # Sanitize subject name
            import bleach
            clean_subject = bleach.clean(subject, tags=[], strip=True).strip()
            
            if len(clean_subject) > 100:
                raise serializers.ValidationError("Teaching subject name is too long (maximum 100 characters).")
            
            # Check for suspicious patterns
            suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
            if any(pattern in clean_subject.lower() for pattern in suspicious_patterns):
                raise serializers.ValidationError("Teaching subject contains invalid characters.")
            
            if clean_subject:  # Only add non-empty subjects
                clean_subjects.append(clean_subject)
        
        return clean_subjects
    
    def validate_rate_structure(self, value):
        """Validate rate structure JSON."""
        if not value:
            return value
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Rate structure must be a valid object.")
        
        # Validate specific rate fields
        rate_fields = ['individual_rate', 'group_rate', 'premium_rate']
        
        for field, rate_value in value.items():
            if field not in rate_fields:
                continue
            
            # Validate rate is a positive number
            try:
                rate_float = float(rate_value)
                if rate_float < 0:
                    raise serializers.ValidationError(f"Rate '{field}' cannot be negative.")
                if rate_float > 1000:  # Reasonable upper limit
                    raise serializers.ValidationError(f"Rate '{field}' is too high (maximum €1000/hour).")
                
                # Round to 2 decimal places
                value[field] = round(rate_float, 2)
                
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Rate '{field}' must be a valid number.")
        
        return value


class ProfileWizardStepValidationSerializer(serializers.Serializer):
    """
    Serializer for validating individual wizard steps.
    """
    
    step = serializers.IntegerField(
        min_value=0,
        max_value=10,  # Reasonable limit for wizard steps
        required=True
    )
    data = serializers.JSONField(required=True)
    
    def validate_data(self, value):
        """Validate step data using the main ProfileWizardDataSerializer."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Step data must be a valid object.")
        
        # Use the main serializer for validation
        serializer = ProfileWizardDataSerializer(data=value)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        
        return serializer.validated_data


class ProfilePhotoUploadSerializer(serializers.Serializer):
    """
    Secure serializer for profile photo uploads.
    """
    
    profile_photo = serializers.ImageField(required=True)
    
    def validate_profile_photo(self, value):
        """Validate uploaded profile photo for security."""
        if not value:
            raise serializers.ValidationError("Profile photo is required.")
        
        # File size validation (5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError("Profile photo file size cannot exceed 5MB.")
        
        # File type validation
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Invalid file type. Only JPEG, PNG, GIF, and WebP images are allowed."
            )
        
        # File extension validation
        import os
        file_extension = os.path.splitext(value.name)[1].lower()
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                "Invalid file extension. Only .jpg, .jpeg, .png, .gif, and .webp files are allowed."
            )
        
        # Image validation using PIL
        try:
            from PIL import Image
            import io
            
            # Reset file pointer
            value.seek(0)
            
            # Try to open and verify the image
            with Image.open(io.BytesIO(value.read())) as img:
                # Verify it's a valid image
                img.verify()
                
                # Check image dimensions (reasonable limits)
                if img.width > 4000 or img.height > 4000:
                    raise serializers.ValidationError("Image dimensions too large (maximum 4000x4000 pixels).")
                
                if img.width < 50 or img.height < 50:
                    raise serializers.ValidationError("Image dimensions too small (minimum 50x50 pixels).")
            
            # Reset file pointer for further processing
            value.seek(0)
            
        except Exception as e:
            raise serializers.ValidationError("Invalid or corrupted image file.")
        
        # Scan for embedded scripts or suspicious content
        value.seek(0)
        file_content = value.read()
        
        # Look for suspicious patterns in binary data
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'data:text/html',
            b'<?php',
            b'<%',
            b'<iframe',
        ]
        
        file_content_lower = file_content.lower()
        for pattern in suspicious_patterns:
            if pattern in file_content_lower:
                raise serializers.ValidationError("Image file contains suspicious content.")
        
        # Reset file pointer
        value.seek(0)
        
        return value


# =======================
# WIZARD ORCHESTRATION SERIALIZERS
# =======================

class WizardStepSerializer(serializers.Serializer):
    """Serializer for wizard step metadata."""
    
    step_number = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    fields = serializers.ListField(child=serializers.CharField())
    is_required = serializers.BooleanField()
    estimated_time_minutes = serializers.IntegerField(required=False)


class WizardCompletionStatusSerializer(serializers.Serializer):
    """Serializer for wizard completion status."""
    
    completion_percentage = serializers.FloatField()
    missing_critical = serializers.ListField(child=serializers.CharField())
    missing_optional = serializers.ListField(child=serializers.CharField())
    is_complete = serializers.BooleanField()
    scores_breakdown = serializers.DictField()
    recommendations = serializers.ListField(child=serializers.DictField())


class SchoolPolicySerializer(serializers.Serializer):
    """Serializer for school policies relevant to wizard."""
    
    currency_code = serializers.CharField()
    rate_constraints = serializers.DictField()
    working_hours = serializers.DictField()
    timezone = serializers.CharField()
    trial_cost_absorption = serializers.CharField()


class WizardMetadataSerializer(serializers.Serializer):
    """Serializer for wizard orchestration metadata."""
    
    steps = WizardStepSerializer(many=True)
    current_step = serializers.IntegerField()
    completion_status = WizardCompletionStatusSerializer()
    school_policies = SchoolPolicySerializer()


class EnhancedInvitationAcceptanceResponseSerializer(serializers.Serializer):
    """Serializer for enhanced invitation acceptance response with wizard metadata."""
    
    success = serializers.BooleanField()
    invitation_accepted = serializers.BooleanField()
    teacher_profile = TeacherSerializer()
    wizard_metadata = WizardMetadataSerializer()
    # Backward compatibility fields
    teacher_profile_created = serializers.BooleanField()
    profile_completion = serializers.DictField()


class StepValidationRequestSerializer(serializers.Serializer):
    """Serializer for step validation requests."""
    
    step = serializers.IntegerField(min_value=0, max_value=10)
    data = serializers.JSONField()


class StepValidationResponseSerializer(serializers.Serializer):
    """Serializer for step validation responses."""
    
    is_valid = serializers.BooleanField()
    validated_data = serializers.JSONField(required=False)
    errors = serializers.DictField(required=False)


# Dashboard Serializers for Teacher Dashboard API

class ProgressAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for progress assessments in dashboard context."""
    
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    grade_letter = serializers.CharField(read_only=True)
    
    class Meta:
        model = ProgressAssessment
        fields = [
            'id', 'assessment_type', 'title', 'score', 'max_score',
            'percentage', 'grade_letter', 'assessment_date', 
            'skills_assessed', 'teacher_notes', 'is_graded'
        ]


class StudentProgressDashboardSerializer(serializers.ModelSerializer):
    """Serializer for student progress in dashboard context."""
    
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    recent_assessments = ProgressAssessmentSerializer(many=True, read_only=True)
    average_assessment_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = StudentProgress
        fields = [
            'id', 'student_name', 'student_email', 'course_name',
            'current_level', 'completion_percentage', 'skills_mastered',
            'current_topics', 'notes', 'last_assessment_date',
            'recent_assessments', 'average_assessment_score', 'updated_at'
        ]


class DashboardSessionSerializer(serializers.Serializer):
    """Serializer for class sessions in dashboard context."""
    
    id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    session_type = serializers.CharField()
    grade_level = serializers.CharField()
    student_count = serializers.IntegerField()
    student_names = serializers.ListField(child=serializers.CharField())
    status = serializers.CharField()
    notes = serializers.CharField()
    duration_hours = serializers.DecimalField(max_digits=4, decimal_places=2)


class DashboardEarningsSerializer(serializers.Serializer):
    """Serializer for earnings data in dashboard context."""
    
    current_month_total = serializers.DecimalField(max_digits=8, decimal_places=2)
    last_month_total = serializers.DecimalField(max_digits=8, decimal_places=2)
    pending_amount = serializers.DecimalField(max_digits=8, decimal_places=2)
    total_hours_taught = serializers.DecimalField(max_digits=6, decimal_places=2)
    recent_payments = serializers.ListField(child=serializers.DictField())


class DashboardQuickStatsSerializer(serializers.Serializer):
    """Serializer for quick stats in dashboard."""
    
    total_students = serializers.IntegerField()
    sessions_today = serializers.IntegerField()
    sessions_this_week = serializers.IntegerField()
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, allow_null=True)


class DashboardProgressMetricsSerializer(serializers.Serializer):
    """Serializer for progress metrics in dashboard."""
    
    average_student_progress = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_assessments_given = serializers.IntegerField()
    students_improved_this_month = serializers.IntegerField()
    completion_rate_trend = serializers.DecimalField(max_digits=5, decimal_places=2)


class DashboardTeacherInfoSerializer(serializers.Serializer):
    """Serializer for teacher info in dashboard context."""
    
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.CharField()
    specialty = serializers.CharField()
    hourly_rate = serializers.DecimalField(max_digits=6, decimal_places=2)
    profile_completion_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    schools = serializers.ListField(child=serializers.DictField())
    courses_taught = serializers.ListField(child=serializers.DictField())


class TeacherConsolidatedDashboardSerializer(serializers.Serializer):
    """Main serializer for consolidated teacher dashboard response."""
    
    teacher_info = DashboardTeacherInfoSerializer()
    students = StudentProgressDashboardSerializer(many=True)
    sessions = serializers.DictField()  # Contains 'today', 'upcoming', 'recent_completed'
    progress_metrics = DashboardProgressMetricsSerializer()
    recent_activities = serializers.ListField(child=serializers.DictField())
    earnings = DashboardEarningsSerializer()
    quick_stats = DashboardQuickStatsSerializer()
    
    def to_representation(self, instance):
        """Custom representation to ensure proper data structure."""
        return {
            'teacher_info': instance.get('teacher_info', {}),
            'students': instance.get('students', []),
            'sessions': instance.get('sessions', {}),
            'progress_metrics': instance.get('progress_metrics', {}),
            'recent_activities': instance.get('recent_activities', []),
            'earnings': instance.get('earnings', {}),
            'quick_stats': instance.get('quick_stats', {}),
        }



