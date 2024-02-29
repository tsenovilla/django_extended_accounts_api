from django.apps import AppConfig


class ExtendedAccountsApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "extended_accounts_api"

    def ready(self):
        # Import the signals
        from .signals import __all__

        return super().ready()
