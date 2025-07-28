import re
from typing import ClassVar

from common.serializers import BaseNestedModelSerializer, BaseSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Course,
    EducationalSystem,
    EmailDeliveryStatus,
    InvitationStatus,
    School,
    SchoolActivity,
    SchoolInvitation,
    SchoolMembership,
    SchoolRole,
    SchoolSettings,
    StudentProfile,
    TeacherCourse,
    TeacherInvitation,
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
    """Serializer for school settings"""
    
    class Meta:
        model = SchoolSettings
        fields = [
            'trial_cost_absorption',
            'default_session_duration',
            'timezone',
            'dashboard_refresh_interval',
            'activity_retention_days'
        ]


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
            "viewed_at",
        ]


class SingleInvitationSerializer(serializers.Serializer):
    """
    Serializer for a single invitation in a bulk request.
    """
    
    email = serializers.CharField()  # Use CharField to allow invalid emails, validate in view


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
        """Validate invitation list for duplicates and limits."""
        if len(value) == 0:
            raise serializers.ValidationError("At least one invitation is required")
        
        if len(value) > 100:
            raise serializers.ValidationError("Maximum 100 invitations allowed per batch")
        
        # Note: Duplicate and invalid email validation moved to view level
        # to allow partial success handling as per API requirements
        
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
