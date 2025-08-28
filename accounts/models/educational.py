"""
Educational system and course related models for the accounts app.

This module contains models related to educational systems,
courses, and the relationships between teachers and courses.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


# Educational System Enumerations
class PortugueseSchoolYear(models.TextChoices):
    """School years for Portuguese education system"""

    FIRST = "1", _("1º ano")
    SECOND = "2", _("2º ano")
    THIRD = "3", _("3º ano")
    FOURTH = "4", _("4º ano")
    FIFTH = "5", _("5º ano")
    SIXTH = "6", _("6º ano")
    SEVENTH = "7", _("7º ano")
    EIGHTH = "8", _("8º ano")
    NINTH = "9", _("9º ano")
    TENTH = "10", _("10º ano")
    ELEVENTH = "11", _("11º ano")
    TWELFTH = "12", _("12º ano")


class PortugueseEducationLevel(models.TextChoices):
    """Education levels for Portuguese system"""

    BASIC_1ST_CYCLE = "ensino_basico_1_ciclo", _("Ensino Básico 1º Ciclo")
    BASIC_2ND_CYCLE = "ensino_basico_2_ciclo", _("Ensino Básico 2º Ciclo")
    BASIC_3RD_CYCLE = "ensino_basico_3_ciclo", _("Ensino Básico 3º Ciclo")
    SECONDARY = "ensino_secundario", _("Ensino Secundário")


class CustomSchoolYear(models.TextChoices):
    """School years for custom/generic education system"""

    GRADE_1 = "1", _("Grade 1")
    GRADE_2 = "2", _("Grade 2")
    GRADE_3 = "3", _("Grade 3")
    GRADE_4 = "4", _("Grade 4")
    GRADE_5 = "5", _("Grade 5")
    GRADE_6 = "6", _("Grade 6")
    GRADE_7 = "7", _("Grade 7")
    GRADE_8 = "8", _("Grade 8")
    GRADE_9 = "9", _("Grade 9")
    GRADE_10 = "10", _("Grade 10")
    GRADE_11 = "11", _("Grade 11")
    GRADE_12 = "12", _("Grade 12")


class CustomEducationLevel(models.TextChoices):
    """Education levels for custom/generic system"""

    ELEMENTARY = "elementary", _("Elementary")
    MIDDLE_SCHOOL = "middle_school", _("Middle School")
    HIGH_SCHOOL = "high_school", _("High School")

class EducationalSystemType(models.TextChoices):
    """Types of educational systems"""

    PORTUGAL = "pt", _("Portugal")
    CUSTOM = "custom", _("Custom")


class EducationalSystem(models.Model):
    """
    Educational system model representing different education systems and their school years.
    Now uses Django enumeration types for better type safety and validation.
    """

    name: models.CharField = models.CharField(
        _("system name"),
        max_length=100,
        help_text=_("Name of the educational system (e.g., 'Portugal')"),
    )
    code: models.CharField = models.CharField(
        _("system code"),
        max_length=20,
        unique=True,
        choices=EducationalSystemType.choices,
        help_text=_("Unique code for the system (e.g., 'pt')"),
    )
    description: models.TextField = models.TextField(
        _("description"), blank=True, help_text=_("Description of the educational system")
    )
    is_active: models.BooleanField = models.BooleanField(_("is active"), default=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Educational System")
        verbose_name_plural = _("Educational Systems")
        ordering = ["name", "code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @property
    def school_year_choices(self):
        """Get the appropriate school year choices for this educational system"""
        if self.code == EducationalSystemType.PORTUGAL:
            return PortugueseSchoolYear.choices
        else:  # custom or any other system
            return CustomSchoolYear.choices

    @property
    def education_level_choices(self):
        """Get the appropriate education level choices for this educational system"""
        if self.code == EducationalSystemType.PORTUGAL:
            return PortugueseEducationLevel.choices
        else:  # custom or any other system
            return CustomEducationLevel.choices

    def validate_school_year(self, school_year_value):
        """Validate that a school year is valid for this educational system"""
        valid_choices = dict(self.school_year_choices)
        return school_year_value in valid_choices

    def validate_education_level(self, education_level_value):
        """Validate that an education level is valid for this educational system"""
        valid_choices = dict(self.education_level_choices)
        return education_level_value in valid_choices

    def get_school_year_display(self, school_year_value):
        """Get the display name for a school year value"""
        choices_dict = dict(self.school_year_choices)
        return choices_dict.get(school_year_value, school_year_value)

    def get_education_level_display(self, education_level_value):
        """Get the display name for an education level value"""
        choices_dict = dict(self.education_level_choices)
        return choices_dict.get(education_level_value, education_level_value)


class Course(models.Model):
    """
    Course model representing a subject or course that can be taught.
    Independent of teachers - teachers can be associated through TeacherCourse.
    """

    name: models.CharField = models.CharField(_("course name"), max_length=150)
    code: models.CharField = models.CharField(
        _("course code"),
        max_length=20,
        help_text=_("Alphanumeric code for the course (e.g., educational system codes)"),
    )
    educational_system: models.ForeignKey = models.ForeignKey(
        EducationalSystem,
        on_delete=models.CASCADE,
        related_name="courses",
        help_text=_("Educational system this course belongs to"),
    )
    education_level: models.CharField = models.CharField(
        _("education level"),
        max_length=50,
        default="other",
        help_text=_("Education level within the educational system"),
    )
    description: models.TextField = models.TextField(
        _("course description"),
        blank=True,
        help_text=_("Detailed description of the course content and objectives"),
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["code", "educational_system"]
        ordering = ["educational_system__name", "name"]
        indexes = [
            models.Index(fields=["educational_system", "education_level"]),
            models.Index(fields=["code"]),
            models.Index(fields=["name"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def clean(self):
        """Validate that education_level is valid for the selected educational system"""
        super().clean()
        if (
            self.educational_system
            and self.education_level
            and not self.educational_system.validate_education_level(self.education_level)
        ):

            valid_levels = dict(self.educational_system.education_level_choices)
            raise ValidationError(
                {
                    "education_level": f"Education level '{self.education_level}' is not valid for "
                    f"educational system '{self.educational_system.name}'. "
                    f"Valid options: {list(valid_levels.keys())}"
                }
            )


class TeacherCourse(models.Model):
    """
    Many-to-Many relationship between Teacher and Course.
    Allows teachers to teach multiple courses and courses to be taught by multiple teachers.
    """

    teacher: models.ForeignKey = models.ForeignKey(
        "TeacherProfile", on_delete=models.CASCADE, related_name="teacher_courses"
    )
    course: models.ForeignKey = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="course_teachers")
    # Optional fields for teacher-specific course information
    hourly_rate: models.DecimalField = models.DecimalField(
        _("hourly rate for this course"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Specific hourly rate for this course (overrides teacher's default rate)"),
    )
    is_active: models.BooleanField = models.BooleanField(_("is actively teaching"), default=True)
    started_teaching: models.DateField = models.DateField(_("started teaching date"), auto_now_add=True)

    class Meta:
        unique_together = ["teacher", "course"]
        indexes = [
            # Indexes for tutor discovery filtering
            models.Index(fields=["hourly_rate"]),
            models.Index(fields=["is_active", "hourly_rate"]),
            models.Index(fields=["course", "is_active"]),
            models.Index(fields=["teacher", "is_active"]),
        ]

    def __str__(self) -> str:
        teacher_name = (
            self.teacher.user.name  # type: ignore[attr-defined]
            if hasattr(self.teacher, "user") and hasattr(self.teacher.user, "name")
            else str(self.teacher.user)  # type: ignore[attr-defined]
        )
        return f"{teacher_name} teaches {self.course.name}"  # type: ignore[attr-defined]
