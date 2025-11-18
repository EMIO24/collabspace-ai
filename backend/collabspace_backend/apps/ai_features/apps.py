from django.apps import AppConfig

class AiFeaturesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_features'
    verbose_name = 'AI Features'
    
    def ready(self):
        # Import signals to ensure they are connected
        import apps.ai_features.signals