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
    cancellation_reason = models.TextField(_("cancellation reason"), blank=True)
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)

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
    def is_past(self):
        """Check if the class is in the past"""
        scheduled_datetime = timezone.datetime.combine(self.scheduled_date, self.start_time)
        return timezone.make_aware(scheduled_datetime) < timezone.now()

    @property
    def can_be_cancelled(self):
        """Check if the class can still be cancelled"""
        if self.status in [ClassStatus.COMPLETED, ClassStatus.CANCELLED]:
            return False
        return not self.is_past

    def cancel(self, reason="", cancelled_by=None):
        """Cancel the class"""
        if not self.can_be_cancelled:
            raise ValidationError("This class cannot be cancelled.")

        self.status = ClassStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()

    def complete(self):
        """Mark the class as completed"""
        if self.status != ClassStatus.CONFIRMED:
            raise ValidationError("Only confirmed classes can be marked as completed.")

        self.status = ClassStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()


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
