"""
Student progress tracking models for the accounts app.

This module contains models for tracking student learning progress,
assessments, and educational outcomes.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .enums import StudentProgressLevel, AssessmentType


class StudentProgress(models.Model):
    """
    Student progress tracking model for individual learning progress.
    
    Tracks a student's progress in a specific course under a specific teacher,
    including skill mastery, completion percentage, and learning notes.
    """
    
    student = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="learning_progress",
        verbose_name=_("student"),
        help_text=_("Student whose progress is being tracked")
    )
    
    teacher = models.ForeignKey(
        "TeacherProfile",
        on_delete=models.CASCADE,
        related_name="student_progress_records",
        verbose_name=_("teacher"),
        help_text=_("Teacher tracking this student's progress")
    )
    
    school = models.ForeignKey(
        "School",
        on_delete=models.CASCADE,
        related_name="student_progress_records",
        verbose_name=_("school"),
        help_text=_("School where progress is being tracked")
    )
    
    course = models.ForeignKey(
        "Course",
        on_delete=models.CASCADE,
        related_name="student_progress_records",
        verbose_name=_("course"),
        help_text=_("Course for which progress is being tracked")
    )
    
    current_level = models.CharField(
        _("current level"),
        max_length=20,
        choices=StudentProgressLevel.choices,
        default=StudentProgressLevel.BEGINNER,
        help_text=_("Current learning level of the student")
    )
    
    completion_percentage = models.DecimalField(
        _("completion percentage"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Percentage of course completed (0-100)")
    )
    
    skills_mastered = models.JSONField(
        _("skills mastered"),
        default=list,
        blank=True,
        help_text=_("List of skills the student has mastered")
    )
    
    current_topics = models.JSONField(
        _("current topics"),
        default=list,
        blank=True,
        help_text=_("Topics currently being studied")
    )
    
    learning_goals = models.JSONField(
        _("learning goals"),
        default=list,
        blank=True,
        help_text=_("Specific learning goals for this student")
    )
    
    notes = models.TextField(
        _("progress notes"),
        blank=True,
        help_text=_("Teacher's notes about student progress")
    )
    
    last_assessment_date = models.DateField(
        _("last assessment date"),
        null=True,
        blank=True,
        help_text=_("Date of the most recent assessment")
    )
    
    created_at = models.DateTimeField(
        _("created at"), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("updated at"), 
        auto_now=True
    )
    
    class Meta:
        verbose_name = _("Student Progress")
        verbose_name_plural = _("Student Progress Records")
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "teacher", "course"],
                name="unique_student_teacher_course_progress"
            )
        ]
        indexes = [
            models.Index(fields=["student", "course"]),
            models.Index(fields=["teacher", "-updated_at"]),
            models.Index(fields=["school", "course"]),
            models.Index(fields=["completion_percentage"]),
            models.Index(fields=["current_level"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.student.name} - {self.course.name} (Teacher: {self.teacher.user.name})"
    
    def clean(self):
        """Validate the progress data."""
        super().clean()
        
        # Validate completion percentage is between 0 and 100
        if self.completion_percentage < Decimal("0.00") or self.completion_percentage > Decimal("100.00"):
            raise ValidationError(
                _("Completion percentage must be between 0 and 100")
            )
    
    @property
    def recent_assessments(self):
        """Get recent assessments for this progress record."""
        return self.assessments.order_by("-assessment_date")[:5]
    
    @property
    def average_assessment_score(self) -> Decimal | None:
        """Calculate average assessment score percentage."""
        assessments = self.assessments.filter(is_graded=True)
        if not assessments.exists():
            return None
        
        total_percentage = sum(assessment.percentage for assessment in assessments)
        return Decimal(str(total_percentage / assessments.count()))
    
    def update_completion_from_assessments(self):
        """Update completion percentage based on recent assessments."""
        avg_score = self.average_assessment_score
        if avg_score is not None:
            self.completion_percentage = avg_score
            self.save(update_fields=["completion_percentage", "updated_at"])


class ProgressAssessment(models.Model):
    """
    Assessment records for student progress tracking.
    
    Records individual assessments, scores, and teacher feedback
    for specific students in their learning journey.
    """
    
    student_progress = models.ForeignKey(
        StudentProgress,
        on_delete=models.CASCADE,
        related_name="assessments",
        verbose_name=_("student progress"),
        help_text=_("Progress record this assessment belongs to")
    )
    
    assessment_type = models.CharField(
        _("assessment type"),
        max_length=20,
        choices=AssessmentType.choices,
        help_text=_("Type of assessment conducted")
    )
    
    title = models.CharField(
        _("assessment title"),
        max_length=200,
        help_text=_("Title or name of the assessment")
    )
    
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("Detailed description of the assessment")
    )
    
    score = models.DecimalField(
        _("score"),
        max_digits=6,
        decimal_places=2,
        help_text=_("Score achieved by the student")
    )
    
    max_score = models.DecimalField(
        _("maximum score"),
        max_digits=6,
        decimal_places=2,
        help_text=_("Maximum possible score for this assessment")
    )
    
    assessment_date = models.DateField(
        _("assessment date"),
        help_text=_("Date when the assessment was conducted")
    )
    
    skills_assessed = models.JSONField(
        _("skills assessed"),
        default=list,
        blank=True,
        help_text=_("List of specific skills that were assessed")
    )
    
    teacher_notes = models.TextField(
        _("teacher notes"),
        blank=True,
        help_text=_("Teacher's observations and feedback")
    )
    
    is_graded = models.BooleanField(
        _("is graded"),
        default=True,
        help_text=_("Whether this assessment contributes to grades")
    )
    
    improvement_areas = models.JSONField(
        _("improvement areas"),
        default=list,
        blank=True,
        help_text=_("Areas where the student needs improvement")
    )
    
    strengths = models.JSONField(
        _("strengths"),
        default=list,
        blank=True,
        help_text=_("Areas where the student performed well")
    )
    
    created_at = models.DateTimeField(
        _("created at"), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("updated at"), 
        auto_now=True
    )
    
    class Meta:
        verbose_name = _("Progress Assessment")
        verbose_name_plural = _("Progress Assessments")
        ordering = ["-assessment_date", "-created_at"]
        indexes = [
            models.Index(fields=["student_progress", "-assessment_date"]),
            models.Index(fields=["assessment_type", "-assessment_date"]),
            models.Index(fields=["is_graded", "-assessment_date"]),
            models.Index(fields=["assessment_date"]),
        ]
    
    def __str__(self) -> str:
        percentage = self.percentage
        return f"{self.title} - {self.student_progress.student.name} ({percentage:.2f}%)"
    
    @property
    def percentage(self) -> Decimal:
        """Calculate the percentage score for this assessment."""
        if self.max_score > 0:
            return (self.score / self.max_score) * Decimal("100.00")
        return Decimal("0.00")
    
    @property
    def grade_letter(self) -> str:
        """Convert percentage to letter grade."""
        percentage = self.percentage
        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"
    
    def clean(self):
        """Validate the assessment data."""
        super().clean()
        
        # Validate score is not greater than max_score
        if self.score > self.max_score:
            raise ValidationError(
                _("Score cannot be greater than maximum score")
            )
        
        # Validate score is not negative
        if self.score < Decimal("0.00"):
            raise ValidationError(
                _("Score cannot be negative")
            )
        
        # Validate max_score is positive
        if self.max_score <= Decimal("0.00"):
            raise ValidationError(
                _("Maximum score must be greater than 0")
            )
    
    def save(self, *args, **kwargs):
        """Override save to update related progress record."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update the student progress last assessment date
        if is_new or self.assessment_date != self.__class__.objects.get(pk=self.pk).assessment_date:
            self.student_progress.last_assessment_date = self.assessment_date
            self.student_progress.save(update_fields=["last_assessment_date", "updated_at"])