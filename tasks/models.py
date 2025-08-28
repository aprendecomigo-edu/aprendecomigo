from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser


class Task(models.Model):
    """
    Task model for to-do functionality
    """

    PRIORITY_CHOICES = [
        ("low", _("Low")),
        ("medium", _("Medium")),
        ("high", _("High")),
    ]

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
    ]

    TASK_TYPE_CHOICES = [
        ("onboarding", _("Onboarding")),
        ("assignment", _("Assignment")),
        ("personal", _("Personal")),
        ("system", _("System")),
    ]

    # Core fields
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

    # Relationships
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="tasks", verbose_name=_("User"))

    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name=_("Status"))
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium", verbose_name=_("Priority"))
    task_type = models.CharField(
        max_length=20, choices=TASK_TYPE_CHOICES, default="personal", verbose_name=_("Task Type")
    )

    # Dates
    due_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Due Date"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Completed At"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    # Additional fields
    is_urgent = models.BooleanField(default=False, verbose_name=_("Is Urgent"))
    is_system_generated = models.BooleanField(
        default=False,
        verbose_name=_("Is System Generated"),
        help_text=_("True if this task was automatically created by the system"),
    )

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ["-priority", "due_date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "due_date"]),
            models.Index(fields=["priority", "status"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def save(self, *args, **kwargs):
        """Override save to handle completion logic"""
        if self.status == "completed" and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != "completed" and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if not self.due_date or self.status == "completed":
            return False
        return timezone.now() > self.due_date

    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if not self.due_date:
            return None
        delta = self.due_date - timezone.now()
        return delta.days

    @classmethod
    def create_onboarding_tasks(cls, user):
        """Create default onboarding tasks for new users"""
        onboarding_tasks = [
            {
                "title": "Complete Your Profile",
                "description": "Fill out your profile information to get started",
                "priority": "high",
                "task_type": "onboarding",
                "is_system_generated": True,
            },
            {
                "title": "Explore the Dashboard",
                "description": "Take a tour of the main features and navigation",
                "priority": "medium",
                "task_type": "onboarding",
                "is_system_generated": True,
            },
        ]

        created_tasks = []
        for task_data in onboarding_tasks:
            task = cls.objects.create(user=user, **task_data)
            created_tasks.append(task)

        return created_tasks


class TaskComment(models.Model):
    """
    Comments/notes for tasks
    """

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments", verbose_name=_("Task"))
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name=_("User"))
    comment = models.TextField(verbose_name=_("Comment"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Task Comment")
        verbose_name_plural = _("Task Comments")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment on {self.task.title} by {self.user.email}"
