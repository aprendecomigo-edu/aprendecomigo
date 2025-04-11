from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(UserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of username.
    """

    def _create_user(self, email, password, **extra_fields):
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
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


# Define user type choices
USER_TYPE_CHOICES = [
    (
        "manager",
        _("School Manager"),
    ),  # School manager, school administrator can be a teacher
    ("teacher", _("Teacher")),  # Teacher
    ("student", _("Student")),  # Student. For adults, student have parent permissions
    ("parent", _("Parent")),  # Parent
]


class CustomUser(AbstractUser):
    """
    Custom User model with email as primary identifier
    """

    username = models.CharField(_("username"), max_length=150, blank=True, null=True)
    email = models.EmailField(_("email address"), unique=True)
    name = models.CharField(_("name"), max_length=150)
    phone_number = models.CharField(_("phone number"), max_length=20, blank=True)
    user_type = models.CharField(
        _("user type"), max_length=20, choices=USER_TYPE_CHOICES, default="manager"
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
    code = models.CharField(
        max_length=6, blank=True
    )  # Kept for backwards compatibility
    secret_key = models.CharField(
        max_length=32, default="DEFAULTSECRETKEYTOBEREPLACED"
    )  # For TOTP
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)

    @classmethod
    def generate_code(cls, email):
        """Generate a TOTP secret for the given email"""
        import pyotp

        # Delete any existing unused codes for this email
        cls.objects.filter(email=email, is_used=False).delete()

        # Generate a new secret key for TOTP
        secret = pyotp.random_base32()

        # Create and return a new verification object
        return cls.objects.create(email=email, secret_key=secret)

    def get_current_code(self):
        """Get the current TOTP code"""
        import pyotp

        totp = pyotp.TOTP(self.secret_key)
        return totp.now()

    def get_provisioning_uri(self, email=None):
        """Get the TOTP provisioning URI for QR codes"""
        import pyotp

        email = email or self.email
        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(name=email, issuer_name="Aprende Comigo")

    def is_valid(self, code=None):
        """
        Check if the code is still valid (not used, not expired, and not too many failed attempts)

        If code is provided, also verify the TOTP code.
        """
        import pyotp
        from django.utils import timezone

        if self.is_used:
            return False

        if self.failed_attempts >= self.max_attempts:
            return False

        # Code expires after 24 hours (extended from 10 minutes since TOTP is more secure)
        expiration_time = self.created_at + timezone.timedelta(hours=24)
        if timezone.now() > expiration_time:
            return False

        # If code is provided, verify it
        if code:
            totp = pyotp.TOTP(self.secret_key)
            return totp.verify(code)

        return True

    def use(self):
        """Mark the code as used"""
        self.is_used = True
        self.save()

    def record_failed_attempt(self):
        """Record a failed verification attempt"""
        self.failed_attempts += 1
        self.save()
        return self.failed_attempts >= self.max_attempts
