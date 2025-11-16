from django.apps import AppConfig


class WorkspacesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.workspaces"
    verbose_name = "Workspaces"

    def ready(self):
        # import signals to ensure they are connected when the app is ready
        try:
            import apps.workspaces.signals  # noqa: F401
        except Exception:
            # Avoid breaking startup if signals have errors; log for debugging
            import logging

            logging.getLogger(__name__).exception("Failed to import apps.workspaces.signals")
