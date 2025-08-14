"""
Course management views for the accounts app.

This module contains all views related to course management,
including courses, educational systems, and teacher-course relationships.
"""

from collections import defaultdict
import logging
from typing import ClassVar

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..db_queries import (
    list_school_ids_owned_or_managed,
)
from ..models import (
    Course,
    EducationalSystem,
    SchoolMembership,
    SchoolRole,
    TeacherCourse,
)
from ..permissions import (
    IsSchoolOwnerOrAdmin,
    IsTeacherInAnySchool,
)
from ..serializers import (
    CourseSerializer,
    EducationalSystemSerializer,
    TeacherCourseSerializer,
)
from ..views.auth import KnoxAuthenticatedViewSet

logger = logging.getLogger(__name__)


class CourseViewSet(KnoxAuthenticatedViewSet):
    """
    Enhanced API endpoint for courses with advanced filtering, popularity metrics, and market data.

    Features:
    - Advanced filtering by educational system, education level, and search
    - Popularity metrics based on session data
    - Market data including pricing information
    - Teacher availability information
    - Caching for performance optimization
    """

    serializer_class = CourseSerializer

    def get_queryset(self):
        """
        Get courses with optional filtering and enhanced data.
        """
        queryset = Course.objects.select_related("educational_system").all()

        # Apply filters
        queryset = self._apply_filters(queryset)

        # Apply search
        search_query = self.request.query_params.get("search")
        if search_query:
            queryset = queryset.filter(
                models.Q(name__icontains=search_query)
                | models.Q(description__icontains=search_query)
                | models.Q(code__icontains=search_query)
            )

        # Apply ordering
        ordering: ClassVar = self.request.query_params.get("ordering")
        if ordering:
            # Handle special ordering cases
            if ordering in ["popularity_score", "-popularity_score"]:
                # Popularity ordering will be handled in list() method
                pass
            elif ordering in ["avg_hourly_rate", "-avg_hourly_rate"]:
                # Price ordering will be handled in list() method
                pass
            else:
                # Standard Django ordering
                try:
                    queryset = queryset.order_by(ordering)
                except Exception:
                    # Invalid ordering, use default
                    queryset = queryset.order_by("name")
        else:
            queryset = queryset.order_by("name")

        return queryset

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Only school admins can create/modify courses
            permission_classes: ClassVar = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            # Anyone can view courses
            permission_classes: ClassVar = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        """
        Enhanced list method with popularity metrics, market data, and teacher info.
        """
        try:
            # Check cache first if enhanced data is requested
            cache_key = self._get_cache_key(request)
            if self._should_use_cache(request):
                cached_data = cache.get(cache_key)
                if cached_data:
                    return Response(cached_data)

            # Get base queryset
            queryset = self.filter_queryset(self.get_queryset())

            # Serialize base course data
            serializer = self.get_serializer(queryset, many=True)
            courses_data = serializer.data

            # Enhance with additional data if requested
            if self._needs_enhancement(request):
                courses_data = self._enhance_courses_data(courses_data, request)

            # Apply custom ordering if needed
            ordering: ClassVar = request.query_params.get("ordering")
            if ordering in ["popularity_score", "-popularity_score", "avg_hourly_rate", "-avg_hourly_rate"]:
                courses_data = self._apply_custom_ordering(courses_data, ordering)

            # Cache results if appropriate
            if self._should_use_cache(request):
                cache.set(cache_key, courses_data, timeout=900)  # 15 minutes

            return Response(courses_data)

        except DRFValidationError:
            # Re-raise validation errors so they return proper 400 responses
            raise
        except Exception as e:
            logger.error(f"Error in CourseViewSet.list for user {request.user.id}: {e}")
            return Response({"error": "Failed to retrieve course data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _apply_filters(self, queryset):
        """Apply filtering based on query parameters."""
        # Filter by educational system
        educational_system_id = self.request.query_params.get("educational_system")
        if educational_system_id:
            try:
                educational_system_id = int(educational_system_id)
                if not EducationalSystem.objects.filter(id=educational_system_id).exists():
                    raise ValidationError("Invalid educational system ID")
                queryset = queryset.filter(educational_system_id=educational_system_id)
            except (ValueError, ValidationError):
                # Invalid ID - raise a 400 error
                raise DRFValidationError({"educational_system": "Invalid educational system ID"})

        # Filter by education level
        education_level = self.request.query_params.get("education_level")
        if education_level:
            queryset = queryset.filter(education_level=education_level)

        return queryset

    def _needs_enhancement(self, request):
        """Check if enhanced data is requested."""
        return any(
            [
                request.query_params.get("include_popularity") == "true",
                request.query_params.get("include_teachers") == "true",
                request.query_params.get("include_market_data") == "true",
            ]
        )

    def _should_use_cache(self, request):
        """Determine if caching should be used."""
        return self._needs_enhancement(request)

    def _get_cache_key(self, request):
        """Generate cache key based on request parameters."""
        key_parts = ["courses_enhanced"]

        # Add filter parameters
        for param in ["educational_system", "education_level", "search", "ordering"]:
            value = request.query_params.get(param)
            if value:
                key_parts.append(f"{param}_{value}")

        # Add enhancement flags
        for param in ["include_popularity", "include_teachers", "include_market_data"]:
            if request.query_params.get(param) == "true":
                key_parts.append(param)

        return "_".join(key_parts)

    def _enhance_courses_data(self, courses_data, request):
        """Add enhanced data to courses."""

        # Get course IDs for efficient querying
        course_ids = [course["id"] for course in courses_data]

        # Prepare enhancement data
        popularity_data = {}
        teacher_data = {}
        market_data = {}

        # Calculate popularity metrics if requested
        if request.query_params.get("include_popularity") == "true":
            popularity_data = self._calculate_popularity_metrics(course_ids)

        # Get teacher information if requested
        if request.query_params.get("include_teachers") == "true":
            teacher_data = self._get_teacher_information(course_ids)

        # Calculate market data if requested
        if request.query_params.get("include_market_data") == "true":
            market_data = self._calculate_market_data(course_ids)

        # Enhance each course with additional data
        for course in courses_data:
            course_id = course["id"]

            if course_id in popularity_data:
                course["popularity_metrics"] = popularity_data[course_id]

            if course_id in teacher_data:
                course["available_teachers"] = teacher_data[course_id]

            if course_id in market_data:
                course["market_data"] = market_data[course_id]

        return courses_data

    def _calculate_popularity_metrics(self, course_ids):
        """Calculate popularity metrics for courses."""
        from finances.models import ClassSession, SessionStatus

        # NOTE: This is a simplified implementation that counts all sessions for teachers
        # who teach a course, regardless of which specific course the session was for.
        # In practice, you might want to track session-to-course relationships more precisely.

        # Get course associations through teacher-course relationships
        teacher_courses = TeacherCourse.objects.filter(course_id__in=course_ids).select_related("teacher", "course")

        # Map courses to teachers
        course_teachers = defaultdict(list)
        for tc in teacher_courses:
            course_teachers[tc.course_id].append(tc.teacher_id)

        # Calculate metrics per course
        course_metrics = {}
        for course_id in course_ids:
            teachers = course_teachers.get(course_id, [])

            if not teachers:
                # No teachers for this course
                course_metrics[course_id] = {
                    "total_sessions": 0,
                    "unique_students": 0,
                    "popularity_score": 0,
                    "rank": 0,
                }
                continue

            # Get sessions for teachers of this course
            sessions = ClassSession.objects.filter(
                teacher_id__in=teachers, status=SessionStatus.COMPLETED
            ).prefetch_related("students")

            total_sessions = sessions.count()
            unique_students = set()
            for session in sessions:
                for student in session.students.all():
                    unique_students.add(student.id)

            # Calculate popularity score (sessions * 2 + unique_students * 3)
            popularity_score = total_sessions * 2 + len(unique_students) * 3

            course_metrics[course_id] = {
                "total_sessions": total_sessions,
                "unique_students": len(unique_students),
                "popularity_score": popularity_score,
                "rank": 0,  # Will be calculated after all scores are computed
            }

        # Calculate ranks
        sorted_courses = sorted(course_metrics.items(), key=lambda x: x[1]["popularity_score"], reverse=True)

        for rank, (course_id, _metrics) in enumerate(sorted_courses, 1):
            course_metrics[course_id]["rank"] = rank

        return course_metrics

    def _get_teacher_information(self, course_ids):
        """Get teacher information for courses."""
        teacher_data = {}

        # Get teacher-course relationships
        teacher_courses = TeacherCourse.objects.filter(course_id__in=course_ids, is_active=True).select_related(
            "teacher__user", "course"
        )

        # Group by course
        for tc in teacher_courses:
            course_id = tc.course_id
            if course_id not in teacher_data:
                teacher_data[course_id] = []

            teacher_info = {
                "id": tc.teacher.id,
                "name": tc.teacher.user.name,
                "email": tc.teacher.user.email,
                "hourly_rate": float(tc.hourly_rate) if tc.hourly_rate else float(tc.teacher.hourly_rate or 0),
                "profile_completion_score": float(tc.teacher.profile_completion_score),
                "is_profile_complete": tc.teacher.is_profile_complete,
                "specialty": tc.teacher.specialty,
            }

            teacher_data[course_id].append(teacher_info)

        return teacher_data

    def _calculate_market_data(self, course_ids):
        """Calculate market data for courses."""

        market_data = {}

        # Get aggregated data from teacher-course relationships
        for course_id in course_ids:
            teacher_courses = TeacherCourse.objects.filter(course_id=course_id, is_active=True).exclude(
                hourly_rate__isnull=True
            )

            if teacher_courses.exists():
                # Use teacher-course specific rates where available
                rates = [float(tc.hourly_rate) for tc in teacher_courses if tc.hourly_rate]

                # Fallback to teacher profile rates if no course-specific rates
                if not rates:
                    rates = [float(tc.teacher.hourly_rate) for tc in teacher_courses if tc.teacher.hourly_rate]

                if rates:
                    avg_rate = sum(rates) / len(rates)
                    min_rate = min(rates)
                    max_rate = max(rates)
                else:
                    avg_rate = min_rate = max_rate = 0.0

                total_teachers = teacher_courses.count()

                # Calculate demand score based on teacher availability and sessions
                # This is a simplified calculation - in production, you might want more sophisticated scoring
                demand_score = min(100, total_teachers * 10)  # Cap at 100

            else:
                avg_rate = min_rate = max_rate = 0.0
                total_teachers = 0
                demand_score = 0

            market_data[course_id] = {
                "avg_hourly_rate": avg_rate,
                "min_hourly_rate": min_rate,
                "max_hourly_rate": max_rate,
                "total_teachers": total_teachers,
                "demand_score": demand_score,
            }

        return market_data

    def _apply_custom_ordering(self, courses_data, ordering):
        """Apply custom ordering for enhanced data."""
        if ordering == "popularity_score":
            courses_data.sort(key=lambda x: x.get("popularity_metrics", {}).get("popularity_score", 0))
        elif ordering == "-popularity_score":
            courses_data.sort(key=lambda x: x.get("popularity_metrics", {}).get("popularity_score", 0), reverse=True)
        elif ordering == "avg_hourly_rate":
            courses_data.sort(key=lambda x: x.get("market_data", {}).get("avg_hourly_rate", 0))
        elif ordering == "-avg_hourly_rate":
            courses_data.sort(key=lambda x: x.get("market_data", {}).get("avg_hourly_rate", 0), reverse=True)

        return courses_data


class EducationalSystemViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for educational systems.
    All users can view educational systems, but only admins can create/modify them.
    """

    serializer_class = EducationalSystemSerializer

    def get_queryset(self):
        """
        All authenticated users can see active educational systems.
        """
        return EducationalSystem.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Only school admins can create/modify educational systems
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            # Anyone can view educational systems
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class TeacherCourseViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for teacher-course relationships.
    """

    serializer_class = TeacherCourseSerializer

    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        - Teachers: can only access their own course relationships
        - School owners/admins: can access relationships for teachers in their schools
        """
        user = self.request.user

        # Check if user is a teacher and get their course relationships
        if hasattr(user, "teacher_profile"):
            own_relationships = TeacherCourse.objects.filter(teacher=user.teacher_profile)
        else:
            own_relationships = TeacherCourse.objects.none()

        # Check if user has permission to see other relationships
        if SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True,
        ).exists():
            # School owners/admins can see relationships of teachers in their schools
            admin_school_ids = list_school_ids_owned_or_managed(user)
            admin_accessible = TeacherCourse.objects.filter(
                teacher__user__school_memberships__school_id__in=admin_school_ids,
                teacher__user__school_memberships__role=SchoolRole.TEACHER,
                teacher__user__school_memberships__is_active=True,
            ).distinct()
            return (own_relationships | admin_accessible).distinct()

        # For teachers, only show their own relationships
        return own_relationships

    def get_permissions(self):
        if self.action == "create":
            # Only teachers can create course relationships
            permission_classes = [IsAuthenticated, IsTeacherInAnySchool]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only teacher or school admin can modify relationships
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Create a teacher-course relationship for the current teacher.
        """
        if not hasattr(self.request.user, "teacher_profile"):
            raise serializers.ValidationError("Only teachers can create course relationships")
        serializer.save(teacher=self.request.user.teacher_profile)

    def check_object_permissions(self, request, obj):
        """
        Check that the user has permission to access this specific teacher-course relationship.
        """
        super().check_object_permissions(request, obj)

        # Teachers can only modify their own relationships
        if self.action in ["update", "partial_update", "destroy"]:
            if hasattr(request.user, "teacher_profile") and obj.teacher == request.user.teacher_profile:
                return

            # School admins can modify relationships of teachers in their schools
            admin_school_ids = list_school_ids_owned_or_managed(request.user)
            if SchoolMembership.objects.filter(
                user=obj.teacher.user,
                school_id__in=admin_school_ids,
                role=SchoolRole.TEACHER,
                is_active=True,
            ).exists():
                return

            # If none of the above, deny permission
            raise PermissionDenied("You don't have permission to modify this teacher-course relationship")
