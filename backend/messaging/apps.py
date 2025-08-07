from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'

    def ready(self):
        """Import signal handlers to register them with Django."""
        try:
            from . import signals  # noqa
        except ImportError:
            pass
