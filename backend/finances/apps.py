import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class FinancesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "finances"

    def ready(self):
        """
        Initialize runtime utilities for cross-app dependencies.
        This method is called when Django starts up and all apps are loaded.
        """
        try:
            # Import signals after app registry is ready to avoid circular imports
            from . import signals
        except ImportError:
            pass

        # Register cross-app signal connections using app registry
        from django.db.models.signals import post_save

        # Connect to lesson completion signals safely
        try:
            from django.apps import apps

            Lesson = apps.get_model("classroom", "Lesson")
            post_save.connect(
                signals.handle_lesson_completion,
                sender=Lesson,
                dispatch_uid="finances_lesson_completion",
            )
        except LookupError:
            # Handle case where classroom app is not installed
            pass

        # Connect to user creation for payment setup
        try:
            User = apps.get_model(*self.get_model("auth", "User")._meta.label.split("."))
            post_save.connect(
                signals.setup_user_payment_profile,
                sender=User,
                dispatch_uid="finances_user_setup",
            )
        except LookupError:
            pass

        # Ensure all required models are available
        required_models = [
            ("accounts", "CustomUser"),
            ("accounts", "School"),
            ("accounts", "TeacherProfile"),
            ("accounts", "SchoolMembership"),
            ("accounts", "ParentChildRelationship"),
            ("accounts", "TeacherCourse"),
        ]

        # Validate all cross-app models are accessible
        for app_label, model_name in required_models:
            try:
                apps.get_model(app_label, model_name)
                logger.debug(f"Successfully accessed {app_label}.{model_name}")
            except LookupError:
                logger.error(f"Could not access required model {app_label}.{model_name}")
