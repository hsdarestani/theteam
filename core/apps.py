from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Keep the singleton branding model in a separate module while ensuring
        # Django registers it as part of the core application.
        from . import identity_models  # noqa: F401
