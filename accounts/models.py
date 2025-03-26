from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
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
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        
        # Generate a username from email if not provided
        if 'username' not in extra_fields or not extra_fields['username']:
            # Use the part before @ in the email
            username = email.split('@')[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while self.model.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            extra_fields['username'] = username
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom User model with email as primary identifier but keeping username for compatibility
    """
    username = models.CharField(_('username'), max_length=150, blank=True, null=True)
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(_('name'), max_length=150)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email
