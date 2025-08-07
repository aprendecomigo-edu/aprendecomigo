from typing import ClassVar

from accounts.models import CustomUser, TeacherProfile
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import (
    ClassSchedule,
    ClassStatus,
    ClassType,
    RecurringClassSchedule,
    TeacherAvailability,
    TeacherUnavailability,
)


class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=TeacherProfile.objects.all(),
        required=False,  # Made optional so teachers can create their own availability
        allow_null=True
    )

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

    def validate(self, data):
        """Validate availability data using model validation"""
        # For updates, merge with existing instance data to avoid incomplete validation
        if self.instance:
            # This is an update operation, merge with existing data
            temp_data = {}
            # Get existing instance data for model fields only
            model_fields = [f.name for f in TeacherAvailability._meta.get_fields() if not f.many_to_many]
            
            for field_name in model_fields:
                if field_name not in ['id']:  # Skip primary key and auto fields
                    if hasattr(self.instance, field_name):
                        value = getattr(self.instance, field_name)
                        # Handle foreign key fields properly
                        if hasattr(value, 'pk'):
                            temp_data[field_name] = value
                        else:
                            temp_data[field_name] = value
            
            # Override with new data, resolving foreign key relationships
            for field_name, value in data.items():
                if field_name == 'teacher' and isinstance(value, int):
                    # Convert teacher ID to TeacherProfile instance
                    temp_data[field_name] = TeacherProfile.objects.get(id=value)
                elif field_name == 'school' and isinstance(value, int):
                    # Convert school ID to School instance  
                    from accounts.models import School
                    temp_data[field_name] = School.objects.get(id=value)
                else:
                    temp_data[field_name] = value
            
            # Create temporary instance with complete data
            instance = TeacherAvailability(**temp_data)
            instance.pk = self.instance.pk  # Preserve primary key for overlap checks
        else:
            # This is a create operation, resolve foreign key relationships
            temp_data = data.copy()
            
            # Resolve foreign key fields to actual model instances
            if 'teacher' in temp_data and isinstance(temp_data['teacher'], int):
                temp_data['teacher'] = TeacherProfile.objects.get(id=temp_data['teacher'])
            if 'school' in temp_data and isinstance(temp_data['school'], int):
                from accounts.models import School
                temp_data['school'] = School.objects.get(id=temp_data['school'])
            
            instance = TeacherAvailability(**temp_data)
        
        try:
            instance.clean()
        except ValidationError as e:
            # Convert Django ValidationError to DRF ValidationError
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
        return data


class TeacherUnavailabilitySerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=TeacherProfile.objects.all(),
        required=False,  # Made optional so teachers can create their own unavailability
        allow_null=True
    )

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

    def validate(self, data):
        """Custom validation for unavailability"""
        # If is_all_day is True, clear start_time and end_time
        if data.get('is_all_day'):
            data['start_time'] = None
            data['end_time'] = None
        
        # For updates, merge with existing instance data to avoid incomplete validation
        if self.instance:
            # This is an update operation, merge with existing data
            temp_data = {}
            # Get existing instance data for model fields only
            model_fields = [f.name for f in TeacherUnavailability._meta.get_fields() if not f.many_to_many]
            
            for field_name in model_fields:
                if field_name not in ['id']:  # Skip primary key and auto fields
                    if hasattr(self.instance, field_name):
                        value = getattr(self.instance, field_name)
                        # Handle foreign key fields properly
                        if hasattr(value, 'pk'):
                            temp_data[field_name] = value
                        else:
                            temp_data[field_name] = value
            
            # Override with new data, resolving foreign key relationships
            for field_name, value in data.items():
                if field_name == 'teacher' and isinstance(value, int):
                    # Convert teacher ID to TeacherProfile instance
                    temp_data[field_name] = TeacherProfile.objects.get(id=value)
                elif field_name == 'school' and isinstance(value, int):
                    # Convert school ID to School instance  
                    from accounts.models import School
                    temp_data[field_name] = School.objects.get(id=value)
                else:
                    temp_data[field_name] = value
            
            # Create temporary instance with complete data
            instance = TeacherUnavailability(**temp_data)
            instance.pk = self.instance.pk  # Preserve primary key for overlap checks
        else:
            # This is a create operation, resolve foreign key relationships
            temp_data = data.copy()
            
            # Resolve foreign key fields to actual model instances
            if 'teacher' in temp_data and isinstance(temp_data['teacher'], int):
                temp_data['teacher'] = TeacherProfile.objects.get(id=temp_data['teacher'])
            if 'school' in temp_data and isinstance(temp_data['school'], int):
                from accounts.models import School
                temp_data['school'] = School.objects.get(id=temp_data['school'])
            
            instance = TeacherUnavailability(**temp_data)
        
        try:
            instance.clean()
        except ValidationError as e:
            # Convert Django ValidationError to DRF ValidationError
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
        
        return data


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
    
    # New computed fields for group classes
    participant_count = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    participants_names = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    
    # Timezone-aware datetime fields
    scheduled_datetime_utc = serializers.SerializerMethodField()
    scheduled_datetime_local = serializers.SerializerMethodField()

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
            # New fields
            "max_participants",
            "metadata",
            "participant_count",
            "participants",
            "participants_names", 
            "is_full",
            "scheduled_datetime_utc",
            "scheduled_datetime_local",
        ]
        read_only_fields: ClassVar = [
            "booked_by",
            "booked_at",
            "cancelled_at",
            "completed_at",
            "created_at",
            "updated_at",
            "can_be_cancelled",
            "is_past",
            "participant_count",
            "participants",
            "participants_names",
            "is_full",
            "scheduled_datetime_utc", 
            "scheduled_datetime_local",
        ]

    def get_additional_students_names(self, obj):
        return [student.name for student in obj.additional_students.all()]

    def get_participant_count(self, obj):
        return obj.get_total_participants()

    def get_participants(self, obj):
        """Return list of all participant IDs (main student + additional students)"""
        participants = [obj.student.id]
        participants.extend([student.id for student in obj.additional_students.all()])
        return participants

    def get_participants_names(self, obj):
        """Return list of all participant names"""
        names = [obj.student.name]
        names.extend([student.name for student in obj.additional_students.all()])
        return names

    def get_is_full(self, obj):
        """Return True if class is at capacity"""
        return obj.is_at_capacity()

    def get_scheduled_datetime_utc(self, obj):
        """Return scheduled datetime in UTC timezone"""
        try:
            utc_dt = obj.get_scheduled_datetime_utc()
            return utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception:
            return None

    def get_scheduled_datetime_local(self, obj):
        """Return scheduled datetime in teacher's local timezone"""
        try:
            local_dt = obj.get_scheduled_datetime_in_teacher_timezone()
            return local_dt.strftime('%Y-%m-%dT%H:%M:%S%z')
        except Exception:
            return None


class CreateClassScheduleSerializer(serializers.ModelSerializer):
    """Serializer for creating class schedules with validation"""

    class Meta:
        model = ClassSchedule
        fields: ClassVar = [
            "id",
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
            "max_participants",
            "metadata",
            "teacher_notes",
            "student_notes",
        ]
        read_only_fields: ClassVar = ["id"]

    def validate(self, data):
        """Validate class schedule data"""
        # Check that scheduled_date is not in the past
        if data["scheduled_date"] < timezone.now().date():
            raise serializers.ValidationError("Cannot schedule classes in the past.")

        # Check that start_time is before end_time
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("End time must be after start time.")

        # Validate max_participants for group classes
        class_type = data.get("class_type")
        max_participants = data.get("max_participants")
        additional_students = data.get("additional_students", [])
        
        if class_type == ClassType.GROUP:
            if not max_participants:
                raise serializers.ValidationError("Max participants is required for group classes.")
            
            # Check if total participants exceed max_participants
            total_participants = 1 + len(additional_students)  # main student + additional
            if total_participants > max_participants:
                raise serializers.ValidationError({
                    "max_participants": f"Total participants ({total_participants}) exceeds max participants limit ({max_participants})."
                })
        elif class_type == ClassType.INDIVIDUAL and max_participants:
            raise serializers.ValidationError("Individual classes should not have max_participants set.")

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
