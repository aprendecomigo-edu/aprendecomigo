from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)

        # Generate a username from email if not provided
        if "username" not in extra_fields or not extra_fields["username"]:
            # Use the part before @ in the email
            username = email.split("@")[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while self.model.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            extra_fields["username"] = username

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_admin", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)


# Define user type choices
USER_TYPE_CHOICES = [
    ("admin", _("Admin")),
    ("teacher", _("Teacher")),
    ("student", _("Student")),
    ("parent", _("Parent")),
]


class CustomUser(AbstractUser):
    """
    Custom User model with email as primary identifier
    """

    username = models.CharField(_("username"), max_length=150, blank=True, null=True)
    email = models.EmailField(_("email address"), unique=True)
    name = models.CharField(_("name"), max_length=150)
    phone_number = models.CharField(_("phone number"), max_length=20, blank=True)
    is_admin = models.BooleanField(default=False)
    user_type = models.CharField(
        _("user type"), max_length=20, choices=USER_TYPE_CHOICES, default="admin"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Student(models.Model):
    """
    Student profile model with additional fields specific to students
    """

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="student_profile"
    )
    school_year = models.CharField(_("school year"), max_length=50)
    birth_date = models.DateField(_("birth date"))
    address = models.TextField(
        _("address"), help_text=_("Street, number, postal code and location")
    )
    cc_number = models.CharField(_("CC number"), max_length=20, blank=True)
    cc_photo = models.ImageField(
        _("CC photo"),
        upload_to="cc_photos/",
        blank=True,
        null=True,
        help_text=_("Photo of CC front and back (only for in-person students)"),
    )
    calendar_iframe = models.TextField(_("calendar iframe"), blank=True)

    def __str__(self):
        return f"Student: {self.user.name}"

    def save(self, *args, **kwargs):
        # Ensure the associated user has the student type
        if self.user.user_type != "student":
            self.user.user_type = "student"
            self.user.save()
        super().save(*args, **kwargs)


class Teacher(models.Model):
    """
    Teacher profile model with additional fields specific to teachers
    """

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="teacher_profile"
    )
    bio = models.TextField(
        _("biography"), blank=True, help_text=_("Teacher's professional biography")
    )
    specialty = models.CharField(_("specialty"), max_length=100, blank=True)
    education = models.TextField(
        _("education"),
        blank=True,
        help_text=_("Educational background and qualifications"),
    )
    hourly_rate = models.DecimalField(
        _("hourly rate"), max_digits=6, decimal_places=2, null=True, blank=True
    )
    availability = models.TextField(
        _("availability"),
        blank=True,
        help_text=_("Available days and times for lessons"),
    )
    address = models.TextField(
        _("address"),
        blank=True,
        help_text=_("Street, number, postal code and location"),
    )
    phone_number = models.CharField(_("teacher phone"), max_length=20, blank=True)
    calendar_iframe = models.TextField(_("calendar iframe"), blank=True)

    def __str__(self):
        return f"Teacher: {self.user.name}"

    def save(self, *args, **kwargs):
        # Ensure the associated user has the teacher type
        if self.user.user_type != "teacher":
            self.user.user_type = "teacher"
            self.user.save()
        super().save(*args, **kwargs)


class EmailVerificationCode(models.Model):
    """
    Model for storing email verification codes.
    """

    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    @classmethod
    def generate_code(cls, email):
        """Generate a 6-digit verification code for the given email"""
        import random
        import string

        # Delete any existing unused codes for this email
        cls.objects.filter(email=email, is_used=False).delete()

        # Generate a random 6-digit code
        code = "".join(random.choices(string.digits, k=6))

        # Create and return a new verification code
        return cls.objects.create(email=email, code=code)

    def is_valid(self):
        """Check if the code is still valid (not used and not expired)"""
        from django.utils import timezone

        if self.is_used:
            return False

        # Code expires after 10 minutes
        expiration_time = self.created_at + timezone.timedelta(minutes=10)
        return timezone.now() <= expiration_time

    def use(self):
        """Mark the code as used"""
        self.is_used = True
        self.save()
