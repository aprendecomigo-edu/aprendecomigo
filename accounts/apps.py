from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = _("Accounts and User Management")

    def ready(self):
        # Import signals to ensure they are registered
        import logging

        logger = logging.getLogger(__name__)
        logger.info("AccountsConfig.ready() called - importing signals")
        try:
            import importlib

            # Force reload to avoid caching issues
            if "accounts.signals" in __import__("sys").modules:
                signals_module = __import__("sys").modules["accounts.signals"]
                importlib.reload(signals_module)
                logger.info("Signals module reloaded")
            else:
                logger.info("Original signals imported")
        except Exception as e:
            logger.error(f"Failed to import signals: {e}")
            import traceback

            traceback.print_exc()
