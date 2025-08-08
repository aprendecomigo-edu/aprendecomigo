import pytz
from datetime import datetime, timedelta
from typing import ClassVar

from accounts.models import CustomUser, School, SchoolMembership, TeacherProfile
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


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

    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name="availabilities"
    )
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
        unique_together: ClassVar = ["teacher", "school", "day_of_week", "start_time"]
        ordering: ClassVar = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.teacher.user.name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    def clean(self):
        """Validate that start_time is before end_time"""
        if self.start_time >= self.end_time:
            raise ValidationError({"end_time": _("End time must be after start time.")})


class TeacherUnavailability(models.Model):
    """
    Teacher unavailability for specific dates/times.
    This overrides the regular availability for holidays, sick days, etc.
    """

    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name="unavailabilities"
    )
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
        unique_together: ClassVar = ["teacher", "school", "date", "start_time"]
        ordering: ClassVar = ["date", "start_time"]

    def __str__(self):
        if self.is_all_day:
            return f"{self.teacher.user.name} - {self.date} (All Day)"
        return f"{self.teacher.user.name} - {self.date} {self.start_time}-{self.end_time}"

    def clean(self):
        """Validate unavailability times"""
        if not self.is_all_day:
            if not self.start_time or not self.end_time:
                raise ValidationError(
                    {
                        "start_time": _(
                            "Start time and end time are required for partial day unavailability."
                        )
                    }
                )
            if self.start_time >= self.end_time:
                raise ValidationError({"end_time": _("End time must be after start time.")})


class ClassSchedule(models.Model):
    """
    Scheduled class sessions between teachers and students.
    """

    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name="scheduled_classes"
    )
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
    status = models.CharField(
        _("status"), max_length=20, choices=ClassStatus.choices, default=ClassStatus.SCHEDULED
    )
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
        help_text=_("User who cancelled this class")
    )
    cancellation_reason = models.TextField(_("cancellation reason"), blank=True)
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)
    completed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_classes",
        help_text=_("User who marked this class as completed")
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
        help_text=_("User who marked this class as no-show")
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
        help_text=_("User who confirmed this class")
    )
    
    # Rejection info
    rejected_at = models.DateTimeField(_("rejected at"), null=True, blank=True)
    rejected_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_classes",
        help_text=_("User who rejected this class")
    )

    # Group class capacity management
    max_participants = models.PositiveIntegerField(
        _("maximum participants"),
        null=True,
        blank=True,
        help_text=_("Maximum number of participants allowed for group classes")
    )

    # Enhanced metadata for structured data storage
    metadata = models.JSONField(
        _("metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional structured metadata for the class")
    )

    # Notes
    teacher_notes = models.TextField(_("teacher notes"), blank=True)
    student_notes = models.TextField(_("student notes"), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar = ["scheduled_date", "start_time"]
        indexes: ClassVar = [
            models.Index(fields=["teacher", "scheduled_date"]),
            models.Index(fields=["student", "scheduled_date"]),
            models.Index(fields=["school", "scheduled_date"]),
            models.Index(fields=["status", "scheduled_date"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.scheduled_date} {self.start_time}"

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
        if not SchoolMembership.objects.filter(
            user=self.student, school=self.school, is_active=True
        ).exists():
            raise ValidationError({"student": _("Student must be a member of the school.")})

        # Check that teacher has a school membership
        if not SchoolMembership.objects.filter(
            user=self.teacher.user, school=self.school, is_active=True
        ).exists():
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
            return float('inf')  # No limit
        return max(0, self.max_participants - self.get_total_participants())

    # Timezone-aware datetime methods
    def get_scheduled_datetime_in_teacher_timezone(self):
        """Get the scheduled datetime in the teacher's timezone (from school settings)"""
        # Get school timezone from school settings
        try:
            school_timezone_str = self.school.settings.timezone
        except (AttributeError, ValueError, TypeError):
            school_timezone_str = 'UTC'
        
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
            school_timezone_str = 'UTC'
        
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
        
        self.save(update_fields=['metadata'])

    def _validate_metadata(self):
        """Validate metadata structure and required fields"""
        if not self.metadata:
            return
        
        errors = {}
        
        # Validate difficulty_level if present
        if 'difficulty_level' in self.metadata:
            valid_levels = ['beginner', 'intermediate', 'advanced']
            if self.metadata['difficulty_level'] not in valid_levels:
                errors['difficulty_level'] = f"Invalid difficulty level. Must be one of: {valid_levels}"
        
        # Validate topics as list of strings
        if 'topics' in self.metadata:
            topics = self.metadata['topics']
            if not isinstance(topics, list):
                errors['topics'] = "Topics must be a list of strings"
            else:
                for topic in topics:
                    if not isinstance(topic, str):
                        errors['topics'] = "Each topic must be a string"
                        break
        
        # Additional validation for group classes
        if self.class_type == ClassType.GROUP:
            # Group classes require specific metadata fields when metadata is provided
            if self.metadata:
                required_group_fields = ['group_dynamics', 'interaction_level', 'collaboration_type']
                missing_fields = [field for field in required_group_fields if field not in self.metadata]
                if missing_fields:
                    errors['metadata'] = f"Group classes must include the following metadata fields: {', '.join(missing_fields)}"
        
        if errors:
            raise ValidationError(errors)


class RecurringClassSchedule(models.Model):
    """
    Template for recurring class schedules.
    Used to automatically create individual ClassSchedule instances.
    """

    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name="recurring_schedules"
    )
    student = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="recurring_schedules"
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="recurring_schedules")
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    class_type = models.CharField(
        _("class type"), max_length=20, choices=ClassType.choices, default=ClassType.INDIVIDUAL
    )

    # Recurrence pattern
    day_of_week = models.CharField(_("day of week"), max_length=10, choices=WeekDay.choices)
    start_time = models.TimeField(_("start time"))
    end_time = models.TimeField(_("end time"))
    duration_minutes = models.PositiveIntegerField(_("duration in minutes"))

    # Recurrence period
    start_date = models.DateField(_("start date"))
    end_date = models.DateField(_("end date"), null=True, blank=True)

    # Status
    is_active = models.BooleanField(_("is active"), default=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="created_recurring_schedules"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.title} - {self.get_day_of_week_display()} {self.start_time}"

    def clean(self):
        """Validate recurring schedule"""
        if self.start_time >= self.end_time:
            raise ValidationError({"end_time": _("End time must be after start time.")})

        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError({"end_date": _("End date must be after start date.")})

    def generate_class_schedules(self, weeks_ahead=4):
        """Generate individual ClassSchedule instances for this recurring schedule"""
        from datetime import timedelta

        if not self.is_active:
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
        while current_date <= end_generation_date:
            # Check if a schedule already exists for this date
            existing_schedule = ClassSchedule.objects.filter(
                teacher=self.teacher,
                student=self.student,
                school=self.school,
                scheduled_date=current_date,
                start_time=self.start_time,
            ).first()

            if not existing_schedule:
                schedule = ClassSchedule.objects.create(
                    teacher=self.teacher,
                    student=self.student,
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
                )
                created_schedules.append(schedule)

            # Move to next week
            current_date += timedelta(weeks=1)

        return created_schedules
