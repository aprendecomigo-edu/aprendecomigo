from common.serializers import BaseNestedModelSerializer, BaseSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    School,
    SchoolInvitation,
    SchoolMembership,
    StudentProfile,
    TeacherProfile,
    SCHOOL_ROLE_CHOICES
)

User = get_user_model()


class UserSerializer(BaseSerializer):
    """
    Serializer for the User model.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "name",
            "phone_number",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class SchoolSerializer(BaseSerializer):
    """
    Serializer for the School model.
    """
    
    class Meta:
        model = School
        fields = (
            "id",
            "name",
            "description",
            "address",
            "contact_email",
            "phone_number",
            "website",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class SchoolMembershipSerializer(BaseNestedModelSerializer):
    """
    Serializer for the SchoolMembership model.
    """
    
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=User.objects.all(),
        source="user"
    )
    
    school = SchoolSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=School.objects.all(),
        source="school"
    )
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = SchoolMembership
        fields = (
            "id",
            "user",
            "user_id",
            "school",
            "school_id",
            "role",
            "role_display",
            "is_active",
            "joined_at",
        )
        read_only_fields = ("id", "joined_at")


class SchoolInvitationSerializer(BaseNestedModelSerializer):
    """
    Serializer for the SchoolInvitation model.
    """
    
    school = SchoolSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=School.objects.all(),
        source="school"
    )
    
    invited_by = UserSerializer(read_only=True)
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = SchoolInvitation
        fields = (
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
        )
        read_only_fields = (
            "id", 
            "invited_by", 
            "token", 
            "created_at", 
            "expires_at", 
            "is_accepted"
        )


class SchoolWithMembersSerializer(SchoolSerializer):
    """
    Extended School serializer that includes member information.
    """
    
    members = serializers.SerializerMethodField()
    
    class Meta(SchoolSerializer.Meta):
        fields = SchoolSerializer.Meta.fields + ("members",)
    
    def get_members(self, obj):
        memberships = obj.memberships.filter(is_active=True)
        return SchoolMembershipSerializer(memberships, many=True).data


class StudentSerializer(BaseNestedModelSerializer):
    """
    Serializer for the StudentProfile model.
    """

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=User.objects.all(),
        source="user",
        required=False,
    )

    class Meta:
        model = StudentProfile
        fields = (
            "id",
            "user",
            "user_id",
            "school_year",
            "birth_date",
            "address",
            "cc_number",
            "cc_photo",
            "calendar_iframe",
        )
        read_only_fields = ("id",)


class TeacherSerializer(BaseNestedModelSerializer):
    """
    Serializer for the TeacherProfile model.
    """

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=User.objects.all(),
        source="user",
        required=False,
    )

    class Meta:
        model = TeacherProfile
        fields = (
            "id",
            "user",
            "user_id",
            "bio",
            "specialty",
            "education",
            "hourly_rate",
            "availability",
            "address",
            "phone_number",
            "calendar_iframe",
        )
        read_only_fields = ("id",)


class UserWithRolesSerializer(UserSerializer):
    """
    Extended User serializer that includes role information.
    """
    
    roles = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("roles",)
    
    def get_roles(self, obj):
        memberships = obj.school_memberships.filter(is_active=True)
        roles_data = []
        
        for membership in memberships:
            roles_data.append({
                "school": {
                    "id": membership.school.id,
                    "name": membership.school.name
                },
                "role": membership.role,
                "role_display": membership.get_role_display()
            })
            
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
    role = serializers.ChoiceField(choices=SCHOOL_ROLE_CHOICES)
    school_id = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True)


class InvitationAcceptSerializer(serializers.Serializer):
    """
    Serializer for accepting a school invitation.
    """
    
    token = serializers.CharField()


class OnboardingSerializer(serializers.Serializer):
    """
    Serializer for the onboarding process.
    
    This serializer handles the data for updating both user and school information
    during the onboarding process after signup.
    """
    
    user = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        help_text="User profile information"
    )
    
    school = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        help_text="School information"
    )
    
    def validate_user(self, value):
        """Validate user data"""
        # Extract only fields that are allowed to be updated
        allowed_fields = ['name', 'phone_number']
        user_data = {k: v for k, v in value.items() if k in allowed_fields}
        
        # Validate name field (required)
        if 'name' in user_data and not user_data['name']:
            raise serializers.ValidationError({"name": "Name is required"})
        elif 'name' in user_data and len(user_data['name']) > 150:
            raise serializers.ValidationError({"name": "Name must be less than 150 characters"})
        
        # Validate phone number format (optional)
        if 'phone_number' in user_data and user_data['phone_number']:
            import re
            if not re.match(r'^\+?[0-9\s\-\(\)]{5,20}$', user_data['phone_number']):
                raise serializers.ValidationError({"phone_number": "Invalid phone number format"})
            
            if len(user_data['phone_number']) > 20:
                raise serializers.ValidationError({"phone_number": "Phone number must be less than 20 characters"})
        
        # Validate using UserSerializer for additional validation
        serializer = UserSerializer(data=user_data, partial=True)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        
        return user_data
    
    def validate_school(self, value):
        """Validate school data"""
        # Extract only fields that are allowed to be updated
        allowed_fields = [
            'name', 'description', 'address', 
            'contact_email', 'phone_number', 'website'
        ]
        school_data = {k: v for k, v in value.items() if k in allowed_fields}
        
        # Validate name field (required)
        if 'name' in school_data and not school_data['name']:
            raise serializers.ValidationError({"name": "School name is required"})
        elif 'name' in school_data and len(school_data['name']) > 150:
            raise serializers.ValidationError({"name": "School name must be less than 150 characters"})
        
        # Validate contact email format (optional)
        if 'contact_email' in school_data and school_data['contact_email']:
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(school_data['contact_email'])
            except ValidationError:
                raise serializers.ValidationError({"contact_email": "Invalid email format"})
        
        # Validate phone number format (optional)
        if 'phone_number' in school_data and school_data['phone_number']:
            import re
            if not re.match(r'^\+?[0-9\s\-\(\)]{5,20}$', school_data['phone_number']):
                raise serializers.ValidationError({"phone_number": "Invalid phone number format"})
            
            if len(school_data['phone_number']) > 20:
                raise serializers.ValidationError({"phone_number": "Phone number must be less than 20 characters"})
        
        # Validate website URL format (optional)
        if 'website' in school_data and school_data['website']:
            from django.core.validators import URLValidator
            from django.core.exceptions import ValidationError
            validate_url = URLValidator()
            try:
                validate_url(school_data['website'])
            except ValidationError:
                raise serializers.ValidationError({"website": "Invalid URL format"})
        
        # Validate using SchoolSerializer for additional validation
        serializer = SchoolSerializer(data=school_data, partial=True)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        
        return school_data
    
    def validate(self, data):
        """
        Ensure that at least one of user or school is provided
        """
        if not data.get('user') and not data.get('school'):
            raise serializers.ValidationError("At least one of 'user' or 'school' information must be provided")
        return data
