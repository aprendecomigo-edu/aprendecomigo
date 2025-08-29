from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import pytz

from accounts.models import CustomUser, School, SchoolMembership, TeacherProfile


class WeekDay(models.TextChoices):
    """Days of the week for availability"""

    MONDAY = "monday", _("Monday")
    TUESDAY = "tuesday", _("Tuesday")
    WEDNESDAY = "wednesday", _("Wednesday")
    THURSDAY = "thursday", _("Thursday")
    FRIDAY = "friday", _("Friday")
    SATURDAY = "saturday", _("Saturday")
    SUNDAY = "sunday", _("Sunday")


class ClassType(models.TextChoices):
    """Types of class sessions"""

    INDIVIDUAL = "individual", _("Individual")
    GROUP = "group", _("Group")
    TRIAL = "trial", _("Trial")


class ClassStatus(models.TextChoices):
    """Status of a class session"""

    SCHEDULED = "scheduled", _("Scheduled")
    CONFIRMED = "confirmed", _("Confirmed")
    COMPLETED = "completed", _("Completed")
    CANCELLED = "cancelled", _("Cancelled")
    NO_SHOW = "no_show", _("No Show")
    REJECTED = "rejected", _("Rejected")


class TeacherAvailability(models.Model):
    """
    Teacher availability for recurring weekly schedule.
    Teachers can set their available time slots for each day of the week.
    """

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="availabilities")
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="teacher_availabilities",
        help_text=_("School context for this availability"),
    )
    day_of_week = models.CharField(_("day of week"), max_length=10, choices=WeekDay.choices)
    start_time = models.TimeField(_("start time"))
    end_time = models.TimeField(_("end time"))
    is_active = models.BooleanField(_("is active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["teacher", "school", "day_of_week", "start_time"]
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.teacher.user.name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    def clean(self):
        """Validate that start_time is before end_time and no overlaps exist"""
        if self.start_time >= self.end_time:
            raise ValidationError({"end_time": _("End time must be after start time.")})

        # Check for overlapping availability periods
        if self.teacher and self.school:
            existing_availabilities = TeacherAvailability.objects.filter(
                teacher=self.teacher, school=self.school, day_of_week=self.day_of_week, is_active=True
            )

            # Exclude self when updating
            if self.pk:
                existing_availabilities = existing_availabilities.exclude(pk=self.pk)

            for availability in existing_availabilities:
                # Check for time overlap: two time periods overlap if one starts before the other ends
                if not (self.end_time <= availability.start_time or self.start_time >= availability.end_time):
                    raise ValidationError(
                        {
                            "start_time": _(
                                f"Availability period overlaps with existing period {availability.start_time}-{availability.end_time}"
                            )
                        }
                    )


class TeacherUnavailability(models.Model):
    """
    Teacher unavailability for specific dates/times.
    This overrides the regular availability for holidays, sick days, etc.
    """

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="unavailabilities")
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="teacher_unavailabilities",
        help_text=_("School context for this unavailability"),
    )
    date = models.DateField(_("date"))
    start_time = models.TimeField(_("start time"), null=True, blank=True)
    end_time = models.TimeField(_("end time"), null=True, blank=True)
    reason = models.CharField(_("reason"), max_length=255, blank=True)
    is_all_day = models.BooleanField(_("all day"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["teacher", "school", "date", "start_time"]
        ordering = ["date", "start_time"]

    def __str__(self):
        if self.is_all_day:
            return f"{self.teacher.user.name} - {self.date} (All Day)"
        return f"{self.teacher.user.name} - {self.date} {self.start_time}-{self.end_time}"

    def clean(self):
        """Validate unavailability times and check for overlaps"""
        # Validate that date is not in the past
        from django.utils import timezone

        if self.date and self.date < timezone.now().date():
            raise ValidationError({"date": _("Cannot create unavailability for past dates.")})

        if not self.is_all_day:
            if not self.start_time or not self.end_time:
                raise ValidationError(
                    {"start_time": _("Start time and end time are required for partial day unavailability.")}
                )
            if self.start_time >= self.end_time:
                raise ValidationError({"end_time": _("End time must be after start time.")})
        
        # Check for overlapping unavailabilities
        if self.teacher and self.school and self.date:
            overlapping_unavailability = TeacherUnavailability.objects.filter(
                teacher=self.teacher,
                school=self.school,
                date=self.date
            )
            
            # Exclude current instance if updating
            if self.pk:
                overlapping_unavailability = overlapping_unavailability.exclude(pk=self.pk)
            
            # Check for exact overlap or any time overlap
            if self.is_all_day:
                # If this is all day, check if any other unavailability exists for this date
                if overlapping_unavailability.exists():
                    raise ValidationError({
                        "date": _("There is already an unavailability for this teacher on this date.")
                    })
            else:
                # Check for time-based overlaps
                for existing in overlapping_unavailability:
                    if existing.is_all_day:
                        # Existing is all day, so any partial day overlaps
                        raise ValidationError({
                            "date": _("Teacher is already unavailable all day on this date.")
                        })
                    
                    # Check time overlap: start_time < existing.end_time AND end_time > existing.start_time
                    if (self.start_time < existing.end_time and 
                        self.end_time > existing.start_time):
                        raise ValidationError({
                            "start_time": _("This time period overlaps with an existing unavailability.")
                        })


class ClassSchedule(models.Model):
    """
    Scheduled class sessions between teachers and students.
    """

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="scheduled_classes")
    student = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="scheduled_classes",
        help_text=_("Student participating in this class"),
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="class_schedules")
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    class_type = models.CharField(
        _("class type"), max_length=20, choices=ClassType.choices, default=ClassType.INDIVIDUAL
    )
    status = models.CharField(_("status"), max_length=20, choices=ClassStatus.choices, default=ClassStatus.SCHEDULED)
    scheduled_date = models.DateField(_("scheduled date"))
    start_time = models.TimeField(_("start time"))
    end_time = models.TimeField(_("end time"))
    duration_minutes = models.PositiveIntegerField(_("duration in minutes"))

    # Booking information
    booked_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="booked_classes",
        help_text=_("User who booked this class"),
    )
    booked_at = models.DateTimeField(_("booked at"), auto_now_add=True)

    # Additional participants for group classes
    additional_students = models.ManyToManyField(
        CustomUser,
        related_name="group_classes",
        blank=True,
        help_text=_("Additional students for group classes"),
    )

    # Cancellation/completion info
    cancelled_at = models.DateTimeField(_("cancelled at"), null=True, blank=True)
    cancelled_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_classes",
        help_text=_("User who cancelled this class"),
    )
    cancellation_reason = models.TextField(_("cancellation reason"), blank=True)
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)
    completed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_classes",
        help_text=_("User who marked this class as completed"),
    )
    actual_duration_minutes = models.PositiveIntegerField(_("actual duration in minutes"), null=True, blank=True)
    completion_notes = models.TextField(_("completion notes"), blank=True)

    # No-show info
    no_show_at = models.DateTimeField(_("marked no-show at"), null=True, blank=True)
    no_show_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="no_show_classes",
        help_text=_("User who marked this class as no-show"),
    )
    no_show_reason = models.TextField(_("no-show reason"), blank=True)

    # Confirmation info
    confirmed_at = models.DateTimeField(_("confirmed at"), null=True, blank=True)
    confirmed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_classes",
        help_text=_("User who confirmed this class"),
    )

    # Rejection info
    rejected_at = models.DateTimeField(_("rejected at"), null=True, blank=True)
    rejected_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_classes",
        help_text=_("User who rejected this class"),
    )

    # Group class capacity management
    max_participants = models.PositiveIntegerField(
        _("maximum participants"),
        null=True,
        blank=True,
        help_text=_("Maximum number of participants allowed for group classes"),
    )

    # Enhanced metadata for structured data storage
    metadata = models.JSONField(
        _("metadata"), default=dict, blank=True, help_text=_("Additional structured metadata for the class")
    )

    # Link to recurring schedule template if generated from one
    recurring_schedule = models.ForeignKey(
        "RecurringClassSchedule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_instances",
        help_text=_("Recurring schedule that generated this instance"),
    )

    # Notes
    teacher_notes = models.TextField(_("teacher notes"), blank=True)
    student_notes = models.TextField(_("student notes"), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_date", "start_time"]
        indexes = [
            models.Index(fields=["teacher", "scheduled_date"]),
            models.Index(fields=["student", "scheduled_date"]),
            models.Index(fields=["school", "scheduled_date"]),
            models.Index(fields=["status", "scheduled_date"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.scheduled_date} {self.start_time}"

    def save(self, *args, **kwargs):
        """Override save to emit signals on status changes"""
        # Track status changes for signal emission
        old_status = None
        emit_signal = False

        if self.pk:
            # Get old status if this is an update
            try:
                old_instance = ClassSchedule.objects.get(pk=self.pk)
                old_status = old_instance.status
                # Check if status has changed
                if old_status != self.status:
                    emit_signal = True
            except ClassSchedule.DoesNotExist:
                # New instance, no signal needed for creation
                pass

        # Call parent save
        super().save(*args, **kwargs)

        # Emit signal if status changed
        if emit_signal:
            from .signals import class_status_changed

            # Get the user who made the change (from context if available)
            changed_by = getattr(self, "_changed_by_user", None)
            class_status_changed.send(
                sender=self.__class__,
                instance=self,
                old_status=old_status,
                new_status=self.status,
                changed_by=changed_by,
            )

    def clean(self):
        """Validate class schedule"""
        # Check that start_time is before end_time
        if self.start_time >= self.end_time:
            raise ValidationError({"end_time": _("End time must be after start time.")})

        # Check that scheduled_date is not in the past
        if self.scheduled_date < timezone.now().date():
            raise ValidationError({"scheduled_date": _("Cannot schedule classes in the past.")})

        # Validate max_participants for group classes
        if self.class_type == ClassType.GROUP:
            if self.max_participants is None:
                raise ValidationError({"max_participants": _("Max participants is required for group classes.")})
            if self.max_participants <= 0:
                raise ValidationError({"max_participants": _("Max participants must be a positive integer.")})
        elif self.class_type == ClassType.INDIVIDUAL and self.max_participants:
            # Individual classes should not have max_participants set
            self.max_participants = None

        # Validate metadata if provided
        if self.metadata:
            self._validate_metadata()

        # Check that student has a school membership
        if not SchoolMembership.objects.filter(user=self.student, school=self.school, is_active=True).exists():
            raise ValidationError({"student": _("Student must be a member of the school.")})

        # Check that teacher has a school membership
        if not SchoolMembership.objects.filter(user=self.teacher.user, school=self.school, is_active=True).exists():
            raise ValidationError({"teacher": _("Teacher must be a member of the school.")})

    @property
    def can_be_cancelled(self):
        """Check if the class can still be cancelled"""
        if self.status in [ClassStatus.COMPLETED, ClassStatus.CANCELLED]:
            return False
        return not self.is_past

    # Group class capacity management methods
    def get_total_participants(self):
        """Get the total number of participants including main student and additional students"""
        if self.class_type == ClassType.INDIVIDUAL:
            return 1
        # Count main student plus additional students
        return 1 + self.additional_students.count()

    def can_add_participant(self, user=None):
        """Check if more participants can be added to this group class"""
        if self.class_type == ClassType.INDIVIDUAL:
            return False
        if not self.max_participants:
            return True  # No limit set
        return self.get_total_participants() < self.max_participants

    def add_participant(self, user):
        """Add a participant to this group class if capacity allows"""
        if self.class_type == ClassType.INDIVIDUAL:
            raise ValidationError("Cannot add participants to individual classes.")

        if not self.can_add_participant():
            raise ValidationError("Class has reached maximum capacity.")

        # Check if user is already the main student
        if user == self.student:
            raise ValidationError("User is already the main student in this class.")

        # Check if user is already an additional student
        if self.additional_students.filter(id=user.id).exists():
            raise ValidationError("User is already a participant in this class.")

        self.additional_students.add(user)

    def is_at_capacity(self):
        """Check if the class is at maximum capacity"""
        if self.class_type == ClassType.INDIVIDUAL:
            return True
        if not self.max_participants:
            return False  # No limit set
        return self.get_total_participants() >= self.max_participants

    def get_available_spots(self):
        """Get the number of available spots remaining"""
        if self.class_type == ClassType.INDIVIDUAL:
            return 0
        if not self.max_participants:
            return float("inf")  # No limit
        return max(0, self.max_participants - self.get_total_participants())

    # Timezone-aware datetime methods
    def get_scheduled_datetime_in_teacher_timezone(self):
        """Get the scheduled datetime in the teacher's timezone (from school settings)"""
        # Get school timezone from school settings
        try:
            school_timezone_str = self.school.settings.timezone
        except (AttributeError, ValueError, TypeError):
            school_timezone_str = "UTC"

        school_tz = pytz.timezone(school_timezone_str)

        # Create naive datetime from date and start_time
        naive_datetime = datetime.combine(self.scheduled_date, self.start_time)

        # Localize to school timezone
        return school_tz.localize(naive_datetime)

    def get_scheduled_datetime_utc(self):
        """Get the scheduled datetime in UTC"""
        local_dt = self.get_scheduled_datetime_in_teacher_timezone()
        return local_dt.astimezone(pytz.UTC)

    @property
    def is_past(self):
        """Check if the class is in the past (timezone-aware)"""
        scheduled_dt_utc = self.get_scheduled_datetime_utc()
        return scheduled_dt_utc < timezone.now()

    def can_cancel_within_deadline(self, hours_before=2):
        """Check if class can be cancelled within the deadline in teacher's timezone"""
        if self.status in [ClassStatus.COMPLETED, ClassStatus.CANCELLED]:
            return False

        scheduled_dt_utc = self.get_scheduled_datetime_utc()
        deadline = scheduled_dt_utc - timedelta(hours=hours_before)
        return timezone.now() < deadline

    def get_class_duration_in_teacher_timezone(self):
        """Get start and end datetime as timezone-aware objects in teacher's timezone"""
        try:
            school_timezone_str = self.school.settings.timezone
        except (AttributeError, ValueError, TypeError):
            school_timezone_str = "UTC"

        school_tz = pytz.timezone(school_timezone_str)

        # Create naive datetimes
        start_naive = datetime.combine(self.scheduled_date, self.start_time)
        end_naive = datetime.combine(self.scheduled_date, self.end_time)

        # Localize to school timezone
        start_dt = school_tz.localize(start_naive)
        end_dt = school_tz.localize(end_naive)

        return start_dt, end_dt

    # Metadata helper methods
    def get_metadata_value(self, key, default=None):
        """Safely get a metadata value with default fallback"""
        if not self.metadata:
            return default
        return self.metadata.get(key, default)

    def update_metadata(self, updates):
        """Update specific metadata fields with validation"""
        if not isinstance(updates, dict):
            raise ValidationError("Metadata updates must be a dictionary")

        # Initialize metadata if it's empty
        if not self.metadata:
            self.metadata = {}

        # Update metadata with new values
        self.metadata.update(updates)

        # Validate metadata structure based on class type
        self._validate_metadata()

        self.save(update_fields=["metadata"])

    def _validate_metadata(self):
        """Validate metadata structure and required fields"""
        if not self.metadata:
            return

        errors = {}

        # Validate difficulty_level if present
        if "difficulty_level" in self.metadata:
            valid_levels = ["beginner", "intermediate", "advanced"]
            if self.metadata["difficulty_level"] not in valid_levels:
                errors["difficulty_level"] = f"Invalid difficulty level. Must be one of: {valid_levels}"

        # Validate topics as list of strings
        if "topics" in self.metadata:
            topics = self.metadata["topics"]
            if not isinstance(topics, list):
                errors["topics"] = "Topics must be a list of strings"
            else:
                for topic in topics:
                    if not isinstance(topic, str):
                        errors["topics"] = "Each topic must be a string"
                        break

        # Additional validation for group classes
        if self.class_type == ClassType.GROUP and self.metadata:
            required_group_fields = ["group_dynamics", "interaction_level", "collaboration_type"]
            missing_fields = [field for field in required_group_fields if field not in self.metadata]
            if missing_fields:
                errors["metadata"] = (
                    f"Group classes must include the following metadata fields: {', '.join(missing_fields)}"
                )

        if errors:
            raise ValidationError(errors)


class FrequencyType(models.TextChoices):
    """Frequency types for recurring classes"""

    WEEKLY = "WEEKLY", _("Weekly")
    BIWEEKLY = "BIWEEKLY", _("Biweekly")
    MONTHLY = "MONTHLY", _("Monthly")


class RecurringClassStatus(models.TextChoices):
    """Status types for recurring class series"""

    ACTIVE = "ACTIVE", _("Active")
    PAUSED = "PAUSED", _("Paused")
    CANCELLED = "CANCELLED", _("Cancelled")


class ReminderType(models.TextChoices):
    """Types of reminders that can be sent"""

    CONFIRMATION = "confirmation", _("Confirmation")
    REMINDER_24H = "reminder_24h", _("24 Hours Before")
    REMINDER_1H = "reminder_1h", _("1 Hour Before")
    REMINDER_15MIN = "reminder_15min", _("15 Minutes Before")
    CANCELLATION = "cancellation", _("Cancellation")
    CHANGE = "change", _("Schedule Change")
    CUSTOM = "custom", _("Custom")


class CommunicationChannel(models.TextChoices):
    """Communication channels for sending reminders"""

    EMAIL = "email", _("Email")
    SMS = "sms", _("SMS")
    PUSH = "push", _("Push Notification")
    IN_APP = "in_app", _("In-App Notification")


class ReminderStatus(models.TextChoices):
    """Status of reminder delivery"""

    PENDING = "pending", _("Pending")
    SENT = "sent", _("Sent")
    FAILED = "failed", _("Failed")
    CANCELLED = "cancelled", _("Cancelled")


class RecurringClassSchedule(models.Model):
    """
    Template for recurring class schedules.
    Used to automatically create individual ClassSchedule instances.
    """

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="recurring_schedules")
    students = models.ManyToManyField(
        CustomUser, related_name="recurring_schedules", help_text=_("Students participating in this recurring class")
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="recurring_schedules")
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    class_type = models.CharField(
        _("class type"), max_length=20, choices=ClassType.choices, default=ClassType.INDIVIDUAL
    )

    # Enhanced frequency options
    frequency_type = models.CharField(
        _("frequency type"), max_length=10, choices=FrequencyType.choices, default=FrequencyType.WEEKLY
    )

    # Enhanced status management
    status = models.CharField(
        _("status"), max_length=10, choices=RecurringClassStatus.choices, default=RecurringClassStatus.ACTIVE
    )

    # Group class capacity
    max_participants = models.PositiveIntegerField(
        _("maximum participants"),
        null=True,
        blank=True,
        help_text=_("Maximum number of participants for group classes"),
    )

    # Recurrence pattern
    day_of_week = models.CharField(_("day of week"), max_length=10, choices=WeekDay.choices)
    start_time = models.TimeField(_("start time"))
    end_time = models.TimeField(_("end time"))
    duration_minutes = models.PositiveIntegerField(_("duration in minutes"))

    # Recurrence period
    start_date = models.DateField(_("start date"))
    end_date = models.DateField(_("end date"), null=True, blank=True)

    # Legacy compatibility - keep for backward compatibility
    is_active = models.BooleanField(_("is active"), default=True)

    # Creation and modification tracking
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_recurring_schedules")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status change tracking
    cancelled_at = models.DateTimeField(_("cancelled at"), null=True, blank=True)
    cancelled_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_recurring_schedules",
        help_text=_("User who cancelled this recurring series"),
    )
    paused_at = models.DateTimeField(_("paused at"), null=True, blank=True)
    paused_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paused_recurring_schedules",
        help_text=_("User who paused this recurring series"),
    )

    class Meta:
        ordering = ["day_of_week", "start_time"]
        indexes = [
            models.Index(fields=["teacher", "status", "start_date"]),
            models.Index(fields=["school", "status"]),
            models.Index(fields=["frequency_type", "status"]),
        ]

    def __str__(self):
        frequency_display = self.get_frequency_type_display()
        return f"{self.title} - {frequency_display} {self.get_day_of_week_display()} {self.start_time}"

    def clean(self):
        """Validate recurring schedule"""
        if self.start_time >= self.end_time:
            raise ValidationError({"end_time": _("End time must be after start time.")})

        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError({"end_date": _("End date must be after start date.")})

        # Validate max_participants for group classes
        if self.class_type == ClassType.GROUP:
            if self.max_participants is None or self.max_participants <= 0:
                raise ValidationError({"max_participants": _("Max participants is required for group classes.")})
        elif self.class_type == ClassType.INDIVIDUAL and self.pk and self.students.count() > 1:
            raise ValidationError({"students": _("Individual classes can only have one student.")})

    def get_student_count(self):
        """Get the total number of students in this recurring class"""
        return self.students.count()

    def add_student(self, user):
        """Add a student to this recurring class if capacity allows"""
        if self.class_type == ClassType.INDIVIDUAL and self.students.count() >= 1:
            raise ValidationError("Individual classes can only have one student.")

        if self.max_participants and self.get_student_count() >= self.max_participants:
            raise ValidationError("Class has reached maximum capacity.")

        # Check if user is a school member
        if not user.school_memberships.filter(school=self.school, is_active=True).exists():
            raise ValidationError("Student must be a member of the school.")

        self.students.add(user)

    def remove_student(self, user):
        """Remove a student from this recurring class"""
        self.students.remove(user)

    def generate_instances(self, weeks_ahead=4):
        """Generate individual ClassSchedule instances for this recurring schedule"""
        from datetime import timedelta

        if self.status != RecurringClassStatus.ACTIVE:
            return []

        # Find the first occurrence
        current_date = self.start_date
        target_weekday = list(WeekDay.values).index(self.day_of_week)

        # Move to the first occurrence of the target weekday
        days_ahead = target_weekday - current_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        current_date += timedelta(days=days_ahead)

        # Generate schedules for the specified number of weeks
        end_generation_date = timezone.now().date() + timedelta(weeks=weeks_ahead)
        if self.end_date:
            end_generation_date = min(end_generation_date, self.end_date)

        created_schedules = []
        interval_weeks = (
            1
            if self.frequency_type == FrequencyType.WEEKLY
            else (2 if self.frequency_type == FrequencyType.BIWEEKLY else 4)
        )

        while current_date <= end_generation_date:
            # Skip if there are conflicts
            if not self._has_conflict_on_date(current_date):
                # Check if a schedule already exists for this date
                existing_schedule = ClassSchedule.objects.filter(
                    teacher=self.teacher,
                    school=self.school,
                    scheduled_date=current_date,
                    start_time=self.start_time,
                    recurring_schedule=self,
                ).first()

                if not existing_schedule:
                    # Create instance for each student
                    for student in self.students.all():
                        schedule = ClassSchedule.objects.create(
                            teacher=self.teacher,
                            student=student,
                            school=self.school,
                            title=self.title,
                            description=self.description,
                            class_type=self.class_type,
                            scheduled_date=current_date,
                            start_time=self.start_time,
                            end_time=self.end_time,
                            duration_minutes=self.duration_minutes,
                            booked_by=self.created_by,
                            status=ClassStatus.SCHEDULED,
                            recurring_schedule=self,
                            max_participants=self.max_participants,
                        )
                        # Add additional students for group classes
                        if self.class_type == ClassType.GROUP:
                            other_students = self.students.exclude(id=student.id)
                            schedule.additional_students.set(other_students)

                        created_schedules.append(schedule)
                        break  # Only create one schedule per recurring class

            # Move to next occurrence based on frequency
            current_date += timedelta(weeks=interval_weeks)

        return created_schedules

    def _has_conflict_on_date(self, target_date):
        """Check if there are conflicts on a specific date"""

        # Check for teacher unavailability
        unavailabilities = TeacherUnavailability.objects.filter(
            teacher=self.teacher,
            school=self.school,
            date=target_date,
        )

        for unavailability in unavailabilities:
            if unavailability.is_all_day:
                return True
            if (
                unavailability.start_time
                and unavailability.end_time
                and not (self.end_time <= unavailability.start_time or self.start_time >= unavailability.end_time)
            ):
                return True

        return False

    def detect_schedule_conflicts(self, weeks_ahead=4):
        """Detect conflicts in the schedule for upcoming weeks"""
        from datetime import timedelta

        conflicts = []
        current_date = self.start_date
        target_weekday = list(WeekDay.values).index(self.day_of_week)

        # Move to the first occurrence
        days_ahead = target_weekday - current_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        current_date += timedelta(days=days_ahead)

        end_date = timezone.now().date() + timedelta(weeks=weeks_ahead)
        if self.end_date:
            end_date = min(end_date, self.end_date)

        interval_weeks = (
            1
            if self.frequency_type == FrequencyType.WEEKLY
            else (2 if self.frequency_type == FrequencyType.BIWEEKLY else 4)
        )

        while current_date <= end_date:
            # Check teacher unavailability
            unavailabilities = TeacherUnavailability.objects.filter(
                teacher=self.teacher,
                school=self.school,
                date=current_date,
            )

            for unavailability in unavailabilities:
                if unavailability.is_all_day or (
                    unavailability.start_time
                    and unavailability.end_time
                    and not (self.end_time <= unavailability.start_time or self.start_time >= unavailability.end_time)
                ):
                    conflicts.append(
                        {
                            "type": "teacher_unavailability",
                            "date": current_date,
                            "details": unavailability,
                        }
                    )

            # Check existing class conflicts
            existing_classes = ClassSchedule.objects.filter(
                teacher=self.teacher,
                school=self.school,
                scheduled_date=current_date,
            ).exclude(recurring_schedule=self)

            for existing_class in existing_classes:
                if not (self.end_time <= existing_class.start_time or self.start_time >= existing_class.end_time):
                    conflicts.append(
                        {
                            "type": "existing_class",
                            "date": current_date,
                            "conflicting_class_id": existing_class.id,
                            "details": existing_class,
                        }
                    )

            current_date += timedelta(weeks=interval_weeks)

        return conflicts

    def pause_series(self, reason="", paused_by=None):
        """Pause the recurring series"""
        if self.status == RecurringClassStatus.PAUSED:
            return {"success": False, "error": "Series is already paused"}

        self.status = RecurringClassStatus.PAUSED
        self.paused_at = timezone.now()
        self.paused_by = paused_by
        self.is_active = False
        self.save()

        return {"success": True}

    def resume_series(self, resumed_by=None):
        """Resume the paused recurring series"""
        if self.status != RecurringClassStatus.PAUSED:
            return {"success": False, "error": "Series is not paused"}

        self.status = RecurringClassStatus.ACTIVE
        self.paused_at = None
        self.paused_by = None
        self.is_active = True
        self.save()

        return {"success": True}

    def cancel_series(self, reason="", cancelled_by=None):
        """Cancel the recurring series (soft delete)"""
        self.status = RecurringClassStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancelled_by = cancelled_by
        self.is_active = False
        self.save()

        # Cancel all future instances (with proper signal emission)
        future_instances = self.generated_instances.filter(
            status=ClassStatus.SCHEDULED, scheduled_date__gte=timezone.now().date()
        )

        # Loop through instances to properly trigger signals for audit trail
        for instance in future_instances:
            instance.status = ClassStatus.CANCELLED
            instance.cancelled_at = timezone.now()
            instance.cancelled_by = cancelled_by
            instance.cancellation_reason = f"Recurring series cancelled: {reason}"
            # Set changed_by for audit trail
            instance._changed_by_user = cancelled_by
            instance.save()

        return {"success": True}

    def cancel_occurrence(self, date, reason="", cancelled_by=None):
        """Cancel a specific occurrence of the recurring class"""
        # Check if the date matches the recurring pattern
        target_weekday = list(WeekDay.values).index(self.day_of_week)
        if date.weekday() != target_weekday:
            raise ValidationError("Date does not match recurring pattern")

        # Find or create the specific instance
        instance = self.generated_instances.filter(scheduled_date=date).first()
        if instance:
            instance.status = ClassStatus.CANCELLED
            instance.cancelled_at = timezone.now()
            instance.cancelled_by = cancelled_by
            instance.cancellation_reason = reason
            # Set changed_by for audit trail
            instance._changed_by_user = cancelled_by
            instance.save()

        return {"cancelled_date": date, "reason": reason}

    def get_cancelled_occurrences(self):
        """Get list of cancelled occurrence dates"""
        return list(
            self.generated_instances.filter(status=ClassStatus.CANCELLED).values_list("scheduled_date", flat=True)
        )

    def get_future_instances(self):
        """Get all future instances of this recurring class"""
        return self.generated_instances.filter(scheduled_date__gte=timezone.now().date())

    # Legacy method for backward compatibility
    def generate_class_schedules(self, weeks_ahead=4):
        """Legacy method - calls generate_instances"""
        return self.generate_instances(weeks_ahead)


class ReminderPreference(models.Model):
    """
    User preferences for class reminders.
    """

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reminder_preferences")
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="reminder_preferences",
        null=True,
        blank=True,
        help_text=_("School-specific preferences (null for global preferences)"),
    )

    # Timing preferences (hours before class)
    reminder_timing_hours = models.JSONField(
        _("reminder timing hours"),
        default=list,  # Default: empty list, will be handled by business logic
        help_text=_("List of hours before class to send reminders (e.g., [24, 2, 0.5])"),
    )

    # Communication channels
    communication_channels = models.JSONField(
        _("communication channels"),
        default=list,  # Default: empty list, will be handled by business logic
        help_text=_("List of preferred communication channels"),
    )

    # Timezone preference (overrides school timezone)
    timezone_preference = models.CharField(
        _("timezone preference"),
        max_length=50,
        null=True,
        blank=True,
        help_text=_("User's preferred timezone (e.g., 'America/New_York')"),
    )

    # Active status
    is_active = models.BooleanField(
        _("is active"), default=True, help_text=_("Whether reminders are enabled for this user")
    )

    # School default indicator
    is_school_default = models.BooleanField(
        _("is school default"),
        default=False,
        help_text=_("Whether this is the default preference template for the school"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "school"]
        ordering = ["user", "school"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["school", "is_school_default"]),
        ]

    def __str__(self):
        school_name = self.school.name if self.school else "Global"
        return f"{self.user.name} - {school_name} Preferences"

    def clean(self):
        """Validate reminder preferences"""
        errors = {}

        # Validate timing hours
        if self.reminder_timing_hours:
            if not isinstance(self.reminder_timing_hours, list):
                errors["reminder_timing_hours"] = _("Must be a list of numbers")
            else:
                for hour in self.reminder_timing_hours:
                    if not isinstance(hour, int | float) or hour < 0 or hour > 168:  # Max 1 week
                        errors["reminder_timing_hours"] = _("Hours must be numbers between 0 and 168")
                        break

        # Validate communication channels
        if self.communication_channels:
            if not isinstance(self.communication_channels, list):
                errors["communication_channels"] = _("Must be a list of channel names")
            else:
                valid_channels = [choice[0] for choice in CommunicationChannel.choices]
                for channel in self.communication_channels:
                    if channel not in valid_channels:
                        errors["communication_channels"] = _(
                            "Invalid channel. Must be one of: {}".format(valid_channels)
                        )
                        break

        # Validate timezone
        if self.timezone_preference:
            try:
                import pytz

                pytz.timezone(self.timezone_preference)
            except pytz.UnknownTimeZoneError:
                errors["timezone_preference"] = _("Invalid timezone")

        if errors:
            raise ValidationError(errors)

    @classmethod
    def get_for_user(cls, user, school=None):
        """Get preferences for a user, with fallback to defaults"""
        try:
            # Try school-specific preferences first
            if school:
                return cls.objects.get(user=user, school=school, is_active=True)
            # Then try global preferences
            return cls.objects.get(user=user, school=None, is_active=True)
        except cls.DoesNotExist:
            # Return default preferences
            return cls.get_default_preferences(user, school)

    @classmethod
    def get_default_preferences(cls, user, school=None):
        """Get default preferences for a user"""
        # Try school default first
        if school:
            try:
                school_default = cls.objects.get(school=school, is_school_default=True)
                return cls(
                    user=user,
                    school=school,
                    reminder_timing_hours=school_default.reminder_timing_hours,
                    communication_channels=school_default.communication_channels,
                    timezone_preference=school_default.timezone_preference,
                    is_active=True,
                )
            except cls.DoesNotExist:
                pass

        # Return system defaults
        return cls(
            user=user,
            school=school,
            reminder_timing_hours=[24, 1],  # 24h and 1h before
            communication_channels=["email"],  # Use string value instead of enum
            timezone_preference=None,
            is_active=True,
        )


class ClassReminder(models.Model):
    """
    Individual reminder instances for class schedules.
    """

    class_schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE, related_name="reminders")

    reminder_type = models.CharField(_("reminder type"), max_length=20, choices=ReminderType.choices)

    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="received_reminders",
        help_text=_("User who will receive this reminder"),
    )

    recipient_type = models.CharField(
        _("recipient type"),
        max_length=20,
        choices=[
            ("teacher", _("Teacher")),
            ("student", _("Student")),
            ("parent", _("Parent")),
            ("admin", _("Admin")),
        ],
        help_text=_("Role of the recipient in the class context"),
    )

    communication_channel = models.CharField(
        _("communication channel"),
        max_length=20,
        choices=CommunicationChannel.choices,
        help_text=_("Channel used to send this reminder"),
    )

    status = models.CharField(
        _("status"), max_length=20, choices=ReminderStatus.choices, default=ReminderStatus.PENDING
    )

    # Timing
    scheduled_for = models.DateTimeField(_("scheduled for"), help_text=_("When this reminder should be sent (UTC)"))

    sent_at = models.DateTimeField(
        _("sent at"), null=True, blank=True, help_text=_("When this reminder was actually sent")
    )

    # Message content
    subject = models.CharField(
        _("subject"), max_length=255, blank=True, help_text=_("Email subject or notification title")
    )

    message = models.TextField(_("message"), blank=True, help_text=_("Reminder message content"))

    # Error handling
    error_message = models.TextField(_("error message"), blank=True, help_text=_("Error message if sending failed"))

    retry_count = models.PositiveIntegerField(
        _("retry count"), default=0, help_text=_("Number of times sending was retried")
    )

    max_retries = models.PositiveIntegerField(
        _("max retries"), default=3, help_text=_("Maximum number of retry attempts")
    )

    # External integration
    external_message_id = models.CharField(
        _("external message ID"), max_length=255, blank=True, help_text=_("ID from external communication service")
    )

    # Metadata
    metadata = models.JSONField(
        _("metadata"), default=dict, blank=True, help_text=_("Additional data for the reminder")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_for", "created_at"]
        indexes = [
            models.Index(fields=["class_schedule", "reminder_type"]),
            models.Index(fields=["recipient", "status"]),
            models.Index(fields=["status", "scheduled_for"]),
            models.Index(fields=["communication_channel", "status"]),
            models.Index(fields=["scheduled_for", "status"]),  # Performance index for queries
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["class_schedule", "reminder_type", "recipient", "communication_channel"],
                name="unique_reminder_per_recipient_channel",
                condition=models.Q(status__in=[ReminderStatus.PENDING, ReminderStatus.SENT]),
            ),
        ]

    def __str__(self):
        return f"{self.get_reminder_type_display()} - {self.recipient.name} ({self.class_schedule.title})"

    def clean(self):
        """Validate reminder data"""
        errors = {}

        # Validate scheduled_for is in the future (when creating)
        if not self.pk and self.scheduled_for and self.scheduled_for <= timezone.now():
            errors["scheduled_for"] = _("Scheduled time must be in the future")

        # Validate retry count doesn't exceed max
        if self.retry_count > self.max_retries:
            errors["retry_count"] = _("Retry count cannot exceed max retries")

        if errors:
            raise ValidationError(errors)

    def can_retry(self):
        """Check if this reminder can be retried"""
        return self.status == ReminderStatus.FAILED and self.retry_count < self.max_retries

    @transaction.atomic
    def mark_sent(self, external_message_id=None):
        """Mark reminder as sent"""
        self.status = ReminderStatus.SENT
        self.sent_at = timezone.now()
        if external_message_id:
            self.external_message_id = external_message_id
        self.save(update_fields=["status", "sent_at", "external_message_id"])

    @transaction.atomic
    def mark_failed(self, error_message=None, increment_retry=True):
        """Mark reminder as failed"""
        self.status = ReminderStatus.FAILED
        if error_message:
            self.error_message = error_message
        if increment_retry:
            self.retry_count += 1
        self.save(update_fields=["status", "error_message", "retry_count"])

    @transaction.atomic
    def mark_cancelled(self, reason=None):
        """Mark reminder as cancelled"""
        self.status = ReminderStatus.CANCELLED
        if reason and self.metadata:
            self.metadata["cancellation_reason"] = reason
        elif reason:
            self.metadata = {"cancellation_reason": reason}
        self.save(update_fields=["status", "metadata"])

    @property
    def is_overdue(self):
        """Check if reminder is overdue for sending"""
        if self.status != ReminderStatus.PENDING:
            return False
        return timezone.now() > self.scheduled_for + timedelta(minutes=30)  # 30min grace period

    @property
    def time_until_send(self):
        """Get time until reminder should be sent"""
        if self.status != ReminderStatus.PENDING:
            return None
        return self.scheduled_for - timezone.now()
