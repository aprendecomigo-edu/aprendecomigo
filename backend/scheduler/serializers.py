from typing import ClassVar

from django.utils import timezone
from rest_framework import serializers

from .models import (
    ClassSchedule,
    ClassStatus,
    RecurringClassSchedule,
    TeacherAvailability,
    TeacherUnavailability,
)


class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model = TeacherAvailability
        fields: ClassVar = [
            "id",
            "teacher",
            "teacher_name",
            "school",
            "school_name",
            "day_of_week",
            "day_of_week_display",
            "start_time",
            "end_time",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar = ["created_at", "updated_at"]


class TeacherUnavailabilitySerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = TeacherUnavailability
        fields: ClassVar = [
            "id",
            "teacher",
            "teacher_name",
            "school",
            "school_name",
            "date",
            "start_time",
            "end_time",
            "reason",
            "is_all_day",
            "created_at",
        ]
        read_only_fields: ClassVar = ["created_at"]


class ClassScheduleSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    student_name = serializers.CharField(source="student.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    booked_by_name = serializers.CharField(source="booked_by.name", read_only=True)
    class_type_display = serializers.CharField(source="get_class_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    additional_students_names = serializers.SerializerMethodField()
    can_be_cancelled = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)

    class Meta:
        model = ClassSchedule
        fields: ClassVar = [
            "id",
            "teacher",
            "teacher_name",
            "student",
            "student_name",
            "school",
            "school_name",
            "title",
            "description",
            "class_type",
            "class_type_display",
            "status",
            "status_display",
            "scheduled_date",
            "start_time",
            "end_time",
            "duration_minutes",
            "booked_by",
            "booked_by_name",
            "booked_at",
            "additional_students_names",
            "cancelled_at",
            "cancellation_reason",
            "completed_at",
            "teacher_notes",
            "student_notes",
            "can_be_cancelled",
            "is_past",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar = [
            "booked_at",
            "cancelled_at",
            "completed_at",
            "created_at",
            "updated_at",
            "can_be_cancelled",
            "is_past",
        ]

    def get_additional_students_names(self, obj):
        return [student.name for student in obj.additional_students.all()]


class CreateClassScheduleSerializer(serializers.ModelSerializer):
    """Serializer for creating class schedules with validation"""

    class Meta:
        model = ClassSchedule
        fields: ClassVar = [
            "teacher",
            "student",
            "school",
            "title",
            "description",
            "class_type",
            "scheduled_date",
            "start_time",
            "end_time",
            "duration_minutes",
            "additional_students",
        ]

    def validate(self, data):
        """Validate class schedule data"""
        # Check that scheduled_date is not in the past
        if data["scheduled_date"] < timezone.now().date():
            raise serializers.ValidationError("Cannot schedule classes in the past.")

        # Check that start_time is before end_time
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("End time must be after start time.")

        # Check for teacher availability
        teacher = data["teacher"]
        school = data["school"]
        date = data["scheduled_date"]
        start_time = data["start_time"]
        end_time = data["end_time"]

        # Check if teacher is available on this day of the week
        day_of_week = date.strftime("%A").lower()
        availability = TeacherAvailability.objects.filter(
            teacher=teacher, school=school, day_of_week=day_of_week, is_active=True
        ).first()

        if not availability:
            raise serializers.ValidationError(f"Teacher is not available on {day_of_week}s")

        # Check if the time fits within available hours
        if start_time < availability.start_time or end_time > availability.end_time:
            raise serializers.ValidationError(
                f"Class time must be within teacher's available hours "
                f"({availability.start_time} - {availability.end_time})"
            )

        # Check for teacher unavailability
        unavailability = TeacherUnavailability.objects.filter(
            teacher=teacher, school=school, date=date
        ).first()

        if unavailability:
            if unavailability.is_all_day:
                raise serializers.ValidationError(f"Teacher is unavailable on {date}")
            elif (
                unavailability.start_time <= start_time < unavailability.end_time
                or unavailability.start_time < end_time <= unavailability.end_time
            ):
                raise serializers.ValidationError(
                    f"Teacher is unavailable from {unavailability.start_time} to {unavailability.end_time}"
                )

        # Check for conflicting classes
        conflicting_classes = (
            ClassSchedule.objects.filter(
                teacher=teacher,
                school=school,
                scheduled_date=date,
                status__in=[ClassStatus.SCHEDULED, ClassStatus.CONFIRMED],
            )
            .exclude(end_time__lte=start_time)
            .exclude(start_time__gte=end_time)
        )

        if conflicting_classes.exists():
            raise serializers.ValidationError("Teacher already has a class scheduled at this time")

        return data

    def create(self, validated_data):
        """Create class schedule with booked_by set to current user"""
        validated_data["booked_by"] = self.context["request"].user
        return super().create(validated_data)


class RecurringClassScheduleSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    student_name = serializers.CharField(source="student.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.name", read_only=True)
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)
    class_type_display = serializers.CharField(source="get_class_type_display", read_only=True)

    class Meta:
        model = RecurringClassSchedule
        fields: ClassVar = [
            "id",
            "teacher",
            "teacher_name",
            "student",
            "student_name",
            "school",
            "school_name",
            "title",
            "description",
            "class_type",
            "class_type_display",
            "day_of_week",
            "day_of_week_display",
            "start_time",
            "end_time",
            "duration_minutes",
            "start_date",
            "end_date",
            "is_active",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar = ["created_at", "updated_at"]

    def create(self, validated_data):
        """Create recurring schedule with created_by set to current user"""
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class AvailableTimeSlotsSerializer(serializers.Serializer):
    """Serializer for available time slots"""

    teacher_id = serializers.IntegerField()
    date = serializers.DateField()
    available_slots = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )


class CancelClassSerializer(serializers.Serializer):
    """Serializer for cancelling classes"""

    reason = serializers.CharField(required=False, allow_blank=True)
