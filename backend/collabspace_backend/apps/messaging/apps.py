from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.messaging'
    verbose_name = 'Messaging'

    def ready(self):
        # Import signals to ensure they are connected upon Django startup
        import apps.messaging.signals