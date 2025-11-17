from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.projects'
    verbose_name = 'Project Management'

    def ready(self):
        """Connect signals when the application is ready."""
        # Import signals to ensure they are registered
        import apps.projects.signals