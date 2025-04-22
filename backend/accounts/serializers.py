from common.serializers import BaseNestedModelSerializer, BaseSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Student, Teacher

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
            "user_type",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class StudentSerializer(BaseNestedModelSerializer):
    """
    Serializer for the Student model.
    """

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=User.objects.filter(user_type="student"),
        source="user",
        required=False,
    )

    class Meta:
        model = Student
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
    Serializer for the Teacher model.
    """

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=User.objects.filter(user_type="teacher"),
        source="user",
        required=False,
    )

    class Meta:
        model = Teacher
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
