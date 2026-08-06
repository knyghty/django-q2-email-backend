from django.apps import AppConfig


class Q2EmailBackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_q2_email_backend"
    label = "q2_email_backend"

    def ready(self) -> None:
        from . import checks  # NOQA: F401
