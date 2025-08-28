"""
Educational models for Milestone 3: Core Business Features.

This module contains models for:
- Courses and curricula
- Student-teacher relationships
- Lesson scheduling and management
- Assignments and assessments
- Payment and billing
"""

from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()

# Import existing profile models from accounts app
from accounts.models import StudentProfile, TeacherProfile


# Optimized QuerySets and Managers for performance
class CourseQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related('teacher__user', 'subject')

    def for_teacher(self, teacher):
        return self.filter(teacher=teacher)

    def published(self):
        return self.filter(status='published')


class EnrollmentQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related('student__user', 'course__teacher__user', 'course__subject')

    def active(self):
        return self.filter(is_active=True)


class LessonQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related('course__teacher__user', 'course__subject')

    def upcoming(self):
        return self.filter(status__in=['scheduled', 'in_progress']).order_by('scheduled_date')


class AssignmentQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related('course__teacher__user')

    def active(self):
        return self.filter(is_active=True)


class PaymentQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related('student__user', 'teacher__user', 'enrollment__course')

    def completed(self):
        return self.filter(status='completed')


class AssignmentSubmissionQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related('student__user', 'assignment__course__teacher__user')

    def pending_grading(self):
        return self.filter(is_draft=False, graded_at__isnull=True)


# Managers that use the custom QuerySets
class CourseManager(models.Manager):
    def get_queryset(self):
        return CourseQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()

    def for_teacher(self, teacher):
        return self.get_queryset().for_teacher(teacher).with_related()

    def published(self):
        return self.get_queryset().published().with_related()


class EnrollmentManager(models.Manager):
    def get_queryset(self):
        return EnrollmentQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()

    def active(self):
        return self.get_queryset().active().with_related()


class LessonManager(models.Manager):
    def get_queryset(self):
        return LessonQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()

    def upcoming(self):
        return self.get_queryset().upcoming().with_related()


class AssignmentManager(models.Manager):
    def get_queryset(self):
        return AssignmentQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()

    def active(self):
        return self.get_queryset().active().with_related()


class PaymentManager(models.Manager):
    def get_queryset(self):
        return PaymentQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()

    def completed(self):
        return self.get_queryset().completed().with_related()


class AssignmentSubmissionManager(models.Manager):
    def get_queryset(self):
        return AssignmentSubmissionQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()

    def pending_grading(self):
        return self.get_queryset().pending_grading().with_related()


class Subject(models.Model):
    """
    Academic subjects (Mathematics, Science, English, etc.)
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=10, unique=True)  # MATH, SCI, ENG
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Course(models.Model):
    """
    Educational courses offered by teachers.
    """

    COURSE_TYPE_CHOICES = [
        ("individual", "Individual Tutoring"),
        ("group", "Group Class"),
        ("workshop", "Workshop"),
        ("intensive", "Intensive Course"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="courses")
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="courses")
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES, default="individual")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Pricing
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    total_hours = models.PositiveIntegerField(default=10)
    max_students = models.PositiveIntegerField(default=1)

    # Scheduling
    start_date = models.DateField()
    end_date = models.DateField()

    # Metadata
    learning_objectives = models.TextField(blank=True)
    prerequisites = models.TextField(blank=True)
    materials_needed = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add optimized manager
    objects = CourseManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.teacher.user.get_full_name()}"

    @property
    def total_price(self):
        return self.price_per_hour * self.total_hours

    @property
    def enrolled_students_count(self):
        return self.enrollments.filter(is_active=True).count()

    @property
    def is_full(self):
        return self.enrolled_students_count >= self.max_students


class Enrollment(models.Model):
    """
    Student enrollment in courses.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("dropped", "Dropped"),
        ("suspended", "Suspended"),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    enrollment_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # Progress tracking
    hours_completed = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    progress_percentage = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)

    # Payment status
    is_paid = models.BooleanField(default=False)
    payment_due_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    # Add optimized manager
    objects = EnrollmentManager()

    class Meta:
        unique_together = ["student", "course"]
        ordering = ["-enrollment_date"]

    def __str__(self):
        return f"{self.student.user.get_full_name()} enrolled in {self.course.title}"

    def update_progress(self):
        """Calculate and update progress percentage based on completed hours."""
        if self.course.total_hours > 0:
            self.progress_percentage = min(100, int((self.hours_completed / self.course.total_hours) * 100))
        self.save(update_fields=["progress_percentage"])


class Lesson(models.Model):
    """
    Individual lesson sessions within a course.
    """

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Scheduling
    scheduled_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")

    # Content
    lesson_plan = models.TextField(blank=True)
    homework_assigned = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    # Attendance
    students_present = models.ManyToManyField(StudentProfile, blank=True, related_name="attended_lessons")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add optimized manager
    objects = LessonManager()

    class Meta:
        ordering = ["scheduled_date"]

    def __str__(self):
        return f"{self.title} - {self.course.title} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"

    @property
    def actual_duration_minutes(self):
        if self.actual_start_time and self.actual_end_time:
            delta = self.actual_end_time - self.actual_start_time
            return int(delta.total_seconds() / 60)
        return self.duration_minutes


class Assignment(models.Model):
    """
    Assignments given to students in courses.
    """

    TYPE_CHOICES = [
        ("homework", "Homework"),
        ("project", "Project"),
        ("quiz", "Quiz"),
        ("exam", "Exam"),
        ("presentation", "Presentation"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    description = models.TextField()
    assignment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="homework")

    # Dates
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()

    # Grading
    max_points = models.PositiveIntegerField(default=100)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("1.00"))  # For weighted grades

    # Files and resources
    instructions_file = models.FileField(upload_to="assignments/instructions/", blank=True)
    resources_notes = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    # Add optimized manager
    objects = AssignmentManager()

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.title} - {self.course.title}"


class AssignmentSubmission(models.Model):
    """
    Student submissions for assignments.
    """

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="submissions")

    # Submission
    submitted_at = models.DateTimeField(auto_now_add=True)
    submission_text = models.TextField(blank=True)
    submission_file = models.FileField(upload_to="assignments/submissions/", blank=True)

    # Grading
    points_earned = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    grade_percentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True
    )
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # Status tracking
    is_late = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=True)

    # Add optimized manager
    objects = AssignmentSubmissionManager()

    class Meta:
        unique_together = ["assignment", "student"]
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student.full_name} - {self.assignment.title}"

    def save(self, *args, **kwargs):
        # Check if submission is late
        if self.submitted_at and self.assignment.due_date:
            self.is_late = self.submitted_at > self.assignment.due_date

        # Calculate grade percentage if points are provided
        if self.points_earned is not None and self.assignment.max_points > 0:
            self.grade_percentage = min(100, int((self.points_earned / self.assignment.max_points) * 100))

        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    Payment records for course enrollments.
    """

    TYPE_CHOICES = [
        ("enrollment", "Course Enrollment"),
        ("lesson", "Individual Lesson"),
        ("materials", "Learning Materials"),
        ("late_fee", "Late Fee"),
        ("refund", "Refund"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
        ("cancelled", "Cancelled"),
    ]

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="payments", null=True, blank=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="payments")
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="received_payments")

    payment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="enrollment")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Amounts
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    teacher_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Stripe integration
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    stripe_charge_id = models.CharField(max_length=200, blank=True)

    # Metadata
    description = models.CharField(max_length=200)
    payment_method = models.CharField(max_length=50, default="stripe")
    currency = models.CharField(max_length=3, default="EUR")

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)
    failure_reason = models.CharField(max_length=200, blank=True)

    # Add optimized manager
    objects = PaymentManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment €{self.amount} - {self.student.user.get_full_name()} to {self.teacher.user.get_full_name()}"

    def calculate_teacher_amount(self):
        """Calculate teacher amount after platform fee."""
        # Platform takes 5% fee
        fee = self.amount * Decimal("0.05")
        self.platform_fee = fee
        self.teacher_amount = self.amount - fee
        return self.teacher_amount
