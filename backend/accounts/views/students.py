"""
Student management views for the accounts app.

This module contains all views related to student management,
including student profiles, onboarding, and student creation.
"""

import logging

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..db_queries import (
    can_user_manage_school,
    list_school_ids_owned_or_managed,
)
from ..models import (
    CustomUser,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
)
from ..permissions import (
    IsOwnerOrSchoolAdmin,
)
from ..serializers import (
    CreateStudentSerializer,
    SchoolMembershipSerializer,
    StudentSerializer,
    UserSerializer,
)
from ..views.auth import KnoxAuthenticatedViewSet

logger = logging.getLogger(__name__)


class StudentViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for student profiles.
    """

    serializer_class = StudentSerializer

    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        - Students: can only access their own profile
        - Teachers: can access profiles of students they teach (via ClassSession)
        - School owners/admins: can access profiles of students in their schools
        """
        user = self.request.user

        # User can see their own student profile
        if hasattr(user, "student_profile"):
            own_profile = StudentProfile.objects.filter(user=user)
        else:
            own_profile = StudentProfile.objects.none()

        # Check if user has permission to see other profiles
        if SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True,
        ).exists():
            # School owners/admins can see students in their schools
            admin_school_ids = list_school_ids_owned_or_managed(user)
            admin_accessible = StudentProfile.objects.filter(
                user__school_memberships__school_id__in=admin_school_ids,
                user__school_memberships__role=SchoolRole.STUDENT,
                user__school_memberships__is_active=True,
            ).distinct()
            return (own_profile | admin_accessible).distinct()

        elif SchoolMembership.objects.filter(
            user=user, role=SchoolRole.TEACHER, is_active=True
        ).exists() and hasattr(user, "teacher_profile"):
            # Teachers can only see students they actually teach (via ClassSession)
            from finances.models import ClassSession

            taught_student_ids = ClassSession.objects.filter(
                teacher=user.teacher_profile
            ).values_list("students", flat=True)

            teacher_accessible = StudentProfile.objects.filter(
                user_id__in=taught_student_ids
            ).distinct()
            return (own_profile | teacher_accessible).distinct()

        # For students and other users, only show their own profile
        return own_profile

    def get_permissions(self):
        if self.action == "create":
            # Only authenticated users can create their own student profile
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only student themselves, or school admin can modify student records
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def onboarding(self, request):
        """
        Create student profile during onboarding.
        """
        # Check if user already has a student profile
        if hasattr(request.user, "student_profile"):
            return Response(
                {"error": "Student profile already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create student profile
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def create_student(self, request):
        """
        Create a complete student record (user + profile + school membership) in one request.
        This action is only available to school administrators.
        """
        # Validate the request data
        serializer = CreateStudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        # Check if user has permission to add students to the specified school
        school = validated_data["school_id"]
        if not can_user_manage_school(request.user, school):
            return Response(
                {"error": "You don't have permission to add students to this school"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            with transaction.atomic():
                # Create the user
                user_data = {
                    "name": validated_data["name"],
                    "email": validated_data["email"],
                    "phone_number": validated_data.get("phone_number", ""),
                    "primary_contact": validated_data.get("primary_contact", "email"),
                }
                user = CustomUser.objects.create_user(**user_data)

                # Create the student profile
                student_data = {
                    "educational_system": validated_data["educational_system_id"],
                    "school_year": validated_data["school_year"],
                    "birth_date": validated_data["birth_date"],
                    "address": validated_data.get("address", ""),
                }
                student_profile = StudentProfile.objects.create(user=user, **student_data)

                # Create school membership
                school_membership = SchoolMembership.objects.create(
                    user=user, school=school, role=SchoolRole.STUDENT, is_active=True
                )

                # Prepare response data
                response_data = {
                    "message": "Student created successfully",
                    "user": UserSerializer(user).data,
                    "student": StudentSerializer(student_profile).data,
                    "school_membership": SchoolMembershipSerializer(school_membership).data,
                    "user_created": True,
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating student: {e!s}")
            return Response(
                {"error": "Failed to create student. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )