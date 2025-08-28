from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "scheduler"

    def ready(self):
        """Import signal handlers when Django starts."""
        import scheduler.signals  # noqa
