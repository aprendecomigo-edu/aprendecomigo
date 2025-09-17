"""
Enumeration classes for the accounts app.

This module contains all the choice enums used across different models
in the accounts application.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class SchoolRole(models.TextChoices):
    SCHOOL_OWNER = (
        "school_owner",
        _("School Owner"),
    )  # Created the school, has full access
    SCHOOL_ADMIN = (
        "school_admin",
        _("School Administrator"),
    )  # Can manage all aspects of the school
    TEACHER = "teacher", _("Teacher")  # Can manage classes and students
    SCHOOL_STAFF = (
        "school_staff",
        _("School Staff"),
    )  # Limited access for administrative tasks
    STUDENT = "student", _("Student")  # Access to assigned classes
    GUARDIAN = "guardian", _("Guardian")  # Can manage student accounts and approve purchases


# Educational System Enumerations
class PortugueseSchoolYear(models.TextChoices):
    """School years for Portuguese education system"""

    FIRST = "1", _("Year 1")
    SECOND = "2", _("Year 2")
    THIRD = "3", _("Year 3")
    FOURTH = "4", _("Year 4")
    FIFTH = "5", _("Year 5")
    SIXTH = "6", _("Year 6")
    SEVENTH = "7", _("Year 7")
    EIGHTH = "8", _("Year 8")
    NINTH = "9", _("Year 9")
    TENTH = "10", _("Year 10")
    ELEVENTH = "11", _("Year 11")
    TWELFTH = "12", _("Year 12")


class PortugueseEducationLevel(models.TextChoices):
    """Education levels for Portuguese system"""

    BASIC_1ST_CYCLE = "ensino_basico_1_ciclo", _("Basic Education 1st Cycle")
    BASIC_2ND_CYCLE = "ensino_basico_2_ciclo", _("Basic Education 2nd Cycle")
    BASIC_3RD_CYCLE = "ensino_basico_3_ciclo", _("Basic Education 3rd Cycle")
    SECONDARY = "ensino_secundario", _("Secondary Education")


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


class ActivityType(models.TextChoices):
    """Types of activities that can occur in a school"""

    INVITATION_SENT = "invitation_sent", _("Invitation Sent")
    INVITATION_ACCEPTED = "invitation_accepted", _("Invitation Accepted")
    INVITATION_DECLINED = "invitation_declined", _("Invitation Declined")
    STUDENT_JOINED = "student_joined", _("Student Joined")
    TEACHER_JOINED = "teacher_joined", _("Teacher Joined")
    CLASS_CREATED = "class_created", _("Class Created")
    CLASS_COMPLETED = "class_completed", _("Class Completed")
    CLASS_CANCELLED = "class_cancelled", _("Class Cancelled")
    SETTINGS_UPDATED = "settings_updated", _("Settings Updated")


class TrialCostAbsorption(models.TextChoices):
    """Options for who absorbs trial class costs"""

    SCHOOL = "school", _("School")
    TEACHER = "teacher", _("Teacher")
    SPLIT = "split", _("Split")


class CurrencyChoices(models.TextChoices):
    """Currency options for school billing"""

    EUR = "EUR", _("Euro")
    USD = "USD", _("US Dollar")
    BRL = "BRL", _("Brazilian Real")
    GBP = "GBP", _("British Pound")


class LanguageChoices(models.TextChoices):
    """Language options for school interface"""

    PT = "pt", _("Portuguese")
    EN = "en", _("English")
    ES = "es", _("Spanish")
    FR = "fr", _("French")


class CalendarIntegrationChoices(models.TextChoices):
    """Calendar integration options"""

    GOOGLE = "google", _("Google Calendar")
    OUTLOOK = "outlook", _("Microsoft Outlook")
    CALDAV = "caldav", _("CalDAV")


class EmailIntegrationChoices(models.TextChoices):
    """Email integration provider options"""

    NONE = "none", _("None")
    SMTP = "smtp", _("SMTP")
    SENDGRID = "sendgrid", _("SendGrid")
    MAILGUN = "mailgun", _("Mailgun")


class DataRetentionChoices(models.TextChoices):
    """Data retention policy options"""

    ONE_YEAR = "1_year", _("1 Year")
    TWO_YEARS = "2_years", _("2 Years")
    FIVE_YEARS = "5_years", _("5 Years")
    INDEFINITE = "indefinite", _("Indefinite")


class EmailDeliveryStatus(models.TextChoices):
    """Email delivery status options with comprehensive tracking"""

    NOT_SENT = "not_sent", _("Not Sent")
    QUEUED = "queued", _("Queued")
    SENDING = "sending", _("Sending")
    SENT = "sent", _("Sent")
    DELIVERED = "delivered", _("Delivered")
    OPENED = "opened", _("Opened")
    CLICKED = "clicked", _("Clicked")
    FAILED = "failed", _("Failed")


class InvitationStatus(models.TextChoices):
    """Status options for teacher invitations"""

    PENDING = "pending", _("Pending")
    SENT = "sent", _("Sent")
    DELIVERED = "delivered", _("Delivered")
    VIEWED = "viewed", _("Viewed")
    ACCEPTED = "accepted", _("Accepted")
    DECLINED = "declined", _("Declined")
    EXPIRED = "expired", _("Expired")
    CANCELLED = "cancelled", _("Cancelled")
