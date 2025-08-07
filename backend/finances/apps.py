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
            # Import here to avoid AppRegistryNotReady errors
            from django.apps import apps
            
            # Ensure all required models are available
            required_models = [
                ('accounts', 'CustomUser'),
                ('accounts', 'School'), 
                ('accounts', 'TeacherProfile'),
                ('accounts', 'SchoolMembership'),
                ('accounts', 'ParentChildRelationship'),
                ('accounts', 'TeacherCourse'),
            ]
            
            # Validate all cross-app models are accessible
            for app_label, model_name in required_models:
                try:
                    apps.get_model(app_label, model_name)
                    logger.debug(f"Successfully accessed {app_label}.{model_name}")
                except LookupError:
                    logger.error(f"Could not access required model {app_label}.{model_name}")
                    
        except Exception as e:
            logger.error(f"Error in FinancesConfig.ready(): {e}")
