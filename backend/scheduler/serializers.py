from django.core.exceptions import ValidationError
from rest_framework import serializers

from accounts.models import CustomUser, School, TeacherProfile

from .models import (
    ClassReminder,
    ClassSchedule,
    ClassType,
    CommunicationChannel,
    RecurringClassSchedule,
    ReminderPreference,
    ReminderType,
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
        allow_null=True,
        allow_empty=True
    )

    class Meta:
        model = TeacherAvailability
        fields = [
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
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        """Validate availability data using model validation"""
        # For updates, merge with existing instance data to avoid incomplete validation
        if self.instance:
            # This is an update operation, merge with existing data
            temp_data = {}
            # Get existing instance data for model fields only
            model_fields = [f.name for f in TeacherAvailability._meta.get_fields() if not f.many_to_many]

            for field_name in model_fields:
                if field_name not in ["id"] and hasattr(self.instance, field_name):  # Skip primary key and auto fields
                    value = getattr(self.instance, field_name)
                    # Handle foreign key fields properly
                    if hasattr(value, "pk"):
                        temp_data[field_name] = value
                    else:
                        temp_data[field_name] = value

            # Override with new data, resolving foreign key relationships
            for field_name, value in data.items():
                if field_name == 'teacher' and value is not None and isinstance(value, int):
                    # Convert teacher ID to TeacherProfile instance
                    temp_data[field_name] = TeacherProfile.objects.get(id=value)
                elif field_name == "school" and isinstance(value, int):
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
            if 'teacher' in temp_data and temp_data['teacher'] is not None:
                if isinstance(temp_data['teacher'], int):
                    temp_data['teacher'] = TeacherProfile.objects.get(id=temp_data['teacher'])
            if 'school' in temp_data and isinstance(temp_data['school'], int):
                from accounts.models import School

                temp_data["school"] = School.objects.get(id=temp_data["school"])

            # Skip model validation if teacher is missing (handled in view)
            if "teacher" not in temp_data or temp_data["teacher"] is None:
                return data

            instance = TeacherAvailability(**temp_data)

        try:
            instance.clean()
        except ValidationError as e:
            # Convert Django ValidationError to DRF ValidationError
            raise serializers.ValidationError(e.message_dict if hasattr(e, "message_dict") else str(e))
        return data


class TeacherUnavailabilitySerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=TeacherProfile.objects.all(),
        required=False,  # Made optional so teachers can create their own unavailability
        allow_null=True,
    )

    class Meta:
        model = TeacherUnavailability
        fields = [
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
        read_only_fields = ["created_at"]

    def validate(self, data):
        """Custom validation for unavailability"""
        # If is_all_day is True, clear start_time and end_time
        if data.get("is_all_day"):
            data["start_time"] = None
            data["end_time"] = None

        # For updates, merge with existing instance data to avoid incomplete validation
        if self.instance:
            # This is an update operation, merge with existing data
            temp_data = {}
            # Get existing instance data for model fields only
            model_fields = [f.name for f in TeacherUnavailability._meta.get_fields() if not f.many_to_many]

            for field_name in model_fields:
                if field_name not in ["id"] and hasattr(self.instance, field_name):  # Skip primary key and auto fields
                    value = getattr(self.instance, field_name)
                    # Handle foreign key fields properly
                    if hasattr(value, "pk"):
                        temp_data[field_name] = value
                    else:
                        temp_data[field_name] = value

            # Override with new data, resolving foreign key relationships
            for field_name, value in data.items():
                if field_name == 'teacher' and value is not None and isinstance(value, int):
                    # Convert teacher ID to TeacherProfile instance
                    temp_data[field_name] = TeacherProfile.objects.get(id=value)
                elif field_name == "school" and isinstance(value, int):
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
            if "teacher" in temp_data and isinstance(temp_data["teacher"], int):
                temp_data["teacher"] = TeacherProfile.objects.get(id=temp_data["teacher"])
            if "school" in temp_data and isinstance(temp_data["school"], int):
                from accounts.models import School

                temp_data["school"] = School.objects.get(id=temp_data["school"])

            instance = TeacherUnavailability(**temp_data)

        try:
            instance.clean()
        except ValidationError as e:
            # Convert Django ValidationError to DRF ValidationError
            raise serializers.ValidationError(e.message_dict if hasattr(e, "message_dict") else str(e))

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

    # Completion and no-show metadata
    completed_by_name = serializers.CharField(source="completed_by.name", read_only=True)
    no_show_by_name = serializers.CharField(source="no_show_by.name", read_only=True)

    # Status history
    status_history = serializers.SerializerMethodField()

    class Meta:
        model = ClassSchedule
        fields = [
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
            "completed_by",
            "completed_by_name",
            "actual_duration_minutes",
            "completion_notes",
            "no_show_at",
            "no_show_by",
            "no_show_by_name",
            "no_show_reason",
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
            "status_history",
        ]
        read_only_fields = [
            "booked_by",
            "booked_at",
            "cancelled_at",
            "completed_at",
            "completed_by",
            "completed_by_name",
            "actual_duration_minutes",
            "completion_notes",
            "no_show_at",
            "no_show_by",
            "no_show_by_name",
            "no_show_reason",
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
            "status_history",
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
            return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return None

    def get_scheduled_datetime_local(self, obj):
        """Return scheduled datetime in teacher's local timezone"""
        try:
            local_dt = obj.get_scheduled_datetime_in_teacher_timezone()
            return local_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        except Exception:
            return None

    def get_status_history(self, obj):
        """Return status change history for the class"""
        from .services import ClassStatusHistoryService

        history_service = ClassStatusHistoryService()
        history = history_service.get_status_history(obj)

        # Format timestamps for JSON serialization
        for entry in history:
            if entry.get("timestamp"):
                entry["timestamp"] = entry["timestamp"].isoformat()

        return history


class CreateClassScheduleSerializer(serializers.ModelSerializer):
    """Serializer for creating class schedules with validation"""

    # Support both API parameter names for backward compatibility
    teacher_id = serializers.IntegerField(source="teacher", write_only=True, required=False)
    date = serializers.DateField(source="scheduled_date", write_only=True, required=False)

    class Meta:
        model = ClassSchedule
        fields = [
            "id",
            "teacher",
            "teacher_id",
            "student",
            "school",
            "title",
            "description",
            "class_type",
            "scheduled_date",
            "date",
            "start_time",
            "end_time",
            "duration_minutes",
            "additional_students",
            "max_participants",
            "metadata",
            "teacher_notes",
            "student_notes",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        """Validate class schedule data using BookingOrchestratorService"""
        from datetime import datetime, timedelta

        from .services import BookingOrchestratorService

        # Set default duration if not provided
        if "duration_minutes" not in data or data["duration_minutes"] is None:
            data["duration_minutes"] = 60

        # Handle start_time string input (support both time objects and strings)
        start_time = data.get("start_time")
        if isinstance(start_time, str):
            from .services import BookingValidationService

            validation_service = BookingValidationService()
            data["start_time"] = validation_service.validate_time_format(start_time)

        # Calculate end_time if not provided
        if "end_time" not in data or not data["end_time"]:
            start_datetime = datetime.combine(data["scheduled_date"], data["start_time"])
            end_datetime = start_datetime + timedelta(minutes=data["duration_minutes"])
            data["end_time"] = end_datetime.time()
        else:
            # If end_time is provided, validate it's after start_time
            if data["start_time"] >= data["end_time"]:
                raise serializers.ValidationError("End time must be after start time.")

        # Validate group class capacity if additional students are provided
        if data.get("class_type") == ClassType.GROUP:
            max_participants = data.get("max_participants")
            additional_students = data.get("additional_students", [])
            total_participants = 1 + len(additional_students)  # 1 primary + additional

            if max_participants and total_participants > max_participants:
                raise serializers.ValidationError(
                    f"Total participants ({total_participants}) exceeds maximum allowed ({max_participants})"
                )

        # Prepare booking data for orchestrator validation
        booking_data = {
            "teacher": data["teacher"],
            "student": data["student"],
            "school": data["school"],
            "date": data["scheduled_date"],
            "start_time": data["start_time"],
            "duration_minutes": data["duration_minutes"],
            "class_type": data.get("class_type", ClassType.INDIVIDUAL),
            "max_participants": data.get("max_participants"),
            "title": data.get("title", "Class"),
            "description": data.get("description", ""),
            "booked_by": self.context["request"].user,
        }

        # Use orchestrator service for validation
        orchestrator = BookingOrchestratorService()
        validation_result = orchestrator.validate_booking_request(booking_data)

        if not validation_result["is_valid"]:
            # Convert validation errors to DRF ValidationError format
            error_messages = validation_result["errors"]
            if len(error_messages) == 1:
                raise serializers.ValidationError(error_messages[0])
            else:
                # Multiple errors - create a general error with details
                combined_message = "; ".join(error_messages)
                raise serializers.ValidationError(combined_message)

        return data

    def create(self, validated_data):
        """Create class schedule using BookingOrchestratorService"""
        from .services import BookingOrchestratorService

        # Prepare booking data for orchestrator
        booking_data = {
            "teacher": validated_data["teacher"],
            "student": validated_data["student"],
            "school": validated_data["school"],
            "date": validated_data["scheduled_date"],
            "start_time": validated_data["start_time"],
            "duration_minutes": validated_data["duration_minutes"],
            "class_type": validated_data.get("class_type", ClassType.INDIVIDUAL),
            "max_participants": validated_data.get("max_participants"),
            "title": validated_data.get("title", "Class"),
            "description": validated_data.get("description", ""),
            "booked_by": self.context["request"].user,
        }

        # Use orchestrator service to create booking
        orchestrator = BookingOrchestratorService()
        result = orchestrator.create_booking(booking_data)

        return result["class_schedule"]


class RecurringClassScheduleSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.name", read_only=True)
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)
    class_type_display = serializers.CharField(source="get_class_type_display", read_only=True)
    frequency_type_display = serializers.CharField(source="get_frequency_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    # Student management fields
    students = serializers.PrimaryKeyRelatedField(many=True, queryset=CustomUser.objects.all(), required=False)
    student_names = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()

    # Generated instances tracking
    generated_instances_count = serializers.SerializerMethodField()
    future_instances_count = serializers.SerializerMethodField()

    # Status change tracking
    cancelled_by_name = serializers.CharField(source="cancelled_by.name", read_only=True)
    paused_by_name = serializers.CharField(source="paused_by.name", read_only=True)

    class Meta:
        model = RecurringClassSchedule
        fields = [
            "id",
            "teacher",
            "teacher_name",
            "students",
            "student_names",
            "student_count",
            "school",
            "school_name",
            "title",
            "description",
            "class_type",
            "class_type_display",
            "frequency_type",
            "frequency_type_display",
            "status",
            "status_display",
            "max_participants",
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
            "cancelled_at",
            "cancelled_by",
            "cancelled_by_name",
            "paused_at",
            "paused_by",
            "paused_by_name",
            "generated_instances_count",
            "future_instances_count",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "cancelled_at",
            "cancelled_by",
            "paused_at",
            "paused_by",
        ]

    def get_student_names(self, obj):
        """Get list of student names"""
        return [student.name for student in obj.students.all()]

    def get_student_count(self, obj):
        """Get count of students"""
        return obj.get_student_count()

    def get_generated_instances_count(self, obj):
        """Get count of generated class instances"""
        return obj.generated_instances.count()

    def get_future_instances_count(self, obj):
        """Get count of future class instances"""
        return obj.get_future_instances().count()

    def validate(self, data):
        """Validate recurring class schedule data"""
        # Validate max_participants for group classes
        class_type = data.get("class_type")
        max_participants = data.get("max_participants")

        if class_type == ClassType.GROUP:
            if not max_participants or max_participants <= 0:
                raise serializers.ValidationError(
                    {"max_participants": "Max participants is required for group classes."}
                )
        elif class_type == ClassType.INDIVIDUAL:
            # Individual classes should have max 1 student
            students = data.get("students", [])
            if len(students) > 1:
                raise serializers.ValidationError({"students": "Individual classes can only have one student."})

        # Validate date range
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if end_date and start_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})

        # Validate time range
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        return data

    def create(self, validated_data):
        """Create recurring schedule with created_by set to current user"""
        students_data = validated_data.pop("students", [])
        validated_data["created_by"] = self.context["request"].user

        instance = super().create(validated_data)

        # Add students
        if students_data:
            instance.students.set(students_data)

        return instance

    def update(self, instance, validated_data):
        """Update recurring schedule"""
        students_data = validated_data.pop("students", None)

        instance = super().update(instance, validated_data)

        # Update students if provided
        if students_data is not None:
            instance.students.set(students_data)

        return instance


class CancelRecurringInstanceSerializer(serializers.Serializer):
    """Serializer for cancelling specific recurring class instances"""

    date = serializers.DateField(help_text="Date of the occurrence to cancel")
    reason = serializers.CharField(
        required=False, allow_blank=True, max_length=500, help_text="Reason for cancellation"
    )


class AddStudentToRecurringSerializer(serializers.Serializer):
    """Serializer for adding students to recurring classes"""

    student_id = serializers.IntegerField(help_text="ID of the student to add")


class RemoveStudentFromRecurringSerializer(serializers.Serializer):
    """Serializer for removing students from recurring classes"""

    student_id = serializers.IntegerField(help_text="ID of the student to remove")


class GenerateRecurringSchedulesSerializer(serializers.Serializer):
    """Serializer for generating schedules from recurring template"""

    weeks_ahead = serializers.IntegerField(
        default=4, min_value=1, max_value=52, help_text="Number of weeks ahead to generate (1-52)"
    )
    skip_existing = serializers.BooleanField(default=True, help_text="Whether to skip existing schedules")


class AvailableTimeSlotsSerializer(serializers.Serializer):
    """Serializer for available time slots"""

    teacher_id = serializers.IntegerField()
    date = serializers.DateField()
    available_slots = serializers.ListField(child=serializers.DictField(child=serializers.CharField()))


class CancelClassSerializer(serializers.Serializer):
    """Serializer for cancelling classes"""

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,  # Add reasonable limit to prevent abuse
        help_text="Reason for cancellation (max 500 characters)",
    )


class ReminderPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user reminder preferences"""

    user_name = serializers.CharField(source="user.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    school = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=School.objects.all())

    class Meta:
        model = ReminderPreference
        fields = [
            "id",
            "user",
            "user_name",
            "school",
            "school_name",
            "reminder_timing_hours",
            "communication_channels",
            "timezone_preference",
            "is_active",
            "is_school_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def validate_reminder_timing_hours(self, value):
        """Validate reminder timing hours"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of numbers")

        for hour in value:
            if not isinstance(hour, int | float):
                raise serializers.ValidationError("Each value must be a number")
            if hour < 0 or hour > 168:  # Max 1 week
                raise serializers.ValidationError("Hours must be between 0 and 168 (1 week)")

        return value

    def validate_communication_channels(self, value):
        """Validate communication channels"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of channel names")

        valid_channels = [choice[0] for choice in CommunicationChannel.choices]
        for channel in value:
            if channel not in valid_channels:
                raise serializers.ValidationError(f"Invalid channel '{channel}'. Must be one of: {valid_channels}")

        return value

    def validate_timezone_preference(self, value):
        """Validate timezone preference"""
        if value:
            from .reminder_services import TimezoneValidationService

            if not TimezoneValidationService.validate_timezone(value):
                raise serializers.ValidationError("Invalid timezone")
        return value


class ClassReminderSerializer(serializers.ModelSerializer):
    """Serializer for class reminders"""

    class_title = serializers.CharField(source="class_schedule.title", read_only=True)
    recipient_name = serializers.CharField(source="recipient.name", read_only=True)
    reminder_type_display = serializers.CharField(source="get_reminder_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    communication_channel_display = serializers.CharField(source="get_communication_channel_display", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    time_until_send = serializers.SerializerMethodField()
    can_retry = serializers.BooleanField(read_only=True)

    class Meta:
        model = ClassReminder
        fields = [
            "id",
            "class_schedule",
            "class_title",
            "reminder_type",
            "reminder_type_display",
            "recipient",
            "recipient_name",
            "recipient_type",
            "communication_channel",
            "communication_channel_display",
            "status",
            "status_display",
            "scheduled_for",
            "sent_at",
            "subject",
            "message",
            "error_message",
            "retry_count",
            "max_retries",
            "external_message_id",
            "metadata",
            "is_overdue",
            "time_until_send",
            "can_retry",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "sent_at",
            "error_message",
            "retry_count",
            "external_message_id",
            "created_at",
            "updated_at",
            "is_overdue",
            "can_retry",
        ]

    def get_time_until_send(self, obj):
        """Get time until reminder should be sent"""
        delta = obj.time_until_send
        if delta is None:
            return None

        total_seconds = int(delta.total_seconds())
        if total_seconds < 0:
            return "Overdue"

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


class TriggerReminderSerializer(serializers.Serializer):
    """Serializer for manually triggering reminders"""

    reminder_type = serializers.ChoiceField(choices=ReminderType.choices, help_text="Type of reminder to send")
    message = serializers.CharField(
        required=False, allow_blank=True, max_length=1000, help_text="Custom message content (for custom reminders)"
    )
    channels = serializers.ListField(
        child=serializers.ChoiceField(choices=CommunicationChannel.choices),
        required=False,
        help_text="Communication channels to use",
    )
    subject = serializers.CharField(required=False, allow_blank=True, max_length=255, help_text="Custom subject/title")


class ReminderQueueStatusSerializer(serializers.Serializer):
    """Serializer for reminder queue status"""

    pending_reminders = serializers.IntegerField()
    processing_reminders = serializers.IntegerField()
    failed_reminders = serializers.IntegerField()
    last_processed_at = serializers.DateTimeField(allow_null=True)
    queue_health = serializers.CharField()
    worker_status = serializers.CharField()


class ProcessReminderQueueSerializer(serializers.Serializer):
    """Serializer for processing reminder queue"""

    batch_size = serializers.IntegerField(
        default=50, min_value=1, max_value=200, help_text="Number of reminders to process per batch"
    )
    max_batches = serializers.IntegerField(
        default=10, min_value=1, max_value=50, help_text="Maximum number of batches to process"
    )
