from django.db import models
from django.conf import settings

class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class ClassType(models.Model):
    """
    Represents a type of class with specific pricing and configuration.
    The name field stores the unique class type code that matches the Google Calendar event description.
    Examples: "MATH101", "CHEMISTRY_ADV", "ENGLISH_PRIVATE", etc.
    """
    name = models.CharField(max_length=100, unique=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class ClassSession(models.Model):
    title = models.CharField(max_length=255)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='teaching_sessions'
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='learning_sessions'
    )
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    class_type = models.ForeignKey(
        ClassType,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    google_calendar_id = models.CharField(max_length=255, unique=True)
    attended = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
